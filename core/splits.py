"""Deterministic cross-subject and episodic split construction."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

import numpy as np
from sklearn.model_selection import GroupKFold  # type: ignore[import-untyped]

from core.contracts import Episode, Split


def leave_one_subject_out(subject_ids: Sequence[str]) -> tuple[Split, ...]:
    """Return one leakage-checked source/target split per subject."""

    subjects = tuple(str(value) for value in subject_ids)
    unique = tuple(sorted(set(subjects)))
    if len(unique) < 2:
        raise ValueError("leave-one-subject-out requires at least two subjects")
    folds: list[Split] = []
    for target in unique:
        support = tuple(index for index, value in enumerate(subjects) if value != target)
        query = tuple(index for index, value in enumerate(subjects) if value == target)
        folds.append(
            Split(
                support_indices=support,
                query_indices=query,
                support_subjects=frozenset(set(unique) - {target}),
                query_subjects=frozenset({target}),
            )
        )
    return tuple(folds)


def grouped_k_fold(subject_ids: Sequence[str], *, folds: int) -> tuple[Split, ...]:
    """Split observations while keeping every subject entirely in one side."""

    subjects = np.asarray(tuple(str(value) for value in subject_ids))
    unique_count = len(set(subjects.tolist()))
    if not 2 <= folds <= unique_count:
        raise ValueError("folds must be between two and the number of subjects")
    dummy = np.zeros(subjects.size, dtype=np.int8)
    result: list[Split] = []
    for support, query in GroupKFold(n_splits=folds).split(dummy, groups=subjects):
        result.append(
            Split(
                support_indices=tuple(int(value) for value in support),
                query_indices=tuple(int(value) for value in query),
                support_subjects=frozenset(subjects[support].tolist()),
                query_subjects=frozenset(subjects[query].tolist()),
            )
        )
    return tuple(result)


def earliest_balanced_episode(
    labels: Sequence[str], *, subject_id: str, shots_per_class: int
) -> Episode:
    """Use each class's earliest trials as support and all remaining trials as query."""

    if shots_per_class < 1:
        raise ValueError("shots_per_class must be positive")
    by_label: defaultdict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_label[str(label)].append(index)
    if len(by_label) < 2:
        raise ValueError("an episode requires at least two classes")
    if any(len(indices) <= shots_per_class for indices in by_label.values()):
        raise ValueError("every class needs support trials and at least one query trial")
    support = sorted(index for values in by_label.values() for index in values[:shots_per_class])
    query = sorted(index for values in by_label.values() for index in values[shots_per_class:])
    return Episode(subject_id, tuple(support), tuple(query))
