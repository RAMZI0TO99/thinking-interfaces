"""Enable only the reviewed Cho EA+tangent scheduling path, with fixed guards."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from evaluation.process_eigh_probe import available_memory_gib, numpy_backend

QUALIFICATION_PATH = "runs/runtime_probe/20260831T142216253834Z/result.json"
QUALIFICATION_SHA256 = "4f793152d3e5c66f9c03689d0774407891746a2aace9ae10cfae21110be38bf6"


def process_eigh_enabled(runtime: Mapping[str, Any]) -> bool:
    settings = runtime.get("tangent_process", {})
    if not isinstance(settings, dict) or set(settings) - {"enabled"}:
        raise ValueError("unknown or invalid tangent process runtime settings")
    enabled = settings.get("enabled", False)
    if type(enabled) is not bool:
        raise ValueError("tangent process enablement must be an explicit boolean")
    return enabled


def process_eigh_startup_ready(
    root: Path,
    *,
    enabled: bool,
    dataset: str,
    methods: Sequence[str],
    benchmark_sha256: str,
) -> bool:
    """Called before heavy model imports; false means use the original calculation.

    Missing/tampered qualification evidence fails closed. Insufficient memory or
    a different backend disables the optional scheduling path, not the benchmark.
    """
    if type(enabled) is not bool:
        raise ValueError("startup enablement must be an explicit boolean")
    if not enabled or dataset != "cho2017" or "ea_tangent_lr" not in methods:
        return False
    raw = (root / QUALIFICATION_PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != QUALIFICATION_SHA256:
        raise ValueError("the reviewed process-eigh qualification receipt changed")
    report = json.loads(raw)
    if (
        report["passed"] is not True
        or report["benchmark_config_sha256"] != benchmark_sha256
        or report["source"]["git_dirty"] is not False
        or report["probe_config"]["probe"]["method"] != "ea_tangent_lr"
        or [row["subject"] for row in report["rows"]] != ["subject_01", "subject_02"]
    ):
        raise ValueError("qualification is not the reviewed two-fold benchmark protocol")
    backend = report["rows"][0]["isolated_process_eigh"]["verified_backend"]
    for row in report["rows"]:
        expected_path = (
            f"runs/benchmark/cho2017/ea_tangent_lr/seed_11/{row['subject']}.json"
        )
        if (
            row["reference_record"] != expected_path
            or hashlib.sha256((root / expected_path).read_bytes()).hexdigest()
            != row["reference_sha256"]
            or row["exact_non_timing_metrics_equal"] is not True
            or row["differences"]
            or row["isolated_process_eigh"]["verified_backend"] != backend
        ):
            raise ValueError("qualification reference or exact-parity evidence changed")
    return available_memory_gib() >= 10.0 and numpy_backend() == backend
