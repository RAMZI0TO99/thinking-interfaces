from __future__ import annotations

import unittest

import numpy as np

from encoder.eegnet_baseline import (
    SessionSplit,
    make_session_split,
    shuffle_development_targets,
)


class SessionSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.labels = np.asarray((["a", "b"] * 20) + (["a", "b"] * 10))
        self.sessions = np.asarray((["train"] * 40) + (["test"] * 20))

    def test_test_session_is_held_out_and_development_is_complete(self) -> None:
        split = make_session_split(
            self.labels,
            self.sessions,
            train_session="train",
            test_session="test",
            validation_fraction=0.25,
            seed=11,
        )
        self.assertEqual(set(split.test.tolist()), set(range(40, 60)))
        self.assertEqual(set(split.train.tolist()) | set(split.validation.tolist()), set(range(40)))
        self.assertEqual(len(split.train), 30)
        self.assertEqual(len(split.validation), 10)
        self.assertEqual(set(self.labels[split.validation]), {"a", "b"})

    def test_split_is_deterministic(self) -> None:
        first = make_session_split(
            self.labels,
            self.sessions,
            train_session="train",
            test_session="test",
            validation_fraction=0.25,
            seed=23,
        )
        second = make_session_split(
            self.labels,
            self.sessions,
            train_session="train",
            test_session="test",
            validation_fraction=0.25,
            seed=23,
        )
        np.testing.assert_array_equal(first.train, second.train)
        np.testing.assert_array_equal(first.validation, second.validation)

    def test_overlap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "disjoint"):
            SessionSplit(
                train=np.asarray([0, 1], dtype=np.int64),
                validation=np.asarray([1, 2], dtype=np.int64),
                test=np.asarray([3], dtype=np.int64),
            )

    def test_same_session_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "differ"):
            make_session_split(
                self.labels,
                self.sessions,
                train_session="train",
                test_session="train",
                validation_fraction=0.25,
                seed=11,
            )

    def test_label_shuffle_never_changes_test_targets(self) -> None:
        split = make_session_split(
            self.labels,
            self.sessions,
            train_session="train",
            test_session="test",
            validation_fraction=0.25,
            seed=11,
        )
        targets = np.arange(60, dtype=np.int64)
        shuffled = shuffle_development_targets(targets, split, seed=11)
        np.testing.assert_array_equal(shuffled[split.test], targets[split.test])
        self.assertEqual(
            sorted(shuffled[np.concatenate((split.train, split.validation))].tolist()),
            list(range(40)),
        )
        self.assertFalse(np.array_equal(shuffled[split.train], targets[split.train]))


if __name__ == "__main__":
    unittest.main()
