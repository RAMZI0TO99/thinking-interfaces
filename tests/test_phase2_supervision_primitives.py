"""Synthetic Windows process-tree tests; no scientific runner is imported."""

from __future__ import annotations

import ctypes
import importlib
import json
import math
import os
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from evaluation import phase2_supervision_primitives as supervision

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")


def _deadline(path: Path, attempt_seconds: float = 3.0) -> Path:
    now = datetime.now(UTC)
    supervision.DeadlineLease.open_or_create(
        path,
        attempt_deadline_utc=now + timedelta(seconds=attempt_seconds),
        session_deadline_utc=now + timedelta(seconds=5),
    )
    return path


def _ample(_root: Path) -> supervision.ResourceSample:
    return supervision.ResourceSample(21 * supervision.GIB, 5 * supervision.GIB)


def _wait_for_file(path: Path, seconds: float = 3.0) -> str:
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if path.is_file():
            return path.read_text(encoding="utf-8")
        time.sleep(0.02)
    raise AssertionError(f"synthetic child did not write {path}")


def _wait_for_exit(pid: int, seconds: float = 3.0) -> None:
    psutil = importlib.import_module("psutil")

    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if not psutil.pid_exists(pid):
            return
        time.sleep(0.02)
    raise AssertionError(f"Job Object member {pid} survived")


def test_normal_child_exits_and_writes_marker(tmp_path: Path) -> None:
    marker = tmp_path / "normal.txt"
    command = [
        sys.executable, "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ok')",
        str(marker),
    ]
    result = supervision.run_supervised(
        command, cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.02,
    )
    assert result.reason == "normal"
    assert result.exit_code == 0
    assert result.pid > 0
    assert marker.read_text(encoding="utf-8") == "ok"


def test_completion_sensor_crossing_deadline_is_not_normal(tmp_path: Path) -> None:
    lease_path = _deadline(tmp_path / "lease.json")
    lease = supervision.DeadlineLease.load(lease_path)
    original_active = supervision._active_processes
    job_empty = False
    expired_during_final_sample = False

    def active(api: supervision._WinApi, job: wintypes.HANDLE) -> int:
        nonlocal job_empty
        count = original_active(api, job)
        if count == 0:
            job_empty = True
        return count

    def sensor(root: Path) -> supervision.ResourceSample:
        nonlocal expired_during_final_sample
        if job_empty:
            expired_during_final_sample = True
        return _ample(root)

    def now() -> datetime:
        if expired_during_final_sample:
            return lease.attempt_deadline_utc + timedelta(seconds=1)
        return datetime.now(UTC)

    with (
        patch.object(supervision, "_active_processes", side_effect=active),
        patch.object(supervision, "_utc_now", side_effect=now),
    ):
        result = supervision.run_supervised(
            [sys.executable, "-c", "pass"], cwd=tmp_path,
            deadline_path=lease_path, sensor=sensor, poll_seconds=0.02,
        )
    assert expired_during_final_sample
    assert result.reason == "attempt_deadline"
    assert result.exit_code == 0


def test_hung_child_stops_at_persisted_attempt_deadline(tmp_path: Path) -> None:
    marker = tmp_path / "started.txt"
    command = [
        sys.executable, "-c",
        "from pathlib import Path; import sys, time; "
        "Path(sys.argv[1]).write_text('started'); time.sleep(30)",
        str(marker),
    ]
    start = time.monotonic()
    result = supervision.run_supervised(
        command, cwd=tmp_path,
        deadline_path=_deadline(tmp_path / "lease.json", attempt_seconds=0.6),
        sensor=_ample, poll_seconds=0.02,
    )
    assert result.reason == "attempt_deadline"
    assert marker.read_text(encoding="utf-8") == "started"
    assert time.monotonic() - start < 2.5
    _wait_for_exit(result.pid)


def test_grandchild_stays_in_owned_job_and_unrelated_process_survives(tmp_path: Path) -> None:
    grandchild_pid = tmp_path / "grandchild.pid"
    child = (
        "import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', "
        "'from pathlib import Path; import sys, os, time; '"
        "+ 'Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(30)', "
        "sys.argv[1]]); time.sleep(30)"
    )
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        result = supervision.run_supervised(
            [sys.executable, "-c", child, str(grandchild_pid)],
            cwd=tmp_path,
            deadline_path=_deadline(tmp_path / "lease.json", attempt_seconds=0.8),
            sensor=_ample, poll_seconds=0.02,
        )
        assert result.reason == "attempt_deadline"
        owned_grandchild = int(_wait_for_file(grandchild_pid))
        _wait_for_exit(result.pid)
        _wait_for_exit(owned_grandchild)
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=3)


