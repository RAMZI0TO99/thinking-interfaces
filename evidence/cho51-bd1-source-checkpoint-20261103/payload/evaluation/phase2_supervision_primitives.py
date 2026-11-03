"""Windows-only, fail-closed supervision for one external process tree.

This is a process primitive, not a Cho case runner. The caller owns the case
contract, per-case lock, proposal validation, GPU checks, and record publication.
Only a process created here is placed in the private Job Object and stopped.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Sequence
from ctypes import wintypes
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

GIB = 1024**3
MAX_ATTEMPT_SECONDS = 10 * 60
MAX_SESSION_SECONDS = 120 * 60
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002
HANDLE_FLAG_INHERIT = 0x00000001
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_BROKEN_PIPE = 109
ERROR_NO_DATA = 232
ERROR_NOT_FOUND = 1168
THREAD_TERMINATE = 0x0001
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS = 1
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF
STILL_ACTIVE = 259
ERROR_TERMINATED = 1
StopReason = Literal["normal", "attempt_deadline", "session_deadline", "disk_floor", "ram_floor"]


class SupervisionError(RuntimeError):
    """A required Windows operation or live sensor failed; no success is attestable."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc(value: datetime) -> datetime:
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError("supervision deadlines must be timezone-aware UTC")
    if offset.total_seconds() != 0:
        raise ValueError("supervision deadlines must be in UTC")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class DeadlineLease:
    """Two immutable UTC deadlines loaded from a write-once local record."""

    attempt_deadline_utc: datetime
    session_deadline_utc: datetime

    @classmethod
    def open_or_create(
        cls, path: Path, *, attempt_deadline_utc: datetime, session_deadline_utc: datetime
    ) -> DeadlineLease:
        attempt = _utc(attempt_deadline_utc)
        session = _utc(session_deadline_utc)
        now = _utc_now()
        if attempt > session:
            raise ValueError("attempt deadline cannot exceed session deadline")
        if (
            (attempt - now).total_seconds() > MAX_ATTEMPT_SECONDS
            or (session - now).total_seconds() > MAX_SESSION_SECONDS
        ):
            raise ValueError("Phase II attempt/session cap exceeded")
        lease = cls(attempt, session)
        contents = (
            json.dumps(
                {
                    "schema": "phase2_supervision_deadlines_v1",
                    "attempt_deadline_utc": attempt.isoformat(),
                    "session_deadline_utc": session.isoformat(),
                },
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n"
        ).encode("utf-8")
        if not path.parent.is_dir() or path.parent.is_symlink():
            raise ValueError("deadline parent must be an existing ordinary directory")
        if path.is_symlink():
            raise ValueError("deadline path cannot be a link")
        try:
            with path.open("xb") as stream:
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            existing = cls.load(path)
            if existing != lease or path.read_bytes() != contents:
                raise ValueError("persisted deadline differs from proposed deadline") from None
        return cls.load(path)

    @classmethod
    def load(cls, path: Path) -> DeadlineLease:
        if path.is_symlink() or not path.is_file():
            raise ValueError("deadline record missing or linked")
        try:
            raw = path.read_bytes()
            obj = json.loads(raw)
            if not isinstance(obj, dict) or set(obj) != {
                "schema", "attempt_deadline_utc", "session_deadline_utc"
            } or obj["schema"] != "phase2_supervision_deadlines_v1":
                raise ValueError("deadline record has unexpected schema")
            attempt = _utc(datetime.fromisoformat(obj["attempt_deadline_utc"]))
            session = _utc(datetime.fromisoformat(obj["session_deadline_utc"]))
            if attempt > session:
                raise ValueError("attempt deadline exceeds session deadline")
            canonical = (
                json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            if raw != canonical:
                raise ValueError("deadline record is not canonical")
        except (OSError, UnicodeDecodeError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError("deadline record is unreadable") from exc
        return cls(attempt, session)


@dataclass(frozen=True, slots=True)
class ResourceSample:
    free_disk_bytes: int
    available_ram_bytes: int


@dataclass(frozen=True, slots=True)
class ResourceFloor:
    disk_bytes: int = 20 * GIB
    ram_bytes: int = 4 * GIB

    def __post_init__(self) -> None:
        if (
            type(self.disk_bytes) is not int
            or type(self.ram_bytes) is not int
            or self.disk_bytes < 20 * GIB
            or self.ram_bytes < 4 * GIB
        ):
            raise ValueError("Phase II live floors cannot be weakened")


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def live_resources(root: Path) -> ResourceSample:
    """Read Windows physical RAM and filesystem free bytes; propagate sensor errors."""
    if sys.platform != "win32":
        raise SupervisionError("Windows live resource sensor required")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    memory = _MemoryStatusEx()
    memory.dwLength = ctypes.sizeof(memory)
    function = kernel.GlobalMemoryStatusEx
    function.argtypes = [ctypes.POINTER(_MemoryStatusEx)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(memory)):
        raise SupervisionError(f"GlobalMemoryStatusEx failed: {ctypes.get_last_error()}")
    free_disk = shutil.disk_usage(root).free
    return ResourceSample(int(free_disk), int(memory.ullAvailPhys))


class _BasicLimit(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
    )]


class _ExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimit),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _AccountingInfo(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [
        ("StartupInfo", _StartupInfo),
        ("lpAttributeList", ctypes.c_void_p),
    ]


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL),
    ]


