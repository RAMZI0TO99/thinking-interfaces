"""Backbone-neutral low-rank adaptation for ``torch.nn.Linear`` layers."""

from __future__ import annotations

import math
from collections.abc import Collection
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn
from torch.nn import functional as F


class LoRALinear(nn.Module):
    """Add a trainable low-rank residual to an existing linear layer."""

    def __init__(
        self,
        base: nn.Linear,
        *,
        rank: int,
        alpha: float,
        dropout: float = 0.0,
        freeze_base: bool = True,
    ) -> None:
        super().__init__()
        if rank < 1:
            raise ValueError("rank must be positive")
        if not math.isfinite(alpha) or alpha <= 0:
            raise ValueError("alpha must be positive")
        if not 0.0 <= dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")

        self.base = base
        self.rank = rank
        self.alpha = float(alpha)
        self.scaling = self.alpha / self.rank
        self.dropout = nn.Dropout(dropout)
        self.lora_a = nn.Parameter(
            torch.empty(
                rank,
                base.in_features,
                device=base.weight.device,
                dtype=base.weight.dtype,
            )
        )
        self.lora_b = nn.Parameter(
            torch.zeros(
                base.out_features,
                rank,
                device=base.weight.device,
                dtype=base.weight.dtype,
            )
        )
        nn.init.kaiming_uniform_(self.lora_a, a=math.sqrt(5))
        if freeze_base:
            self.base.weight.requires_grad_(False)
            if self.base.bias is not None:
                self.base.bias.requires_grad_(False)

    @property
    def in_features(self) -> int:
        return self.base.in_features

    @property
    def out_features(self) -> int:
        return self.base.out_features

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        residual = F.linear(F.linear(self.dropout(inputs), self.lora_a), self.lora_b)
        return cast(torch.Tensor, self.base(inputs) + residual * self.scaling)


@dataclass(frozen=True, slots=True)
class LoRAInjectionResult:
    replaced_modules: tuple[str, ...]
    trainable_adapter_parameters: int


def inject_lora(
    module: nn.Module,
    *,
    rank: int,
    alpha: float,
    dropout: float = 0.0,
    target_names: Collection[str] | None = None,
    freeze_base: bool = True,
) -> LoRAInjectionResult:
    """Recursively replace selected linear children with ``LoRALinear``."""

    targets = set(target_names) if target_names is not None else None
    available: list[tuple[nn.Module, str, str, nn.Linear]] = []

    def collect(parent: nn.Module, prefix: str) -> None:
        for child_name, child in tuple(parent.named_children()):
            qualified_name = f"{prefix}.{child_name}" if prefix else child_name
            if isinstance(child, LoRALinear):
                continue
            if isinstance(child, nn.Linear):
                available.append((parent, child_name, qualified_name, child))
            else:
                collect(child, qualified_name)

    collect(module, "")
    available_names = {item[2] for item in available}
    if targets is not None:
        missing = targets - available_names
        if missing:
            raise ValueError(f"target linear modules were not found: {sorted(missing)}")
    selected = [item for item in available if targets is None or item[2] in targets]
    replaced: list[str] = []
    adapter_parameters = 0
    for parent, child_name, qualified_name, child in selected:
        adapted = LoRALinear(
            child,
            rank=rank,
            alpha=alpha,
            dropout=dropout,
            freeze_base=freeze_base,
        )
        setattr(parent, child_name, adapted)
        replaced.append(qualified_name)
        adapter_parameters += adapted.lora_a.numel() + adapted.lora_b.numel()
    return LoRAInjectionResult(tuple(replaced), adapter_parameters)
