from __future__ import annotations

import copy
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

import test_labram_manifest as fixtures
import torch

from adaptation.labram_adapter import adapt_labram_adapter_support
from adaptation.labram_manifest import LaBraMAdapterSettings
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import load_bci_profile_b_episode


class LaBraMAdapterManifestTests(unittest.TestCase):
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
        return LaBraMAdapterSettings(
            **(
                {
                    "target_modules": ("backbone.blocks.1",),
                    "bottleneck_dim": 4,
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
                    "adaptation.labram_manifest.adapt_labram_adapter_support",
                    wraps=adapt_labram_adapter_support,
                ) as adapt,
            ):
                result = runner.predict_target(
                    self.records["subject_01"], shots_per_class=shots, settings=self.settings()
                )
                self.assertEqual(adapt.call_args.args[1].shape, (4 * shots, 22, 800))
                self.assertEqual(adapt.call_args.args[2].shape, (4 * shots,))
                self.assertEqual(result.logits.shape, (4, 4))
                self.assertTrue(torch.isfinite(result.logits).all())
                self.assertEqual(result.targets.tolist(), [0, 1, 2, 3])
                self.assertEqual(
                    result.binding.query_trial_ids, self.bound().binding.query_trial_ids
                )
                self.assertEqual(result.mask.method, "adapter")
                self.assertEqual(result.mask.injection.adapter_parameters, 1804)
                self.assertEqual(result.mask.trainable_parameters, 2608)
                self.assertTrue(result.engineering_only)
                self.assertFalse(result.source_training_history_verified)

    def test_only_selected_adapters_and_explicit_head_change(self):
        initial = copy.deepcopy(self.model.state_dict())
        self.model.head.weight.grad = torch.ones_like(self.model.head.weight)
        modes = {n: m.training for n, m in self.model.named_modules()}
        flags = {n: p.requires_grad for n, p in self.model.named_parameters()}
        runner = self.runner()
        for head in (False, True):
            captured = []

            def checked(template, inputs, labels, head=head, captured=captured, **kwargs):
                before = copy.deepcopy(template.state_dict())
                result = adapt_labram_adapter_support(template, inputs, labels, **kwargs)
                changed = {
                    n for n, v in result.model.state_dict().items() if not torch.equal(v, before[n])
                }
                expected = {
                    "backbone.blocks.1.adapter.down.weight",
                    "backbone.blocks.1.adapter.down.bias",
                    "backbone.blocks.1.adapter.up.weight",
                    "backbone.blocks.1.adapter.up.bias",
                } | ({"head.weight", "head.bias"} if head else set())
                self.assertEqual(set(result.trainable_names), expected)
                self.assertTrue(changed <= expected)
                self.assertIn("backbone.blocks.1.adapter.up.weight", changed)
                self.assertIn("backbone.blocks.1.adapter.down.weight", changed)
                self.assertEqual("head.weight" in changed, head)
                for name, value in result.model.state_dict().items():
                    if ".adapter." not in name and name not in expected:
                        original = name.replace("backbone.blocks.1.block.", "backbone.blocks.1.")
                        self.assertTrue(torch.equal(value, initial[original]), name)
                self.assertFalse(any(m.training for m in result.model.modules()))
                self.assertTrue(all(p.grad is None for p in result.model.parameters()))
                captured.append(result)
                return result

            rng = torch.random.get_rng_state()
            with (
                self.subTest(train_head=head),
                patch(
                    "adaptation.labram_manifest.adapt_labram_adapter_support", side_effect=checked
                ),
            ):
                prediction = runner.predict_target(
                    self.records["subject_01"],
                    shots_per_class=1,
                    settings=self.settings(train_head=head, steps=3),
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

    def test_adapter_roles_and_wrong_subjects_fail_before_adaptation(self):
        final, inner = self.runner(), self.runner(validation_subject="subject_02")
        settings = self.settings()
        with patch("adaptation.labram_manifest.adapt_labram_adapter_support") as adapt:
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
            patch("adaptation.labram_manifest.inject_labram_adapters", side_effect=fail),
            patch("adaptation.labram_manifest.adapt_labram_adapter_support") as adapt,
            self.assertRaisesRegex(ValueError, "initialization failed"),
        ):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.settings()
            )
        adapt.assert_not_called()
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertEqual(state_digest(self.model), source)
        self.assertEqual(state_digest(runner._source), runner._source_sha)

    def test_bad_settings_and_dimensions_fail_before_binding(self):
        for kwargs in (
            {"bottleneck_dim": True},
            {"bottleneck_dim": 0},
            {"learning_rate": float("inf")},
            {"seed": -1},
            {"seed": True},
            {"seed": 2**63},
            {"train_head": 1},
            {"steps": 0},
            {"target_modules": []},
            {"target_modules": ("head",)},
            {"target_modules": ("backbone.blocks.1",) * 2},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.settings(**kwargs)
        runner = self.runner()
        for settings in (
            self.settings(bottleneck_dim=200),
            self.settings(target_modules=("backbone.blocks.2",)),
        ):
            with patch("adaptation.labram_manifest.load_bci_profile_b_episode") as bind:
                with self.assertRaises(ValueError):
                    runner.predict_target(
                        self.records["subject_01"], shots_per_class=1, settings=settings
                    )
                bind.assert_not_called()

    def test_changed_assets_and_query_mutation_fail_closed(self):
        runner = self.runner()
        for failure in ("state", "nonfinite"):

            def corrupted(*args, failure=failure, **kwargs):
                result = adapt_labram_adapter_support(*args, **kwargs)
                forward = result.model.head.forward

                def bad_forward(inputs):
                    if failure == "state":
                        result.model.head.bias.add_(1)
                        return forward(inputs)
                    return forward(inputs) * float("nan")

                result.model.head.forward = bad_forward
                return result

            with (
                patch(
                    "adaptation.labram_manifest.adapt_labram_adapter_support", side_effect=corrupted
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
        with patch("adaptation.labram_manifest.adapt_labram_adapter_support") as adapt:
            with self.assertRaisesRegex(ValueError, "pinned bm"):
                runner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=self.settings()
                )
            adapt.assert_not_called()
