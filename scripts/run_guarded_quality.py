"""Run full quality with exact-source, resource, deadline and owned-process guards.

This verifies engineering quality only; it does not launch scientific fits or
admit an experiment. Outputs are write-once and never reuse global quality status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.provenance import source_fingerprint  # noqa: E402
from evaluation.quality_audit import verify_quality_bundle  # noqa: E402

START_DISK_GIB = 9.0
START_RAM_GIB = 6.0
STOP_DISK_GIB = 8.0
STOP_RAM_GIB = 4.0
MAX_WALL_SECONDS = 4200.0
START_SAMPLE_INTERVAL_SECONDS = 2.0
POLL_INTERVAL_SECONDS = 1.0
ATTEMPT_DIRECTORY = Path("runs/phase2/quality_attempts")
ARCHIVE_DIRECTORY = Path("runs/phase2/quality_history")


class OwnedProcessTree:
    """Track launched descendants by PID AND creation time, never by process name.

Known children remain tracked if a Windows venv launcher exits or is terminated.
Repeated snapshots also capture grandchildren of a previously captured child.
"""

    def __init__(self, child: subprocess.Popen[bytes]) -> None:
        self.child = child
        self._processes: dict[tuple[int, float], Any] = {}
        try:
            parent = psutil.Process(child.pid)
            self._processes[(parent.pid, parent.create_time())] = parent
        except psutil.NoSuchProcess:
            pass
        self.refresh()

    @staticmethod
    def _alive(process: Any, identity: tuple[int, float]) -> bool:
        try:
            return bool(
                process.pid == identity[0]
                and process.create_time() == identity[1]
                and process.is_running()
                and process.status() != psutil.STATUS_ZOMBIE
            )
        except psutil.NoSuchProcess:
            return False

    def refresh(self) -> None:
        for identity, process in tuple(self._processes.items()):
            if not self._alive(process, identity):
                continue
            try:
                descendants = process.children(recursive=True)
                for descendant in descendants:
                    with suppress(psutil.NoSuchProcess):
                        self._processes[(descendant.pid, descendant.create_time())] = descendant
            except psutil.NoSuchProcess:
                pass

    def living(self) -> list[Any]:
        self.refresh()
        return [
            process
            for identity, process in self._processes.items()
            if self._alive(process, identity)
        ]

    def stop(self) -> None:
        # Stop the launcher first so it cannot spawn new work during cleanup,
        # then terminate the identity-checked descendants captured above.
        self.refresh()
        processes = self.living()
        for process in processes:
            identity = (process.pid, process.create_time())
            if identity in self._processes and self._alive(process, identity):
                with suppress(psutil.NoSuchProcess):
                    process.terminate()
        _, survivors = psutil.wait_procs(processes, timeout=5)
        for process in survivors:
            identity = (process.pid, process.create_time())
            if identity in self._processes and self._alive(process, identity):
                with suppress(psutil.NoSuchProcess):
                    process.kill()
        psutil.wait_procs(survivors, timeout=5)
        self.child.wait(timeout=10)
        if self.living():
            raise RuntimeError("owned descendants remained alive after cleanup")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_resources(root: Path) -> dict[str, float | str]:
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "free_disk_gib": shutil.disk_usage(root).free / 1024**3,
        "available_ram_gib": psutil.virtual_memory().available / 1024**3,
    }


def write_once(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _bounded_attempt(root: Path, path: Path) -> tuple[Path, Path]:
    path = (path if path.is_absolute() else root / path).resolve()
    attempt_root = (root / ATTEMPT_DIRECTORY).resolve()
    archive_root = (root / ARCHIVE_DIRECTORY).resolve()
    if not (
        attempt_root.is_relative_to(root)
        and archive_root.is_relative_to(root)
        and attempt_root == root / ATTEMPT_DIRECTORY
        and archive_root == root / ARCHIVE_DIRECTORY
        and path.parent == attempt_root
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}", path.name)
    ):
        raise ValueError(
            "attempt directory must be a named direct child of " + str(ATTEMPT_DIRECTORY)
        )
    archive = archive_root / f"{path.name}.json"
    if path.exists() or archive.exists():
        raise FileExistsError("write-once attempt directory or pass archive already exists")
    attempt_root.mkdir(parents=True, exist_ok=True)
    path.mkdir()  # Exclusive claim before any subprocess or output is created.
    return path, archive


def _current_status_path(root: Path) -> Path:
    runs = root / "runs"
    status = runs / "quality_status.json"
    if runs.resolve() != runs or status.is_symlink() or (status.exists() and not status.is_file()):
        raise ValueError("current quality status must use ordinary paths inside project runs")
    return status


def _optional_digest(path: Path) -> str | None:
    try:
        return digest(path) if path.is_file() else None
    except OSError:
        return None


def _write_bytes_once(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _quarantine_owned_archive(
    archive: Path, identity: tuple[int, int], out: Path,
) -> Path:
    current = archive.stat(follow_symlinks=False)
    if (current.st_dev, current.st_ino) != identity or archive.is_symlink():
        raise RuntimeError("archive path no longer identifies this attempt's newly created file")
    quarantine = out / "quality_archive.quarantined.json"
    if quarantine.exists():
        raise FileExistsError("write-once quarantine already exists")
    archive.replace(quarantine)
    return quarantine


def _startup_failure(point: dict[str, float | str], ram_floor: float) -> str | None:
    if float(point["free_disk_gib"]) < START_DISK_GIB:
        return "quality-only startup disk floor"
    if float(point["available_ram_gib"]) < ram_floor:
        return "quality-only startup RAM floor"
    return None


def _active_failure(point: dict[str, float | str]) -> str | None:
    if float(point["free_disk_gib"]) < STOP_DISK_GIB:
        return "quality-only active disk floor"
    if float(point["available_ram_gib"]) < STOP_RAM_GIB:
        return "quality-only active RAM floor"
    return None


def read_attempt_status(path: Path, attempt_id: str, source: str) -> dict[str, Any] | None:
    """Only accept a status emitted to THIS attempt with its unguessable token."""
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
        if (
            isinstance(payload, dict)
            and payload.get("attempt_id") == attempt_id
            and payload.get("source_sha256_before") == source
            and payload.get("source_sha256_after") == source
        ):
            return payload
    except (OSError, ValueError):
        pass
    return None


def run_attempt(
    root: Path,
    expect_source: str,
    attempt_directory: Path,
    *,
    startup_ram_gib: float = START_RAM_GIB,
    publish_current_status: bool = False,
    max_wall_seconds: float = MAX_WALL_SECONDS,
) -> int:
    root = root.resolve()
    if re.fullmatch(r"[0-9a-f]{64}", expect_source) is None:
        raise ValueError("--expect-source must be a lowercase SHA256 fingerprint")
    if not math.isfinite(startup_ram_gib) or startup_ram_gib < START_RAM_GIB:
        raise ValueError("startup RAM guard may be strengthened but cannot be below 6 GiB")
    if (
        not math.isfinite(max_wall_seconds)
        or max_wall_seconds <= 0
        or max_wall_seconds > MAX_WALL_SECONDS
    ):
        raise ValueError("maximum wall seconds must be finite, positive and at most 4200")
    out, archive = _bounded_attempt(root, attempt_directory)
    attempt_id = uuid.uuid4().hex
    status_path = out / "quality_status.json"
    log_path = out / "quality_stdout.log"
    command = [
        sys.executable, "-B", "scripts/verify_phase1_quality.py",
        "--status-output", str(status_path), "--attempt-id", attempt_id,
    ]
    started = time.monotonic()
    points: list[dict[str, float | str]] = []
    source_before: str | None = None
    source_after: str | None = None
    child: subprocess.Popen[bytes] | None = None
    tree: OwnedProcessTree | None = None
    reason: str | None = None
    cleanup_error: str | None = None
    error: str | None = None
    verified = False
    payload: dict[str, Any] | None = None
    current_path = root / "runs/quality_status.json"
    previous_status_sha256: str | None = None
    previous_status_bytes: bytes | None = None
    current_status_sha256: str | None = None
    pointer_published = False
    before = {
        "schema": "guarded_exact_source_quality_start_v2",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "attempt_id": attempt_id,
        "expected_source_sha256": expect_source,
        "script_sha256": digest(Path(__file__)),
        "command": command,
        "startup_disk_gib": START_DISK_GIB,
        "startup_ram_gib": startup_ram_gib,
        "active_stop_disk_gib": STOP_DISK_GIB,
        "active_stop_ram_gib": STOP_RAM_GIB,
        "maximum_wall_seconds": max_wall_seconds,
        "policy_maximum_wall_seconds": MAX_WALL_SECONDS,
        "maximum_command_seconds": 3600,
        "publish_current_status_requested": publish_current_status,
        "scope": "Quality-only verification; no fit or scientific admission",
    }
    write_once(out / "before.json", before)
    # Creating the log even on a failed preflight makes every claimed attempt
    # reviewable; neither an old global status nor a prior attempt is consulted.
    with log_path.open("xb") as stream:
        try:
            if publish_current_status:
                current_path = _current_status_path(root)
            if current_path.is_file():
                previous_status_bytes = current_path.read_bytes()
                previous_status_sha256 = hashlib.sha256(previous_status_bytes).hexdigest()
                if publish_current_status:
                    _write_bytes_once(out / "previous_current_status.json", previous_status_bytes)
            source_before = source_fingerprint(root)
            if source_before != expect_source:
                reason = "source differs before full quality"
            first = sample_resources(root)
            points.append(first)
            time.sleep(START_SAMPLE_INTERVAL_SECONDS)
            second = sample_resources(root)
            points.append(second)
            for point in points:
                reason = reason or _startup_failure(point, startup_ram_gib)
            if reason is None:
                # Catch edits between source capture and the two resource samples.
                if source_fingerprint(root) != expect_source:
                    reason = "source differs before quality launch"
                elif time.monotonic() - started >= max_wall_seconds:
                    reason = "quality-only wall limit"
            if reason is None:
                environment = os.environ.copy()
                environment["PYTHONDONTWRITEBYTECODE"] = "1"
                child = subprocess.Popen(
                    command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, env=environment,
                )
                tree = OwnedProcessTree(child)
                while True:
                    tree.refresh()
                    exit_code = child.poll()
                    point = sample_resources(root)
                    points.append(point)
                    reason = _active_failure(point)
                    if reason is None and time.monotonic() - started >= max_wall_seconds:
                        reason = "quality-only wall limit"
                    if reason is None and source_fingerprint(root) != expect_source:
                        reason = "source drift during full quality"
                    if reason is not None:
                        tree.stop()
                        break
                    if exit_code is not None:
                        if tree.living():
                            reason = "quality process left owned descendants alive"
                            tree.stop()
                        break
                    time.sleep(POLL_INTERVAL_SECONDS)
            source_after = source_fingerprint(root)
            if reason is None and source_after != expect_source:
                reason = "source drift after full quality"
            payload = read_attempt_status(status_path, attempt_id, expect_source)
            if reason is None and child is not None and child.returncode == 0:
                if payload is None:
                    reason = "missing or foreign attempt-scoped quality status"
                elif not verify_quality_bundle(root, payload):
                    reason = "quality bundle verification failed"
                else:
                    verified = True
            elif reason is None:
                reason = "quality command failed"
        except KeyboardInterrupt:
            reason = "user cancellation"
        except Exception as caught:
            reason = "quality attempt error"
            error = f"{type(caught).__name__}: {caught}"
        finally:
            if tree is not None:
                try:
                    if (child is not None and child.poll() is None) or tree.living():
                        tree.stop()
                except Exception as caught:
                    cleanup_error = f"{type(caught).__name__}: {caught}"
                    verified = False
            stream.flush()
            os.fsync(stream.fileno())
    # Cancellation or errors must still leave a final immutable receipt.
    try:
        source_after = source_fingerprint(root)
        final_point = sample_resources(root)
        points.append(final_point)
        if child is not None and _active_failure(final_point) is not None:
            verified = False
            reason = reason or _active_failure(final_point)
        if source_after != expect_source:
            verified = False
            reason = reason or "source drift after full quality"
    except (Exception, KeyboardInterrupt) as caught:
        verified = False
        reason = reason or "final provenance or resource sample failed"
        error = error or f"{type(caught).__name__}: {caught}"
    passed = verified and reason is None and cleanup_error is None
    archive_relative: str | None = None
    archive_identity: tuple[int, int] | None = None
    quarantined_archive: Path | None = None
    quality_candidate: Path | None = None
    pointer_replacement_attempted = False
    pointer_publication_occurred = False
    pointer_restored = False
    pointer_rollback_skipped = False
    publication_cleanup_error: str | None = None
    raw_status: bytes | None = None
    if passed:
        assert payload is not None
        try:
            # Stage immutable evidence inside the attempt first. Nothing staged
            # is a pass archive until every commit check succeeds.
            if not verify_quality_bundle(root, payload):
                raise RuntimeError("quality bundle changed before archive")
            raw_status = status_path.read_bytes()
            if json.loads(raw_status) != payload or not verify_quality_bundle(root, payload):
                raise RuntimeError("attempt status or quality bundle changed before archive")
            quality_candidate = out / "quality_candidate.json"
            _write_bytes_once(quality_candidate, raw_status)
            if archive.parent.resolve() != root / ARCHIVE_DIRECTORY:
                raise ValueError("quality history must use ordinary paths inside project runs")
            staged_pointer = out / "current_status.pending.json"
            if publish_current_status:
                _current_status_path(root)
                if _optional_digest(current_path) != previous_status_sha256:
                    raise RuntimeError("current quality status changed during the attempt")
                _write_bytes_once(staged_pointer, raw_status)
            archive.parent.mkdir(parents=True, exist_ok=True)
            with archive.open("xb") as history:
                created = os.fstat(history.fileno())
                archive_identity = (created.st_dev, created.st_ino)
                history.write(raw_status)
                history.flush()
                os.fsync(history.fileno())
            archive_relative = archive.relative_to(root).as_posix()
            if (
                not verify_quality_bundle(root, payload)
                or status_path.read_bytes() != raw_status
                or archive.read_bytes() != raw_status
            ):
                raise RuntimeError("source or quality bundle changed after archive creation")
            if publish_current_status:
                _current_status_path(root)
                if _optional_digest(current_path) != previous_status_sha256:
                    raise RuntimeError("current quality status changed before publication")
                pointer_replacement_attempted = True
                staged_pointer.replace(current_path)
                pointer_published = True
                pointer_publication_occurred = True
            # Recheck after publication too. Any finalization failure removes
            # ONLY this newly created archive from the pass history and restores
            # the previous pointer ONLY while it still contains our exact bytes.
            if not verify_quality_bundle(root, payload):
                raise RuntimeError("source or quality bundle changed during final commit")
            source_after = source_fingerprint(root)
            commit_point = sample_resources(root)
            points.append(commit_point)
            if source_after != expect_source or _active_failure(commit_point):
                raise RuntimeError("source or active resource guard failed during final commit")
            if time.monotonic() - started >= max_wall_seconds:
                raise RuntimeError("quality-only wall limit during final commit")
        except (Exception, KeyboardInterrupt) as caught:
            passed = False
            reason = (
                "user cancellation during finalization" if isinstance(caught, KeyboardInterrupt)
                else "quality finalization failed"
            )
            error = f"{type(caught).__name__}: {caught}"
            if archive_identity is not None:
                try:
                    quarantined_archive = _quarantine_owned_archive(archive, archive_identity, out)
                    archive_relative = None
                except Exception as cleanup_caught:
                    publication_cleanup_error = (
                        f"archive quarantine: {type(cleanup_caught).__name__}: {cleanup_caught}"
                    )
            if pointer_replacement_attempted and raw_status is not None:
                try:
                    _current_status_path(root)
                    if current_path.is_file() and current_path.read_bytes() == raw_status:
                        if previous_status_bytes is None:
                            current_path.unlink()
                        else:
                            restored = out / "current_status.restore.pending.json"
                            _write_bytes_once(restored, previous_status_bytes)
                            restored.replace(current_path)
                        pointer_restored = True
                        pointer_published = False
                    else:
                        pointer_rollback_skipped = True
                        pointer_published = False
                except Exception as cleanup_caught:
                    publication_cleanup_error = (
                        (publication_cleanup_error + "; " if publication_cleanup_error else "")
                        + f"pointer restoration: {type(cleanup_caught).__name__}: {cleanup_caught}"
                    )
            with suppress(Exception):
                source_after = source_fingerprint(root)
    with suppress(OSError):
        current_status_sha256 = _optional_digest(current_path)
    receipt = {
        "schema": "phase2_guarded_exact_source_quality_attempt_v2",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "attempt_id": attempt_id,
        "status": "pass" if passed else "stopped_or_failed",
        "expected_source_sha256": expect_source,
        "source_sha256_before": source_before,
        "source_sha256_after": source_after,
        "source_stable": source_before == source_after == expect_source,
        "before_sha256": digest(out / "before.json"),
        "script_sha256": before["script_sha256"],
        "quality_stdout_sha256": digest(log_path),
        "exit_code": child.returncode if child is not None else None,
        "stop_reason": reason,
        "error": error,
        "cleanup_error": cleanup_error,
        "elapsed_seconds": time.monotonic() - started,
        "maximum_wall_seconds": max_wall_seconds,
        "policy_maximum_wall_seconds": MAX_WALL_SECONDS,
        "resource_samples": points,
        "minimum_free_disk_gib": min(float(p["free_disk_gib"]) for p in points) if points else None,
        "minimum_available_ram_gib": (
            min(float(p["available_ram_gib"]) for p in points) if points else None
        ),
        "quality_status_copy": status_path.relative_to(root).as_posix() if payload else None,
        "quality_status_sha256": _optional_digest(status_path) if payload else None,
        "quality_bundle_verified": passed,
        "quality_verified_before_publication": verified,
        "pass_archive": archive_relative,
        "quality_candidate": (
            quality_candidate.relative_to(root).as_posix() if quality_candidate else None
        ),
        "quality_candidate_sha256": (
            _optional_digest(quality_candidate) if quality_candidate else None
        ),
        "quarantined_quality_archive": (
            quarantined_archive.relative_to(root).as_posix() if quarantined_archive else None
        ),
        "quarantined_quality_archive_sha256": (
            _optional_digest(quarantined_archive) if quarantined_archive else None
        ),
        "publication_cleanup_error": publication_cleanup_error,
        "publish_current_status_requested": publish_current_status,
        "previous_current_status_sha256": previous_status_sha256,
        "current_status_sha256": current_status_sha256,
        "current_status_published": pointer_published,
        "current_status_publication_occurred": pointer_publication_occurred,
        "current_status_restored": pointer_restored,
        "current_status_rollback_skipped": pointer_rollback_skipped,
        "scientific_fit_count": 0,
        "scientific_cell_count": 0,
        "scientific_admission": False,
    }
    write_once(out / "receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True), flush=True)
    return 0 if passed else 1


def _cancel(signum: int, frame: Any) -> None:
    signal.signal(signum, signal.SIG_IGN)
    raise KeyboardInterrupt(f"quality wrapper received signal {signum}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-source", required=True)
    parser.add_argument("--attempt-directory", type=Path, required=True)
    parser.add_argument("--startup-ram-gib", type=float, default=START_RAM_GIB)
    parser.add_argument("--max-wall-seconds", type=float, default=MAX_WALL_SECONDS)
    parser.add_argument("--publish-current-status", action="store_true")
    options = parser.parse_args(argv)
    expected_python = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    if Path(sys.executable).resolve() != expected_python.resolve():
        parser.error("run with the project's .venv Python")
    signal.signal(signal.SIGTERM, _cancel)
    signal.signal(signal.SIGINT, _cancel)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _cancel)
    try:
        return run_attempt(
            ROOT, options.expect_source, options.attempt_directory,
            startup_ram_gib=options.startup_ram_gib,
            publish_current_status=options.publish_current_status,
            max_wall_seconds=options.max_wall_seconds,
        )
    except (ValueError, FileExistsError) as caught:
        parser.error(str(caught))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