class _ProcessInfo(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


class _WinApi:
    def __init__(self) -> None:
        if sys.platform != "win32":
            raise SupervisionError("Windows Job Objects are required")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.create_job = kernel.CreateJobObjectW
        self.create_job.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.create_job.restype = wintypes.HANDLE
        self.set_job = kernel.SetInformationJobObject
        self.set_job.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.set_job.restype = wintypes.BOOL
        self.query_job = kernel.QueryInformationJobObject
        self.query_job.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.query_job.restype = wintypes.BOOL
        self.create_process = kernel.CreateProcessW
        self.create_process.argtypes = [
            wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
            wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
            ctypes.POINTER(_StartupInfo), ctypes.POINTER(_ProcessInfo),
        ]
        self.create_process.restype = wintypes.BOOL
        self.assign = kernel.AssignProcessToJobObject
        self.assign.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.assign.restype = wintypes.BOOL
        self.in_job = kernel.IsProcessInJob
        self.in_job.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
        self.in_job.restype = wintypes.BOOL
        self.resume = kernel.ResumeThread
        self.resume.argtypes = [wintypes.HANDLE]
        self.resume.restype = wintypes.DWORD
        self.wait = kernel.WaitForSingleObject
        self.wait.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.wait.restype = wintypes.DWORD
        self.exit_code = kernel.GetExitCodeProcess
        self.exit_code.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.exit_code.restype = wintypes.BOOL
        self.terminate_job = kernel.TerminateJobObject
        self.terminate_job.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.terminate_job.restype = wintypes.BOOL
        self.terminate_process = kernel.TerminateProcess
        self.terminate_process.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.terminate_process.restype = wintypes.BOOL
        self.close = kernel.CloseHandle
        self.close.argtypes = [wintypes.HANDLE]
        self.close.restype = wintypes.BOOL


class _FrameWinApi(_WinApi):
    def __init__(self) -> None:
        super().__init__()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.create_pipe = kernel.CreatePipe
        self.create_pipe.argtypes = [
            ctypes.POINTER(wintypes.HANDLE), ctypes.POINTER(wintypes.HANDLE),
            ctypes.POINTER(_SecurityAttributes), wintypes.DWORD,
        ]
        self.create_pipe.restype = wintypes.BOOL
        self.set_handle = kernel.SetHandleInformation
        self.set_handle.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
        self.set_handle.restype = wintypes.BOOL
        self.init_attributes = kernel.InitializeProcThreadAttributeList
        self.init_attributes.argtypes = [
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t),
        ]
        self.init_attributes.restype = wintypes.BOOL
        self.update_attribute = kernel.UpdateProcThreadAttribute
        self.update_attribute.argtypes = [
            ctypes.c_void_p, wintypes.DWORD, ctypes.c_size_t, ctypes.c_void_p,
            ctypes.c_size_t, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
        ]
        self.update_attribute.restype = wintypes.BOOL
        self.delete_attributes = kernel.DeleteProcThreadAttributeList
        self.delete_attributes.argtypes = [ctypes.c_void_p]
        self.delete_attributes.restype = None
        self.read_file = kernel.ReadFile
        self.read_file.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
        ]
        self.read_file.restype = wintypes.BOOL
        self.open_thread = kernel.OpenThread
        self.open_thread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.open_thread.restype = wintypes.HANDLE
        self.cancel_sync_io = kernel.CancelSynchronousIo
        self.cancel_sync_io.argtypes = [wintypes.HANDLE]
        self.cancel_sync_io.restype = wintypes.BOOL


def _error(operation: str) -> SupervisionError:
    return SupervisionError(f"{operation} failed: Windows error {ctypes.get_last_error()}")


def _active_processes(api: _WinApi, job: wintypes.HANDLE) -> int:
    accounting = _AccountingInfo()
    if not api.query_job(
        job, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION_CLASS,
        ctypes.byref(accounting), ctypes.sizeof(accounting), None,
    ):
        raise _error("QueryInformationJobObject(accounting)")
    if accounting.TotalProcesses < accounting.ActiveProcesses:
        raise SupervisionError("Job Object accounting is inconsistent")
    return int(accounting.ActiveProcesses)


