"""Precommitted subject-level paired inference for Phase I."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray
from scipy.stats import t, ttest_1samp, wilcoxon  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class PairedComparison:
    mean_difference: float
    confidence_interval: tuple[float, float]
    wilcoxon_statistic: float
    wilcoxon_p_value: float
    subject_count: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def paired_comparison(
    first: NDArray[np.floating],
    second: NDArray[np.floating],
    *,
    confidence_level: float = 0.95,
) -> PairedComparison:
    """Compare same-subject scores as one paired difference with a t interval."""

    left = np.asarray(first, dtype=np.float64)
    right = np.asarray(second, dtype=np.float64)
    if left.ndim != 1 or right.shape != left.shape or left.size < 2:
        raise ValueError("paired score arrays must be one-dimensional and equal length")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("paired scores must be finite")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    differences = left - right
    mean = float(differences.mean())
    standard_error = float(differences.std(ddof=1) / np.sqrt(differences.size))
    critical = float(t.ppf((1.0 + confidence_level) / 2.0, differences.size - 1))
    statistic, p_value = wilcoxon(differences, zero_method="pratt")
    return PairedComparison(
        mean,
        (mean - critical * standard_error, mean + critical * standard_error),
        float(statistic),
        float(p_value),
        int(differences.size),
    )


@dataclass(frozen=True, slots=True)
class TOSTResult:
    margin: float
    lower_p_value: float
    upper_p_value: float
    equivalent: bool


def paired_tost(
    first: NDArray[np.floating],
    second: NDArray[np.floating],
    *,
    margin: float,
    alpha: float = 0.05,
) -> TOSTResult:
    """Paired two-one-sided t tests for equivalence within ``±margin``."""

    if margin <= 0 or not 0.0 < alpha < 0.5:
        raise ValueError("margin and alpha are invalid")
    differences = np.asarray(first, dtype=np.float64) - np.asarray(second, dtype=np.float64)
    if differences.ndim != 1 or differences.size < 2 or not np.isfinite(differences).all():
        raise ValueError("paired differences must contain at least two finite values")
    lower = ttest_1samp(differences, popmean=-margin, alternative="greater")
    upper = ttest_1samp(differences, popmean=margin, alternative="less")
    lower_p, upper_p = float(lower.pvalue), float(upper.pvalue)
    return TOSTResult(margin, lower_p, upper_p, lower_p < alpha and upper_p < alpha)


def variance_derived_equivalence_margin(
    standard_deviation: float,
    *,
    subjects: int,
    target_power: float = 0.8,
    alpha: float = 0.05,
) -> float:
    """Symmetric TOST design margin at zero true difference and known variance.

    Both one-sided tests must reject: |Z| < margin / SE - z(1-alpha).
    Thus target power is 2*Phi(margin/SE-z(1-alpha))-1, not a single tail.
    The supplied SD is a planning proxy; future paired-difference power may differ.
    """

    if not isfinite(standard_deviation) or standard_deviation <= 0 or subjects < 2:
        raise ValueError("positive variance and at least two subjects are required")
    if not 0.5 < target_power < 1.0 or not 0.0 < alpha < 0.5:
        raise ValueError("target_power or alpha is invalid")
    from scipy.stats import norm

    return float(
        (norm.ppf(1.0 - alpha) + norm.ppf((1.0 + target_power) / 2.0))
        * standard_deviation
        / np.sqrt(subjects)
    )


def normal_approximation_equivalence_power(
    margin: float,
    *,
    standard_deviation: float,
    subjects: int,
    alpha: float = 0.05,
) -> float:
    """Probability both symmetric TOST bounds pass at zero true difference.

    Uses known variance/normal critical values, not exact finite-sample t power.
    """

    if (
        not isfinite(margin)
        or not isfinite(standard_deviation)
        or margin <= 0
        or standard_deviation <= 0
        or subjects < 2
    ):
        raise ValueError("margin, variance, and subject count are invalid")
    if not 0.0 < alpha < 0.5:
        raise ValueError("alpha is invalid")
    from scipy.stats import norm

    signal = margin * np.sqrt(subjects) / standard_deviation
    return max(0.0, float(2.0 * norm.cdf(signal - norm.ppf(1.0 - alpha)) - 1.0))
