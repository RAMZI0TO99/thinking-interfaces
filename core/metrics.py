"""Standard classification metrics required beside every accuracy result."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass

from sklearn.metrics import (  # type: ignore[import-untyped]
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
)


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    balanced_accuracy: float
    cohen_kappa: float
    labels: tuple[str, ...]
    confusion_matrix: tuple[tuple[int, ...], ...]
    class_support: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def record_metrics(self) -> dict[str, float]:
        """Return scalar values suitable for the top level of a RunRecord."""

        return {
            "balanced_accuracy": self.balanced_accuracy,
            "cohen_kappa": self.cohen_kappa,
        }


def classification_report(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    *,
    labels: Sequence[str] | None = None,
) -> ClassificationReport:
    """Compute the fixed Phase I metric set with deterministic label ordering."""

    if not y_true:
        raise ValueError("y_true must not be empty")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")

    ordered_labels = (
        tuple(labels) if labels is not None else tuple(sorted(set(y_true) | set(y_pred)))
    )
    if not ordered_labels or len(set(ordered_labels)) != len(ordered_labels):
        raise ValueError("labels must be non-empty and unique")
    unknown = (set(y_true) | set(y_pred)) - set(ordered_labels)
    if unknown:
        raise ValueError(f"observed labels missing from labels: {sorted(unknown)}")

    matrix = confusion_matrix(y_true, y_pred, labels=ordered_labels)
    support = Counter(y_true)
    return ClassificationReport(
        balanced_accuracy=float(balanced_accuracy_score(y_true, y_pred)),
        cohen_kappa=float(cohen_kappa_score(y_true, y_pred, labels=ordered_labels)),
        labels=ordered_labels,
        confusion_matrix=tuple(tuple(int(value) for value in row) for row in matrix),
        class_support={label: support.get(label, 0) for label in ordered_labels},
    )
