from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core.config import config_digest, load_toml
from evaluation.phase2_cho_b_input_snapshot import _ChoBInputSnapshot, _episode_bytes
from evaluation.phase2_cho_input_snapshot import _FilePin
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    CHO_CLASSES,
    ChoProfileAssets,
    ChoProfileAssets60Hz,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog


class _Cho60Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        configs = self.root / "configs"
        (configs / "phase2").mkdir(parents=True)
        project = Path(__file__).resolve().parents[1]
        for name in (
            "base.toml", "benchmark.toml", "phase2/selection_ceiling.toml",
            "phase2/cho_profile_b_60hz.toml",
        ):
            (configs / name).write_bytes((project / "configs" / name).read_bytes())
        self.config = json.loads(json.dumps(load_toml(project / "configs/phase2/protocol.toml")))
        self.config["datasets"]["cho2017"]["expected_subjects"] = 4
        self.config["protocol"]["shots_per_class"] = [1, 2]
        self.config["protocol"]["maximum_support_per_class"] = 2
        variant_path = configs / "phase2/cho_profile_b_60hz.toml"
        variant = load_toml(variant_path)
        threshold_path = configs / "benchmark.toml"
        threshold = load_toml(threshold_path)["datasets"]["cho2017"]["artifact_threshold_volts"]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(threshold_path),
            "dataset": "cho2017", "threshold": threshold,
        })
        generator = np.random.default_rng(23)
        catalogs, self.assets, self.records = [], {}, {}
        for number in range(1, 5):
            subject = f"subject_{number:02d}"
            for profile, samples in (("a", 512), ("b_60hz_v1", 800)):
                directory = self.root / f"data/processed/cho2017/profile_{profile}"
                directory.mkdir(parents=True, exist_ok=True)
                signals = generator.normal(size=(10, 64, samples)).astype(np.float32)
                signals *= 1e-8 if profile == "a" else 0.1
                if profile == "a":
                    signals[0] = 1  # Excluded only by the original frozen A threshold.
                np.savez(
                    directory / f"{subject}.npz", signals=signals,
                    labels=np.array(CHO_CLASSES * 5), sessions=np.array(["s"] * 10),
                    runs=np.array(["r"] * 10), trial_indices=np.arange(10),
                    channel_names=np.array(CHO_CHANNELS),
                )
            raw = self.root / f"data/raw/moabb/cho2017/{subject}.mat"
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(f"synthetic raw provenance for {subject}".encode())
            b_path = self.root / "data/processed/cho2017/profile_b_60hz_v1" / f"{subject}.npz"
            b_manifest = b_path.with_suffix(".manifest.json")
            b_manifest.write_text(json.dumps({
                "artifact_schema_version": 1, "artifact_kind": "profile_b", "subject": number,
                "shape": [10, 64, 800], "channel_names": list(CHO_CHANNELS),
                "epoch_duration_s": 4.0, "sampling_rate_hz": 200.0,
                "config_sha256": config_digest(variant["preprocessing"]), "reference": "original",
                "amplitude_unit_mv": 0.1, "patch_samples": 200, "patches_per_epoch": 4,
                "variant": variant["variant"], "variant_config_sha256": file_digest(variant_path),
                "source_file": raw.relative_to(self.root).as_posix(),
                "source_sha256": file_digest(raw),
            }), encoding="utf-8")
            a_path = self.root / "data/processed/cho2017/profile_a" / f"{subject}.npz"
            catalog, _ = read_catalog(
                a_path, dataset="cho2017", classes=CHO_CLASSES, threshold=threshold,
                preprocessing_sha256=preprocessing,
            )
            catalogs.append(catalog)
            self.assets[subject] = ChoProfileAssets60Hz(
                file_digest(b_path), file_digest(b_manifest), file_digest(variant_path),
            )
            self.records[subject] = envelope(
                "episode_manifest",
                nested_episode(
                    catalog, shots=(1, 2), protocol_sha256=config_digest(self.config),
                ).payload(),
            )
        self.catalogs = tuple(catalogs)
        self.permitted = self.catalogs[1:]
        self.permitted_assets = {c.subject: self.assets[c.subject] for c in self.permitted}
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))

    def snapshot(self, **kwargs):
        return _ChoBInputSnapshot(
            self.root, self.config, self.permitted, self.permitted_assets, **kwargs,
        )

    def load(self, snapshot, catalog=None):
        catalog = catalog or self.permitted[0]
        return snapshot.load(
            self.config, catalog, self.records[catalog.subject], shots_per_class=2,
            profile_assets=self.assets[catalog.subject],
        )

    def subject_paths(self, subject):
        return (
            self.root / "data/processed/cho2017/profile_a" / f"{subject}.npz",
            self.root / "data/processed/cho2017/profile_b_60hz_v1" / f"{subject}.npz",
            self.root / "data/processed/cho2017/profile_b_60hz_v1" / f"{subject}.manifest.json",
            self.root / "data/raw/moabb/cho2017" / f"{subject}.mat",
        )


