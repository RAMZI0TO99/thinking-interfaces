from __future__ import annotations

import unittest
from typing import cast

import torch
from torch import nn

from adaptation.lora import LoRALinear, inject_lora


class StandInModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(4, 6), nn.ReLU(), nn.Linear(6, 3))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.encoder(inputs))


class LoRATests(unittest.TestCase):
    def test_initial_adapter_is_exact_no_op(self) -> None:
        torch.manual_seed(11)
        base = nn.Linear(4, 3)
        inputs = torch.randn(5, 4)
        expected = base(inputs).detach().clone()
        adapted = LoRALinear(base, rank=2, alpha=4.0)
        torch.testing.assert_close(adapted(inputs), expected, rtol=0.0, atol=0.0)

    def test_support_training_changes_adapter_not_base(self) -> None:
        torch.manual_seed(23)
        base = nn.Linear(4, 2)
        original_weight = base.weight.detach().clone()
        adapted = LoRALinear(base, rank=2, alpha=2.0)
        inputs = torch.randn(8, 4)
        before = adapted(inputs).detach().clone()
        optimizer = torch.optim.SGD((adapted.lora_a, adapted.lora_b), lr=0.5)
        loss = adapted(inputs).square().mean()
        loss.backward()
        optimizer.step()
        self.assertFalse(torch.equal(adapted(inputs).detach(), before))
        torch.testing.assert_close(base.weight, original_weight, rtol=0.0, atol=0.0)
        self.assertFalse(base.weight.requires_grad)

    def test_generic_injection_replaces_selected_linear_layers(self) -> None:
        model = StandInModel()
        result = inject_lora(
            model,
            rank=2,
            alpha=4.0,
            target_names={"encoder.0", "encoder.2"},
        )
        self.assertEqual(result.replaced_modules, ("encoder.0", "encoder.2"))
        self.assertIsInstance(model.encoder[0], LoRALinear)
        self.assertIsInstance(model.encoder[2], LoRALinear)
        self.assertEqual(result.trainable_adapter_parameters, 38)

    def test_unknown_target_is_rejected(self) -> None:
        model = StandInModel()
        with self.assertRaisesRegex(ValueError, "not found"):
            inject_lora(
                model,
                rank=2,
                alpha=2.0,
                target_names={"encoder.0", "missing.linear"},
            )
        self.assertIsInstance(model.encoder[0], nn.Linear)

    def test_adapter_inherits_base_dtype(self) -> None:
        adapted = LoRALinear(nn.Linear(4, 2, dtype=torch.float64), rank=2, alpha=2.0)
        self.assertEqual(adapted.lora_a.dtype, torch.float64)
        self.assertEqual(adapted.lora_b.dtype, torch.float64)