def _wait_for_empty_job(api: _WinApi, job: wintypes.HANDLE, seconds: float = 2.0) -> None:
    until = time.monotonic() + seconds
    while True:
        if _active_processes(api, job) == 0:
            return
        if time.monotonic() >= until:
            raise SupervisionError("owned Job Object still has active processes after termination")
        time.sleep(0.02)


def _sample_or_fail(
    root: Path, sensor: Callable[[Path], ResourceSample], floor: ResourceFloor
) -> Literal["disk_floor", "ram_floor"] | None:
    try:
        sample = sensor(root)
    except Exception as exc:
        raise SupervisionError("live disk/RAM sensor failed") from exc
    if (
        type(sample.free_disk_bytes) is not int
        or type(sample.available_ram_bytes) is not int
        or sample.free_disk_bytes < 0
        or sample.available_ram_bytes < 0
    ):
        raise SupervisionError("live disk/RAM sensor returned invalid values")
    if sample.free_disk_bytes < floor.disk_bytes:
        return "disk_floor"
    if sample.available_ram_bytes < floor.ram_bytes:
        return "ram_floor"
    return None


def _validated_process_memory_limit(limit: int | None) -> int | None:
    if limit is None:
        return None
    if type(limit) is not int or not 0 < limit <= 2**48:
        raise ValueError("process memory limit must be a positive int below 2**48")
    return limit


def _set_job_limits(
    api: _WinApi, job: wintypes.HANDLE, process_memory_limit_bytes: int | None,
) -> None:
    """Set and query-back-verify kill-on-close plus an optional commit cap."""
    limits = _ExtendedLimit()
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if process_memory_limit_bytes is not None:
        limits.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_PROCESS_MEMORY
        limits.ProcessMemoryLimit = process_memory_limit_bytes
    if not api.set_job(
        job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
        ctypes.byref(limits), ctypes.sizeof(limits),
    ):
        raise _error("SetInformationJobObject")
    observed = _ExtendedLimit()
    if (
        not api.query_job(
            job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(observed), ctypes.sizeof(observed), None,
        )
        or observed.BasicLimitInformation.LimitFlags
        != limits.BasicLimitInformation.LimitFlags
    ):
        raise SupervisionError("kill-on-close Job Object limit not verified")
    if (
        process_memory_limit_bytes is not None
        and observed.ProcessMemoryLimit != process_memory_limit_bytes
    ):
        raise SupervisionError("process memory Job Object limit not verified")


def _job_memory_peaks(api: _WinApi, job: wintypes.HANDLE) -> tuple[int, int]:
    """Sample the job's current peak counters.

    Windows can reset both peaks once the job's process count returns to
    zero, and the supervision loop observes completion only after the job is
    empty, so callers must accumulate maxima while the child runs.
    """
    observed = _ExtendedLimit()
    if not api.query_job(
        job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
        ctypes.byref(observed), ctypes.sizeof(observed), None,
    ):
        raise _error("QueryInformationJobObject(memory peaks)")
    return int(observed.PeakProcessMemoryUsed), int(observed.PeakJobMemoryUsed)


@dataclass(frozen=True, slots=True)
class SupervisionResult:
    pid: int
    exit_code: int
    reason: StopReason
    peak_process_memory_bytes: int | None = None
    peak_job_memory_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class FramedSupervisionResult:
    """A successful whole-Job result and its single bounded child frame."""

    result: SupervisionResult
    frame: bytes


@dataclass(slots=True)
class _FrameState:
    done: threading.Event = field(default_factory=threading.Event)
    frame: bytes | None = None
    error: SupervisionError | None = None
    finished_utc: datetime | None = None
    finished_mono: float | None = None


def _read_single_frame(
    api: _FrameWinApi, pipe: wintypes.HANDLE, max_frame_bytes: int, state: _FrameState
) -> None:
    """Read through EOF with a strict bound; the caller cancels a blocked read."""
    raw = bytearray()
    expected: int | None = None
    try:
        while True:
            # One surplus byte is enough to reject a duplicate or trailing data.
            remaining = (4 + max_frame_bytes + 1) - len(raw)
            if remaining <= 0:
                raise SupervisionError("result frame contains extra bytes")
            buffer = ctypes.create_string_buffer(min(4096, remaining))
            count = wintypes.DWORD()
            if not api.read_file(pipe, buffer, len(buffer), ctypes.byref(count), None):
                error = ctypes.get_last_error()
                if error in (ERROR_BROKEN_PIPE, ERROR_NO_DATA):
                    break
                raise SupervisionError(f"result frame ReadFile failed: Windows error {error}")
            if count.value == 0:
                break
            raw.extend(buffer.raw[:count.value])
            if len(raw) >= 4 and expected is None:
                expected = int.from_bytes(raw[:4], "little")
                if expected > max_frame_bytes:
                    raise SupervisionError("result frame exceeds size limit")
            if expected is not None and len(raw) > 4 + expected:
                raise SupervisionError("result frame contains extra bytes")
        if len(raw) < 4:
            raise SupervisionError("result frame missing or truncated header")
        if expected is None or len(raw) != 4 + expected:
            raise SupervisionError("result frame payload truncated")
        state.frame = bytes(raw[4:])
    except SupervisionError as exc:
        state.error = exc
    except Exception as exc:
        state.error = SupervisionError(f"result frame reader failed: {exc}")
    finally:
        state.finished_utc = _utc_now()
        state.finished_mono = time.monotonic()
        state.done.set()


