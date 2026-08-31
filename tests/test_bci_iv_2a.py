from __future__ import annotations

import unittest
from pathlib import Path

from data.bci_iv_2a import dataset_metadata, summarize_subject_data, validate_subject


class FakeRaw:
    def __init__(
        self,
        channels: tuple[str, ...],
        sampling_rate: float,
        samples: int,
        channel_types: tuple[str, ...] | None = None,
    ) -> None:
        self.ch_names = channels
        self.info = {"sfreq": sampling_rate}
        self.n_times = samples
        self._channel_types = channel_types or ("eeg",) * len(channels)

    def get_channel_types(self) -> list[str]:
        return list(self._channel_types)


class BCIIV2ATests(unittest.TestCase):
    def test_official_metadata_contract(self) -> None:
        metadata = dataset_metadata()
        self.assertEqual(metadata.subjects, tuple(range(1, 10)))
        self.assertEqual(
            metadata.events,
            {"left_hand": 1, "right_hand": 2, "feet": 3, "tongue": 4},
        )
        self.assertEqual(metadata.interval_s, (2.0, 6.0))

    def test_invalid_subject_is_rejected_without_download(self) -> None:
        with self.assertRaisesRegex(ValueError, "subject"):
            validate_subject(10)

    def test_summary_checks_channel_order_and_counts_runs(self) -> None:
        channels = ("C3", "CZ", "C4")
        data = {
            "train": {
                "0": FakeRaw(channels, 250.0, 1000),
                "1": FakeRaw(channels, 250.0, 1200),
            },
            "test": {"0": FakeRaw(channels, 250.0, 900)},
        }
        summary = summarize_subject_data(
            1,
            (Path("A01T.mat"), Path("A01E.mat")),
            data,
        )
        self.assertEqual(summary.session_count, 2)
        self.assertEqual(summary.run_count, 3)
        self.assertEqual(summary.total_samples, 3100)
        self.assertEqual(summary.sampling_rates_hz, (250.0,))
        self.assertEqual(summary.channel_types, ("eeg", "eeg", "eeg"))

    def test_channel_order_change_is_rejected(self) -> None:
        data = {
            "train": {
                "0": FakeRaw(("C3", "C4"), 250.0, 1000),
                "1": FakeRaw(("C4", "C3"), 250.0, 1000),
            }
        }
        with self.assertRaisesRegex(ValueError, "channel names or types"):
            summarize_subject_data(1, (Path("A01T.mat"),), data)


if __name__ == "__main__":
    unittest.main()
