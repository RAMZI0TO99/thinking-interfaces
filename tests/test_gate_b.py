from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import config_digest
from core.run_record import RunRecord
from evaluation.gate_b import evaluate_gate_b
from evaluation.gate_evidence import GateEvidence


class GateBTests(unittest.TestCase):
    config = {"benchmark": {"shots_per_class": 1}}

    def grid(self, root: Path) -> Path:
        for seed in (11, 23):
            for subject, correct in (("subject_001", 6), ("subject_002", 7)):
                score = correct / 10
                path = root / "cho2017" / "eegnet" / f"seed_{seed}" / f"{subject}.json"
                RunRecord.create(
                    config=self.config,
                    seed=seed,
                    git_commit="test",
                    dataset="cho2017",
                    fold=subject,
                    metrics={
                        "benchmark_schema_version": 2.0,
                        "seed": float(seed),
                        "balanced_accuracy": score,
                        "cohen_kappa": 2 * score - 1,
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
                        "fit_seconds": 1.0,
                        "prediction_seconds": 0.1,
                        "expected_calibration_error": 0.1,
                        "coverage_at_threshold": 0.0,
                    },
                ).write_json(path)
        return path

    def evaluate(self, root: Path, *, signed: bool = True, evidence: bool = True):
        # Arithmetic-only unit tests; disk-backed evidence is tested separately
        # in test_gate_evidence.py without stubbing its verifier.
        with patch(
            "evaluation.gate_b.verify_gate_evidence",
            return_value=GateEvidence(True, True, True, True, True),
        ):
            return evaluate_gate_b(
                root,
                project_root=root,
                dataset_subjects={"cho2017": ("subject_001", "subject_002")},
                methods=("eegnet",),
                seeds=(11, 23),
                preprocessing_frozen=True,
                margin_source_dataset="cho2017",
                margin_source_method="eegnet",
                target_power=0.8,
                alpha=0.05,
                upstream_gate_a_signed=signed,
                artifact_audit_passed=evidence,
                demonstrator_passed=evidence,
                expected_config_sha256=config_digest(self.config),
            )

    def test_complete_grid_and_freeze_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.grid(root)
            result = self.evaluate(root)
        self.assertTrue(result.passed)
        self.assertTrue(result.benchmark_integrity_passed)
        self.assertAlmostEqual(result.achieved_power, 0.8)

    def test_missing_record_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.evaluate(Path(directory))
        self.assertFalse(result.passed)
        self.assertEqual(result.missing_records, 4)

    def test_corrupted_arithmetic_prevents_completion_and_margin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.grid(root)
            payload = json.loads(path.read_text())
            payload["metrics"]["balanced_accuracy"] = 0.99
            path.write_text(json.dumps(payload))
            result = self.evaluate(root)
        self.assertFalse(result.local_deliverables_complete)
        self.assertEqual(result.invalid_records, 1)
        self.assertEqual(result.equivalence_margin, 0)

    def test_upstream_and_local_evidence_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.grid(root)
            unsigned = self.evaluate(root, signed=False)
            no_evidence = self.evaluate(root, evidence=False)
        self.assertTrue(unsigned.local_deliverables_complete)
        self.assertFalse(unsigned.passed)
        self.assertFalse(no_evidence.local_deliverables_complete)
