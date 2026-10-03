from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core.config import load_toml
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import audit, read_catalog


class Phase2ProtocolAuditTests(unittest.TestCase):
    def test_real_npz_rejection_eligibility_resume_and_tamper_detection(self) -> None:
        config = load_toml("configs/phase2/protocol.toml")
        config["protocol"]["shots_per_class"] = [1, 5]
        config["protocol"]["maximum_support_per_class"] = 5
        config["datasets"] = {
            "toy": {
                "artifact_directory": "data/toy",
                "classes": ["left", "right"],
                "expected_subjects": 3,
            }
        }
        thresholds = {"datasets": {"toy": {"artifact_threshold_volts": 1.0}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root / "data/toy"
            directory.mkdir(parents=True)
            (root / "configs").mkdir()
            (root / "configs/benchmark.toml").write_text("# fixed test threshold")
            for index, count in enumerate((8, 8, 5)):
                labels = np.asarray(["left", "right"] * count)
                signals = np.zeros((len(labels), 2, 4), dtype=np.float32)
                signals[0] = 2.0  # one known rejected left trial
                np.savez(
                    directory / f"subject_{index:02}.npz",
                    signals=signals,
                    labels=labels,
                    sessions=np.full(len(labels), "session"),
                    runs=np.full(len(labels), "run"),
                    trial_indices=np.arange(len(labels)),
                    channel_names=["C3", "C4"],
                )

            def configs(path):
                return thresholds if Path(path).name == "benchmark.toml" else config

            with patch("scripts.audit_phase2_protocol.load_toml", side_effect=configs):
                result = audit(root, Path("test.toml"))
                self.assertEqual(result["datasets"]["toy"]["eligible_subjects"], 2)
                self.assertIn("subject_02", result["datasets"]["toy"]["excluded_subjects"])
                files = list((root / "runs/phase2").rglob("*.json"))
                times = {p: p.stat().st_mtime_ns for p in files}
                audit(root, Path("test.toml"), verify_only=True)
                self.assertEqual(times, {p: p.stat().st_mtime_ns for p in files})
                saved_path = next((root / "runs/phase2").rglob("subject_00.episode.json"))
                saved = json.loads(saved_path.read_text())
                saved["payload"]["partitions"][0]["support_indices"][0] = 14
                saved_path.write_text(json.dumps(envelope("episode_manifest", saved["payload"])))
                with self.assertRaisesRegex(ValueError, "differs"):
                    audit(root, Path("test.toml"), verify_only=True)
                with self.assertRaises(FileExistsError):
                    audit(root, Path("test.toml"))

    def test_artifact_metadata_collisions_nonfinite_and_shape_errors_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "subject.npz"
            base = dict(
                signals=np.zeros((4, 2, 4)),
                labels=["left", "right"] * 2,
                sessions=["s"] * 4,
                runs=["r"] * 4,
                trial_indices=np.arange(4),
                channel_names=["C3", "C4"],
            )
            for changed in (
                {"trial_indices": np.zeros(4, dtype=int)},
                {"signals": np.full((4, 2, 4), np.nan)},
                {"runs": ["r"] * 3},
            ):
                np.savez(path, **{**base, **changed})
                with self.subTest(changed=tuple(changed)), self.assertRaises(ValueError):
                    read_catalog(
                        path,
                        dataset="toy",
                        classes=("left", "right"),
                        threshold=1,
                        preprocessing_sha256="a" * 64,
                    )