def _cancel_frame_reader(api: _FrameWinApi, reader: threading.Thread) -> None:
    """Cancel a synchronous ReadFile and join only for a fixed short period."""
    if not reader.is_alive():
        reader.join(timeout=0.1)
        return
    native_id = reader.native_id
    if native_id is None:
        raise SupervisionError("result frame reader has no native thread ID")
    thread_handle = api.open_thread(THREAD_TERMINATE, False, native_id)
    if not thread_handle:
        raise _error("OpenThread(frame reader)")
    try:
        if not api.cancel_sync_io(thread_handle):
            error = ctypes.get_last_error()
            if error != ERROR_NOT_FOUND:
                raise SupervisionError(
                    f"result frame CancelSynchronousIo failed: Windows error {error}"
                )
    finally:
        api.close(thread_handle)
    reader.join(timeout=1.0)
    if reader.is_alive():
        raise SupervisionError("result frame reader did not stop after cancellation")


def run_supervised(
    command: Sequence[str], *, cwd: Path, deadline_path: Path,
    floor: ResourceFloor | None = None,
    sensor: Callable[[Path], ResourceSample] = live_resources,
    poll_seconds: float = 0.1,
    process_memory_limit_bytes: int | None = None,
) -> SupervisionResult:
    """Launch suspended, assign to a private kill-on-close job, then resume.

    The caller must persist the lease before this call. The lease is reloaded
    from disk, so a restarted caller cannot pass a later in-memory deadline.
    ``process_memory_limit_bytes``, when supplied, additionally bounds the
    child's commit charge through a query-back-verified
    ``JOB_OBJECT_LIMIT_PROCESS_MEMORY`` limit; the measured peaks are returned
    on the result. Raises SupervisionError on a failed Windows API or sensor
    read. In all such paths, the owned child is never resumed unassigned and
    an assigned tree is killed by closing the noninherited job handle.
    """
    if sys.platform != "win32":
        raise SupervisionError("Windows Job Objects are required")
    if not command or any(not isinstance(arg, str) or "\x00" in arg for arg in command):
        raise ValueError("command must be nonempty NUL-free strings")
    executable = Path(command[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError("command executable must be an existing absolute file")
    if not cwd.is_dir() or not math.isfinite(poll_seconds) or not 0 < poll_seconds <= 5:
        raise ValueError("invalid working directory or poll interval")
    floor = ResourceFloor() if floor is None else floor
    lease = DeadlineLease.load(deadline_path)
    now = _utc_now()
    if now >= lease.attempt_deadline_utc:
        raise SupervisionError("persisted attempt deadline already expired")
    if now >= lease.session_deadline_utc:
        raise SupervisionError("persisted session deadline already expired")
    if (
        (lease.attempt_deadline_utc - now).total_seconds() > MAX_ATTEMPT_SECONDS
        or (lease.session_deadline_utc - now).total_seconds() > MAX_SESSION_SECONDS
    ):
        raise SupervisionError("persisted deadline exceeds Phase II cap")
    preflight = _sample_or_fail(cwd, sensor, floor)
    if preflight is not None:
        raise SupervisionError(f"prelaunch {preflight} guard failed")
    memory_limit = _validated_process_memory_limit(process_memory_limit_bytes)
    api = _WinApi()
    job = api.create_job(None, None)
    if not job:
        raise _error("CreateJobObjectW")
    process = wintypes.HANDLE()
    thread = wintypes.HANDLE()
    assigned = False
    pid = 0
    try:
        _set_job_limits(api, job, memory_limit)
        before_start = _utc_now()
        if before_start >= lease.attempt_deadline_utc or before_start >= lease.session_deadline_utc:
            raise SupervisionError("persisted deadline expired before process creation")
        if (prestart := _sample_or_fail(cwd, sensor, floor)) is not None:
            raise SupervisionError(f"prelaunch {prestart} guard failed")
        startup = _StartupInfo()
        startup.cb = ctypes.sizeof(startup)
        info = _ProcessInfo()
        cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline(list(command)))
        if not api.create_process(
            str(executable), cmdline, None, None, False,
            CREATE_SUSPENDED | CREATE_NO_WINDOW, None, str(cwd),
            ctypes.byref(startup), ctypes.byref(info),
        ):
            raise _error("CreateProcessW")
        process, thread, pid = info.hProcess, info.hThread, int(info.dwProcessId)
        if not api.assign(job, process):
            raise _error("AssignProcessToJobObject")
        assigned = True
        in_job = wintypes.BOOL()
        if not api.in_job(process, job, ctypes.byref(in_job)) or not in_job.value:
            raise SupervisionError("owned process Job Object assignment not verified")
        if (pre_resume := _sample_or_fail(cwd, sensor, floor)) is not None:
            raise SupervisionError(f"pre-resume {pre_resume} guard failed")
        start_utc = _utc_now()
        start_mono = time.monotonic()
        if start_utc >= lease.attempt_deadline_utc or start_utc >= lease.session_deadline_utc:
            raise SupervisionError("persisted deadline expired before resume")
        attempt_mono = start_mono + (lease.attempt_deadline_utc - start_utc).total_seconds()
        session_mono = start_mono + (lease.session_deadline_utc - start_utc).total_seconds()
        if api.resume(thread) == WAIT_FAILED:
            raise _error("ResumeThread")
        reason: StopReason = "normal"
        root_exited = False
        peak_process = 0
        peak_job = 0
        while True:
            current_utc = _utc_now()
            current_mono = time.monotonic()
            if current_utc >= lease.session_deadline_utc or current_mono >= session_mono:
                reason = "session_deadline"
                break
            if current_utc >= lease.attempt_deadline_utc or current_mono >= attempt_mono:
                reason = "attempt_deadline"
                break
            guard = _sample_or_fail(cwd, sensor, floor)
            if guard is not None:
                reason = guard
                break
            if memory_limit is not None:
                peaks = _job_memory_peaks(api, job)
                peak_process = max(peak_process, peaks[0])
                peak_job = max(peak_job, peaks[1])
            if _active_processes(api, job) == 0:
                # A successful root exit is insufficient while a descendant runs.
                completed_utc = _utc_now()
                completed_mono = time.monotonic()
                if completed_utc >= lease.session_deadline_utc or completed_mono >= session_mono:
                    reason = "session_deadline"
                elif completed_utc >= lease.attempt_deadline_utc or completed_mono >= attempt_mono:
                    reason = "attempt_deadline"
                else:
                    status = api.wait(process, 0)
                    if status != WAIT_OBJECT_0:
                        raise SupervisionError(
                            "Job Object empty before root process exit was observed"
                        )
                    final_guard = _sample_or_fail(cwd, sensor, floor)
                    if final_guard is not None:
                        reason = final_guard
                break
            wait_ms = max(1, min(
                math.ceil(poll_seconds * 1000),
                math.ceil((attempt_mono - current_mono) * 1000),
                math.ceil((session_mono - current_mono) * 1000),
            ))
            if root_exited:
                time.sleep(wait_ms / 1000)
            else:
                status = api.wait(process, wait_ms)
                if status == WAIT_OBJECT_0:
                    root_exited = True
                elif status != WAIT_TIMEOUT:
                    raise _error("WaitForSingleObject")
        if memory_limit is not None:
            # The job may still hold the root on a guard or deadline stop.
            peaks = _job_memory_peaks(api, job)
            peak_process = max(peak_process, peaks[0])
            peak_job = max(peak_job, peaks[1])
        if reason != "normal":
            if not api.terminate_job(job, ERROR_TERMINATED):
                raise _error("TerminateJobObject")
            if api.wait(process, 2000) != WAIT_OBJECT_0:
                raise SupervisionError("owned child did not exit after Job Object termination")
            _wait_for_empty_job(api, job)
        exit_code = wintypes.DWORD()
        if not api.exit_code(process, ctypes.byref(exit_code)):
            raise _error("GetExitCodeProcess")
        if exit_code.value == STILL_ACTIVE:
            raise SupervisionError("owned process still active after completion")
        if DeadlineLease.load(deadline_path) != lease:
            raise SupervisionError("persisted deadline changed during child execution")
        result = SupervisionResult(
            pid, int(exit_code.value), reason,
            None if memory_limit is None else peak_process,
            None if memory_limit is None else peak_job,
        )
    finally:
        cleanup_error: SupervisionError | None = None
        if process and not assigned:
            # A suspended child is never allowed to run without the job.
            if not api.terminate_process(process, ERROR_TERMINATED):
                cleanup_error = _error("TerminateProcess(unassigned child)")
            if api.wait(process, 2000) != WAIT_OBJECT_0:
                cleanup_error = SupervisionError("unassigned suspended child did not exit")
        if thread and not api.close(thread):
            cleanup_error = _error("CloseHandle(thread)")
        if job and not api.close(job):
            cleanup_error = _error("CloseHandle(Job Object)")
            api.terminate_job(job, ERROR_TERMINATED)
            api.close(job)
        if process and assigned and api.wait(process, 2000) != WAIT_OBJECT_0:
            cleanup_error = SupervisionError("owned child survived Job Object close")
        if process and not api.close(process):
            cleanup_error = _error("CloseHandle(process)")
        if cleanup_error is not None:
            raise cleanup_error
    if result.reason == "normal":
        # A final sensor read or Windows cleanup can cross a deadline after the
        # Job Object has become empty. Never attest that path as timely.
        finished_utc = _utc_now()
        finished_mono = time.monotonic()
        if finished_utc >= lease.session_deadline_utc or finished_mono >= session_mono:
            return SupervisionResult(result.pid, result.exit_code, "session_deadline")
        if finished_utc >= lease.attempt_deadline_utc or finished_mono >= attempt_mono:
            return SupervisionResult(result.pid, result.exit_code, "attempt_deadline")
    return result


def run_supervised_with_frame(
    command: Sequence[str], *, cwd: Path, deadline_path: Path,
    floor: ResourceFloor | None = None,
    sensor: Callable[[Path], ResourceSample] = live_resources,
    poll_seconds: float = 0.1,
    process_memory_limit_bytes: int | None = None,
    max_frame_bytes: int = 16384,
) -> FramedSupervisionResult:
    """Run one owned Windows Job and receive exactly one child result frame.

    The command must contain one literal ``{result_handle}`` argument. It is
    replaced with the sole inheritable HANDLE in this child's handle list.
    ``process_memory_limit_bytes`` additionally bounds the child's commit
    charge through a query-back-verified process-memory Job limit, with the
    measured peaks returned on the embedded result. Any process, protocol,
    deadline, or sensor failure raises and kills the owned Job; no result
    frame is attestable on that path.
    """
    if sys.platform != "win32":
        raise SupervisionError("Windows Job Objects are required")
    if not command or any(not isinstance(arg, str) or "\x00" in arg for arg in command):
        raise ValueError("command must be nonempty NUL-free strings")
    if sum(arg == "{result_handle}" for arg in command) != 1:
        raise ValueError("command needs exactly one literal {result_handle} argument")
    if any("{result_handle}" in arg and arg != "{result_handle}" for arg in command):
        raise ValueError("result handle placeholder must be a whole argument")
    executable = Path(command[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ValueError("command executable must be an existing absolute file")
    if not cwd.is_dir() or not math.isfinite(poll_seconds) or not 0 < poll_seconds <= 5:
        raise ValueError("invalid working directory or poll interval")
    if type(max_frame_bytes) is not int or not 0 <= max_frame_bytes <= 16 * 1024 * 1024:
        raise ValueError("invalid result frame size limit")
    memory_limit = _validated_process_memory_limit(process_memory_limit_bytes)
    floor = ResourceFloor() if floor is None else floor
    lease = DeadlineLease.load(deadline_path)
    now = _utc_now()
    if now >= lease.attempt_deadline_utc or now >= lease.session_deadline_utc:
        raise SupervisionError("persisted result frame deadline already expired")
    if (
        (lease.attempt_deadline_utc - now).total_seconds() > MAX_ATTEMPT_SECONDS
        or (lease.session_deadline_utc - now).total_seconds() > MAX_SESSION_SECONDS
    ):
        raise SupervisionError("persisted result frame deadline exceeds Phase II cap")
    if (preflight := _sample_or_fail(cwd, sensor, floor)) is not None:
        raise SupervisionError(f"prelaunch result frame {preflight} guard failed")

    api = _FrameWinApi()
    job = api.create_job(None, None)
    if not job:
        raise _error("CreateJobObjectW")
    process = wintypes.HANDLE()
    child_thread = wintypes.HANDLE()
    read_pipe = wintypes.HANDLE()
    write_pipe = wintypes.HANDLE()
    attribute_buffer: ctypes.Array[ctypes.c_char] | None = None
    attribute_initialized = False
    assigned = False
    completed = False
    reader: threading.Thread | None = None
    state = _FrameState()
    pid = 0
    exit_value = 0
    frame = b""
    peak_process = 0
    peak_job = 0
    start_mono = 0.0
    attempt_mono = 0.0
    session_mono = 0.0
    try:
        _set_job_limits(api, job, memory_limit)

        security = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), None, False)
        if not api.create_pipe(
            ctypes.byref(read_pipe), ctypes.byref(write_pipe), ctypes.byref(security), 0
        ):
            raise _error("CreatePipe(result frame)")
        # The explicit child handle list includes just the pipe writer. Build
        # it before making that handle inheritable to narrow the race window.
        attribute_size = ctypes.c_size_t()
        if (
            api.init_attributes(None, 1, 0, ctypes.byref(attribute_size))
            or ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER
            or attribute_size.value == 0
        ):
            raise _error("InitializeProcThreadAttributeList(size)")
        attribute_buffer = ctypes.create_string_buffer(attribute_size.value)
        attribute_ptr = ctypes.cast(attribute_buffer, ctypes.c_void_p)
        if not api.init_attributes(attribute_ptr, 1, 0, ctypes.byref(attribute_size)):
            raise _error("InitializeProcThreadAttributeList")
        attribute_initialized = True
        handle_list = (wintypes.HANDLE * 1)(write_pipe)
        if not api.update_attribute(
            attribute_ptr, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            ctypes.cast(handle_list, ctypes.c_void_p), ctypes.sizeof(handle_list), None, None,
        ):
            raise _error("UpdateProcThreadAttribute(result handle list)")
        before_start = _utc_now()
        if before_start >= lease.attempt_deadline_utc or before_start >= lease.session_deadline_utc:
            raise SupervisionError("persisted result frame deadline expired before creation")
        if (prestart := _sample_or_fail(cwd, sensor, floor)) is not None:
            raise SupervisionError(f"prelaunch result frame {prestart} guard failed")
        startup = _StartupInfoEx()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = attribute_ptr
        info = _ProcessInfo()
        launch_command = [
            str(write_pipe.value) if arg == "{result_handle}" else arg for arg in command
        ]
        cmdline = ctypes.create_unicode_buffer(subprocess.list2cmdline(launch_command))
        if not api.set_handle(write_pipe, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT):
            raise _error("SetHandleInformation(result writer)")
        if not api.create_process(
            str(executable), cmdline, None, None, True,
            CREATE_SUSPENDED | CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT,
            None, str(cwd), ctypes.cast(ctypes.byref(startup), ctypes.POINTER(_StartupInfo)),
            ctypes.byref(info),
        ):
            raise _error("CreateProcessW(result frame)")
        process, child_thread, pid = info.hProcess, info.hThread, int(info.dwProcessId)
        # Parent's writer must close before child resume, so EOF can be
        # observed once all job members close the inherited writer.
        if not api.close(write_pipe):
            raise _error("CloseHandle(parent result writer)")
        write_pipe = wintypes.HANDLE()
        if not api.assign(job, process):
            raise _error("AssignProcessToJobObject")
        assigned = True
        in_job = wintypes.BOOL()
        if not api.in_job(process, job, ctypes.byref(in_job)) or not in_job.value:
            raise SupervisionError("owned result process Job Object assignment not verified")
        if (pre_resume := _sample_or_fail(cwd, sensor, floor)) is not None:
            raise SupervisionError(f"pre-resume result frame {pre_resume} guard failed")
        start_utc = _utc_now()
        start_mono = time.monotonic()
        if start_utc >= lease.attempt_deadline_utc or start_utc >= lease.session_deadline_utc:
            raise SupervisionError("persisted result frame deadline expired before resume")
        attempt_mono = start_mono + (lease.attempt_deadline_utc - start_utc).total_seconds()
        session_mono = start_mono + (lease.session_deadline_utc - start_utc).total_seconds()
        reader = threading.Thread(
            target=_read_single_frame, args=(api, read_pipe, max_frame_bytes, state),
            name="phase2-result-frame-reader", daemon=True,
        )
        reader.start()
        if api.resume(child_thread) == WAIT_FAILED:
            raise _error("ResumeThread(result process)")
        root_exited = False
        while True:
            current_utc = _utc_now()
            current_mono = time.monotonic()
            if current_utc >= lease.session_deadline_utc or current_mono >= session_mono:
                raise SupervisionError("result frame session_deadline")
            if current_utc >= lease.attempt_deadline_utc or current_mono >= attempt_mono:
                raise SupervisionError("result frame attempt_deadline")
            if (guard := _sample_or_fail(cwd, sensor, floor)) is not None:
                raise SupervisionError(f"result frame {guard} guard failed")
            if memory_limit is not None:
                peaks = _job_memory_peaks(api, job)
                peak_process = max(peak_process, peaks[0])
                peak_job = max(peak_job, peaks[1])
            if state.done.is_set() and state.error is not None:
                raise state.error
            if _active_processes(api, job) == 0 and state.done.is_set():
                break
            wait_ms = max(1, min(
                math.ceil(poll_seconds * 1000),
                math.ceil((attempt_mono - current_mono) * 1000),
                math.ceil((session_mono - current_mono) * 1000),
            ))
            if root_exited:
                state.done.wait(wait_ms / 1000)
            else:
                status = api.wait(process, wait_ms)
                if status == WAIT_OBJECT_0:
                    root_exited = True
                elif status != WAIT_TIMEOUT:
                    raise _error("WaitForSingleObject(result process)")
        if memory_limit is not None:
            # The job is normally empty at this break, so this usually reads
            # reset zeros; it exists to catch the still-running edge.
            peaks = _job_memory_peaks(api, job)
            peak_process = max(peak_process, peaks[0])
            peak_job = max(peak_job, peaks[1])
        if api.wait(process, 0) != WAIT_OBJECT_0:
            raise SupervisionError("result frame Job empty before root exit observed")
        if state.error is not None:
            raise state.error
        if state.frame is None or state.finished_utc is None or state.finished_mono is None:
            raise SupervisionError("result frame reader did not complete")
        if (
            state.finished_utc >= lease.attempt_deadline_utc
            or state.finished_mono >= attempt_mono
            or state.finished_utc >= lease.session_deadline_utc
            or state.finished_mono >= session_mono
        ):
            raise SupervisionError("result frame arrived after deadline")
        if (final_guard := _sample_or_fail(cwd, sensor, floor)) is not None:
            raise SupervisionError(f"result frame final {final_guard} guard failed")
        exit_code = wintypes.DWORD()
        if not api.exit_code(process, ctypes.byref(exit_code)):
            raise _error("GetExitCodeProcess(result process)")
        if exit_code.value == STILL_ACTIVE or exit_code.value != 0:
            raise SupervisionError(f"result process exited unsuccessfully: {exit_code.value}")
        if DeadlineLease.load(deadline_path) != lease:
            raise SupervisionError("persisted result frame deadline changed during execution")
        exit_value = int(exit_code.value)
        frame = state.frame
        completed = True
    finally:
        cleanup_error: SupervisionError | None = None
        if process and not assigned:
            if not api.terminate_process(process, ERROR_TERMINATED):
                cleanup_error = _error("TerminateProcess(unassigned result child)")
            if api.wait(process, 2000) != WAIT_OBJECT_0:
                cleanup_error = SupervisionError("unassigned result child did not exit")
        if job and assigned and not completed:
            if not api.terminate_job(job, ERROR_TERMINATED):
                cleanup_error = _error("TerminateJobObject(result job)")
            else:
                try:
                    _wait_for_empty_job(api, job)
                except SupervisionError as exc:
                    cleanup_error = exc
        if write_pipe and not api.close(write_pipe):
            cleanup_error = _error("CloseHandle(parent result writer)")
        if job and not api.close(job):
            cleanup_error = _error("CloseHandle(result Job Object)")
            api.terminate_job(job, ERROR_TERMINATED)
            api.close(job)
        if reader is not None:
            reader.join(timeout=0.3)
            if reader.is_alive():
                try:
                    _cancel_frame_reader(api, reader)
                except SupervisionError as exc:
                    cleanup_error = exc
        if read_pipe and not api.close(read_pipe):
            cleanup_error = _error("CloseHandle(result reader)")
        if attribute_initialized and attribute_buffer is not None:
            api.delete_attributes(ctypes.cast(attribute_buffer, ctypes.c_void_p))
        if child_thread and not api.close(child_thread):
            cleanup_error = _error("CloseHandle(result thread)")
        if process and assigned and api.wait(process, 2000) != WAIT_OBJECT_0:
            cleanup_error = SupervisionError("owned result child survived Job Object close")
        if process and not api.close(process):
            cleanup_error = _error("CloseHandle(result process)")
        if cleanup_error is not None:
            raise cleanup_error
    finished_utc = _utc_now()
    finished_mono = time.monotonic()
    if finished_utc >= lease.session_deadline_utc or finished_mono >= session_mono:
        raise SupervisionError("result frame session_deadline during cleanup")
    if finished_utc >= lease.attempt_deadline_utc or finished_mono >= attempt_mono:
        raise SupervisionError("result frame attempt_deadline during cleanup")
    if (post_guard := _sample_or_fail(cwd, sensor, floor)) is not None:
        raise SupervisionError(f"result frame post-cleanup {post_guard} guard failed")
    if DeadlineLease.load(deadline_path) != lease:
        raise SupervisionError("persisted result frame deadline changed during cleanup")
    if _utc_now() >= lease.session_deadline_utc or time.monotonic() >= session_mono:
        raise SupervisionError("result frame session_deadline after final sensor")
    if _utc_now() >= lease.attempt_deadline_utc or time.monotonic() >= attempt_mono:
        raise SupervisionError("result frame attempt_deadline after final sensor")
    return FramedSupervisionResult(
        SupervisionResult(
            pid, exit_value, "normal",
            None if memory_limit is None else peak_process,
            None if memory_limit is None else peak_job,
        ),
        frame,
    )
