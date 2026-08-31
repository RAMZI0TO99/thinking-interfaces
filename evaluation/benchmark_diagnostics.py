"""Subject-weighted diagnostics and class counts from a fixed audited snapshot."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean, median

from evaluation.benchmark_audit import AuditedRecord, inspect_record


def read_audited_snapshot(
    root: Path,
    record_files: Mapping[str, str],
    *,
    expected_config_sha256: str,
) -> tuple[AuditedRecord, ...]:
    """Refuse changed files; do not discover new runs after the initial audit."""
    records = []
    resolved_root = root.resolve()
    for relative, expected_hash in sorted(record_files.items()):
        path = root / relative
        if not path.resolve().is_relative_to(resolved_root):
            raise ValueError("snapshot path escapes benchmark root")
        record = inspect_record(path, expected_config_sha256=expected_config_sha256)
        if record.sha256 != expected_hash:
            raise ValueError(f"audited record changed during reporting: {relative}")
        records.append(record)
    return tuple(records)


def _subject_means(records: Sequence[AuditedRecord], metric: str) -> dict[str, float]:
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        if metric in record.metrics:
            grouped[record.subject].append(record.metrics[metric])
    return {subject: fmean(values) for subject, values in grouped.items()}


@dataclass(frozen=True, slots=True)
class DiagnosticRow:
    dataset: str
    method: str
    subject_count: int
    record_count: int
    cohen_kappa_subject_mean: float
    expected_calibration_error_subject_mean: float
    confidence_threshold: float
    coverage_subject_mean: float
    selective_accuracy_subject_mean: float | None
    selective_accuracy_subject_count: int
    selective_accuracy_record_count: int
    class_labels_json: str
    query_class_counts_including_seed_repeats_json: str
    confusion_counts_including_seed_repeats_json: str
    query_evaluations_including_seed_repeats: int
    computed_records: int
    reused_records: int
    measured_fit_seconds: float
    measured_prediction_seconds: float
    median_fit_seconds_computed: float | None
    amortized_batch_prediction_seconds_per_trial: float | None

    def as_dict(self) -> dict[str, str | int | float | None]:
        return asdict(self)


def aggregate_diagnostics(
    records: Sequence[AuditedRecord],
    *,
    confidence_threshold: float,
) -> tuple[DiagnosticRow, ...]:
    if not 0 <= confidence_threshold <= 1:
        raise ValueError("confidence threshold must lie in [0, 1]")
    grouped: defaultdict[tuple[str, str], list[AuditedRecord]] = defaultdict(list)
    identities = set()
    for record in records:
        identity = (record.dataset, record.method, record.subject, record.seed)
        if identity in identities:
            raise ValueError("duplicate diagnostic record")
        identities.add(identity)
        grouped[(record.dataset, record.method)].append(record)
    rows = []
    for (dataset, method), group in sorted(grouped.items()):
        labels = sorted(
            key.removeprefix("class_support_")
            for key in group[0].metrics
            if key.startswith("class_support_")
        )
        if any(
            sorted(
                key.removeprefix("class_support_")
                for key in record.metrics
                if key.startswith("class_support_")
            )
            != labels
            for record in group
        ):
            raise ValueError("class names differ within a diagnostic row")
        counts = {
            label: sum(int(record.metrics[f"class_support_{label}"]) for record in group)
            for label in labels
        }
        confusion = [
            [
                sum(int(record.metrics[f"confusion_true_{left}_pred_{right}"]) for record in group)
                for right in labels
            ]
            for left in labels
        ]
        selective = _subject_means(group, "selective_accuracy")
        computed = [record for record in group if "reused_from_seed" not in record.metrics]
        measured_prediction = sum(record.metrics["prediction_seconds"] for record in computed)
        computed_queries = sum(record.metrics["query_trials"] for record in computed)
        rows.append(
            DiagnosticRow(
                dataset=dataset,
                method=method,
                subject_count=len({record.subject for record in group}),
                record_count=len(group),
                cohen_kappa_subject_mean=fmean(_subject_means(group, "cohen_kappa").values()),
                expected_calibration_error_subject_mean=fmean(
                    _subject_means(group, "expected_calibration_error").values()
                ),
                confidence_threshold=confidence_threshold,
                coverage_subject_mean=fmean(
                    _subject_means(group, "coverage_at_threshold").values()
                ),
                selective_accuracy_subject_mean=fmean(selective.values()) if selective else None,
                selective_accuracy_subject_count=len(selective),
                selective_accuracy_record_count=sum(
                    "selective_accuracy" in record.metrics for record in group
                ),
                class_labels_json=json.dumps(labels),
                query_class_counts_including_seed_repeats_json=json.dumps(counts, sort_keys=True),
                confusion_counts_including_seed_repeats_json=json.dumps(confusion),
                query_evaluations_including_seed_repeats=sum(counts.values()),
                computed_records=len(computed),
                reused_records=len(group) - len(computed),
                measured_fit_seconds=sum(record.metrics["fit_seconds"] for record in computed),
                measured_prediction_seconds=measured_prediction,
                median_fit_seconds_computed=median(
                    record.metrics["fit_seconds"] for record in computed
                )
                if computed
                else None,
                amortized_batch_prediction_seconds_per_trial=measured_prediction / computed_queries
                if computed_queries
                else None,
            )
        )
    return tuple(rows)


def write_diagnostics_csv(rows: Sequence[DiagnosticRow], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(dir=output.parent, suffix=".tmp", text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=tuple(DiagnosticRow.__dataclass_fields__))
            writer.writeheader()
            writer.writerows(row.as_dict() for row in rows)
        os.replace(temporary_name, output)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return output
