from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.benchmark_audit import audit_benchmark
from evaluation.benchmark_diagnostics import aggregate_diagnostics, read_audited_snapshot


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    expected = config_digest(config)
    subjects = {
        name: tuple(
            path.stem
            for path in sorted(
                (root / config["datasets"][name]["artifact_directory"]).glob("subject_*.npz")
            )
        )
        for name in config["benchmark"]["datasets"]
    }
    integrity = audit_benchmark(
        root / "runs" / "benchmark",
        datasets_subjects=subjects,
        methods=config["benchmark"]["methods"],
        seeds=config["benchmark"]["seeds"],
        expected_config_sha256=expected,
    )
    if integrity["invalid_records"] or integrity["unexpected_records"]:
        raise ValueError("record integrity failed; cost report was not overwritten")
    diagnostics = aggregate_diagnostics(
        read_audited_snapshot(
            root / "runs" / "benchmark", integrity["record_files"], expected_config_sha256=expected
        ),
        confidence_threshold=config["benchmark"]["confidence_threshold"],
    )
    rows = [
        {
            "dataset": row.dataset,
            "method": row.method,
            "records": row.record_count,
            "computed_records": row.computed_records,
            "reused_records": row.reused_records,
            "seconds": row.measured_fit_seconds + row.measured_prediction_seconds,
        }
        for row in diagnostics
    ]
    total_seconds = sum(
        row.measured_fit_seconds + row.measured_prediction_seconds for row in diagnostics
    )
    report = {
        "cost_basis": "local laptop; no metered instance charge",
        "complete": integrity["complete"],
        "config_sha256": expected,
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "scope": "final-hash benchmark fit and prediction only; not total project wall time",
        "excluded": [
            "preprocessing",
            "cache/alignment preparation",
            "data loading",
            "cooldowns",
            "earlier debugging/reproduction attempts",
            "auxiliary controls and calibration",
            "reporting",
            "unmeasured electricity and hardware cost",
        ],
        "records": sum(row.record_count for row in diagnostics),
        "measured_fit_prediction_seconds": total_seconds,
        "measured_fit_prediction_hours": total_seconds / 3600.0,
        "rows": rows,
    }
    output = root / "runs" / "benchmark_cost_report.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
