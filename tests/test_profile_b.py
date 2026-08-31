from __future__ import annotations

import unittest

import numpy as np

from data.profile_b import (
    ProfileBConfig,
    extract_profile_b_trials,
    patch_epoch,
    scale_to_amplitude_unit,
)


class ProfileBTests(unittest.TestCase):
    def test_amplitude_is_expressed_in_point_one_millivolt_units(self) -> None:
        volts = np.asarray([[-1e-4, 0.0, 1e-4]], dtype=np.float64)
        scaled = scale_to_amplitude_unit(volts, amplitude_unit_mv=0.1)
        np.testing.assert_allclose(scaled, [[-1.0, 0.0, 1.0]])

    def test_epoch_starts_at_cue_without_baseline_subtraction(self) -> None:
        signal = np.arange(40, dtype=np.float64).reshape(2, 20)
        events = np.asarray([[5, 0, 1]], dtype=np.int64)
        trials, labels = extract_profile_b_trials(
            signal, events, {1: "left_hand"}, epoch_samples=4
        )
        np.testing.assert_allclose(trials[0], signal[:, 5:9])
        self.assertEqual(labels, ("left_hand",))

    def test_patching_is_channel_first_and_capped(self) -> None:
        epoch = np.arange(24, dtype=np.float32).reshape(2, 12)
        patches = patch_epoch(epoch, patch_samples=3, maximum_patches=2)
        self.assertEqual(patches.shape, (2, 2, 3))
        np.testing.assert_array_equal(patches[0], epoch[:, :3])
        np.testing.assert_array_equal(patches[1], epoch[:, 3:6])

    def test_invalid_frequency_order_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "low < notch < high"):
            ProfileBConfig(
                bandpass_low_hz=0.1,
                bandpass_high_hz=40.0,
                notch_hz=50.0,
                resample_hz=200.0,
                reference="original",
                epoch_duration_s=4.0,
                amplitude_unit_mv=0.1,
                patch_duration_s=1.0,
                maximum_patches=256,
            )
