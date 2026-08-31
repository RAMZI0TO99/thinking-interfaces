from __future__ import annotations

import unittest

import numpy as np

from data.profile_a import extract_trials


class ProfileAExtractionTests(unittest.TestCase):
    def test_exact_epoch_length_and_baseline_subtraction(self) -> None:
        signal = np.zeros((2, 30), dtype=np.float64)
        signal[0, 5:10] = 2.0
        signal[1, 5:10] = -3.0
        signal[0, 10:18] = 5.0
        signal[1, 10:18] = 1.0
        events = np.asarray([[10, 0, 1]], dtype=np.int64)
        trials, labels = extract_trials(
            signal,
            events,
            {1: "left_hand"},
            baseline_samples=5,
            epoch_samples=8,
        )
        self.assertEqual(trials.shape, (1, 2, 8))
        np.testing.assert_allclose(trials[0, 0], 3.0)
        np.testing.assert_allclose(trials[0, 1], 4.0)
        self.assertEqual(labels, ("left_hand",))

    def test_incomplete_baseline_is_rejected(self) -> None:
        signal = np.zeros((2, 30), dtype=np.float64)
        events = np.asarray([[3, 0, 1]], dtype=np.int64)
        with self.assertRaisesRegex(ValueError, "complete baseline"):
            extract_trials(
                signal,
                events,
                {1: "left_hand"},
                baseline_samples=5,
                epoch_samples=8,
            )

    def test_unknown_event_code_is_rejected(self) -> None:
        signal = np.zeros((2, 30), dtype=np.float64)
        events = np.asarray([[10, 0, 2]], dtype=np.int64)
        with self.assertRaisesRegex(ValueError, "unknown event"):
            extract_trials(
                signal,
                events,
                {1: "left_hand"},
                baseline_samples=5,
                epoch_samples=8,
            )


if __name__ == "__main__":
    unittest.main()
