"""Run or verify the proposed 36-fit no-future EEGNet matched diagnostic.

The historical pre-cue preset and Gate A records are never written by this script.
The default run is supervised; --check-only recomputes every raw no-future input
and verifies already saved diagnostic records without fitting a model.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

from core.config import config_digest
from core.provenance import capture_source, source_fingerprint
from core.run_record import RunRecord
from evaluation.no_future_matched_control import (
    ARTIFACT_PATTERN,
    AUDIT_RELATIVE,
    DIAGNOSTIC_ID,
    DIAGNOSTIC_NAME,
    RUNS_RELATIVE,
    RUNTIME,
    SUBJECTS,
    audit_context,
    build_context,
    ensure_run_namespace,
    expected_units,
    quality_identity,
    validate_matched_unit,
    verify_quality_identity,
    verify_subject_raw,
)
from evaluation.source_bound_controls import (
    file_digest,
    resolved_config,
    unit_name,
)
from scripts.refresh_source_bound_controls import prediction_capture

ROOT = Path(__file__).resolve().parents[1]
LOCK_RELATIVE = f"{RUNS_RELATIVE}/.run.lock"
WRITER_TIMEOUT_SECONDS = 1800
POLL_SECONDS = 2.0
GIB = 1024**3


def _safe_output_path(root: Path, path: Path) -> None:
    """Check every existing output ancestor and the destination for aliases."""

    directory = ensure_run_namespace(root, path.parent.name)
    if path.parent.absolute() != directory.absolute():
        raise ValueError("matched-control evidence must remain in its context directory")
    if (path.exists() or path.is_symlink()) and (
        not path.is_file() or path.is_symlink() or path.resolve() != path.absolute()
    ):
        raise ValueError("matched-control evidence path aliases another location")


def publish_json(root: Path, path: Path, payload: dict[str, Any]) -> None:
    """Publish exact bytes once, rechecking the output path before the hard link."""

    _safe_output_path(root, path)
    contents = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).replace("\n", os.linesep).encode("utf-8")
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".matched-", suffix=".tmp")
    temporary = Path(name)
    identity: tuple[int, int] | None = None
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        info = temporary.stat()
        identity = (info.st_dev, info.st_ino)
        _safe_output_path(root, path)  # Immediately before the no-clobber hard link.
        if (
            not temporary.is_file() or temporary.is_symlink()
            or temporary.resolve() != temporary.absolute()
            or identity != (temporary.stat().st_dev, temporary.stat().st_ino)
        ):
            raise ValueError("matched-control temporary file changed before publication")
        try:
            os.link(temporary, path)
        except FileExistsError:
            _safe_output_path(root, path)
            if path.read_bytes() != contents:
                raise ValueError(f"existing matched-control evidence differs: {path}") from None
    finally:
        if temporary.is_file() and not temporary.is_symlink():
            info = temporary.stat()
            if (
                temporary.resolve() == temporary.absolute()
                and identity == (info.st_dev, info.st_ino)
            ):
                temporary.unlink()


def resource_snapshot(root: Path) -> dict[str, float]:
    provider = importlib.import_module("psutil")
    return {
        "available_ram_gib": provider.virtual_memory().available / GIB,
        "free_disk_gib": shutil.disk_usage(root).free / GIB,
    }


def startup_guard(root: Path) -> dict[str, float]:
    snapshot = resource_snapshot(root)
    if (
        snapshot["available_ram_gib"] < RUNTIME["minimum_free_memory_gib"]
        or snapshot["free_disk_gib"] < RUNTIME["minimum_free_disk_gib"]
    ):
        raise RuntimeError(
            "proposed matched control startup guard failed: "
            f"RAM {snapshot['available_ram_gib']:.3f}/10 GiB, "
            f"disk {snapshot['free_disk_gib']:.3f}/20 GiB"
        )
    return snapshot


def active_guard(root: Path) -> dict[str, float]:
    snapshot = resource_snapshot(root)
    if (
        snapshot["available_ram_gib"] < RUNTIME["stop_below_free_memory_gib"]
        or snapshot["free_disk_gib"] < RUNTIME["minimum_free_disk_gib"]
    ):
        raise RuntimeError(
            "proposed matched control active resource guard failed: "
            f"RAM {snapshot['available_ram_gib']:.3f}/4 GiB, "
            f"disk {snapshot['free_disk_gib']:.3f}/20 GiB"
        )
    return snapshot


def run_writer_check(root: Path) -> str:
    """Require the writer's all-nine raw recomputation before any fit."""

    script = root / "scripts/preprocess_pre_cue_no_future_v1.py"
    before = source_fingerprint(root)
    command = [
        sys.executable, "-m", "scripts.preprocess_pre_cue_no_future_v1",
        "--subjects", *(str(subject) for subject in SUBJECTS), "--check-only",
    ]
    result = subprocess.run(
        command, cwd=root, capture_output=True, check=False,
        timeout=WRITER_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace")[-2000:]
        raise RuntimeError(f"writer all-nine raw --check-only failed: {detail}")
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != len(SUBJECTS):
        raise ValueError("writer raw check did not report all nine subjects")
    for subject, row in zip(SUBJECTS, rows, strict=True):
        expected_artifact = root / ARTIFACT_PATTERN.format(subject=subject)
        if (
            row.get("subject") != subject
            or row.get("status") != "verified_existing"
            or row.get("artifact") != str(expected_artifact)
            or row.get("manifest") != str(expected_artifact.with_suffix(".manifest.json"))
            or row.get("artifact_sha256") != file_digest(expected_artifact)
        ):
            raise ValueError("writer raw check output differs from the proposed artifacts")
    if source_fingerprint(root) != before or not script.is_file():
        raise ValueError("source changed during the all-nine raw recomputation")
    return hashlib.sha256(result.stdout).hexdigest()


def check_subject_inputs(root: Path, context: dict[str, Any], subject: int) -> None:
    verify_subject_raw(root, context, subject)
    identity = context["subject_inputs"][str(subject)]
    audit = root / AUDIT_RELATIVE
    if (
        audit.is_symlink() or audit.resolve() != audit.absolute()
        or file_digest(audit) != context["inputs"][AUDIT_RELATIVE]
    ):
        raise ValueError("no-future audit receipt changed during execution")
    for relative_key, digest_key in (
        ("artifact_relative", "artifact_sha256"),
        ("manifest_relative", "manifest_sha256"),
    ):
        relative = identity[relative_key]
        path = root / relative
        if path.is_symlink() or path.resolve() != path.absolute():
            raise ValueError("no-future control input path aliases another location")
        if file_digest(path) != identity[digest_key]:
            raise ValueError("no-future control input changed during execution")


def _load_subject(root: Path, context: dict[str, Any], subject: int) -> tuple[Any, Any, Any]:
    import numpy as np

    check_subject_inputs(root, context, subject)
    artifact = root / ARTIFACT_PATTERN.format(subject=subject)
    with np.load(artifact, allow_pickle=False) as data:
        signals, labels, sessions = data["signals"], data["labels"], data["sessions"]
    identity = context["subject_inputs"][str(subject)]
    if (
        hashlib.sha256(signals.tobytes(order="C")).hexdigest() != identity["signal_sha256"]
        or labels.tolist() != identity["labels"]
        or sessions.tolist() != identity["sessions"]
    ):
        raise ValueError("loaded no-future signals differ from the pinned NPZ identity")
    return signals, labels, sessions


def _lock_record(root: Path, key: str, writer_check_sha256: str) -> bytes:
    return (json.dumps({
        "kind": DIAGNOSTIC_ID,
        "parent_pid": os.getpid(),
        "context_sha256": key,
        "writer_check_stdout_sha256": writer_check_sha256,
        "source_sha256": source_fingerprint(root),
        "quality_status_sha256": quality_identity(root)["status_sha256"],
    }, sort_keys=True) + "\n").encode("utf-8")


def _stop_owned_worker(process: subprocess.Popen[bytes]) -> None:
    provider = importlib.import_module("psutil")
    try:
        owned = provider.Process(process.pid)
        children = owned.children(recursive=True)
        for child in children:
            child.terminate()
        owned.terminate()
        provider.wait_procs([*children, owned], timeout=5)
        for child in [*children, owned]:
            if child.is_running():
                child.kill()
    except provider.NoSuchProcess:
        pass
    process.wait(timeout=10)


def supervise(
    root: Path, context: dict[str, Any], writer_check_sha256: str, *, started_at: float
) -> int:
    """Own only the spawned worker and enforce a 120-minute wall/resource cap."""

    startup_guard(root)
    verify_quality_identity(root, context)
    key = config_digest(context)
    lock = root / LOCK_RELATIVE
    ensure_run_namespace(root, create=True)
    if (lock.exists() or lock.is_symlink()) and (
        lock.is_symlink() or lock.resolve() != lock.absolute()
    ):
        raise ValueError("matched-control lock path aliases another location")
    content = _lock_record(root, key, writer_check_sha256)
    ensure_run_namespace(root)
    with lock.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    process: subprocess.Popen[bytes] | None = None
    try:
        verify_quality_identity(root, context)
        process = subprocess.Popen(
            [sys.executable, "-m", "scripts.run_no_future_matched_control",
             "--worker", "--expected-key", key,
             "--writer-check-sha", writer_check_sha256],
            cwd=root,
        )
        while process.poll() is None:
            if time.monotonic() - started_at >= RUNTIME["maximum_wall_seconds"]:
                _stop_owned_worker(process)
                raise RuntimeError("proposed matched control stopped at the 120-minute wall cap")
            try:
                active_guard(root)
            except RuntimeError:
                _stop_owned_worker(process)
                raise
            time.sleep(POLL_SECONDS)
        return process.returncode
    finally:
        if process is not None and process.poll() is None:
            _stop_owned_worker(process)
        ensure_run_namespace(root)
        if (
            lock.is_file() and not lock.is_symlink()
            and lock.resolve() == lock.absolute() and lock.read_bytes() == content
        ):
            lock.unlink()


def _supervisor_ancestors(provider: Any) -> set[int]:
    """This process and every ancestor, so launcher shims cannot break ownership.

    The project virtual environment's ``python.exe`` is a launcher that can
    insert a trampoline process between a supervisor and its spawned worker,
    so a direct ``os.getppid()`` comparison rejects legitimate workers here.
    Requiring the lock's supervisor pid to appear anywhere on the worker's
    ancestor chain preserves the ownership guarantee through any depth.
    """
    chain: set[int] = set()
    process: Any = None
    try:
        process = provider.Process(os.getpid())
        while process is not None and process.pid not in chain:
            chain.add(process.pid)
            process = process.parent()
    except provider.Error:
        pass
    return chain


def execute_worker(root: Path, expected_key: str, writer_check_sha256: str) -> int:
    provider = importlib.import_module("psutil")
    lock = root / LOCK_RELATIVE
    ensure_run_namespace(root)
    if not lock.is_file() or lock.is_symlink() or lock.resolve() != lock.absolute():
        raise ValueError("supervisor lock is required for a matched-control worker")
    owner = json.loads(lock.read_bytes())
    if (
        owner.get("kind") != DIAGNOSTIC_ID
        or owner.get("parent_pid") not in _supervisor_ancestors(provider)
        or owner.get("context_sha256") != expected_key
        or owner.get("writer_check_stdout_sha256") != writer_check_sha256
        or owner.get("source_sha256") != source_fingerprint(root)
        or owner.get("quality_status_sha256") != quality_identity(root)["status_sha256"]
    ):
        raise ValueError("matched-control worker does not belong to this supervisor")
    startup_guard(root)
    context = build_context(root, writer_check_sha256)
    verify_quality_identity(root, context)
    key = config_digest(context)
    if key != expected_key:
        raise ValueError("matched-control context changed before supervised execution")
    initial = audit_context(root, context)
    if initial["invalid_records"] or initial["unexpected_records"]:
        raise ValueError("existing matched-control evidence is invalid; preserve it")
    if initial["passed"]:
        print(json.dumps(initial, indent=2, sort_keys=True), flush=True)
        return 0
    # No model/torch import occurs before source and startup-resource admission.
    import numpy as np
    import torch

    from core.gpu_cooling import cool_gpu, load_cooling_policy
    from encoder import eegnet_baseline as baseline
    from scripts.diagnose_profile_units import guarded_constructor, make_resource_guard

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the matched EEGNet control")
    source = capture_source(root)
    if source.source_sha256 != context["source_sha256"] or type(source.git_dirty) is not bool:
        raise ValueError("exact source/Git identity changed before matched-control fits")
    directory = ensure_run_namespace(root, key, create=True)
    publish_json(root, directory / "context.json", context)
    cooling = load_cooling_policy(root / "configs/runtime_limits.toml")
    constructor = vars(baseline)["EEGNet"]
    model_config = context["model_configuration"]
    gate = context["specifications"][DIAGNOSTIC_NAME]["gate_a"]
    loaded_subject: int | None = None
    signals: Any = None
    labels: Any = None
    sessions: Any = None
    for unit in expected_units(context):
        _, subject, seed = unit
        path = directory / unit_name(*unit)
        if path.is_file():
            validate_matched_unit(json.loads(path.read_bytes()), context, unit)
            continue
        active_guard(root)
        if not provider.pid_exists(os.getppid()):
            raise RuntimeError("matched-control supervisor ended")
        if source_fingerprint(root) != context["source_sha256"]:
            raise ValueError("source changed during matched-control run")
        verify_quality_identity(root, context)
        check_subject_inputs(root, context, subject)
        if loaded_subject != subject:
            signals, labels, sessions = _load_subject(root, context, subject)
            loaded_subject = subject
        training = {**model_config["training"], **gate["training"]}
        model = {**model_config["model"], **gate.get("model", {})}
        split = baseline.make_session_split(
            labels, sessions,
            train_session=model_config["data"]["train_session"],
            test_session=model_config["data"]["test_session"],
            validation_fraction=training["validation_fraction"], seed=seed,
        )
        classes = sorted(set(labels.tolist()))
        targets = np.asarray([classes.index(label) for label in labels], dtype=np.int64)
        guard, resources = make_resource_guard(provider, RUNTIME["stop_below_free_memory_gib"])
        guard()
        cool_gpu(cooling)
        active_guard(root)
        capture_predictions, captured = prediction_capture(baseline._predict)
        started = time.perf_counter()
        with (
            patch.object(baseline, "EEGNet", guarded_constructor(constructor, guard)),
            patch.object(baseline, "_predict", capture_predictions),
        ):
            result, trained = baseline.train_eegnet(
                signals=signals, labels=labels, sessions=sessions,
                train_session=model_config["data"]["train_session"],
                test_session=model_config["data"]["test_session"],
                sampling_rate_hz=gate["sampling_rate_hz"],
                epochs=training["epochs"], batch_size=training["batch_size"],
                learning_rate=training["learning_rate"],
                weight_decay=training["weight_decay"],
                validation_fraction=training["validation_fraction"],
                early_stopping_patience=training["early_stopping_patience"],
                input_scale=training["input_scale"], seed=seed,
                model_options={name: model[name] for name in ("F1", "D", "drop_prob")},
                device_name="cuda", shuffle_labels=False,
            )
        elapsed = time.perf_counter() - started
        if len(captured) != 1:
            raise ValueError("held-out prediction call was not captured exactly once")
        record = RunRecord.create(
            config=resolved_config(context, unit), seed=seed,
            git_commit=source.git_commit, source_sha256=source.source_sha256,
            git_dirty=source.git_dirty, dataset="BNCI2014-001",
            fold=f"{Path(DIAGNOSTIC_NAME).stem}:subject-{subject}",
            metrics={**result.report.record_metrics(),
                     "training_and_prediction_seconds": elapsed},
        )
        payload = {
            "schema": 1, "context_sha256": key,
            "unit": {"configuration": DIAGNOSTIC_NAME, "subject": subject, "seed": seed},
            "record": asdict(record), "result": result.as_dict(), "resources": resources,
            "signal_identity": {
                "shape": list(signals.shape), "dtype": str(signals.dtype),
                "sha256": hashlib.sha256(signals.tobytes(order="C")).hexdigest(),
            },
            "input_labels": labels.tolist(), "input_sessions": sessions.tolist(),
            "split": {name: getattr(split, name).tolist()
                      for name in ("train", "validation", "test")},
            "training_targets": targets.tolist(),
            "query_targets": labels[split.test].tolist(),
            "query_predictions": [classes[index] for index in captured[0].tolist()],
            "diagnostic": {
                "kind": DIAGNOSTIC_ID, "status": "proposed_engineering_diagnostic",
                "gate_a_signed": False, "scientific_cell": False,
            },
        }
        payload = json.loads(json.dumps(payload, allow_nan=False))
        validate_matched_unit(payload, context, unit)
        check_subject_inputs(root, context, subject)
        active_guard(root)
        if source_fingerprint(root) != context["source_sha256"]:
            raise ValueError("source changed during a matched-control fit; record withheld")
        publish_json(root, path, payload)
        print(json.dumps({
            "saved": str(path), "subject": subject, "seed": seed,
            "epochs": result.epochs_completed,
            "balanced_accuracy": result.report.balanced_accuracy,
            "status": "proposed_engineering_diagnostic",
        }), flush=True)
        del trained
    if config_digest(build_context(root, writer_check_sha256)) != key:
        raise ValueError("matched-control context changed before completion")
    report = audit_context(root, context)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0 if report["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--expected-key", default="", help=argparse.SUPPRESS)
    parser.add_argument("--writer-check-sha", default="", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if args.check_only or not args.expected_key or not args.writer_check_sha:
            raise ValueError("supervised worker requires its context and writer-check identity")
        return execute_worker(ROOT, args.expected_key, args.writer_check_sha)
    if args.expected_key or args.writer_check_sha:
        raise ValueError("worker identity options are internal to the supervisor")
    if not args.check_only:
        try:
            startup_guard(ROOT)
        except RuntimeError as error:
            print(json.dumps({
                "deferred": str(error), "training_performed": False,
                "status": "proposed_engineering_diagnostic",
            }), flush=True)
            return 2
    quality_identity(ROOT)
    started_at = time.monotonic()
    writer_check_sha256 = run_writer_check(ROOT)
    context = build_context(ROOT, writer_check_sha256)
    report = audit_context(ROOT, context)
    if args.check_only or report["complete"]:
        print(json.dumps(report, indent=2, sort_keys=True), flush=True)
        return 0 if report["passed"] else 1
    if report["invalid_records"] or report["unexpected_records"]:
        raise ValueError("existing matched-control evidence is invalid; preserve it")
    return supervise(ROOT, context, writer_check_sha256, started_at=started_at)


if __name__ == "__main__":
    raise SystemExit(main())
