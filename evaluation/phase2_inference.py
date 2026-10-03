"""Pure, unratified Cho Phase II paired calculations.

The caller must independently admit the complete 1,040-cell roster, verify all
source and analysis pins, and aggregate the five seeds for each subject/method.
This function cannot establish any of those conditions or issue a scientific
superiority or equivalence claim. Inputs must be exact rational differences,
not Fractions constructed from previously rounded floating-point scores.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import isfinite, sqrt

from scipy.stats import t, wilcoxon  # type: ignore[import-untyped]

CHO_SUBJECTS = tuple(f"subject_{index:02d}" for index in range(1, 53))
_CHO_SUBJECT_PATTERN = re.compile(r"subject_(?:0[1-9]|[1-4][0-9]|5[0-2])\Z")


@dataclass(frozen=True, slots=True)
class ChoPairedCalculations:
    """Numerical results only; no cell admission or inferential decision."""

    subject_count: int
    mean_difference: Fraction
    sample_variance: Fraction
    zero_difference_count: int
    nonzero_tied_subject_count: int
    nonzero_absolute_tie_class_count: int
    signed_rank_levels: tuple[tuple[str, int], ...]
    wilcoxon_statistic: float
    wilcoxon_p_value: float
    paired_mean_ci_95: tuple[float, float]
    paired_mean_ci_90: tuple[float, float]


def _require_cho_subject(value: object) -> str:
    if not isinstance(value, str) or _CHO_SUBJECT_PATTERN.fullmatch(value) is None:
        raise ValueError("subject IDs must be canonical Cho subject_01..subject_52 names")
    return value


def _finite_float(value: Fraction, name: str) -> float:
    result = float(value)
    if not isfinite(result) or (value != 0 and result == 0.0):
        raise ValueError(f"{name} cannot be represented as a nonzero finite float")
    return result


def _paired_mean_interval(
    mean: float,
    standard_error: float,
    *,
    confidence_level: float,
    subjects: int,
) -> tuple[float, float]:
    if standard_error == 0.0:
        return mean, mean
    critical = float(t.ppf((1.0 + confidence_level) / 2.0, subjects - 1))
    lower = mean - critical * standard_error
    upper = mean + critical * standard_error
    if not all(isfinite(value) for value in (critical, lower, upper)):
        raise ValueError("paired-mean interval contains a non-finite value")
    return lower, upper


def calculate_cho_paired_inference(
    paired_differences: Sequence[tuple[str, Fraction]],
    *,
    expected_subjects: Sequence[str],
) -> ChoPairedCalculations:
    """Calculate proposed paired summaries after independent full-roster admission.

    The caller must independently admit all 1,040 cells and verify the source,
    preprocessing, method, seed, and analysis pins. This pure calculation does
    not do so and cannot decide scientific superiority or equivalence.
    """
    if not isinstance(expected_subjects, Sequence) or isinstance(expected_subjects, str):
        raise ValueError("expected_subjects must be an explicit sequence")
    expected = tuple(_require_cho_subject(subject) for subject in expected_subjects)
    if len(expected) != 52 or len(set(expected)) != 52 or set(expected) != set(CHO_SUBJECTS):
        raise ValueError("expected_subjects must contain all 52 distinct canonical Cho subjects")
    if not isinstance(paired_differences, Sequence) or isinstance(paired_differences, str):
        raise ValueError("paired_differences must be an explicit sequence")
    if len(paired_differences) != 52:
        raise ValueError("exactly 52 paired differences are required")

    by_subject: dict[str, Fraction] = {}
    for row in paired_differences:
        if not isinstance(row, tuple) or len(row) != 2:
            raise ValueError("each paired difference must be a (subject_id, Fraction) pair")
        subject = _require_cho_subject(row[0])
        difference = row[1]
        if type(difference) is not Fraction or not -1 <= difference <= 1:
            raise ValueError("paired differences must be exact Fractions in [-1, 1]")
        if subject in by_subject:
            raise ValueError("duplicate paired subject ID")
        if subject not in expected:
            raise ValueError("paired subject is outside expected_subjects")
        by_subject[subject] = difference
    if set(by_subject) != set(expected):
        raise ValueError("paired differences do not match expected_subjects")

    ordered = tuple((subject, by_subject[subject]) for subject in sorted(expected))
    differences = tuple(difference for _, difference in ordered)
    mean = sum(differences, Fraction()) / 52
    sample_variance = sum(((value - mean) ** 2 for value in differences), Fraction()) / 51
    zero_count = sum(value == 0 for value in differences)

    nonzero_counts: dict[Fraction, int] = {}
    for difference in differences:
        if difference != 0:
            magnitude = abs(difference)
            nonzero_counts[magnitude] = nonzero_counts.get(magnitude, 0) + 1
    tied_subjects = sum(count for count in nonzero_counts.values() if count > 1)
    tied_classes = sum(count > 1 for count in nonzero_counts.values())
    level_by_magnitude = {
        magnitude: level for level, magnitude in enumerate(sorted(nonzero_counts), start=1)
    }
    signed_levels = tuple(
        (
            subject,
            0
            if difference == 0
            else (1 if difference > 0 else -1) * level_by_magnitude[abs(difference)],
        )
        for subject, difference in ordered
    )

    if zero_count == 52:
        statistic, p_value = 0.0, 1.0
    else:
        result = wilcoxon(
            [level for _, level in signed_levels],
            zero_method="pratt",
            alternative="greater",
            method="asymptotic",
            correction=False,
        )
        statistic, p_value = float(result.statistic), float(result.pvalue)
        if not isfinite(statistic) or not isfinite(p_value) or not 0.0 <= p_value <= 1.0:
            raise ValueError("Wilcoxon calculation produced an invalid result")

    mean_float = _finite_float(mean, "paired mean")
    variance_of_mean = sample_variance / 52
    standard_error = sqrt(_finite_float(variance_of_mean, "paired-mean variance"))
    return ChoPairedCalculations(
        subject_count=52,
        mean_difference=mean,
        sample_variance=sample_variance,
        zero_difference_count=zero_count,
        nonzero_tied_subject_count=tied_subjects,
        nonzero_absolute_tie_class_count=tied_classes,
        signed_rank_levels=signed_levels,
        wilcoxon_statistic=statistic,
        wilcoxon_p_value=p_value,
        paired_mean_ci_95=_paired_mean_interval(
            mean_float,
            standard_error,
            confidence_level=0.95,
            subjects=52,
        ),
        paired_mean_ci_90=_paired_mean_interval(
            mean_float,
            standard_error,
            confidence_level=0.90,
            subjects=52,
        ),
    )
