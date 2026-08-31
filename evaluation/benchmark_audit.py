"""Independent arithmetic, provenance, completeness, and plausibility checks.

This audit reads saved results only. It never modifies benchmark records, trains
models, or interprets a high accuracy as proof of leakage or scientific validity.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from core.config import config_digest

DETERMINISTIC_METHODS = frozenset({"fbcsp", "tangent_lr", "ea_tangent_lr"})


@dataclass(frozen=True)
class AuditedRecord:
    dataset: str
    method: str
    subject: str
    seed: int
    classes: int
    metrics: dict[str, float]
    sha256: str
    git_commit: str = "unversioned-workspace"
    source_sha256: str | None = None
    git_dirty: bool | None = None


def inspect_record(path: Path, *, expected_config_sha256: str) -> AuditedRecord:
    """Reject inconsistent arithmetic/provenance even when schema/hash tags match."""
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("config"), dict):
        raise ValueError("record and configuration must be objects")
    if (
        payload.get("config_sha256") != expected_config_sha256
        or config_digest(payload["config"]) != expected_config_sha256
    ):
        raise ValueError("stale or inconsistent configuration hash")
    dataset, method, seed_dir = path.parts[-4:-1]
    seed = payload.get("seed")
    if (
        type(seed) is not int
        or seed < 0
        or seed_dir != f"seed_{seed}"
        or payload.get("dataset") != dataset
        or payload.get("fold") != path.stem
    ):
        raise ValueError("record identity disagrees with its path")
    timestamp = datetime.fromisoformat(str(payload.get("timestamp_utc", "")))
    if timestamp.tzinfo is None or not payload.get("git_commit"):
        raise ValueError("timezone-aware timestamp and code provenance are required")
    source_sha256 = payload.get("source_sha256")
    if source_sha256 is not None and (
        not isinstance(source_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None
    ):
        raise ValueError("invalid source fingerprint")
    git_dirty = payload.get("git_dirty")
    if git_dirty is not None and not isinstance(git_dirty, bool):
        raise ValueError("invalid dirty-source indicator")
    raw_metrics = payload.get("metrics")
    if not isinstance(raw_metrics, dict) or any(
        isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value)
        for value in raw_metrics.values()
    ):
        raise ValueError("metrics must be finite numeric scalars")
    metrics = {str(key): float(value) for key, value in raw_metrics.items()}
    if metrics.get("benchmark_schema_version") != 2.0:
        raise ValueError("schema version 2 is required")

    def count(key: str, *, positive: bool = False) -> int:
        value = metrics[key]
        if not value.is_integer() or value < (1 if positive else 0):
            raise ValueError(f"invalid count: {key}")
        return int(value)

    labels = sorted(
        key.removeprefix("class_support_") for key in metrics if key.startswith("class_support_")
    )
    if len(labels) < 2:
        raise ValueError("at least two query classes are required")
    supports = [count(f"class_support_{label}", positive=True) for label in labels]
    expected_cells = {f"confusion_true_{left}_pred_{right}" for left in labels for right in labels}
    actual_cells = {key for key in metrics if key.startswith("confusion_true_")}
    if actual_cells != expected_cells:
        raise ValueError("confusion matrix is incomplete or has extra classes")
    confusion = [
        [count(f"confusion_true_{left}_pred_{right}") for right in labels] for left in labels
    ]
    if [sum(row) for row in confusion] != supports:
        raise ValueError("confusion row sums disagree with class support")
    query = count("query_trials", positive=True)
    support = count("support_trials", positive=True)
    if sum(supports) != query:
        raise ValueError("confusion total disagrees with query count")
    retained = count("dataset_input_trials", positive=True) - count("dataset_rejected_trials")
    if retained <= query + support:
        raise ValueError("no source trials remain outside target support/query")
    benchmark = payload["config"].get("benchmark", {})
    if "shots_per_class" in benchmark and support != int(benchmark["shots_per_class"]) * len(
        labels
    ):
        raise ValueError("support count disagrees with configured shots per class")
    ba = mean(confusion[index][index] / size for index, size in enumerate(supports))
    observed = sum(confusion[index][index] for index in range(len(labels))) / query
    columns = [sum(row[index] for row in confusion) for index in range(len(labels))]
    expected = sum(left * right for left, right in zip(supports, columns, strict=True)) / query**2
    kappa = (observed - expected) / (1.0 - expected)
    for key, recomputed in (("balanced_accuracy", ba), ("cohen_kappa", kappa)):
        if not math.isclose(metrics[key], recomputed, rel_tol=1e-8, abs_tol=1e-8):
            raise ValueError(f"{key} disagrees with confusion matrix")
    for key in ("expected_calibration_error", "coverage_at_threshold", "selective_accuracy"):
        if key in metrics and not 0 <= metrics[key] <= 1:
            raise ValueError(f"{key} is outside [0, 1]")
    for key in ("expected_calibration_error", "coverage_at_threshold"):
        if key not in metrics:
            raise ValueError(f"missing metric: {key}")
    if metrics["coverage_at_threshold"] > 0 and "selective_accuracy" not in metrics:
        raise ValueError("nonempty coverage requires selective accuracy")
    if metrics["fit_seconds"] < 0 or metrics["prediction_seconds"] < 0:
        raise ValueError("negative runtime")
    certificate_keys = {
        "csp_certified_band_count",
        "csp_automatic_rank_band_count",
        "csp_minimum_certified_bound_ratio",
    }
    if certificate_keys & set(metrics):
        if method != "fbcsp" or not {
            "csp_certified_band_count",
            "csp_automatic_rank_band_count",
        } <= set(metrics):
            raise ValueError("incomplete or misplaced CSP rank diagnostics")
        dataset_settings = payload["config"].get("datasets", {}).get(dataset, {})
        sampling_rate = dataset_settings.get("sampling_rate_hz")
        if type(sampling_rate) not in (int, float) or not math.isfinite(sampling_rate):
            raise ValueError("CSP diagnostics require a configured sampling rate")
        expected_bands = sum(low < sampling_rate / 2 - 1 for low in (8, 12, 16, 20, 24, 28))
        certified = count("csp_certified_band_count")
        automatic = count("csp_automatic_rank_band_count")
        if certified + automatic != expected_bands or expected_bands < 1:
            raise ValueError("CSP rank diagnostic counts disagree with the filter bank")
        ratio = metrics.get("csp_minimum_certified_bound_ratio")
        if (certified > 0 and (ratio is None or ratio <= 64)) or (
            certified == 0 and ratio is not None
        ):
            raise ValueError("CSP certified rank lacks its required numerical separation")
    process_keys = {
        "process_eigh_worker_count",
        "process_eigh_block_count",
        "process_eigh_minimum_free_memory_gib",
    }
    if process_keys & set(metrics):
        if (
            dataset != "cho2017"
            or method != "ea_tangent_lr"
            or not process_keys <= set(metrics)
            or metrics["process_eigh_worker_count"] != 2.0
            or metrics["process_eigh_minimum_free_memory_gib"] < 4.0
        ):
            raise ValueError("incomplete or unqualified process eigensolver diagnostics")
        count("process_eigh_block_count", positive=True)
    origin = metrics.get("reused_from_seed")
    if origin is not None:
        if method not in DETERMINISTIC_METHODS or not origin.is_integer() or origin == seed:
            raise ValueError("invalid deterministic reuse marker")
        if metrics["fit_seconds"] != 0 or metrics["prediction_seconds"] != 0:
            raise ValueError("reused records must not duplicate measured runtime")
    if metrics.get("seed") != (origin if origin is not None else seed):
        raise ValueError("metric seed disagrees with fitting origin")
    return AuditedRecord(
        dataset,
        method,
        path.stem,
        seed,
        len(labels),
        metrics,
        hashlib.sha256(raw).hexdigest(),
        str(payload["git_commit"]),
        source_sha256,
        git_dirty,
    )


def audit_benchmark(
    root: Path,
    *,
    datasets_subjects: Mapping[str, Sequence[str]],
    methods: Sequence[str],
    seeds: Sequence[int],
    expected_config_sha256: str,
    review_ceiling: float = 0.78,
) -> dict[str, Any]:
    """Audit the exact grid; separately flag high two-class subject/method means."""
    if not 0.5 < review_ceiling < 1:
        raise ValueError("review ceiling must be in (0.5, 1)")
    expected = {
        f"{dataset}/{method}/seed_{seed}/{subject}.json"
        for dataset, subjects in datasets_subjects.items()
        for method in methods
        for seed in seeds
        for subject in subjects
    }
    if (
        not expected
        or len(seeds) != len(set(seeds))
        or len(methods) != len(set(methods))
        or any(
            not subjects or len(subjects) != len(set(subjects))
            for subjects in datasets_subjects.values()
        )
    ):
        raise ValueError("nonempty unique benchmark grid is required")
    found = {
        path.relative_to(root).as_posix(): path for path in sorted(root.glob("*/*/seed_*/*.json"))
    }
    records: dict[str, AuditedRecord] = {}
    invalid: dict[str, str] = {}
    for relative in sorted(expected & found.keys()):
        try:
            records[relative] = inspect_record(
                found[relative], expected_config_sha256=expected_config_sha256
            )
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            invalid[relative] = str(error)
    for relative, record in tuple(records.items()):
        origin = record.metrics.get("reused_from_seed")
        if origin is None:
            continue
        origin_key = f"{record.dataset}/{record.method}/seed_{int(origin)}/{record.subject}.json"
        source = records.get(origin_key)
        ignored = {"fit_seconds", "prediction_seconds", "reused_from_seed"}
        comparable = {key: value for key, value in record.metrics.items() if key not in ignored}
        if (
            source is None
            or "reused_from_seed" in source.metrics
            or comparable
            != {key: value for key, value in source.metrics.items() if key not in ignored}
        ):
            invalid[relative] = "deterministic reuse has no matching original measurement"
    valid = {key: value for key, value in records.items() if key not in invalid}
    grouped: defaultdict[tuple[str, str, str], list[AuditedRecord]] = defaultdict(list)
    for record in valid.values():
        if record.classes == 2:
            grouped[(record.dataset, record.method, record.subject)].append(record)
    subjects_report: list[dict[str, Any]] = []
    method_scores: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    for (dataset, method, subject), group in sorted(grouped.items()):
        scores = [record.metrics["balanced_accuracy"] for record in group]
        average = mean(scores)
        method_scores[(dataset, method)].append(average)
        if max(scores) > review_ceiling:
            subjects_report.append(
                {
                    "dataset": dataset,
                    "method": method,
                    "subject": subject,
                    "mean_balanced_accuracy": average,
                    "minimum": min(scores),
                    "maximum": max(scores),
                    "seeds_present": sorted(record.seed for record in group),
                    "all_seeds_present": len(group) == len(seeds),
                }
            )
    methods_report = [
        {
            "dataset": dataset,
            "method": method,
            "subject_mean": mean(scores),
            "subjects_present": len(scores),
        }
        for (dataset, method), scores in sorted(method_scores.items())
        if mean(scores) > review_ceiling
    ]
    snapshot = "\n".join(f"{key}:{value.sha256}" for key, value in sorted(valid.items()))
    missing = sorted(expected - found.keys())
    unexpected = sorted(found.keys() - expected)
    return {
        "config_sha256": expected_config_sha256,
        "record_snapshot_sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
        "record_files": {key: record.sha256 for key, record in sorted(valid.items())},
        "expected_records": len(expected),
        "valid_records": len(valid),
        "source_provenance": {
            "records_with_git_revision": sum(
                re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", record.git_commit) is not None
                for record in valid.values()
            ),
            "records_with_source_fingerprint": sum(
                record.source_sha256 is not None for record in valid.values()
            ),
            "records_from_dirty_source": sum(record.git_dirty is True for record in valid.values()),
            "legacy_unversioned_records": sum(
                record.git_commit in {"no-git-workspace", "unversioned-workspace"}
                for record in valid.values()
            ),
        },
        "valid_records_by_dataset": {
            dataset: sum(record.dataset == dataset for record in valid.values())
            for dataset in datasets_subjects
        },
        "missing_records": missing,
        "invalid_records": invalid,
        "unexpected_records": unexpected,
        "complete": not missing and not invalid and not unexpected,
        "existing_records_arithmetic_passed": bool(valid) and not invalid and not unexpected,
        "two_class_review_ceiling": review_ceiling,
        "flagged_subjects": subjects_report,
        "flagged_methods": methods_report,
        "scientific_review_complete": False,
        "interpretation": (
            "Integrity is not leakage clearance; flagged scores need independent controls."
        ),
    }
