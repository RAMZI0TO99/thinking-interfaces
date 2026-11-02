"""One newly admitted bounded local Sysmon recovery operation on Windows.

This is a new runner, not a bootstrap004/005 or migration-launcher invocation.
Its trust base is pinned by Root before execution; it does not certify itself.
"""
from __future__ import annotations

import ctypes
import dataclasses
import hashlib
import importlib.util
import json
import os
import stat
import sys
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
BASE = ROOT / "runs/coordination/cho51_p3_sysmon_recovery_20261028_v7"
STOP = ROOT / "runs/coordination/PROJECT_STOP.json"
REQUIRED = [
    "tools/custody_boundary/v7/collector.py",
    "tools/custody_boundary/v7/test_collector.py",
    "tools/custody_boundary/v7/child_entry.py",
    "tools/custody_boundary/v7/validation_runner.py",
    "tools/custody_boundary/v7/README.md",
    "tools/custody_boundary/v7/PROTOCOL.md",
    "tools/custody_boundary/v4/collector.py",
    "tools/custody_boundary/v5/decoder.py",
    "evaluation/phase2_supervision_primitives.py",
    "tools/migration/job_adapter.py",
    "runs/coordination/cho51_p3_contracts_20261027_v1/bootstrap-supervise_004.ps1",
    "runs/coordination/cho51_p3_contracts_20261027_v1/bootstrap-disposition_004.json",
    "runs/coordination/cho51_p3_contracts_20261027_v1/bootstrap-external-audit_004.json",
    "docs/PROJECT_EXECUTION_POLICY.md",
]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result
    if len(raw) > 1048576:
        raise ValueError("record exceeds1MiB")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))


def write(path, value):
    raw = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    if len(raw) > 1048576:
        raise ValueError("record exceeds1MiB")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def check_path(path):
    if not path.is_absolute() or str(path).startswith("\\\\") or path != path.resolve():
        raise ValueError("absolute canonical local path required")
    for current in [*reversed(path.parents), path]:
        value = current.lstat()
        if value.st_file_attributes & 1024 or stat.S_ISLNK(value.st_mode):
            raise ValueError("reparse path refused")


class Pins:
    """Retain read-only no-write/no-delete sharing for source and runtime files.

    These are runner inputs, not authenticated historical boundary artifacts.
    Directory handles prevent replacement through ancestor renames during use.
    """
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        self.api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.api.CreateFileW.restype = ctypes.c_void_p
        self.api.CloseHandle.argtypes = [ctypes.c_void_p]
        self.api.CloseHandle.restype = ctypes.c_int
        self.api.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
        self.api.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
        self.handles = []
        self.directories = set()
        self.rows = []

    def open(self, path, directory=False):
        check_path(path)
        handle = self.api.CreateFileW(str(path), 0x80000000, 1, None, 3,
                                      0x00200000 | (0x02000000 if directory else 0), None)
        if handle in (None, ctypes.c_void_p(-1).value):
            raise OSError(ctypes.get_last_error(), "retained input open")
        self.handles.append(handle)
        check_path(path)
        actual = ctypes.create_unicode_buffer(32768)
        count = self.api.GetFinalPathNameByHandleW(handle, actual, len(actual), 0)
        if not 0 < count < len(actual) or actual.value != "\\\\?\\" + str(path):
            raise ValueError("retained path identity differs")
        return handle

    def read(self, path, expected=None):
        import msvcrt
        for parent in reversed(path.parents):
            if parent not in self.directories:
                self.open(parent, True)
                self.directories.add(parent)
        handle = self.open(path)
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        self.handles.remove(handle)  # descriptor now owns this handle
        stream = os.fdopen(descriptor, "rb")
        try:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > 16777216:
                raise ValueError("input file type/link/size refused")
            raw = stream.read(16777217)
            after = os.fstat(stream.fileno())
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
            if identity(before) != identity(after) or len(raw) != before.st_size:
                raise ValueError("input changed during retained read")
            if expected and (set(expected) != {"bytes", "sha256"} or
                             expected != {"bytes": len(raw), "sha256": digest(raw)}):
                raise ValueError("input pin mismatch: " + str(path))
            self.rows.append((stream, identity(after), identity))
            return raw
        except BaseException:
            stream.close()
            raise

    def close_files(self):
        failures = []
        for stream, before, identity in reversed(self.rows):
            try:
                if identity(os.fstat(stream.fileno())) != before:
                    failures.append("retained file changed")
            finally:
                stream.close()
        if failures:
            raise RuntimeError("; ".join(failures))

    def close_directories(self):
        failures = []
        for handle in reversed(self.handles):
            if not self.api.CloseHandle(handle):
                failures.append("retained directory handle close failed")
        if failures:
            raise RuntimeError("; ".join(failures))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def no_stop():
    # exists() can conceal access errors; only an actual ENOENT is absence.
    check_path(STOP.parent)
    try:
        STOP.lstat()
    except FileNotFoundError:
        return
    raise RuntimeError("local stop present or unknown")


