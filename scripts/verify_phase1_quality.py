"""Run local lint, type and regression checks and save an exact-source receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.provenance import capture_source, source_fingerprint  # noqa: E402
from evaluation.quality_audit import QUALITY_COMMANDS  # noqa: E402
from scripts.run_guarded_quality import OwnedProcessTree  # noqa: E402

QUALITY_COMMAND_TIMEOUT_SECONDS = 3600
QUALITY_PROCESS_POLL_SECONDS = 0.1


def _run_command(root: Path, arguments: tuple[str, ...], stream: TextIO) -> int:
    child = subprocess.Popen(
        [sys.executable, *arguments],
        cwd=root,
        stdout=stream,
        stderr=subprocess.STDOUT,
    )
    tree = OwnedProcessTree(child)
    started = time.monotonic()
    try:
        while True:
            tree.refresh()
            exit_code = child.poll()
            if time.monotonic() - started >= QUALITY_COMMAND_TIMEOUT_SECONDS:
                raise subprocess.TimeoutExpired(child.args, QUALITY_COMMAND_TIMEOUT_SECONDS)
            if exit_code is not None:
                if tree.living():
                    stream.write(
                        "\nQuality command left owned descendants alive; rejecting pass.\n"
                    )
                    tree.stop()
                    return -1
                return exit_code
            time.sleep(QUALITY_PROCESS_POLL_SECONDS)
    finally:
        # Polling retains descendants even after a venv launcher exits. A
        # successful parent exit never certifies unfinished descendant work.
        if child.poll() is None or tree.living():
            tree.stop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-output", type=Path)
    parser.add_argument("--attempt-id", default=None)
    options = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    output = root / "runs" / "quality_status.json"
    scoped = options.status_output is not None
    if scoped:
        output = options.status_output
        if not output.is_absolute():
            output = root / output
        output = output.resolve()
        runs_root = (root / "runs").resolve()
        if not runs_root.is_relative_to(root) or not output.is_relative_to(runs_root):
            parser.error("--status-output must remain inside the project's runs directory")
        if output.exists():
            parser.error("--status-output is write-once and already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
    attempt_id = options.attempt_id or uuid.uuid4().hex
    if len(attempt_id) != 32 or any(
        character not in "0123456789abcdef" for character in attempt_id
    ):
        parser.error("--attempt-id must be 32 lowercase hexadecimal characters")
    source = capture_source(root)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output_root = root / "runs" / "quality" / f"{stamp}_{attempt_id}"
    output_root.mkdir(parents=True)
    checks: dict[str, Any] = {}
    for name, arguments in QUALITY_COMMANDS.items():
        print(f"Verifying {name}...", flush=True)
        started = time.perf_counter()
        log = output_root / f"{name}.txt"
        with log.open("x", encoding="utf-8") as stream:
            try:
                exit_code = _run_command(root, arguments, stream)
            except subprocess.TimeoutExpired:
                stream.write(
                    "\nQuality command timed out after "
                    f"{QUALITY_COMMAND_TIMEOUT_SECONDS} seconds.\n"
                )
                exit_code = -1
            except OSError as error:
                stream.write(f"\nQuality command failed to start: {error}\n")
                exit_code = -1
        checks[name] = {
            "arguments": list(arguments),
            "exit_code": exit_code,
            "elapsed_seconds": time.perf_counter() - started,
            "log": log.relative_to(root).as_posix(),
            "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
        print(f"{name}: exit {exit_code}", flush=True)
    final_digest = source_fingerprint(root)
    passed = source.source_sha256 == final_digest and all(
        check["exit_code"] == 0 for check in checks.values()
    )
    report = {
        "passed": passed,
        "attempt_id": attempt_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": asdict(source),
        "source_sha256_before": source.source_sha256,
        "source_sha256_after": final_digest,
        "checks": checks,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if scoped:
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
