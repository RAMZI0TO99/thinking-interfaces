"""Maximum-probability confidence gate with explicit abstention."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class GateDecision:
    state: str
    confidence: float
    abstained: bool
    winning_index: int | None


def confidence_gate(
    probabilities: NDArray[np.floating],
    class_labels: tuple[str, ...],
    *,
    threshold: float,
    neutral_state: str = "neutral",
    probability_tolerance: float = 1e-4,
) -> GateDecision:
    """Emit one class only when a unique maximum reaches the threshold."""

    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1 or values.size != len(class_labels) or values.size < 2:
        raise ValueError("probabilities must be one-dimensional and match class_labels")
    if len(set(class_labels)) != len(class_labels) or not all(class_labels):
        raise ValueError("class_labels must be non-empty and unique")
    if neutral_state in class_labels or not neutral_state:
        raise ValueError("neutral_state must be non-empty and separate from class labels")
    if not 0.0 <= threshold <= 1.0 or probability_tolerance < 0:
        raise ValueError("threshold and probability_tolerance are invalid")
    if not np.isfinite(values).all() or np.any(values < 0.0) or np.any(values > 1.0):
        raise ValueError("probabilities must be finite and within [0, 1]")
    if not np.isclose(values.sum(), 1.0, atol=probability_tolerance, rtol=0.0):
        raise ValueError("probabilities must sum to one")

    winning_index = int(np.argmax(values))
    confidence = float(values[winning_index])
    tied = int(np.count_nonzero(np.isclose(values, confidence, atol=1e-12, rtol=0.0))) > 1
    abstained = confidence < threshold or tied
    return GateDecision(
        state=neutral_state if abstained else class_labels[winning_index],
        confidence=confidence,
        abstained=abstained,
        winning_index=None if abstained else winning_index,
    )
