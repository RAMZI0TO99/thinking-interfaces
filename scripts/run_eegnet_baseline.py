"""Run the session-held-out Subject 1 EEGNet baseline."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from core.provenance import capture_source
from core.run_record import RunRecord
from encoder.eegnet_baseline import train_eegnet, write_checkpoint_atomic, write_result_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs" / "eegnet.toml")
    parser.add_argument(
        "--smoke", action="store_true", help="Run two epochs without saving a checkpoint"
    )
    parser.add_argument("--device", choices=("cpu", "cuda"), default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = capture_source(PROJECT_ROOT)
    with args.config.open("rb") as stream:
        config: dict[str, Any] = tomllib.load(stream)
    data_config = config["data"]
    model_config = config["model"]
    training_config = config["training"]
    output_config = config["output"]
    artifact = PROJECT_ROOT / data_config["artifact"]
    with np.load(artifact, allow_pickle=False) as payload:
        signals = payload["signals"]
        labels = payload["labels"]
        sessions = payload["sessions"]

    epochs = 2 if args.smoke else int(training_config["epochs"])
    model_options = {
        "F1": int(model_config["F1"]),
        "D": int(model_config["D"]),
        "drop_prob": float(model_config["drop_prob"]),
    }
    result, model = train_eegnet(
        signals=signals,
        labels=labels,
        sessions=sessions,
        train_session=str(data_config["train_session"]),
        test_session=str(data_config["test_session"]),
        sampling_rate_hz=float(model_config["sampling_rate_hz"]),
        epochs=epochs,
        batch_size=int(training_config["batch_size"]),
        learning_rate=float(training_config["learning_rate"]),
        weight_decay=float(training_config["weight_decay"]),
        validation_fraction=float(training_config["validation_fraction"]),
        early_stopping_patience=int(training_config["early_stopping_patience"]),
        input_scale=float(training_config["input_scale"]),
        seed=int(training_config["seed"]),
        model_options=model_options,
        device_name=args.device,
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    mode = "smoke" if args.smoke else "train"
    stem = f"subject_01_seed_{training_config['seed']}_{mode}_{stamp}"
    runs_root = PROJECT_ROOT / output_config["runs_root"]
    result_path = write_result_json(result, runs_root / f"{stem}.result.json")
    run_config = dict(config)
    run_config["resolved"] = {"epochs": epochs, "mode": mode, "device": result.device}
    record = RunRecord.create(
        config=run_config,
        seed=int(training_config["seed"]),
        git_commit=source.git_commit,
        source_sha256=source.source_sha256,
        git_dirty=source.git_dirty,
        dataset=str(data_config["dataset"]),
        fold=f"subject-{data_config['subject']}:session-{data_config['test_session']}",
        metrics=result.report.record_metrics(),
    )
    record_path = record.write_json(runs_root / f"{stem}.run.json")
    checkpoint_path: Path | None = None
    if not args.smoke:
        checkpoint_path = write_checkpoint_atomic(
            model,
            PROJECT_ROOT / output_config["checkpoints_root"] / f"{stem}.pt",
            metadata={"config_sha256": record.config_sha256, **result.as_dict()},
        )
    print(
        json.dumps(
            {
                "result": str(result_path),
                "run_record": str(record_path),
                "checkpoint": str(checkpoint_path) if checkpoint_path else None,
                **result.as_dict(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
