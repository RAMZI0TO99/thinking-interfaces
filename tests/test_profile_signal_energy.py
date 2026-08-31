from __future__ import annotations

import unittest

import numpy as np

from scripts.audit_profile_signals import signal_energy


class ProfileSignalEnergyTests(unittest.TestCase):
    def test_single_frequency_and_common_average(self):
        wave = np.sin(2 * np.pi * 10 * np.arange(512) / 128) * 1e-6
        signals = np.array([[wave, -wave]])
        report = signal_energy(signals, 128, 8, 30)
        self.assertAlmostEqual(report["energy_fractions"]["profile_a_band_inclusive"], 1.0)
        self.assertAlmostEqual(report["rms_microvolts"], 1 / np.sqrt(2))
        self.assertAlmostEqual(report["spatial_common_mean_energy_fraction"], 0.0)

    def test_dc_and_odd_length_parseval(self):
        report = signal_energy(np.ones((2, 3, 513)) * 1e-6, 128, 8, 30)
        self.assertAlmostEqual(report["energy_fractions"]["dc"], 1.0)
        self.assertAlmostEqual(report["spatial_common_mean_energy_fraction"], 1.0)
        self.assertAlmostEqual(report["rms_microvolts"], 1.0)

    def test_invalid_or_zero_signal_is_rejected(self):
        for signals in (np.zeros((1, 2, 512)), np.full((1, 2, 512), np.nan), np.zeros((2, 512))):
            with self.subTest(shape=signals.shape), self.assertRaises(ValueError):
                signal_energy(signals, 128, 8, 30)


if __name__ == "__main__":
    unittest.main()
