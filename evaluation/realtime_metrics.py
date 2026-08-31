"""Metrics for gated real-time classification."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray


def information_transfer_rate(
    accuracy: float, *, classes: int, decisions_per_minute: float
) -> float:
    """Return Wolpaw information-transfer rate in bits/minute."""

    if classes < 2 or decisions_per_minute <= 0 or not 0.0 <= accuracy <= 1.0:
        raise ValueError("invalid ITR inputs")
    if accuracy == 1.0:
        bits_per_decision = math.log2(classes)
    elif accuracy == 0.0:
        bits_per_decision = math.log2(classes) + math.log2(1.0 / (classes - 1))
    else:
        bits_per_decision = (
            math.log2(classes)
            + accuracy * math.log2(accuracy)
            + (1.0 - accuracy) * math.log2((1.0 - accuracy) / (classes - 1))
        )
    return max(0.0, bits_per_decision * decisions_per_minute)


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_confidence: float
    accuracy: float

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    expected_calibration_error: float
    bins: tuple[CalibrationBin, ...]


def calibration_report(
    probabilities: NDArray[np.floating],
    targets: NDArray[np.integer],
    *,
    bins: int = 10,
) -> CalibrationReport:
    """Compute a fixed-width reliability diagram and weighted ECE."""

    values = np.asarray(probabilities, dtype=np.float64)
    truth = np.asarray(targets, dtype=np.int64)
    if values.ndim != 2 or truth.ndim != 1 or values.shape[0] != truth.size:
        raise ValueError("probabilities and targets have incompatible shapes")
    if bins < 2 or values.shape[1] < 2 or truth.size == 0:
        raise ValueError("at least two bins, classes, and one sample are required")
    if not np.isfinite(values).all() or np.any(values < 0) or np.any(values > 1):
        raise ValueError("probabilities must be finite and within [0, 1]")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-5, rtol=0.0):
        raise ValueError("each probability row must sum to one")
    if np.any(truth < 0) or np.any(truth >= values.shape[1]):
        raise ValueError("target index is outside the class range")
    confidence = values.max(axis=1)
    correct = values.argmax(axis=1) == truth
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: list[CalibrationBin] = []
    ece = 0.0
    for index in range(bins):
        lower, upper = float(edges[index]), float(edges[index + 1])
        mask = (confidence >= lower) & (
            confidence <= upper if index == bins - 1 else confidence < upper
        )
        count = int(mask.sum())
        mean_confidence = float(confidence[mask].mean()) if count else 0.0
        accuracy = float(correct[mask].mean()) if count else 0.0
        ece += count / truth.size * abs(accuracy - mean_confidence)
        rows.append(CalibrationBin(lower, upper, count, mean_confidence, accuracy))
    return CalibrationReport(float(ece), tuple(rows))


@dataclass(frozen=True, slots=True)
class CoveragePoint:
    threshold: float
    coverage: float
    accuracy: float | None


def accuracy_coverage_curve(
    probabilities: NDArray[np.floating],
    targets: NDArray[np.integer],
    *,
    thresholds: tuple[float, ...],
) -> tuple[CoveragePoint, ...]:
    """Evaluate selective accuracy over precommitted confidence thresholds."""

    values = np.asarray(probabilities, dtype=np.float64)
    truth = np.asarray(targets, dtype=np.int64)
    if values.ndim != 2 or truth.shape != (values.shape[0],):
        raise ValueError("probabilities and targets have incompatible shapes")
    confidence = values.max(axis=1)
    correct = values.argmax(axis=1) == truth
    points: list[CoveragePoint] = []
    for threshold in thresholds:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("coverage thresholds must be within [0, 1]")
        selected = confidence >= threshold
        count = int(selected.sum())
        points.append(
            CoveragePoint(
                float(threshold),
                count / truth.size,
                float(correct[selected].mean()) if count else None,
            )
        )
    return tuple(points)
