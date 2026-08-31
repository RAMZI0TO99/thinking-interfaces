"""Exact reference grid and descriptive aggregation; never scientific gate approval."""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from core.config import config_digest


@dataclass(frozen=True, order=True, slots=True)
class ReferenceUnit:
    model_seed: int
    subject: int
    session: str
    fold_index: int

    def __post_init__(self) -> None:
        if (type(self.model_seed) is not int or not 0 <= self.model_seed < 2**32
                or type(self.subject) is not int or self.subject < 1
                or type(self.fold_index) is not int or self.fold_index < 0
                or self.session not in ("0train", "1test")):
            raise ValueError("invalid reference fold identity")

    @property
    def key(self) -> str:
        return (
            f"seed_{self.model_seed}/subject_{self.subject:02d}/"
            f"{self.session}/fold_{self.fold_index}"
        )


@dataclass(frozen=True, slots=True)
class ReferencePlan:
    reference_seed: int
    repeat_seeds: tuple[int, ...]
    subjects: tuple[int, ...]
    sessions: tuple[str, ...]
    fold_count: int
    split_seed: int
    published_roc_auc: float
    published_sd: float
    confidence_level: float
    config_sha256: str

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> ReferencePlan:
        if set(config) != {"reference", "training", "preprocessing", "paths"}:
            raise ValueError("reference configuration must declare all four sections")
        reference = config["reference"]
        required = {
            "subjects", "sessions", "reference_model_seed", "repeat_model_seeds",
            "split_seed", "fold_count", "published_roc_auc",
            "published_between_subject_session_sd", "confidence_level",
        }
        if not isinstance(reference, Mapping) or set(reference) != required:
            raise ValueError("reference section has missing or unknown fields")
        subjects = reference["subjects"]
        if not isinstance(subjects, list) or any(type(item) is not int for item in subjects):
            raise ValueError("reference subjects must be exact integers")
        if subjects != list(range(1, 10)) or reference["sessions"] != ["0train", "1test"]:
            raise ValueError("full reference requires all nine subjects and both sessions")
        seeds = reference["repeat_model_seeds"]
        if not isinstance(seeds, list) or seeds != [11, 23, 37, 53]:
            raise ValueError("reference repeats must preserve the four declared Gate A seeds")
        if any(type(seed) is not int for seed in seeds):
            raise ValueError("reference seeds must be exact integers")
        for field, value in (("reference_model_seed", 42), ("split_seed", 42), ("fold_count", 5)):
            if type(reference[field]) is not int or reference[field] != value:
                raise ValueError(f"reference {field} must preserve the linked protocol")
        score = float(reference["published_roc_auc"])
        sd = float(reference["published_between_subject_session_sd"])
        confidence = float(reference["confidence_level"])
        if score != 0.7715 or sd != 0.1933 or not 0 < confidence < 1:
            raise ValueError("invalid published reference values or confidence level")
        training = {
            "epochs": 300, "batch_size": 64, "learning_rate": 0.001,
            "validation_split": 0.2, "drop_rate": 0.5, "patience": 75,
            "learning_rate_factor": 0.5, "restore_best_weights": False,
        }
        preprocessing = {
            "fmin": 8.0, "fmax": 32.0, "resample_hz": 128.0,
            "common_average_reference": False, "baseline": "none",
            "epoch_interval": "dataset_default_inclusive",
            "standardization": "upstream_per_epoch_across_channels_at_each_time_sample",
        }
        for section, expected in (("training", training), ("preprocessing", preprocessing)):
            actual = config[section]
            if not isinstance(actual, Mapping) or set(actual) != set(expected):
                raise ValueError(f"reference {section} has missing or unknown fields")
            if any(type(actual[key]) is not type(value) or actual[key] != value
                   for key, value in expected.items()):
                raise ValueError(f"reference {section} differs from the specified protocol")
        paths = config["paths"]
        expected_paths = {"environment_config", "raw_directory", "output_directory"}
        if not isinstance(paths, Mapping) or set(paths) != expected_paths:
            raise ValueError("reference paths have missing or unknown fields")
        if any(not isinstance(value, str) or not value for value in paths.values()):
            raise ValueError("reference paths must be nonempty strings")
        return cls(42, tuple(seeds), tuple(subjects), ("0train", "1test"), 5, 42,
                   score, sd, confidence, config_digest(config))

    @property
    def units(self) -> tuple[ReferenceUnit, ...]:
        return tuple(
            ReferenceUnit(seed, subject, session, fold)
            for seed in (self.reference_seed, *self.repeat_seeds)
            for subject in self.subjects
            for session in self.sessions
            for fold in range(self.fold_count)
        )


