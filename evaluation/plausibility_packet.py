"""Prepare evidence for review, without automatically clearing scientific flags."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.config import config_digest
from evaluation.benchmark_audit import inspect_record


def build_plausibility_packet(
    root: Path,
    *,
    config: Mapping[str, Any],
    integrity: Mapping[str, Any],
    corpus: Mapping[str, Any],
) -> dict[str, Any]:
    """Join a verified corpus snapshot to each independently audited result.

    The caller must first verify the corpus against the current input files.
    No fitted model, benchmark record, acceptance threshold or exclusion changes.
    """
    digest = config_digest(config)
    if (
        integrity.get("config_sha256") != digest
        or corpus.get("config_sha256") != digest
        or corpus.get("complete") is not True
    ):
        raise ValueError("matching benchmark and complete corpus snapshots are required")
    subjects = {(row["dataset"], row["subject"]): row for row in corpus["subjects"]}
    if len(subjects) != corpus["subject_count"]:
        raise ValueError("corpus subject summary is missing or duplicated")
    dataset_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input_trials": 0, "rejected_trials": 0}
    )
    shots = int(config["benchmark"]["shots_per_class"])
    for (dataset, _), row in subjects.items():
        class_counts = row["retained_class_counts"]
        if (
            row["retained_trials"] != sum(class_counts.values())
            or row["input_trials"] - row["rejected_trials"] != row["retained_trials"]
            or row["support_trials"] != shots * len(class_counts)
            or row["query_trials"] != row["retained_trials"] - row["support_trials"]
            or any(count <= shots for count in class_counts.values())
        ):
            raise ValueError("inconsistent corpus episode counts")
        for name in ("input_trials", "rejected_trials"):
            dataset_totals[dataset][name] += row[name]
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    mismatches: dict[str, list[str]] = {}
    files = integrity["record_files"]
    snapshot = "\n".join(f"{name}:{sha}" for name, sha in sorted(files.items()))
    if hashlib.sha256(snapshot.encode()).hexdigest() != integrity["record_snapshot_sha256"]:
        raise ValueError("inconsistent benchmark file snapshot")
    for name, sha in sorted(files.items()):
        path = (root / "runs" / "benchmark" / name).resolve()
        if not path.is_relative_to((root / "runs" / "benchmark").resolve()):
            raise ValueError("record path escapes the benchmark directory")
        record = inspect_record(path, expected_config_sha256=digest)
        if record.sha256 != sha:
            raise ValueError(f"record changed after integrity audit: {name}")
        row = subjects.get((record.dataset, record.subject))
        if row is None:
            raise ValueError(f"record has no corpus subject: {name}")
        counts = row["retained_class_counts"]
        expected: dict[str, int] = {
            "support_trials": row["support_trials"],
            "query_trials": row["query_trials"],
            "dataset_input_trials": dataset_totals[record.dataset]["input_trials"],
            "dataset_rejected_trials": dataset_totals[record.dataset]["rejected_trials"],
            **{f"class_support_{label}": count - shots for label, count in counts.items()},
        }
        errors = [key for key, count in expected.items() if record.metrics.get(key) != count]
        observed_labels = {
            key.removeprefix("class_support_")
            for key in record.metrics
            if key.startswith("class_support_")
        }
        if observed_labels != set(counts):
            errors.append("class_names")
        if errors:
            mismatches[name] = errors
        grouped[(record.dataset, record.method, record.subject)].append(
            {
                "seed": record.seed,
                "balanced_accuracy": record.metrics["balanced_accuracy"],
                "class_recall": {
                    label: record.metrics[f"confusion_true_{label}_pred_{label}"]
                    / record.metrics[f"class_support_{label}"]
                    for label in sorted(observed_labels)
                },
                "query_class_counts": {
                    label: int(record.metrics[f"class_support_{label}"])
                    for label in sorted(observed_labels)
                },
                "record_file": name,
                "record_sha256": sha,
                "reused_from_seed": record.metrics.get("reused_from_seed"),
            }
        )
    cases = []
    for flag in integrity["flagged_subjects"]:
        key = (flag["dataset"], flag["method"], flag["subject"])
        if key not in grouped:
            raise ValueError("a flagged case has no audited measurements")
        cases.append(
            {
                **flag,
                "retained_input": subjects[(flag["dataset"], flag["subject"])],
                "runs": sorted(grouped[key], key=lambda run: run["seed"]),
                "disposition": "unresolved; retain in frozen exploratory results",
                "independent_control_scope": (
                    "Subject 43 EEGNet/Shallow controls are separate evidence; they do not "
                    "clear other methods, subjects, or acquisition/filter-boundary confounds."
                    if flag["dataset"] == "cho2017"
                    else "No subject-specific shuffled-label control is attached by this packet."
                ),
            }
        )
    return {
        "config_sha256": digest,
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "artifact_snapshot_sha256": corpus["artifact_snapshot_sha256"],
        "benchmark_complete": integrity["complete"],
        "records_cross_checked": len(files),
        "record_input_count_mismatches": mismatches,
        "record_input_counts_passed": bool(files) and not mismatches,
        "no_exact_train_query_copies": corpus["no_exact_train_query_copies"],
        "two_class_review_ceiling": integrity["two_class_review_ceiling"],
        "flagged_subject_method_cases": cases,
        "flagged_method_means": integrity["flagged_methods"],
        "local_review_complete": False,
        "scientific_leakage_clearance": False,
        "interpretation": (
            "Evidence packet, not a scientific sign-off. Counts verify episode size and class "
            "balance, not that model fitting obeyed the split. Repeated seeds share query trials. "
            "Four-class BCI results are not judged by the two-class 78% trigger. The separate "
            "two-class support-adaptation baseline has its own review."
        ),
    }
