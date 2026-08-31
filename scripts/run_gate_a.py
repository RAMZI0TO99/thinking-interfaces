"""Run the documented four-seed, nine-subject EEGNet Gate A benchmark."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from core.run_record import RunRecord
from data.moabb_gate_a import apply_common_average_reference, load_reference_subject
from encoder.eegnet_baseline import train_eegnet, write_checkpoint_atomic
from evaluation.aggregate import subject_level_interval

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "gate_a.toml")
    return parser.parse_args()


def load_subject_arrays(
    gate: dict[str, Any], subject: int
) -> tuple[
    np.ndarray[Any, np.dtype[np.float32]],
    np.ndarray[Any, np.dtype[np.str_]],
    np.ndarray[Any, np.dtype[np.str_]],
]:
    source = str(gate.get("source", "artifact"))
    if source == "artifact":
        artifact = PROJECT_ROOT / str(gate["artifact_pattern"]).format(subject=subject)
        with np.load(artifact, allow_pickle=False) as payload:
            return payload["signals"], payload["labels"], payload["sessions"]
    if source == "moabb_reference":
        signals, labels, sessions = load_reference_subject(
            subject,
            project_root=PROJECT_ROOT,
            raw_root=PROJECT_ROOT / "data" / "raw" / "moabb",
            events=tuple(str(event) for event in gate["events"]),
            bandpass_low_hz=float(gate["bandpass_low_hz"]),
            bandpass_high_hz=float(gate["bandpass_high_hz"]),
        )
        if bool(gate.get("common_average_reference", False)):
            signals = apply_common_average_reference(signals)
        return signals, labels, sessions
    raise ValueError(f"unsupported Gate A source: {source}")


def write_json_atomic(payload: object, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return output


def main() -> int:
    args = parse_args()
    model_config = load_toml(PROJECT_ROOT / "configs" / "eegnet.toml")
    gate_config = load_toml(args.config)
    gate = gate_config["gate_a"]
    output = gate_config["output"]
    data = model_config["data"]
    model = model_config["model"]
    gate_model = {**model, **gate.get("model", {})}
    training = {**model_config["training"], **gate.get("training", {})}
    observations: list[tuple[int, float]] = []
    rows: list[dict[str, object]] = []
    total_runs = len(gate["subjects"]) * len(gate["seeds"])
    run_number = 0

    for subject_value in gate["subjects"]:
        subject = int(subject_value)
        signals, labels, sessions = load_subject_arrays(gate, subject)
        included_labels = tuple(str(label) for label in gate.get("included_labels", []))
        if included_labels:
            included = np.isin(labels, included_labels)
            signals = signals[included]
            labels = labels[included]
            sessions = sessions[included]
        for seed_value in gate["seeds"]:
            seed = int(seed_value)
            run_number += 1
            result, trained_model = train_eegnet(
                signals=signals,
                labels=labels,
                sessions=sessions,
                train_session=str(data["train_session"]),
                test_session=str(data["test_session"]),
                sampling_rate_hz=float(
                    gate.get("sampling_rate_hz", gate_model["sampling_rate_hz"])
                ),
                epochs=int(training["epochs"]),
                batch_size=int(training["batch_size"]),
                learning_rate=float(training["learning_rate"]),
                weight_decay=float(training["weight_decay"]),
                validation_fraction=float(training["validation_fraction"]),
                early_stopping_patience=int(training["early_stopping_patience"]),
                input_scale=float(training["input_scale"]),
                seed=seed,
                model_options={
                    "F1": int(gate_model["F1"]),
                    "D": int(gate_model["D"]),
                    "drop_prob": float(gate_model["drop_prob"]),
                },
                shuffle_labels=bool(gate.get("shuffle_development_labels", False)),
            )
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            stem = f"subject_{subject:02d}_seed_{seed}_{stamp}"
            resolved_config = {
                **model_config,
                "gate_a": gate,
                "resolved": {"subject": subject, "seed": seed, "device": result.device},
            }
            record = RunRecord.create(
                config=resolved_config,
                seed=seed,
                git_commit="unversioned-workspace",
                dataset=str(data["dataset"]),
                fold=f"subject-{subject}:session-{data['test_session']}",
                metrics=result.report.record_metrics(),
            )
            runs_root = PROJECT_ROOT / output["runs_root"]
            record_path = record.write_json(runs_root / f"{stem}.run.json")
            checkpoint_path = write_checkpoint_atomic(
                trained_model,
                PROJECT_ROOT / output["checkpoints_root"] / f"{stem}.pt",
                metadata={
                    "config_sha256": record.config_sha256,
                    "subject": subject,
                    "seed": seed,
                    **result.as_dict(),
                },
            )
            score = result.report.balanced_accuracy
            observations.append((subject, score))
            row: dict[str, object] = {
                "subject": subject,
                "seed": seed,
                "balanced_accuracy": score,
                "cohen_kappa": result.report.cohen_kappa,
                "best_epoch": result.best_epoch,
                "epochs_completed": result.epochs_completed,
                "run_record": str(record_path),
                "checkpoint": str(checkpoint_path),
            }
            rows.append(row)
            print(
                json.dumps(
                    {
                        "progress": f"{run_number}/{total_runs}",
                        **row,
                    }
                ),
                flush=True,
            )

    aggregate = subject_level_interval(
        observations, confidence_level=float(gate["confidence_level"])
    )
    summary = {
        "gate": gate.get("gate_name", "A"),
        "attempt": gate.get("attempt", "unspecified"),
        "protocol": gate.get("protocol", "within-subject cross-session EEGNet"),
        "included_labels": list(gate.get("included_labels", [])),
        "shuffle_development_labels": bool(gate.get("shuffle_development_labels", False)),
        "subjects": list(gate["subjects"]),
        "seeds": list(gate["seeds"]),
        "reference_name": gate["reference_name"],
        "reference_status": gate["reference_status"],
        "sign_off_status": "pending_valid_published_reference",
        "balanced_accuracy": aggregate.as_dict(),
        "runs": rows,
    }
    if "reference_score" in gate:
        reference_score = float(gate["reference_score"])
        summary["reference_score"] = reference_score
        summary["difference_from_reference"] = aggregate.mean - reference_score
    if bool(gate.get("shuffle_development_labels", False)):
        maximum = float(gate["negative_control_max_accuracy"])
        summary["negative_control_max_accuracy"] = maximum
        summary["negative_control_passed"] = aggregate.mean <= maximum
    if "control_max_accuracy" in gate:
        maximum = float(gate["control_max_accuracy"])
        passed = aggregate.mean <= maximum
        summary["control_max_accuracy"] = maximum
        summary["control_passed"] = passed
        summary["sign_off_status"] = "passed" if passed else "failed"
    summary_path = write_json_atomic(summary, PROJECT_ROOT / output["summary"])
    print(json.dumps({"summary": str(summary_path), **summary}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
