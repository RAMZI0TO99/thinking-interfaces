"""Tiny exact-rational rosters; no file, model, or scientific cell is loaded."""

from __future__ import annotations

from dataclasses import replace

import pytest

from evaluation.phase2_subject_aggregation import (
    AdmittedCellDigest,
    ExpectedCell,
    ScoreRow,
    SubjectAggregation,
    SubjectMethodMean,
    aggregate_subject_methods,
)


def _grid() -> tuple[tuple[ExpectedCell, ...], tuple[ScoreRow, ...]]:
    first = ExpectedCell("dataset", "subject_02", "method_b", 5, 2)
    second = ExpectedCell("dataset", "subject_01", "method_a", 10, 2)
    third = ExpectedCell("dataset", "subject_01", "method_a", 5, 1)
    fourth = ExpectedCell("dataset", "subject_01", "method_b", 5, 1)
    fifth = ExpectedCell("dataset", "subject_01", "method_a", 5, 2)
    return (
        (first, second, third, fourth, fifth),
        (
            ScoreRow(first, 1, 3, "a" * 64),
            ScoreRow(second, 4, 6, "b" * 64),
            ScoreRow(third, 2, 6, "c" * 64),
            ScoreRow(fourth, 1, 1, "d" * 64),
            ScoreRow(fifth, 2, 3, "e" * 64),
        ),
    )


def test_exact_thirds_unreduced_pairs_and_stable_digest_roster() -> None:
    expected, rows = _grid()
    result = aggregate_subject_methods(expected, rows)
    assert result == SubjectAggregation(
        means=(
            SubjectMethodMean("dataset", "subject_01", "method_a", 5, 1, 2, 2),
            SubjectMethodMean("dataset", "subject_01", "method_a", 10, 2, 3, 1),
            SubjectMethodMean("dataset", "subject_01", "method_b", 5, 1, 1, 1),
            SubjectMethodMean("dataset", "subject_02", "method_b", 5, 1, 3, 1),
        ),
        admitted_digests=tuple(
            AdmittedCellDigest(row.key, row.cell_sha256)
            for row in sorted(rows, key=lambda row: row.key)
        ),
    )
    assert aggregate_subject_methods(tuple(reversed(expected)), reversed(rows)) == result


def test_duplicate_expected_and_duplicate_or_reused_row_are_rejected() -> None:
    expected, rows = _grid()
    with pytest.raises(ValueError, match="duplicate cell identities"):
        aggregate_subject_methods((*expected, expected[0]), rows)
    with pytest.raises(ValueError, match="duplicate score row"):
        aggregate_subject_methods(expected, (*rows, rows[0]))
    with pytest.raises(ValueError, match="digest cannot fill two"):
        aggregate_subject_methods(expected, (*rows[:-1], replace(rows[-1], cell_sha256="a" * 64)))


def test_missing_extra_and_wrong_shots_do_not_silently_change_roster() -> None:
    expected, rows = _grid()
    with pytest.raises(ValueError, match="missing score rows"):
        aggregate_subject_methods(expected, rows[:-1])
    extra = ScoreRow(ExpectedCell("dataset", "subject_03", "method_a", 5, 1), 1, 2,
                     "e" * 64)
    with pytest.raises(ValueError, match="outside the expected roster"):
        aggregate_subject_methods(expected, (*rows, extra))
    wrong_shots = replace(rows[0], key=replace(rows[0].key, shots=20))
    with pytest.raises(ValueError, match="outside the expected roster"):
        aggregate_subject_methods(expected, (wrong_shots, *rows[1:]))


@pytest.mark.parametrize("numerator,denominator", [
    (1, 0), (-1, 3), (4, 3), (True, 3), (1, False), (1.0, 3), (1, "3"),
])
def test_malformed_or_out_of_range_score_is_rejected(
    numerator: object, denominator: object,
) -> None:
    expected, _ = _grid()
    with pytest.raises(ValueError, match="integer rational"):
        ScoreRow(expected[0], numerator, denominator, "a" * 64)  # type: ignore[arg-type]


@pytest.mark.parametrize("digest", ["a" * 63, "A" * 64, "g" * 64, "", None])
def test_bad_externally_verified_digest_is_rejected(digest: object) -> None:
    expected, _ = _grid()
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        ScoreRow(expected[0], 1, 3, digest)  # type: ignore[arg-type]


def test_bad_identity_or_missing_expected_roster_is_rejected() -> None:
    with pytest.raises(ValueError, match="canonical name"):
        ExpectedCell(" dataset", "subject", "method", 5, 1)
    with pytest.raises(ValueError, match="positive integer"):
        ExpectedCell("dataset", "subject", "method", True, 1)
    with pytest.raises(ValueError, match="nonnegative integer"):
        ExpectedCell("dataset", "subject", "method", 5, -1)
    with pytest.raises(ValueError, match="nonempty expected roster"):
        aggregate_subject_methods((), ())
