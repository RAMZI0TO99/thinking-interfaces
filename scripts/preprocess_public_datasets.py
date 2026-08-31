from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import load_toml
from data.runtime import configure_scientific_runtime

configure_scientific_runtime()

from moabb.datasets import Cho2017  # type: ignore[import-untyped]  # noqa: E402

from data.cho2017 import configure_local_cache as configure_cho  # noqa: E402
from data.mmidb import (  # noqa: E402
    drop_incomplete_motor_annotations,
    load_left_right_fist_raws,
)
from data.profile_a import ProfileAConfig, save_epoch_artifact  # noqa: E402
from data.unified import preprocess_raw_runs_profile_a  # noqa: E402


def profile_a_config(project_root: Path) -> ProfileAConfig:
    root = cast(Mapping[str, Any], load_toml(project_root / "configs" / "base.toml"))
    preprocessing = cast(Mapping[str, Any], root["preprocessing"])
    values = cast(Mapping[str, Any], preprocessing["profile_a"])
    return ProfileAConfig(
        bandpass_low_hz=float(values["bandpass_low_hz"]),
        bandpass_high_hz=float(values["bandpass_high_hz"]),
        resample_hz=float(values["resample_hz"]),
        baseline_duration_s=float(values["pre_cue_s"]),
        epoch_duration_s=float(values["epoch_duration_s"]),
        reference=str(values["reference"]),
    )


def preprocess_cho(project_root: Path, subject: int) -> dict[str, object]:
    raw_root = project_root / "data" / "raw" / "moabb" / "cho2017"
    configure_cho(project_root, raw_root)
    dataset = Cho2017()
    data = dataset.get_data(subjects=[subject], n_jobs=1)[subject]
    runs = [
        (str(session), str(run), raw)
        for session, session_runs in data.items()
        for run, raw in session_runs.items()
    ]
    artifact = preprocess_raw_runs_profile_a(
        runs,
        event_id=dataset.event_id,
        label_map={label: label for label in dataset.event_id},
        config=profile_a_config(project_root),
    )
    output = (
        project_root
        / "data"
        / "processed"
        / "cho2017"
        / "profile_a"
        / f"subject_{subject:02d}.npz"
    )
    save_epoch_artifact(
        output,
        signals=artifact.signals,
        labels=artifact.labels,
        sessions=artifact.sessions,
        runs=artifact.runs,
        trial_indices=artifact.trial_indices,
        channel_names=artifact.channel_names,
    )
    return {
        "dataset": "cho2017",
        "subject": subject,
        "shape": list(artifact.signals.shape),
        "class_counts": artifact.class_counts,
        "output": str(output),
    }


def preprocess_mmidb(project_root: Path, subject: int) -> dict[str, object]:
    source_runs = load_left_right_fist_raws(subject, project_root / "data" / "raw" / "mmidb")
    preprocessing = profile_a_config(project_root)
    dropped = 0
    runs = []
    for source, raw in source_runs:
        sanitized, run_dropped = drop_incomplete_motor_annotations(
            raw,
            baseline_s=preprocessing.baseline_duration_s,
            epoch_s=preprocessing.epoch_duration_s,
        )
        dropped += run_dropped
        runs.append(("0", source.stem[-2:], sanitized))
    artifact = preprocess_raw_runs_profile_a(
        runs,
        event_id={"T1": 2, "T2": 3},
        label_map={"T1": "left_fist", "T2": "right_fist"},
        config=preprocessing,
    )
    output = (
        project_root
        / "data"
        / "processed"
        / "mmidb"
        / "profile_a"
        / f"subject_{subject:03d}.npz"
    )
    save_epoch_artifact(
        output,
        signals=artifact.signals,
        labels=artifact.labels,
        sessions=artifact.sessions,
        runs=artifact.runs,
        trial_indices=artifact.trial_indices,
        channel_names=artifact.channel_names,
    )
    return {
        "dataset": "mmidb",
        "subject": subject,
        "shape": list(artifact.signals.shape),
        "class_counts": artifact.class_counts,
        "dropped_incomplete_annotations": dropped,
        "output": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess public Phase I datasets")
    parser.add_argument("dataset", choices=("cho2017", "mmidb"))
    parser.add_argument("subjects", nargs="+", type=int)
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    function = preprocess_cho if args.dataset == "cho2017" else preprocess_mmidb
    for subject in args.subjects:
        print(json.dumps(function(project_root, subject), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