def summarize_reference_scores(
    plan: ReferencePlan, observations: Iterable[tuple[ReferenceUnit, float]]
) -> dict[str, Any]:
    """Summarize an exact score grid; callers must separately validate underlying runs."""
    expected = set(plan.units)
    scores: dict[ReferenceUnit, float] = {}
    for unit, score in observations:
        if unit not in expected or unit in scores:
            raise ValueError("unexpected or duplicate reference fold")
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("reference ROC-AUC must be finite and in [0, 1]")
        scores[unit] = float(score)
    if set(scores) != expected:
        raise ValueError("reference summaries require every configured fold, session and seed")
    session_scores = {
        (seed, subject, session): statistics.mean(
            scores[ReferenceUnit(seed, subject, session, fold)] for fold in range(plan.fold_count)
        )
        for seed in (plan.reference_seed, *plan.repeat_seeds)
        for subject in plan.subjects for session in plan.sessions
    }
    by_seed = {}
    for seed in (plan.reference_seed, *plan.repeat_seeds):
        values = [value for (model_seed, _, _), value in session_scores.items()
                  if model_seed == seed]
        by_seed[str(seed)] = {
            "mean_roc_auc": statistics.mean(values),
            "subject_session_sd_ddof1": statistics.stdev(values),
            "subject_session_sd_ddof0": statistics.pstdev(values),
            "subject_session_count": len(values),
            "difference_from_published_mean": statistics.mean(values) - plan.published_roc_auc,
        }
    subject_means = {
        str(subject): statistics.mean(
            session_scores[(seed, subject, session)]
            for seed in plan.repeat_seeds for session in plan.sessions
        )
        for subject in plan.subjects
    }
    # Import only for the final small statistical calculation, not in preflight.
    from evaluation.aggregate import subject_level_interval

    interval = subject_level_interval(
        ((int(subject), value) for subject, value in subject_means.items()),
        confidence_level=plan.confidence_level,
    )
    return {
        "config_sha256": plan.config_sha256,
        "fold_score_grid_complete": True,
        "underlying_run_integrity_verified": False,
        "scientific_gate_approved": False,
        "acceptance_tolerance_adopted": False,
        "fold_count": len(scores),
        "published_mean_roc_auc": plan.published_roc_auc,
        "published_between_subject_session_sd": plan.published_sd,
        "published_sd_is_not_an_acceptance_band": True,
        "per_seed": by_seed,
        "reference_seed": plan.reference_seed,
        "repeat_seeds": list(plan.repeat_seeds),
        "four_seed_subject_interval": interval.as_dict(),
        "four_seed_sd_of_seed_means": statistics.stdev(
            by_seed[str(seed)]["mean_roc_auc"] for seed in plan.repeat_seeds
        ),
        "aggregation": "folds within session; repeat seeds and sessions within subject for CI",
        "sd_note": "Both SD conventions shown; the table's exact ddof is not established here.",
        "subject_session_scores": [
            {"seed": seed, "subject": subject, "session": session, "roc_auc": score}
            for (seed, subject, session), score in session_scores.items()
        ],
    }
