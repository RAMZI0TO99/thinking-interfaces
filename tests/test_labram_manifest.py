from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from adaptation.labram_manifest import (
    BCIProfileAssets,
    LaBraMTuningManifestRunner,
    LaBraMTuningSettings,
)
from adaptation.labram_tuning import adapt_labram_tuning_support
from core.config import config_digest, load_toml
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import (
    BCI_CHANNELS,
    BCI_CLASSES,
    load_bci_profile_b_episode,
)
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog


class LaBraMManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(2)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        from braindecode.models import Labram

        self.rng = torch.random.get_rng_state()
        torch.manual_seed(23)
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        for name in ("base.toml", "benchmark.toml"):
            (self.root / "configs" / name).write_bytes((Path("configs") / name).read_bytes())
        ceiling = self.root / "configs/phase2"
        ceiling.mkdir(parents=True, exist_ok=True)
        (ceiling / "selection_ceiling.toml").write_bytes(
            Path("configs/phase2/selection_ceiling.toml").read_bytes()
        )
        self.config = load_toml("configs/phase2/protocol.toml")
        base = load_toml("configs/base.toml")["preprocessing"]
        threshold_path = self.root / "configs/benchmark.toml"
        threshold = load_toml(threshold_path)["datasets"]["bci_iv_2a"]["artifact_threshold_volts"]
        preprocessing = config_digest(
            {
                "profile_identity": self.config["preparation"]["profile_identity"],
                "threshold_config_sha256": file_digest(threshold_path),
                "dataset": "bci_iv_2a",
                "threshold": threshold,
            }
        )
        self.catalogs, self.assets, self.records = [], {}, {}
        generator = np.random.default_rng(23)
        for profile, samples in (("a", 512), ("b", 800)):
            directory = self.root / f"data/processed/bci_iv_2a/profile_{profile}"
            directory.mkdir(parents=True)
            signals = generator.normal(size=(84, 22, samples)).astype(np.float32)
            signals *= 1e-7 if profile == "a" else 0.1
            cfg = dict(base["profile_" + profile])
            if profile == "a":
                cfg["baseline_duration_s"] = cfg.pop("pre_cue_s")
            for subject in range(1, 10):
                name = f"subject_{subject:02d}"
                np.savez_compressed(
                    directory / (name + ".npz"),
                    signals=signals,
                    labels=np.array(BCI_CLASSES * 21),
                    sessions=np.array(["s"] * 84),
                    runs=np.array(["r"] * 84),
                    trial_indices=np.arange(84),
                    channel_names=np.array(BCI_CHANNELS),
                )
                manifest = dict(
                    artifact_schema_version=1,
                    subject=subject,
                    shape=[84, 22, samples],
                    channel_names=list(BCI_CHANNELS),
                    epoch_duration_s=4.0,
                    sampling_rate_hz=128.0 if profile == "a" else 200.0,
                    config_sha256=config_digest(cfg),
                )
                if profile == "a":
                    manifest["baseline_duration_s"] = 1.0
                else:
                    manifest.update(
                        artifact_kind="profile_b",
                        reference="original",
                        amplitude_unit_mv=0.1,
                        patch_samples=200,
                        patches_per_epoch=4,
                    )
                (directory / (name + ".manifest.json")).write_text(json.dumps(manifest))
        for subject in range(1, 10):
            name = f"subject_{subject:02d}"
            a = self.root / f"data/processed/bci_iv_2a/profile_a/{name}.npz"
            b = self.root / f"data/processed/bci_iv_2a/profile_b/{name}.npz"
            catalog, _ = read_catalog(
                a,
                dataset="bci_iv_2a",
                classes=BCI_CLASSES,
                threshold=threshold,
                preprocessing_sha256=preprocessing,
            )
            self.catalogs.append(catalog)
            self.assets[name] = BCIProfileAssets(
                file_digest(a.with_suffix(".manifest.json")),
                file_digest(b),
                file_digest(b.with_suffix(".manifest.json")),
            )
            self.records[name] = envelope(
                "episode_manifest",
                nested_episode(
                    catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
                ).payload(),
            )
        self.catalogs = tuple(self.catalogs)
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))
        self.model = LaBraMClassifier(
            Labram(
                n_times=800,
                n_chans=22,
                n_outputs=0,
                num_layers=2,
                drop_prob=0.2,
                attn_drop_prob=0.2,
            ),
            classes=4,
            channel_names=BCI_CHANNELS,
        )

    def tearDown(self):
        self.temp.cleanup()
        torch.random.set_rng_state(self.rng)

    def runner(self, **kwargs):
        return LaBraMTuningManifestRunner(
            self.root,
            self.config,
            self.catalogs,
            self.selection_record,
            self.model,
            self.assets,
            outer_target="subject_01",
            **kwargs,
        )

    def test_all_methods_and_shots_use_only_bound_support_and_preserve_common_queries(self):
        runner = self.runner()
        source = state_digest(self.model)
        for method, depth in (("linear", None), ("partial", 1), ("full", None)):
            for shots in (1, 5, 10, 20):
                with self.subTest(method=method, shots=shots):
                    settings = LaBraMTuningSettings(method, 1, 1e-4, depth, 2)
                    with patch(
                        "adaptation.labram_manifest.adapt_labram_tuning_support",
                        wraps=adapt_labram_tuning_support,
                    ) as adapt:
                        result = runner.predict_target(
                            self.records["subject_01"], shots_per_class=shots, settings=settings
                        )
                    support, labels = adapt.call_args.args[1:]
                    self.assertEqual(support.shape, (shots * 4, 22, 800))
                    self.assertEqual(labels.shape, (shots * 4,))
                    self.assertEqual(result.logits.shape, (4, 4))
                    self.assertEqual(result.targets.tolist(), [0, 1, 2, 3])
                    self.assertEqual(
                        result.binding.query_trial_ids,
                        tuple(
                            json.dumps(["s", "r", i], separators=(",", ":")) for i in range(80, 84)
                        ),
                    )
                    self.assertNotEqual(result.adapted_state_sha256, result.source_state_sha256)
                    self.assertEqual(result.source_state_sha256, source)
                    self.assertEqual(len(result.support_losses), 1)
                    self.assertEqual(result.mask.method, method)
                    self.assertTrue(result.engineering_only)
                    self.assertFalse(result.source_training_history_verified)
        self.assertEqual(state_digest(self.model), source)

    def test_role_violations_fail_before_binding_or_adaptation(self):
        final = self.runner()
        inner = self.runner(validation_subject="subject_02")
        self.assertEqual(len(final.training_subjects), 8)
        self.assertEqual(inner.training_subjects, tuple(f"subject_{i:02d}" for i in range(3, 10)))
        settings = LaBraMTuningSettings("linear", 1, 1e-4)
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode") as bind:
            with self.assertRaises(ValueError):
                inner.predict_target(
                    self.records["subject_01"], shots_per_class=1, settings=settings
                )
            with self.assertRaises(ValueError):
                final.predict_validation(
                    self.records["subject_02"], shots_per_class=1, settings=settings
                )
            bind.assert_not_called()
        with patch("adaptation.labram_manifest.adapt_labram_tuning_support") as adapt:
            for record in (self.records["subject_01"], self.records["subject_03"]):
                with self.assertRaises(ValueError):
                    inner.predict_validation(record, shots_per_class=1, settings=settings)
            adapt.assert_not_called()
        result = inner.predict_validation(
            self.records["subject_02"], shots_per_class=1, settings=settings
        )
        self.assertEqual(result.role, "inner_validation")
        self.assertEqual(result.binding.subject, "subject_02")

    def test_source_snapshot_repeat_reset_and_caller_state_preserved(self):
        self.model.head.weight.grad = torch.ones_like(self.model.head.weight)
        state = state_digest(self.model)
        modes = {n: m.training for n, m in self.model.named_modules()}
        flags = {n: p.requires_grad for n, p in self.model.named_parameters()}
        runner = self.runner()
        rng = torch.random.get_rng_state()
        settings = LaBraMTuningSettings("full", 1, 1e-4)
        first = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=settings
        )
        second = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=settings
        )
        self.assertEqual(first.adapted_state_sha256, second.adapted_state_sha256)
        torch.testing.assert_close(first.logits, second.logits, rtol=0, atol=0)
        self.assertEqual(state_digest(self.model), state)
        self.assertEqual(modes, {n: m.training for n, m in self.model.named_modules()})
        self.assertEqual(flags, {n: p.requires_grad for n, p in self.model.named_parameters()})
        self.assertTrue(
            torch.equal(self.model.head.weight.grad, torch.ones_like(self.model.head.weight))
        )
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        with torch.no_grad():
            self.model.head.bias.add_(10)
        third = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=settings
        )
        torch.testing.assert_close(first.logits, third.logits, rtol=0, atol=0)

    def test_query_labels_never_change_adaptation_or_predictions(self):
        runner = self.runner()
        bound = load_bci_profile_b_episode(
            self.root,
            self.config,
            self.catalogs[0],
            self.records["subject_01"],
            shots_per_class=1,
            **asdict(self.assets["subject_01"]),
        )
        settings = LaBraMTuningSettings("partial", 1, 1e-4, 1)
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode", return_value=bound):
            first = runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=settings
            )
        changed = replace(
            bound,
            query_labels=(bound.query_labels + 1) % 4,
            query_signals=bound.query_signals.copy(),
        )
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode", return_value=changed):
            second = runner.predict_target(
                self.records["subject_01"], shots_per_class=1, settings=settings
            )
        self.assertEqual(first.adapted_state_sha256, second.adapted_state_sha256)
        self.assertEqual(first.support_losses, second.support_losses)
        torch.testing.assert_close(first.logits, second.logits, rtol=0, atol=0)
        self.assertFalse(torch.equal(first.targets, second.targets))

    def test_rehashed_selection_tampering_incomplete_assets_and_bad_roles_fail(self):
        payload = copy.deepcopy(self.selection_record["payload"])
        payload["source_subjects"].append("subject_01")
        self.selection_record = envelope("source_selection", payload)
        with self.assertRaisesRegex(ValueError, "selection"):
            self.runner()
        self.selection_record = envelope("source_selection", asdict(self.selection))
        with self.assertRaisesRegex(ValueError, "inner validation"):
            self.runner(validation_subject="subject_01")
        self.assets.pop("subject_09")
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.runner()

    def test_changed_profile_bytes_fail_before_adaptation(self):
        runner = self.runner()
        path = self.root / "data/processed/bci_iv_2a/profile_b/subject_01.manifest.json"
        path.write_text(path.read_text() + "\n")
        with patch("adaptation.labram_manifest.adapt_labram_tuning_support") as adapt:
            with self.assertRaisesRegex(ValueError, "pinned bm"):
                runner.predict_target(
                    self.records["subject_01"],
                    shots_per_class=1,
                    settings=LaBraMTuningSettings("linear", 1, 1e-4),
                )
            adapt.assert_not_called()

    def test_query_state_mutation_and_nonfinite_outputs_are_rejected(self):
        runner = self.runner()
        settings = LaBraMTuningSettings("linear", 1, 1e-4)
        for failure in ("state", "nonfinite"):
            with self.subTest(failure=failure):

                def corrupted(*args, failure=failure, **kwargs):
                    result = adapt_labram_tuning_support(*args, **kwargs)
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
                        "adaptation.labram_manifest.adapt_labram_tuning_support",
                        side_effect=corrupted,
                    ),
                    self.assertRaisesRegex(ValueError, "model state|invalid query logits"),
                ):
                    runner.predict_target(
                        self.records["subject_01"], shots_per_class=1, settings=settings
                    )
                self.assertEqual(state_digest(runner._source), runner._source_sha)

    def test_invalid_settings_or_source_contract_fail_before_execution(self):
        for kwargs in (
            {"method": "other"},
            {"steps": True},
            {"learning_rate": True},
            {"learning_rate": float("nan")},
            {"partial_depth": 1},
            {"query_batch_size": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                LaBraMTuningSettings(
                    **({"method": "linear", "steps": 1, "learning_rate": 1e-4} | kwargs)
                )
        runner = self.runner()
        with patch("adaptation.labram_manifest.load_bci_profile_b_episode") as bind:
            with self.assertRaisesRegex(ValueError, "depth"):
                runner.predict_target(
                    self.records["subject_01"],
                    shots_per_class=1,
                    settings=LaBraMTuningSettings("partial", 1, 1e-4, 3),
                )
            bind.assert_not_called()
        self.model.double()
        with self.assertRaisesRegex(ValueError, "CPU float32"):
            self.runner()
