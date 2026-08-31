from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from evaluation.calibration_plot import save_calibration_diagnostics


class CalibrationPlotTests(unittest.TestCase):
    def test_renders_png_with_empty_bins_and_empty_selections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "check.png"
            save_calibration_diagnostics(
                np.asarray([[0.9, 0.1], [0.2, 0.8]]), np.asarray([0, 0]), path,
                title="Synthetic test", thresholds=(0.0, 0.9, 1.0),
            )
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            self.assertGreater(path.stat().st_size, 1000)

    def test_rejects_invalid_threshold_order_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "check.png"
            with self.assertRaises(ValueError):
                save_calibration_diagnostics(
                    np.asarray([[0.9, 0.1]]), np.asarray([0]), path,
                    title="Synthetic test", thresholds=(0.9, 0.5),
                )
            self.assertFalse(path.exists())
