"""Synthetic exact-rational checks for the pure Cho paired-input builder."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest

import evaluation.phase2_cho_paired_inputs as paired_inputs
from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    SELECTED_SHOTS,
)
from evaluation.phase2_cho_paired_inputs import build_cho_paired_inputs
from evaluation.phase2_inference import calculate_cho_paired_inference
from evaluation.phase2_subject_aggregation import ExpectedCell, ScoreRow


def _rows() -> tuple[ScoreRow, ...]:
    return tuple(
        ScoreRow(
            ExpectedCell("cho2017", subject, method, SELECTED_SHOTS, seed),
            10 * (method_index + 1) + subject_index % 5 + seed_index,
            97,
            f"{1 + (subject_index * 4 + method_index) * 5 + seed_index:064x}",
        )
        for subject_index, subject in enumerate(CHO_SUBJECTS)
        for method_index, method in enumerate(SELECTED_METHODS)
        for seed_index, seed in enumerate(SELECTED_SEEDS)
    )


def test_full_roster_yields_exact_means_and_inference_ready_pairs() -> None:
    result = build_cho_paired_inputs(_rows())
    assert len(result.aggregation.means) == 208
    assert len(result.aggregation.admitted_digests) == 1040
    assert all(mean.contributing_cells == 5 for mean in result.aggregation.means)
    assert result.paired_differences == tuple(
        (subject, Fraction(10, 97)) for subject in CHO_SUBJECTS
    )
    inference = calculate_cho_paired_inference(
        result.paired_differences, expected_subjects=CHO_SUBJECTS
    )
    assert inference.subject_count == 52
    assert inference.mean_difference == Fraction(10, 97)


def test_input_order_does_not_change_aggregation_or_pairs() -> None:
    rows = _rows()
    assert build_cho_paired_inputs(reversed(rows)) == build_cho_paired_inputs(rows)


def test_missing_extra_and_duplicate_cells_are_rejected() -> None:
    rows = _rows()
    with pytest.raises(ValueError, match="missing score rows"):
        build_cho_paired_inputs(rows[:-1])
    extra = ScoreRow(ExpectedCell("cho2017", "subject_53", "eegnet", 5, 11), 1, 2, "f" * 64)
    with pytest.raises(ValueError, match="outside the expected roster"):
        build_cho_paired_inputs((*rows, extra))
    with pytest.raises(ValueError, match="duplicate score row"):
        build_cho_paired_inputs((*rows, rows[0]))


@pytest.mark.parametrize("change", [
    {"method": "labram_partial"},
    {"seed": 12},
    {"shots": 10},
    {"dataset": "bci_iv_2a"},
])
def test_wrong_case_identity_is_rejected(change: dict[str, object]) -> None:
    rows = _rows()
    wrong = replace(rows[0], key=replace(rows[0].key, **change))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="outside the expected roster"):
        build_cho_paired_inputs((wrong, *rows[1:]))


def test_reused_or_malformed_digest_is_rejected() -> None:
    rows = _rows()
    with pytest.raises(ValueError, match="digest cannot fill two"):
        build_cho_paired_inputs((*rows[:-1], replace(rows[-1], cell_sha256=rows[0].cell_sha256)))
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        replace(rows[0], cell_sha256="bad")


@pytest.mark.parametrize(("name", "value"), [
    ("CHO_SUBJECTS", (*CHO_SUBJECTS[:-1], "subject_53")),
    ("SELECTED_METHODS", (*SELECTED_METHODS[:-1], "labram_partial")),
    ("SELECTED_SEEDS", (*SELECTED_SEEDS[:-1], 73)),
    ("SELECTED_SHOTS", 10),
])
def test_frozen_roster_value_drift_is_rejected_before_aggregation(
    monkeypatch: pytest.MonkeyPatch, name: str, value: object,
) -> None:
    monkeypatch.setattr(paired_inputs, name, value)
    with pytest.raises(ValueError, match="selected Cho first-tranche roster differs"):
        build_cho_paired_inputs(_rows())
