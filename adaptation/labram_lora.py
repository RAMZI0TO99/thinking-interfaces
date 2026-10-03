"""LoRA on the effective QKV weight read directly by installed LaBraM attention."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn.utils import parametrize


class LowRankWeight(nn.Module):
    """Weight + (alpha/rank) BA, with zero B for exact initial identity.

    Weight parametrization reaches both Linear.forward and functional.linear
    callers. Input-dropout LoRA is deliberately not represented by this class.
    """

    def __init__(self, weight: torch.Tensor, *, rank: int, alpha: float) -> None:
        super().__init__()
        if weight.ndim != 2 or type(rank) is not int or not 1 <= rank <= min(weight.shape):
            raise ValueError("rank must be a positive integer within the weight dimensions")
        if not math.isfinite(alpha) or alpha <= 0:
            raise ValueError("alpha must be positive and finite")
        self.scaling = alpha / rank
        self.lora_a = nn.Parameter(weight.new_empty((rank, weight.shape[1])))
        self.lora_b = nn.Parameter(weight.new_zeros((weight.shape[0], rank)))
        nn.init.kaiming_uniform_(self.lora_a, a=math.sqrt(5))

    def forward(self, weight: torch.Tensor) -> torch.Tensor:
        return weight + self.scaling * (self.lora_b @ self.lora_a)


@dataclass(frozen=True, slots=True)
class QKVLoRAReport:
    target_modules: tuple[str, ...]
    adapter_parameters: int
    rank: int
    alpha: float


def inject_labram_qkv_lora(
    model: nn.Module,
    *,
    target_modules: tuple[str, ...],
    rank: int,
    alpha: float,
) -> QKVLoRAReport:
    """Parametrize explicit QKV modules, freezing only their original weights.

    Validate all targets before mutation. Callers must separately freeze the
    backbone and choose the classifier/normalization policy before optimization.
    Install parametrizations before constructing the optimizer.
    """
    if not target_modules or len(set(target_modules)) != len(target_modules):
        raise ValueError("explicit, unique QKV target modules are required")
    selected: list[tuple[str, nn.Linear, LowRankWeight]] = []
    for name in target_modules:
        if re.fullmatch(r"(?:backbone\.)?blocks\.\d+\.attn\.qkv", name) is None:
            raise ValueError(f"not an explicit LaBraM QKV target: {name}")
        try:
            module = model.get_submodule(name)
        except AttributeError as error:
            raise ValueError(f"missing QKV target: {name}") from error
        if (
            not isinstance(module, nn.Linear)
            or module.bias is not None
            or module.out_features % 3 != 0
            or parametrize.is_parametrized(module)
        ):
            raise ValueError(f"target must be an unparametrized bias-free QKV Linear: {name}")
        adapter = LowRankWeight(module.weight, rank=rank, alpha=alpha)
        selected.append((name, module, adapter))
    for _, module, adapter in selected:
        module.weight.requires_grad_(False)
        parametrize.register_parametrization(module, "weight", adapter)
    return QKVLoRAReport(
        target_modules,
        sum(parameter.numel() for _, _, a in selected for parameter in a.parameters()),
        rank,
        alpha,
    )
