"""Profile A preprocessing for canonical motor-imagery epochs."""

from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import mne  # type: ignore[import-untyped]
import numpy as np
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]
from numpy.typing import NDArray

from core.config import config_digest
from data.bci_iv_2a import configure_local_cache, download_subject

FloatArray = NDArray[np.float32]
IntArray = NDArray[np.int64]


class ManifestSummary(Protocol):
    def as_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class ProfileAConfig:
    bandpass_low_hz: float
    bandpass_high_hz: float
    resample_hz: float
    baseline_duration_s: float
    epoch_duration_s: float
    reference: str


@dataclass(frozen=True, slots=True)
class EpochArtifactSummary:
    artifact_schema_version: int
    subject: int
    shape: tuple[int, int, int]
    channel_names: tuple[str, ...]
    class_counts: dict[str, int]
    sessions: tuple[str, ...]
    sampling_rate_hz: float
    baseline_duration_s: float
    epoch_duration_s: float
    signal_min: float
    signal_max: float
    signal_mean: float
    signal_std: float
    config_sha256: str
    source_files: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def extract_trials(
    signal: NDArray[np.floating[Any]],
    events: IntArray,
    event_labels: Mapping[int, str],
    *,
    baseline_samples: int,
    epoch_samples: int,
) -> tuple[FloatArray, tuple[str, ...]]:
    """Extract exact-length epochs and subtract each channel's pre-cue mean."""

    if signal.ndim != 2:
        raise ValueError("signal must have shape (channels, samples)")
    if baseline_samples < 1 or epoch_samples < 1:
        raise ValueError("baseline_samples and epoch_samples must be positive")

    trials: list[FloatArray] = []
    labels: list[str] = []
    for event in events:
        cue_sample = int(event[0])
        event_code = int(event[2])
        baseline_start = cue_sample - baseline_samples
        epoch_end = cue_sample + epoch_samples
        if baseline_start < 0 or epoch_end > signal.shape[1]:
            raise ValueError(
                f"event at sample {cue_sample} does not have a complete baseline and epoch"
            )
        if event_code not in event_labels:
            raise ValueError(f"unknown event code: {event_code}")
        baseline = signal[:, baseline_start:cue_sample].mean(axis=1, keepdims=True)
        trial = signal[:, cue_sample:epoch_end] - baseline
        trials.append(np.asarray(trial, dtype=np.float32))
        labels.append(event_labels[event_code])

    if not trials:
        raise ValueError("no events were available for epoch extraction")
    return np.stack(trials), tuple(labels)


def preprocess_run(
    raw: Any,
    event_id: Mapping[str, int],
    config: ProfileAConfig,
) -> tuple[FloatArray, tuple[str, ...], tuple[str, ...]]:
    """Apply Profile A to one continuous run and return canonical EEG epochs."""

    if config.reference != "common_average":
        raise ValueError(f"unsupported Profile A reference: {config.reference}")
    processed = raw.copy().pick(picks="eeg")
    processed.filter(
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        method="fir",
        phase="zero",
        n_jobs=1,
        verbose=False,
    )
    processed.set_eeg_reference(ref_channels="average", projection=False, verbose=False)
    processed.resample(config.resample_hz, npad="auto", n_jobs=1, verbose=False)
    events, _ = mne.events_from_annotations(
        processed,
        event_id=dict(event_id),
        regexp=None,
        verbose=False,
    )
    inverse_event_id = {code: label for label, code in event_id.items()}
    baseline_samples = round(config.baseline_duration_s * config.resample_hz)
    epoch_samples = round(config.epoch_duration_s * config.resample_hz)
    signals, labels = extract_trials(
        processed.get_data(),
        np.asarray(events, dtype=np.int64),
        inverse_event_id,
        baseline_samples=baseline_samples,
        epoch_samples=epoch_samples,
    )
    return signals, labels, tuple(processed.ch_names)


def preprocess_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    config: ProfileAConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Preprocess every run for one subject while preserving provenance arrays."""

    configure_local_cache(project_root, raw_root)
    download_subject(subject, raw_root)
    dataset = BNCI2014_001()
    subject_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    signal_batches: list[FloatArray] = []
    labels: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []
    trial_indices: list[int] = []
    channel_names: tuple[str, ...] | None = None
    for session_id, session_runs in subject_data.items():
        for run_id, raw in session_runs.items():
            batch, batch_labels, batch_channels = preprocess_run(raw, dataset.event_id, config)
            if channel_names is None:
                channel_names = batch_channels
            elif batch_channels != channel_names:
                raise ValueError("canonical EEG channel order changes between runs")
            signal_batches.append(batch)
            labels.extend(batch_labels)
            sessions.extend([str(session_id)] * len(batch_labels))
            runs.extend([str(run_id)] * len(batch_labels))
            trial_indices.extend(range(len(batch_labels)))
    if channel_names is None:
        raise ValueError("subject contains no runs")
    return (
        np.concatenate(signal_batches, axis=0),
        np.asarray(labels),
        np.asarray(sessions),
        np.asarray(runs),
        np.asarray(trial_indices, dtype=np.int64),
        channel_names,
    )


def save_epoch_artifact(
    output: Path,
    *,
    signals: FloatArray,
    labels: NDArray[np.str_],
    sessions: NDArray[np.str_],
    runs: NDArray[np.str_],
    trial_indices: IntArray,
    channel_names: tuple[str, ...],
) -> Path:
    """Atomically write one compressed, self-describing subject artifact."""

    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".npz",
    )
    os.close(handle)
    try:
        np.savez_compressed(
            temporary_name,
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=np.asarray(channel_names),
        )
        os.replace(temporary_name, output)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return output


def build_summary(
    *,
    subject: int,
    signals: FloatArray,
    labels: NDArray[np.str_],
    sessions: NDArray[np.str_],
    runs: NDArray[np.str_],
    trial_indices: IntArray,
    channel_names: tuple[str, ...],
    config: ProfileAConfig,
    source_files: tuple[Path, ...],
) -> EpochArtifactSummary:
    trial_count = signals.shape[0]
    provenance_lengths = {
        trial_count,
        labels.shape[0],
        sessions.shape[0],
        runs.shape[0],
        trial_indices.shape[0],
    }
    if len(provenance_lengths) != 1:
        raise ValueError("signals and provenance arrays must contain the same trial count")
    if signals.ndim != 3:
        raise ValueError("signals must have shape (trials, channels, samples)")
    shape = (int(signals.shape[0]), int(signals.shape[1]), int(signals.shape[2]))
    return EpochArtifactSummary(
        artifact_schema_version=1,
        subject=subject,
        shape=shape,
        channel_names=channel_names,
        class_counts=dict(Counter(str(label) for label in labels)),
        sessions=tuple(sorted({str(session) for session in sessions})),
        sampling_rate_hz=config.resample_hz,
        baseline_duration_s=config.baseline_duration_s,
        epoch_duration_s=config.epoch_duration_s,
        signal_min=float(signals.min()),
        signal_max=float(signals.max()),
        signal_mean=float(signals.mean()),
        signal_std=float(signals.std()),
        config_sha256=config_digest(asdict(config)),
        source_files=tuple(str(path) for path in source_files),
    )


def write_manifest(path: Path, summary: ManifestSummary) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary.as_dict(), indent=2, sort_keys=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return path
