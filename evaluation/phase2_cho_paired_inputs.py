"""Pure exact-rational Cho paired inputs from externally verified score rows.

The caller is responsible for admitting and verifying every underlying cell.
This module only enforces the fixed first-tranche roster, averages five seeds,
and constructs subject-level LoRA-minus-linear differences. It does not read
records, run inference, or make a scientific claim.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction

from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    SELECTED_METHODS,
    SELECTED_SEEDS,
    SELECTED_SHOTS,
)
from evaluation.phase2_subject_aggregation import (
    ExpectedCell,
    ScoreRow,
    SubjectAggregation,
    aggregate_subject_methods,
)


@dataclass(frozen=True, slots=True)
class ChoPairedInputs:
    """Complete subject aggregation and sorted exact LoRA-minus-linear pairs."""

    aggregation: SubjectAggregation
    paired_differences: tuple[tuple[str, Fraction], ...]


def build_cho_paired_inputs(rows: Iterable[ScoreRow]) -> ChoPairedInputs:
    """Require the canonical 1,040 cells before forming the 52 paired inputs."""
    if (
        tuple(f"subject_{index:02d}" for index in range(1, 53)) != CHO_SUBJECTS
        or SELECTED_METHODS != ("labram_linear", "labram_lora", "labram_full", "eegnet")
        or SELECTED_SEEDS != (11, 23, 37, 53, 71)
        or SELECTED_SHOTS != 5
    ):
        raise ValueError("selected Cho first-tranche roster differs")
    expected_roster = tuple(
        ExpectedCell("cho2017", subject, method, SELECTED_SHOTS, seed)
        for subject in CHO_SUBJECTS
        for method in SELECTED_METHODS
        for seed in SELECTED_SEEDS
    )
    if len(expected_roster) != 1040 or len(set(expected_roster)) != 1040:
        raise ValueError("selected Cho first-tranche roster differs")

    aggregation = aggregate_subject_methods(expected_roster, rows)
    expected_groups = {
        ("cho2017", subject, method, SELECTED_SHOTS)
        for subject in CHO_SUBJECTS
        for method in SELECTED_METHODS
    }
    if len(aggregation.means) != 208 or len(aggregation.admitted_digests) != 1040:
        raise ValueError("Cho subject aggregation has incomplete coverage")
    means: dict[tuple[str, str, str, int], Fraction] = {}
    for mean in aggregation.means:
        key = (mean.dataset, mean.subject, mean.method, mean.shots)
        if (
            key not in expected_groups
            or key in means
            or type(mean.contributing_cells) is not int
            or mean.contributing_cells != len(SELECTED_SEEDS)
            or type(mean.numerator) is not int
            or type(mean.denominator) is not int
            or mean.denominator <= 0
            or not 0 <= mean.numerator <= mean.denominator
        ):
            raise ValueError("Cho subject mean differs from the five-cell roster")
        means[key] = Fraction(mean.numerator, mean.denominator)
    if set(means) != expected_groups:
        raise ValueError("Cho subject means differ from the selected roster")

    pairs = tuple(
        (
            subject,
            means[("cho2017", subject, "labram_lora", SELECTED_SHOTS)]
            - means[("cho2017", subject, "labram_linear", SELECTED_SHOTS)],
        )
        for subject in sorted(CHO_SUBJECTS)
    )
    if len(pairs) != 52 or any(not -1 <= difference <= 1 for _, difference in pairs):
        raise ValueError("Cho paired differences are incomplete or outside [-1, 1]")
    return ChoPairedInputs(aggregation, pairs)
