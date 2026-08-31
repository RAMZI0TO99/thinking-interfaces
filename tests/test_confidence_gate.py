from __future__ import annotations

import unittest

import numpy as np

from realtime.confidence_gate import confidence_gate


class ConfidenceGateTests(unittest.TestCase):
    labels = ("left", "right", "feet", "tongue")

    def test_unique_maximum_at_threshold_is_emitted(self) -> None:
        decision = confidence_gate(
            np.asarray([0.1, 0.7, 0.1, 0.1]), self.labels, threshold=0.7
        )
        self.assertEqual(decision.state, "right")
        self.assertFalse(decision.abstained)
        self.assertEqual(decision.winning_index, 1)

    def test_below_threshold_returns_explicit_neutral_state(self) -> None:
        decision = confidence_gate(
            np.asarray([0.3, 0.2, 0.25, 0.25]), self.labels, threshold=0.7
        )
        self.assertEqual(decision.state, "neutral")
        self.assertTrue(decision.abstained)
        self.assertIsNone(decision.winning_index)

    def test_tied_maximum_abstains_even_above_threshold(self) -> None:
        decision = confidence_gate(
            np.asarray([0.5, 0.5, 0.0, 0.0]), self.labels, threshold=0.4
        )
        self.assertTrue(decision.abstained)
        self.assertEqual(decision.state, "neutral")

    def test_invalid_probability_vector_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "sum to one"):
            confidence_gate(
                np.asarray([0.4, 0.4, 0.4, 0.0]), self.labels, threshold=0.7
            )
