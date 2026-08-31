"""PhysioNet EEG Motor Movement/Imagery (EEGMMIDB) metadata and loading."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mne  # type: ignore[import-untyped]

from core.contracts import Epoch
from data.channel_names import canonicalize_channel_names
from data.runtime import configure_scientific_runtime

DATASET_KEY = "mmidb"
SUBJECTS = tuple(range(1, 110))
ANOMALOUS_SUBJECTS: Mapping[int, str] = {
    88: "annotation timing differs from the majority",
    89: "annotation timing differs from the majority",
    92: "recording length/sampling metadata requires explicit audit",
    100: "annotation timing differs from the majority",
    104: "one terminal cue lacks a complete four-second epoch",
}
LEFT_RIGHT_FIST_RUNS = (4, 8, 12)
EVENT_LABELS = {2: "left_fist", 3: "right_fist"}


@dataclass(frozen=True, slots=True)
class MMIDBSubjectSummary:
    subject: int
    files: tuple[str, ...]
    sampling_rates_hz: tuple[float, ...]
    channel_names: tuple[str, ...]
    event_counts: dict[str, int]
    anomaly_policy: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def subject_code(subject: int) -> str:
    if subject not in SUBJECTS:
        raise ValueError("MMIDB subject must be in 1..109")
    return f"S{subject:03d}"


def anomaly_policy(subject: int) -> str:
    """Return the precommitted anomaly handling decision.

    We retain all four recordings but require structural validation after load;
    this avoids silently shrinking the published 109-subject cohort.
    """

    return "retain_with_structural_validation" if subject in ANOMALOUS_SUBJECTS else "standard"


def load_left_right_fist_epochs(
    subject: int,
    raw_root: Path,
    *,
    tmin_s: float = 0.0,
    duration_s: float = 4.0,
    preload: bool = True,
) -> tuple[tuple[Epoch, ...], MMIDBSubjectSummary]:
    """Download/load runs 4, 8 and 12 and emit canonical two-class Epoch records."""

    code = subject_code(subject)
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    configure_scientific_runtime()
    raw_root.mkdir(parents=True, exist_ok=True)
    files = mne.datasets.eegbci.load_data(
        subject,
        runs=list(LEFT_RIGHT_FIST_RUNS),
        path=str(raw_root),
        update_path=False,
        verbose=False,
    )
    records: list[Epoch] = []
    rates: set[float] = set()
    expected_channels: tuple[str, ...] | None = None
    event_counts = {label: 0 for label in EVENT_LABELS.values()}
    for source in files:
        raw = mne.io.read_raw_edf(source, preload=preload, verbose=False)
        raw.pick(picks="eeg")
        names = canonicalize_channel_names(tuple(str(name) for name in raw.ch_names))
        raw.rename_channels(dict(zip(raw.ch_names, names, strict=True)))
        if expected_channels is None:
            expected_channels = names
        elif names != expected_channels:
            raise ValueError(f"{code} channel order changes between runs")
        rate = float(raw.info["sfreq"])
        rates.add(rate)
        events, _ = mne.events_from_annotations(
            raw, event_id={"T1": 2, "T2": 3}, regexp=None, verbose=False
        )
        samples = round(duration_s * rate)
        for onset, _, event_code in events:
            end = int(onset) + samples
            if end > raw.n_times:
                continue
            label = EVENT_LABELS[int(event_code)]
            signal = raw.get_data(start=int(onset), stop=end)
            records.append(
                Epoch(
                    signal=signal,
                    channel_names=names,
                    sampling_rate_hz=rate,
                    subject_id=f"{DATASET_KEY}/{code}",
                    dataset=DATASET_KEY,
                    event_label=label,
                    tmin_s=tmin_s,
                )
            )
            event_counts[label] += 1
    if not records or expected_channels is None:
        raise ValueError(f"{code} produced no left/right fist epochs")
    if set(event_counts.values()) == {0}:
        raise ValueError(f"{code} has no recognized events")
    summary = MMIDBSubjectSummary(
        subject=subject,
        files=tuple(str(Path(value).resolve()) for value in files),
        sampling_rates_hz=tuple(sorted(rates)),
        channel_names=expected_channels,
        event_counts=event_counts,
        anomaly_policy=anomaly_policy(subject),
    )
    return tuple(records), summary


def load_left_right_fist_raws(subject: int, raw_root: Path) -> tuple[tuple[Path, Any], ...]:
    """Return the three continuous motor-imagery runs for Profile A preprocessing."""

    subject_code(subject)
    configure_scientific_runtime()
    raw_root.mkdir(parents=True, exist_ok=True)
    files = mne.datasets.eegbci.load_data(
        subject,
        runs=list(LEFT_RIGHT_FIST_RUNS),
        path=str(raw_root),
        update_path=False,
        verbose=False,
    )
    return tuple(
        (Path(source).resolve(), mne.io.read_raw_edf(source, preload=True, verbose=False))
        for source in files
    )


def drop_incomplete_motor_annotations(
    raw: Any, *, baseline_s: float, epoch_s: float
) -> tuple[Any, int]:
    """Drop T1/T2 cues that cannot supply the configured baseline and epoch."""

    if baseline_s < 0 or epoch_s <= 0:
        raise ValueError("baseline and epoch durations are invalid")
    result = raw.copy()
    recording_end = float(result.n_times) / float(result.info["sfreq"])
    keep: list[int] = []
    dropped = 0
    for index, (onset, description) in enumerate(
        zip(result.annotations.onset, result.annotations.description, strict=True)
    ):
        motor_event = str(description) in {"T1", "T2"}
        complete = float(onset) >= baseline_s and float(onset) + epoch_s <= recording_end
        if motor_event and not complete:
            dropped += 1
        else:
            keep.append(index)
    result.set_annotations(result.annotations[keep])
    return result, dropped
