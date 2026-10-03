"""Immutable Phase II partitions; no changes to the frozen Phase I split API."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import config_digest, load_toml

SELECTION_CEILING_RELATIVE = "configs/phase2/selection_ceiling.toml"


def selection_gradient_ceiling(root: Path) -> int:
    """The committed full-cohort selection ceiling; raising it is an owner act."""
    document = load_toml(Path(root) / SELECTION_CEILING_RELATIVE)
    value = document.get("maximum_gradient_steps")
    if type(value) is not int or value < 1:
        raise ValueError("the committed selection ceiling must be a positive integer")
    return value


def require_digest(value: str, name: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def require_names(values: tuple[str, ...], name: str) -> None:
    if (
        not isinstance(values, tuple)
        or not values
        or any(not isinstance(v, str) or not v.strip() for v in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError(f"{name} must contain unique nonempty strings")


@dataclass(frozen=True, slots=True)
class TrialCatalog:
    """Retained trials in loader order, bound to exact input/preprocessing bytes."""

    dataset: str
    subject: str
    trial_ids: tuple[str, ...]
    labels: tuple[str, ...]
    classes: tuple[str, ...]
    artifact_sha256: str
    preprocessing_sha256: str

    def __post_init__(self) -> None:
        require_names((self.dataset,), "dataset")
        require_names((self.subject,), "subject")
        require_names(self.trial_ids, "trial_ids")
        require_names(self.classes, "classes")
        if len(self.classes) < 2 or tuple(sorted(self.classes)) != self.classes:
            raise ValueError("classes must be sorted and contain at least two classes")
        if not isinstance(self.labels, tuple) or len(self.labels) != len(self.trial_ids):
            raise ValueError("labels must match trial_ids")
        if any(not isinstance(label, str) or label not in self.classes for label in self.labels):
            raise ValueError("labels must belong to the declared class inventory")
        require_digest(self.artifact_sha256, "artifact_sha256")
        require_digest(self.preprocessing_sha256, "preprocessing_sha256")

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class EpisodePartition:
    shots_per_class: int
    support_indices: tuple[int, ...]
    query_indices: tuple[int, ...]
    unused_pool_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if type(self.shots_per_class) is not int or self.shots_per_class < 1:
            raise ValueError("shots_per_class must be a positive integer")
        collections = (self.support_indices, self.query_indices, self.unused_pool_indices)
        if not self.support_indices or not self.query_indices:
            raise ValueError("support and query must be nonempty")
        for indices in collections:
            if (
                not isinstance(indices, tuple)
                or any(type(i) is not int or i < 0 for i in indices)
                or tuple(sorted(set(indices))) != indices
            ):
                raise ValueError("partition indices must be sorted unique nonnegative integers")
        if sum(map(len, collections)) != len(set().union(*collections)):
            raise ValueError("support, query and unused pool must be disjoint")


@dataclass(frozen=True, slots=True)
class EpisodeManifest:
    catalog: TrialCatalog
    protocol_sha256: str
    partitions: tuple[EpisodePartition, ...]

    def __post_init__(self) -> None:
        require_digest(self.protocol_sha256, "protocol_sha256")
        if not isinstance(self.partitions, tuple) or not self.partitions:
            raise ValueError("partitions must be a nonempty tuple")
        shots = tuple(row.shots_per_class for row in self.partitions)
        if tuple(sorted(set(shots))) != shots:
            raise ValueError("partitions must have increasing unique shot levels")
        maximum = shots[-1]
        by_class = {
            label: tuple(i for i, value in enumerate(self.catalog.labels) if value == label)
            for label in self.catalog.classes
        }
        if any(len(indices) <= maximum for indices in by_class.values()):
            raise ValueError("every class needs maximum support and a query example")
        pool = {i for indices in by_class.values() for i in indices[:maximum]}
        query = tuple(i for i in range(len(self.catalog.labels)) if i not in pool)
        for row in self.partitions:
            support = tuple(
                sorted(i for indices in by_class.values() for i in indices[: row.shots_per_class])
            )
            if (
                row.support_indices != support
                or row.query_indices != query
                or row.unused_pool_indices != tuple(sorted(pool - set(support)))
            ):
                raise ValueError("partition violates nested fixed-earliest common-query policy")

    def payload(self) -> dict[str, Any]:
        return {"schema_version": 1, "phase": 2, **asdict(self)}

    @property
    def sha256(self) -> str:
        return config_digest(self.payload())

    def partition(self, shots_per_class: int) -> EpisodePartition:
        if type(shots_per_class) is not int:
            raise ValueError("shots_per_class must be an integer")
        for partition in self.partitions:
            if partition.shots_per_class == shots_per_class:
                return partition
        raise ValueError("shot condition is not in this manifest")


def nested_episode(
    catalog: TrialCatalog, *, shots: tuple[int, ...], protocol_sha256: str
) -> EpisodeManifest:
    """Withhold the maximum support pool at every shot; query never changes."""
    require_digest(protocol_sha256, "protocol_sha256")
    if (
        not isinstance(shots, tuple)
        or not shots
        or any(type(n) is not int or n < 1 for n in shots)
        or tuple(sorted(set(shots))) != shots
    ):
        raise ValueError("shots must be strictly increasing positive integers")
    per_class = {
        label: tuple(i for i, value in enumerate(catalog.labels) if value == label)
        for label in catalog.classes
    }
    maximum = shots[-1]
    insufficient = {
        label: len(indices) for label, indices in per_class.items() if len(indices) <= maximum
    }
    if insufficient:
        raise ValueError(f"insufficient retained support/query trials per class: {insufficient}")
    pool = frozenset(i for indices in per_class.values() for i in indices[:maximum])
    query = tuple(i for i in range(len(catalog.trial_ids)) if i not in pool)
    partitions = []
    for count in shots:
        support = tuple(sorted(i for indices in per_class.values() for i in indices[:count]))
        unused = tuple(sorted(pool - set(support)))
        partitions.append(EpisodePartition(count, support, query, unused))
    return EpisodeManifest(catalog, protocol_sha256, tuple(partitions))


def verify_episode_payload(
    payload: Mapping[str, Any],
    *,
    catalog: TrialCatalog,
    shots: tuple[int, ...],
    protocol_sha256: str,
    expected_sha256: str,
) -> bool:
    """Reconstruct from trusted inputs; a self-consistent tampered hash is insufficient."""
    try:
        expected = nested_episode(catalog, shots=shots, protocol_sha256=protocol_sha256)
        return config_digest(payload) == expected_sha256 == expected.sha256
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True, slots=True)
class InnerFold:
    training_subjects: tuple[str, ...]
    validation_subject: str


@dataclass(frozen=True, slots=True)
class SourceSelection:
    dataset: str
    target_subject: str
    source_subjects: tuple[str, ...]
    inner_folds: tuple[InnerFold, ...]
    catalog_sha256: tuple[tuple[str, str], ...]

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


def source_selection(catalogs: Sequence[TrialCatalog], *, target: str) -> SourceSelection:
    """Every inner validation fold excludes the outer target entirely."""
    if len(catalogs) < 3:
        raise ValueError("source-only inner validation requires at least three subjects")
    names = tuple(c.subject for c in catalogs)
    require_names(names, "subjects")
    if target not in names:
        raise ValueError("target subject is absent")
    if len({(c.dataset, c.classes, c.preprocessing_sha256) for c in catalogs}) != 1:
        raise ValueError("catalogs must share dataset, classes and preprocessing")
    if any(set(c.labels) != set(c.classes) for c in catalogs):
        raise ValueError("every source/target catalog must retain every declared class")
    source = tuple(sorted(name for name in names if name != target))
    inner = tuple(InnerFold(tuple(s for s in source if s != val), val) for val in source)
    return SourceSelection(
        catalogs[0].dataset,
        target,
        source,
        inner,
        tuple(sorted((c.subject, c.sha256) for c in catalogs)),
    )
