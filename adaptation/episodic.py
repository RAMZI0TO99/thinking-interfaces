"""Support-only PyTorch adaptation for target-subject episodes."""

from __future__ import annotations

import copy
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import cast

import torch
from torch import nn


@dataclass(frozen=True, slots=True)
class AdaptationResult:
    model: nn.Module
    losses: tuple[float, ...]
    trainable_parameters: int


def adapt_torch_model(
    base_model: nn.Module,
    support_inputs: torch.Tensor,
    support_targets: torch.Tensor,
    *,
    steps: int,
    learning_rate: float,
    trainable: Callable[[str, nn.Parameter], bool] | None = None,
    device: torch.device | str = "cpu",
) -> AdaptationResult:
    """Clone and adapt a model using support data; query data is not accepted."""

    if support_inputs.shape[0] != support_targets.shape[0] or support_inputs.shape[0] < 1:
        raise ValueError("support inputs and targets must have the same non-zero size")
    if steps < 1 or learning_rate <= 0:
        raise ValueError("steps and learning_rate must be positive")
    model = copy.deepcopy(base_model).to(device)
    selected: list[nn.Parameter] = []
    for name, parameter in model.named_parameters():
        use = trainable(name, parameter) if trainable is not None else True
        parameter.requires_grad_(use)
        if use:
            selected.append(parameter)
    if not selected:
        raise ValueError("adaptation selected no trainable parameters")
    optimizer = torch.optim.AdamW(selected, lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    inputs = support_inputs.to(device)
    targets = support_targets.to(device)
    losses: list[float] = []
    model.train()
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        logits = cast(torch.Tensor, model(inputs))
        loss = criterion(logits, targets)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return AdaptationResult(model, tuple(losses), sum(value.numel() for value in selected))


def named_parameter_snapshot(module: nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in module.named_parameters()}


def parameters_unchanged(
    before: dict[str, torch.Tensor], after: Iterable[tuple[str, nn.Parameter]]
) -> bool:
    return all(
        name in before and torch.equal(before[name], value.detach().cpu())
        for name, value in after
    )
