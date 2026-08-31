from __future__ import annotations

import unittest

from evaluation.benchmark_audit import AuditedRecord
from evaluation.compute_estimate import estimate_remaining_work


def observation(
    method: str, subject: str, seed: int, seconds: float, *, origin: int | None = None
) -> AuditedRecord:
    metrics = {"fit_seconds": seconds, "prediction_seconds": 0.0}
    if origin is not None:
        metrics["reused_from_seed"] = float(origin)
    return AuditedRecord("example", method, subject, seed, 2, metrics, "hash")


class ComputeEstimateTests(unittest.TestCase):
    def test_deterministic_seed_copies_do_not_multiply_fits_or_bias_median(self) -> None:
        report = estimate_remaining_work(
            [observation("fbcsp", "A", 11, 100), observation("fbcsp", "A", 23, 0, origin=11)],
            dataset_subjects={"example": ("A", "B")},
            methods=("fbcsp",),
            seeds=(11, 23, 37),
        )
        self.assertEqual(report["remaining_records"], 4)
        self.assertEqual(report["remaining_fit_units"], 1)
        self.assertEqual(report["remaining_seed_copy_records"], 3)
        self.assertEqual(report["rows"][0]["median_fit_prediction_seconds"], 100)
        self.assertAlmostEqual(report["all_work_fit_prediction_hours_estimate"], 100 / 3600)

    def test_unknown_method_is_not_given_another_methods_runtime(self) -> None:
        report = estimate_remaining_work(
            [observation("eegnet", "A", 11, 2)],
            dataset_subjects={"example": ("A", "B")},
            methods=("eegnet", "fbcsp"),
            seeds=(11, 23),
        )
        self.assertEqual(report["remaining_fit_units"], 5)
        self.assertEqual(report["unmeasured_fit_units"], 2)
        self.assertIsNone(report["all_work_fit_prediction_hours_estimate"])
        self.assertAlmostEqual(report["known_work_fit_prediction_hours_estimate"], 6 / 3600)

    def test_complete_grid_has_zero_remaining_work_even_without_positive_timing(self) -> None:
        report = estimate_remaining_work(
            [observation("eegnet", "A", 11, 0)],
            dataset_subjects={"example": ("A",)},
            methods=("eegnet",),
            seeds=(11,),
        )
        self.assertEqual(report["all_work_fit_prediction_hours_estimate"], 0)
        self.assertEqual(report["unmeasured_fit_units"], 0)

    def test_rejects_duplicate_or_orphan_records_and_invalid_durations(self) -> None:
        valid = observation("fbcsp", "A", 11, 10)
        for records in (
            [valid, valid],
            [observation("fbcsp", "A", 23, 0, origin=11)],
            [observation("fbcsp", "A", 11, -1)],
            [observation("fbcsp", "A", 11, float("nan"))],
            [observation("fbcsp", "missing", 11, 1)],
        ):
            with self.subTest(records=records), self.assertRaises(ValueError):
                estimate_remaining_work(
                    records,
                    dataset_subjects={"example": ("A", "B")},
                    methods=("fbcsp",),
                    seeds=(11, 23),
                )
