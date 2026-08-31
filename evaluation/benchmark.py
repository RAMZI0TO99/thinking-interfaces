"""Resumable LOSO benchmark execution with support-only target adaptation."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from gc import collect as collect_garbage
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.config import config_digest, load_toml
from core.gpu_cooling import cool_gpu, load_cooling_policy
from core.metrics import classification_report
from core.provenance import capture_source
from core.run_record import RunRecord
from core.splits import earliest_balanced_episode
from data.artifact_rejection import reject_amplitude_artifacts
from data.unified import UnifiedArtifact, load_unified_artifact
from evaluation.alignment import EuclideanAlignment, align_training_subjects
from evaluation.baselines import (
    BASELINE_METHODS,
    BraindecodeClassifier,
    FilterBankCSP,
    TangentSpaceLogistic,
    TorchTrainingConfig,
)
from evaluation.csp_rank_certificate import FullRankCertificate
from evaluation.process_eigh_probe import ProcessEighProbe
from evaluation.process_eigh_runtime import process_eigh_enabled
from evaluation.realtime_metrics import accuracy_coverage_curve, calibration_report

FloatArray = NDArray[np.float32]
IntArray = NDArray[np.int64]
DETERMINISTIC_METHODS = frozenset({"fbcsp", "tangent_lr", "ea_tangent_lr"})


@dataclass(frozen=True, slots=True)
class DatasetMatrix:
    dataset: str
    signals: FloatArray
    labels: NDArray[np.str_]
    subjects: NDArray[np.str_]
    channel_names: tuple[str, ...]
    sampling_rate_hz: float
    input_trials: int = 0
    rejected_trials: int = 0


def load_dataset_matrix(
    directory: Path,
    *,
    dataset: str,
    sampling_rate_hz: float,
    absolute_peak_volts: float | None = None,
) -> DatasetMatrix:
    paths = tuple(sorted(directory.glob("subject_*.npz")))
    if len(paths) < 2:
        raise ValueError(f"{dataset} needs at least two subject artifacts for LOSO")
    artifacts: list[UnifiedArtifact] = []
    input_trials = 0
    rejected_trials = 0
    for path in paths:
        artifact = load_unified_artifact(path)
        input_trials += int(artifact.signals.shape[0])
        if absolute_peak_volts is not None:
            artifact, rejection = reject_amplitude_artifacts(
                artifact, absolute_peak_volts=absolute_peak_volts
            )
            rejected_trials += rejection.rejected_trials
        artifacts.append(artifact)
    shape = artifacts[0].signals.shape[1:]
    names = artifacts[0].channel_names
    if any(item.signals.shape[1:] != shape or item.channel_names != names for item in artifacts):
        raise ValueError(f"{dataset} artifacts do not share channel/sample dimensions")
    signals = np.concatenate([item.signals for item in artifacts])
    labels = np.concatenate([item.labels for item in artifacts])
    subjects = np.concatenate(
        [np.full(item.labels.shape, path.stem) for path, item in zip(paths, artifacts, strict=True)]
    )
    return DatasetMatrix(
        dataset,
        signals,
        labels,
        subjects,
        names,
        sampling_rate_hz,
        input_trials,
        rejected_trials,
    )


def _decoder(
    method: str,
    matrix: DatasetMatrix,
    *,
    classes: int,
    seed: int,
    torch_config: TorchTrainingConfig,
) -> Any:
    base_method = method.removeprefix("ea_")
    if base_method == "tangent_lr":
        return TangentSpaceLogistic()
    if base_method == "fbcsp":
        nyquist = matrix.sampling_rate_hz / 2.0
        standard_bands = (
            (8.0, 12.0),
            (12.0, 16.0),
            (16.0, 20.0),
            (20.0, 24.0),
            (24.0, 28.0),
            (28.0, 32.0),
        )
        bands = tuple(
            (low, min(high, nyquist - 1.0)) for low, high in standard_bands if low < nyquist - 1.0
        )
        return FilterBankCSP(sampling_rate_hz=matrix.sampling_rate_hz, bands_hz=bands)
    return BraindecodeClassifier(
        base_method,
        channels=matrix.signals.shape[1],
        classes=classes,
        samples=matrix.signals.shape[2],
        sampling_rate_hz=matrix.sampling_rate_hz,
        seed=seed,
        training=torch_config,
    )


@dataclass(frozen=True, slots=True)
class BenchmarkFoldResult:
    target_subject: str
    method: str
    seed: int
    balanced_accuracy: float
    cohen_kappa: float
    expected_calibration_error: float
    coverage_at_threshold: float
    selective_accuracy: float | None
    fit_seconds: float
    prediction_seconds: float
    support_trials: int
    query_trials: int
    dataset_input_trials: int
    dataset_rejected_trials: int
    class_support: dict[str, int]
    confusion_matrix: tuple[tuple[int, ...], ...]
    class_names: tuple[str, ...]
    csp_rank_certificates: tuple[FullRankCertificate, ...] = ()

    def scalar_metrics(self) -> dict[str, float]:
        metrics = {
            key: float(value)
            for key, value in asdict(self).items()
            if isinstance(value, int | float) and not isinstance(value, bool)
        }
        metrics["benchmark_schema_version"] = 2.0
        for label, support in self.class_support.items():
            metrics[f"class_support_{label}"] = float(support)
        for true_index, true_label in enumerate(self.class_names):
            for predicted_index, predicted_label in enumerate(self.class_names):
                metrics[f"confusion_true_{true_label}_pred_{predicted_label}"] = float(
                    self.confusion_matrix[true_index][predicted_index]
                )
        return metrics


def run_fold(
    matrix: DatasetMatrix,
    *,
    target_subject: str,
    method: str,
    seed: int,
    shots_per_class: int,
    confidence_threshold: float,
    torch_config: TorchTrainingConfig,
    prealigned_source_signals: FloatArray | None = None,
    prefiltered_fbcsp: tuple[FloatArray, ...] | None = None,
    certify_csp_rank: bool = False,
) -> BenchmarkFoldResult:
    if method not in BASELINE_METHODS:
        raise ValueError(f"unknown baseline method: {method}")
    target_global = np.flatnonzero(matrix.subjects == target_subject)
    source_global = np.flatnonzero(matrix.subjects != target_subject)
    if not target_global.size or not source_global.size:
        raise ValueError("target and source trials must both be present")
    episode = earliest_balanced_episode(
        matrix.labels[target_global].tolist(),
        subject_id=target_subject,
        shots_per_class=shots_per_class,
    )
    support_global = target_global[np.asarray(episode.support_indices, dtype=np.int64)]
    query_global = target_global[np.asarray(episode.query_indices, dtype=np.int64)]
    train_global = np.concatenate((source_global, support_global))
    class_names = tuple(sorted(set(matrix.labels.tolist())))
    class_to_index = {name: index for index, name in enumerate(class_names)}
    targets = np.asarray([class_to_index[name] for name in matrix.labels], dtype=np.int64)
    train_signals: FloatArray | None = None
    query_signals: FloatArray | None = None
    if method.startswith("ea_"):
        target_aligner = EuclideanAlignment().fit(matrix.signals[support_global])
        aligned_support = target_aligner.transform(matrix.signals[support_global])
        if prealigned_source_signals is None:
            train_signals = align_training_subjects(
                matrix.signals[train_global], matrix.subjects[train_global]
            )
        else:
            if prealigned_source_signals.shape != matrix.signals.shape:
                raise ValueError("prealigned source signals must match the dataset matrix")
            train_signals = np.concatenate(
                (prealigned_source_signals[source_global], aligned_support)
            )
        query_signals = target_aligner.transform(matrix.signals[query_global])
    elif method != "fbcsp" or prefiltered_fbcsp is None:
        train_signals = matrix.signals[train_global]
        query_signals = matrix.signals[query_global]
    decoder = _decoder(
        method,
        matrix,
        classes=len(class_names),
        seed=seed,
        torch_config=torch_config,
    )
    fit_started = time.perf_counter()
    if certify_csp_rank:
        if not isinstance(decoder, FilterBankCSP):
            raise ValueError("CSP rank certification only applies to the FBCSP decoder")
        decoder.certify_rank = True
    if method == "fbcsp" and prefiltered_fbcsp is not None:
        if not isinstance(decoder, FilterBankCSP):
            raise TypeError("FBCSP cache requires a FilterBankCSP decoder")
        decoder.fit_prefiltered(
            prefiltered_fbcsp,
            targets[train_global],
            indices=train_global,
        )
    else:
        if train_signals is None:
            raise RuntimeError("uncached decoder needs training signals")
        decoder.fit(train_signals, targets[train_global])
    fit_seconds = time.perf_counter() - fit_started
    prediction_started = time.perf_counter()
    if method == "fbcsp" and prefiltered_fbcsp is not None:
        probabilities = np.asarray(
            decoder.predict_proba_prefiltered(
                prefiltered_fbcsp,
                indices=query_global,
            ),
            dtype=np.float32,
        )
    else:
        if query_signals is None:
            raise RuntimeError("uncached decoder needs query signals")
        probabilities = np.asarray(decoder.predict_proba(query_signals), dtype=np.float32)
    prediction_seconds = time.perf_counter() - prediction_started
    predicted = probabilities.argmax(axis=1)
    report = classification_report(
        [class_names[index] for index in targets[query_global]],
        [class_names[index] for index in predicted],
        labels=class_names,
    )
    calibration = calibration_report(probabilities, targets[query_global], bins=10)
    coverage = accuracy_coverage_curve(
        probabilities,
        targets[query_global],
        thresholds=(confidence_threshold,),
    )[0]
    return BenchmarkFoldResult(
        target_subject,
        method,
        seed,
        report.balanced_accuracy,
        report.cohen_kappa,
        calibration.expected_calibration_error,
        coverage.coverage,
        coverage.accuracy,
        fit_seconds,
        prediction_seconds,
        int(support_global.size),
        int(query_global.size),
        matrix.input_trials or int(matrix.signals.shape[0]),
        matrix.rejected_trials,
        report.class_support,
        report.confusion_matrix,
        class_names,
        tuple(decoder.rank_certificates) if isinstance(decoder, FilterBankCSP) else (),
    )


def valid_run_record(path: Path, *, expected_config_sha256: str | None = None) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        required = {"config", "config_sha256", "seed", "dataset", "fold", "metrics"}
        if not isinstance(payload, dict) or not required <= set(payload):
            return False
        metrics = payload["metrics"]
        config_matches = (
            expected_config_sha256 is None or payload.get("config_sha256") == expected_config_sha256
        )
        return (
            isinstance(metrics, dict)
            and metrics.get("benchmark_schema_version") == 2.0
            and config_matches
        )
    except (OSError, json.JSONDecodeError):
        return False


def _reusable_metrics(
    output_root: Path,
    *,
    dataset: str,
    method: str,
    subject: str,
    seeds: Sequence[int],
    expected_config_sha256: str,
) -> tuple[dict[str, float], int] | None:
    """Find a completed equivalent deterministic run for another seed."""

    if method not in DETERMINISTIC_METHODS:
        return None
    for source_seed in seeds:
        source = output_root / dataset / method / f"seed_{source_seed}" / f"{subject}.json"
        if not valid_run_record(source, expected_config_sha256=expected_config_sha256):
            continue
        payload = json.loads(source.read_text(encoding="utf-8"))
        raw_metrics = payload["metrics"]
        if not isinstance(raw_metrics, dict):
            continue
        metrics = {str(key): float(value) for key, value in raw_metrics.items()}
        metrics["fit_seconds"] = 0.0
        metrics["prediction_seconds"] = 0.0
        metrics["reused_from_seed"] = float(source_seed)
        return metrics, source_seed
    return None


def run_benchmark(
    matrix: DatasetMatrix,
    *,
    methods: Sequence[str],
    seeds: Sequence[int],
    shots_per_class: int,
    confidence_threshold: float,
    torch_config: TorchTrainingConfig,
    output_root: Path,
    config: Mapping[str, Any],
    max_new_runs: int | None = None,
    process_eigh_startup_headroom: bool = False,
) -> tuple[Path, ...]:
    """Run missing folds only and atomically write every completed record."""

    outputs: list[Path] = []
    completed = 0
    expected_config_sha256 = config_digest(config)
    source_provenance = capture_source(Path(__file__).resolve().parents[1])
    runtime = load_toml(Path(__file__).resolve().parents[1] / "configs" / "runtime_limits.toml")
    process_enabled = process_eigh_enabled(runtime)
    if type(process_eigh_startup_headroom) is not bool:
        raise ValueError("process startup headroom must be an explicit boolean")
    csp_settings = runtime.get("csp", {})
    if not isinstance(csp_settings, dict):
        raise ValueError("CSP runtime settings must be a table")
    certify_csp = csp_settings.get("certify_full_numerical_rank", False)
    if type(certify_csp) is not bool:
        raise ValueError("CSP rank certification must be an explicit boolean")
    cooling_policy = (
        load_cooling_policy(Path(__file__).resolve().parents[1] / "configs" / "runtime_limits.toml")
        if str(torch_config.device).startswith("cuda")
        else None
    )
    initial_temperature_checked = False
    prealigned_source_signals: FloatArray | None = None
    subjects = tuple(sorted(set(matrix.subjects.tolist())))
    for method in methods:
        method_needs_work = any(
            not valid_run_record(
                output_root / matrix.dataset / method / f"seed_{seed}" / f"{subject}.json",
                expected_config_sha256=expected_config_sha256,
            )
            for seed in seeds
            for subject in subjects
        )
        prefiltered_fbcsp: tuple[FloatArray, ...] | None = None
        if method == "fbcsp" and method_needs_work:
            filter_decoder = _decoder(
                method,
                matrix,
                classes=len(set(matrix.labels.tolist())),
                seed=int(seeds[0]),
                torch_config=torch_config,
            )
            if not isinstance(filter_decoder, FilterBankCSP):
                raise TypeError("FBCSP factory returned the wrong decoder type")
            prefiltered_fbcsp = filter_decoder.filtered_bands_memmap(
                matrix.signals,
                output_root / ".cache" / matrix.dataset / expected_config_sha256 / "fbcsp",
            )
        if method.startswith("ea_") and method_needs_work and prealigned_source_signals is None:
            prealigned_source_signals = align_training_subjects(matrix.signals, matrix.subjects)
        for seed in seeds:
            for subject in subjects:
                output = output_root / matrix.dataset / method / f"seed_{seed}" / f"{subject}.json"
                if valid_run_record(output, expected_config_sha256=expected_config_sha256):
                    outputs.append(output)
                    continue
                if max_new_runs is not None and completed >= max_new_runs:
                    return tuple(outputs)
                reusable = _reusable_metrics(
                    output_root,
                    dataset=matrix.dataset,
                    method=method,
                    subject=subject,
                    seeds=seeds,
                    expected_config_sha256=expected_config_sha256,
                )
                if reusable is None:
                    if (
                        cooling_policy is not None
                        and method not in DETERMINISTIC_METHODS
                        and not initial_temperature_checked
                    ):
                        cool_gpu(cooling_policy)
                        initial_temperature_checked = True
                    process_eigh = (
                        ProcessEighProbe(workers=2, chunk_matrices=64, minimum_memory_gib=4.0)
                        if process_enabled
                        and process_eigh_startup_headroom
                        and matrix.dataset == "cho2017"
                        and method == "ea_tangent_lr"
                        else None
                    )
                    with process_eigh if process_eigh is not None else nullcontext():
                        result = run_fold(
                            matrix,
                            target_subject=subject,
                            method=method,
                            seed=seed,
                            shots_per_class=shots_per_class,
                            confidence_threshold=confidence_threshold,
                            torch_config=torch_config,
                            prealigned_source_signals=prealigned_source_signals,
                            prefiltered_fbcsp=prefiltered_fbcsp,
                            certify_csp_rank=certify_csp and method == "fbcsp",
                        )
                    metrics = result.scalar_metrics()
                    if process_eigh is not None:
                        if not process_eigh.stats["parallel_calls"]:
                            raise RuntimeError("qualified process eigensolver was not used")
                        metrics["process_eigh_worker_count"] = float(
                            len(process_eigh.stats["worker_pids"])
                        )
                        metrics["process_eigh_block_count"] = float(process_eigh.stats["blocks"])
                        metrics["process_eigh_minimum_free_memory_gib"] = float(
                            process_eigh.stats["minimum_observed_free_memory_gib"]
                        )
                    if result.csp_rank_certificates:
                        certificates = result.csp_rank_certificates
                        certified = [item for item in certificates if item.certified]
                        metrics["csp_certified_band_count"] = float(len(certified))
                        metrics["csp_automatic_rank_band_count"] = float(
                            len(certificates) - len(certified)
                        )
                        if certified:
                            metrics["csp_minimum_certified_bound_ratio"] = min(
                                item.sample_lower_bound / item.global_threshold_upper_bound
                                for item in certified
                            )
                else:
                    metrics, _ = reusable
                if reusable is None:
                    git_commit = source_provenance.git_commit
                    source_sha256 = source_provenance.source_sha256
                    git_dirty = source_provenance.git_dirty
                else:
                    # Reused measurements retain the original fit's code provenance.
                    original_path = (
                        output_root
                        / matrix.dataset
                        / method
                        / f"seed_{reusable[1]}"
                        / f"{subject}.json"
                    )
                    original = json.loads(original_path.read_text(encoding="utf-8"))
                    git_commit = original["git_commit"]
                    source_sha256 = original.get("source_sha256")
                    git_dirty = original.get("git_dirty")
                record = RunRecord.create(
                    config=config,
                    seed=seed,
                    git_commit=git_commit,
                    source_sha256=source_sha256,
                    git_dirty=git_dirty,
                    dataset=matrix.dataset,
                    fold=subject,
                    metrics=metrics,
                )
                record.write_json(output)
                outputs.append(output)
                completed += 1
                if cooling_policy is not None and method not in DETERMINISTIC_METHODS:
                    cool_gpu(cooling_policy)
        prefiltered_fbcsp = None
        collect_garbage()
    return tuple(outputs)


def estimated_instance_hours(
    *, completed_run_seconds: float, methods: int, datasets_and_folds: Mapping[str, int], seeds: int
) -> float:
    if completed_run_seconds <= 0 or methods < 1 or seeds < 1:
        raise ValueError("cost-estimate inputs must be positive")
    total_runs = methods * seeds * sum(datasets_and_folds.values())
    return completed_run_seconds * total_runs / 3600.0
