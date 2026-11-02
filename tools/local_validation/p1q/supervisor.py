"""Q4 supervisor. Fixed qualification only; no P/L/V/C command path."""
import ctypes
import dataclasses
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import types
import unittest
import unittest.mock
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).absolute().parents[3]
HERE = Path(__file__).absolute().parent
BASE = ROOT / "runs/coordination/cho51_p3_preparation_engine_20261029_p1q"
STOP = ROOT / "runs/coordination/PROJECT_STOP.json"
MAX_RECORD = 8 * 1024**2


def initial_json(raw):
    if type(raw) is not bytes or len(raw) > MAX_RECORD:
        raise ValueError("bootstrap record bound")
    def pairs(items):
        value = {}
        for key, entry in items:
            if key in value:
                raise ValueError("duplicate bootstrap JSON key")
            value[key] = entry
        return value
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_bound(path, cap=MAX_RECORD):
    with Path(path).open("rb") as stream:
        raw = stream.read(cap + 1)
    if len(raw) > cap:
        raise ValueError("bootstrap read cap")
    return raw


def module_bytes(name, path, raw, pin):
    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("bootstrap source byte mismatch")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def namespaces():
    for name in ("tools", "tools.local_validation", "tools.local_validation.v1", "tools.local_validation.p1q",
                 "tools.local_validation.q4", "tools.local_validation.p1"):
        if name not in sys.modules:
            mod = types.ModuleType(name)
            mod.__package__ = name
            mod.__path__ = []
            sys.modules[name] = mod


def load_source(request, name, relative, reader=None):
    path = ROOT / relative
    raw = read_bound(path) if reader is None else reader.read_small(path, request["sources"][relative])
    return module_bytes(name, path, raw, request["sources"][relative])


def absent(path):
    # Distinguish true missing leaf from permissions, missing ancestor or links.
    for ancestor in [*reversed(path.parent.parents), path.parent]:
        value = ancestor.lstat()
        if not ancestor.is_dir() or value.st_file_attributes & 1024:
            raise ValueError("absence ancestry unknown/reparse")
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("required absent path exists")


