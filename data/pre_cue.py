"""Pre-cue negative-control epochs for BCI Competition IV 2a."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mne  # type: ignore[import-untyped]
import numpy as np
from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]
from numpy.typing import NDArray

from core.config import config_digest
from data.bci_iv_2a import configure_local_cache, download_subject
from data.profile_a import FloatArray, IntArray


@dataclass(frozen=True, slots=True)
class PreCueConfig:
    bandpass_low_hz: float
    bandpass_high_hz: float
    resample_hz: float
    window_duration_s: float
    reference: str


@dataclass(frozen=True, slots=True)
class PreCueSummary:
    artifact_schema_version: int
    artifact_kind: str
    subject: int
    shape: tuple[int, int, int]
    channel_names: tuple[str, ...]
    sampling_rate_hz: float
    window_duration_s: float
    reference: str
    config_sha256: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def extract_pre_cue_trials(
    signal: NDArray[np.floating[Any]],
    events: IntArray,
    event_labels: Mapping[int, str],
    *,
    window_samples: int,
) -> tuple[FloatArray, tuple[str, ...]]:
    """Extract mean-centred windows ending exactly at each cue onset."""

    if signal.ndim != 2:
        raise ValueError("signal must have shape (channels, samples)")
    if window_samples < 1:
        raise ValueError("window_samples must be positive")

    trials: list[FloatArray] = []
    labels: list[str] = []
    for event in events:
        cue_sample = int(event[0])
        event_code = int(event[2])
        window_start = cue_sample - window_samples
        if window_start < 0 or cue_sample > signal.shape[1]:
            raise ValueError(f"event at sample {cue_sample} has no complete pre-cue window")
        if event_code not in event_labels:
            raise ValueError(f"unknown event code: {event_code}")
        window = signal[:, window_start:cue_sample]
        centred = window - window.mean(axis=1, keepdims=True)
        trials.append(np.asarray(centred, dtype=np.float32))
        labels.append(event_labels[event_code])

    if not trials:
        raise ValueError("no events were available for pre-cue extraction")
    return np.stack(trials), tuple(labels)


def preprocess_pre_cue_run(
    raw: Any,
    event_id: Mapping[str, int],
    config: PreCueConfig,
) -> tuple[FloatArray, tuple[str, ...], tuple[str, ...]]:
    """Apply Profile A signal processing and return only the pre-cue interval."""

    if config.reference != "common_average":
        raise ValueError(f"unsupported pre-cue reference: {config.reference}")
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
    signals, labels = extract_pre_cue_trials(
        processed.get_data(),
        np.asarray(events, dtype=np.int64),
        {code: label for label, code in event_id.items()},
        window_samples=round(config.window_duration_s * config.resample_hz),
    )
    return signals, labels, tuple(processed.ch_names)


def preprocess_pre_cue_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    config: PreCueConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Build pre-cue windows for every run while preserving provenance."""

    configure_local_cache(project_root, raw_root)
    download_subject(subject, raw_root)
    dataset = BNCI2014_001()
    subject_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    batches: list[FloatArray] = []
    labels: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []
    trial_indices: list[int] = []
    channel_names: tuple[str, ...] | None = None
    for session_id, session_runs in subject_data.items():
        for run_id, raw in session_runs.items():
            batch, batch_labels, batch_channels = preprocess_pre_cue_run(
                raw, dataset.event_id, config
            )
            if channel_names is None:
                channel_names = batch_channels
            elif batch_channels != channel_names:
                raise ValueError("canonical EEG channel order changes between runs")
            batches.append(batch)
            labels.extend(batch_labels)
            sessions.extend([str(session_id)] * len(batch_labels))
            runs.extend([str(run_id)] * len(batch_labels))
            trial_indices.extend(range(len(batch_labels)))
    if channel_names is None:
        raise ValueError("subject contains no runs")
    return (
        np.concatenate(batches, axis=0),
        np.asarray(labels),
        np.asarray(sessions),
        np.asarray(runs),
        np.asarray(trial_indices, dtype=np.int64),
        channel_names,
    )


def build_pre_cue_summary(
    *,
    subject: int,
    signals: FloatArray,
    channel_names: tuple[str, ...],
    config: PreCueConfig,
) -> PreCueSummary:
    if signals.ndim != 3:
        raise ValueError("signals must have shape (trials, channels, samples)")
    return PreCueSummary(
        artifact_schema_version=1,
        artifact_kind="pre_cue_control",
        subject=subject,
        shape=(int(signals.shape[0]), int(signals.shape[1]), int(signals.shape[2])),
        channel_names=channel_names,
        sampling_rate_hz=config.resample_hz,
        window_duration_s=config.window_duration_s,
        reference=config.reference,
        config_sha256=config_digest(asdict(config)),
    )
