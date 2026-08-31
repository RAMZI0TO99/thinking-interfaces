from __future__ import annotations

import unittest
from statistics import NormalDist

import numpy as np

from evaluation.statistics import (
    normal_approximation_equivalence_power,
    paired_comparison,
    paired_tost,
    variance_derived_equivalence_margin,
)


class StatisticsTests(unittest.TestCase):
    def test_paired_difference_and_interval(self) -> None:
        result = paired_comparison(np.asarray([0.8, 0.7, 0.9]), np.asarray([0.7, 0.6, 0.8]))
        self.assertAlmostEqual(result.mean_difference, 0.1)
        self.assertEqual(result.subject_count, 3)

    def test_tost_detects_tight_identical_scores(self) -> None:
        first = np.asarray([0.60, 0.61, 0.59, 0.60])
        result = paired_tost(first, first.copy(), margin=0.03)
        self.assertTrue(result.equivalent)

    def test_tost_rejects_unpaired_shapes_before_broadcasting(self) -> None:
        scores = np.asarray([0.60, 0.61, 0.59, 0.60])
        invalid_pairs = (
            (scores, np.asarray([0.60])),
            (np.asarray([0.60]), scores),
            (scores, np.asarray(0.60)),
            (scores, scores[:3]),
            (scores[:, None], scores[:, None]),
            (scores[:0], scores[:0]),
            (scores[:1], scores[:1]),
        )
        for first, second in invalid_pairs:
            with (
                self.subTest(first=first.shape, second=second.shape),
                self.assertRaises(ValueError),
            ):
                paired_tost(first, second, margin=0.03)

    def test_tost_rejects_nonfinite_scores_and_bounds(self) -> None:
        scores = np.asarray([0.60, 0.61, 0.59, 0.60])
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(margin=value), self.assertRaises(ValueError):
                paired_tost(scores, scores, margin=value)
            with self.subTest(alpha=value), self.assertRaises(ValueError):
                paired_tost(scores, scores, margin=0.03, alpha=value)
            invalid = scores.copy()
            invalid[0] = value
            for first, second in ((invalid, scores), (scores, invalid)):
                with self.subTest(score=value), self.assertRaises(ValueError):
                    paired_tost(first, second, margin=0.03)

    def test_tost_variable_paired_scores_respect_both_bounds(self) -> None:
        first = np.asarray([0.60, 0.63, 0.62, 0.64])
        second = np.asarray([0.60, 0.61, 0.61, 0.62])
        # Paired mean = 0.0125; the 90% t interval is about [0.00124, 0.02376].
        self.assertTrue(paired_tost(first, second, margin=0.03).equivalent)
        self.assertFalse(paired_tost(first, second, margin=0.015).equivalent)

    def test_variance_derived_margin_scales_with_variance(self) -> None:
        small = variance_derived_equivalence_margin(0.05, subjects=9)
        large = variance_derived_equivalence_margin(0.15, subjects=9)
        self.assertGreater(large, small)

    def test_variance_derived_margin_achieves_target_design_power(self) -> None:
        margin = variance_derived_equivalence_margin(0.12, subjects=52, target_power=0.8)
        power = normal_approximation_equivalence_power(margin, standard_deviation=0.12, subjects=52)
        self.assertAlmostEqual(power, 0.8)

    def test_equivalence_requires_both_one_sided_bounds(self) -> None:
        normal = NormalDist()
        sd = 0.12
        se = sd / np.sqrt(52)
        former_margin = (normal.inv_cdf(0.95) + normal.inv_cdf(0.8)) * se
        self.assertAlmostEqual(
            normal_approximation_equivalence_power(
                former_margin, standard_deviation=sd, subjects=52
            ),
            0.6,
        )
        margin = variance_derived_equivalence_margin(sd, subjects=52)
        # Independent simulation of BOTH bounds rather than round-tripping helpers.
        estimates = np.random.default_rng(72).normal(0.0, se, size=400_000)
        lower = estimates - normal.inv_cdf(0.95) * se
        upper = estimates + normal.inv_cdf(0.95) * se
        observed = float(np.mean((lower > -margin) & (upper < margin)))
        self.assertAlmostEqual(observed, 0.8, delta=0.003)

    def test_nonoverlapping_equivalence_bounds_have_zero_power(self) -> None:
        self.assertEqual(
            normal_approximation_equivalence_power(0.001, standard_deviation=0.12, subjects=52),
            0.0,
        )

    def test_nonfinite_design_inputs_are_rejected(self) -> None:
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                variance_derived_equivalence_margin(value, subjects=52)
            with self.subTest(value=value), self.assertRaises(ValueError):
                normal_approximation_equivalence_power(value, standard_deviation=0.12, subjects=52)
