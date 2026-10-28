"""Versioned bounded integrated engineering Job with the owner-adopted 4 GiB startup allowance."""

from __future__ import annotations

import argparse
import ctypes
import dataclasses
import hashlib
import json
import stat
import importlib.util
import os
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
MIGRATION = ROOT / "tools/migration"
FROZEN_IMPORTS = {
    "tools/migration/guard.py": "1150228137873b783ba5800b89ded0e7598448f05da3b87a7ac0a62e6079f157",
    "tools/migration/common.py": "fe2790bc2703af17b930dffe109d8c750fb8d0abfa205fbd40245aec178936d5",
    "tools/migration/job_adapter.py": "a6902fabf675b329440b39404cdc4306e562fda4b47efefb19982c6c2502ae8b",
    "tools/migration/task.py": "8ffb5d42cfe7107d57b8bb7d69d07909cd1dd14bc32a5e645b1d675e0c3e8a70",
    "evaluation/phase2_supervision_primitives.py": "3590b6c72e9ddfbfa0de4e012b55b0237c77375ede5b75ccfe7352e4c8cb063e",
}
OPERATION_NAMES = {
    "guard.py", "prepare.py", "parent.py", "runtime.py", "origin.py",
    "native_pins.ps1", "launch.ps1", "closeout.py",
}
PAUSE_PATHS = tuple(Path("D:/Aenv/pro2/WORK") / f"resume-{day}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json"
    for day in ("20261007", "20261012", "20261013", "20261015", "20261025"))


def pinned_bytes(path, expected, maximum=8 * 1024**2):
    path = Path(path)
    before = path.stat()
    key = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    if path.resolve(strict=True) != path or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 <= before.st_size <= maximum:
        raise ValueError("direct bounded single-link guard input required")
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
            raise ValueError("guard input reparse ancestor refused")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(before.st_size + 1)
        finished = os.fstat(stream.fileno())
    if (len(raw) != before.st_size or key(before) != key(path.stat()) or key(opened) != key(finished)
            or key(before)[:4] != key(opened)[:4] or hashlib.sha256(raw).hexdigest() != expected):
        raise ValueError("guard input physical identity or hash changed")
    return raw


