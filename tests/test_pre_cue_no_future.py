"""The proposed pre-cue control must never use samples at or after its cue."""

from __future__ import annotations

import unittest

import mne  # type: ignore[import-untyped]
import numpy as np

from data.pre_cue_no_future import (
    BCI_EEG_CHANNELS,
    BCI_EVENT_ID,
    build_no_future_summary,
    load_no_future_config,
    minimum_prefix_samples,
    no_future_window,
    preprocess_no_future_run,
)


def _raw(signal: np.ndarray, *, cue_sample: int = 1250) -> mne.io.RawArray:
    info = mne.create_info(list(BCI_EEG_CHANNELS), sfreq=250.0, ch_types="eeg")
    raw = mne.io.RawArray(signal, info, verbose=False)
    raw.set_annotations(
        mne.Annotations(onset=[cue_sample / 250.0], duration=[0.0], description=["left_hand"])
    )
    return raw


class NoFuturePreCueTests(unittest.TestCase):
    def test_cue_sample_and_later_samples_cannot_change_window(self) -> None:
        config = load_no_future_config()
        generator = np.random.default_rng(41)
        original = generator.normal(scale=2e-6, size=(22, 3000))
        cue_only = original.copy()
        cue_only[0, 1250] += 100e-6
        later_only = original.copy()
        later_only[:, 1251:] += generator.normal(scale=30e-6, size=(22, 1749))
        combined = cue_only.copy()
        combined[:, 1251:] = later_only[:, 1251:]

        reference, labels, channels = preprocess_no_future_run(
            _raw(original), BCI_EVENT_ID, config
        )
        for altered in (cue_only, later_only, combined):
            actual, altered_labels, altered_channels = preprocess_no_future_run(
                _raw(altered), BCI_EVENT_ID, config
            )
            np.testing.assert_array_equal(actual, reference)
            self.assertEqual(altered_labels, labels)
            self.assertEqual(altered_channels, channels)
        self.assertEqual(reference.shape, (1, 22, 128))
        self.assertEqual(reference.dtype, np.float32)
        np.testing.assert_allclose(reference.mean(axis=2), 0.0, atol=1e-12)

    def test_full_fir_boundary_is_accepted_and_short_prefix_refused(self) -> None:
        config = load_no_future_config()
        floor = minimum_prefix_samples(config)
        self.assertEqual(floor, 413)
        raw = _raw(np.zeros((22, 1000), dtype=np.float64), cue_sample=floor)
        eeg = raw.copy().pick(picks="eeg")
        accepted = no_future_window(eeg, cue_sample=floor, config=config)
        self.assertEqual(accepted.shape, (22, 128))
        with self.assertRaisesRegex(ValueError, "short raw EEG prefix"):
            no_future_window(eeg, cue_sample=floor - 1, config=config)
        with self.assertRaisesRegex(ValueError, "cue sample is invalid"):
            no_future_window(eeg, cue_sample=raw.n_times + 1, config=config)
        with self.assertRaisesRegex(ValueError, "canonical four-class"):
            preprocess_no_future_run(raw, {"left_hand": 1}, config)

    def test_manifest_identity_is_distinct_and_bound_to_config(self) -> None:
        config = load_no_future_config()
        zeros = np.zeros((22, 3000), dtype=np.float64)
        signals, _, channels = preprocess_no_future_run(
            _raw(zeros), BCI_EVENT_ID, config
        )
        summary = build_no_future_summary(
            subject=1, signals=signals, channel_names=channels, config=config
        )
        self.assertEqual(summary.artifact_kind, "pre_cue_no_future_control_v1")
        self.assertEqual(summary.manifest_kind, "pre_cue_no_future_manifest_v1")
        self.assertEqual(summary.control_id, "pre_cue_no_future_v1")
        self.assertNotEqual(summary.artifact_kind, "pre_cue_control")
        self.assertEqual(summary.shape, (1, 22, 128))
        self.assertEqual(summary.minimum_prefix_samples, 413)
        self.assertEqual(summary.prefix_policy, config.prefix_policy)
        self.assertEqual(summary.filter_phase, "zero")
        self.assertTrue(summary.mne_version)
        self.assertEqual(summary.config_file_sha256, config.config_file_sha256)


if __name__ == "__main__":
    unittest.main()
