from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.config import config_digest
from core.run_record import RunRecord
from evaluation.benchmark_audit import audit_benchmark, inspect_record


class BenchmarkAuditTests(unittest.TestCase):
    config = {
        "benchmark": {"shots_per_class": 1},
        "datasets": {"d": {"sampling_rate_hz": 128.0}},
    }

    def record(self, root: Path, *, method: str = "eegnet", seed: int = 11) -> Path:
        metrics = {
            "benchmark_schema_version": 2.0,
            "seed": float(seed),
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
            "dataset_input_trials": 50.0,
            "dataset_rejected_trials": 0.0,
            "fit_seconds": 1.0,
            "prediction_seconds": 0.1,
            "expected_calibration_error": 0.1,
            "coverage_at_threshold": 1.0,
            "selective_accuracy": 0.9,
        }
        path = root / "d" / method / f"seed_{seed}" / "subject_01.json"
        return RunRecord.create(
            config=self.config,
            seed=seed,
            git_commit="test",
            dataset="d",
            fold="subject_01",
            metrics=metrics,
        ).write_json(path)

    def inspect(self, path: Path) -> None:
        inspect_record(path, expected_config_sha256=config_digest(self.config))

    def test_process_diagnostics_require_qualified_scope_and_intact_bounds(self) -> None:
        cases = (
            ("cho2017", "ea_tangent_lr", {}, True),
            ("d", "ea_tangent_lr", {}, False),
            ("cho2017", "tangent_lr", {}, False),
            ("cho2017", "ea_tangent_lr", {"process_eigh_worker_count": 1}, False),
            ("cho2017", "ea_tangent_lr", {"process_eigh_block_count": 1.5}, False),
            ("cho2017", "ea_tangent_lr", {"process_eigh_block_count": 0}, False),
            ("cho2017", "ea_tangent_lr", {"process_eigh_minimum_free_memory_gib": 3.9}, False),
            ("cho2017", "ea_tangent_lr", {"process_eigh_worker_count": None}, False),
        )
        for dataset, method, changes, valid in cases:
            with (
                self.subTest(dataset=dataset, method=method, changes=changes),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                payload = json.loads(self.record(root, method=method).read_text())
                payload["dataset"] = dataset
                payload["metrics"].update({
                    "process_eigh_worker_count": 2,
                    "process_eigh_block_count": 3,
                    "process_eigh_minimum_free_memory_gib": 4.0,
                    **changes,
                })
                if payload["metrics"].get("process_eigh_worker_count") is None:
                    del payload["metrics"]["process_eigh_worker_count"]
                path = root / dataset / method / "seed_11/subject_01.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload))
                if valid:
                    self.inspect(path)
                else:
                    with self.assertRaises(ValueError):
                        self.inspect(path)

    def test_optional_csp_diagnostics_accept_certified_and_fallback_bands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for certified, automatic, ratio in ((6, 0, 1000), (2, 4, 65), (0, 6, None)):
                with self.subTest(certified=certified):
                    path = self.record(Path(directory), method="fbcsp")
                    payload = json.loads(path.read_text())
                    payload["metrics"].update(
                        {
                            "csp_certified_band_count": certified,
                            "csp_automatic_rank_band_count": automatic,
                        }
                    )
                    if ratio is not None:
                        payload["metrics"]["csp_minimum_certified_bound_ratio"] = ratio
                    path.write_text(json.dumps(payload))
                    self.inspect(path)

    def test_csp_diagnostic_arithmetic_and_method_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for method, certified, automatic, ratio in (
                ("eegnet", 6, 0, 1000),
                ("fbcsp", 5, 0, 1000),
                ("fbcsp", 6, 0, 64),
                ("fbcsp", 6, 0, None),
                ("fbcsp", 0, 6, 1000),
                ("fbcsp", 5.5, 0.5, 1000),
            ):
                with self.subTest(method=method, certified=certified, ratio=ratio):
                    path = self.record(Path(directory), method=method)
                    payload = json.loads(path.read_text())
                    payload["metrics"].update(
                        {
                            "csp_certified_band_count": certified,
                            "csp_automatic_rank_band_count": automatic,
                        }
                    )
                    if ratio is not None:
                        payload["metrics"]["csp_minimum_certified_bound_ratio"] = ratio
                    path.write_text(json.dumps(payload))
                    with self.assertRaises(ValueError):
                        self.inspect(path)

    def test_valid_high_score_flagged_without_claiming_scientific_clearance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.record(root)
            report = audit_benchmark(
                root,
                datasets_subjects={"d": ("subject_01",)},
                methods=("eegnet",),
                seeds=(11,),
                expected_config_sha256=config_digest(self.config),
            )
        self.assertTrue(report["complete"])
        self.assertEqual(report["valid_records"], 1)
        self.assertEqual(len(report["flagged_subjects"]), 1)
        self.assertEqual(len(report["flagged_methods"]), 1)
        self.assertFalse(report["scientific_review_complete"])

    def test_corrupt_metrics_fail_even_with_matching_hash_and_schema(self) -> None:
        corruptions = {
            "balanced_accuracy": 0.99,
            "cohen_kappa": 0.1,
            "class_support_left": 11.0,
            "query_trials": 21.0,
            "support_trials": 4.0,
            "dataset_input_trials": 20.0,
            "fit_seconds": -1.0,
            "expected_calibration_error": float("nan"),
            "seed": 23.0,
            "confusion_true_left_pred_left": 9.5,
        }
        with tempfile.TemporaryDirectory() as directory:
            for key, value in corruptions.items():
                with self.subTest(key=key):
                    path = self.record(Path(directory))
                    payload = json.loads(path.read_text())
                    payload["metrics"][key] = value
                    path.write_text(json.dumps(payload))
                    with self.assertRaises(ValueError):
                        self.inspect(path)

    def test_identity_config_and_timestamp_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for key, value in (
                ("dataset", "wrong"),
                ("fold", "wrong"),
                ("seed", 23),
                ("config", {"different": True}),
                ("timestamp_utc", "2026-08-31T12:00:00"),
                ("source_sha256", "not-a-digest"),
                ("git_dirty", "false"),
            ):
                with self.subTest(key=key):
                    path = self.record(Path(directory))
                    payload = json.loads(path.read_text())
                    payload[key] = value
                    path.write_text(json.dumps(payload))
                    with self.assertRaises(ValueError):
                        self.inspect(path)

    def test_missing_or_extra_identity_prevents_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.record(root)
            self.record(root, seed=99)
            report = audit_benchmark(
                root,
                datasets_subjects={"d": ("subject_01",)},
                methods=("eegnet",),
                seeds=(11, 23),
                expected_config_sha256=config_digest(self.config),
            )
        self.assertFalse(report["complete"])
        self.assertEqual(len(report["missing_records"]), 1)
        self.assertEqual(len(report["unexpected_records"]), 1)

    def test_reuse_requires_matching_measured_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.record(root, method="tangent_lr")
            path = self.record(root, method="tangent_lr", seed=23)
            payload = json.loads(path.read_text())
            payload["metrics"].update(
                reused_from_seed=11.0, seed=11.0, fit_seconds=0.0, prediction_seconds=0.0
            )
            path.write_text(json.dumps(payload))
            arguments = {
                "datasets_subjects": {"d": ("subject_01",)},
                "methods": ("tangent_lr",),
                "seeds": (11, 23),
                "expected_config_sha256": config_digest(self.config),
            }
            report = audit_benchmark(root, **arguments)
            self.assertTrue(report["complete"])
            payload["metrics"]["expected_calibration_error"] = 0.2
            path.write_text(json.dumps(payload))
            report = audit_benchmark(root, **arguments)
            self.assertFalse(report["complete"])
            self.assertEqual(len(report["invalid_records"]), 1)

    def test_neural_reuse_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.record(Path(directory))
            payload = json.loads(path.read_text())
            payload["metrics"]["reused_from_seed"] = 23.0
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                self.inspect(path)
