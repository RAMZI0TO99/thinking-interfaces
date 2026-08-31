from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from core.config import config_digest
from core.run_record import RunRecord
from evaluation.benchmark_diagnostics import (
    aggregate_diagnostics,
    read_audited_snapshot,
    write_diagnostics_csv,
)


class BenchmarkDiagnosticsTests(unittest.TestCase):
    config = {"benchmark": {"shots_per_class": 1}}

    def grid(self, root: Path, *, deterministic: bool = False):
        files = {}
        for seed in (11, 23):
            for subject, correct in (("A", 9), ("B", 8)):
                reused = deterministic and seed == 23
                metrics = {
                    "benchmark_schema_version": 2.0,
                    "seed": 11.0 if reused else float(seed),
                    "balanced_accuracy": correct / 10,
                    "cohen_kappa": correct / 5 - 1,
                    "class_support_left": 10.0,
                    "class_support_right": 10.0,
                    "confusion_true_left_pred_left": float(correct),
                    "confusion_true_left_pred_right": float(10 - correct),
                    "confusion_true_right_pred_left": float(10 - correct),
                    "confusion_true_right_pred_right": float(correct),
                    "query_trials": 20.0,
                    "support_trials": 2.0,
                    "dataset_input_trials": 50.0,
                    "dataset_rejected_trials": 0.0,
                    "fit_seconds": 0.0 if reused else 1.0,
                    "prediction_seconds": 0.0 if reused else 0.1,
                    "expected_calibration_error": 0.2 if subject == "A" else 0.1,
                    "coverage_at_threshold": 0.0,
                }
                if reused:
                    metrics["reused_from_seed"] = 11.0
                method = "fbcsp" if deterministic else "eegnet"
                path = root / "d" / method / f"seed_{seed}" / f"{subject}.json"
                RunRecord.create(
                    config=self.config,
                    seed=seed,
                    git_commit="test",
                    dataset="d",
                    fold=subject,
                    metrics=metrics,
                ).write_json(path)
                files[path.relative_to(root).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
        return files

    def read(self, root, files):
        return read_audited_snapshot(root, files, expected_config_sha256=config_digest(self.config))

    def test_counts_kappa_empty_coverage_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.read(root, self.grid(root))
            rows = aggregate_diagnostics(records, confidence_threshold=0.7)
            row = rows[0]
            self.assertAlmostEqual(row.cohen_kappa_subject_mean, 0.7)
            self.assertAlmostEqual(row.expected_calibration_error_subject_mean, 0.15)
            self.assertIsNone(row.selective_accuracy_subject_mean)
            self.assertEqual(row.selective_accuracy_record_count, 0)
            self.assertEqual(
                json.loads(row.query_class_counts_including_seed_repeats_json),
                {"left": 40, "right": 40},
            )
            self.assertEqual(
                json.loads(row.confusion_counts_including_seed_repeats_json), [[34, 6], [6, 34]]
            )
            self.assertEqual(row.query_evaluations_including_seed_repeats, 80)
            output = write_diagnostics_csv(rows, root / "diagnostics.csv")
            with output.open(newline="", encoding="utf-8") as stream:
                exported = list(csv.DictReader(stream))
            self.assertEqual(exported[0]["selective_accuracy_subject_mean"], "")

    def test_partial_grid_still_weights_subjects_equally(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = self.grid(root)
            del files["d/eegnet/seed_23/B.json"]
            row = aggregate_diagnostics(self.read(root, files), confidence_threshold=0.7)[0]
        self.assertEqual(row.record_count, 3)
        self.assertAlmostEqual(row.cohen_kappa_subject_mean, 0.7)
        self.assertAlmostEqual(row.expected_calibration_error_subject_mean, 0.15)

    def test_reused_timings_do_not_dilute_per_trial_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = aggregate_diagnostics(
                self.read(root, self.grid(root, deterministic=True)), confidence_threshold=0.7
            )[0]
        self.assertEqual(row.computed_records, 2)
        self.assertEqual(row.reused_records, 2)
        self.assertEqual(row.measured_fit_seconds, 2.0)
        self.assertAlmostEqual(row.amortized_batch_prediction_seconds_per_trial, 0.005)

    def test_snapshot_ignores_new_files_but_rejects_changed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = self.grid(root)
            extra = root / "d" / "eegnet" / "seed_37" / "A.json"
            extra.parent.mkdir()
            extra.write_text("not part of this snapshot")
            self.assertEqual(len(self.read(root, files)), 4)
            path = root / "d" / "eegnet" / "seed_11" / "A.json"
            payload = json.loads(path.read_text())
            payload["git_commit"] = "changed"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "changed during reporting"):
                self.read(root, files)

    def test_duplicate_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = self.read(root, self.grid(root))
            with self.assertRaises(ValueError):
                aggregate_diagnostics((records[0], records[0]), confidence_threshold=0.7)
            with self.assertRaisesRegex(ValueError, "escapes"):
                self.read(root, {"../outside.json": "hash"})
