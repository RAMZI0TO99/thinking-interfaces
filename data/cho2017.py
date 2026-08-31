"""Strict Cho2017 access through MOABB with canonical 10-20 channel names."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from mne.channels import make_standard_montage  # type: ignore[import-untyped]
from moabb.datasets import Cho2017  # type: ignore[import-untyped]

from data.runtime import configure_scientific_runtime

DATASET_KEY = "cho2017"
STANDARD_1005_NAMES = {
    name.casefold(): name for name in make_standard_montage("standard_1005").ch_names
}


@dataclass(frozen=True, slots=True)
class ChoMetadata:
    key: str
    subjects: tuple[int, ...]
    events: dict[str, int]
    interval_s: tuple[float, float]
    sampling_rate_hz: float
    eeg_channels: int
    line_frequency_hz: float


@dataclass(frozen=True, slots=True)
class ChoSubjectSummary:
    subject: int
    file: str
    session_count: int
    run_count: int
    sampling_rates_hz: tuple[float, ...]
    channel_names: tuple[str, ...]
    channel_types: tuple[str, ...]
    eeg_channel_count: int
    emg_channel_count: int
    total_samples: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def dataset_metadata() -> ChoMetadata:
    dataset = Cho2017()
    return ChoMetadata(
        key=DATASET_KEY,
        subjects=tuple(dataset.subject_list),
        events=dict(dataset.event_id),
        interval_s=(float(dataset.interval[0]), float(dataset.interval[1])),
        sampling_rate_hz=512.0,
        eeg_channels=64,
        line_frequency_hz=60.0,
    )


def canonicalize_10_20_channel_names(names: tuple[str, ...]) -> tuple[str, ...]:
    """Normalize case while rejecting names outside the standard 1005 montage."""

    canonical: list[str] = []
    for name in names:
        match = STANDARD_1005_NAMES.get(name.casefold())
        if match is None:
            raise ValueError(f"EEG channel is not in the standard 1005 montage: {name}")
        canonical.append(match)
    if len(set(canonical)) != len(canonical):
        raise ValueError("canonical EEG channel names must be unique")
    return tuple(canonical)


def configure_local_cache(project_root: Path, raw_root: Path) -> None:
    raw_root.mkdir(parents=True, exist_ok=True)
    configure_scientific_runtime(project_root)
    os.environ["MNE_DATASETS_GIGADB_PATH"] = str(raw_root)


def validate_subject(subject: int) -> None:
    if subject not in dataset_metadata().subjects:
        raise ValueError(f"subject must be in 1..52; got {subject}")


def download_subject(
    subject: int, raw_root: Path, *, force_update: bool = False
) -> Path:
    validate_subject(subject)
    dataset = Cho2017()
    path = Path(
        dataset.data_path(
            subject,
            path=str(raw_root),
            force_update=force_update,
            update_path=False,
            verbose=False,
        )
    ).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"MOABB returned a missing Cho2017 file: {path}")
    return path


def summarize_subject_data(
    subject: int,
    source_file: Path,
    subject_data: Mapping[str, Mapping[str, Any]],
) -> ChoSubjectSummary:
    sampling_rates: set[float] = set()
    channel_names: tuple[str, ...] | None = None
    channel_types: tuple[str, ...] | None = None
    total_samples = 0
    run_count = 0
    for runs in subject_data.values():
        for raw in runs.values():
            raw_names = tuple(str(name) for name in raw.ch_names)
            types = tuple(str(name) for name in raw.get_channel_types())
            eeg_names = tuple(
                name
                for name, kind in zip(raw_names, types, strict=True)
                if kind == "eeg"
            )
            canonical_eeg = iter(canonicalize_10_20_channel_names(eeg_names))
            names = tuple(
                next(canonical_eeg) if kind == "eeg" else name
                for name, kind in zip(raw_names, types, strict=True)
            )
            if channel_names is None:
                channel_names = names
                channel_types = types
            elif names != channel_names or types != channel_types:
                raise ValueError("channel names or types change between Cho2017 runs")
            sampling_rates.add(float(raw.info["sfreq"]))
            total_samples += int(raw.n_times)
            run_count += 1
    if run_count == 0 or channel_names is None or channel_types is None:
        raise ValueError("Cho2017 subject contains no runs")
    eeg_count = channel_types.count("eeg")
    emg_count = channel_types.count("emg")
    if eeg_count != 64 or emg_count != 4:
        raise ValueError(f"expected 64 EEG and 4 EMG channels; got {eeg_count} and {emg_count}")
    if sampling_rates != {512.0}:
        raise ValueError(f"expected 512 Hz Cho2017 data; got {sorted(sampling_rates)}")
    return ChoSubjectSummary(
        subject=subject,
        file=str(source_file),
        session_count=len(subject_data),
        run_count=run_count,
        sampling_rates_hz=tuple(sorted(sampling_rates)),
        channel_names=channel_names,
        channel_types=channel_types,
        eeg_channel_count=eeg_count,
        emg_channel_count=emg_count,
        total_samples=total_samples,
    )


def load_and_summarize_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    *,
    force_update: bool = False,
) -> ChoSubjectSummary:
    configure_local_cache(project_root, raw_root)
    source = download_subject(subject, raw_root, force_update=force_update)
    dataset = Cho2017()
    data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    return summarize_subject_data(subject, source, data)
