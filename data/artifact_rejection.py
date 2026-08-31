"""Configured amplitude-threshold rejection for unified epoch artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray

from data.unified import UnifiedArtifact


@dataclass(frozen=True, slots=True)
class ArtifactRejectionReport:
    threshold_volts: float
    input_trials: int
    retained_trials: int
    rejected_trials: int
    retained_fraction: float
    maximum_absolute_amplitude: float

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


def amplitude_retention_mask(
    signals: NDArray[np.floating], *, absolute_peak_volts: float
) -> NDArray[np.bool_]:
    values = np.asarray(signals)
    if values.ndim != 3 or not np.isfinite(values).all():
        raise ValueError("signals must be finite with shape (trials, channels, samples)")
    if absolute_peak_volts <= 0:
        raise ValueError("absolute_peak_volts must be positive")
    return np.max(np.abs(values), axis=(1, 2)) <= absolute_peak_volts


def reject_amplitude_artifacts(
    artifact: UnifiedArtifact, *, absolute_peak_volts: float
) -> tuple[UnifiedArtifact, ArtifactRejectionReport]:
    mask = amplitude_retention_mask(
        artifact.signals, absolute_peak_volts=absolute_peak_volts
    )
    retained = int(mask.sum())
    if retained == 0:
        raise ValueError("artifact threshold rejected every trial")
    filtered = UnifiedArtifact(
        artifact.signals[mask],
        artifact.labels[mask],
        artifact.sessions[mask],
        artifact.runs[mask],
        artifact.trial_indices[mask],
        artifact.channel_names,
    )
    if set(filtered.labels.tolist()) != set(artifact.labels.tolist()):
        raise ValueError("artifact threshold removed an entire class")
    report = ArtifactRejectionReport(
        absolute_peak_volts,
        int(mask.size),
        retained,
        int(mask.size - retained),
        retained / mask.size,
        float(np.max(np.abs(artifact.signals))),
    )
    return filtered, report
