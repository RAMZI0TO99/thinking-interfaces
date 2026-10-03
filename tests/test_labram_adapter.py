from __future__ import annotations

import copy
import unittest

import torch
from torch import nn

from adaptation.labram_adapter import (
    LaBraMAdapterBlock,
    adapt_labram_adapter_support,
    inject_labram_adapters,
)
from data.runtime import configure_scientific_runtime


class ActualBlockClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        configure_scientific_runtime()
        from braindecode.models.labram import _WindowsAttentionBlock

        self.normalization = nn.BatchNorm1d(12)
        self.blocks = nn.ModuleList(
            [
                _WindowsAttentionBlock(
                    dim=12,
                    num_heads=3,
                    qkv_bias=True,
                    qk_norm=nn.LayerNorm,
                    init_values=0.1,
                    drop=0.2,
                )
                for _ in range(2)
            ]
        )
        self.head = nn.Linear(12, 2)

    def forward(self, x):
        x = self.normalization(x).transpose(1, 2)
        for block in self.blocks:
            x = block(x)
        return self.head(x.mean(1))


class LaBraMAdapterTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(37)
        self.base = ActualBlockClassifier().eval()
        self.inputs = torch.randn(2, 12, 4)
        self.labels = torch.tensor([0, 1])

    def assert_state_equal(self, left, right):
        self.assertEqual(set(left), set(right))
        for name in left:
            torch.testing.assert_close(left[name], right[name], rtol=0, atol=0)

    def test_actual_blocks_initial_identity_dtype_mode_and_diagnostic_rejection(self):
        model = copy.deepcopy(self.base).double()
        expected = model(self.inputs.double()).detach()
        report = inject_labram_adapters(
            model, target_modules=("blocks.0", "blocks.1"), bottleneck_dim=3
        )
        torch.testing.assert_close(model(self.inputs.double()), expected, rtol=0, atol=0)
        self.assertEqual(report.adapter_parameters, 2 * (12 * 3 + 3 + 3 * 12 + 12))
        self.assertFalse(any(m.training for m in model.modules()))
        for block in model.blocks:
            self.assertIsInstance(block, LaBraMAdapterBlock)
            self.assertFalse(any(p.requires_grad for p in block.block.parameters()))
            self.assertTrue(all(p.dtype == torch.float64 for p in block.adapter.parameters()))
            for flags in ({"return_attention": True}, {"return_qkv": True}):
                with self.subTest(flags=flags), self.assertRaises(ValueError):
                    block(torch.randn(2, 4, 12).double(), **flags)

    def test_bad_targets_fail_before_any_model_mutation(self):
        before = copy.deepcopy(self.base.state_dict())
        for names, width in (
            ((), 3),
            (("blocks.0", "blocks.9"), 3),
            (("blocks.0", "head"), 3),
            (("blocks.0",) * 2, 3),
            (("blocks.0",), 12),
            (("blocks.0",), True),
        ):
            with self.subTest(names=names, width=width), self.assertRaises(ValueError):
                inject_labram_adapters(self.base, target_modules=names, bottleneck_dim=width)
            self.assert_state_equal(self.base.state_dict(), before)
            self.assertTrue(all(p.requires_grad for p in self.base.parameters()))
        inject_labram_adapters(self.base, target_modules=("blocks.0",), bottleneck_dim=3)
        before = copy.deepcopy(self.base.state_dict())
        with self.assertRaises(ValueError):
            inject_labram_adapters(
                self.base, target_modules=("blocks.1", "blocks.0"), bottleneck_dim=3
            )
        self.assert_state_equal(self.base.state_dict(), before)

    def test_one_shot_support_updates_only_adapter_and_explicit_head_policy(self):
        inject_labram_adapters(self.base, target_modules=("blocks.0", "blocks.1"), bottleneck_dim=3)
        before = copy.deepcopy(self.base.state_dict())
        for train_head in (False, True):
            with self.subTest(train_head=train_head):
                result = adapt_labram_adapter_support(
                    self.base,
                    self.inputs,
                    self.labels,
                    steps=3,
                    learning_rate=0.1,
                    train_head=train_head,
                )
                changed = {
                    name
                    for name, value in result.model.state_dict().items()
                    if not torch.equal(value, before[name])
                }
                expected_names = {
                    name
                    for name, _ in result.model.named_parameters()
                    if ".adapter." in name or (train_head and name.startswith("head."))
                }
                self.assertEqual(set(result.trainable_names), expected_names)
                self.assertTrue(changed <= expected_names)
                self.assertTrue(any("adapter.down.weight" in name for name in changed))
                self.assertTrue(any("adapter.up.weight" in name for name in changed))
                self.assertEqual("head.weight" in changed, train_head)
                self.assertFalse(any(m.training for m in result.model.modules()))
                self.assertTrue(all(p.grad is None for p in result.model.parameters()))
                self.assert_state_equal(self.base.state_dict(), before)
                self.assertFalse(torch.equal(result.model(self.inputs), self.base(self.inputs)))

    def test_episode_reset_query_buffers_and_state_round_trip(self):
        inject_labram_adapters(self.base, target_modules=("blocks.0",), bottleneck_dim=3)
        # A nonzero source adapter must be restored too, not silently reinitialized.
        with torch.no_grad():
            self.base.blocks[0].adapter.up.weight.fill_(0.05)
        self.base.train()  # episode policy must override this only on the clone
        before = copy.deepcopy(self.base.state_dict())
        modes = {name: module.training for name, module in self.base.named_modules()}
        first = adapt_labram_adapter_support(
            self.base, self.inputs, self.labels, steps=3, learning_rate=0.1, train_head=True
        )
        query = torch.randn(4, 12, 4)
        query_before = copy.deepcopy(first.model.state_dict())
        with torch.inference_mode():
            prediction = first.model(query)
            first.model(query * 100)  # intervening queries cannot affect a new episode
        self.assert_state_equal(first.model.state_dict(), query_before)
        repeated = adapt_labram_adapter_support(
            self.base, self.inputs, self.labels, steps=3, learning_rate=0.1, train_head=True
        )
        self.assert_state_equal(first.model.state_dict(), repeated.model.state_dict())
        self.assertEqual(first.losses, repeated.losses)
        self.assert_state_equal(self.base.state_dict(), before)
        self.assertEqual(
            modes, {name: module.training for name, module in self.base.named_modules()}
        )
        self.assertTrue(
            all(
                p.data_ptr() != dict(self.base.named_parameters())[n].data_ptr()
                for n, p in first.model.named_parameters()
            )
        )
        restored = ActualBlockClassifier().eval()
        inject_labram_adapters(restored, target_modules=("blocks.0",), bottleneck_dim=3)
        restored.load_state_dict(first.model.state_dict(), strict=True)
        torch.testing.assert_close(restored(query), prediction, rtol=0, atol=0)

    def test_invalid_support_and_missing_adapters_are_rejected(self):
        with self.assertRaises(ValueError):
            adapt_labram_adapter_support(
                self.base, self.inputs, self.labels, steps=1, learning_rate=0.1, train_head=True
            )
        inject_labram_adapters(self.base, target_modules=("blocks.0",), bottleneck_dim=3)
        for values, labels, steps, rate in (
            (self.inputs, torch.tensor([0, 0]), 1, 0.1),
            (self.inputs, self.labels.float(), 1, 0.1),
            (self.inputs * float("nan"), self.labels, 1, 0.1),
            (self.inputs, self.labels, True, 0.1),
            (self.inputs, self.labels, 1, float("nan")),
        ):
            with self.subTest(steps=steps, rate=rate), self.assertRaises(ValueError):
                adapt_labram_adapter_support(
                    self.base, values, labels, steps=steps, learning_rate=rate, train_head=True
                )