def test_root_exit_zero_waits_for_grandchild_then_hits_deadline(tmp_path: Path) -> None:
    grandchild_pid = tmp_path / "grandchild.pid"
    child = (
        "import subprocess, sys; "
        "subprocess.Popen([sys.executable, '-c', "
        "'from pathlib import Path; import os, sys, time; '"
        "+ 'Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(30)', "
        "sys.argv[1]])"
    )
    result = supervision.run_supervised(
        [sys.executable, "-c", child, str(grandchild_pid)], cwd=tmp_path,
        deadline_path=_deadline(tmp_path / "lease.json", attempt_seconds=0.8),
        sensor=_ample, poll_seconds=0.02,
    )
    assert result.reason == "attempt_deadline"
    _wait_for_exit(result.pid)
    _wait_for_exit(int(_wait_for_file(grandchild_pid)))


def test_root_exit_zero_waits_for_grandchild_natural_exit(tmp_path: Path) -> None:
    child = (
        "import subprocess, sys; "
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.2)'])"
    )
    start = time.monotonic()
    result = supervision.run_supervised(
        [sys.executable, "-c", child], cwd=tmp_path,
        deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.02,
    )
    assert result.reason == "normal"
    assert result.exit_code == 0
    assert time.monotonic() - start >= 0.18


@pytest.mark.parametrize("low_resource", ["disk", "ram"])
def test_live_resource_guard_stops_owned_child(tmp_path: Path, low_resource: str) -> None:
    calls = 0

    def sensor(_root: Path) -> supervision.ResourceSample:
        nonlocal calls
        calls += 1
        if calls >= 5:
            if low_resource == "disk":
                return supervision.ResourceSample(19 * supervision.GIB, 5 * supervision.GIB)
            return supervision.ResourceSample(21 * supervision.GIB, 3 * supervision.GIB)
        return _ample(_root)

    result = supervision.run_supervised(
        [sys.executable, "-c", "import time; time.sleep(30)"], cwd=tmp_path,
        deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=sensor, poll_seconds=0.02,
    )
    assert result.reason == f"{low_resource}_floor"
    _wait_for_exit(result.pid)


def test_sensor_exception_after_launch_kills_child(tmp_path: Path) -> None:
    marker = tmp_path / "child.pid"
    calls = 0

    def sensor(_root: Path) -> supervision.ResourceSample:
        nonlocal calls
        calls += 1
        if calls > 4 and marker.is_file():
            raise OSError("sensor unavailable")
        return _ample(_root)

    with pytest.raises(supervision.SupervisionError, match="sensor failed"):
        supervision.run_supervised(
            [
                sys.executable, "-c",
                "from pathlib import Path; import os, sys, time; "
                "Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(30)",
                str(marker),
            ],
            cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
            sensor=sensor, poll_seconds=0.02,
        )
    _wait_for_exit(int(_wait_for_file(marker)))


def test_failed_job_assignment_never_runs_suspended_child(tmp_path: Path) -> None:
    marker = tmp_path / "should-not-exist.txt"
    original = supervision._WinApi

    def failed_api() -> supervision._WinApi:
        api = original()
        api.__dict__["assign"] = lambda _job, _process: False
        return api

    with (
        patch.object(supervision, "_WinApi", side_effect=failed_api),
        pytest.raises(supervision.SupervisionError, match="AssignProcessToJobObject"),
    ):
        supervision.run_supervised(
            [
                sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
                str(marker),
            ],
            cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
            sensor=_ample,
        )
    assert not marker.exists()


def test_deadline_expiry_during_pre_resume_sensor_never_runs_child(tmp_path: Path) -> None:
    marker = tmp_path / "should-not-resume.txt"
    reads = 0

    def slow_sensor(root: Path) -> supervision.ResourceSample:
        nonlocal reads
        reads += 1
        if reads == 3:
            time.sleep(0.3)
        return _ample(root)

    with pytest.raises(supervision.SupervisionError, match="deadline expired"):
        supervision.run_supervised(
            [
                sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
                str(marker),
            ],
            cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json", 0.2),
            sensor=slow_sensor, poll_seconds=0.02,
        )
    assert not marker.exists()


