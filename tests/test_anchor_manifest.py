from __future__ import annotations

import copy
import unittest
from dataclasses import asdict, replace
from unittest.mock import patch

import numpy as np
import test_labram_manifest as fixtures
import torch

from adaptation.anchor_manifest import (
    BCIAnchorManifestRunner,
    EATangentAnchorSettings,
    EEGNetAnchorSettings,
)
from evaluation.alignment import EuclideanAlignment
from evaluation.baselines import TangentSpaceLogistic
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import (
    load_bci_profile_a_subject,
    load_bci_profile_b_episode,
)
from evaluation.phase2_records import envelope


class AnchorManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        from braindecode.models import EEGNet

        fixtures.LaBraMManifestTests.setUp(self)
        self.eegnet = EEGNet(
            n_chans=22, n_outputs=4, n_times=512, sfreq=128, final_layer_with_constraint=True
        )
        self.manifests = {n: v.profile_a_manifest_sha256 for n, v in self.assets.items()}
        self.eeg_settings = EEGNetAnchorSettings(1, 0.001, 1e6, 2)
        self.ea_settings = EATangentAnchorSettings(1e-6, 1.0, 1000, 2)

    tearDown = fixtures.LaBraMManifestTests.tearDown

    def runner(self, **kwargs):
        return BCIAnchorManifestRunner(
            self.root,
            self.config,
            self.catalogs,
            self.selection_record,
            self.manifests,
            eegnet_source=self.eegnet,
            outer_target="subject_01",
            **kwargs,
        )

    def test_both_anchors_match_labram_trial_ids_at_every_shot_level(self):
        runner = self.runner()
        for shots in (1, 5, 10, 20):
            b = load_bci_profile_b_episode(
                self.root,
                self.config,
                self.catalogs[0],
                self.records["subject_01"],
                shots_per_class=shots,
                **asdict(self.assets["subject_01"]),
            )
            for settings in (self.eeg_settings, self.ea_settings):
                with self.subTest(shots=shots, method=type(settings).__name__):
                    result = runner.predict_target(
                        self.records["subject_01"], shots_per_class=shots, settings=settings
                    )
                    self.assertEqual(result.support_trial_ids, b.binding.support_trial_ids)
                    self.assertEqual(result.query_trial_ids, b.binding.query_trial_ids)
                    self.assertEqual(result.episode_sha256, b.binding.episode_sha256)
                    self.assertEqual(result.probabilities.shape, (4, 4))
                    np.testing.assert_array_equal(result.targets, b.query_labels)
                    self.assertTrue(np.isfinite(result.probabilities).all())
                    self.assertTrue(result.engineering_only)

    def test_eegnet_updates_parameters_preserves_buffers_caller_and_repeat(self):
        self.eegnet.conv_temporal.weight.grad = torch.ones_like(self.eegnet.conv_temporal.weight)
        initial = copy.deepcopy(self.eegnet.state_dict())
        modes = {n: m.training for n, m in self.eegnet.named_modules()}
        flags = {n: p.requires_grad for n, p in self.eegnet.named_parameters()}
        runner = self.runner()
        seen = []

        def observe(module, args):
            if torch.is_grad_enabled():
                seen.append(args[0].detach().clone())
            self.assertFalse(any(m.training for m in module.modules()))
            for name, value in module.named_buffers():
                self.assertTrue(torch.equal(value, initial[name]), name)

        runner._eegnet.register_forward_pre_hook(observe)
        rng = torch.random.get_rng_state()
        first = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=self.eeg_settings
        )
        second = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=self.eeg_settings
        )
        data = load_bci_profile_a_subject(
            self.root,
            self.config,
            self.catalogs[0],
            profile_a_manifest_sha256=self.manifests["subject_01"],
        )
        np.testing.assert_array_equal(seen[0].numpy(), data.signals[:4] * 1e6)
        self.assertEqual(len(seen), 2)
        self.assertNotEqual(first.fitted_state_sha256, first.source_state_sha256)
        self.assertEqual(first.fitted_state_sha256, second.fitted_state_sha256)
        np.testing.assert_array_equal(first.probabilities, second.probabilities)
        for name, value in self.eegnet.state_dict().items():
            self.assertTrue(torch.equal(value, initial[name]), name)
        self.assertEqual(modes, {n: m.training for n, m in self.eegnet.named_modules()})
        self.assertEqual(flags, {n: p.requires_grad for n, p in self.eegnet.named_parameters()})
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertTrue(
            torch.equal(
                self.eegnet.conv_temporal.weight.grad,
                torch.ones_like(self.eegnet.conv_temporal.weight),
            )
        )

    def test_ea_matches_independent_source_plus_support_recipe(self):
        runner = self.runner(validation_subject="subject_02")
        result = runner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=self.ea_settings
        )
        signals, labels = [], []
        for name in runner.training_subjects:
            c = self.catalogs[int(name[-2:]) - 1]
            data = load_bci_profile_a_subject(
                self.root, self.config, c, profile_a_manifest_sha256=self.manifests[name]
            )
            signals.append(EuclideanAlignment().fit_transform(data.signals))
            labels.append(data.labels)
        data = load_bci_profile_a_subject(
            self.root,
            self.config,
            self.catalogs[1],
            profile_a_manifest_sha256=self.manifests["subject_02"],
        )
        target = EuclideanAlignment().fit(data.signals[:4])
        signals.append(target.transform(data.signals[:4]))
        labels.append(data.labels[:4])
        decoder = TangentSpaceLogistic().fit(np.concatenate(signals), np.concatenate(labels))
        expected = decoder.predict_proba(target.transform(data.signals[80:]))
        np.testing.assert_allclose(result.probabilities, expected, rtol=1e-6, atol=1e-7)
        np.testing.assert_array_equal(result.fit["target_whitener"], target.whitener_)
        self.assertEqual(
            set(result.fit["source_trial_ids"]), {f"subject_{i:02d}" for i in range(3, 10)}
        )
        self.assertTrue(all(len(ids) == 84 for ids in result.fit["source_trial_ids"].values()))

    def test_query_labels_and_signals_cannot_change_either_fit(self):
        runner = self.runner()
        original = load_bci_profile_a_subject
        for settings in (self.eeg_settings, self.ea_settings):
            first = runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=settings
            )

            def changed(*args, **kwargs):
                data = original(*args, **kwargs)
                if args[2].subject == "subject_01":
                    labels = data.labels.copy()
                    labels[80:] = (labels[80:] + 1) % 4
                    signals = data.signals.copy()
                    signals[80:] *= 10
                    return replace(data, labels=labels, signals=signals)
                return data

            with patch(
                "adaptation.anchor_manifest.load_bci_profile_a_subject", side_effect=changed
            ):
                second = runner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=settings
                )
            self.assertEqual(first.fitted_state_sha256, second.fitted_state_sha256)
            self.assertEqual(first.fit, second.fit)
            self.assertFalse(np.array_equal(first.targets, second.targets))

    def test_roles_selection_and_assets_fail_before_fit(self):
        final, inner = self.runner(), self.runner(validation_subject="subject_02")
        with patch("adaptation.anchor_manifest.load_bci_profile_a_subject") as load:
            for runner, method, subject in (
                (inner, "predict_target", "subject_01"),
                (final, "predict_validation", "subject_02"),
                (inner, "predict_validation", "subject_01"),
                (inner, "predict_validation", "subject_03"),
            ):
                with self.subTest(method=method, subject=subject), self.assertRaises(ValueError):
                    getattr(runner, method)(
                        self.records[subject], shots_per_class=1, settings=self.ea_settings
                    )
            load.assert_not_called()
        payload = copy.deepcopy(self.selection_record["payload"])
        payload["source_subjects"].append("subject_01")
        self.selection_record = envelope("source_selection", payload)
        with self.assertRaisesRegex(ValueError, "selection"):
            self.runner()
        self.selection_record = envelope("source_selection", asdict(self.selection))
        with self.assertRaisesRegex(ValueError, "inner validation"):
            self.runner(validation_subject="subject_01")
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_01.manifest.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "pinned am"):
            final.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.eeg_settings
            )

    def test_query_state_mutation_and_nonfinite_output_rejected(self):
        runner = self.runner()

        def mutate(module, args):
            if not torch.is_grad_enabled():
                module.bnorm_1.running_mean.add_(1)

        runner._eegnet.register_forward_pre_hook(mutate)
        with self.assertRaisesRegex(ValueError, "model state"):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.eeg_settings
            )
        self.assertEqual(state_digest(runner._eegnet), runner._source_sha)
        original = TangentSpaceLogistic.predict_proba

        def corrupt(decoder, epochs):
            result = original(decoder, epochs)
            decoder.tangent.reference_[0, 0] += 1
            return result

        with (
            patch.object(TangentSpaceLogistic, "predict_proba", corrupt),
            self.assertRaisesRegex(ValueError, "fitted state"),
        ):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.ea_settings
            )
        with patch.object(
            TangentSpaceLogistic, "predict_proba", return_value=np.full((2, 4), np.nan)
        ), self.assertRaisesRegex(ValueError, "invalid anchor probabilities"):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.ea_settings
            )

    def test_bad_settings_and_source_contract(self):
        for args in ((True, 0.01, 1e6), (1, float("nan"), 1e6), (1, 0.01, True), (1, 0.01, 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                EEGNetAnchorSettings(*args)
        for args in ((True, 1.0, 1000), (1e-6, float("inf"), 1000), (1e-6, 1.0, True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                EATangentAnchorSettings(*args)
        self.eegnet.double()
        with self.assertRaisesRegex(ValueError, "CPU float32"):
            self.runner()

    def test_source_bytes_changed_after_construction_fail_before_classifier_fit(self):
        runner = self.runner()
        path = self.root / "data/processed/bci_iv_2a/profile_a/subject_03.npz"
        path.write_bytes(path.read_bytes() + b"changed")
        with (
            patch("adaptation.anchor_manifest.TangentSpaceLogistic") as decoder,
            self.assertRaisesRegex(ValueError, "pinned a"),
        ):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.ea_settings
            )
        decoder.return_value.classifier.fit.assert_not_called()

    def test_profile_b_not_required_and_changed_profile_a_contract_rejected(self):
        directory = self.root / "data/processed/bci_iv_2a/profile_b"
        assert directory.resolve().is_relative_to(self.root.resolve())
        directory.rename(directory.with_name("unused_b"))
        runner = self.runner()
        for settings in (self.eeg_settings, self.ea_settings):
            result = runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=settings
            )
            self.assertEqual(result.probabilities.shape, (4, 4))
        path = self.root / "configs/base.toml"
        path.write_text(path.read_text().replace("resample_hz = 128.0", "resample_hz = 129.0"))
        with self.assertRaisesRegex(ValueError, "base Profile A"):
            runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=self.eeg_settings
            )
