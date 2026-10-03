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
from evaluation.phase2_cho_input_snapshot import _ChoInputSnapshot, _FilePin
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import CHO_CHANNELS, CHO_CLASSES
from evaluation.phase2_protocol import source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog


class _ChoFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        configs = self.root / "configs"
        configs.mkdir()
        (configs / "phase2").mkdir()
        project = Path(__file__).resolve().parents[1]
        for name in ("base.toml", "benchmark.toml", "phase2/selection_ceiling.toml"):
            (configs / name).write_bytes((project / "configs" / name).read_bytes())
        self.config = json.loads(json.dumps(load_toml(project / "configs/phase2/protocol.toml")))
        self.config["datasets"]["cho2017"]["expected_subjects"] = 3
        self.config["protocol"]["shots_per_class"] = [1, 2]
        self.config["protocol"]["maximum_support_per_class"] = 2
        directory = self.root / "data/processed/cho2017/profile_a"
        directory.mkdir(parents=True)
        threshold_path = configs / "benchmark.toml"
        threshold = load_toml(threshold_path)["datasets"]["cho2017"]["artifact_threshold_volts"]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(threshold_path),
            "dataset": "cho2017", "threshold": threshold,
        })
        generator = np.random.default_rng(23)
        catalogs = []
        for number in range(1, 4):
            path = directory / f"subject_{number:02d}.npz"
            signals = generator.normal(size=(12, 64, 512)).astype(np.float32) * 1e-8
            np.savez(
                path, signals=signals, labels=np.array(CHO_CLASSES * 6),
                sessions=np.array(["s"] * 12), runs=np.array(["r"] * 12),
                trial_indices=np.arange(12), channel_names=np.array(CHO_CHANNELS),
            )
            catalog, _ = read_catalog(
                path, dataset="cho2017", classes=CHO_CLASSES, threshold=threshold,
                preprocessing_sha256=preprocessing,
            )
            catalogs.append(catalog)
        self.catalogs = tuple(catalogs)
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))
        self.permitted = self.catalogs[1:]

    def snapshot(self, **kwargs):
        return _ChoInputSnapshot(self.root, self.config, self.permitted, **kwargs)

    def artifact(self, catalog):
        return self.root / "data/processed/cho2017/profile_a" / f"{catalog.subject}.npz"