def test_deadline_record_survives_restart_and_cannot_be_extended(tmp_path: Path) -> None:
    path = tmp_path / "lease.json"
    _deadline(path, attempt_seconds=0.15)
    original = supervision.DeadlineLease.load(path)
    with pytest.raises(ValueError, match="differs"):
        supervision.DeadlineLease.open_or_create(
            path,
            attempt_deadline_utc=original.attempt_deadline_utc + timedelta(seconds=3),
            session_deadline_utc=original.session_deadline_utc,
        )
    time.sleep(0.2)
    assert supervision.DeadlineLease.load(path) == original
    marker = tmp_path / "should-not-start.txt"
    with pytest.raises(supervision.SupervisionError, match="already expired"):
        supervision.run_supervised(
            [
                sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
                str(marker),
            ], cwd=tmp_path, deadline_path=path, sensor=_ample,
        )
    assert not marker.exists()


def test_parent_crash_closes_job_and_kills_owned_child(tmp_path: Path) -> None:
    child_marker = tmp_path / "child.pid"
    grandchild_marker = tmp_path / "grandchild.pid"
    lease = _deadline(tmp_path / "lease.json")
    grandchild_script = tmp_path / "grandchild.py"
    grandchild_script.write_text(
        "from pathlib import Path\nimport os, sys, time\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()))\ntime.sleep(30)\n",
        encoding="utf-8",
    )
    child_script = tmp_path / "child.py"
    child_script.write_text(
        "from pathlib import Path\nimport os, subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2]])\n"
        "Path(sys.argv[3]).write_text(str(os.getpid()))\ntime.sleep(30)\n",
        encoding="utf-8",
    )
    parent_script = tmp_path / "parent.py"
    parent_script.write_text(
        "from pathlib import Path\nimport sys\n"
        "from evaluation.phase2_supervision_primitives import "
        "run_supervised, ResourceSample, GIB\n"
        "run_supervised([sys.executable, sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]], "
        "cwd=Path(sys.argv[6]), deadline_path=Path(sys.argv[1]), "
        "sensor=lambda _: ResourceSample(21*GIB, 5*GIB), poll_seconds=0.02)\n",
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parents[1]
    parent = subprocess.Popen(
        [
            sys.executable, str(parent_script), str(lease), str(child_script),
            str(grandchild_script), str(grandchild_marker), str(child_marker), str(tmp_path),
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    try:
        child_pid = int(_wait_for_file(child_marker))
        grandchild_pid = int(_wait_for_file(grandchild_marker))
        parent.kill()
        parent.wait(timeout=3)
        _wait_for_exit(child_pid)
        _wait_for_exit(grandchild_pid)
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=3)


def test_deadline_rejects_corruption_and_weak_floor(tmp_path: Path) -> None:
    path = _deadline(tmp_path / "lease.json")
    contents = json.loads(path.read_text(encoding="utf-8"))
    contents["unexpected"] = True
    path.write_text(json.dumps(contents), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected schema"):
        supervision.DeadlineLease.load(path)
    with pytest.raises(ValueError, match="cannot be weakened"):
        supervision.ResourceFloor(disk_bytes=19 * supervision.GIB)
    with pytest.raises(ValueError, match="cannot be weakened"):
        supervision.ResourceFloor(disk_bytes=math.nan)  # type: ignore[arg-type]
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="cap exceeded"):
        supervision.DeadlineLease.open_or_create(
            tmp_path / "too-long.json",
            attempt_deadline_utc=now + timedelta(minutes=11),
            session_deadline_utc=now + timedelta(minutes=20),
        )


_FRAME_CHILD = (
    "import msvcrt, os, struct, sys; "
    "handle=int(sys.argv[1]); os.set_handle_inheritable(handle, False); "
    "fd=msvcrt.open_osfhandle(handle, os.O_WRONLY); "
    "stream=os.fdopen(fd, 'wb', buffering=0); "
    "payload=b'engineering-only'; "
    "stream.write(struct.pack('<I', len(payload)) + payload); stream.close()"
)


def test_framed_supervisor_receives_one_exact_frame(tmp_path: Path) -> None:
    output = supervision.run_supervised_with_frame(
        [sys.executable, "-c", _FRAME_CHILD, "{result_handle}"],
        cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.02,
    )
    assert output.result.reason == "normal"
    assert output.result.exit_code == 0
    assert output.frame == b"engineering-only"


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        (b"", "missing|truncated"),
        (b"\x03\x00", "truncated"),
        (b"\x04\x00\x00\x00abc", "truncated"),
        (b"\x0a\x00\x00\x00", "size limit"),
        (b"\x01\x00\x00\x00xy", "extra bytes"),
        (b"\x01\x00\x00\x00x\x01\x00\x00\x00y", "extra bytes"),
    ],
)
def test_framed_supervisor_rejects_bad_frames(
    tmp_path: Path, written: bytes, expected: str
) -> None:
    script = (
        "import msvcrt, os, sys; "
        "handle=int(sys.argv[1]); os.set_handle_inheritable(handle, False); "
        "fd=msvcrt.open_osfhandle(handle, os.O_WRONLY); "
        "stream=os.fdopen(fd, 'wb', buffering=0); "
        "stream.write(bytes.fromhex(sys.argv[2])); stream.close()"
    )
    with pytest.raises(supervision.SupervisionError, match=f"frame.*({expected})"):
        supervision.run_supervised_with_frame(
            [sys.executable, "-c", script, "{result_handle}", written.hex()],
            cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
            sensor=_ample, poll_seconds=0.02, max_frame_bytes=4,
        )


