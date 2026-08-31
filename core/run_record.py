"""Machine-written, append-safe experiment provenance records."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import config_digest, config_snapshot


@dataclass(frozen=True, slots=True)
class RunRecord:
    config: Mapping[str, Any]
    config_sha256: str
    seed: int
    git_commit: str
    dataset: str
    fold: str
    metrics: Mapping[str, float]
    timestamp_utc: str

    @classmethod
    def create(
        cls,
        *,
        config: Mapping[str, Any],
        seed: int,
        git_commit: str,
        dataset: str,
        fold: str,
        metrics: Mapping[str, float],
    ) -> RunRecord:
        if seed < 0:
            raise ValueError("seed must be non-negative")
        if not git_commit or not dataset or not fold:
            raise ValueError("git_commit, dataset, and fold are required")
        return cls(
            config=config_snapshot(config),
            config_sha256=config_digest(config),
            seed=seed,
            git_commit=git_commit,
            dataset=dataset,
            fold=fold,
            metrics=dict(metrics),
            timestamp_utc=datetime.now(UTC).isoformat(),
        )

    def write_json(self, path: str | Path) -> Path:
        """Atomically write a complete record; partial records never exist."""

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(self), indent=2, sort_keys=True)
        handle, temporary_name = tempfile.mkstemp(
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.write("\n")
            os.replace(temporary_name, output)
        except BaseException:
            with suppress(FileNotFoundError):
                os.unlink(temporary_name)
            raise
        return output
