"""Profile B preprocessing for pretrained EEG encoders."""

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
class ProfileBConfig:
    bandpass_low_hz: float
    bandpass_high_hz: float
    notch_hz: float
    resample_hz: float
    reference: str
    epoch_duration_s: float
    amplitude_unit_mv: float
    patch_duration_s: float
    maximum_patches: int

    def __post_init__(self) -> None:
        if not 0 < self.bandpass_low_hz < self.notch_hz < self.bandpass_high_hz:
            raise ValueError("Profile B frequencies must satisfy low < notch < high")
        if self.bandpass_high_hz >= self.resample_hz / 2:
            raise ValueError("Profile B high cutoff must be below the resampled Nyquist rate")
        if self.reference != "original":
            raise ValueError("Profile B currently preserves the original dataset reference")
        if min(self.epoch_duration_s, self.amplitude_unit_mv, self.patch_duration_s) <= 0:
            raise ValueError("Profile B durations and amplitude unit must be positive")
        if self.maximum_patches < 1:
            raise ValueError("maximum_patches must be positive")


@dataclass(frozen=True, slots=True)
class ProfileBSummary:
    artifact_schema_version: int
    artifact_kind: str
    subject: int
    shape: tuple[int, int, int]
    channel_names: tuple[str, ...]
    sampling_rate_hz: float
    epoch_duration_s: float
    amplitude_unit_mv: float
    reference: str
    patch_samples: int
    patches_per_epoch: int
    fraction_within_unit_interval: float
    absolute_amplitude_p95: float
    config_sha256: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def scale_to_amplitude_unit(
    signal_volts: NDArray[np.floating[Any]], *, amplitude_unit_mv: float
) -> FloatArray:
    """Express volts in units of ``amplitude_unit_mv`` millivolts."""

    if amplitude_unit_mv <= 0 or not np.isfinite(signal_volts).all():
        raise ValueError("signal must be finite and amplitude_unit_mv must be positive")
    unit_volts = amplitude_unit_mv * 1e-3
    return np.asarray(signal_volts / unit_volts, dtype=np.float32)


def extract_profile_b_trials(
    signal: NDArray[np.floating[Any]],
    events: IntArray,
    event_labels: Mapping[int, str],
    *,
    epoch_samples: int,
) -> tuple[FloatArray, tuple[str, ...]]:
    """Extract exact post-cue epochs without baseline subtraction."""

    if signal.ndim != 2 or epoch_samples < 1:
        raise ValueError("signal must be two-dimensional and epoch_samples positive")
    trials: list[FloatArray] = []
    labels: list[str] = []
    for event in events:
        cue_sample = int(event[0])
        event_code = int(event[2])
        epoch_end = cue_sample + epoch_samples
        if cue_sample < 0 or epoch_end > signal.shape[1]:
            raise ValueError(f"event at sample {cue_sample} has no complete Profile B epoch")
        if event_code not in event_labels:
            raise ValueError(f"unknown event code: {event_code}")
        trials.append(np.asarray(signal[:, cue_sample:epoch_end], dtype=np.float32))
        labels.append(event_labels[event_code])
    if not trials:
        raise ValueError("no events were available for Profile B extraction")
    return np.stack(trials), tuple(labels)


