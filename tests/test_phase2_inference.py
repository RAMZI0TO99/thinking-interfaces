"""Synthetic Cho paired differences only; no scientific cell or fit is loaded."""

from __future__ import annotations

from dataclasses import fields
from fractions import Fraction
from math import isclose, lcm, sqrt

import pytest
from scipy.stats import t, wilcoxon  # type: ignore[import-untyped]

from evaluation.phase2_inference import CHO_SUBJECTS, calculate_cho_paired_inference


def _rows(values: list[Fraction]) -> tuple[tuple[str, Fraction], ...]:
    assert len(values) == 52
    return tuple(zip(CHO_SUBJECTS, values, strict=True))


def test_exact_rational_ties_match_common_denominator_wilcoxon() -> None:
    values = [
        Fraction(1, 3),
        Fraction(2, 6),
        Fraction(-1, 3),
        Fraction(1, 6),
        Fraction(-1, 6),
        *([Fraction()] * 47),
    ]
    result = calculate_cho_paired_inference(_rows(values), expected_subjects=CHO_SUBJECTS)
    common_denominator = lcm(*(value.denominator for value in values))
    scaled = [value.numerator * (common_denominator // value.denominator) for value in values]
    reference = wilcoxon(
        scaled, zero_method="pratt", alternative="greater", method="asymptotic", correction=False
    )

    assert result.mean_difference == Fraction(1, 156)
    assert result.zero_difference_count == 47
    assert result.nonzero_tied_subject_count == 5
    assert result.nonzero_absolute_tie_class_count == 2
    assert tuple(level for _, level in result.signed_rank_levels[:5]) == (2, 2, -2, 1, -1)
    assert result.wilcoxon_statistic == float(reference.statistic)
    assert result.wilcoxon_p_value == float(reference.pvalue)


def test_pratt_zeros_change_statistic_from_dropping_zeros() -> None:
    values = [Fraction(1, 4), Fraction(-1, 2), *([Fraction()] * 50)]
    result = calculate_cho_paired_inference(_rows(values), expected_subjects=CHO_SUBJECTS)
    pratt = wilcoxon(
        [1, -2, *([0] * 50)],
        zero_method="pratt",
        alternative="greater",
        method="asymptotic",
        correction=False,
    )
    dropped = wilcoxon(
        [1, -2], zero_method="wilcox", alternative="greater", method="asymptotic", correction=False
    )
    assert result.zero_difference_count == 50
    assert result.wilcoxon_statistic == float(pratt.statistic)
    assert result.wilcoxon_p_value == float(pratt.pvalue)
    assert result.wilcoxon_statistic != float(dropped.statistic)


def test_all_zero_and_constant_positive_point_intervals() -> None:
    zero = calculate_cho_paired_inference(_rows([Fraction()] * 52), expected_subjects=CHO_SUBJECTS)
    assert zero.wilcoxon_statistic == 0.0
    assert zero.wilcoxon_p_value == 1.0
    assert zero.zero_difference_count == 52
    assert zero.sample_variance == 0
    assert zero.paired_mean_ci_95 == zero.paired_mean_ci_90 == (0.0, 0.0)

    positive = calculate_cho_paired_inference(
        _rows([Fraction(1, 8)] * 52), expected_subjects=CHO_SUBJECTS
    )
    assert positive.mean_difference == Fraction(1, 8)
    assert positive.sample_variance == 0
    assert positive.paired_mean_ci_95 == positive.paired_mean_ci_90 == (0.125, 0.125)
    assert positive.nonzero_tied_subject_count == 52
    assert positive.nonzero_absolute_tie_class_count == 1
    assert not any(
        "superior" in field.name or "equivalent" in field.name for field in fields(positive)
    )


def test_student_intervals_use_exact_sample_variance_and_subject_count() -> None:
    values = [Fraction(1, 2)] * 26 + [Fraction(-1, 2)] * 26
    result = calculate_cho_paired_inference(_rows(values), expected_subjects=CHO_SUBJECTS)
    assert result.mean_difference == 0
    assert result.sample_variance == Fraction(13, 51)
    standard_error = sqrt(float(Fraction(13, 51 * 52)))
    expected_95 = float(t.ppf(0.975, 51)) * standard_error
    expected_90 = float(t.ppf(0.95, 51)) * standard_error
    assert isclose(result.paired_mean_ci_95[0], -expected_95)
    assert isclose(result.paired_mean_ci_95[1], expected_95)
    assert isclose(result.paired_mean_ci_90[0], -expected_90)
    assert isclose(result.paired_mean_ci_90[1], expected_90)


def test_sign_reversal_and_input_order_invariance() -> None:
    values = [Fraction(1, 2)] * 30 + [Fraction(-1, 4)] * 20 + [Fraction()] * 2
    rows = _rows(values)
    first = calculate_cho_paired_inference(rows, expected_subjects=CHO_SUBJECTS)
    reversed_order = calculate_cho_paired_inference(
        rows[::-1], expected_subjects=CHO_SUBJECTS[::-1]
    )
    negated = calculate_cho_paired_inference(
        tuple((subject, -difference) for subject, difference in rows),
        expected_subjects=CHO_SUBJECTS,
    )
    assert first == reversed_order
    assert negated.mean_difference == -first.mean_difference
    assert negated.wilcoxon_p_value > first.wilcoxon_p_value
    assert negated.wilcoxon_statistic < first.wilcoxon_statistic
    assert negated.paired_mean_ci_95 == tuple(-value for value in first.paired_mean_ci_95[::-1])


@pytest.mark.parametrize("bad_value", [Fraction(2), Fraction(-2), 0.5, 0, None, "1/2"])
def test_invalid_value_or_type_is_rejected(bad_value: object) -> None:
    rows = list(_rows([Fraction()] * 52))
    rows[0] = (CHO_SUBJECTS[0], bad_value)  # type: ignore[assignment]
    with pytest.raises(ValueError, match="exact Fractions"):
        calculate_cho_paired_inference(rows, expected_subjects=CHO_SUBJECTS)


def test_bad_rosters_and_subject_identities_are_rejected() -> None:
    rows = _rows([Fraction()] * 52)
    with pytest.raises(ValueError, match="all 52 distinct"):
        calculate_cho_paired_inference(rows, expected_subjects=CHO_SUBJECTS[:-1])
    with pytest.raises(ValueError, match="all 52 distinct"):
        calculate_cho_paired_inference(
            rows, expected_subjects=(*CHO_SUBJECTS[:-1], CHO_SUBJECTS[0])
        )
    with pytest.raises(ValueError, match="canonical Cho"):
        calculate_cho_paired_inference(rows, expected_subjects=(*CHO_SUBJECTS[:-1], " subject_52"))
    with pytest.raises(ValueError, match="exactly 52"):
        calculate_cho_paired_inference(rows[:-1], expected_subjects=CHO_SUBJECTS)
    with pytest.raises(ValueError, match="duplicate paired"):
        calculate_cho_paired_inference((*rows[:-1], rows[0]), expected_subjects=CHO_SUBJECTS)
    with pytest.raises(ValueError, match="canonical Cho"):
        calculate_cho_paired_inference(
            (*rows[:-1], ("subject_53", Fraction())), expected_subjects=CHO_SUBJECTS
        )
    with pytest.raises(ValueError, match="pair"):
        calculate_cho_paired_inference(
            (*rows[:-1], (CHO_SUBJECTS[-1],)),  # type: ignore[arg-type]
            expected_subjects=CHO_SUBJECTS,
        )


def test_nonzero_float_underflow_cannot_be_reported_as_zero() -> None:
    values = [Fraction(1, 10**1000), *([Fraction()] * 51)]
    with pytest.raises(ValueError, match="represented as a nonzero finite float"):
        calculate_cho_paired_inference(_rows(values), expected_subjects=CHO_SUBJECTS)
