from __future__ import annotations

import unittest

import numpy as np

from scripts.audit_profile_alignment import compare_epochs, cue_indices, reconstruct_epochs


class ProfileAlignmentTests(unittest.TestCase):
    def test_mat_index_origin_cue_offset_and_both_resampling_rates(self):
        trials = np.array([1, 251, 1001], dtype=np.int64)
        self.assertEqual(cue_indices(trials, 128.0).tolist(), [256, 384, 768])
        self.assertEqual(cue_indices(trials, 200.0).tolist(), [400, 600, 1200])
        for values in ([], [0], [1.5], [2, 1], [1, 1], [float("nan")]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                cue_indices(np.array(values), 128.0)

    def test_manual_baseline_and_quantized_profile_b_units(self):
        signal = np.arange(40, dtype=np.float64).reshape(2, 20) * 1e-6
        indices = np.array([5], dtype=np.int64)
        profile_a = reconstruct_epochs(signal, indices, samples=4, baseline_samples=2,
                                       stored_unit_volts=1.0)
        np.testing.assert_array_equal(profile_a[0], np.asarray(
            signal[:, 5:9] - signal[:, 3:5].mean(axis=1, keepdims=True), dtype=np.float32))
        profile_b = reconstruct_epochs(signal, indices, samples=4, baseline_samples=0,
                                       stored_unit_volts=1e-4)
        np.testing.assert_array_equal(profile_b[0], signal[:, 5:9].astype(np.float32) / 1e-4)
        with self.assertRaises(ValueError):
            reconstruct_epochs(signal, np.array([19]), samples=4, baseline_samples=0,
                               stored_unit_volts=1.0)

    def test_comparison_rejects_shifted_or_nonfinite_epochs(self):
        signal = np.arange(40, dtype=np.float32).reshape(1, 2, 20) * 1e-6
        self.assertTrue(compare_epochs(signal, signal.copy(), unit_volts=1.0)[
            "exact_float32_values_equal"])
        self.assertFalse(compare_epochs(signal, signal + 1e-6, unit_volts=1.0)[
            "within_declared_float32_tolerance"])
        with self.assertRaises(ValueError):
            compare_epochs(signal, signal[:, :, :-1], unit_volts=1.0)
        with self.assertRaises(ValueError):
            compare_epochs(signal, signal * np.nan, unit_volts=1.0)
        with self.assertRaises(ValueError):
            compare_epochs(signal, signal.copy(), unit_volts=0.0)
