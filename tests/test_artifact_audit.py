from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from evaluation.artifact_audit import audit_epoch_artifact


def write_fixture(path: Path, signals: np.ndarray, sessions: np.ndarray) -> None:
    trial_count = len(signals)
    np.savez_compressed(
        path,
        signals=signals,
        labels=np.asarray(["left", "right"] * (trial_count // 2)),
        sessions=sessions,
        runs=np.asarray(["0"] * trial_count),
        trial_indices=np.arange(trial_count),
        channel_names=np.asarray(["C3", "C4"]),
    )


class ArtifactAuditTests(unittest.TestCase):
    def test_clean_artifact_passes(self) -> None:
        rng = np.random.default_rng(7)
        first_channel = rng.normal(size=(4, 1, 16)).astype(np.float32)
        signals = np.concatenate([first_channel, -first_channel], axis=1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.npz"
            write_fixture(path, signals, np.asarray(["train", "train", "test", "test"]))
            audit = audit_epoch_artifact(path)
        self.assertTrue(audit.passed)
        self.assertEqual(audit.exact_duplicate_groups, 0)

    def test_cross_session_duplicate_is_rejected(self) -> None:
        rng = np.random.default_rng(11)
        first_channel = rng.normal(size=(4, 1, 16)).astype(np.float32)
        signals = np.concatenate([first_channel, -first_channel], axis=1)
        signals[3] = signals[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.npz"
            write_fixture(path, signals, np.asarray(["train", "train", "test", "test"]))
            audit = audit_epoch_artifact(path)
        self.assertFalse(audit.passed)
        self.assertEqual(audit.cross_session_duplicate_groups, 1)


if __name__ == "__main__":
    unittest.main()

