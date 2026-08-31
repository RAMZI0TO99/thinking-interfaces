from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from core.config import config_digest
from core.run_record import RunRecord
from evaluation.benchmark_audit import audit_benchmark
from evaluation.plausibility_packet import build_plausibility_packet


class PlausibilityPacketTests(unittest.TestCase):
    config = {"benchmark": {"shots_per_class": 1}}

    def setup_evidence(self, root):
        benchmark = root / "runs" / "benchmark"
        subjects = ("subject_01", "subject_02")
        corpus_rows = []
        for subject in subjects:
            corpus_rows.append(
                {
                    "dataset": "d",
                    "subject": subject,
                    "input_trials": 22,
                    "retained_trials": 22,
                    "rejected_trials": 0,
                    "support_trials": 2,
                    "query_trials": 20,
                    "retained_class_counts": {"left": 11, "right": 11},
                }
            )
            metrics = {
                "benchmark_schema_version": 2.0,
                "seed": 11.0,
                "balanced_accuracy": 0.9,
                "cohen_kappa": 0.8,
                "class_support_left": 10.0,
                "class_support_right": 10.0,
                "confusion_true_left_pred_left": 9.0,
                "confusion_true_left_pred_right": 1.0,
                "confusion_true_right_pred_left": 1.0,
                "confusion_true_right_pred_right": 9.0,
                "query_trials": 20.0,
                "support_trials": 2.0,
                "dataset_input_trials": 44.0,
                "dataset_rejected_trials": 0.0,
                "fit_seconds": 1.0,
                "prediction_seconds": 0.1,
                "expected_calibration_error": 0.1,
                "coverage_at_threshold": 1.0,
                "selective_accuracy": 0.9,
            }
            RunRecord.create(
                config=self.config,
                seed=11,
                git_commit="test",
                dataset="d",
                fold=subject,
                metrics=metrics,
            ).write_json(benchmark / "d" / "eegnet" / "seed_11" / f"{subject}.json")
        corpus = {
            "complete": True,
            "config_sha256": config_digest(self.config),
            "artifact_snapshot_sha256": "a" * 64,
            "subjects": corpus_rows,
            "subject_count": 2,
            "no_exact_train_query_copies": True,
        }
        integrity = self.audit(benchmark)
        return corpus, integrity

    def audit(self, benchmark, seeds=(11,)):
        return audit_benchmark(
            benchmark,
            datasets_subjects={"d": ("subject_01", "subject_02")},
            methods=("eegnet",),
            seeds=seeds,
            expected_config_sha256=config_digest(self.config),
        )

    def packet(self, root, corpus, integrity):
        return build_plausibility_packet(
            root, config=self.config, integrity=integrity, corpus=corpus
        )

    def test_counts_and_all_flags_are_exposed_without_automatic_review_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus, integrity = self.setup_evidence(root)
            result = self.packet(root, corpus, integrity)
        self.assertTrue(result["record_input_counts_passed"])
        self.assertTrue(result["benchmark_complete"])
        self.assertEqual(result["records_cross_checked"], 2)
        self.assertEqual(len(result["flagged_subject_method_cases"]), 2)
        self.assertFalse(result["local_review_complete"])
        self.assertFalse(result["scientific_leakage_clearance"])
        run = result["flagged_subject_method_cases"][0]["runs"][0]
        self.assertEqual(run["class_recall"], {"left": 0.9, "right": 0.9})
        self.assertEqual(run["query_class_counts"], {"left": 10, "right": 10})

    def test_internally_valid_result_with_wrong_input_counts_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus, _ = self.setup_evidence(root)
            path = root / "runs/benchmark/d/eegnet/seed_11/subject_01.json"
            data = json.loads(path.read_text())
            data["metrics"]["dataset_input_trials"] = 50.0
            path.write_text(json.dumps(data))
            integrity = self.audit(root / "runs/benchmark")
            self.assertTrue(integrity["complete"])
            result = self.packet(root, corpus, integrity)
        self.assertFalse(result["record_input_counts_passed"])
        self.assertEqual(
            result["record_input_count_mismatches"],
            {"d/eegnet/seed_11/subject_01.json": ["dataset_input_trials"]},
        )

    def test_changed_record_and_changed_snapshot_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus, integrity = self.setup_evidence(root)
            changed = copy.deepcopy(integrity)
            changed["record_snapshot_sha256"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "file snapshot"):
                self.packet(root, corpus, changed)
            path = root / "runs/benchmark/d/eegnet/seed_11/subject_01.json"
            path.write_text(path.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "record changed"):
                self.packet(root, corpus, integrity)

    def test_partial_grid_never_becomes_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus, _ = self.setup_evidence(root)
            integrity = self.audit(root / "runs/benchmark", seeds=(11, 23))
            result = self.packet(root, corpus, integrity)
        self.assertFalse(result["benchmark_complete"])
        self.assertFalse(result["local_review_complete"])

    def test_invalid_corpus_and_escaping_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus, integrity = self.setup_evidence(root)
            for update in ({"config_sha256": "wrong"}, {"subject_count": 3}):
                with self.subTest(update=update), self.assertRaises(ValueError):
                    self.packet(root, {**corpus, **update}, integrity)
            corpus["subjects"][0]["support_trials"] = 3
            with self.assertRaisesRegex(ValueError, "episode counts"):
                self.packet(root, corpus, integrity)
            corpus["subjects"][0]["support_trials"] = 2
            integrity["record_files"] = {"../../elsewhere.json": "b" * 64}
            integrity["record_snapshot_sha256"] = hashlib.sha256(
                ("../../elsewhere.json:" + "b" * 64).encode()
            ).hexdigest()
            with self.assertRaisesRegex(ValueError, "escapes"):
                self.packet(root, corpus, integrity)
