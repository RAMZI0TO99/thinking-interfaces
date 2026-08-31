"""Three Phase I leakage checks runnable without retraining models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from core.splits import grouped_k_fold, leave_one_subject_out


@dataclass(frozen=True, slots=True)
class LeakageCIReport:
    subject_disjointness_passed: bool
    shuffled_label_passed: bool
    pre_cue_passed: bool

    @property
    def passed(self) -> bool:
        return all(asdict(self).values())


def _summary_flag(path: Path, key: str) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload[key] is True
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return False


def run_leakage_ci(project_root: Path) -> LeakageCIReport:
    subjects = [f"subject_{index:02d}" for index in range(1, 10) for _ in range(3)]
    loso = leave_one_subject_out(subjects)
    grouped = grouped_k_fold(subjects, folds=3)
    disjoint = all(
        not fold.support_subjects & fold.query_subjects for fold in (*loso, *grouped)
    )
    shuffled = _summary_flag(
        project_root / "runs" / "gate_a" / "gate_a_shuffled_label_summary.json",
        "negative_control_passed",
    )
    pre_cue = _summary_flag(
        project_root / "runs" / "pre_cue_control" / "summary.json",
        "control_passed",
    )
    return LeakageCIReport(disjoint, shuffled, pre_cue)
