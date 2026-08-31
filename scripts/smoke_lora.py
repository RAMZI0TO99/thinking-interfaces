"""Train generic LoRA adapters on a small stand-in network."""

from __future__ import annotations

import json
from typing import cast

import torch
from torch import nn

from adaptation.lora import LoRALinear, inject_lora


class StandInBackbone(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(8, 12), nn.GELU(), nn.Linear(12, 4))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.layers(inputs))


def main() -> int:
    torch.manual_seed(20260830)
    model = StandInBackbone()
    inputs = torch.randn(16, 8)
    expected = model(inputs).detach().clone()
    original_weights = {
        name: child.weight.detach().clone()
        for name, child in model.named_modules()
        if isinstance(child, nn.Linear)
    }
    injection = inject_lora(model, rank=4, alpha=8.0)
    initial = model(inputs).detach().clone()
    initial_exact = torch.equal(initial, expected)
    optimizer = torch.optim.Adam(
        (parameter for parameter in model.parameters() if parameter.requires_grad), lr=0.05
    )
    for _ in range(3):
        optimizer.zero_grad(set_to_none=True)
        loss = model(inputs).square().mean()
        loss.backward()
        optimizer.step()
    trained = model(inputs).detach()
    output_delta = float((trained - initial).abs().max().item())
    base_unchanged = all(
        torch.equal(child.base.weight.detach(), original_weights[name])
        for name, child in model.named_modules()
        if isinstance(child, LoRALinear)
    )
    result = {
        "replaced_modules": injection.replaced_modules,
        "trainable_adapter_parameters": injection.trainable_adapter_parameters,
        "initial_output_exact": initial_exact,
        "trained_output_max_abs_delta": output_delta,
        "base_weights_unchanged": base_unchanged,
    }
    print(json.dumps(result, indent=2))
    return 0 if initial_exact and output_delta > 0.0 and base_unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
