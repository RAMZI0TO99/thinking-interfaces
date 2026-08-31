from __future__ import annotations

import unittest

import torch

from adaptation.episodic import adapt_torch_model
from adaptation.prompt_standin import PromptedTransformerStandIn


class PromptStandInTests(unittest.TestCase):
    def model(self, mode):
        torch.manual_seed(18)
        support = torch.randn(4, 5, 8)
        labels = torch.tensor([0, 1, 0, 1])
        model = PromptedTransformerStandIn(
            embedding_dim=8,
            classes=2,
            prompt_tokens=2,
            hidden_dim=12,
            layers=3,
            heads=2,
            mode=mode,
            support_embeddings=support.mean(dim=1).unsqueeze(0),
            support_labels=labels.unsqueeze(0),
        )
        return model, support, labels

    def test_both_modes_condition_query_tokens_without_sequence_growth(self):
        for mode in ("temporal_prefix", "per_block_prefix"):
            with self.subTest(mode=mode):
                model, _, _ = self.model(mode)
                lengths = []
                hooks = [
                    block.register_forward_pre_hook(
                        lambda _module, args, seen=lengths: seen.append(args[0].shape[1])
                    )
                    for block in model.blocks
                ]
                query = torch.randn(3, 5, 8)
                output = model(query)
                for hook in hooks:
                    hook.remove()
                self.assertEqual(lengths, [7, 7, 7])
                self.assertEqual(output.shape, (3, 2))
                changed = model(query + torch.randn_like(query))
                self.assertFalse(torch.equal(output, changed))

    def test_support_adaptation_changes_prompts_and_query_output_only_through_generator(self):
        for mode in ("temporal_prefix", "per_block_prefix"):
            with self.subTest(mode=mode):
                base, support, labels = self.model(mode)
                before = {key: value.detach().clone() for key, value in base.state_dict().items()}
                query = torch.randn(3, 5, 8)
                initial = base(query).detach()
                initial_prompts = base.generated_prompts().detach().clone()
                result = adapt_torch_model(
                    base,
                    support,
                    labels,
                    steps=3,
                    learning_rate=0.05,
                    trainable=lambda name, _: name.startswith("generator."),
                )
                adapted = result.model.eval()
                for key, value in base.state_dict().items():
                    self.assertTrue(torch.equal(before[key], value), key)
                for key, value in adapted.state_dict().items():
                    if not key.startswith("generator."):
                        self.assertTrue(torch.equal(before[key], value), key)
                with torch.inference_mode():
                    final = adapted(query)
                    prompts = adapted.generated_prompts().clone()
                    saved = {key: value.clone() for key, value in adapted.state_dict().items()}
                    adapted(query * 2)
                self.assertFalse(torch.equal(initial, final))
                self.assertFalse(torch.equal(initial_prompts, prompts))
                self.assertTrue(torch.equal(prompts, adapted.generated_prompts()))
                for key, value in adapted.state_dict().items():
                    self.assertTrue(torch.equal(saved[key], value), key)

    def test_support_is_copied_and_invalid_query_is_rejected(self):
        model, _, _ = self.model("temporal_prefix")
        with self.assertRaises(ValueError):
            model(torch.empty(0, 5, 8))
        with self.assertRaises(ValueError):
            model(torch.full((2, 5, 8), float("nan")))
        self.assertFalse(model.support_embeddings.requires_grad)