class _Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("faults", ctypes.c_uint32)] + [
        (name, ctypes.c_size_t) for name in ("peak_working", "working", "peak_paged",
        "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]


class Guard:
    def __init__(self, origin_utc, origin_qpc, frequency, cache):
        self.kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        self.psapi = ctypes.WinDLL("psapi.dll", use_last_error=True, winmode=0x800)
        self.kernel.QueryPerformanceCounter.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        self.kernel.QueryPerformanceCounter.restype = ctypes.c_int
        self.kernel.QueryPerformanceFrequency.argtypes = [ctypes.POINTER(ctypes.c_int64)]
        self.kernel.QueryPerformanceFrequency.restype = ctypes.c_int
        self.kernel.GlobalMemoryStatusEx.argtypes = [ctypes.c_void_p]
        self.kernel.GlobalMemoryStatusEx.restype = ctypes.c_int
        self.kernel.GetCurrentProcess.restype = ctypes.c_void_p
        self.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
        self.psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        actual = ctypes.c_int64()
        if not self.kernel.QueryPerformanceFrequency(ctypes.byref(actual)) or actual.value != frequency:
            raise ValueError("caller QPC domain differs")
        self.origin = datetime.fromisoformat(origin_utc.replace("Z", "+00:00"))
        if self.origin.utcoffset() != timedelta(0) or type(origin_qpc) is not int or origin_qpc <= 0:
            raise ValueError("caller origin refused")
        self.origin_qpc, self.frequency = origin_qpc, frequency
        self.cache = cache
        self.work_seconds = 60
        self.samples = 0
        self.min_ram = self.min_disk = 2**63 - 1
        self.max_private = 0
        self.started = time.monotonic()
        self.lock = threading.RLock()
        self.fault = None
        self.stop_watchdog = threading.Event()
        # Independent from test/native work. The outer caller also bounds this
        # supervisor and closes its original process handle after return.
        self.watchdog = threading.Thread(target=self.watch, daemon=True, name="Q-parent-watchdog")
        self.watchdog.start()

    def elapsed(self):
        now = ctypes.c_int64()
        if not self.kernel.QueryPerformanceCounter(ctypes.byref(now)):
            raise OSError(ctypes.get_last_error(), "QPC")
        elapsed = (now.value - self.origin_qpc) / self.frequency
        if elapsed < 0:
            raise ValueError("QPC moved before origin")
        return elapsed

    def sample(self):
        memory = ctypes.create_string_buffer(64)
        ctypes.c_uint32.from_buffer(memory).value = 64
        if not self.kernel.GlobalMemoryStatusEx(memory):
            raise OSError(ctypes.get_last_error(), "RAM sensor")
        available = ctypes.c_uint64.from_buffer(memory, 16).value
        free = shutil.disk_usage(ROOT).free
        counters = _Counters()
        counters.cb = ctypes.sizeof(counters)
        if not self.psapi.GetProcessMemoryInfo(self.kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "parent memory sensor")
        with self.lock:
            self.samples += 1
            self.min_ram = min(self.min_ram, available)
            self.min_disk = min(self.min_disk, free)
            self.max_private = max(self.max_private, counters.private)
        if available < 4 * 1024**3 or free < 20 * 1024**3 or counters.private > 512 * 1024**2:
            raise RuntimeError("resource floor or parent commit cap")
        return {"available_ram_bytes": available, "free_disk_bytes": free,
                "parent_private_bytes": counters.private, "elapsed_seconds": self.elapsed()}

    def checkpoint(self):
        if self.fault:
            raise RuntimeError(self.fault)
        if self.elapsed() >= self.work_seconds or datetime.now(timezone.utc) >= self.origin + timedelta(seconds=self.work_seconds):
            raise RuntimeError("original caller work deadline")
        absent(STOP)
        absent(self.cache)
        self.sample()
        return True

    def watch(self):
        while not self.stop_watchdog.wait(.1):
            try:
                if self.fault and time.monotonic() - getattr(self, '_fault_at', self.started) >= 5:
                    os._exit(125)
                elapsed = self.elapsed()
                if elapsed >= 65:
                    os._exit(124)  # owned Job dies on supervisor handle closure
                absent(STOP)
                absent(self.cache)
                self.sample()
                if elapsed >= 60:
                    self.fault = "work deadline"
                    self._fault_at = getattr(self, '_fault_at', time.monotonic())
            except BaseException as error:
                if self.fault is None:
                    self.fault = str(error)[:256]
                    first = time.monotonic()
                else:
                    first = getattr(self, "_fault_at", time.monotonic())
                self._fault_at = first
                if time.monotonic() - first >= 5:
                    os._exit(125)

    def summary(self):
        return {"sample_count": self.samples, "minimum_available_ram_bytes": self.min_ram,
                "minimum_free_disk_bytes": self.min_disk, "peak_parent_private_bytes": self.max_private,
                "elapsed_seconds": self.elapsed(), "guard_fault": self.fault}


def restrict(request, cache, fixture=None):
    allowed = {str((ROOT / p)).lower() for p in request["sources"]}
    allowed |= {str(Path(p)).lower() for p in request["runtime"]["files"]}
    # Only these metadata inputs are read outside the pinned source/runtime.
    allowed |= {str(BASE / n).lower() for n in ("source-review.json", "contract-adoption.json")}
    runtime_root = Path(request["runtime"]["root"])
    sys.path[:] = [str(runtime_root / "Lib"), str(runtime_root / "DLLs"), str(runtime_root)]
    write_root = None if fixture is None else str(fixture).lower()
    def inside(path):
        return write_root is not None and (path == write_root or path.startswith(write_root + os.sep))
    def audit(event, args):
        if event == "open":
            target = args[0]
            if type(target) is int:
                return  # original pipe/stdio descriptors, not a pathname
            text = str(Path(target).absolute()).lower()
            mode = args[1] or ""
            flags = args[2] or 0
            writing = any(c in mode for c in "wax+") or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writing:
                if not inside(text):
                    raise PermissionError("Q write outside owned fixtures")
            elif text not in allowed and not inside(text):
                # Fresh pycache absence permits an importlib cache miss only.
                if text.startswith(str(cache).lower() + os.sep) and not Path(target).exists():
                    return
                raise PermissionError("Q read outside pinned inputs")
        elif event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.__new__", "socket.connect", "os.symlink"}:
            raise PermissionError("Q forbidden effect: " + event)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.link"}:
            paths = args[:2] if event in {"os.rename", "os.link"} else args[:1]
            if not all(inside(str(Path(p).absolute()).lower()) for p in paths):
                raise PermissionError("Q filesystem effect outside fixture")
        elif event == "ctypes.dlopen":
            name = args[0]
            if name not in ("kernel32", "kernel32.dll", "psapi.dll", None):
                raise PermissionError("Q DLL outside declared Windows trust")
        elif event == "import" and len(args) > 1 and args[1]:
            path = str(Path(args[1]).absolute()).lower()
            if path not in allowed:
                raise PermissionError("Q import origin outside runtime pins")
    sys.addaudithook(audit)


def runtime_paths(root):
    """Exact Q base-runtime recipe; no package closure or loaded-image claim."""
    paths = {root / "python.exe"}
    paths.update(root.glob("*.dll"))
    for directory in (root / "Lib", root / "DLLs"):
        for current, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in ("site-packages", "__pycache__"))
            if len(Path(current).relative_to(root).parts) > 32:
                raise ValueError("runtime directory depth")
            for name in files:
                p = Path(current) / name
                if p.suffix.lower() in (".py", ".pyd", ".dll"):
                    paths.add(p)
                    if len(paths) > 2000:
                        raise ValueError("runtime count")
    return {p.as_posix() for p in paths}


def new_state():
    flags = ("limits_set", "limits_query_verified", "job_created", "created_suspended",
             "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned", "membership_verified",
             "resumed", "job_empty_before_close", "job_closed", "root_exit_after_job_close",
             "process_handle_closed", "thread_handle_closed", "assignment_step_seen", "owned_job_termination_called")
    value = {key: False for key in flags}
    value.update(peak_samples=0, peak_process_commit_bytes=0, peak_job_commit_bytes=0,
                 cleanup_errors=[], peak_sampling_errors=[])
    return value


def lifecycle_ok(state):
    required = ("atomic_job_assignment_verified", "limits_query_verified", "job_empty_before_close", "job_closed",
                "root_exit_after_job_close", "process_handle_closed", "thread_handle_closed",
                "result_reader_closed", "result_writer_closed")
    return all(state.get(k) is True for k in required) and not state["cleanup_errors"] and not state["peak_sampling_errors"]


def main(admission_path, admission_hash, origin_utc, origin_qpc, frequency):
    if sys.platform != "win32":
        raise ValueError("Windows Q required")
    admission_path = Path(admission_path)
    if admission_path.parent != BASE or not admission_path.name.startswith("admission_"):
        raise ValueError("admission namespace")
    raw = read_bound(admission_path)
    if hashlib.sha256(raw).hexdigest() != admission_hash:
        raise ValueError("admission caller hash")
    preliminary = initial_json(raw)
    operation = preliminary["operation_id"]
    cache = BASE / "disabled-bytecode" / operation
    guard = Guard(origin_utc, int(origin_qpc), int(frequency), cache)
    namespaces()
    records = load_source(preliminary, "tools.local_validation.v1.records", "tools/local_validation/v1/records.py")
    protocol = load_source(preliminary, "tools.local_validation.p1q.protocol", "tools/local_validation/p1q/protocol.py")
    request = protocol.validate_admission(records.strict_loads(raw), ROOT.as_posix(), origin_utc)
    native = load_source(request, "tools.local_validation.p1q.native_reader", "tools/local_validation/p1q/native_reader.py")
    reader = native.RetainedReader(guard.checkpoint, max_files=2000, max_total_bytes=64*1024**2, max_file_bytes=16*1024**2)
    outputs = None
    accepted = False
    error = None
    operations = []
    out = BASE / "attempts" / operation
    result_report = None
    handle_closure = {"outputs": False, "inputs": False}
    try:
        startup = []
        for index in range(2):
            guard.checkpoint()
            startup.append(guard.sample())
            if index == 0:
                time.sleep(.21)
        if sys.pycache_prefix != str(cache) or sys.flags.isolated != 1 or not sys.flags.no_site:
            raise ValueError("isolated fresh bytecode configuration required")
        reader.read_small(admission_path, {"bytes": len(raw), "sha256": admission_hash})
        for name, expected in request["sources"].items():
            reader.retain(ROOT / name, expected)
        for name, expected in request["runtime"]["files"].items():
            reader.retain(Path(name), expected)
        if Path(sys.executable).as_posix() != request["python"] or runtime_paths(Path(request["runtime"]["root"])) != set(request["runtime"]["files"]):
            raise ValueError("current exact runtime census")
        review = records.strict_loads(reader.read_small(BASE / request["review"]["path"], {k: request["review"][k] for k in ("bytes", "sha256")}))
        adoption = records.strict_loads(reader.read_small(BASE / request["adoption"]["path"], {k: request["adoption"][k] for k in ("bytes", "sha256")}))
        protocol.validate_chain(request, review, adoption)
        predecessor = request["predecessor"]
        reader.retain(ROOT / predecessor["path"], {k: predecessor[k] for k in ("bytes", "sha256")})
        reader.retain_directory(out.parent)
        absent(out)
        out.mkdir()
        reader.retain_directory(out)
        restrict(request, cache, out)
        outputs = native.RetainedOutputs(reader, out)
        outputs.write("claim.json", records.canonical_bytes({"schema": "cho51_q_claim_v1", "operation_id": operation,
                      "admission_sha256": admission_hash, "origin_utc": origin_utc, "origin_qpc": int(origin_qpc), "frequency": int(frequency)}))
        fixture = out / "fixtures"
        fixture.mkdir()
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"):
            os.environ.pop(key, None)
        os.environ.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1",
                          CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
        for mode in protocol.MODES:
            guard.checkpoint()
            primitive = load_source(request, "_q_primitive_" + mode, "evaluation/phase2_supervision_primitives.py", reader)
            adapter = load_source(request, "_q_adapter_" + mode, "tools/local_validation/p1q/job_adapter.py", reader)
            state = new_state()
            adapter.install_job_adapter(primitive, state, None)
            # All deadlines share the external origin. Fault probes are declared
            # controls, never automatic retries of the suite.
            remaining = 60 - guard.elapsed()
            seconds = min(40 if mode == "suite" else 2, remaining - 5)
            if seconds <= 0:
                raise ValueError("insufficient remaining work/cleanup")
            deadline = min(guard.origin + timedelta(seconds=60), datetime.now(timezone.utc) + timedelta(seconds=seconds))
            deadline_name = "deadline_" + mode + ".json"
            outputs.write(deadline_name, (json.dumps({"schema": "phase2_supervision_deadlines_v1",
                  "attempt_deadline_utc": deadline.isoformat(), "session_deadline_utc": deadline.isoformat()},
                  sort_keys=True, separators=(",", ":")) + "\n").encode())
            command = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + str(cache),
                       str(HERE / "child_entry.py"), str(admission_path), admission_hash, mode,
                       str(fixture), "{result_handle}", origin_utc, str(origin_qpc), str(frequency)]
            outputs.write("dispatch_" + mode + ".json", records.canonical_bytes({"schema": "cho51_q_dispatch_v1",
                "mode": mode, "command": command, "start_attempted": True, "custody_known_before_native_call": False}))
            observed, failure = None, None
            def sensor(path):
                guard.checkpoint()
                return primitive.live_resources(path)
            try:
                observed = primitive.run_supervised_with_frame(command, cwd=ROOT, deadline_path=out / deadline_name,
                    floor=primitive.ResourceFloor(ram_bytes=4*1024**3, disk_bytes=20*1024**3),
                    sensor=sensor, poll_seconds=.1, process_memory_limit_bytes=512*1024**2, max_frame_bytes=1048576)
            except Exception as exc:
                failure = type(exc).__name__ + ": " + str(exc)[:512]
            fact = {"mode": mode, "failure": failure, "state": state,
                    "result": None if observed is None else dataclasses.asdict(observed.result)}
            operations.append(fact)
            if not lifecycle_ok(state):
                raise ValueError("owned lifecycle incomplete: " + mode)
            if mode == "suite":
                if failure or observed is None:
                    raise ValueError("suite failed: " + str(failure))
                result_report = records.strict_loads(observed.frame)
                outputs.write("test-report.json", observed.frame)
                protocol.validate_report(result_report, request["expected_tests"], operation)
            elif mode == "badframe":
                if observed is not None or not failure or "extra bytes" not in failure:
                    raise ValueError("malformed-frame control did not refuse as specified")
            elif mode == "stall":
                if observed is not None or not failure or "deadline" not in failure or not state["owned_job_termination_called"]:
                    raise ValueError("timeout control did not terminate owned Job")
        reader.verify()
        if runtime_paths(Path(request["runtime"]["root"])) != set(request["runtime"]["files"]):
            raise ValueError("runtime census drift")
        guard.checkpoint()
        outputs.verify()
        outputs.write("payload.json", records.canonical_bytes({"schema": "cho51_q_payload_v1",
            "operation_id": operation, "startup_samples": startup, "operations": operations,
            "foundation_tests": 31, "expected_suite_count": len(request["expected_tests"]),
            "actual_supervisor_fault_controls": 2, "native_reparse_fixture_qualified": False,
            "full_26_scenario_matrix_completed": False, **protocol.FALSES}))
        accepted = True
    except BaseException as exc:
        error = type(exc).__name__ + ": " + str(exc)[:768]
        reader.checkpoint = lambda: True
    finally:
        try:
            if outputs is not None:
                outputs.write("receipt.json", records.canonical_bytes({"schema": "cho51_q_receipt_v1",
                    "operation_id": operation, "accepted_by_supervisor": accepted, "error": error,
                    "operations": operations, "resources": guard.summary(),
                    "external_caller_return_pending": True, "independent_actual_review_pending": True,
                    "original_handle_closure_pending": True, **protocol.FALSES}))
                outputs.verify()
                outputs.close()
                handle_closure["outputs"] = True
        finally:
            reader.close()
            handle_closure["inputs"] = True
            guard.stop_watchdog.set()
    # Caller retains this bounded stream separately: receipt pending flags are
    # resolved by that independent evidence, not rewritten after handle close.
    print(json.dumps({"schema": "cho51_q_supervisor_return_v1", "operation_id": operation,
                      "accepted_by_supervisor": accepted, "error": error, "handle_closure": handle_closure,
                      "resources": guard.summary(), **protocol.FALSES}, allow_nan=False))
    return 0 if accepted else 1

