from __future__ import annotations

import unittest

import numpy as np

from data.artifact_rejection import reject_amplitude_artifacts
from data.unified import UnifiedArtifact


class ArtifactRejectionTests(unittest.TestCase):
    def test_threshold_removes_only_large_trials_and_preserves_provenance(self) -> None:
        signals = np.zeros((4, 2, 3), dtype=np.float32)
        signals[2, 0, 0] = 2.0
        artifact = UnifiedArtifact(
            signals,
            np.asarray(["left", "right", "left", "right"]),
            np.asarray(["0"] * 4),
            np.asarray(["0"] * 4),
            np.arange(4),
            ("C3", "C4"),
        )
        filtered, report = reject_amplitude_artifacts(
            artifact, absolute_peak_volts=1.0
        )
        self.assertEqual(filtered.signals.shape[0], 3)
        self.assertEqual(filtered.trial_indices.tolist(), [0, 1, 3])
        self.assertEqual(report.rejected_trials, 1)

    def test_rejecting_a_whole_class_is_an_error(self) -> None:
        signals = np.zeros((2, 1, 2), dtype=np.float32)
        signals[1] = 2.0
        artifact = UnifiedArtifact(
            signals,
            np.asarray(["left", "right"]),
            np.asarray(["0", "0"]),
            np.asarray(["0", "0"]),
            np.arange(2),
            ("Cz",),
        )
        with self.assertRaisesRegex(ValueError, "entire class"):
            reject_amplitude_artifacts(artifact, absolute_peak_volts=1.0)
