"""Independent completion/arithmetic check for the separate calibration baseline."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import config_digest


def audit_support_adaptation(
    root: Path,
    *,
    settings: Mapping[str, Any],
    subjects: Sequence[str],
    benchmark_sha256: str,
) -> dict[str, Any]:
    episode = settings["episode"]
    dataset = str(episode["dataset"])
    seeds = episode["seeds"]
    labels = sorted(episode["included_labels"])
    if (
        len(subjects) != len(set(subjects))
        or not subjects
        or not seeds
        or len(seeds) != len(set(seeds))
        or len(labels) < 2
        or len(labels) != len(set(labels))
    ):
        raise ValueError("unique nonempty subject and seed inventories are required")
    expected = {
        f"seed_{seed}/{subject}.json": (seed, subject) for seed in seeds for subject in subjects
    }
    found = {path.relative_to(root).as_posix(): path for path in root.glob("seed_*/*.json")}
    invalid: dict[str, str] = {}
    fingerprints = []
    scores: dict[str, list[float]] = {}
    adaptation_seconds = []
    split_by_subject: dict[str, Any] = {}
    for key in sorted(expected.keys() & found.keys()):
        try:
            raw = found[key].read_bytes()
            payload = json.loads(raw)
            seed, subject = expected[key]
            config = payload["config"]
            if (
                payload["dataset"] != dataset
                or payload["fold"] != subject
                or payload["seed"] != seed
                or config["settings"] != settings
                or config["benchmark_config_sha256"] != benchmark_sha256
                or payload["config_sha256"] != config_digest(config)
                or not payload["git_commit"]
                or datetime.fromisoformat(payload["timestamp_utc"]).tzinfo is None
            ):
                raise ValueError("identity or provenance mismatch")
            split = config["split"]
            if set(split) != {f"{part}_indices_sha256" for part in ("source", "support", "query")}:
                raise ValueError("incomplete split fingerprints")
            for digest in split.values():
                if (
                    not isinstance(digest, str)
                    or len(digest) != 64
                    or len(bytes.fromhex(digest)) != 32
                ):
                    raise ValueError("invalid split fingerprint")
            if subject in split_by_subject and split != split_by_subject[subject]:
                raise ValueError("support/query membership changed across seeds")
            metrics = payload["metrics"]
            if any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in metrics.values()
            ):
                raise ValueError("nonfinite/nonnumeric metrics")
            for flag in (
                "support_adaptation_schema_version",
                "parameters_changed",
                "base_model_unchanged",
                "source_target_disjoint",
                "support_query_disjoint",
            ):
                if metrics[flag] != 1:
                    raise ValueError(f"failed invariant: {flag}")
            if metrics["support_trials"] != episode["shots_per_class"] * len(labels):
                raise ValueError("incorrect support size")
            if metrics["adaptation_steps"] != settings["adaptation"]["steps"]:
                raise ValueError("incorrect adaptation step count")
            cells = [
                [metrics[f"confusion_true_{left}_pred_{right}"] for right in labels]
                for left in labels
            ]
            if any(value < 0 or int(value) != value for row in cells for value in row):
                raise ValueError("invalid confusion counts")
            supports = [metrics[f"class_support_{label}"] for label in labels]
            if any(size <= 0 for size in supports) or [sum(row) for row in cells] != supports:
                raise ValueError("invalid class support")
            query = sum(supports)
            if metrics["query_trials"] != query or metrics["source_trials"] <= 0:
                raise ValueError("incorrect query/source size")
            ba = sum(cells[i][i] / supports[i] for i in range(len(labels))) / len(labels)
            observed = sum(cells[i][i] for i in range(len(labels))) / query
            columns = [sum(row[i] for row in cells) for i in range(len(labels))]
            chance = sum(a * b for a, b in zip(supports, columns, strict=True)) / query**2
            if not math.isclose(
                metrics["balanced_accuracy"], ba, abs_tol=1e-10
            ) or not math.isclose(
                metrics["cohen_kappa"], (observed - chance) / (1 - chance), abs_tol=1e-10
            ):
                raise ValueError("classification arithmetic mismatch")
            if not 0 <= metrics["before_balanced_accuracy"] <= 1:
                raise ValueError("invalid before-adaptation score")
            for timing in ("source_fit_seconds", "adaptation_seconds", "prediction_seconds"):
                if metrics[timing] <= 0:
                    raise ValueError("unmeasured or invalid runtime")
            split_by_subject[subject] = split
            scores.setdefault(subject, []).append(ba)
            adaptation_seconds.append(metrics["adaptation_seconds"])
            fingerprints.append(key + ":" + hashlib.sha256(raw).hexdigest())
        except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError) as error:
            invalid[key] = str(error)
    missing = sorted(expected.keys() - found.keys())
    unexpected = sorted(found.keys() - expected.keys())
    return {
        "complete": not missing and not invalid and not unexpected,
        "expected_records": len(expected),
        "valid_records": len(fingerprints),
        "missing_records": missing,
        "invalid_records": invalid,
        "unexpected_records": unexpected,
        "record_snapshot_sha256": hashlib.sha256("\n".join(fingerprints).encode()).hexdigest(),
        "settings_sha256": config_digest(settings),
        "benchmark_config_sha256": benchmark_sha256,
        "subject_mean_balanced_accuracy": {
            subject: sum(values) / len(values) for subject, values in scores.items()
        },
        "measured_adaptation_seconds": sum(adaptation_seconds),
        "scientific_gate_approval": False,
    }
