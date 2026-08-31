from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.benchmark_audit import audit_benchmark
from evaluation.corpus_duplicates import expected_subject_inventory, verify_corpus_snapshot
from evaluation.plausibility_packet import build_plausibility_packet


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    gate = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    subjects = expected_subject_inventory(root, config=config, counts=gate["subjects"])
    corpus = json.loads((root / "runs" / "corpus_duplicate_audit.json").read_text("utf-8"))
    if not verify_corpus_snapshot(root, corpus, config=config, subjects=subjects):
        raise SystemExit("Corpus snapshot is stale; rerun the independent corpus audit first.")
    integrity = audit_benchmark(
        root / "runs" / "benchmark",
        datasets_subjects=subjects,
        methods=config["benchmark"]["methods"],
        seeds=config["benchmark"]["seeds"],
        expected_config_sha256=config_digest(config),
    )
    if integrity["invalid_records"] or integrity["unexpected_records"]:
        raise SystemExit("Resolve invalid or unexpected benchmark records before review.")
    packet = build_plausibility_packet(root, config=config, integrity=integrity, corpus=corpus)
    path = root / "runs" / "plausibility_packet.json"
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(packet, indent=2, sort_keys=True, allow_nan=False) + "\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "packet": str(path),
                "benchmark_complete": packet["benchmark_complete"],
                "records_cross_checked": packet["records_cross_checked"],
                "record_input_count_mismatches": packet["record_input_count_mismatches"],
                "flagged_cases": len(packet["flagged_subject_method_cases"]),
                "local_review_complete": False,
            },
            indent=2,
        )
    )
    if not packet["record_input_counts_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