class ChoBInputSnapshotTests(_Cho60Fixture):
    def test_lazy_exact_immutable_episode_and_no_outer_prefetch(self):
        for path in self.subject_paths("subject_01"):
            path.write_bytes(b"outer target is unreadable")
        with patch(
            "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
            wraps=load_cho_profile_b_episode,
        ) as loader:
            snapshot = self.snapshot()
            loader.assert_not_called()
            data = self.load(snapshot)
            self.assertIs(data, self.load(snapshot))
            self.assertEqual(loader.call_count, 1)
        catalog = self.permitted[0]
        reference = load_cho_profile_b_episode(
            self.root, self.config, catalog, self.records[catalog.subject],
            shots_per_class=2, **asdict(self.assets[catalog.subject]),
        )
        self.assertEqual(asdict(data.binding), asdict(reference.binding))
        for field in ("support_signals", "query_signals", "support_labels", "query_labels"):
            array = getattr(data, field)
            np.testing.assert_array_equal(array, getattr(reference, field))
            with self.assertRaises(ValueError):
                array.setflags(write=True)
            with self.assertRaises(ValueError):
                array.flat[0] = 0
        owned = np.stack([data.support_signals[0], data.query_signals[0]])
        self.assertTrue(owned.flags.writeable)
        owned[:] = 0
        np.testing.assert_array_equal(data.support_signals, reference.support_signals)
        self.assertEqual(snapshot._retained_bytes, _episode_bytes(data))
        self.assertEqual(set(snapshot._subject_pins), {catalog.subject})
        snapshot.verify(self.config)

    def test_lru_counts_all_partitions_and_retains_evicted_pins(self):
        item_size = _episode_bytes(self.load(self.snapshot()))
        snapshot = self.snapshot(maximum_retained_bytes=2 * item_size)
        with patch(
            "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
            wraps=load_cho_profile_b_episode,
        ) as loader:
            for catalog in (
                self.permitted[0], self.permitted[1], self.permitted[0], self.permitted[2],
            ):
                self.load(snapshot, catalog)
                self.assertLessEqual(snapshot._retained_bytes, 2 * item_size)
            self.assertEqual(loader.call_count, 3)
            self.assertEqual(
                tuple(snapshot._entries), (self.permitted[0].subject, self.permitted[2].subject),
            )
        self.assertEqual(set(snapshot._subject_pins), {c.subject for c in self.permitted})
        with patch.object(_FilePin, "verify_bytes", autospec=True) as verify:
            snapshot.verify(self.config)
        checked_paths = {call.args[0].path for call in verify.call_args_list}
        self.assertTrue(set(self.subject_paths(self.permitted[1].subject)) <= checked_paths)

    def test_oversize_bypass_retains_pins_and_returns_owned_loader_arrays(self):
        snapshot = self.snapshot(maximum_retained_bytes=1)
        with patch(
            "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
            wraps=load_cho_profile_b_episode,
        ) as loader:
            first, second = self.load(snapshot), self.load(snapshot)
            self.assertIsNot(first, second)
            self.assertEqual(loader.call_count, 2)
            self.assertTrue(first.support_signals.flags.writeable)
        self.assertEqual(snapshot._retained_bytes, 0)
        self.assertFalse(snapshot._entries)
        self.assertEqual(len(snapshot._subject_pins[self.permitted[0].subject]), 4)
        snapshot.verify(self.config)

    def test_clear_releases_residency_and_preserves_integrity_pins(self):
        snapshot = self.snapshot()
        self.load(snapshot)
        expected_pins = dict(snapshot._subject_pins)
        snapshot.clear()
        self.assertEqual(snapshot._retained_bytes, 0)
        self.assertFalse(snapshot._entries)
        self.assertEqual(snapshot._subject_pins, expected_pins)
        snapshot.verify(self.config)
        with patch(
            "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
            wraps=load_cho_profile_b_episode,
        ) as loader:
            self.load(snapshot)
            self.assertEqual(loader.call_count, 1)

    def test_configuration_protocol_catalog_assets_and_episode_drift_clear_arrays(self):
        for kind in ("protocol", "catalog", "assets", "episode", "shots"):
            with self.subTest(kind=kind):
                snapshot = self.snapshot()
                self.load(snapshot)
                catalog = self.permitted[0]
                config = json.loads(json.dumps(self.config))
                record = json.loads(json.dumps(self.records[catalog.subject]))
                assets = self.assets[catalog.subject]
                shots = 2
                if kind == "protocol":
                    config["protocol"]["model_seeds"] = [99]
                elif kind == "catalog":
                    catalog = replace(catalog, artifact_sha256="0" * 64)
                elif kind == "assets":
                    assets = replace(assets, profile_b_manifest_sha256="0" * 64)
                elif kind == "episode":
                    record["sha256"] = "0" * 64
                else:
                    shots = 1
                with self.assertRaises(ValueError):
                    snapshot.load(
                        config, catalog, record, shots_per_class=shots, profile_assets=assets,
                    )
                self.assertFalse(snapshot._entries)
                self.assertEqual(snapshot._retained_bytes, 0)

    def test_hit_metadata_tamper_rejects_and_clears(self):
        for index in range(4):
            with self.subTest(index=index):
                snapshot = self.snapshot()
                self.load(snapshot)
                path = self.subject_paths(self.permitted[0].subject)[index]
                status = path.stat()
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns + 1_000_000))
                try:
                    with self.assertRaisesRegex(ValueError, "file identity changed"):
                        self.load(snapshot)
                    self.assertFalse(snapshot._entries)
                finally:
                    os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))

    def test_final_stream_hash_catches_restored_mtime_tamper_even_after_eviction(self):
        item_size = _episode_bytes(self.load(self.snapshot()))
        for index in range(4):
            with self.subTest(index=index):
                snapshot = self.snapshot(maximum_retained_bytes=item_size)
                self.load(snapshot)
                self.load(snapshot, self.permitted[1])
                self.assertNotIn(self.permitted[0].subject, snapshot._entries)
                path = self.subject_paths(self.permitted[0].subject)[index]
                original, status = path.read_bytes(), path.stat()
                changed = bytearray(original)
                changed[-1] ^= 1
                path.write_bytes(changed)
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
                try:
                    with (
                        patch.object(_FilePin, "check_metadata"),
                        self.assertRaisesRegex(ValueError, "bytes changed"),
                    ):
                        snapshot.verify(self.config)
                    self.assertFalse(snapshot._entries)
                finally:
                    path.write_bytes(original)
                    os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))

    def test_small_config_exact_bytes_checked_on_hits_with_hidden_metadata(self):
        for relative in (
            "configs/base.toml", "configs/benchmark.toml", "configs/phase2/cho_profile_b_60hz.toml",
        ):
            with self.subTest(relative=relative):
                snapshot = self.snapshot()
                self.load(snapshot)
                path = self.root / relative
                original, status = path.read_bytes(), path.stat()
                changed = bytearray(original)
                changed[-1] ^= 1
                path.write_bytes(changed)
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
                try:
                    with (
                        patch.object(_FilePin, "check_metadata"),
                        self.assertRaisesRegex(ValueError, "bytes changed"),
                    ):
                        self.load(snapshot)
                    self.assertFalse(snapshot._entries)
                finally:
                    path.write_bytes(original)
                    os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))

    def test_outer_and_legacy_assets_rejected_without_reads(self):
        snapshot = self.snapshot()
        with self.assertRaisesRegex(ValueError, "outside permitted"):
            self.load(snapshot, self.catalogs[0])
        legacy = dict(self.permitted_assets)
        asset = legacy[self.permitted[0].subject]
        legacy[self.permitted[0].subject] = ChoProfileAssets(
            asset.profile_b_artifact_sha256, asset.profile_b_manifest_sha256,
        )
        with self.assertRaises(ValueError):
            _ChoBInputSnapshot(self.root, self.config, self.permitted, legacy)
        for limit in (-1, True, 2 * 1024**3 + 1):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.snapshot(maximum_retained_bytes=limit)

    def test_loader_failure_clears_existing_residency(self):
        snapshot = self.snapshot()
        self.load(snapshot)
        with (
            patch(
                "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
                side_effect=ValueError("loader stopped"),
            ),
            self.assertRaisesRegex(ValueError, "loader stopped"),
        ):
            self.load(snapshot, self.permitted[1])
        self.assertFalse(snapshot._entries)
        self.assertEqual(snapshot._retained_bytes, 0)


