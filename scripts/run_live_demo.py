"""Real-rate LSL -> causal windows -> source-only EEGNet -> gate -> native UI."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
import uuid
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread
from typing import Any, cast

import numpy as np
import torch
from pylsl import local_clock  # type: ignore[import-untyped]

from core.config import config_digest, load_toml
from core.provenance import capture_source
from evaluation.baselines import BraindecodeClassifier, TorchTrainingConfig
from evaluation.benchmark import load_dataset_matrix
from realtime.accumulated_evidence import AccumulatedEvidence
from realtime.confidence_gate import GateDecision
from realtime.interface import GateDrivenInterface, InterfaceFrame
from realtime.live_pipeline import run_live_pipeline
from realtime.lsl import LSLInletStream, make_eeg_outlet


def write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/live_demo.toml")
    parser.add_argument(
        "--hidden-preview",
        action="store_true",
        help="Render and verify the UI without placing a visible window on the desktop",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / args.config))
    source = capture_source(root)
    settings = config["data"]
    training = config["training"]
    stream_settings = config["stream"]
    decision = config["decision"]
    benchmark = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    dataset = benchmark["datasets"][settings["dataset"]]
    # Prefer the configured modern runtime; do not alter execution-policy settings.
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        raise RuntimeError("This native demo requires Windows PowerShell or PowerShell on Windows")
    torch.set_num_threads(int(training["cpu_threads"]))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output_root = root / config["output"]["directory"]
    output = output_root / stamp
    output.mkdir(parents=True)
    matrix = load_dataset_matrix(
        root / dataset["artifact_directory"],
        dataset=settings["dataset"],
        sampling_rate_hz=dataset["sampling_rate_hz"],
        absolute_peak_volts=dataset["artifact_threshold_volts"],
    )
    held_out = str(settings["held_out_subject"])
    source_indices = np.flatnonzero(matrix.subjects != held_out)
    target_indices = np.flatnonzero(matrix.subjects == held_out)
    if not source_indices.size or not target_indices.size:
        raise ValueError("source and held-out subjects must both exist")
    class_names = tuple(sorted(set(matrix.labels.tolist())))
    per_class = int(settings["query_trials_per_class"])
    selected = []
    for label in class_names:
        matching = target_indices[matrix.labels[target_indices] == label]
        if matching.size < per_class:
            raise ValueError("insufficient held-out trials for the configured balanced replay")
        selected.extend(matching[:per_class].tolist())
    query_indices = np.asarray(sorted(selected), dtype=np.int64)
    source_subjects = sorted(set(matrix.subjects[source_indices].tolist()))
    if held_out in source_subjects or np.intersect1d(source_indices, query_indices).size:
        raise ValueError("source/target split is not disjoint")
    labels = {label: index for index, label in enumerate(class_names)}
    targets = np.asarray([labels[label] for label in matrix.labels], dtype=np.int64)
    print(
        f"Training source-only EEGNet on {len(source_subjects)} subjects; "
        f"replay subject {held_out} is held out.",
        flush=True,
    )
    fit_started = time.perf_counter()
    decoder = BraindecodeClassifier(
        "eegnet",
        channels=matrix.signals.shape[1],
        classes=len(class_names),
        samples=matrix.signals.shape[2],
        sampling_rate_hz=matrix.sampling_rate_hz,
        seed=int(training["seed"]),
        training=TorchTrainingConfig(
            epochs=int(training["epochs"]),
            batch_size=int(training["batch_size"]),
            learning_rate=float(training["learning_rate"]),
            weight_decay=float(training["weight_decay"]),
            input_scale=float(training["input_scale"]),
            device=str(training["device"]),
        ),
    ).fit(matrix.signals[source_indices], targets[source_indices])
    fit_seconds = time.perf_counter() - fit_started
    signal = np.concatenate([matrix.signals[index] for index in query_indices], axis=1)
    window = round(stream_settings["window_seconds"] * matrix.sampling_rate_hz)
    stride = round(stream_settings["stride_seconds"] * matrix.sampling_rate_hz)
    if window != matrix.signals.shape[2] or stride != window:
        raise ValueError(
            "this saved-epoch demo requires one non-overlapping model-sized window per trial"
        )
    expected_digest = hashlib.sha256(np.ascontiguousarray(signal.T).tobytes()).hexdigest()
    interface = GateDrivenInterface(target="waiting for the first complete window")
    neutral = GateDecision("neutral", 0.0, True, None)
    initial_frame = interface.update(
        neutral, AccumulatedEvidence(required_consecutive=1).update(neutral), latency_ms=0
    )
    state_path = output / "state.json"
    state: dict[str, Any] = {
        "subject": held_out,
        "interface": config["interface"],
        "class_labels": class_names,
        "confidence_threshold": decision["confidence_threshold"],
        "required_consecutive": decision["required_consecutive"],
        "sequence": -1,
        "frame": asdict(initial_frame),
        "received_samples": 0,
        "total_samples": int(signal.shape[1]),
        "status": "starting",
    }
    write_json(state_path, state)
    command = [
        powershell,
        "-NoProfile",
        "-WindowStyle",
        "Hidden",
        "-File",
        str(root / "scripts" / "show_live_demo.ps1"),
        "-StatePath",
        str(state_path),
        "-OutputDirectory",
        str(output),
    ]
    if args.hidden_preview:
        command.append("-HiddenPreview")
    ui_log_path = output / "interface.log"
    ui_log = ui_log_path.open("w", encoding="utf-8")
    ui = subprocess.Popen(command, cwd=root, stdout=ui_log, stderr=subprocess.STDOUT)
    name = f"ThinkingInterfacesLive-{uuid.uuid4()}"
    outlet = make_eeg_outlet(matrix.channel_names, matrix.sampling_rate_hz, name=name)
    stop = Event()
    sender_errors: list[str] = []
    inlet: LSLInletStream | None = None
    worker: Thread | None = None
    rendered_frames: list[dict[str, Any]] = []
    try:
        inlet = LSLInletStream.resolve(name, timeout_s=10)
        if (
            inlet.channel_names != matrix.channel_names
            or inlet.sampling_rate_hz != matrix.sampling_rate_hz
        ):
            raise ValueError("LSL channel order or sampling rate changed")

        def send() -> None:
            try:
                beginning = local_clock() + float(stream_settings["startup_seconds"])
                for index in range(signal.shape[1]):
                    deadline = beginning + index / matrix.sampling_rate_hz
                    if stop.wait(max(0.0, deadline - local_clock())):
                        return
                    outlet.push_sample(signal[:, index].tolist(), deadline, pushthrough=True)
            except Exception as error:
                sender_errors.append(str(error))

        def show_frame(sequence: int, received: int, frame: InterfaceFrame) -> None:
            if ui.poll() is not None:
                raise RuntimeError("native interface closed before the replay completed")
            displayed = {**asdict(frame), "target": str(matrix.labels[query_indices[sequence]])}
            rendered_frames.append(displayed)
            state.update(
                sequence=sequence, received_samples=received, frame=displayed, status="streaming"
            )
            write_json(state_path, state)
            print(
                f"Live window {sequence + 1}/{len(query_indices)}: "
                f"{frame.decision_state}, confidence {frame.confidence:.1%}",
                flush=True,
            )

        worker = Thread(target=send, daemon=True)
        worker.start()
        result = run_live_pipeline(
            inlet,
            decoder,
            class_names,
            interface,
            total_samples=signal.shape[1],
            window_samples=window,
            stride_samples=stride,
            chunk_samples=round(stream_settings["chunk_seconds"] * matrix.sampling_rate_hz),
            confidence_threshold=decision["confidence_threshold"],
            required_consecutive=decision["required_consecutive"],
            timeout_s=signal.shape[1] / matrix.sampling_rate_hz
            + stream_settings["timeout_extra_seconds"],
            on_frame=show_frame,
        )
        worker.join(timeout=1)
        if worker.is_alive() or sender_errors or result.received_sample_sha256 != expected_digest:
            raise RuntimeError("sender failed or replayed samples differ from the input")
        state["status"] = "complete"
        write_json(state_path, state)
        if ui.wait(timeout=20) != 0:
            raise RuntimeError(
                "native interface did not finish successfully; inspect its local log"
            )
        receipt_path = output / "interface_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        expected_sequences = list(range(len(query_indices)))
        if (
            not receipt["completed"]
            or receipt["error"]
            or receipt["sequences"] != expected_sequences
        ):
            raise RuntimeError("not every decoded window was rendered by the native interface")
        expected_duration = (signal.shape[1] - 1) / matrix.sampling_rate_hz
        drift = result.wall_seconds - expected_duration
        passed = abs(drift) <= stream_settings["maximum_wall_drift_seconds"]
        report = {
            "passed": passed,
            "source": asdict(source),
            "config": config,
            "config_sha256": config_digest(config),
            "benchmark_config_sha256": config_digest(benchmark),
            "held_out_subject": held_out,
            "source_subjects": source_subjects,
            "source_trials": int(source_indices.size),
            "support_trials": 0,
            "query_indices": query_indices.tolist(),
            "query_class_counts": {label: per_class for label in class_names},
            "source_query_disjoint": True,
            "fit_seconds": fit_seconds,
            "sample_sha256": expected_digest,
            "expected_samples": int(signal.shape[1]),
            "expected_wall_seconds": expected_duration,
            "wall_drift_seconds": drift,
            "interface_all_frames_rendered": True,
            "rendered_frames": rendered_frames,
            "interface_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "preview_sha256": {
                name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                for name in ("initial.png", "final.png")
            },
            "stream": asdict(result),
            "limitations": [
                "Saved, offline-preprocessed Profile A epochs replayed at nominal rate; "
                "not online raw-EEG filtering.",
                "Processing latency covers window copy, prediction and decision logic; "
                "excludes window acquisition, IPC and native paint latency.",
                "Gate A unsigned; no research or clinical claim.",
            ],
        }
        report_path = output / "result.json"
        write_json(report_path, report)
        write_json(
            output_root / "latest.json",
            {
                "result": report_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            },
        )
        print(
            json.dumps(
                {
                    "passed": passed,
                    "received_samples": result.received_samples,
                    "frames": len(result.frames),
                    "report": str(report_path),
                },
                indent=2,
            )
        )
        return 0 if passed else 1
    except BaseException as error:
        state.update(status="failed", error=str(error))
        write_json(state_path, state)
        raise
    finally:
        stop.set()
        if worker is not None:
            worker.join(timeout=2)
        if inlet is not None:
            inlet.close()
        if ui.poll() is None:
            try:
                ui.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ui.terminate()
                ui.wait(timeout=5)
        ui_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
