"""Three Phase I leakage checks runnable without retraining models."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, cast

from core.config import config_digest, load_toml
from core.splits import grouped_k_fold, leave_one_subject_out
from evaluation.source_bound_controls import verify_current_controls


@dataclass(frozen=True, slots=True)
class LeakageCIReport:
    subject_disjointness_passed: bool
    shuffled_label_passed: bool
    pre_cue_passed: bool
    current_source_controls_passed: bool

    @property
    def passed(self) -> bool:
        return all(asdict(self).values())


def verified_control_summary(
    root: Path, config_name: str, *, flag_key: str, limit_key: str
) -> bool:
    """Recheck historical control records, not merely a saved boolean pass flag."""
    try:
        config = cast(Mapping[str, Any], load_toml(root / "configs" / config_name))
        settings = config["gate_a"]
        payload = json.loads((root / config["output"]["summary"]).read_text("utf-8"))
        expected = {
            (subject, seed) for subject in settings["subjects"] for seed in settings["seeds"]
        }
        observed: set[tuple[int, int]] = set()
        scores: dict[int, list[float]] = defaultdict(list)
        records_root = (root / config["output"]["runs_root"]).resolve()
        for row in payload["runs"]:
            identity = (row["subject"], row["seed"])
            if identity in observed or identity not in expected:
                return False
            path = (root / row["run_record"]).resolve()
            if not path.is_relative_to(records_root):
                return False
            record = json.loads(path.read_text("utf-8"))
            score = float(record["metrics"]["balanced_accuracy"])
            if (
                record["config_sha256"] != config_digest(record["config"])
                or record["config"]["gate_a"] != settings
                or record["seed"] != identity[1]
                or record["config"]["resolved"]["subject"] != identity[0]
                or record["config"]["resolved"]["seed"] != identity[1]
                or not math.isfinite(score)
                or not 0 <= score <= 1
                or score != row["balanced_accuracy"]
            ):
                return False
            scores[identity[0]].append(score)
            observed.add(identity)
        if observed != expected or not scores:
            return False
        subject_means = {str(subject): mean(values) for subject, values in scores.items()}
        overall = mean(subject_means.values())
        return bool(
            payload[flag_key] is True
            and payload[limit_key] == settings[limit_key]
            and payload["balanced_accuracy"]["subject_count"] == len(subject_means)
            and set(payload["balanced_accuracy"]["subject_means"]) == set(subject_means)
            and all(
                math.isclose(
                    payload["balanced_accuracy"]["subject_means"][key], value, abs_tol=1e-12
                )
                for key, value in subject_means.items()
            )
            and math.isclose(payload["balanced_accuracy"]["mean"], overall, abs_tol=1e-12)
            and overall <= settings[limit_key]
        )
    except (OSError, KeyError, TypeError, ValueError):
        return False


def run_leakage_ci(project_root: Path) -> LeakageCIReport:
    subjects = [f"subject_{index:02d}" for index in range(1, 10) for _ in range(3)]
    loso = leave_one_subject_out(subjects)
    grouped = grouped_k_fold(subjects, folds=3)
    disjoint = all(not fold.support_subjects & fold.query_subjects for fold in (*loso, *grouped))
    evidence = verify_current_controls(project_root)
    controls = evidence["controls"]
    shuffled = controls.get("gate_a_shuffle.toml", {}).get("passed") is True
    pre_cue = controls.get("pre_cue_control.toml", {}).get("passed") is True
    current = evidence.get("passed") is True
    return LeakageCIReport(disjoint, shuffled, pre_cue, current)