class ChoInputSnapshotTests(_ChoFixture):
    def test_lazy_immutable_exact_rows_and_no_outer_target_read(self):
        # Even unreadable outer bytes cannot affect a source-only snapshot.
        self.artifact(self.catalogs[0]).write_bytes(b"outer target must never be read")
        with patch(
            "evaluation.phase2_cho_input_snapshot.load_cho_profile_a_subject",
            wraps=load_cho_profile_a_subject,
        ) as loader:
            snapshot = self.snapshot()
            loader.assert_not_called()
            data = snapshot.load(self.config, self.permitted[0])
            reference = load_cho_profile_a_subject(self.root, self.config, self.permitted[0])
            np.testing.assert_array_equal(data.signals, reference.signals)
            np.testing.assert_array_equal(data.labels, reference.labels)
            self.assertEqual(data.artifact_rows, reference.artifact_rows)
            self.assertEqual(data.manifest_sha256, reference.manifest_sha256)
            self.assertEqual(data.base_config_sha256, reference.base_config_sha256)
            self.assertIs(data, snapshot.load(self.config, self.permitted[0]))
            self.assertEqual(loader.call_count, 1)
            for array in (data.signals, data.labels):
                self.assertFalse(array.flags.writeable)
                with self.assertRaises(ValueError):
                    array.setflags(write=True)
                with self.assertRaises(ValueError):
                    array.flat[0] = 0
            # Caller batches remain independently owned, matching the existing executor.
            owned = data.signals[[0, 1]].copy()
            owned[:] = 0
            np.testing.assert_array_equal(data.signals, reference.signals)
            snapshot.verify(self.config)
            with self.assertRaisesRegex(ValueError, "permitted source"):
                snapshot.load(self.config, self.catalogs[0])

    def test_lru_counts_labels_and_retains_evicted_pins(self):
        size = 12 * 64 * 512 * 4 + 12 * 8
        snapshot = self.snapshot(maximum_retained_bytes=size)
        with patch(
            "evaluation.phase2_cho_input_snapshot.load_cho_profile_a_subject",
            wraps=load_cho_profile_a_subject,
        ) as loader:
            snapshot.load(self.config, self.permitted[0])
            self.assertEqual(snapshot._retained_bytes, size)
            snapshot.load(self.config, self.permitted[1])
            self.assertEqual(tuple(snapshot._entries), (self.permitted[1].subject,))
            snapshot.load(self.config, self.permitted[0])
            self.assertEqual(loader.call_count, 3)
        self.assertEqual(snapshot._retained_bytes, size)
        self.assertEqual(set(snapshot._artifact_pins), {c.subject for c in self.permitted})
        with patch(
            "evaluation.phase2_cho_input_snapshot.file_digest", wraps=file_digest,
        ) as hashes:
            snapshot.verify(self.config)
        self.assertEqual(
            {c.args[0] for c in hashes.call_args_list},
            {self.artifact(c) for c in self.permitted}
            | {self.root / "configs/base.toml", self.root / "configs/benchmark.toml"},
        )

    def test_oversize_bypasses_cache_but_still_gets_final_hash(self):
        snapshot = self.snapshot(maximum_retained_bytes=1)
        with patch(
            "evaluation.phase2_cho_input_snapshot.load_cho_profile_a_subject",
            wraps=load_cho_profile_a_subject,
        ) as loader:
            first = snapshot.load(self.config, self.permitted[0])
            second = snapshot.load(self.config, self.permitted[0])
            self.assertIsNot(first, second)
            self.assertTrue(first.signals.flags.writeable)
            self.assertEqual(loader.call_count, 2)
        self.assertEqual(snapshot._retained_bytes, 0)
        self.assertFalse(snapshot._entries)
        with patch(
            "evaluation.phase2_cho_input_snapshot.file_digest", wraps=file_digest,
        ) as hashes:
            snapshot.verify(self.config)
        self.assertIn(self.artifact(self.permitted[0]), [c.args[0] for c in hashes.call_args_list])

    def test_hits_update_lru_recency_without_reloading(self):
        size = 12 * 64 * 512 * 4 + 12 * 8
        snapshot = self.snapshot(maximum_retained_bytes=2 * size)
        with patch(
            "evaluation.phase2_cho_input_snapshot.load_cho_profile_a_subject",
            wraps=load_cho_profile_a_subject,
        ) as loader:
            for catalog in (*self.permitted, self.permitted[0]):
                snapshot.load(self.config, catalog)
            self.assertEqual(loader.call_count, 2)
        self.assertEqual(
            tuple(snapshot._entries), (self.permitted[1].subject, self.permitted[0].subject),
        )
        self.assertEqual(snapshot._retained_bytes, 2 * size)

    def test_no_shared_snapshot_state_between_selectors(self):
        first, second = self.snapshot(), self.snapshot()
        data = first.load(self.config, self.permitted[0])
        self.assertFalse(second._entries)
        self.assertFalse(second._artifact_pins)
        self.assertIsNot(data, second.load(self.config, self.permitted[0]))

    def test_metadata_drift_rejects_hits_and_evicted_reload(self):
        for evict in (False, True):
            with self.subTest(evict=evict):
                snapshot = self.snapshot(maximum_retained_bytes=12 * 64 * 512 * 4 + 12 * 8)
                snapshot.load(self.config, self.permitted[0])
                if evict:
                    snapshot.load(self.config, self.permitted[1])
                path = self.artifact(self.permitted[0])
                original = path.stat()
                os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns + 1_000_000))
                with self.assertRaisesRegex(ValueError, "file identity changed"):
                    snapshot.load(self.config, self.permitted[0])
                os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))

    def test_mtime_preserved_tamper_still_requires_final_stream_hash(self):
        # Suppress metadata changes to discriminate full hashing from metadata-only checks.
        for relative in (
            "data/processed/cho2017/profile_a/subject_02.npz",
            "configs/base.toml", "configs/benchmark.toml",
        ):
            with self.subTest(relative=relative):
                snapshot = self.snapshot(maximum_retained_bytes=1)
                snapshot.load(self.config, self.permitted[0])
                path = self.root / relative
                original = path.read_bytes()
                status = path.stat()
                changed = bytearray(original)
                changed[-1] ^= 1
                path.write_bytes(changed)
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
                with (
                    patch.object(_FilePin, "check_metadata"),
                    self.assertRaisesRegex(ValueError, "bytes changed"),
                ):
                    snapshot.verify(self.config)
                path.write_bytes(original)
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))

    def test_protocol_catalog_and_config_file_drift_fail_closed(self):
        snapshot = self.snapshot()
        snapshot.load(self.config, self.permitted[0])
        altered = json.loads(json.dumps(self.config))
        altered["protocol"]["model_seeds"] = [99]
        with self.assertRaisesRegex(ValueError, "protocol configuration changed"):
            snapshot.load(altered, self.permitted[0])
        with self.assertRaisesRegex(ValueError, "protocol configuration changed"):
            snapshot.verify(altered)
        with self.assertRaisesRegex(ValueError, "permitted source"):
            snapshot.load(self.config, replace(self.permitted[0], artifact_sha256="0" * 64))
        threshold = self.root / "configs/benchmark.toml"
        threshold.write_bytes(threshold.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "file identity changed"):
            snapshot.load(self.config, self.permitted[0])

    def test_bad_limit_and_non_cho_catalogs_reject_before_read(self):
        for limit in (-1, True, 2 * 1024**3):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.snapshot(maximum_retained_bytes=limit)
        with self.assertRaises(ValueError):
            _ChoInputSnapshot(self.root, self.config, ())
        with self.assertRaises(ValueError):
            _ChoInputSnapshot(
                self.root, self.config, (replace(self.permitted[0], dataset="bci_iv_2a"),),
            )


