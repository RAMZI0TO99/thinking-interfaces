from __future__ import annotations

import unittest

from evaluation.aggregate import subject_level_interval


class SubjectLevelIntervalTests(unittest.TestCase):
    def test_seeds_are_averaged_before_subject_interval(self) -> None:
        summary = subject_level_interval(
            [(1, 0.6), (1, 0.8), (2, 0.4), (2, 0.6)], confidence_level=0.95
        )
        self.assertEqual(summary.subject_means, {1: 0.7, 2: 0.5})
        self.assertAlmostEqual(summary.mean, 0.6)
        self.assertEqual(summary.subject_count, 2)
        self.assertLess(summary.confidence_interval[0], summary.mean)
        self.assertGreater(summary.confidence_interval[1], summary.mean)

    def test_single_subject_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "two subjects"):
            subject_level_interval([(1, 0.6), (1, 0.7)])

    def test_non_finite_score_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            subject_level_interval([(1, 0.6), (2, float("nan"))])


if __name__ == "__main__":
    unittest.main()
