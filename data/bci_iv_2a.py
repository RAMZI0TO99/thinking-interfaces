"""BCI Competition IV 2a access through MOABB's BNCI2014_001 adapter."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from moabb.datasets import BNCI2014_001  # type: ignore[import-untyped]

from data.runtime import configure_scientific_runtime

DATASET_KEY = "bci_iv_2a"


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    key: str
    subjects: tuple[int, ...]
    events: dict[str, int]
    interval_s: tuple[float, float]


@dataclass(frozen=True, slots=True)
class SubjectSummary:
    subject: int
    files: tuple[str, ...]
    session_count: int
    run_count: int
    sampling_rates_hz: tuple[float, ...]
    channel_names: tuple[str, ...]
    channel_types: tuple[str, ...]
    total_samples: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def dataset_metadata() -> DatasetMetadata:
    dataset = BNCI2014_001()
    return DatasetMetadata(
        key=DATASET_KEY,
        subjects=tuple(dataset.subject_list),
        events=dict(dataset.event_id),
        interval_s=(float(dataset.interval[0]), float(dataset.interval[1])),
    )


def configure_local_cache(project_root: Path, raw_root: Path) -> None:
    """Keep all MOABB data and generated caches inside this project."""

    raw_root.mkdir(parents=True, exist_ok=True)
    configure_scientific_runtime(project_root)
    os.environ["MNE_DATASETS_BNCI_PATH"] = str(raw_root)


def validate_subject(subject: int) -> None:
    if subject not in dataset_metadata().subjects:
        raise ValueError(f"subject must be one of {dataset_metadata().subjects}; got {subject}")


def download_subject(
    subject: int,
    raw_root: Path,
    *,
    force_update: bool = False,
) -> tuple[Path, ...]:
    """Download or reuse the two official files for one subject."""

    validate_subject(subject)
    dataset = BNCI2014_001()
    files = dataset.data_path(
        subject,
        path=str(raw_root),
        force_update=force_update,
        update_path=False,
        verbose=False,
    )
    paths = tuple(Path(item).resolve() for item in files)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"MOABB returned missing files: {missing}")
    return paths


def summarize_subject_data(
    subject: int,
    files: tuple[Path, ...],
    subject_data: Mapping[str, Mapping[str, Any]],
) -> SubjectSummary:
    """Create a compact structural audit without copying signal arrays."""

    sampling_rates: set[float] = set()
    channel_names: tuple[str, ...] | None = None
    channel_types: tuple[str, ...] | None = None
    total_samples = 0
    run_count = 0
    for runs in subject_data.values():
        for raw in runs.values():
            names = tuple(str(name) for name in raw.ch_names)
            types = tuple(str(name) for name in raw.get_channel_types())
            if channel_names is None:
                channel_names = names
                channel_types = types
            elif names != channel_names or types != channel_types:
                raise ValueError("channel names or types change between runs")
            sampling_rates.add(float(raw.info["sfreq"]))
            total_samples += int(raw.n_times)
            run_count += 1
    if run_count == 0 or channel_names is None or channel_types is None:
        raise ValueError("subject contains no runs")
    return SubjectSummary(
        subject=subject,
        files=tuple(str(path) for path in files),
        session_count=len(subject_data),
        run_count=run_count,
        sampling_rates_hz=tuple(sorted(sampling_rates)),
        channel_names=channel_names,
        channel_types=channel_types,
        total_samples=total_samples,
    )


def load_and_summarize_subject(
    subject: int,
    project_root: Path,
    raw_root: Path,
    *,
    force_update: bool = False,
) -> SubjectSummary:
    configure_local_cache(project_root, raw_root)
    files = download_subject(subject, raw_root, force_update=force_update)
    dataset = BNCI2014_001()
    data = dataset.get_data(subjects=[subject], n_jobs=1)
    return summarize_subject_data(subject, files, data[subject])
