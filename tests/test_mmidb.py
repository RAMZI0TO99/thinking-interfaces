from __future__ import annotations

import unittest

from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

import mne  # noqa: E402
import numpy as np  # noqa: E402

from data.mmidb import drop_incomplete_motor_annotations  # noqa: E402


class MMIDBBoundaryTests(unittest.TestCase):
    def test_drops_only_motor_cues_without_complete_window(self) -> None:
        info = mne.create_info(["C3"], sfreq=10.0, ch_types=["eeg"])
        raw = mne.io.RawArray(np.zeros((1, 100)), info, verbose=False)
        raw.set_annotations(
            mne.Annotations(
                onset=[2.0, 8.0, 9.5],
                duration=[0.0, 0.0, 0.0],
                description=["T1", "T2", "rest"],
            )
        )
        sanitized, dropped = drop_incomplete_motor_annotations(
            raw, baseline_s=1.0, epoch_s=4.0
        )
        self.assertEqual(dropped, 1)
        self.assertEqual(tuple(sanitized.annotations.description), ("T1", "rest"))
