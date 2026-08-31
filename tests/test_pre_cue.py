from __future__ import annotations

import unittest

import numpy as np

from data.pre_cue import extract_pre_cue_trials


class PreCueExtractionTests(unittest.TestCase):
    def test_window_ends_at_cue_and_is_mean_centred(self) -> None:
        signal = np.zeros((2, 20), dtype=np.float64)
        signal[0, 5:10] = np.asarray([1, 2, 3, 4, 5])
        signal[1, 5:10] = np.asarray([-2, -1, 0, 1, 2])
        signal[:, 10:] = 1000.0
        events = np.asarray([[10, 0, 1]], dtype=np.int64)

        trials, labels = extract_pre_cue_trials(
            signal, events, {1: "left_hand"}, window_samples=5
        )

        self.assertEqual(trials.shape, (1, 2, 5))
        np.testing.assert_allclose(trials.mean(axis=2), 0.0, atol=1e-7)
        self.assertLess(float(trials.max()), 1000.0)
        self.assertEqual(labels, ("left_hand",))

    def test_incomplete_window_is_rejected(self) -> None:
        signal = np.zeros((2, 20), dtype=np.float64)
        events = np.asarray([[3, 0, 1]], dtype=np.int64)
        with self.assertRaisesRegex(ValueError, "complete pre-cue"):
            extract_pre_cue_trials(signal, events, {1: "left_hand"}, window_samples=5)

    def test_unknown_event_is_rejected(self) -> None:
        signal = np.zeros((2, 20), dtype=np.float64)
        events = np.asarray([[10, 0, 2]], dtype=np.int64)
        with self.assertRaisesRegex(ValueError, "unknown event"):
            extract_pre_cue_trials(signal, events, {1: "left_hand"}, window_samples=5)
