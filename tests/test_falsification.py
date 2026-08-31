from __future__ import annotations

import unittest

import numpy as np

from evaluation.benchmark import DatasetMatrix
from evaluation.falsification import control_indices, shuffled_training_control, signal_audit


class SpyDecoder:
    def fit(self, epochs, labels):
        self.train = epochs.copy()
        self.labels = labels.copy()
        return self

    def predict_proba(self, epochs):
        self.query = epochs.copy()
        return np.full((len(epochs), 2), 0.5, dtype=np.float32)


class FalsificationTests(unittest.TestCase):
    def setUp(self):
        self.matrix = DatasetMatrix(
            "synthetic",
            np.arange(48 * 2 * 4, dtype=np.float32).reshape(48, 2, 4),
            np.asarray(["left", "right"] * 24),
            np.asarray(["A"] * 24 + ["B"] * 24),
            ("C3", "C4"),
            64.0,
        )

    def test_only_training_labels_are_shuffled_after_fixed_split(self):
        decoder = SpyDecoder()
        before_signals = self.matrix.signals.copy()
        before_labels = self.matrix.labels.copy()
        source, support, query = control_indices(self.matrix, "B", 2)
        result = shuffled_training_control(
            self.matrix,
            decoder,
            target_subject="B",
            shots_per_class=2,
            shuffle_seed=11,
        )
        np.testing.assert_array_equal(decoder.train, before_signals[np.r_[source, support]])
        np.testing.assert_array_equal(decoder.query, before_signals[query])
        np.testing.assert_array_equal(self.matrix.labels, before_labels)
        np.testing.assert_array_equal(self.matrix.signals, before_signals)
        self.assertEqual(result["support_trials"], 4)
        self.assertEqual(result["query_trials"], 20)
        self.assertEqual(result["metrics"]["balanced_accuracy"], 0.5)
        self.assertTrue(result["train_query_disjoint"])
        self.assertTrue(result["training_label_counts_preserved"])
        self.assertGreater(result["changed_training_labels"], 0)
        self.assertEqual(np.bincount(decoder.labels).tolist(), [14, 14])

    def test_changing_shuffle_preserves_query_and_support(self):
        results = [
            shuffled_training_control(
                self.matrix,
                SpyDecoder(),
                target_subject="B",
                shots_per_class=2,
                shuffle_seed=seed,
            )
            for seed in (11, 23)
        ]
        for key in ("support_indices_sha256", "query_indices_sha256", "query_labels_sha256"):
            self.assertEqual(results[0][key], results[1][key])
        self.assertNotEqual(
            results[0]["training_labels_shuffled_sha256"],
            results[1]["training_labels_shuffled_sha256"],
        )

    def test_duplicate_audit_detects_source_query_copy(self):
        clean = signal_audit(self.matrix, target_subject="B", shots_per_class=2)
        self.assertTrue(clean["exact_duplicate_checks_passed"])
        self.matrix.signals[-1] = self.matrix.signals[0]
        duplicated = signal_audit(self.matrix, target_subject="B", shots_per_class=2)
        self.assertFalse(duplicated["exact_duplicate_checks_passed"])
        self.assertEqual(duplicated["query_indices_exactly_duplicated_in_training"], [47])

    def test_missing_subject_is_rejected(self):
        with self.assertRaises(ValueError):
            control_indices(self.matrix, "C", 2)

    def test_invalid_probabilities_fail_closed(self):
        class BadDecoder(SpyDecoder):
            def predict_proba(self, epochs):
                return np.full((len(epochs), 2), np.nan, dtype=np.float32)

        with self.assertRaises(ValueError):
            shuffled_training_control(
                self.matrix, BadDecoder(), target_subject="B", shots_per_class=2, shuffle_seed=11
            )
