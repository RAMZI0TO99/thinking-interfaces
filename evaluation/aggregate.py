"""Subject-level aggregation utilities for repeated-seed experiments."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import t  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class SubjectInterval:
    subject_means: dict[int, float]
    mean: float
    standard_deviation: float
    confidence_level: float
    confidence_interval: tuple[float, float]
    subject_count: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def subject_level_interval(
    observations: Iterable[tuple[int, float]], *, confidence_level: float = 0.95
) -> SubjectInterval:
    """Average seeds within subjects, then form an interval across subjects."""

    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    grouped: defaultdict[int, list[float]] = defaultdict(list)
    for subject, value in observations:
        if subject < 1 or not np.isfinite(value):
            raise ValueError("subjects must be positive and scores must be finite")
        grouped[subject].append(float(value))
    if len(grouped) < 2:
        raise ValueError("at least two subjects are required for a subject-level interval")

    subject_means = {
        subject: float(np.mean(values)) for subject, values in sorted(grouped.items())
    }
    values = np.asarray(list(subject_means.values()), dtype=np.float64)
    mean = float(values.mean())
    standard_deviation = float(values.std(ddof=1))
    standard_error = standard_deviation / np.sqrt(values.size)
    critical = float(t.ppf((1.0 + confidence_level) / 2.0, df=values.size - 1))
    margin = critical * standard_error
    return SubjectInterval(
        subject_means=subject_means,
        mean=mean,
        standard_deviation=standard_deviation,
        confidence_level=confidence_level,
        confidence_interval=(mean - margin, mean + margin),
        subject_count=int(values.size),
    )
