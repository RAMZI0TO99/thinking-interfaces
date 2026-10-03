from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core.config import config_digest, load_toml
from evaluation.phase2_profile_binding import BCI_CHANNELS, BCI_CLASSES, load_bci_profile_b_episode
from evaluation.phase2_protocol import nested_episode
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog


class ProfileBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        for name in ("base.toml", "benchmark.toml"):
            (self.root / "configs" / name).write_bytes((Path("configs") / name).read_bytes())
        self.config = load_toml("configs/phase2/protocol.toml")
        self.paths = {}
        self.arrays = {}
        base = load_toml("configs/base.toml")["preprocessing"]
        for profile, samples in (("a", 512), ("b", 800)):
            directory = self.root / f"data/processed/bci_iv_2a/profile_{profile}"
            directory.mkdir(parents=True)
            self.paths[profile] = directory / "subject_01.npz"
            self.paths[profile + "m"] = directory / "subject_01.manifest.json"
            signals = np.broadcast_to(
                np.arange(92, dtype=np.float32)[:, None, None], (92, 22, samples)
            ).copy()
            if profile == "a":
                signals *= 1e-8
                signals[0] = 1  # Reject one original trial before constructing the catalog.
            else:
                signals = signals / 100 + 1
            self.arrays[profile] = dict(
                signals=signals,
                labels=np.array(BCI_CLASSES * 23),
                sessions=np.array(["session"] * 92),
                runs=np.array(["run"] * 92),
                trial_indices=np.arange(92),
                channel_names=np.array(BCI_CHANNELS),
            )
            cfg = copy.deepcopy(base["profile_" + profile])
            if profile == "a":
                cfg["baseline_duration_s"] = cfg.pop("pre_cue_s")
            manifest = dict(
                artifact_schema_version=1,
                subject=1,
                shape=[92, 22, samples],
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
            self.paths[profile + "m"].write_text(json.dumps(manifest))
            self.save(profile)
        self.refresh_catalog()

    def tearDown(self):
        self.temp.cleanup()

    def save(self, profile):
        np.savez_compressed(self.paths[profile], **self.arrays[profile])

    def refresh_catalog(self):
        path = self.root / "configs/benchmark.toml"
        threshold = load_toml(path)["datasets"]["bci_iv_2a"]["artifact_threshold_volts"]
        sha = config_digest(
            {
                "profile_identity": self.config["preparation"]["profile_identity"],
                "threshold_config_sha256": file_digest(path),
                "dataset": "bci_iv_2a",
                "threshold": threshold,
            }
        )
        self.catalog, _ = read_catalog(
            self.paths["a"],
            dataset="bci_iv_2a",
            classes=BCI_CLASSES,
            threshold=threshold,
            preprocessing_sha256=sha,
        )
        self.record = envelope(
            "episode_manifest",
            nested_episode(
                self.catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
            ).payload(),
        )

    def load(self, shots=1, **overrides):
        kwargs = dict(
            shots_per_class=shots,
            profile_a_manifest_sha256=file_digest(self.paths["am"]),
            profile_b_artifact_sha256=file_digest(self.paths["b"]),
            profile_b_manifest_sha256=file_digest(self.paths["bm"]),
        )
        kwargs.update(overrides)
        return load_bci_profile_b_episode(
            self.root, self.config, self.catalog, self.record, **kwargs
        )

    def test_reordered_b_rows_join_by_identity_at_every_shot_without_rescaling(self):
        original = copy.deepcopy(self.arrays["b"])
        for name in ("signals", "labels", "sessions", "runs", "trial_indices"):
            self.arrays["b"][name] = original[name][::-1].copy()
        self.save("b")
        common = None
        maximum_pool = set(
            self.catalog.trial_ids[i]
            for i in nested_episode(
                self.catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
            )
            .partition(20)
            .support_indices
        )
        for shots in (1, 5, 10, 20):
            with self.subTest(shots=shots):
                result = self.load(shots)
                binding = result.binding
                self.assertEqual(result.support_signals.shape, (4 * shots, 22, 800))
                self.assertEqual(result.query_signals.shape, (11, 22, 800))
                self.assertEqual(binding.profile_a_rejected_trials, 1)
                self.assertEqual(binding.stored_unit_volts, 1e-4)
                self.assertEqual(binding.extra_input_scale, 1.0)
                self.assertFalse(maximum_pool.intersection(binding.query_trial_ids))
                for ids, values, labels in (
                    (binding.support_trial_ids, result.support_signals, result.support_labels),
                    (binding.query_trial_ids, result.query_signals, result.query_labels),
                ):
                    indices = [json.loads(trial)[2] for trial in ids]
                    self.assertNotIn(0, indices)
                    np.testing.assert_array_equal(values, original["signals"][indices])
                    np.testing.assert_array_equal(labels, np.array(indices) % 4)
                if common is not None:
                    self.assertEqual(binding.query_trial_ids, common)
                common = binding.query_trial_ids

    def test_returned_arrays_are_owned_and_repeat_identity_is_stable(self):
        hashes = {k: file_digest(p) for k, p in self.paths.items()}
        first = self.load()
        expected = first.support_signals.copy()
        first.support_signals[:] = 999
        first.support_labels[:] = 3
        second = self.load()
        self.assertEqual(first.binding.sha256, second.binding.sha256)
        np.testing.assert_array_equal(second.support_signals, expected)
        self.assertEqual(hashes, {k: file_digest(p) for k, p in self.paths.items()})

    def test_missing_extra_duplicate_and_relabeled_original_trials_fail_with_new_hashes(self):
        original = copy.deepcopy(self.arrays["b"])
        manifest = json.loads(self.paths["bm"].read_text())
        for failure in ("missing", "extra", "duplicate", "label", "session"):
            with self.subTest(failure=failure):
                self.arrays["b"] = copy.deepcopy(original)
                if failure in ("missing", "extra"):
                    rows = np.arange(91) if failure == "missing" else np.r_[np.arange(92), 0]
                    for name in ("signals", "labels", "sessions", "runs", "trial_indices"):
                        self.arrays["b"][name] = original[name][rows].copy()
                    if failure == "extra":
                        self.arrays["b"]["trial_indices"][-1] = 92
                elif failure == "duplicate":
                    self.arrays["b"]["trial_indices"][1] = 0
                elif failure == "label":
                    self.arrays["b"]["labels"][0] = "tongue"
                else:
                    self.arrays["b"]["sessions"][0] = "other"
                manifest["shape"] = list(self.arrays["b"]["signals"].shape)
                self.paths["bm"].write_text(json.dumps(manifest))
                self.save("b")
                with self.assertRaises(ValueError):
                    self.load()

    def test_invalid_encoder_arrays_and_montage_fail_with_new_hashes(self):
        original = copy.deepcopy(self.arrays["b"])
        for failure in (
            "samples",
            "dtype",
            "nonfinite",
            "channels",
            "negative_index",
            "float_index",
        ):
            with self.subTest(failure=failure):
                self.arrays["b"] = copy.deepcopy(original)
                values = self.arrays["b"]
                if failure == "samples":
                    values["signals"] = values["signals"][:, :, :512]
                elif failure == "dtype":
                    values["signals"] = values["signals"].astype(np.float64)
                elif failure == "nonfinite":
                    values["signals"][0, 0, 0] = np.nan
                elif failure == "channels":
                    values["channel_names"] = values["channel_names"][::-1]
                    values["signals"] = values["signals"][:, ::-1]
                elif failure == "negative_index":
                    values["trial_indices"][0] = -1
                else:
                    values["trial_indices"] = values["trial_indices"].astype(np.float64)
                self.save("b")
                with self.assertRaises(ValueError):
                    self.load()

    def test_manifest_units_subject_sampling_patch_and_config_cannot_be_rehashed_away(self):
        original = json.loads(self.paths["bm"].read_text())
        for field, value in (
            ("amplitude_unit_mv", 1.0),
            ("sampling_rate_hz", 128.0),
            ("subject", 2),
            ("patch_samples", 100),
            ("reference", "average"),
            ("config_sha256", "a" * 64),
            ("artifact_schema_version", True),
        ):
            with self.subTest(field=field):
                changed = {**original, field: value}
                self.paths["bm"].write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, "manifest"):
                    self.load()

    def test_pinned_files_episode_and_catalog_are_checked_independently(self):
        sha = file_digest(self.paths["b"])
        self.arrays["b"]["signals"][0] += 1
        self.save("b")
        with self.assertRaisesRegex(ValueError, "pinned b"):
            self.load(profile_b_artifact_sha256=sha)
        payload = copy.deepcopy(self.record["payload"])
        payload["partitions"][0]["query_indices"][0] = 0
        self.record = envelope("episode_manifest", payload)
        with self.assertRaisesRegex(ValueError, "episode"):
            self.load()
        self.refresh_catalog()
        self.catalog = replace(
            self.catalog,
            labels=tuple("tongue" if i == 0 else v for i, v in enumerate(self.catalog.labels)),
        )
        self.record = envelope(
            "episode_manifest",
            nested_episode(
                self.catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
            ).payload(),
        )
        with self.assertRaisesRegex(ValueError, "catalog differs"):
            self.load()

    def test_invalid_shots_and_changed_base_or_threshold_are_rejected(self):
        for shots in (True, 0, 2, -1):
            with self.subTest(shots=shots), self.assertRaises(ValueError):
                self.load(shots)
        base = self.root / "configs/base.toml"
        original = base.read_bytes()
        base.write_text(
            base.read_text().replace("amplitude_unit_mv = 0.1", "amplitude_unit_mv = 1.0")
        )
        with self.assertRaisesRegex(ValueError, "base profiles"):
            self.load()
        base.write_bytes(original)
        threshold = self.root / "configs/benchmark.toml"
        threshold.write_bytes(threshold.read_bytes() + b"\n# identity changed\n")
        with self.assertRaisesRegex(ValueError, "catalog differs"):
            self.load()

    def test_duplicate_rejected_a_trial_is_not_hidden_by_retained_catalog(self):
        self.arrays["a"]["trial_indices"][0] = 1
        self.save("a")
        self.refresh_catalog()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.load()

    def test_last_hash_check_rejects_concurrent_input_change(self):
        kwargs = dict(profile_b_artifact_sha256=file_digest(self.paths["b"]))
        calls = 0

        def digest(path):
            nonlocal calls
            if path == self.paths["b"]:
                calls += 1
                if calls == 2:
                    return "f" * 64  # Initial check, then final check.
            return file_digest(path)

        with (
            patch("evaluation.phase2_profile_binding.file_digest", side_effect=digest),
            self.assertRaisesRegex(ValueError, "changed while loading"),
        ):
            self.load(**kwargs)
