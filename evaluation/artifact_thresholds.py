"""Dataset-wide amplitude summaries used to freeze artifact thresholds."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True, slots=True)
class ThresholdAudit:
    dataset: str
    subject_count: int
    trial_count: int
    threshold_volts: float
    retained_trials: int
    rejected_trials: int
    retained_fraction: float
    peak_abs_volts_p50: float
    peak_abs_volts_p95: float
    peak_abs_volts_p99: float
    peak_abs_volts_p999: float
    peak_abs_volts_max: float

    def as_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


def audit_threshold_directory(
    directory: Path,
    *,
    dataset: str,
    threshold_volts: float,
    expected_subjects: int | None = None,
) -> ThresholdAudit:
    """Summarize trial peaks without retaining full datasets in memory."""

    if threshold_volts <= 0:
        raise ValueError("threshold_volts must be positive")
    paths = sorted(directory.glob("subject_*.npz"))
    if not paths:
        raise ValueError(f"no subject artifacts found in {directory}")
    if expected_subjects is not None and len(paths) != expected_subjects:
        raise ValueError(
            f"{dataset} has {len(paths)} subjects; expected {expected_subjects}"
        )
    peaks: list[np.ndarray] = []
    for path in paths:
        with np.load(path, allow_pickle=False) as payload:
            signals = np.asarray(payload["signals"])
        if signals.ndim != 3 or not np.isfinite(signals).all():
            raise ValueError(f"invalid signals in {path}")
        peaks.append(np.max(np.abs(signals), axis=(1, 2)).astype(np.float64))
    values = np.concatenate(peaks)
    retained = int(np.count_nonzero(values <= threshold_volts))
    return ThresholdAudit(
        dataset=dataset,
        subject_count=len(paths),
        trial_count=int(values.size),
        threshold_volts=threshold_volts,
        retained_trials=retained,
        rejected_trials=int(values.size - retained),
        retained_fraction=retained / values.size,
        peak_abs_volts_p50=float(np.percentile(values, 50.0)),
        peak_abs_volts_p95=float(np.percentile(values, 95.0)),
        peak_abs_volts_p99=float(np.percentile(values, 99.0)),
        peak_abs_volts_p999=float(np.percentile(values, 99.9)),
        peak_abs_volts_max=float(values.max()),
    )
