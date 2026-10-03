from __future__ import annotations

import copy
import unittest

import torch

from adaptation.labram_adapter import inject_labram_adapters
from adaptation.labram_lora import inject_labram_qkv_lora
from adaptation.labram_tuning import adapt_labram_tuning_support, configure_labram_tuning
from encoder.labram import LaBraMClassifier


class LaBraMTuningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        from braindecode.models import Labram

        torch.manual_seed(23)
        backbone = Labram(
            n_times=200,
            n_chans=3,
            n_outputs=0,
            num_layers=2,
            drop_prob=0.2,
            attn_drop_prob=0.2,
            drop_path_prob=0.1,
        )
        self.source = LaBraMClassifier(backbone, classes=2, channel_names=("C3", "Cz", "C4"))
        self.support = torch.randn(2, 3, 200) * 0.1
        self.labels = torch.tensor([0, 1])

    def assert_state_equal(self, left, right):
        self.assertEqual(set(left), set(right))
        for name in left:
            torch.testing.assert_close(left[name], right[name], rtol=0, atol=0)

    def test_masks_include_head_and_distinguish_all_blocks_from_full(self):
        self.source.eval()
        initial = copy.deepcopy(self.source.state_dict())
        with torch.inference_mode():
            logits = self.source(self.support)
        for method, depth in (("full", None), ("linear", None), ("partial", 1), ("partial", 2)):
            with self.subTest(method=method, depth=depth):
                result = configure_labram_tuning(self.source, method=method, partial_depth=depth)
                selected_ids = {id(p) for p in self.source.head.parameters()}
                if method == "full":
                    selected_ids.update(id(p) for p in self.source.backbone.parameters())
                elif method == "partial":
                    for block in list(self.source.backbone.blocks)[-depth:]:
                        selected_ids.update(id(p) for p in block.parameters())
                names = {
                    name for name, p in self.source.named_parameters() if id(p) in selected_ids
                }
                self.assertEqual(set(result.trainable_names), names)
                self.assertEqual(
                    result.trainable_parameters,
                    sum(p.numel() for p in self.source.parameters() if id(p) in selected_ids),
                )
                self.assertEqual(self.source.backbone.norm.weight.requires_grad, method == "full")
                self.assertEqual(
                    self.source.backbone.position_embedding.requires_grad, method == "full"
                )
                if method == "partial":
                    self.assertTrue(self.source.backbone.blocks[-1].norm1.weight.requires_grad)
                self.assert_state_equal(self.source.state_dict(), initial)
                with torch.inference_mode():
                    torch.testing.assert_close(self.source(self.support), logits, rtol=0, atol=0)
                self.assertFalse(any(m.training for m in self.source.modules()))

    def test_one_shot_changes_only_selected_groups_for_every_method(self):
        source_state = copy.deepcopy(self.source.state_dict())
        for method, depth in (("linear", None), ("partial", 1), ("partial", 2), ("full", None)):
            with self.subTest(method=method, depth=depth):
                result = adapt_labram_tuning_support(
                    self.source,
                    self.support,
                    self.labels,
                    method=method,
                    partial_depth=depth,
                    steps=2,
                    learning_rate=0.001,
                )
                changed = {
                    name
                    for name, value in result.model.state_dict().items()
                    if not torch.equal(value, source_state[name])
                }
                self.assertTrue(changed <= set(result.mask.trainable_names))
                self.assertIn("head.weight", changed)
                if method == "linear":
                    self.assertTrue(all(name.startswith("head.") for name in changed))
                else:
                    self.assertIn("backbone.blocks.1.attn.qkv.weight", changed)
                    self.assertIn("backbone.blocks.1.norm1.weight", changed)
                self.assertEqual("backbone.position_embedding" in changed, method == "full")
                self.assertEqual("backbone.norm.weight" in changed, method == "full")
                self.assertEqual(
                    "backbone.patch_embed.temporal_conv.conv1.weight" in changed, method == "full"
                )
                self.assertFalse(any(m.training for m in result.model.modules()))
                self.assertTrue(all(p.grad is None for p in result.model.parameters()))
                self.assert_state_equal(self.source.state_dict(), source_state)

    def test_source_modes_gradients_query_and_episode_reset_are_isolated(self):
        source_state = copy.deepcopy(self.source.state_dict())
        source_modes = {n: m.training for n, m in self.source.named_modules()}
        self.source.head.weight.grad = torch.ones_like(self.source.head.weight)
        query = torch.randn(3, 3, 200)
        for method, depth in (("linear", None), ("partial", 1), ("full", None)):
            with self.subTest(method=method):
                first = adapt_labram_tuning_support(
                    self.source,
                    self.support,
                    self.labels,
                    method=method,
                    partial_depth=depth,
                    steps=2,
                    learning_rate=0.001,
                )
                adapted_state = copy.deepcopy(first.model.state_dict())
                with torch.inference_mode():
                    outputs = first.model(query)
                    first.model(query * 50)
                self.assert_state_equal(first.model.state_dict(), adapted_state)
                second = adapt_labram_tuning_support(
                    self.source,
                    self.support,
                    self.labels,
                    method=method,
                    partial_depth=depth,
                    steps=2,
                    learning_rate=0.001,
                )
                self.assert_state_equal(second.model.state_dict(), adapted_state)
                self.assertEqual(first.losses, second.losses)
                self.assertTrue(
                    all(
                        p.data_ptr() != dict(self.source.named_parameters())[n].data_ptr()
                        for n, p in first.model.named_parameters()
                    )
                )
                restored = copy.deepcopy(self.source).eval()
                restored.load_state_dict(first.model.state_dict(), strict=True)
                with torch.inference_mode():
                    torch.testing.assert_close(restored(query), outputs, rtol=0, atol=0)
        self.assert_state_equal(self.source.state_dict(), source_state)
        self.assertEqual(source_modes, {n: m.training for n, m in self.source.named_modules()})
        torch.testing.assert_close(
            self.source.head.weight.grad, torch.ones_like(self.source.head.weight), rtol=0, atol=0
        )

    def test_invalid_policies_and_hybrid_models_fail_without_mask_mutation(self):
        for method, depth in (
            ("partial", None),
            ("partial", 0),
            ("partial", -1),
            ("partial", 3),
            ("partial", True),
            ("partial", 1.0),
            ("full", 2),
            ("linear", 0),
            ("unknown", None),
        ):
            flags = {n: p.requires_grad for n, p in self.source.named_parameters()}
            with self.subTest(method=method, depth=depth), self.assertRaises(ValueError):
                configure_labram_tuning(self.source, method=method, partial_depth=depth)
            self.assertEqual(flags, {n: p.requires_grad for n, p in self.source.named_parameters()})
        for kind in ("adapter", "lora"):
            hybrid = copy.deepcopy(self.source)
            if kind == "adapter":
                inject_labram_adapters(
                    hybrid, target_modules=("backbone.blocks.1",), bottleneck_dim=4
                )
            else:
                inject_labram_qkv_lora(
                    hybrid, target_modules=("backbone.blocks.1.attn.qkv",), rank=4, alpha=8
                )
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                configure_labram_tuning(hybrid, method="full")

    def test_invalid_support_and_nonfinite_loss_leave_source_unchanged(self):
        for inputs, labels, steps, rate in (
            (self.support, torch.tensor([0, 0]), 1, 0.001),
            (self.support, self.labels.float(), 1, 0.001),
            (self.support[:, :2], self.labels, 1, 0.001),
            (self.support * float("nan"), self.labels, 1, 0.001),
            (self.support, self.labels, True, 0.001),
            (self.support, self.labels, 1, float("inf")),
        ):
            with self.subTest(steps=steps, rate=rate), self.assertRaises(ValueError):
                adapt_labram_tuning_support(
                    self.source, inputs, labels, method="linear", steps=steps, learning_rate=rate
                )
        with torch.no_grad():
            self.source.head.bias.fill_(float("inf"))
        before = copy.deepcopy(self.source.state_dict())
        with self.assertRaisesRegex(ValueError, "nonfinite support loss"):
            adapt_labram_tuning_support(
                self.source,
                self.support,
                self.labels,
                method="linear",
                steps=1,
                learning_rate=0.001,
            )
        self.assert_state_equal(self.source.state_dict(), before)
