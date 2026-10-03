"""Seeded effective-QKV LoRA episodes from a plain immutable CPU source."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import torch
from torch import nn

from adaptation.labram_lora import inject_labram_qkv_lora
from adaptation.labram_tuning import configure_labram_tuning
from encoder.labram import LaBraMClassifier


@dataclass(frozen=True, slots=True)
class LoRAMask:
    target_modules: tuple[str, ...]
    rank: int
    alpha: float
    train_head: bool
    trainable_names: tuple[str, ...]
    trainable_parameters: int
    adapter_parameters: int
    method: str = "lora"
    support_normalization_policy: str = "all_modules_eval_source_affine_and_buffers_frozen"


@dataclass(frozen=True, slots=True)
class LoRAEpisodeResult:
    model: LaBraMClassifier
    mask: LoRAMask
    losses: tuple[float, ...]


def adapt_labram_lora_support(
    source_model: LaBraMClassifier,
    support_inputs: torch.Tensor,
    support_targets: torch.Tensor,
    *,
    target_modules: tuple[str, ...],
    rank: int,
    alpha: float,
    seed: int,
    train_head: bool,
    steps: int,
    learning_rate: float,
) -> LoRAEpisodeResult:
    """Fresh seeded LoRA + SGD, using support only and preserving caller RNG.

    The source must be plain, finite CPU float32 LaBraM. Only newly installed
    LoRA A/B tensors and the explicitly enabled existing head are optimized.
    Zero B preserves the initial forward; A can have zero gradient on step one.
    Fixed full-support SGD steps are engineering settings, not selected scientific
    hyperparameters. Source provenance and subject roles belong to the runner.
    """
    if (
        type(steps) is not int
        or steps < 1
        or type(learning_rate) not in (int, float)
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
        or type(seed) is not int
        or not 0 <= seed < 2**63
        or type(train_head) is not bool
        or type(rank) is not int
        or rank < 1
        or type(alpha) not in (int, float)
        or not math.isfinite(alpha)
        or alpha <= 0
        or type(target_modules) is not tuple
        or not target_modules
        or any(type(n) is not str for n in target_modules)
    ):
        raise ValueError(
            "explicit valid LoRA targets, rank, alpha, seed, head and SGD settings required"
        )
    if not isinstance(source_model, LaBraMClassifier) or not isinstance(
        source_model.head, nn.Linear
    ):
        raise ValueError("source must be a LaBraMClassifier with a linear head")
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in source_model.parameters()):
        raise ValueError("LoRA support episodes require CPU float32 parameters")
    if any(not torch.isfinite(v).all() for v in source_model.state_dict().values()):
        raise ValueError("source state contains nonfinite values")
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
    configure_labram_tuning(model, method="linear")  # Reject hybrid/wrapped sources.
    model.requires_grad_(False)
    # CPU-only generator seeding avoids touching any CUDA RNG state.
    with torch.random.fork_rng(devices=[]):
        torch.random.set_rng_state(torch.Generator(device="cpu").manual_seed(seed).get_state())
        report = inject_labram_qkv_lora(
            model, target_modules=target_modules, rank=rank, alpha=alpha
        )
    model.head.requires_grad_(train_head)
    model.eval()
    names, selected = [], []
    for name, parameter in model.named_parameters():
        parameter.grad = None
        if parameter.requires_grad:
            names.append(name)
            selected.append(parameter)
    mask = LoRAMask(
        report.target_modules,
        report.rank,
        report.alpha,
        train_head,
        tuple(names),
        sum(p.numel() for p in selected),
        report.adapter_parameters,
    )
    inputs = support_inputs.detach().to(device="cpu", dtype=torch.float32).clone()
    targets = support_targets.detach().to(device="cpu").clone()
    optimizer = torch.optim.SGD(selected, lr=learning_rate)
    losses = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(inputs), targets)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite support loss")
        loss.backward()  # type: ignore[no-untyped-call]  # Torch's backward lacks annotations.
        if any(p.grad is None or not torch.isfinite(p.grad).all() for p in selected):
            raise ValueError("missing or nonfinite selected support gradient")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in selected):
            raise ValueError("nonfinite adapted parameter")
        losses.append(float(loss.detach()))
    optimizer.zero_grad(set_to_none=True)
    return LoRAEpisodeResult(model, mask, tuple(losses))
