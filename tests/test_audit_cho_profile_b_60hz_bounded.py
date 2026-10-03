from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.config import config_digest, load_toml
from evaluation.phase2_profile_binding import CHO_CHANNELS, CHO_CLASSES
from scripts.audit_cho_profile_b_60hz_bounded import audit_subject_01
from scripts.audit_phase2_protocol import file_digest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ChoBounded60HzAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        config_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_bytes(
            (PROJECT_ROOT / "configs/phase2/cho_profile_b_60hz.toml").read_bytes()
        )
        variant_config = load_toml(config_file)
        base = load_toml(PROJECT_ROOT / "configs/base.toml")["preprocessing"]["profile_b"]
        old = self.root / "data/processed/cho2017/profile_b"
        new = self.root / variant_config["variant"]["output_directory"]
        a_dir = self.root / "data/processed/cho2017/profile_a"
        for directory in (old, new, a_dir):
            directory.mkdir(parents=True)
        raw_file = self.root / "data/raw/moabb/cho2017/subject_01.mat"
        raw_file.parent.mkdir(parents=True)
        raw_file.write_bytes(b"pinned synthetic source")
        self.raw_file = raw_file
        rng = np.random.default_rng(20260923)
        seconds = np.arange(800) / 200.0
        noise = rng.normal(scale=0.001, size=(2, 64, 800)).astype(np.float32)
        tone = np.sin(2 * np.pi * 60 * seconds).astype(np.float32)
        self.old_signals = noise + 0.1 * tone
        self.new_signals = noise + 0.0002 * tone
        self.meta = dict(
            labels=np.array(CHO_CLASSES),
            sessions=np.array(["session", "session"]),
            runs=np.array(["run", "run"]),
            trial_indices=np.array([0, 1], dtype=np.int64),
            channel_names=np.array(CHO_CHANNELS),
        )
        a = a_dir / "subject_01.npz"
        np.savez(a, signals=np.zeros((2, 64, 512), dtype=np.float32), **self.meta)
        old_artifact = old / "subject_01.npz"
        new_artifact = new / "subject_01.npz"
        np.savez(old_artifact, signals=self.old_signals, **self.meta)
        np.savez(new_artifact, signals=self.new_signals, **self.meta)
        old_manifest = old / "subject_01.manifest.json"
        new_manifest = new / "subject_01.manifest.json"
        common = dict(
            artifact_schema_version=1,
            artifact_kind="profile_b",
            subject=1,
            shape=[2, 64, 800],
            channel_names=list(CHO_CHANNELS),
            epoch_duration_s=4.0,
            sampling_rate_hz=200.0,
            reference="original",
            amplitude_unit_mv=0.1,
            patch_samples=200,
            patches_per_epoch=4,
        )
        old_manifest.write_text(
            json.dumps({**common, "config_sha256": config_digest(base)}), encoding="utf-8"
        )
        new_manifest.write_text(json.dumps({
            **common,
            "config_sha256": config_digest(variant_config["preprocessing"]),
            "variant": variant_config["variant"],
            "variant_config_sha256": file_digest(config_file),
            "source_file": raw_file.relative_to(self.root).as_posix(),
            "source_sha256": file_digest(raw_file),
        }), encoding="utf-8")
        self.paths = {
            "profile_a": a,
            "legacy_artifact": old_artifact,
            "legacy_manifest": old_manifest,
            "variant_artifact": new_artifact,
            "variant_manifest": new_manifest,
            "variant_config": config_file,
            "raw_source": raw_file,
        }
        self.pins = {name: file_digest(path) for name, path in self.paths.items()}

    def test_predeclared_tone_attenuation_passes_and_reports_joins(self) -> None:
        report = audit_subject_01(self.root, self.pins)
        self.assertTrue(report["passed"])
        self.assertEqual(report["subject"], "subject_01")
        self.assertEqual(report["trials"], 2)
        self.assertEqual(report["profile_a_trial_join"], "complete")
        self.assertGreater(report["variant_60hz_attenuation_db_vs_legacy"], 6.0)

    def test_changed_raw_source_refuses(self) -> None:
        self.raw_file.write_bytes(b"modified source")
        with self.assertRaisesRegex(ValueError, "raw_source bytes changed"):
            audit_subject_01(self.root, self.pins)

    def test_trial_label_mismatch_refuses_after_repinned_artifact(self) -> None:
        changed_meta = dict(self.meta)
        changed_meta["labels"] = np.array(("right_hand", "left_hand"))
        np.savez(self.paths["variant_artifact"], signals=self.new_signals, **changed_meta)
        self.pins["variant_artifact"] = file_digest(self.paths["variant_artifact"])
        with self.assertRaisesRegex(ValueError, "trial identities or labels differ"):
            audit_subject_01(self.root, self.pins)

    def test_missing_60hz_attenuation_fails_diagnostic(self) -> None:
        np.savez(self.paths["variant_artifact"], signals=self.old_signals, **self.meta)
        self.pins["variant_artifact"] = file_digest(self.paths["variant_artifact"])
        report = audit_subject_01(self.root, self.pins)
        self.assertFalse(report["passed"])
        self.assertAlmostEqual(report["variant_60hz_attenuation_db_vs_legacy"], 0.0)

    def test_legacy_manifest_with_variant_marker_refuses(self) -> None:
        path = self.paths["legacy_manifest"]
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["variant"] = {"name": "profile_b_60hz_v1"}
        path.write_text(json.dumps(payload), encoding="utf-8")
        self.pins["legacy_manifest"] = file_digest(path)
        with self.assertRaisesRegex(ValueError, "historical 50 Hz manifest"):
            audit_subject_01(self.root, self.pins)


if __name__ == "__main__":
    unittest.main()
