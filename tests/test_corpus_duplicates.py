from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from evaluation.corpus_duplicates import (
    audit_corpus_duplicates,
    expected_subject_inventory,
    verify_corpus_snapshot,
)


class CorpusDuplicateTests(unittest.TestCase):
    config = {
        "benchmark": {"shots_per_class": 1},
        "datasets": {
            "d": {
                "artifact_directory": "data/processed/d",
                "artifact_threshold_volts": 1000.0,
                "sampling_rate_hz": 128,
            }
        },
    }
    subjects = {"d": ("subject_01", "subject_02")}

    def write(self, root, subject, signals, names=("C3", "C4")):
        directory = root / "data" / "processed" / "d"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{subject}.npz"
        np.savez_compressed(
            path,
            signals=signals,
            labels=np.asarray(["left", "right"] * 4),
            channel_names=np.asarray(names),
            sessions=np.asarray(["session"] * 8),
            runs=np.asarray(["run"] * 8),
            trial_indices=np.arange(8),
        )
        return path

    def signals(self, offset=0):
        return np.arange(64, dtype=np.float32).reshape(8, 2, 4) + offset

    def test_clean_corpus_passes_and_changed_artifact_invalidates_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "subject_01", self.signals())
            self.write(root, "subject_02", self.signals(100))
            report = audit_corpus_duplicates(root, config=self.config, subjects=self.subjects)
            self.assertTrue(report["no_exact_train_query_copies"])
            self.assertEqual(report["retained_trials"], 16)
            self.assertTrue(
                verify_corpus_snapshot(root, report, config=self.config, subjects=self.subjects)
            )
            self.write(root, "subject_02", self.signals(101))
            self.assertFalse(
                verify_corpus_snapshot(root, report, config=self.config, subjects=self.subjects)
            )

    def test_support_query_and_cross_subject_copies_are_found_despite_different_labels_or_order(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = self.signals(), self.signals(100)
            a[2] = a[0]
            b[3] = a[4, ::-1]
            self.write(root, "subject_01", a)
            self.write(root, "subject_02", b, ("C4", "C3"))
            report = audit_corpus_duplicates(root, config=self.config, subjects=self.subjects)
            self.assertFalse(report["no_exact_train_query_copies"])
            self.assertEqual(report["exact_train_query_copy_groups"], 2)
            self.assertTrue(
                any(
                    group["same_subject_support_query_copy"] for group in report["duplicate_groups"]
                )
            )
            self.assertTrue(
                any(
                    group["cross_subject_source_query_copy"] for group in report["duplicate_groups"]
                )
            )

    def test_frozen_rejection_is_applied_before_role_assignment_and_hashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = self.signals()
            a[0] = 2000
            a[2] = 2000
            self.write(root, "subject_01", a)
            self.write(root, "subject_02", self.signals(100))
            report = audit_corpus_duplicates(root, config=self.config, subjects=self.subjects)
            self.assertEqual(report["rejected_trials"], 2)
            self.assertEqual(report["retained_trials"], 14)
            self.assertEqual(report["duplicate_groups"], [])

    def test_missing_subject_is_not_accepted_as_a_complete_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "subject_01", self.signals())
            with self.assertRaisesRegex(ValueError, "inventory"):
                audit_corpus_duplicates(root, config=self.config, subjects=self.subjects)

    def test_three_digit_subject_ids_are_verified_without_renaming(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, "subject_001", self.signals())
            self.write(root, "subject_002", self.signals(100))
            actual = expected_subject_inventory(root, self.config, {"d": 2})
            self.assertEqual(actual, {"d": ("subject_001", "subject_002")})
            self.write(root, "subject_01", self.signals())
            with self.assertRaises(ValueError):
                expected_subject_inventory(root, self.config, {"d": 2})
