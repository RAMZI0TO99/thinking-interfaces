from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from data.profile_a import save_epoch_artifact
from evaluation.alignment import align_training_subjects
from evaluation.baselines import TorchTrainingConfig
from evaluation.benchmark import (
    DatasetMatrix,
    load_dataset_matrix,
    run_benchmark,
    run_fold,
    valid_run_record,
)


class BenchmarkTests(unittest.TestCase):
    def setUp(self) -> None:
        rng = np.random.default_rng(9)
        signals = rng.normal(size=(36, 3, 64)).astype(np.float32)
        labels = np.asarray((["left", "right"] * 6) * 3)
        subjects = np.asarray(["A"] * 12 + ["B"] * 12 + ["C"] * 12)
        signals[labels == "right", 0] *= 2
        self.matrix = DatasetMatrix(
            "synthetic", signals, labels, subjects, ("C3", "Cz", "C4"), 64.0
        )
        self.training = TorchTrainingConfig(epochs=1, device="cpu")

    def test_query_is_held_out_and_fold_runs(self) -> None:
        result = run_fold(
            self.matrix,
            target_subject="C",
            method="tangent_lr",
            seed=11,
            shots_per_class=2,
            confidence_threshold=0.7,
            torch_config=self.training,
        )
        self.assertEqual(result.support_trials, 4)
        self.assertEqual(result.query_trials, 8)
        metrics = result.scalar_metrics()
        self.assertEqual(metrics["benchmark_schema_version"], 2.0)
        self.assertEqual(metrics["class_support_left"], 4.0)
        self.assertIn("confusion_true_left_pred_right", metrics)

    def test_cached_alignment_matches_fold_local_alignment(self) -> None:
        local = run_fold(
            self.matrix,
            target_subject="C",
            method="ea_tangent_lr",
            seed=11,
            shots_per_class=2,
            confidence_threshold=0.7,
            torch_config=self.training,
        )
        cached = run_fold(
            self.matrix,
            target_subject="C",
            method="ea_tangent_lr",
            seed=11,
            shots_per_class=2,
            confidence_threshold=0.7,
            torch_config=self.training,
            prealigned_source_signals=align_training_subjects(
                self.matrix.signals, self.matrix.subjects
            ),
        )
        self.assertAlmostEqual(local.balanced_accuracy, cached.balanced_accuracy)
        self.assertEqual(local.confusion_matrix, cached.confusion_matrix)

    def test_atomic_records_resume(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = run_benchmark(
                self.matrix,
                methods=("tangent_lr",),
                seeds=(11,),
                shots_per_class=2,
                confidence_threshold=0.7,
                torch_config=self.training,
                output_root=root,
                config={"test": True},
                max_new_runs=1,
            )
            self.assertEqual(len(first), 1)
            self.assertTrue(valid_run_record(first[0]))
            second = run_benchmark(
                self.matrix,
                methods=("tangent_lr",),
                seeds=(11,),
                shots_per_class=2,
                confidence_threshold=0.7,
                torch_config=self.training,
                output_root=root,
                config={"test": True},
            )
            self.assertEqual(len(second), 3)

    def test_deterministic_method_reuses_first_seed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outputs = run_benchmark(
                self.matrix,
                methods=("tangent_lr",),
                seeds=(11, 23),
                shots_per_class=2,
                confidence_threshold=0.7,
                torch_config=self.training,
                output_root=Path(directory),
                config={"test": True},
            )
            self.assertEqual(len(outputs), 6)
            payload = json.loads(outputs[-1].read_text(encoding="utf-8"))
            self.assertEqual(payload["metrics"]["reused_from_seed"], 11.0)
            self.assertEqual(payload["metrics"]["fit_seconds"], 0.0)
            original = json.loads(outputs[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["git_commit"], original["git_commit"])
            self.assertEqual(payload["source_sha256"], original["source_sha256"])

    def test_loaded_subject_names_are_not_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for subject in ("subject_01", "subject_02"):
                save_epoch_artifact(
                    root / f"{subject}.npz",
                    signals=np.zeros((2, 3, 8), dtype=np.float32),
                    labels=np.asarray(["left", "right"]),
                    sessions=np.asarray(["0", "0"]),
                    runs=np.asarray(["0", "0"]),
                    trial_indices=np.asarray([0, 1]),
                    channel_names=("C3", "Cz", "C4"),
                )
            matrix = load_dataset_matrix(root, dataset="synthetic", sampling_rate_hz=2.0)
            self.assertEqual(set(matrix.subjects.tolist()), {"subject_01", "subject_02"})

    def test_loader_applies_artifact_threshold_before_splitting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for subject in ("subject_01", "subject_02"):
                signals = np.zeros((4, 3, 8), dtype=np.float32)
                signals[0, 0, 0] = 2.0
                save_epoch_artifact(
                    root / f"{subject}.npz",
                    signals=signals,
                    labels=np.asarray(["left", "right", "left", "right"]),
                    sessions=np.asarray(["0"] * 4),
                    runs=np.asarray(["0"] * 4),
                    trial_indices=np.arange(4),
                    channel_names=("C3", "Cz", "C4"),
                )
            matrix = load_dataset_matrix(
                root,
                dataset="synthetic",
                sampling_rate_hz=2.0,
                absolute_peak_volts=1.0,
            )
            self.assertEqual(matrix.input_trials, 8)
            self.assertEqual(matrix.rejected_trials, 2)
            self.assertEqual(matrix.signals.shape[0], 6)