class ChoSelectorSnapshotEquivalenceTests(_ChoFixture):
    """Torch imports happen only when these explicitly selected integration tests run."""

    def selector(self):
        from adaptation.anchor_manifest import EEGNetAnchorSettings
        from adaptation.source_selection import (
            BCIEEGNetSourceSelector,
            EEGNetCandidate,
            EEGNetSourceSettings,
        )

        candidate = EEGNetCandidate(
            "a", EEGNetSourceSettings(2, 4, 0.001, 1e6),
            EEGNetAnchorSettings(1, 0.001, 1e6, 4),
        )
        second = replace(candidate, name="b", source=replace(candidate.source, learning_rate=0.002))
        return BCIEEGNetSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, {},
            outer_target="subject_01", candidates=(candidate, second),
            seed=23, shots_per_class=1, maximum_gradient_steps=64,
        )

    def test_complete_selection_exact_weights_histories_confusions_scores_and_evidence(self):
        import torch

        self.artifact(self.catalogs[0]).write_bytes(b"outer target must never be read")
        cached, uncached = self.selector(), self.selector()
        # Private test toggle only; no public/executable scientific setting is added.
        uncached._cho_inputs = None
        rng = torch.random.get_rng_state()
        with patch(
            "evaluation.phase2_cho_input_snapshot.load_cho_profile_a_subject",
            wraps=load_cho_profile_a_subject,
        ) as loads:
            actual = cached.run_selection()
        reference = uncached.run_selection()
        self.assertEqual(loads.call_count, 2)
        self.assertTrue(torch.equal(rng, torch.random.get_rng_state()))
        self.assertEqual(actual.evidence.record_json, reference.evidence.record_json)
        self.assertEqual(tuple(actual.source.state_dict()), tuple(reference.source.state_dict()))
        for name, tensor in actual.source.state_dict().items():
            self.assertTrue(torch.equal(tensor, reference.source.state_dict()[name]), name)
        payload = actual.evidence.record["payload"]
        self.assertEqual(len(payload["folds"]), 4)
        self.assertEqual(len(payload["final_source_fit"]["steps"]), 4)
        self.assertFalse(payload["outer_target_predictions_performed"])
        self.assertEqual(
            set(cached._cho_inputs._artifact_pins), {c.subject for c in self.permitted},
        )

    def test_public_fold_and_selection_evidence_verify_inputs_before_return(self):
        path = self.artifact(self.permitted[0])
        original = path.read_bytes()
        for mode in ("fold", "selection"):
            with self.subTest(mode=mode):
                selector = self.selector()
                original_evidence = selector._evidence

                def tamper_then_evidence(payload, original_evidence=original_evidence):
                    status = path.stat()
                    changed = bytearray(original)
                    changed[-1] ^= 1
                    path.write_bytes(changed)
                    os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
                    # Metadata is hidden to exercise unconditional artifact hashing.
                    with patch.object(_FilePin, "check_metadata"):
                        return original_evidence(payload)

                try:
                    with (
                        patch.object(selector, "_evidence", side_effect=tamper_then_evidence),
                        self.assertRaisesRegex(ValueError, "bytes changed"),
                    ):
                        if mode == "fold":
                            selector.run_fold(candidate_name="a", validation_subject="subject_02")
                        else:
                            selector.run_selection()
                finally:
                    path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
