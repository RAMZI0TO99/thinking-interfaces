from __future__ import annotations

import unittest

import torch
from torch import nn

from adaptation.adapter import AdaptedBlock, inject_adapters
from adaptation.prompt import PromptInjector, SupportPromptGenerator, prepend_prompt_tokens


class AdaptationModuleTests(unittest.TestCase):
    def test_adapter_is_initially_an_exact_no_op(self) -> None:
        torch.manual_seed(1)
        model = nn.Sequential(nn.Linear(4, 4), nn.ReLU())
        inputs = torch.randn(2, 4)
        expected = model(inputs).detach().clone()
        result = inject_adapters(
            model,
            embedding_dim=4,
            bottleneck_dim=2,
            target_names={"0"},
        )
        self.assertIsInstance(model[0], AdaptedBlock)
        torch.testing.assert_close(model(inputs), expected, rtol=0.0, atol=0.0)
        self.assertGreater(result.trainable_adapter_parameters, 0)

    def test_prompt_shape_and_prepend(self) -> None:
        generator = SupportPromptGenerator(
            embedding_dim=8, classes=2, prompt_tokens=3, hidden_dim=12
        )
        prompts = generator(torch.randn(4, 5, 8), torch.zeros((4, 5), dtype=torch.long))
        self.assertEqual(prompts.shape, (4, 3, 8))
        combined = prepend_prompt_tokens(torch.randn(4, 7, 8), prompts)
        self.assertEqual(combined.shape, (4, 10, 8))

    def test_prompt_injection_modes_are_distinct(self) -> None:
        sequence = torch.randn(2, 5, 4)
        prompts = torch.randn(2, 2, 4)
        temporal = PromptInjector("temporal_prefix")
        per_block = PromptInjector("per_block_prefix")
        self.assertEqual(temporal.for_block(sequence, prompts, block_index=0).shape[1], 7)
        self.assertEqual(temporal.for_block(sequence, prompts, block_index=1).shape[1], 5)
        self.assertEqual(per_block.for_block(sequence, prompts, block_index=1).shape[1], 7)
