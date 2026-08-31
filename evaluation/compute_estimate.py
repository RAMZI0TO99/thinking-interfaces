"""Snapshot-bound estimates of remaining measured work, not completion promises."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any

from core.config import config_digest
from core.provenance import capture_source
from evaluation.benchmark_audit import DETERMINISTIC_METHODS, AuditedRecord, audit_benchmark
from evaluation.benchmark_diagnostics import read_audited_snapshot


def estimate_remaining_work(
    records: Sequence[AuditedRecord],
    *,
    dataset_subjects: Mapping[str, Sequence[str]],
    methods: Sequence[str],
    seeds: Sequence[int],
) -> dict[str, Any]:
    """Use only same-dataset/method timings; count deterministic fits once.

    Reused seed records contribute neither durations nor new fit work. Work
    without an observed matching duration remains unknown, never a borrowed
    neural timing or a zero. The caller independently audits saved records.
    """
    if (
        not dataset_subjects
        or not methods
        or not seeds
        or len(set(methods)) != len(methods)
        or len(set(seeds)) != len(seeds)
        or any(
            not subjects or len(set(subjects)) != len(subjects)
            for subjects in dataset_subjects.values()
        )
    ):
        raise ValueError("a nonempty, duplicate-free work grid is required")
    indexed: dict[tuple[str, str, str, int], AuditedRecord] = {}
    for record in records:
        key = (record.dataset, record.method, record.subject, record.seed)
        if (
            record.dataset not in dataset_subjects
            or record.subject not in dataset_subjects[record.dataset]
            or record.method not in methods
            or record.seed not in seeds
            or key in indexed
        ):
            raise ValueError("duplicate record or record outside the requested work grid")
        indexed[key] = record
    for record in records:
        origin = record.metrics.get("reused_from_seed")
        if origin is not None:
            if record.method not in DETERMINISTIC_METHODS or not float(origin).is_integer():
                raise ValueError("invalid deterministic reuse")
            original = indexed.get((record.dataset, record.method, record.subject, int(origin)))
            if original is None or "reused_from_seed" in original.metrics:
                raise ValueError("reused timing has no independently computed origin")
    rows: list[dict[str, Any]] = []
    for dataset, subjects in dataset_subjects.items():
        for method in methods:
            group = [r for r in records if r.dataset == dataset and r.method == method]
            computed = [r for r in group if "reused_from_seed" not in r.metrics]
            durations = []
            for record in computed:
                values = [record.metrics[name] for name in ("fit_seconds", "prediction_seconds")]
                if any(not math.isfinite(value) or value < 0 for value in values):
                    raise ValueError("invalid measured runtime")
                duration = sum(values)
                if duration > 0:
                    durations.append(duration)
            missing = len(subjects) * len(seeds) - len(group)
            units = (
                len(set(subjects) - {r.subject for r in computed})
                if method in DETERMINISTIC_METHODS
                else missing
            )
            seconds_per_fit = median(durations) if durations else None
            seconds = (
                0.0
                if units == 0
                else (units * seconds_per_fit if seconds_per_fit is not None else None)
            )
            rows.append(
                {
                    "dataset": dataset,
                    "method": method,
                    "remaining_records": missing,
                    "remaining_fit_units": units,
                    "remaining_seed_copy_records": missing - units,
                    "observed_computed_fits": len(computed),
                    "positive_duration_observations": len(durations),
                    "median_fit_prediction_seconds": seconds_per_fit,
                    "observed_minimum_seconds": min(durations) if durations else None,
                    "observed_maximum_seconds": max(durations) if durations else None,
                    "estimated_remaining_fit_prediction_seconds": seconds,
                    "timing_source_fingerprints": sorted(
                        {r.source_sha256 or "unrecorded" for r in computed}
                    ),
                    "basis": "nothing remaining"
                    if units == 0
                    else ("same-dataset/method observed median" if durations else "unmeasured"),
                }
            )
    unknown = sum(
        row["remaining_fit_units"]
        for row in rows
        if row["estimated_remaining_fit_prediction_seconds"] is None
    )
    known_seconds = sum(row["estimated_remaining_fit_prediction_seconds"] or 0 for row in rows)
    return {
        "remaining_records": sum(row["remaining_records"] for row in rows),
        "remaining_fit_units": sum(row["remaining_fit_units"] for row in rows),
        "remaining_seed_copy_records": sum(row["remaining_seed_copy_records"] for row in rows),
        "unmeasured_fit_units": unknown,
        "known_work_fit_prediction_hours_estimate": known_seconds / 3600.0,
        "all_work_fit_prediction_hours_estimate": None if unknown else known_seconds / 3600.0,
        "rows": rows,
    }


def benchmark_work_report(
    root: Path,
    config: Mapping[str, Any],
    *,
    datasets: Sequence[str] | None = None,
    methods: Sequence[str] | None = None,
) -> dict[str, Any]:
    settings = config["benchmark"]
    selected_datasets = tuple(datasets if datasets is not None else settings["datasets"])
    selected_methods = tuple(methods if methods is not None else settings["methods"])
    if not set(selected_datasets) <= set(settings["datasets"]) or not set(selected_methods) <= set(
        settings["methods"]
    ):
        raise ValueError("requested estimate is outside the frozen benchmark")
    subjects = {
        name: tuple(
            path.stem
            for path in sorted(
                (root / config["datasets"][name]["artifact_directory"]).glob("subject_*.npz")
            )
        )
        for name in settings["datasets"]
    }
    digest = config_digest(config)
    integrity = audit_benchmark(
        root / "runs" / "benchmark",
        datasets_subjects=subjects,
        methods=settings["methods"],
        seeds=settings["seeds"],
        expected_config_sha256=digest,
    )
    if integrity["invalid_records"] or integrity["unexpected_records"]:
        raise ValueError("record integrity failed; runtime estimates are not trustworthy")
    records = read_audited_snapshot(
        root / "runs" / "benchmark",
        integrity["record_files"],
        expected_config_sha256=digest,
    )
    result = estimate_remaining_work(
        [r for r in records if r.dataset in selected_datasets and r.method in selected_methods],
        dataset_subjects={name: subjects[name] for name in selected_datasets},
        methods=selected_methods,
        seeds=settings["seeds"],
    )
    return {
        **result,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "cost_basis": config["cost"]["cost_basis"],
        "config_sha256": digest,
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "source": asdict(capture_source(root)),
        "scope": "remaining successful fit/prediction work only; not an elapsed-time forecast",
        "limitations": [
            "Methods with no matching measurements remain unknown; no cross-method fallback.",
            "Small timing samples and changing machine load can make medians unreliable.",
            "An in-progress unsaved fit is counted as a full remaining fit.",
            "Deterministic seed-copy records add no fit work; their write time is unmeasured.",
            "Loading, filtering, alignment preparation, cooling, retries and review excluded.",
            "Timings may span recorded source variants; provenance is listed per method.",
        ],
    }
