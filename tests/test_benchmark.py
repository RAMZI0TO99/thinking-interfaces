from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

from data.profile_a import save_epoch_artifact
from evaluation.alignment import align_training_subjects
from evaluation.baselines import FilterBankCSP, TorchTrainingConfig
from evaluation.benchmark import (
    DatasetMatrix,
    _decoder,
    load_dataset_matrix,
    run_benchmark,
    run_fold,
    valid_run_record,
)


class BenchmarkTests(unittest.TestCase):
    def test_process_eigh_is_scoped_and_diagnostics_are_saved(self) -> None:
        class Candidate:
            stats = {
                "parallel_calls": 1, "worker_pids": [101, 102], "blocks": 12,
                "minimum_observed_free_memory_gib": 4.5,
            }

            def __enter__(self):
                return self

            def __exit__(self, *unused):
                pass

        for dataset, method, ready, expected in (
            ("cho2017", "ea_tangent_lr", True, 1),
            ("cho2017", "ea_tangent_lr", False, 0),
            ("cho2017", "tangent_lr", True, 0),
            ("mmidb", "ea_tangent_lr", True, 0),
        ):
            with (
                self.subTest(dataset=dataset, method=method, ready=ready),
                tempfile.TemporaryDirectory() as directory,
                patch("evaluation.benchmark.load_toml",
                      return_value={"tangent_process": {"enabled": True}}),
                patch("evaluation.benchmark.ProcessEighProbe", return_value=Candidate()) as factory,
            ):
                outputs = run_benchmark(
                    replace(self.matrix, dataset=dataset), methods=(method,), seeds=(11,),
                    shots_per_class=2, confidence_threshold=0.7, torch_config=self.training,
                    output_root=Path(directory), config={"test": True}, max_new_runs=1,
                    process_eigh_startup_headroom=ready,
                )
                self.assertEqual(factory.call_count, expected)
                metrics = json.loads(outputs[0].read_text())["metrics"]
                if expected:
                    self.assertEqual(metrics["process_eigh_worker_count"], 2)
                    self.assertEqual(metrics["process_eigh_block_count"], 12)
                    self.assertEqual(metrics["process_eigh_minimum_free_memory_gib"], 4.5)
                else:
                    self.assertNotIn("process_eigh_worker_count", metrics)

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

    def test_opt_in_csp_certificate_counts_are_saved_with_the_fit(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            patch(
                "evaluation.benchmark.load_toml",
                return_value={"csp": {"certify_full_numerical_rank": True}},
            ),
        ):
            outputs = run_benchmark(
                self.matrix,
                methods=("fbcsp",),
                seeds=(11,),
                shots_per_class=2,
                confidence_threshold=0.7,
                torch_config=self.training,
                output_root=Path(directory),
                config={"test": True},
                max_new_runs=1,
            )
            metrics = json.loads(outputs[0].read_text("utf-8"))["metrics"]
            self.assertEqual(metrics["csp_certified_band_count"], 6)
            self.assertEqual(metrics["csp_automatic_rank_band_count"], 0)
            self.assertGreater(metrics["csp_minimum_certified_bound_ratio"], 64)

    def test_csp_runtime_switch_rejects_ambiguous_text(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            patch(
                "evaluation.benchmark.load_toml",
                return_value={"csp": {"certify_full_numerical_rank": "false"}},
            ),
            self.assertRaises(ValueError),
        ):
            run_benchmark(
                self.matrix,
                methods=("fbcsp",),
                seeds=(11,),
                shots_per_class=2,
                confidence_threshold=0.7,
                torch_config=self.training,
                output_root=Path(directory),
                config={"test": True},
                max_new_runs=1,
            )

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

    def test_cached_filter_bank_does_not_copy_unused_raw_signals(self) -> None:
        class NoRawIndexing(np.ndarray):
            def __getitem__(self, key):
                raise AssertionError("cached FBCSP should not index raw signal arrays")

        decoder = _decoder("fbcsp", self.matrix, classes=2, seed=11, torch_config=self.training)
        self.assertIsInstance(decoder, FilterBankCSP)
        bands = decoder.filtered_bands(self.matrix.signals)
        arguments = {
            "target_subject": "C",
            "method": "fbcsp",
            "seed": 11,
            "shots_per_class": 2,
            "confidence_threshold": 0.7,
            "torch_config": self.training,
        }
        direct = run_fold(self.matrix, **arguments)
        guarded = replace(self.matrix, signals=self.matrix.signals.view(NoRawIndexing))
        cached = run_fold(guarded, prefiltered_fbcsp=bands, **arguments)
        direct_metrics, cached_metrics = direct.scalar_metrics(), cached.scalar_metrics()
        for name in ("fit_seconds", "prediction_seconds"):
            direct_metrics.pop(name)
            cached_metrics.pop(name)
        self.assertEqual(direct_metrics, cached_metrics)

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
