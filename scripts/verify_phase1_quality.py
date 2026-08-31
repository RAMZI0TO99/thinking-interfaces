"""Run local lint, type and regression checks and save an exact-source receipt."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.provenance import capture_source, source_fingerprint
from evaluation.quality_audit import QUALITY_COMMANDS


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = capture_source(root)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output_root = root / "runs" / "quality" / stamp
    output_root.mkdir(parents=True)
    checks: dict[str, Any] = {}
    for name, arguments in QUALITY_COMMANDS.items():
        print(f"Verifying {name}...", flush=True)
        started = time.perf_counter()
        log = output_root / f"{name}.txt"
        with log.open("w", encoding="utf-8") as stream:
            try:
                result = subprocess.run(
                    [sys.executable, *arguments],
                    cwd=root,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    timeout=600,
                    check=False,
                )
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                stream.write("\nQuality command timed out after 600 seconds.\n")
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
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": asdict(source),
        "source_sha256_before": source.source_sha256,
        "source_sha256_after": final_digest,
        "checks": checks,
    }
    output = root / "runs" / "quality_status.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
