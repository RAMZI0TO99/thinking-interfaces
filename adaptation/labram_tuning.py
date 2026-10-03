"""Explicit linear/partial/full LaBraM masks and isolated support-only tuning."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Literal

import torch
from torch import nn
from torch.nn.utils import parametrize

from encoder.labram import LaBraMClassifier, configure_trainable_depth

TuningMethod = Literal["linear", "partial", "full"]


@dataclass(frozen=True, slots=True)
class TuningMask:
    method: TuningMethod
    depth: int | str
    selected_blocks: tuple[int, ...]
    trainable_names: tuple[str, ...]
    trainable_parameters: int
    head_policy: str = "existing_head_always_trainable"
    support_normalization_policy: str = "all_modules_eval_affine_follows_parameter_mask"


def configure_labram_tuning(
    model: LaBraMClassifier, *, method: TuningMethod, partial_depth: int | None = None
) -> TuningMask:
    """Validate first, then apply the established depth mask without changing mode.

    Linear selects the existing head. Partial selects the last N complete blocks
    plus head; patcher, embeddings and final norm remain frozen, even at N=all
    blocks. Full selects the entire backbone and head. Normalization affine
    parameters follow those boundaries; module evaluation mode is a separate
    support-loop policy. Hybrid adapter/LoRA models are rejected here.
    """
    from braindecode.models import Labram  # type: ignore[import-untyped]
    from braindecode.models.labram import _WindowsAttentionBlock  # type: ignore[import-untyped]

    if not isinstance(model, LaBraMClassifier) or not isinstance(model.backbone, Labram):
        raise ValueError("a LaBraMClassifier with the installed LaBraM backbone is required")
    blocks = model.backbone.blocks
    if (
        not blocks
        or any(not isinstance(block, _WindowsAttentionBlock) for block in blocks)
        or any(parametrize.is_parametrized(module) for module in model.modules())
        or not isinstance(model.head, nn.Linear)
        or model.head.out_features < 2
        or any(not name.startswith(("backbone.", "head.")) for name, _ in model.named_parameters())
    ):
        raise ValueError("plain unwrapped LaBraM blocks and a classification head are required")
    if method not in ("linear", "partial", "full"):
        raise ValueError("method must be linear, partial or full")
    if method == "partial":
        if type(partial_depth) is not int or not 1 <= partial_depth <= len(blocks):
            raise ValueError("partial_depth must be an integer in 1..number of blocks")
        depth: int | str = partial_depth
        indices = tuple(range(len(blocks) - partial_depth, len(blocks)))
    else:
        if partial_depth is not None:
            raise ValueError("partial_depth is only valid for partial tuning")
        depth = "all" if method == "full" else 0
        indices = tuple(range(len(blocks))) if method == "full" else ()
    prefixes = tuple(f"backbone.blocks.{i}." for i in indices)
    expected = tuple(
        name
        for name, _ in model.named_parameters()
        if name.startswith("head.") or method == "full" or name.startswith(prefixes)
    )
    count = configure_trainable_depth(model, depth)
    actual = tuple(name for name, p in model.named_parameters() if p.requires_grad)
    if actual != expected:
        raise ValueError("established depth mask differs from the explicit tuning policy")
    return TuningMask(method, depth, indices, actual, count)


@dataclass(frozen=True, slots=True)
class TuningEpisodeResult:
    model: LaBraMClassifier
    mask: TuningMask
    losses: tuple[float, ...]


def adapt_labram_tuning_support(
    source_model: LaBraMClassifier,
    support_inputs: torch.Tensor,
    support_targets: torch.Tensor,
    *,
    method: TuningMethod,
    partial_depth: int | None = None,
    steps: int,
    learning_rate: float,
) -> TuningEpisodeResult:
    """Clone the immutable source and run fresh full-support SGD in eval mode.

    No query argument, optimizer reuse or head reinitialization. Call with the
    same source template to reset an episode. SGD and fixed support steps are
    explicit engineering choices, not the future source-validated search budget.
    Dataset permission, label mapping and source identity belong to the runner.
    """
    if (
        type(steps) is not int
        or steps < 1
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
    ):
        raise ValueError("steps and learning_rate must be positive and finite")
    if not isinstance(source_model, LaBraMClassifier) or not isinstance(
        source_model.head, nn.Linear
    ):
        raise ValueError("source must be a LaBraMClassifier with a linear head")
    if (
        support_inputs.ndim != 3
        or any(size < 1 for size in support_inputs.shape)
        or support_inputs.shape[1] != len(source_model.channel_names)
        or support_targets.shape != (support_inputs.shape[0],)
        or not support_inputs.is_floating_point()
        or support_targets.dtype != torch.long
        or not torch.isfinite(support_inputs).all()
        or set(support_targets.tolist()) != set(range(source_model.head.out_features))
    ):
        raise ValueError(
            "finite named-channel inputs and integer support labels for all classes required"
        )
    model = copy.deepcopy(source_model)
    mask = configure_labram_tuning(model, method=method, partial_depth=partial_depth)
    model.eval()
    for parameter in model.parameters():
        parameter.grad = None
    selected = [p for p in model.parameters() if p.requires_grad]
    weight = next(model.parameters())
    inputs = support_inputs.detach().to(device=weight.device, dtype=weight.dtype).clone()
    targets = support_targets.detach().to(device=weight.device).clone()
    optimizer = torch.optim.SGD(selected, lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    losses = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(inputs), targets)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite support loss")
        loss.backward()
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
            raise ValueError("missing or nonfinite selected support gradient")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in selected):
            raise ValueError("nonfinite adapted parameter")
        losses.append(float(loss.detach()))
    optimizer.zero_grad(set_to_none=True)
    return TuningEpisodeResult(model, mask, tuple(losses))
