"""Structural leakage and quality audit for processed epoch artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True, slots=True)
class ArtifactAudit:
    artifact: str
    shape: tuple[int, int, int]
    dtype: str
    finite: bool
    class_counts: dict[str, int]
    session_counts: dict[str, int]
    provenance_unique: bool
    exact_duplicate_groups: int
    cross_session_duplicate_groups: int
    zero_variance_trials: int
    common_average_abs_max: float
    trial_peak_to_peak_volts_p50: float
    trial_peak_to_peak_volts_p95: float
    trial_peak_to_peak_volts_max: float
    passed: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _text_counts(values: np.ndarray) -> dict[str, int]:
    return dict(Counter(str(value) for value in values))


def audit_epoch_artifact(path: Path) -> ArtifactAudit:
    with np.load(path, allow_pickle=False) as artifact:
        required = {
            "signals",
            "labels",
            "sessions",
            "runs",
            "trial_indices",
            "channel_names",
        }
        missing = required - set(artifact.files)
        if missing:
            raise ValueError(f"artifact is missing arrays: {sorted(missing)}")
        signals = artifact["signals"]
        labels = artifact["labels"]
        sessions = artifact["sessions"]
        runs = artifact["runs"]
        trial_indices = artifact["trial_indices"]

    if signals.ndim != 3:
        raise ValueError("signals must have shape (trials, channels, samples)")
    trial_count = signals.shape[0]
    lengths = {trial_count, len(labels), len(sessions), len(runs), len(trial_indices)}
    if len(lengths) != 1:
        raise ValueError("signals and provenance arrays have different lengths")

    provenance = [
        (str(session), str(run), int(trial))
        for session, run, trial in zip(sessions, runs, trial_indices, strict=True)
    ]
    provenance_unique = len(set(provenance)) == len(provenance)

    hashes: defaultdict[str, list[int]] = defaultdict(list)
    for index, trial in enumerate(signals):
        hashes[hashlib.sha256(trial.tobytes()).hexdigest()].append(index)
    duplicate_groups = [indices for indices in hashes.values() if len(indices) > 1]
    cross_session_duplicates = sum(
        1 for indices in duplicate_groups if len({str(sessions[index]) for index in indices}) > 1
    )

    trial_variance = signals.var(axis=(1, 2))
    zero_variance_trials = int(np.count_nonzero(trial_variance == 0.0))
    peak_to_peak = np.ptp(signals, axis=2).max(axis=1)
    finite = bool(np.isfinite(signals).all())
    common_average_abs_max = float(np.abs(signals.mean(axis=1)).max())
    passed = bool(
        finite
        and provenance_unique
        and not duplicate_groups
        and zero_variance_trials == 0
        and common_average_abs_max < 1e-9
    )
    return ArtifactAudit(
        artifact=str(path.resolve()),
        shape=(int(signals.shape[0]), int(signals.shape[1]), int(signals.shape[2])),
        dtype=str(signals.dtype),
        finite=finite,
        class_counts=_text_counts(labels),
        session_counts=_text_counts(sessions),
        provenance_unique=provenance_unique,
        exact_duplicate_groups=len(duplicate_groups),
        cross_session_duplicate_groups=cross_session_duplicates,
        zero_variance_trials=zero_variance_trials,
        common_average_abs_max=common_average_abs_max,
        trial_peak_to_peak_volts_p50=float(np.percentile(peak_to_peak, 50)),
        trial_peak_to_peak_volts_p95=float(np.percentile(peak_to_peak, 95)),
        trial_peak_to_peak_volts_max=float(peak_to_peak.max()),
        passed=passed,
    )


def write_audit(path: Path, audit: ArtifactAudit) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(audit.as_dict(), indent=2, sort_keys=True)
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

