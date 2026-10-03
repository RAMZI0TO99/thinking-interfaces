from __future__ import annotations

import copy
import unittest

import torch

from adaptation.labram_prompt import (
    ClassPrototypePromptGenerator,
    SupportPromptedLaBraM,
    adapt_labram_prompt_support,
    prompted_labram_logits,
)
from encoder.labram import LaBraMClassifier


class LaBraMPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        from braindecode.models import Labram

        torch.manual_seed(53)
        self.source = LaBraMClassifier(
            Labram(n_times=200, n_chans=3, n_outputs=0, num_layers=2, drop_prob=0.2),
            classes=2,
            channel_names=("C3", "Cz", "C4"),
        )
        self.generator = ClassPrototypePromptGenerator(
            embedding_dim=200, classes=2, prompt_tokens=3, hidden_dim=16
        )
        self.support = torch.randn(2, 3, 200) * 0.1
        self.labels = torch.tensor([0, 1])
        self.query = torch.randn(3, 3, 200) * 0.1

    def assert_state_equal(self, left, right):
        self.assertEqual(set(left), set(right))
        for name in left:
            torch.testing.assert_close(left[name], right[name], rtol=0, atol=0)

    def test_empty_prefix_matches_real_forward_and_added_tokens_reach_every_block(self):
        self.source.eval()
        with torch.inference_mode():
            torch.testing.assert_close(
                prompted_labram_logits(self.source, self.query, torch.empty(1, 0, 200)),
                self.source(self.query),
                rtol=0,
                atol=0,
            )
        episode = SupportPromptedLaBraM(self.source, self.generator, self.support, self.labels)
        lengths, seen_cls = [], []

        def observe(module, args):
            lengths.append(args[0].shape[1])
            seen_cls.append(args[0][:, 0].detach().clone())

        handles = [b.register_forward_pre_hook(observe) for b in episode.classifier.backbone.blocks]
        try:
            output = episode(self.query)
        finally:
            for handle in handles:
                handle.remove()
        self.assertEqual(lengths, [7, 7])  # CLS + 3 prompts + 3 EEG patches
        self.assertEqual(output.shape, (3, 2))
        expected_cls = (
            self.source.backbone.cls_token + self.source.backbone.position_embedding[:, :1]
        ).expand(3, -1, -1)[:, 0]
        torch.testing.assert_close(seen_cls[0], expected_cls, rtol=0, atol=0)
        self.assertFalse(torch.equal(output, self.source(self.query)))

    def test_label_association_signal_changes_and_joint_support_order(self):
        original = SupportPromptedLaBraM(self.source, self.generator, self.support, self.labels)
        swapped = SupportPromptedLaBraM(
            self.source, self.generator, self.support, self.labels.flip(0)
        )
        reordered = SupportPromptedLaBraM(
            self.source, self.generator, self.support.flip(0), self.labels.flip(0)
        )
        changed = SupportPromptedLaBraM(
            self.source, self.generator, self.support + torch.randn_like(self.support), self.labels
        )
        self.assertFalse(torch.allclose(original.generated_prompts(), swapped.generated_prompts()))
        self.assertFalse(torch.allclose(original(self.query), swapped(self.query)))
        self.assertFalse(torch.equal(original.generated_prompts(), changed.generated_prompts()))
        torch.testing.assert_close(
            original.generated_prompts(), reordered.generated_prompts(), rtol=1e-5, atol=1e-6
        )

    def test_query_context_is_copied_and_frozen_for_batch_and_single_predictions(self):
        episode = SupportPromptedLaBraM(self.source, self.generator, self.support, self.labels)
        before = copy.deepcopy(episode.state_dict())
        prompts = episode.generated_prompts().detach().clone()
        self.support.zero_()
        self.labels.fill_(1)
        with torch.inference_mode():
            whole = episode(self.query)
            separate = torch.cat([episode(row.unsqueeze(0)) for row in self.query])
            episode(self.query * 100)
        torch.testing.assert_close(whole, separate, rtol=1e-4, atol=1e-5)
        self.assert_state_equal(episode.state_dict(), before)
        torch.testing.assert_close(prompts, episode.generated_prompts(), rtol=0, atol=0)
        self.assertFalse(episode.support_features.requires_grad)
        episode.train()
        with self.assertRaises(ValueError):
            episode(self.query)  # no silent dropout-enabled query path

    def test_one_shot_updates_generator_and_explicit_head_with_exact_reset(self):
        source_before = copy.deepcopy(self.source.state_dict())
        generator_before = copy.deepcopy(self.generator.state_dict())
        source_modes = {n: m.training for n, m in self.source.named_modules()}
        initial = SupportPromptedLaBraM(self.source, self.generator, self.support, self.labels)
        initial_state = copy.deepcopy(initial.state_dict())
        for train_head in (False, True):
            with self.subTest(train_head=train_head):
                result = adapt_labram_prompt_support(
                    self.source,
                    self.generator,
                    self.support,
                    self.labels,
                    steps=2,
                    learning_rate=0.001,
                    train_head=train_head,
                )
                changed = {
                    n
                    for n, t in result.model.state_dict().items()
                    if not torch.equal(t, initial_state[n])
                }
                expected = {
                    n
                    for n, _ in result.model.named_parameters()
                    if n.startswith("generator.")
                    or (train_head and n.startswith("classifier.head."))
                }
                self.assertEqual(expected, set(result.trainable_names))
                self.assertTrue(changed <= expected)
                self.assertIn("generator.network.0.weight", changed)
                self.assertIn("generator.network.2.weight", changed)
                self.assertEqual("classifier.head.weight" in changed, train_head)
                self.assertFalse(
                    torch.equal(result.model.generated_prompts(), initial.generated_prompts())
                )
                self.assertFalse(torch.equal(result.model(self.query), initial(self.query)))
                self.assertFalse(any(m.training for m in result.model.modules()))
                self.assertTrue(all(p.grad is None for p in result.model.parameters()))
                repeated = adapt_labram_prompt_support(
                    self.source,
                    self.generator,
                    self.support,
                    self.labels,
                    steps=2,
                    learning_rate=0.001,
                    train_head=train_head,
                )
                self.assertEqual(result.losses, repeated.losses)
                self.assert_state_equal(result.model.state_dict(), repeated.model.state_dict())
                restored = SupportPromptedLaBraM(
                    self.source, self.generator, self.support, self.labels
                )
                restored.load_state_dict(result.model.state_dict(), strict=True)
                torch.testing.assert_close(
                    restored(self.query), result.model(self.query), rtol=0, atol=0
                )
        self.assert_state_equal(self.source.state_dict(), source_before)
        self.assert_state_equal(self.generator.state_dict(), generator_before)
        self.assertEqual(source_modes, {n: m.training for n, m in self.source.named_modules()})

    def test_missing_classes_and_invalid_support_or_prompts_are_rejected(self):
        for signals, labels in (
            (self.support, torch.tensor([0, 0])),
            (self.support, self.labels.float()),
            (self.support * float("nan"), self.labels),
            (self.support[:, :2], self.labels),
        ):
            with self.subTest(shape=signals.shape), self.assertRaises(ValueError):
                SupportPromptedLaBraM(self.source, self.generator, signals, labels)
        self.source.eval()
        for prompts in (
            torch.zeros(2, 3, 200),
            torch.zeros(1, 3, 20),
            torch.full((1, 3, 200), float("nan")),
        ):
            with self.subTest(shape=prompts.shape), self.assertRaises(ValueError):
                prompted_labram_logits(self.source, self.query, prompts)
        with self.assertRaises(ValueError):
            adapt_labram_prompt_support(
                self.source,
                self.generator,
                self.support,
                self.labels,
                steps=True,
                learning_rate=0.01,
                train_head=False,
            )

    def test_class_means_weight_classes_equally_and_preserve_label_associations(self):
        features = torch.randn(4, 200)
        labels = torch.tensor([0, 0, 1, 1])
        expected = self.generator(features, labels)
        order = torch.tensor([3, 0, 2, 1])
        torch.testing.assert_close(self.generator(features[order], labels[order]), expected)
        repeated_features = torch.cat((features[:2], features[:2], features[2:]))
        torch.testing.assert_close(
            self.generator(repeated_features, torch.tensor([0, 0, 0, 0, 1, 1])), expected
        )
        self.assertFalse(torch.allclose(self.generator(features, labels.flip(0)), expected))
