"""Reconstruct reference inputs from MAT arrays without the MOABB loader or pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.config import config_digest
from core.provenance import capture_source
from data.runtime import configure_scientific_runtime
from evaluation.moabb_reference_plan import ReferenceUnit
from scripts.run_moabb_reference import ROOT, atomic_json, audit, digest, read_json, resolve_config

CHANNELS = [
    "Fz",
    "FC3",
    "FC1",
    "FCz",
    "FC2",
    "FC4",
    "C5",
    "C3",
    "C1",
    "Cz",
    "C2",
    "C4",
    "C6",
    "CP3",
    "CP1",
    "CPz",
    "CP2",
    "CP4",
    "P1",
    "Pz",
    "P2",
    "POz",
]


def guard_memory(minimum_gib: float) -> None:
    available = importlib.import_module("psutil").virtual_memory().available / 1024**3
    if available < minimum_gib:
        raise RuntimeError("raw-input audit deferred at the existing low-memory stop threshold")


def reconstruct_session(path: Path, settings: dict[str, Any], minimum_gib: float) -> dict[str, Any]:
    """Share pinned MNE/sklearn primitives, not training-side dataset/split orchestration."""
    guard_memory(minimum_gib)
    np = importlib.import_module("numpy")
    mne = importlib.import_module("mne")
    scipy_io = importlib.import_module("scipy.io")
    preprocessing = importlib.import_module("sklearn.preprocessing")
    selection = importlib.import_module("sklearn.model_selection")
    mne.set_log_level("ERROR")
    before = digest(path)
    content = scipy_io.loadmat(path, struct_as_record=False, squeeze_me=True)["data"]
    runs = list(content) if isinstance(content, np.ndarray) else [content]
    epoch_groups = []
    raw_events: list[dict[str, int]] = []
    for raw_run_index, run in enumerate(runs):
        guard_memory(minimum_gib)
        onsets = np.asarray(run.trial).reshape(-1)
        if not onsets.size:
            continue
        labels = np.asarray(run.y).reshape(-1)
        if (
            float(run.fs) != 250.0
            or run.X.ndim != 2
            or run.X.shape[1] != 25
            or onsets.shape != labels.shape
            or not np.array_equal(onsets, onsets.astype(int))
            or not np.all(np.diff(onsets) > 0)
            or not set(labels.tolist()) <= {1, 2, 3, 4}
        ):
            raise ValueError("unexpected BNCI raw run structure or event order")
        selected = np.flatnonzero(np.isin(labels, [1, 2]))
        if not selected.size:
            continue
        # MAT indices are one-based; the published interval is [2, 6] seconds.
        events = np.column_stack(
            (
                onsets[selected].astype(int) - 1,
                np.zeros(len(selected), dtype=int),
                labels[selected].astype(int),
            )
        )
        if events[0, 0] < 0 or events[-1, 0] + 1500 >= len(run.X):
            raise ValueError("reference event window exceeds the raw recording")
        raw = mne.io.RawArray(
            (1e-6 * run.X[:, :22]).T,
            mne.create_info(CHANNELS, 250.0, ch_types="eeg"),
            verbose=False,
        )
        raw.filter(
            l_freq=settings["fmin"],
            h_freq=settings["fmax"],
            method="iir",
            picks="eeg",
            verbose=False,
        )
        epochs = mne.Epochs(
            raw,
            events,
            event_id={"left_hand": 1, "right_hand": 2},
            tmin=2.0,
            tmax=6.0,
            proj=False,
            baseline=None,
            preload=True,
            picks="eeg",
            event_repeated="drop",
            on_missing="ignore",
            verbose=False,
        )
        if len(epochs) != len(events):
            raise ValueError("independent reference epoching dropped an event")
        epoch_groups.append(epochs)
        raw_events.extend(
            {
                "raw_run_index": raw_run_index,
                "event_sample_zero_based": int(event[0]),
                "class_code": int(event[2]),
            }
            for event in events
        )
        del raw
    epochs = mne.concatenate_epochs(epoch_groups, verbose=False)
    targets = (epochs.events[:, 2] - 1).astype(int)
    if epochs.get_data().shape != (144, 22, 1001) or targets.tolist().count(0) != 72:
        raise ValueError("independent session inventory differs from the reference")
    folds = {}
    cv = selection.StratifiedKFold(5, shuffle=True, random_state=42)
    for index, (_, query) in enumerate(cv.split(np.zeros(144), targets)):
        guard_memory(minimum_gib)
        values = epochs[query].copy().resample(settings["resample_hz"]).get_data()
        values = np.array([preprocessing.StandardScaler().fit_transform(trial) for trial in values])
        folds[str(index)] = {
            "query_indices": query.tolist(),
            "transformed_query_shape": list(values.shape),
            "transformed_query_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
        }
    if digest(path) != before:
        raise RuntimeError("raw input changed during reconstruction")
    return {
        "raw_file_sha256": before,
        "raw_events": raw_events,
        "session_targets": targets.tolist(),
        "channel_names": list(epochs.ch_names),
        "native_epoch_shape": list(epochs.get_data().shape),
        "folds": folds,
    }


def compare_input_proof(result: dict[str, Any], proof: dict[str, Any], unit: ReferenceUnit) -> None:
    for key in ("session_targets", "channel_names", "native_epoch_shape"):
        if result[key] != proof[key]:
            raise ValueError(f"independently reconstructed {key} differs")
    fold = proof["folds"][str(unit.fold_index)]
    for key in ("query_indices", "transformed_query_shape", "transformed_query_sha256"):
        if result[key] != fold[key]:
            raise ValueError(f"independently reconstructed {key} differs")
    suffix = "T" if unit.session == "0train" else "E"
    if result["raw_file_sha256"][f"A{unit.subject:02d}{suffix}.mat"] != proof["raw_file_sha256"]:
        raise ValueError("independent reconstruction used a different raw file")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/moabb_reference_evaluation.toml"
    )
    args = parser.parse_args()
    config, plan, environment, output = resolve_config(args.config)
    if Path(sys.prefix).resolve() != (ROOT / environment["environment"]["directory"]).resolve():
        raise ValueError("input reconstruction requires the pinned reference interpreter")
    preflight = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.check_moabb_reference_environment",
            "--config",
            str(ROOT / config["paths"]["environment_config"]),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    receipt_path = Path(json.loads(preflight.stdout)["report"])
    receipt = read_json(receipt_path)
    if receipt["environment_verified"] is not True:
        raise ValueError("input audit requires a verified reference environment")
    # This is read-only input reconstruction, not training: no TensorFlow/model import.
    minimum = environment["runtime"]["stop_below_free_memory_gib"]
    guard_memory(minimum)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = str(environment["runtime"]["intra_op_threads"])
    configure_scientific_runtime(ROOT)
    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit input-audit source before recording scientific evidence")
    integrity = audit(config, plan, environment, output)
    if integrity["invalid_units"] or integrity["unexpected_files"] or integrity["pending_locks"]:
        raise ValueError("reference records require review before input reconstruction")
    proofs: dict[str, Any] = {}
    checked, mismatches = [], {}
    for unit in plan.units:
        relative = f"{unit.key}.json"
        if relative not in integrity["record_files"]:
            continue
        pair = f"subject_{unit.subject:02d}/{unit.session}"
        if pair not in proofs:
            suffix = "T" if unit.session == "0train" else "E"
            path = ROOT / config["paths"]["raw_directory"] / f"A{unit.subject:02d}{suffix}.mat"
            print(json.dumps({"reconstructing": pair}), flush=True)
            proofs[pair] = reconstruct_session(path, config["preprocessing"], minimum)
        payload = read_json(output / relative)
        try:
            compare_input_proof(payload["result"], proofs[pair], unit)
            checked.append(unit.key)
        except ValueError as error:
            mismatches[unit.key] = str(error)
    for relative, expected in integrity["record_files"].items():
        if digest(output / relative) != expected:
            raise RuntimeError("reference record changed during raw-input audit")
    if capture_source(ROOT).source_sha256 != source.source_sha256:
        raise RuntimeError("input audit source changed during reconstruction")
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": asdict(source),
        "environment_receipt": str(receipt_path),
        "environment_receipt_sha256": digest(receipt_path),
        "evaluation_config_sha256": config_digest(config),
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "record_files": integrity["record_files"],
        "expected_fits": len(plan.units),
        "checked_units": checked,
        "mismatches": mismatches,
        "session_proofs": proofs,
        "existing_inputs_match": bool(checked) and not mismatches,
        "complete": integrity["complete"] and len(checked) == len(plan.units) and not mismatches,
        "training_performed": False,
        "scientific_gate_approved": False,
        "scope": (
            "Independent MAT/event/epoch orchestration using the same pinned MNE and "
            "sklearn primitives; not an independent numerical-library implementation "
            "or confound clearance."
        ),
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = ROOT / "runs/moabb_reference/input_audits" / f"{stamp}.json"
    atomic_json(target, report)
    print(
        json.dumps(
            {
                "report": str(target),
                "checked_fits": len(checked),
                "complete": report["complete"],
                "mismatches": mismatches,
            }
        ),
        flush=True,
    )
    return 0 if report["complete"] else 1 if mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
