"""Contract v1 for data, adaptation, decoding, and streaming boundaries.

The local freeze is recorded in configs/contract_freeze.toml. Earlier runs are
not retroactively relabelled as having used a previously announced v1 freeze.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Epoch:
    """One canonical EEG epoch emitted by every dataset loader.

    ``signal`` must be a two-dimensional array-like object in
    ``(channels, samples)`` order. The contract intentionally does not depend
    on NumPy so it can be validated before scientific dependencies are installed.
    """

    signal: Any
    channel_names: tuple[str, ...]
    sampling_rate_hz: float
    subject_id: str
    dataset: str
    event_label: str
    tmin_s: float = 0.0

    def __post_init__(self) -> None:
        shape = getattr(self.signal, "shape", None)
        if shape is None or len(shape) != 2:
            raise ValueError("signal must have shape (channels, samples)")
        if shape[0] != len(self.channel_names):
            raise ValueError("channel_names must match the signal channel dimension")
        if shape[0] < 1 or shape[1] < 1:
            raise ValueError("signal dimensions must be non-empty")
        if len(set(self.channel_names)) != len(self.channel_names):
            raise ValueError("channel names must be unique after canonicalisation")
        if self.sampling_rate_hz <= 0:
            raise ValueError("sampling_rate_hz must be positive")
        if not self.subject_id or not self.dataset or not self.event_label:
            raise ValueError("subject_id, dataset, and event_label are required")


@dataclass(frozen=True, slots=True)
class Split:
    """Support/query split with explicit subject-level leakage protection."""

    support_indices: tuple[int, ...]
    query_indices: tuple[int, ...]
    support_subjects: frozenset[str]
    query_subjects: frozenset[str]

    def __post_init__(self) -> None:
        if not self.support_indices or not self.query_indices:
            raise ValueError("support and query sets must both be non-empty")
        if len(set(self.support_indices)) != len(self.support_indices):
            raise ValueError("support indices must not contain duplicates")
        if len(set(self.query_indices)) != len(self.query_indices):
            raise ValueError("query indices must not contain duplicates")
        if any(index < 0 for index in self.support_indices + self.query_indices):
            raise ValueError("support and query indices must be non-negative")
        if set(self.support_indices) & set(self.query_indices):
            raise ValueError("support and query indices must be disjoint")
        if not self.support_subjects or not self.query_subjects:
            raise ValueError("support and query subjects must both be non-empty")
        if self.support_subjects & self.query_subjects:
            raise ValueError("support and query subjects must be disjoint")


@dataclass(frozen=True, slots=True)
class Episode:
    """Within-target-subject support/query episode.

    The support and query trials belong to one target subject, but their trial
    indices are strictly disjoint.  Source-subject data is carried separately
    by the evaluation harness and must never contain ``subject_id``.
    """

    subject_id: str
    support_indices: tuple[int, ...]
    query_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.subject_id:
            raise ValueError("subject_id is required")
        if not self.support_indices or not self.query_indices:
            raise ValueError("support and query sets must both be non-empty")
        if min(self.support_indices + self.query_indices) < 0:
            raise ValueError("support and query indices must be non-negative")
        if len(set(self.support_indices)) != len(self.support_indices):
            raise ValueError("support indices must not contain duplicates")
        if len(set(self.query_indices)) != len(self.query_indices):
            raise ValueError("query indices must not contain duplicates")
        if set(self.support_indices) & set(self.query_indices):
            raise ValueError("support and query indices must be disjoint")


@runtime_checkable
class Decoder(Protocol):
    """Minimum decoder surface consumed by evaluation and real-time lanes."""

    def fit(self, epochs: Any, labels: Any) -> Decoder:
        """Fit only on training or support data."""

    def predict_proba(self, epochs: Any) -> Any:
        """Return class probabilities without changing model state."""


@runtime_checkable
class Stream(Protocol):
    """Minimum causal sample stream surface."""

    @property
    def sampling_rate_hz(self) -> float:
        """Nominal stream sampling rate."""

    @property
    def channel_names(self) -> tuple[str, ...]:
        """Canonical channel names in stream order."""

    def read(self, max_samples: int) -> Any:
        """Return at most ``max_samples`` newly available samples."""
