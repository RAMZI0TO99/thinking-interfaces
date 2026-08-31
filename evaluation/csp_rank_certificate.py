"""Conservative full-numerical-rank shortcut; inconclusive means original MNE.

For a channel-by-sample matrix A and a column subset B, A A.T - B B.T
is positive semidefinite. Thus sigma_min(A) >= sigma_min(B), while
sigma_max(A) <= ||A||_F. A well-separated lower bound can certify the
same full-rank outcome as MNE's eps * channels * sigma_max(A) rule.

This is only for the current CSP wrapper's info=None, uniformly scaled dummy
channel type and no projectors. It is not a claim of physiological independence.
Finite-precision guards are deliberately conservative; no reduced rank is
inferred. No caller may substitute full rank when this check is inconclusive.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import svdvals  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class FullRankCertificate:
    certified: bool
    channels: int
    inspected_columns: int
    sample_minimum_singular_value: float
    sample_lower_bound: float
    global_threshold_upper_bound: float
    safety_factor: float

    @property
    def mne_rank(self) -> dict[str, int] | None:
        return {"mag": self.channels} if self.certified else None


def full_rank_certificate(
    epochs: NDArray[np.floating],
    *,
    sample_columns: int = 2048,
    chunk_trials: int = 32,
) -> FullRankCertificate:
    """Bound the original full-matrix threshold using training data only.

    Small temporary arrays replace neither data nor covariance estimation.
    The original MNE rank=None calculation is required if not certified.
    """
    if epochs.ndim != 3 or min(epochs.shape) < 1 or min(sample_columns, chunk_trials) < 1:
        raise ValueError("rank checking needs nonempty epochs and positive chunk/sample sizes")
    channels = epochs.shape[1]
    columns = epochs.shape[0] * epochs.shape[2]
    count = min(columns, sample_columns)
    indices = np.linspace(0, columns - 1, count, dtype=np.int64)
    sample = np.asarray(
        epochs[indices // epochs.shape[2], :, indices % epochs.shape[2]], dtype=np.float64
    ).T
    if not np.isfinite(sample).all():
        raise ValueError("non-finite CSP data")
    singular = np.asarray(svdvals(sample), dtype=np.float64)
    eps = np.finfo(np.float64).eps
    safety = 64.0
    # Guard numerical error of the small SVD; this is intentionally a loose bound.
    lower = max(0.0, float(singular[-1] - safety * eps * max(sample.shape) * singular[0]))
    squares = []
    for start in range(0, len(epochs), chunk_trials):
        chunk = np.asarray(epochs[start : start + chunk_trials], dtype=np.float64)
        if not np.isfinite(chunk).all():
            raise ValueError("non-finite CSP data")
        squares.append(float(np.einsum("ijk,ijk->", chunk, chunk, dtype=np.float64)))
    total = math.fsum(squares)
    if not math.isfinite(total):
        raise ValueError("CSP norm overflow; full rank cannot be certified")
    # Positive-sum rounding guard. The intended arrays are far below this limit.
    rounding_guard = 8.0 * eps * (epochs.size + 1)
    upper_norm = math.sqrt(total) * (1.0 + rounding_guard)
    upper_threshold = float(channels * eps * upper_norm)
    certified = bool(
        count >= channels
        and rounding_guard < 0.01
        and lower > safety * upper_threshold
        and upper_threshold > 0.0
    )
    return FullRankCertificate(
        certified,
        channels,
        count,
        float(singular[-1]),
        lower,
        upper_threshold,
        safety,
    )
