"""Fail-closed checks for an exact-source local quality verification bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from core.provenance import source_fingerprint

QUALITY_COMMANDS = {
    "lint": (
        "-m",
        "ruff",
        "check",
        "core",
        "encoder",
        "adaptation",
        "data",
        "realtime",
        "evaluation",
        "scripts",
        "tests",
    ),
    "types": (
        "-m",
        "mypy",
        "core",
        "encoder",
        "adaptation",
        "data",
        "realtime",
        "evaluation",
        "scripts",
    ),
    "tests": ("-m", "pytest", "-q"),
}


def verify_quality_bundle(root: Path, payload: dict[str, Any]) -> bool:
    """Reject stale source, failed/omitted checks, changed logs and escaped paths."""
    try:
        expected = source_fingerprint(root)
        if not (
            payload.get("passed") is True
            and payload.get("source_sha256_before") == expected
            and payload.get("source_sha256_after") == expected
        ):
            return False
        checks = payload["checks"]
        if not isinstance(checks, dict) or set(checks) != set(QUALITY_COMMANDS):
            return False
        log_root = (root / "runs" / "quality").resolve()
        for name, command in QUALITY_COMMANDS.items():
            check = checks[name]
            log = (root / check["log"]).resolve()
            if not (
                check["arguments"] == list(command)
                and type(check["exit_code"]) is int
                and check["exit_code"] == 0
                and log.is_relative_to(log_root)
                and log.is_file()
                and hashlib.sha256(log.read_bytes()).hexdigest() == check["log_sha256"]
            ):
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def read_quality_status(root: Path) -> dict[str, Any]:
    try:
        payload: object = json.loads((root / "runs" / "quality_status.json").read_text("utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError):
        return {}
