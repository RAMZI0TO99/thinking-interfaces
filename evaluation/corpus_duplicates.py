"""Bounded-memory exact-trial copy audit for the frozen LOSO episodes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from core.config import config_digest
from core.splits import earliest_balanced_episode
from data.array_cache import file_sha256


@dataclass(frozen=True, slots=True)
class TrialOccurrence:
    dataset: str
    subject: str
    artifact_index: int
    episode_role: str
    label: str
    session: str
    run: str
    trial_in_run: int


def expected_subject_inventory(
    root: Path, config: Mapping[str, Any], counts: Mapping[str, int]
) -> dict[str, tuple[str, ...]]:
    """Verify numeric subject identities while preserving each loader's zero padding."""
    result = {}
    for dataset, count in counts.items():
        directory = root / config["datasets"][dataset]["artifact_directory"]
        identifiers = tuple(sorted(path.stem for path in directory.glob("subject_*.npz")))
        if len(identifiers) != count or {
            int(name.removeprefix("subject_")) for name in identifiers
        } != set(range(1, count + 1)):
            raise ValueError(f"{dataset}: numeric subject inventory is incomplete or duplicated")
        result[dataset] = identifiers
    return result


def artifact_files(
    root: Path, config: Mapping[str, Any], subjects: Mapping[str, Sequence[str]]
) -> dict[str, Path]:
    result = {}
    for dataset, identifiers in subjects.items():
        directory = root / config["datasets"][dataset]["artifact_directory"]
        paths = {path.stem: path for path in directory.glob("subject_*.npz")}
        if set(paths) != set(identifiers):
            raise ValueError(f"{dataset}: subject artifacts do not match the expected inventory")
        for subject, path in sorted(paths.items()):
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("artifact path is outside the project")
            result[f"{dataset}/{subject}"] = path
    return result


def summarize_duplicates(groups: Mapping[str, Sequence[TrialOccurrence]]) -> list[dict[str, Any]]:
    duplicates = []
    for digest, occurrences in sorted(groups.items()):
        if len(occurrences) < 2:
            continue
        by_subject: dict[tuple[str, str], set[str]] = defaultdict(set)
        by_dataset: dict[str, list[TrialOccurrence]] = defaultdict(list)
        for occurrence in occurrences:
            by_subject[(occurrence.dataset, occurrence.subject)].add(occurrence.episode_role)
            by_dataset[occurrence.dataset].append(occurrence)
        within_subject_copy = any(roles == {"support", "query"} for roles in by_subject.values())
        cross_subject_copy = any(
            len({item.subject for item in items}) > 1
            and any(item.episode_role == "query" for item in items)
            for items in by_dataset.values()
        )
        duplicates.append(
            {
                "signal_sha256": digest,
                "occurrences": [asdict(item) for item in occurrences],
                "same_subject_support_query_copy": within_subject_copy,
                "cross_subject_source_query_copy": cross_subject_copy,
                "cross_dataset_copy": len(by_dataset) > 1,
            }
        )
    return duplicates


