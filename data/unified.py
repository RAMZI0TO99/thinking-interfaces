"""Unified Profile A artifact construction and Epoch-record conversion."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from core.contracts import Epoch
from data.channel_names import canonicalize_channel_names
from data.profile_a import FloatArray, IntArray, ProfileAConfig, preprocess_run


@dataclass(frozen=True, slots=True)
class UnifiedArtifact:
    signals: FloatArray
    labels: NDArray[np.str_]
    sessions: NDArray[np.str_]
    runs: NDArray[np.str_]
    trial_indices: IntArray
    channel_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.signals.ndim != 3:
            raise ValueError("signals must have shape (trials, channels, samples)")
        length = self.signals.shape[0]
        provenance = (self.labels, self.sessions, self.runs, self.trial_indices)
        if any(array.shape != (length,) for array in provenance):
            raise ValueError("all provenance arrays must match the trial count")
        if self.signals.shape[1] != len(self.channel_names):
            raise ValueError("channel names must match the signal channel dimension")

    @property
    def class_counts(self) -> dict[str, int]:
        return dict(Counter(str(label) for label in self.labels))


def preprocess_raw_runs_profile_a(
    raw_runs: Sequence[tuple[str, str, Any]],
    *,
    event_id: Mapping[str, int],
    label_map: Mapping[str, str],
    config: ProfileAConfig,
) -> UnifiedArtifact:
    """Preprocess dataset-specific raw runs into one dataset-neutral artifact."""

    batches: list[FloatArray] = []
    labels: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []
    trial_indices: list[int] = []
    channel_names: tuple[str, ...] | None = None
    for session_id, run_id, raw in raw_runs:
        signals, raw_labels, names = preprocess_run(raw, event_id, config)
        canonical = canonicalize_channel_names(names)
        if channel_names is None:
            channel_names = canonical
        elif canonical != channel_names:
            raise ValueError("canonical channel order changes between runs")
        try:
            mapped = [label_map[label] for label in raw_labels]
        except KeyError as error:
            raise ValueError(f"event label has no canonical mapping: {error.args[0]}") from error
        batches.append(signals)
        labels.extend(mapped)
        sessions.extend([session_id] * len(mapped))
        runs.extend([run_id] * len(mapped))
        trial_indices.extend(range(len(mapped)))
    if not batches or channel_names is None:
        raise ValueError("raw run collection is empty")
    return UnifiedArtifact(
        np.concatenate(batches),
        np.asarray(labels),
        np.asarray(sessions),
        np.asarray(runs),
        np.asarray(trial_indices, dtype=np.int64),
        channel_names,
    )


def load_unified_artifact(path: Path) -> UnifiedArtifact:
    with np.load(path) as payload:
        return UnifiedArtifact(
            np.asarray(payload["signals"], dtype=np.float32),
            np.asarray(payload["labels"], dtype=np.str_),
            np.asarray(payload["sessions"], dtype=np.str_),
            np.asarray(payload["runs"], dtype=np.str_),
            np.asarray(payload["trial_indices"], dtype=np.int64),
            tuple(str(value) for value in payload["channel_names"]),
        )


def artifact_epoch_records(
    artifact: UnifiedArtifact,
    *,
    dataset: str,
    subject_id: str,
    sampling_rate_hz: float,
) -> tuple[Epoch, ...]:
    return tuple(
        Epoch(
            signal=artifact.signals[index],
            channel_names=artifact.channel_names,
            sampling_rate_hz=sampling_rate_hz,
            subject_id=f"{dataset}/{subject_id}",
            dataset=dataset,
            event_label=str(artifact.labels[index]),
        )
        for index in range(artifact.signals.shape[0])
    )