def patch_epoch(
    epoch: NDArray[np.floating[Any]], *, patch_samples: int, maximum_patches: int
) -> FloatArray:
    """Split one channel-first epoch into a capped sequence of full patches."""

    if epoch.ndim != 2 or patch_samples < 1 or maximum_patches < 1:
        raise ValueError("epoch must be two-dimensional and patch limits positive")
    patch_count = min(epoch.shape[1] // patch_samples, maximum_patches)
    if patch_count < 1:
        raise ValueError("epoch is shorter than one patch")
    trimmed = epoch[:, : patch_count * patch_samples]
    patches = trimmed.reshape(epoch.shape[0], patch_count, patch_samples).transpose(1, 0, 2)
    return np.ascontiguousarray(patches, dtype=np.float32)


def preprocess_profile_b_run(
    raw: Any,
    event_id: Mapping[str, int],
    config: ProfileBConfig,
) -> tuple[FloatArray, tuple[str, ...], tuple[str, ...]]:
    """Filter, notch, resample, epoch, and scale one continuous EEG run."""

    processed = raw.copy().pick(picks="eeg")
    processed.filter(
        l_freq=config.bandpass_low_hz,
        h_freq=config.bandpass_high_hz,
        method="fir",
        phase="zero",
        n_jobs=1,
        verbose=False,
    )
    processed.notch_filter(
        freqs=[config.notch_hz], method="fir", phase="zero", n_jobs=1, verbose=False
    )
    processed.resample(config.resample_hz, npad="auto", n_jobs=1, verbose=False)
    events, _ = mne.events_from_annotations(
        processed, event_id=dict(event_id), regexp=None, verbose=False
    )
    trials, labels = extract_profile_b_trials(
        processed.get_data(),
        np.asarray(events, dtype=np.int64),
        {code: label for label, code in event_id.items()},
        epoch_samples=round(config.epoch_duration_s * config.resample_hz),
    )
    scaled = scale_to_amplitude_unit(trials, amplitude_unit_mv=config.amplitude_unit_mv)
    return scaled, labels, tuple(processed.ch_names)


def collect_profile_b_runs(
    subject_data: Mapping[Any, Mapping[Any, Any]],
    event_id: Mapping[str, int],
    config: ProfileBConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Collect one MOABB subject's runs through the shared run-level pipeline."""
    batches: list[FloatArray] = []
    labels: list[str] = []
    sessions: list[str] = []
    runs: list[str] = []
    trial_indices: list[int] = []
    channel_names: tuple[str, ...] | None = None
    for session_id, session_runs in subject_data.items():
        for run_id, raw in session_runs.items():
            batch, batch_labels, batch_channels = preprocess_profile_b_run(
                raw, event_id, config
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


def preprocess_profile_b_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    config: ProfileBConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Build Profile B epochs for every run while preserving provenance."""

    configure_local_cache(project_root, raw_root)
    download_subject(subject, raw_root)
    dataset = BNCI2014_001()
    subject_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    return collect_profile_b_runs(subject_data, dataset.event_id, config)


def preprocess_profile_b_cho_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    config: ProfileBConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Build Cho2017 Profile B epochs from the pinned local GIGADB raw files."""

    from moabb.datasets import Cho2017

    from data.cho2017 import configure_local_cache as configure_cho_cache
    from data.cho2017 import download_subject as download_cho_subject

    configure_cho_cache(project_root, raw_root)
    download_cho_subject(subject, raw_root)
    dataset = Cho2017()
    subject_data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    return collect_profile_b_runs(subject_data, dataset.event_id, config)


def build_profile_b_summary(
    *,
    subject: int,
    signals: FloatArray,
    channel_names: tuple[str, ...],
    config: ProfileBConfig,
) -> ProfileBSummary:
    if signals.ndim != 3 or not np.isfinite(signals).all():
        raise ValueError("signals must be finite with shape (trials, channels, samples)")
    patch_samples = round(config.patch_duration_s * config.resample_hz)
    patches_per_epoch = min(signals.shape[2] // patch_samples, config.maximum_patches)
    absolute = np.abs(signals)
    return ProfileBSummary(
        artifact_schema_version=1,
        artifact_kind="profile_b",
        subject=subject,
        shape=(int(signals.shape[0]), int(signals.shape[1]), int(signals.shape[2])),
        channel_names=channel_names,
        sampling_rate_hz=config.resample_hz,
        epoch_duration_s=config.epoch_duration_s,
        amplitude_unit_mv=config.amplitude_unit_mv,
        reference=config.reference,
        patch_samples=patch_samples,
        patches_per_epoch=patches_per_epoch,
        fraction_within_unit_interval=float(np.mean(absolute <= 1.0)),
        absolute_amplitude_p95=float(np.percentile(absolute, 95)),
        config_sha256=config_digest(asdict(config)),
    )


def preprocess_profile_b_mmidb_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    config: ProfileBConfig,
) -> tuple[
    FloatArray,
    NDArray[np.str_],
    NDArray[np.str_],
    NDArray[np.str_],
    IntArray,
    tuple[str, ...],
]:
    """Build MMIDB Profile B epochs from the pinned local PhysioNet EDF runs.

    The three left/right-fist motor runs are loaded, cues that cannot supply a
    complete post-cue epoch are dropped (the same completeness rule as Profile A
    with a zero baseline), T1/T2 annotations are renamed to the canonical
    classes, and channel names are canonicalized so Profile A and B agree on
    the standard sixty-four-electrode montage (T9/T10, not P9/P10).
    """
    from data.channel_names import canonicalize_channel_names
    from data.mmidb import drop_incomplete_motor_annotations, load_left_right_fist_raws

    runs = load_left_right_fist_raws(subject, raw_root)
    prepared: list[tuple[str, str, Any]] = []
    for _index, (source, raw) in enumerate(runs):
        complete, _dropped = drop_incomplete_motor_annotations(
            raw, baseline_s=0.0, epoch_s=config.epoch_duration_s
        )
        renamed = complete.copy()
        descriptions = [
            {"T1": "left_fist", "T2": "right_fist"}.get(str(d), str(d))
            for d in renamed.annotations.description
        ]
        renamed.set_annotations(
            mne.Annotations(
                onset=renamed.annotations.onset,
                duration=renamed.annotations.duration,
                description=descriptions,
            )
        )
        canonical = canonicalize_channel_names(tuple(renamed.ch_names))
        rename_map = {
            old: new for old, new in zip(renamed.ch_names, canonical, strict=True)
        }
        renamed.rename_channels(rename_map)
        # Some MMIDB recordings are native 128 Hz, below the Profile B bandpass
        # Nyquist; upsample every run to the target rate BEFORE filtering. The
        # run-level resample is then a same-rate no-op. Upsampling adds no
        # information above the native Nyquist; this order is the MMIDB policy.
        renamed.resample(config.resample_hz, npad="auto", n_jobs=1, verbose=False)
        # Profile A names sessions "0" and runs by the EDF run number
        # (S001R04.edf -> "04"); the A/B join key must match exactly.
        run_code = source.stem.split("R")[-1].zfill(2)
        prepared.append(("0", run_code, renamed))
    grouped: dict[str, dict[str, Any]] = {}
    for session, run, raw in prepared:
        grouped.setdefault(session, {})[run] = raw
    return collect_profile_b_runs(
        grouped,
        {"left_fist": 2, "right_fist": 3},
        config,
    )
