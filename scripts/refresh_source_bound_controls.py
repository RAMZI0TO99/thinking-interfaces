"""Run/resume all 45 configured controls without touching historical evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

from core.config import config_digest
from core.provenance import capture_source, source_fingerprint
from core.run_record import RunRecord
from evaluation.source_bound_controls import (
    audit_context,
    build_context,
    expected_units,
    file_digest,
    resolved_config,
    unit_name,
    validate_unit,
)

ROOT = Path(__file__).resolve().parents[1]


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".control-", suffix=".tmp")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def check_unit_inputs(context: dict[str, Any], unit: tuple[str, int, int]) -> None:
    name, subject, _ = unit
    names = (
        [f"data/raw/moabb/MNE-bnci-data/~bci/database/001-2014/A{subject:02d}{part}.mat"
         for part in ("T", "E")]
        if name == "gate_a_shuffle.toml" else
        [f"data/processed/bci_iv_2a/pre_cue_control/subject_{subject:02d}.npz"]
    )
    if any(file_digest(ROOT / path) != context["inputs"][path] for path in names):
        raise ValueError("control input changed during execution")


def prediction_capture(original: Any) -> tuple[Any, list[Any]]:
    captured: list[Any] = []

    def capture(*arguments: Any, **keywords: Any) -> Any:
        prediction = original(*arguments, **keywords)
        captured.append(prediction.copy())
        return prediction

    return capture, captured


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    context = build_context(ROOT)
    initial = audit_context(ROOT, context)
    if args.check_only or initial["passed"]:
        print(json.dumps(initial, indent=2, sort_keys=True))
        return 0 if initial["passed"] else 1
    if initial["invalid_records"] or initial["unexpected_records"]:
        raise ValueError("existing control evidence is invalid; preserve and investigate it")
    provider = importlib.import_module("psutil")
    runtime = context["configuration"]["runtime"]
    if (provider.virtual_memory().available / 1024**3 < runtime["minimum_free_memory_gib"]
            or shutil.disk_usage(ROOT).free / 1024**3 < runtime["minimum_free_disk_gib"]):
        print(json.dumps({"deferred": "resource guard", "training_performed": False}))
        return 2
    # No heavy EEG/model import occurs before the resource guard above.
    import numpy as np

    from core.gpu_cooling import cool_gpu, load_cooling_policy
    from encoder import eegnet_baseline as baseline
    from scripts.diagnose_profile_units import guarded_constructor, make_resource_guard
    from scripts.run_gate_a import load_subject_arrays

    eegnet_constructor = vars(baseline)["EEGNet"]
    key = config_digest(context)
    directory = ROOT / "runs/source_bound_controls" / key
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory.parent / ".refresh.lock"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "context_sha256": key}, stream)
    try:
        source = capture_source(ROOT)
        if source.source_sha256 != context["source_sha256"]:
            raise ValueError("source changed before control training")
        context_path = directory / "context.json"
        if context_path.is_file():
            if config_digest(json.loads(context_path.read_text("utf-8"))) != key:
                raise ValueError("saved control context changed")
        else:
            atomic_json(context_path, context)
        cooling = load_cooling_policy(ROOT / "configs/runtime_limits.toml")
        loaded: tuple[str, int] | None = None
        signals: Any = None
        labels: Any = None
        sessions: Any = None
        model_config = context["model_configuration"]
        for unit in expected_units(context):
            name, subject, seed = unit
            path = directory / unit_name(*unit)
            if path.is_file():
                validate_unit(json.loads(path.read_text("utf-8")), context, unit)
                continue
            if source_fingerprint(ROOT) != context["source_sha256"]:
                raise ValueError("source changed during control refresh")
            check_unit_inputs(context, unit)
            gate = context["specifications"][name]["gate_a"]
            if loaded != (name, subject):
                signals, labels, sessions = load_subject_arrays(gate, subject)
                included = np.isin(labels, gate["included_labels"])
                signals, labels, sessions = signals[included], labels[included], sessions[included]
                loaded = (name, subject)
            training = {**model_config["training"], **gate["training"]}
            model = {**model_config["model"], **gate.get("model", {})}
            split = baseline.make_session_split(
                labels, sessions, train_session=model_config["data"]["train_session"],
                test_session=model_config["data"]["test_session"],
                validation_fraction=training["validation_fraction"], seed=seed,
            )
            classes = sorted(set(labels.tolist()))
            targets = np.asarray([classes.index(label) for label in labels], dtype=np.int64)
            if gate.get("shuffle_development_labels", False):
                targets = baseline.shuffle_development_targets(targets, split, seed=seed)
            guard, resources = make_resource_guard(provider, runtime["stop_below_free_memory_gib"])
            guard()
            cool_gpu(cooling)
            capture_predictions, captured = prediction_capture(baseline._predict)
            started = time.perf_counter()
            with (
                patch.object(baseline, "EEGNet",
                             guarded_constructor(eegnet_constructor, guard)),
                patch.object(baseline, "_predict", capture_predictions),
            ):
                result, trained = baseline.train_eegnet(
                    signals=signals, labels=labels, sessions=sessions,
                    train_session=model_config["data"]["train_session"],
                    test_session=model_config["data"]["test_session"],
                    sampling_rate_hz=gate.get("sampling_rate_hz", model["sampling_rate_hz"]),
                    epochs=training["epochs"], batch_size=training["batch_size"],
                    learning_rate=training["learning_rate"], weight_decay=training["weight_decay"],
                    validation_fraction=training["validation_fraction"],
                    early_stopping_patience=training["early_stopping_patience"],
                    input_scale=training["input_scale"], seed=seed,
                    model_options={key: model[key] for key in ("F1", "D", "drop_prob")},
                    device_name=context["configuration"]["controls"]["device"],
                    shuffle_labels=gate.get("shuffle_development_labels", False),
                )
            elapsed = time.perf_counter() - started
            if len(captured) != 1:
                raise ValueError("actual held-out prediction call was not captured exactly once")
            record = RunRecord.create(
                config=resolved_config(context, unit), seed=seed, git_commit=source.git_commit,
                source_sha256=source.source_sha256, git_dirty=source.git_dirty,
                dataset="BNCI2014-001", fold=f"{Path(name).stem}:subject-{subject}",
                metrics={**result.report.record_metrics(),
                         "training_and_prediction_seconds": elapsed},
            )
            payload = {
                "schema": 1, "context_sha256": key,
                "unit": {"configuration": name, "subject": subject, "seed": seed},
                "record": asdict(record), "result": result.as_dict(), "resources": resources,
                "signal_identity": {"shape": list(signals.shape), "dtype": str(signals.dtype),
                                    "sha256": hashlib.sha256(signals.tobytes()).hexdigest()},
                "input_labels": labels.tolist(), "input_sessions": sessions.tolist(),
                "split": {field: getattr(split, field).tolist()
                          for field in ("train", "validation", "test")},
                "training_targets": targets.tolist(), "query_targets": labels[split.test].tolist(),
                "query_predictions": [classes[index] for index in captured[0].tolist()],
            }
            # Normalize tuple/list representation exactly as it will be read from disk.
            payload = json.loads(json.dumps(payload, allow_nan=False))
            validate_unit(payload, context, unit)
            check_unit_inputs(context, unit)
            if source_fingerprint(ROOT) != context["source_sha256"]:
                raise ValueError("source changed during a control fit; no record written")
            atomic_json(path, payload)
            print(json.dumps({"saved": str(path), "epochs": result.epochs_completed,
                              "balanced_accuracy": result.report.balanced_accuracy,
                              "training_and_prediction_seconds": elapsed}), flush=True)
            del trained
        if config_digest(build_context(ROOT)) != key:
            raise ValueError("control source/input/environment context changed before completion")
        report = audit_context(ROOT, context)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1
    finally:
        if lock.is_file() and json.loads(lock.read_text("utf-8"))["pid"] == os.getpid():
            lock.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
