from __future__ import annotations

import copy
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

import test_labram_manifest as fixtures
import torch

from adaptation.labram_manifest import LaBraMPromptSettings
from adaptation.labram_prompt import adapt_labram_prompt_support
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import load_bci_profile_b_episode


class LaBraMPromptManifestTests(unittest.TestCase):
    # Reuse the complete nine-subject, real installed-model fixture, not its tests.
    setUp = fixtures.LaBraMManifestTests.setUp
    tearDown = fixtures.LaBraMManifestTests.tearDown
    runner = fixtures.LaBraMManifestTests.runner

    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def settings(self, **kwargs):
        return LaBraMPromptSettings(
            **(
                {
                    "prompt_tokens": 2,
                    "hidden_dim": 8,
                    "seed": 11,
                    "train_head": True,
                    "steps": 1,
                    "learning_rate": 0.01,
                    "query_batch_size": 2,
                }
                | kwargs
            )
        )

    def bound(self):
        return load_bci_profile_b_episode(
            self.root,
            self.config,
            self.catalogs[0],
            self.records["subject_01"],
            shots_per_class=1,
            **asdict(self.assets["subject_01"]),
        )

    def test_all_shots_bind_only_support_and_keep_fixed_queries(self):
        runner = self.runner()
        for shots in (1, 5, 10, 20):
            with (
                self.subTest(shots=shots),
                patch(
                    "adaptation.labram_manifest.adapt_labram_prompt_support",
                    wraps=adapt_labram_prompt_support,
                ) as adapt,
            ):
                result = runner.predict_target(
                    self.records["subject_01"], shots_per_class=shots, settings=self.settings()
                )
                self.assertEqual(adapt.call_args.args[2].shape, (4 * shots, 22, 800))
                self.assertEqual(adapt.call_args.args[3].shape, (4 * shots,))
                self.assertEqual(result.logits.shape, (4, 4))
                self.assertTrue(torch.isfinite(result.logits).all())
                self.assertEqual(result.targets.tolist(), [0, 1, 2, 3])
                self.assertEqual(
                    result.binding.query_trial_ids, self.bound().binding.query_trial_ids
                )
                self.assertEqual(result.mask.method, "support_prompt")
                self.assertEqual(result.mask.generator_parameters, 10008)
                self.assertEqual(result.mask.trainable_parameters, 10812)
                self.assertTrue(result.engineering_only)
                self.assertFalse(result.source_training_history_verified)

    def test_only_generator_and_explicit_head_change_with_frozen_support_context(self):
        initial = copy.deepcopy(self.model.state_dict())
        self.model.head.weight.grad = torch.ones_like(self.model.head.weight)
        modes = {n: m.training for n, m in self.model.named_modules()}
        flags = {n: p.requires_grad for n, p in self.model.named_parameters()}
        runner = self.runner()
        for head in (False, True):
            captured = []

            def checked(source, generator, inputs, labels, head=head, captured=captured, **kwargs):
                generator_before = copy.deepcopy(generator.state_dict())
                result = adapt_labram_prompt_support(source, generator, inputs, labels, **kwargs)
                expected = {f"generator.{n}" for n in generator_before}
                if head:
                    expected.update(("classifier.head.weight", "classifier.head.bias"))
                self.assertEqual(set(result.trainable_names), expected)
                for name, value in result.model.classifier.state_dict().items():
                    if not (head and name.startswith("head.")):
                        self.assertTrue(torch.equal(value, initial[name]), name)
                self.assertEqual(
                    torch.equal(result.model.classifier.head.weight, initial["head.weight"]),
                    not head,
                )
                for name in ("network.0.weight", "network.2.weight"):
                    self.assertFalse(
                        torch.equal(
                            result.model.generator.state_dict()[name], generator_before[name]
                        )
                    )
                self.assertTrue(torch.equal(result.model.support_labels, labels))
                with torch.no_grad():
                    features = torch.cat(
                        [
                            source.backbone(
                                trial.unsqueeze(0),
                                ch_names=list(source.channel_names),
                                return_features=True,
                            )["cls_token"]
                            for trial in inputs
                        ]
                    )
                self.assertTrue(torch.equal(result.model.support_features, features))
                self.assertFalse(any(m.training for m in result.model.modules()))
                self.assertTrue(all(p.grad is None for p in result.model.parameters()))
                for name, value in generator.state_dict().items():
                    self.assertTrue(torch.equal(value, generator_before[name]))
                captured.append(result)
                return result

            rng = torch.random.get_rng_state()
            with (
                self.subTest(train_head=head),
                patch(
                    "adaptation.labram_manifest.adapt_labram_prompt_support", side_effect=checked
                ),
            ):
                prediction = runner.predict_target(
                    self.records["subject_01"],
                    shots_per_class=1,
                    settings=self.settings(train_head=head, steps=2),
                )
            self.assertEqual(prediction.adapted_state_sha256, state_digest(captured[0].model))
            self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        for name, value in self.model.state_dict().items():
            self.assertTrue(torch.equal(value, initial[name]), name)
        self.assertEqual(modes, {n: m.training for n, m in self.model.named_modules()})
        self.assertEqual(flags, {n: p.requires_grad for n, p in self.model.named_parameters()})
        self.assertTrue(
            torch.equal(self.model.head.weight.grad, torch.ones_like(self.model.head.weight))
        )

    def test_repeat_reset_seed_identity_and_query_labels_are_isolated(self):
        runner = self.runner()
        bound = self.bound()
        settings = self.settings()
        rng = torch.random.get_rng_state()
        first = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=settings
        )
        with torch.no_grad():
            self.model.head.bias.add_(10)
        changed = replace(bound, query_labels=(bound.query_labels + 1) % 4)
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode", return_value=changed):
            repeat = runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=settings
            )
        self.assertEqual(first.support_losses, repeat.support_losses)
        self.assertEqual(first.adapted_state_sha256, repeat.adapted_state_sha256)
        self.assertTrue(torch.equal(first.logits, repeat.logits))
        self.assertFalse(torch.equal(first.targets, repeat.targets))
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        other = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=replace(settings, seed=23)
        )
        self.assertNotEqual(first.settings.sha256, other.settings.sha256)
        self.assertNotEqual(first.adapted_state_sha256, other.adapted_state_sha256)
        self.assertFalse(torch.equal(first.logits, other.logits))

    def test_prompt_roles_and_wrong_subjects_fail_before_adaptation(self):
        final, inner = self.runner(), self.runner(validation_subject="subject_02")
        settings = self.settings()
        with patch("adaptation.labram_manifest.adapt_labram_prompt_support") as adapt:
            for runner, method, subject in (
                (inner, "predict_target", "subject_01"),
                (final, "predict_validation", "subject_02"),
                (inner, "predict_validation", "subject_01"),
                (inner, "predict_validation", "subject_03"),
            ):
                with self.subTest(method=method, subject=subject), self.assertRaises(ValueError):
                    getattr(runner, method)(
                        self.records[subject], shots_per_class=1, settings=settings
                    )
            adapt.assert_not_called()

        result = inner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=settings
        )
        self.assertEqual(result.role, "inner_validation")
        self.assertEqual(inner.training_subjects, tuple(f"subject_{i:02d}" for i in range(3, 10)))

    def test_failed_initialization_restores_rng_and_source(self):
        runner = self.runner()
        rng = torch.random.get_rng_state()
        source = state_digest(self.model)

        def fail(*args, **kwargs):
            torch.rand(7)
            raise ValueError("initialization failed")

        with (
            patch("adaptation.labram_manifest.ClassPrototypePromptGenerator", side_effect=fail),
            patch("adaptation.labram_manifest.adapt_labram_prompt_support") as adapt,
            self.assertRaisesRegex(ValueError, "initialization failed"),
        ):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.settings()
            )
        adapt.assert_not_called()
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertEqual(state_digest(self.model), source)
        self.assertEqual(state_digest(runner._source), runner._source_sha)

    def test_bad_settings_and_unsupported_encoder_fail_before_binding(self):
        for kwargs in (
            {"prompt_tokens": 0},
            {"prompt_tokens": True},
            {"hidden_dim": 0},
            {"hidden_dim": True},
            {"learning_rate": float("nan")},
            {"learning_rate": True},
            {"steps": True},
            {"seed": -1},
            {"seed": True},
            {"seed": 2**63},
            {"train_head": 1},
            {"query_batch_size": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.settings(**kwargs)
        self.model.backbone.fc_norm = torch.nn.LayerNorm(200)
        runner = self.runner()
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode") as bind:
            with self.assertRaisesRegex(ValueError, "CLS-head"):
                runner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=self.settings()
                )
            bind.assert_not_called()

    def test_changed_assets_and_query_mutation_fail_closed(self):
        runner = self.runner()
        for failure in ("state", "context", "nonfinite"):

            def corrupted(*args, failure=failure, **kwargs):
                result = adapt_labram_prompt_support(*args, **kwargs)
                forward = result.model.classifier.head.forward

                def bad_forward(inputs):
                    if failure == "state":
                        result.model.classifier.head.bias.add_(1)
                        return forward(inputs)
                    if failure == "context":
                        result.model.support_features.add_(1)
                        return forward(inputs)
                    return forward(inputs) * float("nan")

                result.model.classifier.head.forward = bad_forward
                return result

            with (
                patch(
                    "adaptation.labram_manifest.adapt_labram_prompt_support", side_effect=corrupted
                ),
                self.subTest(failure=failure),
                self.assertRaisesRegex(ValueError, "model state|invalid query logits"),
            ):
                runner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=self.settings()
                )
            self.assertEqual(state_digest(runner._source), runner._source_sha)
        path = self.root / "data/processed/bci_iv_2a/profile_b/subject_01.manifest.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with patch("adaptation.labram_manifest.adapt_labram_prompt_support") as adapt:
            with self.assertRaisesRegex(ValueError, "pinned bm"):
                runner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=self.settings()
                )
            adapt.assert_not_called()
