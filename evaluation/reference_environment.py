"""Lightweight identity/resource checks before loading reference ML dependencies."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def resource_gate(
    runtime: Mapping[str, Any], *, free_memory_gib: float, free_disk_gib: float
) -> dict[str, object]:
    """Fail closed; insufficient resources defer work, not a successful smoke test."""
    minimum_memory = float(runtime["minimum_free_memory_gib"])
    stop_memory = float(runtime["stop_below_free_memory_gib"])
    minimum_disk = float(runtime["minimum_free_disk_gib"])
    values = (minimum_memory, stop_memory, minimum_disk, free_memory_gib, free_disk_gib)
    if not all(math.isfinite(value) and value >= 0 for value in values):
        raise ValueError("resource observations and limits must be finite and nonnegative")
    if not 0 < stop_memory < minimum_memory or minimum_disk <= 0:
        raise ValueError("invalid reference runtime resource limits")
    reasons = []
    if free_memory_gib < minimum_memory:
        reasons.append("insufficient_free_memory")
    if free_disk_gib < minimum_disk:
        reasons.append("insufficient_free_disk")
    return {
        "ready": not reasons,
        "reasons": reasons,
        "free_memory_gib": free_memory_gib,
        "free_disk_gib": free_disk_gib,
        "minimum_free_memory_gib": minimum_memory,
        "minimum_free_disk_gib": minimum_disk,
    }


def verify_reference_files(
    site_packages: Path, expected: Mapping[str, str]
) -> dict[str, str]:
    """Verify installed bytes against the reviewed, revision-pinned upstream files."""
    root = site_packages.resolve(strict=True)
    observed = {}
    if not expected:
        raise ValueError("reference source manifest must not be empty")
    for relative, digest in expected.items():
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root) or path.suffix != ".py":
            raise ValueError("reference source path must be a Python file inside site-packages")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"reference source mismatch: {relative}")
        observed[relative] = actual
    return observed
