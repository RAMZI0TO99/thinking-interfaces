from __future__ import annotations

import unittest

import torch
from torch import nn

from adaptation.episodic import (
    adapt_torch_model,
    named_parameter_snapshot,
    parameters_unchanged,
)


class EpisodicAdaptationTests(unittest.TestCase):
    def test_support_changes_clone_and_never_changes_base(self) -> None:
        torch.manual_seed(7)
        base = nn.Linear(3, 2)
        original = named_parameter_snapshot(base)
        inputs = torch.randn(8, 3)
        targets = torch.tensor([0, 1, 0, 1, 0, 1, 0, 1])
        result = adapt_torch_model(
            base, inputs, targets, steps=4, learning_rate=0.1
        )
        self.assertTrue(parameters_unchanged(original, base.named_parameters()))
        self.assertFalse(parameters_unchanged(original, result.model.named_parameters()))
        self.assertEqual(len(result.losses), 4)
