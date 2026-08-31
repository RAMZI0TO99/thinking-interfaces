"""Independent arithmetic, provenance, completeness, and plausibility checks.

This audit reads saved results only. It never modifies benchmark records, trains
models, or interprets a high accuracy as proof of leakage or scientific validity.
"""

from __future__ import annotations

import hashlib
import json
import math
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
    origin = metrics.get("reused_from_seed")
    if origin is not None:
        if method not in DETERMINISTIC_METHODS or not origin.is_integer() or origin == seed:
            raise ValueError("invalid deterministic reuse marker")
        if metrics["fit_seconds"] != 0 or metrics["prediction_seconds"] != 0:
            raise ValueError("reused records must not duplicate measured runtime")
    if metrics.get("seed") != (origin if origin is not None else seed):
        raise ValueError("metric seed disagrees with fitting origin")
    return AuditedRecord(
        dataset, method, path.stem, seed, len(labels), metrics, hashlib.sha256(raw).hexdigest()
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
