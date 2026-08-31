from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluation.reporting import (
    RecordObservation,
    aggregate_observations,
    missing_records,
    write_benchmark_csv,
)


class ReportingTests(unittest.TestCase):
    def test_seeds_are_averaged_before_subject_interval(self) -> None:
        rows = aggregate_observations(
            (
                RecordObservation("d", "m", "A", 1, 0.6),
                RecordObservation("d", "m", "A", 2, 0.8),
                RecordObservation("d", "m", "B", 1, 0.4),
                RecordObservation("d", "m", "B", 2, 0.6),
            )
        )
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0].mean, 0.6)
        self.assertEqual(rows[0].subject_count, 2)
        self.assertEqual(rows[0].seed_count, 2)
        self.assertAlmostEqual(rows[0].seed_mean_standard_deviation, 0.2 / 2**0.5)

    def test_deterministic_seed_variation_is_zero(self) -> None:
        row = aggregate_observations(
            tuple(
                RecordObservation("d", "m", subject, seed, score)
                for subject, score in (("A", 0.6), ("B", 0.8))
                for seed in (11, 23, 37)
            )
        )[0]
        self.assertEqual(row.seed_mean_standard_deviation, 0.0)
        self.assertGreater(row.standard_deviation, 0.0)

    def test_duplicate_or_nonfinite_observations_fail(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_observations((RecordObservation("d", "m", "A", 1, float("nan")),))
        observation = RecordObservation("d", "m", "A", 1, 0.6)
        with self.assertRaises(ValueError):
            aggregate_observations((observation, observation))

    def test_missing_grid_and_atomic_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = missing_records(
                root,
                datasets_subjects={"d": ("A", "B")},
                methods=("m",),
                seeds=(1,),
            )
            self.assertEqual(len(missing), 2)
            output = write_benchmark_csv((), root / "table.csv")
            self.assertTrue(output.is_file())
