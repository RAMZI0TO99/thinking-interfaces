"""Verified Job process-memory cap tests; no scientific runner is imported."""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from evaluation import phase2_supervision_primitives as supervision

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")

GIB = 1024**3


def _deadline(path: Path, attempt_seconds: float = 60.0) -> Path:
    now = datetime.now(UTC)
    supervision.DeadlineLease.open_or_create(
        path,
        attempt_deadline_utc=now + timedelta(seconds=attempt_seconds),
        session_deadline_utc=now + timedelta(seconds=120.0),
    )
    return path


def _ample(_root: Path) -> supervision.ResourceSample:
    return supervision.ResourceSample(21 * GIB, 5 * GIB)


def _wait_for_file(path: Path, seconds: float = 20.0) -> None:
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if path.is_file():
            return
        time.sleep(0.05)
    raise AssertionError(f"child did not write {path}")


def test_cap_validation_rejects_invalid_values(tmp_path: Path) -> None:
    marker = tmp_path / "never.txt"
    command = [
        sys.executable, "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
        str(marker),
    ]
    for bad in (0, -1, True, 1.5, "512"):
        with pytest.raises(ValueError):
            supervision.run_supervised(
                command, cwd=tmp_path,
                deadline_path=_deadline(tmp_path / "lease.json"),
                sensor=_ample, process_memory_limit_bytes=bad,  # type: ignore[arg-type]
            )
    assert not marker.exists()


def test_cap_reported_and_respected_for_small_child(tmp_path: Path) -> None:
    marker = tmp_path / "alloc.txt"
    command = [
        sys.executable, "-c",
        "data = bytearray(200 * 1024 * 1024); "
        "from pathlib import Path; import sys; "
        "Path(sys.argv[1]).write_text(str(len(data)))",
        str(marker),
    ]
    result = supervision.run_supervised(
        command, cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.05, process_memory_limit_bytes=2 * GIB,
    )
    assert result.reason == "normal"
    assert result.exit_code == 0
    assert result.peak_process_memory_bytes is not None
    assert 0 < result.peak_process_memory_bytes <= 2 * GIB
    assert result.peak_job_memory_bytes is not None
    assert 0 < result.peak_job_memory_bytes <= 2 * GIB
    _wait_for_file(marker)
    assert marker.read_text(encoding="utf-8") == str(200 * 1024 * 1024)


def test_child_exceeding_cap_fails(tmp_path: Path) -> None:
    command = [
        sys.executable, "-c",
        "import sys\n"
        "try:\n"
        "    data = bytearray(700 * 1024 * 1024)\n"
        "except MemoryError:\n"
        "    sys.exit(3)\n"
        "sys.exit(0)\n",
    ]
    result = supervision.run_supervised(
        command, cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.05, process_memory_limit_bytes=512 * 1024**2,
    )
    assert result.exit_code != 0
    assert result.reason == "normal"


def test_queryback_limit_mismatch_refuses_without_child(tmp_path: Path) -> None:
    marker = tmp_path / "never.txt"
    command = [
        sys.executable, "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
        str(marker),
    ]
    original = supervision._WinApi

    def tampered_api() -> supervision._WinApi:
        api = original()
        real_query = api.__dict__["query_job"]

        def query_job(
            job: int, info_class: int, info: object, length: int,
            return_length: object = None,
        ) -> bool:
            ok = real_query(job, info_class, info, length, None)
            if ok and info_class == supervision.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS:
                limits = info._obj
                limits.ProcessMemoryLimit = 0
            return bool(ok)

        api.__dict__["query_job"] = query_job
        return api

    with (
        patch.object(supervision, "_WinApi", side_effect=tampered_api),
        pytest.raises(supervision.SupervisionError, match="process memory"),
    ):
        supervision.run_supervised(
            command, cwd=tmp_path,
            deadline_path=_deadline(tmp_path / "lease.json"),
            sensor=_ample, process_memory_limit_bytes=1 * GIB,
        )
    time.sleep(0.5)
    assert not marker.exists()


def test_peaks_absent_without_cap(tmp_path: Path) -> None:
    marker = tmp_path / "plain.txt"
    command = [
        sys.executable, "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ok')",
        str(marker),
    ]
    result = supervision.run_supervised(
        command, cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.05,
    )
    assert result.reason == "normal"
    assert result.peak_process_memory_bytes is None
    assert result.peak_job_memory_bytes is None


def test_framed_runner_reports_peaks_under_cap(tmp_path: Path) -> None:
    frame_child = (
        "import msvcrt, os, struct, sys; "
        "handle=int(sys.argv[1]); os.set_handle_inheritable(handle, False); "
        "fd=msvcrt.open_osfhandle(handle, os.O_WRONLY); "
        "stream=os.fdopen(fd, 'wb', buffering=0); "
        "payload=b'x' * 64; "
        "stream.write(struct.pack('<I', len(payload)) + payload); stream.close()"
    )
    command = [sys.executable, "-c", frame_child, "{result_handle}"]
    output = supervision.run_supervised_with_frame(
        command, cwd=tmp_path, deadline_path=_deadline(tmp_path / "lease.json"),
        sensor=_ample, poll_seconds=0.05, process_memory_limit_bytes=2 * GIB,
    )
    assert output.frame == b"x" * 64
    assert output.result.reason == "normal"
    assert output.result.peak_process_memory_bytes is not None
    assert 0 < output.result.peak_process_memory_bytes <= 2 * GIB
