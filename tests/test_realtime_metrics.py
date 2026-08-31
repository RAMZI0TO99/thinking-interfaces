from __future__ import annotations

import math
import unittest

import numpy as np

from evaluation.realtime_metrics import (
    accuracy_coverage_curve,
    calibration_report,
    information_transfer_rate,
)


class RealtimeMetricTests(unittest.TestCase):
    def test_itr_hand_worked_perfect_binary_example(self) -> None:
        value = information_transfer_rate(1.0, classes=2, decisions_per_minute=15)
        self.assertTrue(math.isclose(value, 15.0))

    def test_chance_itr_is_zero(self) -> None:
        value = information_transfer_rate(0.5, classes=2, decisions_per_minute=30)
        self.assertAlmostEqual(value, 0.0)

    def test_calibration_and_coverage(self) -> None:
        probabilities = np.asarray([[0.9, 0.1], [0.6, 0.4], [0.2, 0.8]])
        targets = np.asarray([0, 1, 1])
        report = calibration_report(probabilities, targets, bins=2)
        self.assertGreaterEqual(report.expected_calibration_error, 0.0)
        curve = accuracy_coverage_curve(probabilities, targets, thresholds=(0.0, 0.85))
        self.assertEqual(curve[0].coverage, 1.0)
        self.assertEqual(curve[1].coverage, 1 / 3)
