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
