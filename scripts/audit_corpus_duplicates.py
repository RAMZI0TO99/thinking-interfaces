"""Audit every public subject for exact signal copies without fitting a model."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from core.config import load_toml
from core.provenance import capture_source
from evaluation.corpus_duplicates import audit_corpus_duplicates, expected_subject_inventory


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    gate = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    subjects = expected_subject_inventory(root, config, gate["subjects"])
    source = capture_source(root)
    print(
        f"Auditing {sum(map(len, subjects.values()))} subjects, one artifact at a time...",
        flush=True,
    )
    report = audit_corpus_duplicates(root, config=config, subjects=subjects)
    report["source"] = asdict(source)
    output = root / "runs" / "corpus_duplicate_audit.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(
        json.dumps(
            {
                "report": str(output),
                "complete": report["complete"],
                "subjects": report["subject_count"],
                "retained_trials": report["retained_trials"],
                "rejected_trials": report["rejected_trials"],
                "duplicate_groups": len(report["duplicate_groups"]),
                "exact_train_query_copy_groups": report["exact_train_query_copy_groups"],
                "artifact_snapshot_sha256": report["artifact_snapshot_sha256"],
            },
            indent=2,
        )
    )
    return 0 if report["no_exact_train_query_copies"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
