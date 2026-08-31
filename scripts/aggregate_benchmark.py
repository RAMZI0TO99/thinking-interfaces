from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.benchmark_audit import audit_benchmark
from evaluation.benchmark_diagnostics import (
    aggregate_diagnostics,
    read_audited_snapshot,
    write_diagnostics_csv,
)
from evaluation.reporting import (
    RecordObservation,
    aggregate_observations,
    write_benchmark_csv,
)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(project_root / "configs" / "benchmark.toml"))
    benchmark = cast(Mapping[str, Any], config["benchmark"])
    datasets = cast(Mapping[str, Any], config["datasets"])
    subjects: dict[str, tuple[str, ...]] = {}
    for name in cast(list[str], benchmark["datasets"]):
        dataset = cast(Mapping[str, Any], datasets[name])
        directory = project_root / str(dataset["artifact_directory"])
        subjects[name] = tuple(path.stem for path in sorted(directory.glob("subject_*.npz")))
    run_root = project_root / "runs" / "benchmark"
    expected_config_sha256 = config_digest(config)
    integrity = audit_benchmark(
        run_root,
        datasets_subjects=subjects,
        methods=cast(list[str], benchmark["methods"]),
        seeds=cast(list[int], benchmark["seeds"]),
        expected_config_sha256=expected_config_sha256,
    )
    if integrity["invalid_records"] or integrity["unexpected_records"]:
        raise ValueError("result integrity failed; no aggregate table was overwritten")
    records = read_audited_snapshot(
        run_root, integrity["record_files"], expected_config_sha256=expected_config_sha256
    )
    observations = tuple(
        RecordObservation(
            record.dataset,
            record.method,
            record.subject,
            record.seed,
            record.metrics["balanced_accuracy"],
        )
        for record in records
    )
    rows = aggregate_observations(
        observations, confidence_level=float(benchmark["confidence_level"])
    )
    diagnostic_rows = aggregate_diagnostics(
        records, confidence_threshold=float(benchmark["confidence_threshold"])
    )
    table = write_benchmark_csv(rows, project_root / "runs" / "benchmark_table.csv")
    diagnostics = write_diagnostics_csv(
        diagnostic_rows,
        project_root / "runs" / "benchmark_diagnostics.csv",
    )
    missing = integrity["missing_records"]
    report = {
        "records": len(observations),
        "table_rows": len(rows),
        "missing_records": len(missing),
        "complete": integrity["complete"],
        "config_sha256": expected_config_sha256,
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "uncertainty": "subject SD and subject 95% interval; separate SD across seed means",
        "table": str(table),
        "diagnostics_table": str(diagnostics),
        "table_sha256": hashlib.sha256(table.read_bytes()).hexdigest(),
        "diagnostics_sha256": hashlib.sha256(diagnostics.read_bytes()).hexdigest(),
        "diagnostics_notes": (
            "Metrics average seeds within subjects. Class/confusion counts include repeated-seed "
            "query evaluations, not independent samples. Selective means exclude empty coverage "
            "and expose their contributing counts. Amortized batch timing is not online latency."
        ),
        "first_missing": list(missing[:20]),
    }
    output = project_root / "runs" / "benchmark_status.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
