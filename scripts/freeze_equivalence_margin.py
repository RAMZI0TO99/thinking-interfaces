from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.equivalence_freeze import source_margin_record, write_margin_once


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    gate = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    dataset = str(gate["gate_b"]["margin_source_dataset"])
    directory = root / config["datasets"][dataset]["artifact_directory"]
    subjects = tuple(path.stem for path in sorted(directory.glob("subject_*.npz")))
    if len(subjects) != int(gate["subjects"][dataset]):
        raise ValueError("complete source subject inventory is required")
    record = source_margin_record(
        root / "runs" / "benchmark",
        dataset=dataset,
        method=str(gate["gate_b"]["margin_source_method"]),
        subjects=subjects,
        seeds=tuple(config["benchmark"]["seeds"]),
        expected_config_sha256=config_digest(config),
        target_power=float(gate["gate_b"]["target_power"]),
        alpha=float(gate["gate_b"]["alpha"]),
    )
    output = root / "runs" / "equivalence_margin_freeze.json"
    created = write_margin_once(record, output)
    print(json.dumps({"created": created, "path": str(output), **record.metrics}, indent=2))


if __name__ == "__main__":
    main()
