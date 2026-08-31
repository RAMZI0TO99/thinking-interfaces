"""Benchmark record validation, completeness checks, and table aggregation."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.stats import t  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    dataset: str
    method: str
    mean: float
    standard_deviation: float
    confidence_low: float
    confidence_high: float
    subject_count: int
    record_count: int
    seed_mean_standard_deviation: float
    seed_count: int
    seed_comparison_subject_count: int

    def as_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RecordObservation:
    dataset: str
    method: str
    subject: str
    seed: int
    balanced_accuracy: float


def collect_observations(
    root: Path, *, expected_config_sha256: str | None = None
) -> tuple[RecordObservation, ...]:
    observations: list[RecordObservation] = []
    for path in sorted(root.glob("*/*/seed_*/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if (
                expected_config_sha256 is not None
                and payload.get("config_sha256") != expected_config_sha256
            ):
                continue
            metrics = payload["metrics"]
            if (
                expected_config_sha256 is not None
                and metrics.get("benchmark_schema_version") != 2.0
            ):
                continue
            observations.append(
                RecordObservation(
                    dataset=str(payload["dataset"]),
                    method=path.parts[-3],
                    subject=str(payload["fold"]),
                    seed=int(payload["seed"]),
                    balanced_accuracy=float(metrics["balanced_accuracy"]),
                )
            )
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid benchmark record: {path}") from error
    return tuple(observations)


def aggregate_observations(
    observations: Sequence[RecordObservation], *, confidence_level: float = 0.95
) -> tuple[BenchmarkRow, ...]:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be in (0, 1)")
    grouped: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    by_seed: defaultdict[tuple[str, str, int], dict[str, float]] = defaultdict(dict)
    records: defaultdict[tuple[str, str], int] = defaultdict(int)
    for observation in observations:
        seed_key = (observation.dataset, observation.method, observation.seed)
        if observation.subject in by_seed[seed_key]:
            raise ValueError("duplicate dataset/method/subject/seed observation")
        if (
            not np.isfinite(observation.balanced_accuracy)
            or not 0 <= observation.balanced_accuracy <= 1
        ):
            raise ValueError("balanced accuracy must be finite and in [0, 1]")
        by_seed[seed_key][observation.subject] = observation.balanced_accuracy
        grouped[(observation.dataset, observation.method, observation.subject)].append(
            observation.balanced_accuracy
        )
        records[(observation.dataset, observation.method)] += 1
    method_subjects: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    for (dataset, method, _), values in grouped.items():
        method_subjects[(dataset, method)].append(float(np.mean(values)))
    rows: list[BenchmarkRow] = []
    for (dataset, method), values in sorted(method_subjects.items()):
        seed_groups = [group for (d, m, _), group in by_seed.items() if (d, m) == (dataset, method)]
        common_subjects = set.intersection(*(set(group) for group in seed_groups))
        # Partial grids cannot compare differently populated seed means fairly.
        seed_means = (
            [
                np.mean([group[subject] for subject in sorted(common_subjects)])
                for group in seed_groups
            ]
            if common_subjects
            else []
        )
        seed_sd = (
            float(np.std(seed_means, ddof=1))
            if len(seed_means) > 1 and np.ptp(seed_means) > 0
            else 0.0
        )
        scores = np.asarray(values, dtype=np.float64)
        mean = float(scores.mean())
        if scores.size > 1:
            standard_deviation = float(scores.std(ddof=1))
            critical = float(t.ppf((1.0 + confidence_level) / 2.0, scores.size - 1))
            margin = critical * standard_deviation / np.sqrt(scores.size)
        else:
            standard_deviation = 0.0
            margin = 0.0
        rows.append(
            BenchmarkRow(
                dataset,
                method,
                mean,
                standard_deviation,
                mean - margin,
                mean + margin,
                int(scores.size),
                records[(dataset, method)],
                seed_sd,
                len(seed_groups),
                len(common_subjects),
            )
        )
    return tuple(rows)


def missing_records(
    root: Path,
    *,
    datasets_subjects: Mapping[str, Sequence[str]],
    methods: Sequence[str],
    seeds: Sequence[int],
    expected_config_sha256: str | None = None,
) -> tuple[str, ...]:
    missing: list[str] = []
    for dataset, subjects in datasets_subjects.items():
        for method in methods:
            for seed in seeds:
                for subject in subjects:
                    path = root / dataset / method / f"seed_{seed}" / f"{subject}.json"
                    valid = path.is_file()
                    if valid and expected_config_sha256 is not None:
                        try:
                            payload = json.loads(path.read_text(encoding="utf-8"))
                            valid = bool(
                                payload.get("config_sha256") == expected_config_sha256
                                and payload.get("metrics", {}).get("benchmark_schema_version")
                                == 2.0
                            )
                        except (OSError, AttributeError, json.JSONDecodeError):
                            valid = False
                    if not valid:
                        missing.append(str(path))
    return tuple(missing)


def write_benchmark_csv(rows: Sequence[BenchmarkRow], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp", text=True
    )
    fields = tuple(BenchmarkRow.__dataclass_fields__)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(row.as_dict() for row in rows)
        os.replace(temporary_name, output)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return output
