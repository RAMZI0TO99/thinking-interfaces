"""Window-to-decision latency recording."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class LatencySummary:
    count: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    maximum_ms: float

    def as_dict(self) -> dict[str, int | float]:
        return asdict(self)


class LatencyRecorder:
    def __init__(self) -> None:
        self._values_ms: list[float] = []

    def add_seconds(self, elapsed_s: float) -> None:
        if not np.isfinite(elapsed_s) or elapsed_s < 0:
            raise ValueError("latency must be finite and non-negative")
        self._values_ms.append(elapsed_s * 1000.0)

    def summarize(self) -> LatencySummary:
        if not self._values_ms:
            raise ValueError("cannot summarize an empty latency trace")
        values = np.asarray(self._values_ms, dtype=np.float64)
        return LatencySummary(
            count=int(values.size),
            mean_ms=float(values.mean()),
            p50_ms=float(np.percentile(values, 50)),
            p95_ms=float(np.percentile(values, 95)),
            maximum_ms=float(values.max()),
        )
