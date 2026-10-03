"""LaBraM post-block residual adapters and isolated support-only episodes."""

from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn

from adaptation.adapter import BottleneckAdapter


class LaBraMAdapterBlock(nn.Module):
    """Apply h + up(GELU(down(h))) after the complete transformer block.

    Standard feature forwards only. Attention/QKV diagnostic returns have
    different semantics and are deliberately rejected, rather than adapted.
    """

    def __init__(self, block: nn.Module, adapter: BottleneckAdapter) -> None:
        super().__init__()
        self.block = block
        self.adapter = adapter

    def forward(
        self, inputs: torch.Tensor, return_attention: bool = False, return_qkv: bool = False
    ) -> torch.Tensor:
        if return_attention or return_qkv:
            raise ValueError("LaBraM adapters support standard feature forwards only")
        return cast(torch.Tensor, self.adapter(self.block(inputs)))


@dataclass(frozen=True, slots=True)
class LaBraMAdapterReport:
    target_modules: tuple[str, ...]
    bottleneck_dim: int
    adapter_parameters: int
    placement: str = "serial_residual_after_complete_block"


def inject_labram_adapters(
    model: nn.Module, *, target_modules: tuple[str, ...], bottleneck_dim: int
) -> LaBraMAdapterReport:
    """Validate all explicit targets, then wrap actual installed LaBraM blocks.

    Only wrapped source blocks are frozen here. Callers separately select the
    rest of the backbone/head policy. Adapters inherit device, dtype and mode.
    There is no adapter dropout or extra normalization. Install before creating
    an optimizer, and reconstruct the same wrappers before loading saved state.
    """
    from data.runtime import configure_scientific_runtime

    configure_scientific_runtime()
    from braindecode.models.labram import (  # type: ignore[import-untyped]
        _WindowsAttentionBlock,
    )

    if not target_modules or len(set(target_modules)) != len(target_modules):
        raise ValueError("explicit unique LaBraM block targets are required")
    if type(bottleneck_dim) is not int or bottleneck_dim < 1:
        raise ValueError("bottleneck_dim must be a positive integer")
    selected: list[tuple[str, nn.Module, int]] = []
    for name in target_modules:
        if re.fullmatch(r"(?:backbone\.)?blocks\.\d+", name) is None:
            raise ValueError(f"not an explicit LaBraM block target: {name}")
        try:
            block = model.get_submodule(name)
        except AttributeError as error:
            raise ValueError(f"missing LaBraM block: {name}") from error
        if not isinstance(block, _WindowsAttentionBlock):
            raise ValueError(f"target must be an unwrapped installed LaBraM block: {name}")
        dim = int(block.norm1.normalized_shape[0])
        if bottleneck_dim >= dim:
            raise ValueError("bottleneck must be smaller than the block embedding dimension")
        if any(block is previous for _, previous, _ in selected):
            raise ValueError("aliased LaBraM block targets are not supported")
        selected.append((name, block, dim))
    # No model mutation until every target and allocation succeeds.
    wrappers = []
    for name, block, dim in selected:
        weight = next(block.parameters())
        adapter = BottleneckAdapter(dim, bottleneck_dim).to(
            device=weight.device, dtype=weight.dtype
        )
        wrapper = LaBraMAdapterBlock(block, adapter)
        wrapper.training = block.training
        adapter.train(block.training)
        wrappers.append((name, wrapper))
    for name, wrapper in wrappers:
        parent_name, child = name.rsplit(".", 1)
        wrapper.block.requires_grad_(False)
        setattr(model.get_submodule(parent_name), child, wrapper)
    return LaBraMAdapterReport(
        target_modules,
        bottleneck_dim,
        sum(p.numel() for _, wrapper in wrappers for p in wrapper.adapter.parameters()),
    )


@dataclass(frozen=True, slots=True)
class AdapterEpisodeResult:
    model: nn.Module
    losses: tuple[float, ...]
    trainable_names: tuple[str, ...]
    trainable_parameters: int


def adapt_labram_adapter_support(
    source_model: nn.Module,
    support_inputs: torch.Tensor,
    support_targets: torch.Tensor,
    *,
    steps: int,
    learning_rate: float,
    train_head: bool,
) -> AdapterEpisodeResult:
    """Fresh clone + fresh SGD; update adapters and optionally the existing head.

    Evaluation mode is retained even during gradient updates, keeping source
    normalization buffers and dropout fixed. The input API accepts no queries.
    The returned model is in eval mode with gradients cleared. Always pass the
    immutable source template, not a previous episode's result, to reset.

    SGD/full-support steps are an explicit engineering choice here, not a frozen
    scientific optimizer/search budget. Manifest/label permissions are enforced
    by the future experiment runner, not inferred from tensor contents.
    """
    if (
        type(steps) is not int
        or steps < 1
        or not math.isfinite(learning_rate)
        or learning_rate <= 0
    ):
        raise ValueError("steps and learning_rate must be positive and finite")
    if type(train_head) is not bool:
        raise ValueError("train_head must be explicitly boolean")
    head = getattr(source_model, "head", None)
    if not isinstance(head, nn.Linear) or head.out_features < 2:
        raise ValueError("an existing classification head with at least two classes is required")
    if (
        support_inputs.ndim != 3
        or support_inputs.shape[0] < 1
        or support_targets.shape != (support_inputs.shape[0],)
        or not support_inputs.is_floating_point()
        or support_targets.dtype != torch.long
        or not torch.isfinite(support_inputs).all()
        or set(support_targets.tolist()) != set(range(head.out_features))
    ):
        raise ValueError(
            "finite support inputs and integer labels covering every class are required"
        )
    model = copy.deepcopy(source_model)
    model.eval().requires_grad_(False)
    selected_ids: set[int] = set()
    adapters = [
        module.adapter for module in model.modules() if isinstance(module, LaBraMAdapterBlock)
    ]
    if not adapters:
        raise ValueError("source template has no LaBraM adapters")
    for adapter in adapters:
        selected_ids.update(id(p) for p in adapter.parameters())
    if train_head:
        selected_ids.update(id(p) for p in model.get_submodule("head").parameters())
    names, selected = [], []
    for name, parameter in model.named_parameters():
        parameter.grad = None
        if id(parameter) in selected_ids:
            parameter.requires_grad_(True)
            names.append(name)
            selected.append(parameter)
    weight = next(model.parameters())
    inputs = support_inputs.detach().to(device=weight.device, dtype=weight.dtype).clone()
    targets = support_targets.detach().to(device=weight.device).clone()
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
    return AdapterEpisodeResult(
        model, tuple(losses), tuple(names), sum(p.numel() for p in selected)
    )
