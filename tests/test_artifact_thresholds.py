from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from evaluation.artifact_thresholds import audit_threshold_directory


class ArtifactThresholdAuditTests(unittest.TestCase):
    def test_reports_retention_and_requires_expected_subjects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            signals = np.asarray([[[0.5, -0.5]], [[2.0, -2.0]]], dtype=np.float32)
            np.savez_compressed(root / "subject_001.npz", signals=signals)
            audit = audit_threshold_directory(
                root,
                dataset="fixture",
                threshold_volts=1.0,
                expected_subjects=1,
            )
            self.assertEqual(audit.retained_trials, 1)
            self.assertEqual(audit.rejected_trials, 1)
            with self.assertRaisesRegex(ValueError, "expected 2"):
                audit_threshold_directory(
                    root,
                    dataset="fixture",
                    threshold_volts=1.0,
                    expected_subjects=2,
                )
