from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.gate_b import evaluate_gate_b
from evaluation.gate_evidence import read_json
from evaluation.live_demo_audit import verify_live_demo


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    gate_config = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    gate = cast(Mapping[str, Any], gate_config["gate_b"])
    subject_counts = cast(Mapping[str, Any], gate_config["subjects"])
    benchmark_config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    benchmark_datasets = cast(Mapping[str, Any], benchmark_config["datasets"])
    artifact_config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "artifact_rejection.toml")
    )
    policy = cast(Mapping[str, Any], artifact_config["policy"])
    artifact_audit_path = root / "runs" / "artifact_audit_status.json"
    artifact_audit = read_json(artifact_audit_path)
    # Require the same hash-verified, held-out, visible native LSL evidence as
    # the Phase I completion report; legacy array frames are not sufficient.
    demonstrator_passed = verify_live_demo(root)
    datasets = tuple(cast(list[str], gate["required_datasets"]))
    dataset_subjects: dict[str, tuple[str, ...]] = {}
    for dataset in datasets:
        settings = cast(Mapping[str, Any], benchmark_datasets[dataset])
        directory = root / str(settings["artifact_directory"])
        subjects = tuple(path.stem for path in sorted(directory.glob("subject_*.npz")))
        expected = int(subject_counts[dataset])
        if len(subjects) != expected:
            raise SystemExit(f"{dataset} has {len(subjects)} artifacts; expected {expected}")
        dataset_subjects[dataset] = subjects
    result = evaluate_gate_b(
        root / "runs" / "benchmark",
        project_root=root,
        dataset_subjects=dataset_subjects,
        methods=tuple(cast(list[str], gate["required_methods"])),
        seeds=tuple(cast(list[int], gate["seeds"])),
        preprocessing_frozen=policy["frozen"] is True and bool(policy["freeze_date"]),
        margin_source_dataset=str(gate["margin_source_dataset"]),
        margin_source_method=str(gate["margin_source_method"]),
        target_power=float(gate["target_power"]),
        alpha=float(gate["alpha"]),
        expected_config_sha256=config_digest(benchmark_config),
        artifact_audit_passed=artifact_audit.get("passed") is True,
        demonstrator_passed=demonstrator_passed,
        upstream_gate_a_signed=gate.get("upstream_gate_a_signed") is True,
    )
    output = root / "runs" / "gate_b_status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
