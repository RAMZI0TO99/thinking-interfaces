"""Generic residual bottleneck adapters for transformer-like blocks."""

from __future__ import annotations

import math
from collections.abc import Collection
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn


class BottleneckAdapter(nn.Module):
    def __init__(self, embedding_dim: int, bottleneck_dim: int, *, dropout: float = 0.0) -> None:
        super().__init__()
        if embedding_dim < 1 or not 0 < bottleneck_dim < embedding_dim:
            raise ValueError("adapter dimensions must satisfy 0 < bottleneck < embedding")
        if not 0.0 <= dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        self.down = nn.Linear(embedding_dim, bottleneck_dim)
        self.activation = nn.GELU()
        self.dropout = nn.Dropout(dropout)
        self.up = nn.Linear(bottleneck_dim, embedding_dim)
        nn.init.kaiming_uniform_(self.down.weight, a=math.sqrt(5))
        nn.init.zeros_(self.up.weight)
        nn.init.zeros_(self.up.bias)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return cast(
            torch.Tensor,
            inputs + self.up(self.dropout(self.activation(self.down(inputs)))),
        )


class AdaptedBlock(nn.Module):
    def __init__(self, block: nn.Module, adapter: BottleneckAdapter) -> None:
        super().__init__()
        self.block = block
        self.adapter = adapter

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.adapter(self.block(inputs)))


@dataclass(frozen=True, slots=True)
class AdapterInjectionResult:
    replaced_modules: tuple[str, ...]
    trainable_adapter_parameters: int


def inject_adapters(
    module: nn.Module,
    *,
    embedding_dim: int,
    bottleneck_dim: int,
    target_names: Collection[str],
    dropout: float = 0.0,
    freeze_backbone: bool = True,
) -> AdapterInjectionResult:
    """Wrap named child blocks after validating all target names first."""

    targets = set(target_names)
    available: list[tuple[nn.Module, str, str, nn.Module]] = []

    def collect(parent: nn.Module, prefix: str) -> None:
        for name, child in tuple(parent.named_children()):
            qualified = f"{prefix}.{name}" if prefix else name
            available.append((parent, name, qualified, child))
            collect(child, qualified)

    collect(module, "")
    names = {item[2] for item in available}
    missing = targets - names
    if missing:
        raise ValueError(f"adapter target modules were not found: {sorted(missing)}")
    if freeze_backbone:
        module.requires_grad_(False)
    replaced: list[str] = []
    parameters = 0
    for parent, child_name, qualified, child in available:
        if qualified not in targets:
            continue
        adapter = BottleneckAdapter(embedding_dim, bottleneck_dim, dropout=dropout)
        wrapped = AdaptedBlock(child, adapter)
        setattr(parent, child_name, wrapped)
        replaced.append(qualified)
        parameters += sum(value.numel() for value in adapter.parameters())
    return AdapterInjectionResult(tuple(replaced), parameters)
