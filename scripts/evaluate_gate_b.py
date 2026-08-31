from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.gate_b import evaluate_gate_b


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    gate_config = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    gate = cast(Mapping[str, Any], gate_config["gate_b"])
    subject_counts = cast(Mapping[str, Any], gate_config["subjects"])
    benchmark_config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml")
    )
    benchmark_datasets = cast(Mapping[str, Any], benchmark_config["datasets"])
    artifact_config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "artifact_rejection.toml")
    )
    policy = cast(Mapping[str, Any], artifact_config["policy"])
    artifact_audit_path = root / "runs" / "artifact_audit_status.json"
    artifact_audit = (
        json.loads(artifact_audit_path.read_text(encoding="utf-8"))
        if artifact_audit_path.is_file()
        else {}
    )
    demo_path = root / "runs" / "replay_demo_subject_09_cuda.json"
    demonstrator_passed = False
    if demo_path.is_file():
        demo = json.loads(demo_path.read_text(encoding="utf-8"))
        demonstrator_passed = bool(demo.get("frames")) and int(
            demo.get("query_trials", 0)
        ) > 0
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
        dataset_subjects=dataset_subjects,
        methods=tuple(cast(list[str], gate["required_methods"])),
        seeds=tuple(cast(list[int], gate["seeds"])),
        preprocessing_frozen=bool(policy["frozen"]) and bool(policy["freeze_date"]),
        margin_source_dataset=str(gate["margin_source_dataset"]),
        margin_source_method=str(gate["margin_source_method"]),
        target_power=float(gate["target_power"]),
        alpha=float(gate["alpha"]),
        expected_config_sha256=config_digest(benchmark_config),
        artifact_audit_passed=bool(artifact_audit.get("passed", False)),
        demonstrator_passed=demonstrator_passed,
        upstream_gate_a_signed=bool(gate["upstream_gate_a_signed"]),
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