def pinned_json(path, expected):
    def unique(rows):
        result = {}
        for name, value in rows:
            if name in result:
                raise ValueError("duplicate guard JSON key")
            result[name] = value
        return result
    return json.loads(pinned_bytes(path, expected), object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite guard JSON")))


for frozen_relative, frozen_sha256 in FROZEN_IMPORTS.items():
    pinned_bytes(ROOT / frozen_relative, frozen_sha256, 1024**2)
sys.path.insert(0, str(MIGRATION))
from common import GIB, digest, source_check, write_json


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    pinned_bytes(path, FROZEN_IMPORTS[path.relative_to(ROOT).as_posix()], 1024**2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--process-mib", type=int, default=4096)
    parser.add_argument("--job-mib", type=int, default=5120)
    parser.add_argument("--pause-file", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    expected_prefix = [str(ROOT / ".venv/Scripts/python.exe"), "-I", "-S", "-B", str(RUN / "parent.py"), "--pins", str(RUN / "pins.json"), "--expect-pins"]
    outputs = {str(RUN / ({"tests": "t1", "integration": "i1"}[phase])): phase for phase in ("tests", "integration")}
    if (sys.platform != "win32" or args.seconds != 600 or args.process_mib != 4096 or args.job_mib != 5120
            or len(command) != 11 or command[:8] != expected_prefix
            or command[9:10] != ["--output"] or command[10] not in outputs or args.pause_file != PAUSE_PATHS[-1]):
        parser.error("only the exact bounded integrated engineering child and unchanged caps are admitted")
    phase = outputs[command[10]]
    if Path(command[10]).exists():
        raise ValueError("phase output is consumed; no automatic replay")
    scope = "cho51_provenance_numerical_worker_20261025_v7_" + phase
    bound_pins = pinned_json(RUN / "pins.json", command[8])
    if (bound_pins.get("schema") != "cho51_provenance_numerical_worker_pins_v1"
            or bound_pins.get("startup_ram_gib") != 4 or bound_pins.get("active_ram_gib") != 4
            or bound_pins.get("disk_gib") != 20):
        raise ValueError("fresh owner-amended restoration pins required")
    expected_budget = {"source_updates": 0, "restore_count": 1, "support_updates": 1,
        "gradient_updates": 1, "target_inference_calls": 1, "query_count": 2,
        "model_constructions": 1, "measured_cells": 0}
    if phase == "tests":
        expected_budget = dict.fromkeys(expected_budget, 0)
    if (bound_pins.get("phase_scopes") != {name: "cho51_provenance_numerical_worker_20261025_v7_" + name for name in ("tests", "integration")}
            or bound_pins.get("phase_budgets", {}).get(phase) != expected_budget):
        raise ValueError("exact disjoint phase scopes and budgets required")
    if bound_pins["phase_budgets"][phase] != expected_budget or any(
            type(bound_pins["phase_budgets"][phase].get(name)) is not int
            for name in expected_budget) or bound_pins.get("scientific_admission") is not False:
        raise ValueError("exact engineering-only integrated numerical budget required")
    amendment_path = Path(bound_pins["owner_resource_amendment_path"])
    amendment = pinned_json(amendment_path, bound_pins["owner_resource_amendment_sha256"])
    expected_amendment = {
        "schema": "cho51_provenance_numerical_worker_owner_resource_amendment_v1",
        "scope": "cho51_provenance_numerical_worker_20261025_v7",
        "owner_instruction_exact": "use the available ram now!",
        "previous_startup_ram_gib": 10, "startup_ram_gib": 4, "active_ram_gib": 4,
        "disk_gib": 20, "maximum_job_seconds": 600, "process_mib": 4096, "job_mib": 5120,
        "threads": 1, "gpu_hidden": True, "canonical_guard_modified": False,
        "historical_receipts_requalified": False, "scientific_admission": False,
    }
    if amendment_path != RUN / "owner-resource-amendment.json" or any(
            type(amendment.get(name)) is not type(value) or amendment[name] != value
            for name, value in expected_amendment.items()):
        raise ValueError("exact direct-owner startup-only amendment required")
    dispatch_path = RUN / ("dispatch_" + phase + "_001.json")
    with dispatch_path.open("rb") as stream:
        dispatch_raw = stream.read(1024**2 + 1)
    if len(dispatch_raw) > 1024**2:
        raise ValueError("bounded fresh dispatch required")
    dispatch = pinned_json(dispatch_path, hashlib.sha256(dispatch_raw).hexdigest())
    root_admission = pinned_json(RUN / ("admission_" + phase + ".json"), dispatch["admission_sha256"])
    expected_root = {
        "schema": "cho51_provenance_numerical_worker_admission_v1", "phase": phase, "pins_sha256": command[8],
        "expected_numerical_budget": expected_budget,
        "source_review_sha256": bound_pins["source_review_sha256"], "accepted": True,
        "scientific_admission": False, "max_job_seconds": 600, "process_mib": 4096, "job_mib": 5120,
        "startup_ram_gib": 4, "active_ram_gib": 4, "disk_gib": 20,
        "owner_resource_amendment_path": str(amendment_path),
        "owner_resource_amendment_sha256": bound_pins["owner_resource_amendment_sha256"],
    }
    if any(type(root_admission.get(name)) is not type(value) or root_admission[name] != value
            for name, value in expected_root.items()):
        raise ValueError("exact freshly pinned root admission required")
    peer_release = pinned_json(Path(root_admission["peer_release_path"]), root_admission["peer_release_sha256"])
    expected_peer = {
        "schema": "pro2_pro3_compute_release_v1", "scope": scope,
        "released": True, "pins_sha256": command[8], "maximum_jobs": 1, "max_job_seconds": 600,
        "process_mib": 4096, "job_mib": 5120, "window_start_utc": root_admission["window_start_utc"],
        "window_end_utc": root_admission["window_end_utc"],
    }
    if any(type(peer_release.get(name)) is not type(value) or peer_release[name] != value
            for name, value in expected_peer.items()):
        raise ValueError("exact fresh peer release for the bounded pinned Job required")
    peer_start = datetime.fromisoformat(root_admission["window_start_utc"].replace("Z", "+00:00"))
    peer_end = datetime.fromisoformat(root_admission["window_end_utc"].replace("Z", "+00:00"))
    if not peer_start <= datetime.now(UTC) <= peer_end - timedelta(seconds=600):
        raise ValueError("the full finite Job must fit the live explicit peer window")
    review = pinned_json(RUN / "source-review.json", bound_pins["source_review_sha256"])
    if review.get("source_only") is not True or review.get("remaining_actionable_findings") != [] or review.get("files") != bound_pins["reviewed_files"]:
        raise ValueError("exact independently settled source review required")
    reviewed_operations = {name: value for name, value in bound_pins["reviewed_files"].items()
        if Path(name).parent == RUN.relative_to(ROOT)}
    if {Path(name).name for name in reviewed_operations} != OPERATION_NAMES or len(bound_pins["reviewed_files"]) != 13:
        raise ValueError("exact eight operations and five integration candidate source pins required")
    for reviewed_name, reviewed_sha256 in bound_pins["reviewed_files"].items():
        pinned_bytes(ROOT / reviewed_name, reviewed_sha256, 1024**2)
    if phase == "integration":
        origin_path = RUN / "origin.py"
        origin_spec = importlib.util.spec_from_file_location("_two_stage_guard_origin", origin_path)
        origin_module = importlib.util.module_from_spec(origin_spec)
        sys.modules[origin_spec.name] = origin_module
        origin_spec.loader.exec_module(origin_module)
        origin_module.verify_tests_join(root_admission, bound_pins, command[8])
    source = source_check(ROOT)
    primitive_path = ROOT / "evaluation/phase2_supervision_primitives.py"
    if digest(primitive_path) != "3590b6c72e9ddfbfa0de4e012b55b0237c77375ede5b75ccfe7352e4c8cb063e":
        raise ValueError("supervision primitive differs")
    primitive = load("_migration_supervision", primitive_path)
    adapter = load("_migration_adapter", ROOT / "tools/migration/job_adapter.py")
    adapter.MEMORY_LIMIT_BYTES = args.process_mib * 1024**2
    adapter.AGGREGATE_LIMIT_BYTES = args.job_mib * 1024**2
    out = (
        ROOT
        / "runs/migration"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:10])
    )
    out.mkdir(parents=True, exist_ok=False)
    job_name = "pro3_migration_" + out.name
    state = {
        key: False
        for key in (
            "limits_set",
            "limits_query_verified",
            "job_created",
            "created_suspended",
            "atomic_job_assignment_requested",
            "atomic_job_assignment_verified",
            "assigned",
            "membership_verified",
            "resumed",
            "job_empty_before_close",
            "job_closed",
            "root_exit_after_job_close",
            "process_handle_closed",
            "thread_handle_closed",
            "assignment_step_seen",
            "owned_job_termination_called",
        )
    }
    state.update(
        peak_samples=0,
        peak_process_commit_bytes=0,
        peak_job_commit_bytes=0,
        cleanup_errors=[],
        peak_sampling_errors=[],
    )
    adapter.install_job_adapter(primitive, state, job_name)
    pause = args.pause_file
    if pause is None and os.environ.get("PRO3_PEER_PAUSE_FILE"):
        pause = Path(os.environ["PRO3_PEER_PAUSE_FILE"])
    pins = {
        pinned_path.relative_to(ROOT).as_posix(): digest(pinned_path)
        for pinned_path in (ROOT / "tools/migration").iterdir()
        if pinned_path.is_file() and pinned_path.suffix in {".py", ".ps1", ".json", ".lock"}
    }
    pins[primitive_path.relative_to(ROOT).as_posix()] = digest(primitive_path)
    pins.update(reviewed_operations)
    runtime = {str(Path(sys.executable).resolve()): digest(Path(sys.executable))}
    for name in ("python312.dll", "python3.dll"):
        path = Path(sys.base_prefix) / name
        if path.exists():
            runtime[str(path)] = digest(path)
    started = datetime.now(UTC)
    deadline = started + timedelta(seconds=args.seconds)
    samples = []

    def sensor(path):
        if pause is not None and pause.exists() or any(path.exists() for path in PAUSE_PATHS):
            raise primitive.SupervisionError("peer pause requested")
        if datetime.now(UTC) > peer_end:
            raise primitive.SupervisionError("explicit peer compute release expired")
        return primitive.live_resources(path)

    accepted = False
    result = None
    error = None
    try:
        for _ in range(2):
            sample = sensor(ROOT)
            samples.append(dataclasses.asdict(sample))
            if sample.available_ram_bytes < 4 * GIB or sample.free_disk_bytes < 20 * GIB:
                raise ValueError("owner-amended integration startup requires 4 GiB available RAM and 20 GiB free disk")
            time.sleep(0.2)
        admission = {
            "schema": "migration_admission_v1",
            "purpose": args.purpose,
            "authority": "direct owner startup-only 4 GiB amendment for bounded engineering integration; no training or scientific admission",
            "guard_policy_schema": "cho51_provenance_numerical_worker_guard_v1",
            "phase": phase, "expected_numerical_budget": expected_budget,
            "startup_ram_gib": 4,
            "previous_startup_ram_gib": 10,
            "historical_10gib_startup_pass_claimed": False,
            "owner_resource_amendment_path": str(amendment_path),
            "owner_resource_amendment_sha256": bound_pins["owner_resource_amendment_sha256"],
            "source_sha256": source,
            "operation_pins": pins,
            "selected_runtime_pins": runtime,
            "command": command,
            "started_utc": started.isoformat(),
            "deadline_utc": deadline.isoformat(),
            "startup_samples": samples,
            "process_mib": args.process_mib,
            "job_mib": args.job_mib,
            "active_ram_gib": 4,
            "active_disk_gib": 20,
            "native_threads": 1,
            "peer_pause_file": None if pause is None else str(pause),
        }
        write_json(out / "admission.json", admission)
        primitive.DeadlineLease.open_or_create(
            out / "deadline.json",
            attempt_deadline_utc=deadline,
            session_deadline_utc=deadline + timedelta(seconds=5),
        )
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"):
            os.environ.pop(key, None)
        for key in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        ):
            os.environ[key] = "1"
        os.environ.update(
            CUDA_VISIBLE_DEVICES="",
            HF_HUB_OFFLINE="1",
            HF_HOME=str(ROOT / ".cache/huggingface"),
            PYTHONNOUSERSITE="1",
            PYTHONDONTWRITEBYTECODE="1",
        )
        task = [
            str(Path(sys.executable).resolve()),
            "-I",
            "-S",
            "-B",
            str(ROOT / "tools/migration/task.py"),
            str(out),
            *command,
        ]
        result = primitive.run_supervised(
            task,
            cwd=ROOT,
            deadline_path=out / "deadline.json",
            sensor=sensor,
            floor=primitive.ResourceFloor(),
            poll_seconds=0.2,
            process_memory_limit_bytes=adapter.MEMORY_LIMIT_BYTES,
        )
        if result.exit_code != 0 or result.reason != "normal":
            raise ValueError("guarded command failed: " + str(result))
        if state["cleanup_errors"] or state["peak_sampling_errors"]:
            raise ValueError("Job cleanup or peak sampling unconfirmed")
        for key in (
            "atomic_job_assignment_verified",
            "job_empty_before_close",
            "job_closed",
            "process_handle_closed",
            "thread_handle_closed",
        ):
            if not state[key]:
                raise ValueError("native cleanup unconfirmed: " + key)
        if source_check(ROOT) != source or any(digest(ROOT / pinned_path) != pinned_sha256 for pinned_path, pinned_sha256 in pins.items()):
            raise ValueError("source/operations changed during command")
        pinned_json(amendment_path, bound_pins["owner_resource_amendment_sha256"])
        if any(digest(Path(pinned_path)) != pinned_sha256 for pinned_path, pinned_sha256 in runtime.items()):
            raise ValueError("selected runtime changed during command")
        accepted = True
    except Exception as exc:
        error = str(exc)
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    ctypes.set_last_error(0)
    handle = api.OpenJobObjectW(0x0004, False, job_name)
    absent = not handle and ctypes.get_last_error() == 2
    if handle:
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        api.CloseHandle(handle)
    accepted = accepted and absent
    receipt = {
        "schema": "migration_guard_receipt_v1",
        "accepted": accepted,
        "error": error,
        "job_name": job_name,
        "job_absent": absent,
        "startup_samples": samples,
        "native_state": state,
        "result": None if result is None else dataclasses.asdict(result),
        "completed_utc": datetime.now(UTC).isoformat(),
        "scientific_admission": False,
    }
    write_json(out / "receipt.json", receipt)
    print(str(out))
    print("PASS" if accepted else "FAIL: " + str(error))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())







