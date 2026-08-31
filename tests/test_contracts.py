from __future__ import annotations

import unittest

from core.contracts import Epoch, Split


class FakeArray:
    def __init__(self, shape: tuple[int, int]) -> None:
        self.shape = shape


class EpochTests(unittest.TestCase):
    def test_valid_epoch(self) -> None:
        epoch = Epoch(
            signal=FakeArray((3, 128)),
            channel_names=("C3", "CZ", "C4"),
            sampling_rate_hz=128.0,
            subject_id="A01",
            dataset="bci_iv_2a",
            event_label="left_hand",
        )
        self.assertEqual(epoch.signal.shape, (3, 128))

    def test_channel_count_must_match(self) -> None:
        with self.assertRaisesRegex(ValueError, "channel_names"):
            Epoch(
                signal=FakeArray((2, 128)),
                channel_names=("C3",),
                sampling_rate_hz=128.0,
                subject_id="A01",
                dataset="bci_iv_2a",
                event_label="left_hand",
            )


class SplitTests(unittest.TestCase):
    def test_subject_overlap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "subjects"):
            Split(
                support_indices=(0, 1),
                query_indices=(2,),
                support_subjects=frozenset({"A01"}),
                query_subjects=frozenset({"A01"}),
            )

    def test_disjoint_split_is_valid(self) -> None:
        split = Split(
            support_indices=(0, 1),
            query_indices=(2,),
            support_subjects=frozenset({"A01"}),
            query_subjects=frozenset({"A02"}),
        )
        self.assertFalse(split.support_subjects & split.query_subjects)

    def test_duplicate_indices_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            Split(
                support_indices=(0, 0),
                query_indices=(2,),
                support_subjects=frozenset({"A01"}),
                query_subjects=frozenset({"A02"}),
            )

    def test_negative_indices_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            Split(
                support_indices=(-1,),
                query_indices=(2,),
                support_subjects=frozenset({"A01"}),
                query_subjects=frozenset({"A02"}),
            )


if __name__ == "__main__":
    unittest.main()
