"""Pure exact-rational aggregation over an externally verified Phase II cell roster.

The caller must verify each cell's identity, contents, and digest before making
a ScoreRow. This module admits only an explicit complete roster and computes
equal-weight means across seeds within each subject, method, and shot count. It
does not read files, estimate uncertainty, or publish a scientific report.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction

from evaluation.phase2_protocol import require_digest


@dataclass(frozen=True, order=True, slots=True)
class ExpectedCell:
    dataset: str
    subject: str
    method: str
    shots: int
    seed: int

    def __post_init__(self) -> None:
        for name in ("dataset", "subject", "method"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError(f"{name} must be a nonempty canonical name")
        if type(self.shots) is not int or self.shots < 1:
            raise ValueError("shots must be a positive integer")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ScoreRow:
    key: ExpectedCell
    numerator: int
    denominator: int
    cell_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.key, ExpectedCell):
            raise ValueError("score row requires an expected cell identity")
        if (
            type(self.numerator) is not int or type(self.denominator) is not int
            or self.denominator <= 0 or not 0 <= self.numerator <= self.denominator
        ):
            raise ValueError("score must be an integer rational in [0, 1]")
        require_digest(self.cell_sha256, "externally verified cell")


@dataclass(frozen=True, slots=True)
class SubjectMethodMean:
    dataset: str
    subject: str
    method: str
    shots: int
    numerator: int
    denominator: int
    contributing_cells: int


@dataclass(frozen=True, slots=True)
class AdmittedCellDigest:
    key: ExpectedCell
    cell_sha256: str


@dataclass(frozen=True, slots=True)
class SubjectAggregation:
    means: tuple[SubjectMethodMean, ...]
    admitted_digests: tuple[AdmittedCellDigest, ...]


def aggregate_subject_methods(
    expected_roster: Sequence[ExpectedCell], rows: Iterable[ScoreRow],
) -> SubjectAggregation:
    """Require exact roster coverage, then average every declared cell equally."""
    if not isinstance(expected_roster, Sequence) or not expected_roster:
        raise ValueError("an explicit nonempty expected roster is required")
    expected = tuple(expected_roster)
    if any(not isinstance(key, ExpectedCell) for key in expected):
        raise ValueError("expected roster contains an invalid cell identity")
    if len(set(expected)) != len(expected):
        raise ValueError("expected roster contains duplicate cell identities")
    expected_set = set(expected)
    admitted: dict[ExpectedCell, ScoreRow] = {}
    digests: set[str] = set()
    for row in rows:
        if not isinstance(row, ScoreRow):
            raise ValueError("rows must be validated ScoreRow values")
        if row.key not in expected_set:
            raise ValueError("score row is outside the expected roster")
        if row.key in admitted:
            raise ValueError("duplicate score row for one expected cell")
        if row.cell_sha256 in digests:
            raise ValueError("one verified cell digest cannot fill two roster cells")
        admitted[row.key] = row
        digests.add(row.cell_sha256)
    if len(admitted) != len(expected):
        raise ValueError("expected roster has missing score rows")

    ordered = tuple(sorted(expected))
    groups: dict[tuple[str, str, str, int], list[Fraction]] = {}
    for key in ordered:
        row = admitted[key]
        group = key.dataset, key.subject, key.method, key.shots
        groups.setdefault(group, []).append(Fraction(row.numerator, row.denominator))
    means = []
    for (dataset, subject, method, shots), scores in sorted(groups.items()):
        mean = sum(scores, Fraction(0, 1)) / len(scores)
        means.append(SubjectMethodMean(
            dataset, subject, method, shots, mean.numerator, mean.denominator, len(scores),
        ))
    roster = tuple(AdmittedCellDigest(key, admitted[key].cell_sha256) for key in ordered)
    return SubjectAggregation(tuple(means), roster)