def audit_corpus_duplicates(
    root: Path, *, config: Mapping[str, Any], subjects: Mapping[str, Sequence[str]]
) -> dict[str, Any]:
    files = artifact_files(root, config, subjects)
    groups: dict[str, list[TrialOccurrence]] = defaultdict(list)
    file_hashes = {}
    summaries = []
    expected_labels: dict[str, tuple[str, ...]] = {}
    for identity, path in files.items():
        dataset, subject = identity.split("/")
        before = file_sha256(path)
        with np.load(path, allow_pickle=False) as stored:
            signals = np.asarray(stored["signals"], dtype=np.float32)
            labels = np.asarray(stored["labels"], dtype=np.str_)
            names = tuple(str(value) for value in stored["channel_names"])
            sessions, runs, trial_indices = (
                stored["sessions"],
                stored["runs"],
                stored["trial_indices"],
            )
        if (
            signals.ndim != 3
            or signals.shape[1] != len(names)
            or len(set(names)) != len(names)
            or not all(names)
            or not np.isfinite(signals).all()
            or any(
                values.shape != (signals.shape[0],)
                for values in (labels, sessions, runs, trial_indices)
            )
        ):
            raise ValueError(f"{identity}: invalid trial arrays or channels")
        threshold = float(config["datasets"][dataset]["artifact_threshold_volts"])
        retained = np.flatnonzero(np.max(np.abs(signals), axis=(1, 2)) <= threshold)
        present_labels = tuple(sorted(set(labels.tolist())))
        if set(labels[retained]) != set(present_labels):
            raise ValueError(f"{identity}: rejection removed an entire class")
        if dataset in expected_labels and expected_labels[dataset] != present_labels:
            raise ValueError(f"{identity}: class labels differ across subjects")
        expected_labels[dataset] = present_labels
        episode = earliest_balanced_episode(
            labels[retained].tolist(),
            subject_id=subject,
            shots_per_class=int(config["benchmark"]["shots_per_class"]),
        )
        support = set(episode.support_indices)
        channel_order = np.argsort(names)
        header = json.dumps(
            {
                "channels": sorted(names),
                "samples": signals.shape[2],
                "dtype": "float32",
                "rate": config["datasets"][dataset]["sampling_rate_hz"],
            },
            sort_keys=True,
        ).encode()
        flat_trials = 0
        for local_index, original_index in enumerate(retained):
            trial = np.ascontiguousarray(signals[original_index, channel_order])
            digest = hashlib.sha256(header)
            digest.update(memoryview(trial).cast("B"))
            groups[digest.hexdigest()].append(
                TrialOccurrence(
                    dataset,
                    subject,
                    int(original_index),
                    "support" if local_index in support else "query",
                    str(labels[original_index]),
                    str(sessions[original_index]),
                    str(runs[original_index]),
                    int(trial_indices[original_index]),
                )
            )
            flat_trials += int(np.ptp(trial) == 0)
        if file_sha256(path) != before:
            raise ValueError(f"{identity}: artifact changed during the audit")
        file_hashes[path.relative_to(root).as_posix()] = before
        summaries.append(
            {
                "dataset": dataset,
                "subject": subject,
                "input_trials": int(len(signals)),
                "retained_trials": int(len(retained)),
                "rejected_trials": int(len(signals) - len(retained)),
                "support_trials": len(episode.support_indices),
                "query_trials": len(episode.query_indices),
                "retained_class_counts": {
                    label: int(np.count_nonzero(labels[retained] == label))
                    for label in present_labels
                },
                "flat_trials": flat_trials,
            }
        )
        del signals
    duplicates = summarize_duplicates(groups)
    exact_leakage = [
        group
        for group in duplicates
        if group["same_subject_support_query_copy"] or group["cross_subject_source_query_copy"]
    ]
    snapshot = "\n".join(f"{name}:{digest}" for name, digest in sorted(file_hashes.items()))
    return {
        "complete": True,
        "config_sha256": config_digest(config),
        "artifact_snapshot_sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
        "artifact_files": file_hashes,
        "subject_count": len(summaries),
        "subjects": summaries,
        "retained_trials": sum(row["retained_trials"] for row in summaries),
        "rejected_trials": sum(row["rejected_trials"] for row in summaries),
        "duplicate_groups": duplicates,
        "exact_train_query_copy_groups": len(exact_leakage),
        "no_exact_train_query_copies": not exact_leakage,
        "scientific_leakage_clearance": False,
        "scope": (
            "All retained Profile A trials and frozen earliest-balanced episodes; "
            "label-independent hashes after canonical channel ordering."
        ),
        "limitations": (
            "Byte-exact copies only. Does not exclude near-duplicates, acquisition confounds, "
            "temporal/filter boundary effects, or pretraining overlap. "
            "Cross-dataset copies do not by themselves imply within-dataset LOSO leakage."
        ),
    }


def verify_corpus_snapshot(
    root: Path,
    report: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    subjects: Mapping[str, Sequence[str]],
) -> bool:
    try:
        files = artifact_files(root, config, subjects)
        current = {path.relative_to(root).as_posix(): file_sha256(path) for path in files.values()}
        snapshot = "\n".join(f"{name}:{digest}" for name, digest in sorted(current.items()))
        return bool(
            report.get("complete") is True
            and report.get("config_sha256") == config_digest(config)
            and report.get("artifact_files") == current
            and report.get("subject_count") == len(files)
            and report.get("artifact_snapshot_sha256")
            == hashlib.sha256(snapshot.encode()).hexdigest()
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False
