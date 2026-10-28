"""Fresh once-only native metadata-test Job; no numerical execution."""

from __future__ import annotations

import argparse
import ctypes
import dataclasses
import importlib.util
import os
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN))
import metadata_common as metadata
for relative, expected in metadata.FROZEN.items():
    metadata.read(ROOT / relative, expected, 1024**2, retain=False)
sys.path.insert(0, str(ROOT / 'tools/migration'))
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
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    prefix = [str(ROOT / '.venv/Scripts/python.exe'), '-I', '-S', '-B', str(RUN / 'runner.py'),
              '--pins', str(RUN / 'pins.json'), '--expect-pins']
    metadata.need(sys.platform == 'win32' and len(command) == 11 and command[:8] == prefix
        and command[9:] == ['--output', str(metadata.OUTPUT)]
        and args.purpose == metadata.SCOPE and args.seconds == 600 and args.process_mib == 4096
        and args.job_mib == 5120 and args.pause_file == metadata.PAUSES[-1],
        'only exact fixed metadata child and unchanged native limits admitted')
    metadata.need(not metadata.OUTPUT.exists(), 'consumed metadata output cannot be replayed')
    bound = metadata.pins(command[8])
    root_admission, peer = metadata.admission(bound, command[8])
    dispatch = metadata.document(RUN / 'dispatch_001.json')
    metadata.need(dispatch['command'] == command and dispatch['pins_sha256'] == command[8]
        and dispatch['root_admission_sha256'] == digest(RUN / 'admission.json'), 'exact immutable dispatch required')
    attempt_sha = metadata.write(RUN / 'guard-attempt_001.json', dict(schema='cho51_p3_contracts_guard_attempt_v1',
        observed_utc=datetime.now(UTC).isoformat(), pins_sha256=command[8],
        root_admission_sha256=digest(RUN / 'admission.json'), dispatch_sha256=digest(RUN / 'dispatch_001.json'),
        peer_release_sha256=root_admission['peer_release_sha256'], maximum_jobs=1, automatic_retry_permitted=False))
    metadata.verify_files(bound)
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
    pins = {
        migration_path.relative_to(ROOT).as_posix(): digest(migration_path)
        for migration_path in (ROOT / "tools/migration").iterdir()
        if migration_path.is_file() and migration_path.suffix in {".py", ".ps1", ".json", ".lock"}
    }
    pins[primitive_path.relative_to(ROOT).as_posix()] = digest(primitive_path)
    runtime = {str(Path(sys.executable).resolve()): digest(Path(sys.executable))}
    for name in ("python312.dll", "python3.dll"):
        path = Path(sys.base_prefix) / name
        if path.exists():
            runtime[str(path)] = digest(path)
    metadata.verify_files(bound)
    root_admission, peer = metadata.admission(bound, command[8])
    started = datetime.now(UTC)
    deadline = started + timedelta(seconds=args.seconds)
    metadata.need(metadata.lease_fits(started, datetime.fromisoformat(peer['window_end_utc']).astimezone(UTC)),
                  'full attempt and cleanup lease must fit fresh peer window')
    samples = []

    def sensor(path):
        if any(path.exists() for path in metadata.PAUSES):
            raise primitive.SupervisionError("peer pause requested")
        if datetime.now(UTC) > datetime.fromisoformat(peer['window_end_utc']).astimezone(UTC):
            raise primitive.SupervisionError('peer window ended')
        return primitive.live_resources(path)

    accepted = False
    result = None
    error = None
    try:
        for _ in range(2):
            sample = sensor(ROOT)
            samples.append(dataclasses.asdict(sample))
            if sample.available_ram_bytes < bound['startup_ram_gib'] * GIB or sample.free_disk_bytes < 20 * GIB:
                raise ValueError("startup RAM below independently recorded phase floor or disk below20GiB")
            time.sleep(0.2)
        admission = {
            "schema": "migration_admission_v1",
            "purpose": args.purpose,
            "authority": "owner-authorized metadata tests; zero numerical/scientific admission",
            "pins_sha256": command[8],
            "guard_attempt_sha256": attempt_sha,
            "root_admission_sha256": digest(RUN / "admission.json"),
            "source_review_sha256": bound["source_review_sha256"],
            "peer_release_sha256": root_admission["peer_release_sha256"],
            "expected_numerical_budget": metadata.ZERO,
            "startup_ram_gib": bound["startup_ram_gib"],
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
        metadata.admission(bound, command[8])
        metadata.need(datetime.now(UTC) < deadline and deadline + timedelta(seconds=5)
            <= datetime.fromisoformat(peer['window_end_utc']).astimezone(UTC), 'peer lease changed before Job launch')
        os.environ.update(PRO3_P3_NATIVE=str(out), PRO3_P3_JOB=job_name)
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
        if source_check(ROOT) != source or any(digest(ROOT / relative) != expected for relative, expected in pins.items()):
            raise ValueError("source/operations changed during command")
        if any(digest(Path(runtime_path)) != expected for runtime_path, expected in runtime.items()):
            raise ValueError("selected runtime changed during command")
        metadata.verify_files(bound)
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
    if (out / "command.log").exists():
        print(metadata.tail(out / 'command.log'))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