class ChoBSelectorEquivalenceTests(_Cho60Fixture):
    """Deferred runtime tests: Torch/Braindecode are imported inside test methods only."""

    def selector(self, method="linear"):
        import torch
        from braindecode.models import Labram

        from adaptation.labram_lora_trained import (
            LoRAContinuationSettings,
            LoRASourceCandidate,
            LoRASourceSettings,
        )
        from adaptation.labram_manifest import LaBraMTuningSettings
        from adaptation.labram_source import (
            BCILaBraMSourceSelector,
            LaBraMSourceCandidate,
            LaBraMSourceSettings,
        )
        from encoder.labram import LaBraMClassifier
        from evaluation.labram_parity import state_digest

        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            backbone = Labram(
                n_times=800, n_chans=64, n_outputs=0, num_layers=1,
                drop_prob=0.2, attn_drop_prob=0.2,
            )
            model = LaBraMClassifier(backbone, classes=2, channel_names=CHO_CHANNELS).eval()
        if method == "lora":
            first = LoRASourceCandidate(
                "a", LoRASourceSettings(
                    ("backbone.blocks.0.attn.qkv",), 2, 4.0, 11, True, 1, 2, 0.001,
                ),
                LoRAContinuationSettings(True, 1, 0.001, 2),
            )
        else:
            first = LaBraMSourceCandidate(
                "a", LaBraMSourceSettings(method, 1, 2, 0.001),
                LaBraMTuningSettings(method, 1, 0.001, query_batch_size=2),
            )
        second = replace(first, name="b", source=replace(first.source, learning_rate=0.002))
        return BCILaBraMSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, model, self.assets,
            outer_target="subject_01", template_state_sha256=state_digest(model),
            candidates=(first, second), seed=23, shots_per_class=1, maximum_gradient_steps=64,
        )

    def assert_equivalent(self, method):
        import torch

        # The template constructor and every fit must preserve the caller's RNG.
        rng = torch.random.get_rng_state()
        cached, uncached = self.selector(method), self.selector(method)
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        uncached._cho_b_inputs = None  # Private test-only toggle, absent from scientific settings.
        for path in self.subject_paths("subject_01"):
            path.write_bytes(b"outer target must never be read")
        with patch(
            "evaluation.phase2_cho_b_input_snapshot.load_cho_profile_b_episode",
            wraps=load_cho_profile_b_episode,
        ) as loads:
            actual = cached.run_selection()
        reference = uncached.run_selection()
        self.assertEqual(loads.call_count, len(self.permitted))
        self.assertEqual(actual.evidence.record_json, reference.evidence.record_json)
        self.assertEqual(tuple(actual.source.state_dict()), tuple(reference.source.state_dict()))
        for name, value in actual.source.state_dict().items():
            self.assertTrue(torch.equal(value, reference.source.state_dict()[name]), name)
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertFalse(cached._cho_b_inputs._entries)
        self.assertEqual(cached._cho_b_inputs._retained_bytes, 0)
        payload = actual.evidence.record["payload"]
        self.assertEqual(len(payload["folds"]), 6)
        self.assertEqual(len(payload["final_source_fit"]["steps"]), 3)
        self.assertFalse(payload["outer_target_predictions_performed"])

    def test_plain_linear_complete_selection_exact_model_history_evidence_and_rng(self):
        self.assert_equivalent("linear")

    def test_plain_full_complete_selection_exact_model_history_evidence_and_rng(self):
        self.assert_equivalent("full")

    def test_lora_complete_selection_exact_model_history_evidence_and_rng(self):
        self.assert_equivalent("lora")

    def test_owned_batch_does_not_mutate_cached_episode(self):
        from adaptation.labram_source import _batch

        selector = self.selector()
        snapshot = selector._cho_b_inputs
        episode = self.load(snapshot)
        original = episode.support_signals.copy()
        inputs, labels = _batch(episode, episode.binding.support_trial_ids[:2])
        inputs.zero_()
        labels.zero_()
        np.testing.assert_array_equal(episode.support_signals, original)

    def test_public_success_and_every_execution_failure_clear_cache(self):
        for mode in ("fold_success", "fold_failure", "fit_failure", "selection_failure"):
            with self.subTest(mode=mode):
                selector = self.selector()
                snapshot = selector._cho_b_inputs
                self.load(snapshot)
                if mode == "fold_success":
                    selector.run_fold(candidate_name="a", validation_subject="subject_02")
                else:
                    method = "_fit_sgd" if mode == "fit_failure" else "_fold"
                    with (
                        patch.object(
                            selector, method, side_effect=RuntimeError("execution stopped"),
                        ),
                        self.assertRaisesRegex(RuntimeError, "execution stopped"),
                    ):
                        if mode == "selection_failure":
                            selector.run_selection()
                        else:
                            selector.run_fold(candidate_name="a", validation_subject="subject_02")
                self.assertFalse(snapshot._entries)
                self.assertEqual(snapshot._retained_bytes, 0)

    def test_public_evidence_refuses_changed_evicted_raw_and_releases_arrays(self):
        selector = self.selector()
        snapshot = selector._cho_b_inputs
        snapshot._maximum_retained_bytes = 1
        self.load(snapshot)
        path = self.subject_paths(self.permitted[0].subject)[3]
        status = path.stat()
        original = path.read_bytes()
        changed = bytearray(original)
        changed[-1] ^= 1
        path.write_bytes(changed)
        os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
        with (
            patch.object(_FilePin, "check_metadata"),
            self.assertRaisesRegex(ValueError, "bytes changed"),
        ):
            selector._evidence({"complete": False})
        self.assertFalse(snapshot._entries)
        self.assertEqual(snapshot._retained_bytes, 0)


if __name__ == "__main__":
    unittest.main()
