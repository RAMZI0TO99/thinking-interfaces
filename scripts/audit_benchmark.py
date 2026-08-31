from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.benchmark_audit import audit_benchmark


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    gate = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    benchmark = config["benchmark"]
    subjects: dict[str, tuple[str, ...]] = {}
    for dataset in benchmark["datasets"]:
        directory = root / config["datasets"][dataset]["artifact_directory"]
        subjects[dataset] = tuple(path.stem for path in sorted(directory.glob("subject_*.npz")))
        if len(subjects[dataset]) != int(gate["subjects"][dataset]):
            raise SystemExit(f"{dataset}: processed subject inventory is incomplete")
    report = audit_benchmark(
        root / "runs" / "benchmark",
        datasets_subjects=subjects,
        methods=benchmark["methods"],
        seeds=benchmark["seeds"],
        expected_config_sha256=config_digest(config),
    )
    output = root / "runs" / "benchmark_integrity_audit.json"
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "report": str(output),
                "complete": report["complete"],
                "valid_records": report["valid_records"],
                "expected_records": report["expected_records"],
                "invalid_records": report["invalid_records"],
                "missing_records": len(report["missing_records"]),
                "flagged_subjects": len(report["flagged_subjects"]),
                "flagged_methods": report["flagged_methods"],
            },
            indent=2,
        )
    )
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