def main():
    began = time.monotonic()
    if sys.platform != "win32" or len(sys.argv) != 3:
        raise ValueError("Windows, admission path and digest required")
    # The private Job is noninherited and kill-on-close. A forced parent exit
    # closes it in the kernel, including uncertain native creation paths.
    # Such exit has NO accepted receipt; actual caller/result review must fail.
    def outer_deadline():
        while time.monotonic() - began < 90:
            time.sleep(0.05)
        os._exit(124)
    threading.Thread(target=outer_deadline, daemon=True, name="boundary-deadline").start()
    pins = Pins()
    out = None
    state = {}
    result = None
    samples = []
    error = None
    accepted = False
    try:
        request_path = Path(sys.argv[1])
        raw = pins.read(request_path)
        if digest(raw) != sys.argv[2]:
            raise ValueError("admission digest differs from external caller pin")
        request = strict(raw)
        if set(request) != {"schema", "operation_id", "mode", "created_utc", "expires_utc",
                             "sources", "runtime", "review", "limits", "scientific_admission"}:
            raise ValueError("closed admission fields required")
        if request["schema"] != "cho51_p3_sysmon_recovery_admission_v7" or request["scientific_admission"] is not False:
            raise ValueError("wrong admission kind")
        operation = str(uuid.UUID(request["operation_id"]))
        if operation != request["operation_id"] or request["mode"] not in {"tests", "capture"}:
            raise ValueError("operation identity/mode refused")
        cache_prefix = BASE / "disabled-bytecode" / operation
        if sys.pycache_prefix != str(cache_prefix):
            raise ValueError("fresh bytecode prefix required for parent")
        def no_cache():
            check_path(cache_prefix.parent)
            try:
                cache_prefix.lstat()
            except FileNotFoundError:
                return
            raise RuntimeError("bytecode cache prefix exists or is unknown")
        no_cache()
        now = datetime.now(UTC)
        start, end = (datetime.fromisoformat(request[k].replace("Z", "+00:00")) for k in ("created_utc", "expires_utc"))
        if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0) or not start <= now < end or not 0 < (end-start).total_seconds() <= 900:
            raise ValueError("admission window refused")
        limits = {"startup_ram_gib": 4, "active_ram_gib": 4, "disk_gib": 20,
                  "process_mib": 512, "job_mib": 768, "child_seconds": 45,
                  "whole_seconds": 90, "payload_bytes": 1048576, "threads": 1, "gpu_visible": False}
        if (type(request["limits"]) is not dict or set(request["limits"]) != set(limits)
                or any(type(request["limits"][key]) is not type(value) or request["limits"][key] != value
                       for key, value in limits.items())):
            raise ValueError("fixed operation limits required")
        if set(request["sources"]) != set(REQUIRED):
            raise ValueError("source set incomplete or extended")
        for relative, expected in request["sources"].items():
            pins.read(ROOT / relative, expected)
        review_ref = request["review"]
        if set(review_ref) != {"path", "bytes", "sha256"} or review_ref["path"] != "source-review.json":
            raise ValueError("review reference refused")
        review = strict(pins.read(BASE / review_ref["path"], {k: review_ref[k] for k in ("bytes", "sha256")}))
        if review["status"] != "ACCEPTED_SOURCE" or review["sources"] != request["sources"] or review["reviewer"] in review["authors"]:
            raise ValueError("independent exact source review required")
        runtime = request["runtime"]
        python_root = Path(sys.base_prefix).resolve()
        expected_runtime = {str(python_root / n) for n in ("python.exe", "python312.dll", "python3.dll", "vcruntime140.dll", "vcruntime140_1.dll")}
        expected_runtime |= {str(p) for directory, suffixes in (("Lib", {".py"}), ("DLLs", {".pyd", ".dll"}))
                             for p in (python_root / directory).rglob("*") if p.suffix in suffixes and "site-packages" not in p.parts}
        if set(runtime) != expected_runtime or Path(sys.executable).resolve() != python_root / "python.exe":
            raise ValueError("exact base runtime inventory required")
        for path, expected in runtime.items():
            pins.read(Path(path), expected)
        no_stop()
        check_path(BASE / "attempts")
        pins.open(BASE / "attempts", True)
        out = BASE / "attempts" / operation
        out.mkdir()  # atomic create-once; an existing identity is consumed
        pins.open(out, True)
        # Pure/injected tests write no fixture files. Only the fixed child writes
        # its bounded create-once payload beneath this retained fresh directory.
        write(out / "claim.json", {"operation_id": operation, "admission_sha256": digest(raw), "created_utc": now.isoformat()})
        primitive = load("_boundary_supervision", ROOT / "evaluation/phase2_supervision_primitives.py")
        adapter = load("_boundary_job_adapter", ROOT / "tools/migration/job_adapter.py")
        adapter.MEMORY_LIMIT_BYTES = limits["process_mib"] * 1024**2
        adapter.AGGREGATE_LIMIT_BYTES = limits["job_mib"] * 1024**2
        state = {key: False for key in (
            "limits_set", "limits_query_verified", "job_created", "created_suspended",
            "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned",
            "membership_verified", "resumed", "job_empty_before_close", "job_closed",
            "root_exit_after_job_close", "process_handle_closed", "thread_handle_closed",
            "assignment_step_seen", "owned_job_termination_called")}
        state.update(peak_samples=0, peak_process_commit_bytes=0, peak_job_commit_bytes=0,
                     cleanup_errors=[], peak_sampling_errors=[])
        # Unnamed Job: no name collision or independently opened named handle.
        adapter.install_job_adapter(primitive, state, None)
        def sensor(path):
            no_stop()
            no_cache()
            if time.monotonic() - began >= 75 or datetime.now(UTC) >= end:
                raise RuntimeError("outer work bound expired")
            return primitive.live_resources(path)
        for _ in range(2):
            sample = sensor(ROOT)
            samples.append(dataclasses.asdict(sample))
            if sample.available_ram_bytes < 4 * 1024**3 or sample.free_disk_bytes < 20 * 1024**3:
                raise RuntimeError("startup resource floor")
            time.sleep(0.2)
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"):
            os.environ.pop(key, None)
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[key] = "1"
        os.environ.update(CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
        deadline = min(end, datetime.now(UTC) + timedelta(seconds=45))
        primitive.DeadlineLease.open_or_create(out / "deadline.json", attempt_deadline_utc=deadline,
                                              session_deadline_utc=deadline)
        command = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + str(cache_prefix),
                   str(HERE / "child_entry.py"), request["mode"], str(out / "payload.json")]
        write(out / "dispatch.json", {"command": command, "start_attempted": True,
                                      "custody_known_before_native_call": False, "startup_samples": samples})
        result = primitive.run_supervised(command, cwd=ROOT, deadline_path=out / "deadline.json",
                                           sensor=sensor, poll_seconds=0.1,
                                           process_memory_limit_bytes=adapter.MEMORY_LIMIT_BYTES)
        needed = ("atomic_job_assignment_verified", "limits_query_verified", "job_empty_before_close",
                  "job_closed", "root_exit_after_job_close", "process_handle_closed", "thread_handle_closed")
        if result.exit_code != 0 or result.reason != "normal" or not all(state[k] for k in needed) or state["cleanup_errors"] or state["peak_sampling_errors"]:
            raise RuntimeError("child result/owned cleanup not accepted")
        raw_payload = pins.read(out / "payload.json")
        payload = strict(raw_payload)
        if request["mode"] == "tests":
            if payload.get("successful") is not True or not payload.get("tests_run", 0) > 0 or payload.get("failures") != 0 or payload.get("errors") != 0 or payload.get("skipped") != 0:
                raise ValueError("fixture payload rejected")
        elif (payload.get("schema") != "cho51_p3_sysmon_capture_v7" or payload.get("status") != "UNRESOLVED"
              or payload.get("fresh_provider_observation") is not True
              or payload.get("native_handles_closed") is not True
              or any(payload.get(key) is not False for key in (
                  "historical_custody_closed", "historical_operation_released", "historical_retry_allowed",
                  "boundary_qualified"))):
            raise ValueError("bounded Sysmon capture payload rejected")
        if payload.get("launch_authorized") is not False or payload.get("scientific_admission") is not False:
            raise ValueError("payload attempted authority upgrade")
        accepted = True
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:512]
    finally:
        try:
            pins.close_files()
        except Exception as exc:
            accepted = False
            error = "pin cleanup: " + str(exc)[:512]
    if time.monotonic() - began >= 90:
        accepted, error = False, "whole bound exceeded"
    if accepted:
        try:
            no_stop()
            no_cache()
            sample = primitive.live_resources(ROOT)
            if sample.available_ram_bytes < 4 * 1024**3 or sample.free_disk_bytes < 20 * 1024**3 or datetime.now(UTC) >= end:
                raise RuntimeError("final resource/admission predicate")
        except Exception as exc:
            accepted, error = False, "final acceptance: " + str(exc)[:512]
    receipt = {"schema": "cho51_p3_sysmon_recovery_receipt_v7", "accepted_by_runner": accepted,
               "error": error, "native_state": state, "startup_samples": samples,
               "result": None if result is None else dataclasses.asdict(result),
               "completed_utc": datetime.now(UTC).isoformat(), "elapsed_seconds": time.monotonic() - began,
               "actual_external_caller_return_pending": True, "independent_result_review_pending": True,
               "boundary_qualified": False, "launch_authorized": False, "scientific_admission": False}
    try:
        if out is not None:
            write(out / "receipt.json", receipt)
        print(json.dumps({"attempt": None if out is None else str(out), "accepted_by_runner": accepted, "error": error}))
    finally:
        # A failure here makes the actual caller exit nonzero, invalidating the
        # provisional receipt. Output namespace remains locked through writes.
        pins.close_directories()
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
