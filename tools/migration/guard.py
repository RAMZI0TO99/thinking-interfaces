"""Finite Windows Job for setup, archive verification and data-only rebuilds."""

from __future__ import annotations

import argparse
import ctypes
import dataclasses
import hashlib
import importlib.util
import os
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GIB, ROOT, digest, source_check, write_json


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
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
    parser.add_argument("--quality", action="store_true", help="fixed full quality command, up to 4200s; no arbitrary command")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if args.quality:
        if command:
            parser.error("quality mode uses its fixed reviewed command")
        command = [str(ROOT / ".venv/Scripts/python.exe"), "-I", "-B",
                   str(ROOT / "scripts/run_guarded_quality.py"), "--expect-source",
                   source_check(ROOT), "--attempt-directory",
                   "runs/phase2/quality_attempts/portable_" + uuid.uuid4().hex[:12],
                   "--startup-ram-gib", "10"]
        args.process_mib, args.job_mib = 6144, 7680
    cap = 4200 if args.quality else 600
    if sys.platform != "win32" or not command or not 10 <= args.seconds <= cap:
        parser.error(f"Windows, a command and a 10..{cap} second bound are required")
    if not 256 <= args.process_mib <= args.job_mib <= 7680:
        parser.error("invalid memory caps")
    source = source_check(ROOT)
    primitive_path = ROOT / "evaluation/phase2_supervision_primitives.py"
    if digest(primitive_path) != "3590b6c72e9ddfbfa0de4e012b55b0237c77375ede5b75ccfe7352e4c8cb063e":
        raise ValueError("supervision primitive differs")
    primitive = load("_migration_supervision", primitive_path)
    if args.quality:
        primitive.MAX_ATTEMPT_SECONDS = 4200
    adapter = load("_migration_adapter", ROOT / "tools/migration/job_adapter.py")
    adapter.MEMORY_LIMIT_BYTES = args.process_mib * 1024**2
    adapter.AGGREGATE_LIMIT_BYTES = args.job_mib * 1024**2
    out = ROOT / "runs/migration" / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:10])
    out.mkdir(parents=True, exist_ok=False)
    job_name = "pro3_migration_" + out.name
    state = {key: False for key in (
        "limits_set", "limits_query_verified", "job_created", "created_suspended",
        "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned",
        "membership_verified", "resumed", "job_empty_before_close", "job_closed",
        "root_exit_after_job_close", "process_handle_closed", "thread_handle_closed",
        "assignment_step_seen", "owned_job_termination_called")}
    state.update(peak_samples=0, peak_process_commit_bytes=0, peak_job_commit_bytes=0,
                 cleanup_errors=[], peak_sampling_errors=[])
    adapter.install_job_adapter(primitive, state, job_name)
    pause = args.pause_file
    if pause is None and os.environ.get("PRO3_PEER_PAUSE_FILE"):
        pause = Path(os.environ["PRO3_PEER_PAUSE_FILE"])
    pins = {p.relative_to(ROOT).as_posix(): digest(p)
            for p in (ROOT / "tools/migration").iterdir()
            if p.is_file() and p.suffix in {".py", ".ps1", ".json", ".lock"}}
    pins[primitive_path.relative_to(ROOT).as_posix()] = digest(primitive_path)
    runtime = {str(Path(sys.executable).resolve()): digest(Path(sys.executable))}
    for name in ("python312.dll", "python3.dll"):
        path = Path(sys.base_prefix) / name
        if path.exists():
            runtime[str(path)] = digest(path)
    started = datetime.now(UTC)
    deadline = started + timedelta(seconds=args.seconds)
    samples = []

    def sensor(path):
        if pause is not None and pause.exists():
            raise primitive.SupervisionError("peer pause requested")
        return primitive.live_resources(path)

    accepted = False
    result = None
    error = None
    try:
        for _ in range(2):
            sample = sensor(ROOT)
            samples.append(dataclasses.asdict(sample))
            if sample.available_ram_bytes < 10 * GIB or sample.free_disk_bytes < 20 * GIB:
                raise ValueError("startup requires 10 GiB available RAM and 20 GiB free disk")
            time.sleep(0.2)
        admission = {
            "schema": "migration_admission_v1", "purpose": args.purpose,
            "authority": "operator setup command; no training or scientific admission",
            "source_sha256": source, "operation_pins": pins, "selected_runtime_pins": runtime,
            "command": command, "started_utc": started.isoformat(),
            "deadline_utc": deadline.isoformat(), "startup_samples": samples,
            "process_mib": args.process_mib, "job_mib": args.job_mib,
            "active_ram_gib": 4, "active_disk_gib": 20, "native_threads": 1,
            "peer_pause_file": None if pause is None else str(pause),
        }
        write_json(out / "admission.json", admission)
        primitive.DeadlineLease.open_or_create(
            out / "deadline.json", attempt_deadline_utc=deadline,
            session_deadline_utc=deadline + timedelta(seconds=5))
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"):
            os.environ.pop(key, None)
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
            os.environ[key] = "1"
        os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1",
                          HF_HOME=str(ROOT / ".cache/huggingface"),
                          PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
        task = [str(Path(sys.executable).resolve()), "-I", "-S", "-B",
                str(ROOT / "tools/migration/task.py"), str(out), *command]
        result = primitive.run_supervised(
            task, cwd=ROOT, deadline_path=out / "deadline.json", sensor=sensor,
            floor=primitive.ResourceFloor(), poll_seconds=0.2,
            process_memory_limit_bytes=adapter.MEMORY_LIMIT_BYTES)
        if result.exit_code != 0 or result.reason != "normal":
            raise ValueError("guarded command failed: " + str(result))
        if state["cleanup_errors"] or state["peak_sampling_errors"]:
            raise ValueError("Job cleanup or peak sampling unconfirmed")
        for key in ("atomic_job_assignment_verified", "job_empty_before_close", "job_closed",
                    "process_handle_closed", "thread_handle_closed"):
            if not state[key]:
                raise ValueError("native cleanup unconfirmed: " + key)
        if source_check(ROOT) != source or any(digest(ROOT / p) != h for p, h in pins.items()):
            raise ValueError("source/operations changed during command")
        if any(digest(Path(p)) != h for p, h in runtime.items()):
            raise ValueError("selected runtime changed during command")
        accepted = True
    except Exception as exc:
        error = str(exc)
    # The adapter queried Job emptiness and closed every owned handle. Verify name absent too.
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
    receipt = {"schema": "migration_guard_receipt_v1", "accepted": accepted,
               "error": error, "job_name": job_name, "job_absent": absent,
               "startup_samples": samples,
               "native_state": state, "result": None if result is None else dataclasses.asdict(result),
               "completed_utc": datetime.now(UTC).isoformat(), "scientific_admission": False}
    write_json(out / "receipt.json", receipt)
    print(str(out))
    print("PASS" if accepted else "FAIL: " + str(error))
    if (out / "command.log").exists():
        print((out / "command.log").read_text(errors="replace")[-4000:])
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
