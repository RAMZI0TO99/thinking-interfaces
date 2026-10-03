from __future__ import annotations

import unittest

import numpy as np

from data.profile_b import (
    ProfileBConfig,
    collect_profile_b_runs,
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


    def test_collect_profile_b_runs_joins_runs_and_preserves_identity(self) -> None:
        import mne

        def synthetic_raw(seed: int):
            generator = np.random.default_rng(seed)
            data = generator.normal(size=(2, 20 * 200)) * 1e-5
            info = mne.create_info(["C3", "C4"], 200.0, ch_types="eeg")
            raw = mne.io.RawArray(data, info, verbose=False)
            annotations = mne.Annotations(
                onset=[5.0, 10.0], duration=[0.0, 0.0], description=["left_hand", "right_hand"]
            )
            raw.set_annotations(annotations)
            return raw

        config = ProfileBConfig(
            bandpass_low_hz=1.0,
            bandpass_high_hz=90.0,
            notch_hz=50.0,
            resample_hz=200.0,
            reference="original",
            epoch_duration_s=4.0,
            amplitude_unit_mv=0.1,
            patch_duration_s=1.0,
            maximum_patches=4,
        )
        subject_data = {
            "0": {"0": synthetic_raw(1), "1": synthetic_raw(2)},
            "1": {"0": synthetic_raw(3)},
        }
        signals, labels, sessions, runs, trial_indices, channels = collect_profile_b_runs(
            subject_data, {"left_hand": 1, "right_hand": 2}, config
        )
        self.assertEqual(signals.shape, (6, 2, 800))
        self.assertEqual(labels.tolist(), ["left_hand", "right_hand"] * 3)
        self.assertEqual(sessions.tolist(), ["0", "0", "0", "0", "1", "1"])
        self.assertEqual(runs.tolist(), ["0", "0", "1", "1", "0", "0"])
        self.assertEqual(trial_indices.tolist(), [0, 1, 0, 1, 0, 1])
        self.assertEqual(channels, ("C3", "C4"))
        self.assertTrue(np.isfinite(signals).all())
        with self.assertRaisesRegex(ValueError, "no runs"):
            collect_profile_b_runs({}, {"left_hand": 1}, config)
