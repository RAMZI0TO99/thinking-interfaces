from __future__ import annotations

import unittest

from core.splits import earliest_balanced_episode, grouped_k_fold, leave_one_subject_out


class SubjectSplitTests(unittest.TestCase):
    def test_loso_has_disjoint_subjects_on_every_fold(self) -> None:
        subjects = ["A", "A", "B", "B", "C", "C"]
        folds = leave_one_subject_out(subjects)
        self.assertEqual(len(folds), 3)
        self.assertTrue(all(not fold.support_subjects & fold.query_subjects for fold in folds))

    def test_grouped_fold_never_splits_a_subject(self) -> None:
        subjects = ["A", "A", "B", "B", "C", "C", "D", "D"]
        folds = grouped_k_fold(subjects, folds=2)
        self.assertTrue(all(not fold.support_subjects & fold.query_subjects for fold in folds))

    def test_episode_uses_earliest_balanced_trials(self) -> None:
        episode = earliest_balanced_episode(
            ["left", "right", "left", "right", "left", "right"],
            subject_id="mmidb/S001",
            shots_per_class=2,
        )
        self.assertEqual(episode.support_indices, (0, 1, 2, 3))
        self.assertEqual(episode.query_indices, (4, 5))
