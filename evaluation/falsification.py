"""Independent targeted controls; never write into the benchmark result tree."""

from __future__ import annotations

import hashlib
import time
from collections import Counter
from dataclasses import asdict
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from core.metrics import classification_report
from core.splits import earliest_balanced_episode
from evaluation.benchmark import DatasetMatrix


class ControlDecoder(Protocol):
    def fit(self, epochs: NDArray[np.float32], labels: NDArray[np.int64]) -> Any: ...

    def predict_proba(self, epochs: NDArray[np.float32]) -> NDArray[np.float32]: ...


def array_digest(array: NDArray[Any]) -> str:
    values = np.ascontiguousarray(array)
    digest = hashlib.sha256(f"{values.dtype}:{values.shape}".encode())
    digest.update(memoryview(values).cast("B"))
    return digest.hexdigest()


def control_indices(
    matrix: DatasetMatrix, target_subject: str, shots_per_class: int
) -> tuple[NDArray[np.int64], NDArray[np.int64], NDArray[np.int64]]:
    target = np.flatnonzero(matrix.subjects == target_subject)
    source = np.flatnonzero(matrix.subjects != target_subject)
    if not target.size or not source.size:
        raise ValueError("source and held-out subject are required")
    episode = earliest_balanced_episode(
        matrix.labels[target].tolist(),
        subject_id=target_subject,
        shots_per_class=shots_per_class,
    )
    support = target[np.asarray(episode.support_indices, dtype=np.int64)]
    query = target[np.asarray(episode.query_indices, dtype=np.int64)]
    return source, support, query


def shuffled_training_control(
    matrix: DatasetMatrix,
    decoder: ControlDecoder,
    *,
    target_subject: str,
    shots_per_class: int,
    shuffle_seed: int,
) -> dict[str, Any]:
    """Shuffle training labels only, after selecting the original balanced episode."""
    source, support, query = control_indices(matrix, target_subject, shots_per_class)
    train = np.concatenate((source, support))
    if np.intersect1d(train, query).size:
        raise ValueError("control train/query overlap")
    names = tuple(sorted(set(matrix.labels.tolist())))
    lookup = {name: index for index, name in enumerate(names)}
    original = np.asarray([lookup[name] for name in matrix.labels[train]], dtype=np.int64)
    shuffled = np.random.default_rng(shuffle_seed).permutation(original)
    if np.array_equal(shuffled, original):
        raise ValueError("control shuffle did not change the labels")
    started = time.perf_counter()
    decoder.fit(matrix.signals[train], shuffled)
    fit_seconds = time.perf_counter() - started
    started = time.perf_counter()
    probabilities = np.asarray(decoder.predict_proba(matrix.signals[query]))
    prediction_seconds = time.perf_counter() - started
    if (
        probabilities.shape != (len(query), len(names))
        or not np.isfinite(probabilities).all()
        or (probabilities < 0).any()
        or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-5)
    ):
        raise ValueError("invalid control prediction probabilities")
    predicted = np.asarray(names)[probabilities.argmax(axis=1)]
    report = classification_report(matrix.labels[query].tolist(), predicted.tolist(), labels=names)
    return {
        "control": "training_labels_shuffled_after_fixed_episode_selection",
        "target_subject": target_subject,
        "shuffle_seed": shuffle_seed,
        "source_trials": len(source),
        "support_trials": len(support),
        "query_trials": len(query),
        "train_query_disjoint": True,
        "source_subjects_disjoint": target_subject not in matrix.subjects[source],
        "source_indices_sha256": array_digest(source),
        "support_indices_sha256": array_digest(support),
        "query_indices_sha256": array_digest(query),
        "training_labels_original_sha256": array_digest(original),
        "training_labels_shuffled_sha256": array_digest(shuffled),
        "query_labels_sha256": array_digest(matrix.labels[query]),
        "training_label_counts_preserved": np.array_equal(
            np.bincount(original), np.bincount(shuffled)
        ),
        "changed_training_labels": int(np.count_nonzero(shuffled != original)),
        "query_predictions": predicted.tolist(),
        "fit_seconds": fit_seconds,
        "prediction_seconds": prediction_seconds,
        "metrics": asdict(report),
    }


def signal_audit(
    matrix: DatasetMatrix, *, target_subject: str, shots_per_class: int
) -> dict[str, Any]:
    """Exact duplicate audit and descriptive amplitude/order checks, not leakage proof."""
    source, support, query = control_indices(matrix, target_subject, shots_per_class)
    target = np.sort(np.concatenate((support, query)))
    hashes = [array_digest(trial) for trial in matrix.signals]
    train_hashes = {hashes[index] for index in np.concatenate((source, support))}
    source_hashes = {hashes[index] for index in source}
    counts = Counter(hashes[index] for index in target)
    labels = matrix.labels[target]
    amplitude = {}
    for label in sorted(set(labels.tolist())):
        signals = matrix.signals[target[labels == label]]
        rms = np.sqrt(np.mean(np.square(signals, dtype=np.float64), axis=(1, 2)))
        amplitude[label] = {
            "trials": len(signals),
            "median_rms_volts": float(np.median(rms)),
            "minimum_rms_volts": float(np.min(rms)),
            "maximum_rms_volts": float(np.max(rms)),
            "maximum_absolute_volts": float(np.max(np.abs(signals))),
        }
    query_train_duplicates = [int(index) for index in query if hashes[index] in train_hashes]
    source_target_duplicates = [int(index) for index in target if hashes[index] in source_hashes]
    return {
        "target_subject": target_subject,
        "shape": list(matrix.signals.shape),
        "channel_names": list(matrix.channel_names),
        "non_eeg_named_channels": [
            name
            for name in matrix.channel_names
            if any(token in name.upper() for token in ("EOG", "EMG", "STI", "TRIG"))
        ],
        "query_indices_exactly_duplicated_in_training": query_train_duplicates,
        "target_indices_exactly_duplicated_in_sources": source_target_duplicates,
        "target_repeated_signal_hashes": sum(count > 1 for count in counts.values()),
        "exact_duplicate_checks_passed": not query_train_duplicates
        and not source_target_duplicates,
        "target_signal_sha256": array_digest(matrix.signals[target]),
        "label_transitions_in_target_trial_order": int(np.count_nonzero(labels[1:] != labels[:-1])),
        "ordered_target_labels": labels.tolist(),
        "amplitude_by_class": amplitude,
        "limitations": (
            "Exact hashes do not detect near-duplicates, overlapping raw windows, or physiological "
            "and acquisition confounds. Channel names alone do not prove channel type. "
            "High scores are not cleared by this descriptive audit."
        ),
    }
