from __future__ import annotations

import unittest

from data.cho2017 import (
    canonicalize_10_20_channel_names,
    dataset_metadata,
    validate_subject,
)


class Cho2017Tests(unittest.TestCase):
    def test_official_metadata_contract(self) -> None:
        metadata = dataset_metadata()
        self.assertEqual(metadata.subjects, tuple(range(1, 53)))
        self.assertEqual(metadata.events, {"left_hand": 1, "right_hand": 2})
        self.assertEqual(metadata.interval_s, (0.0, 3.0))
        self.assertEqual(metadata.sampling_rate_hz, 512.0)
        self.assertEqual(metadata.eeg_channels, 64)
        self.assertEqual(metadata.line_frequency_hz, 60.0)

    def test_channel_names_are_canonicalized_case_insensitively(self) -> None:
        self.assertEqual(
            canonicalize_10_20_channel_names(("FP1", "cz", "poZ")),
            ("Fp1", "Cz", "POz"),
        )

    def test_unknown_channel_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "standard 1005"):
            canonicalize_10_20_channel_names(("not-an-electrode",))

    def test_invalid_subject_is_rejected_without_download(self) -> None:
        with self.assertRaisesRegex(ValueError, "1..52"):
            validate_subject(53)