def test_framed_supervisor_waits_for_grandchild_and_stops_owned_job(tmp_path: Path) -> None:
    marker = tmp_path / "grandchild.pid"
    child = (
        "import msvcrt, os, struct, subprocess, sys; "
        "handle=int(sys.argv[1]); os.set_handle_inheritable(handle, False); "
        "fd=msvcrt.open_osfhandle(handle, os.O_WRONLY); "
        "stream=os.fdopen(fd, 'wb', buffering=0); "
        "stream.write(struct.pack('<I', 2)+b'ok'); stream.close(); "
        "subprocess.Popen([sys.executable, '-c', "
        "'from pathlib import Path; import os,sys,time; '"
        "+'Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(30)', "
        "sys.argv[2]])"
    )
    with pytest.raises(supervision.SupervisionError, match="result frame attempt_deadline"):
        supervision.run_supervised_with_frame(
            [sys.executable, "-c", child, "{result_handle}", str(marker)],
            cwd=tmp_path,
            deadline_path=_deadline(tmp_path / "lease.json", attempt_seconds=0.8),
            sensor=_ample, poll_seconds=0.02,
        )
    _wait_for_exit(int(_wait_for_file(marker)))


def test_framed_supervisor_excludes_unrelated_inheritable_handle(tmp_path: Path) -> None:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create_event = kernel.CreateEventW
    create_event.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    create_event.restype = wintypes.HANDLE
    set_handle = kernel.SetHandleInformation
    set_handle.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
    set_handle.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    unrelated = create_event(None, False, False, None)
    assert unrelated
    try:
        assert set_handle(
            unrelated, supervision.HANDLE_FLAG_INHERIT, supervision.HANDLE_FLAG_INHERIT
        )
        script = (
            "import ctypes, msvcrt, os, struct, sys; "
            "kernel=ctypes.WinDLL('kernel32', use_last_error=True); "
            "flags=ctypes.c_ulong(); "
            "leaked=kernel.GetHandleInformation(ctypes.c_void_p(int(sys.argv[2])), "
            "ctypes.byref(flags)); "
            "handle=int(sys.argv[1]); os.set_handle_inheritable(handle, False); "
            "fd=msvcrt.open_osfhandle(handle, os.O_WRONLY); "
            "stream=os.fdopen(fd, 'wb', buffering=0); "
            "payload=b'leaked' if leaked else b'isolated'; "
            "stream.write(struct.pack('<I', len(payload))+payload); stream.close()"
        )
        output = supervision.run_supervised_with_frame(
            [sys.executable, "-c", script, "{result_handle}", str(unrelated)],
            cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
            sensor=_ample, poll_seconds=0.02,
        )
        assert output.frame == b"isolated"
    finally:
        close(unrelated)


def test_framed_command_requires_one_whole_placeholder(tmp_path: Path) -> None:
    lease = _deadline(tmp_path / "lease.json")
    for command in (
        [sys.executable, "-c", "pass"],
        [sys.executable, "-c", "pass", "{result_handle}", "{result_handle}"],
        [sys.executable, "-c", "pass", "x{result_handle}"],
    ):
        with pytest.raises(ValueError, match="result_handle"):
            supervision.run_supervised_with_frame(
                command, cwd=tmp_path, deadline_path=lease, sensor=_ample,
            )
