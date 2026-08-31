from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from core.contract_freeze import verify_contract_freeze
from evaluation.benchmark_audit import audit_benchmark
from evaluation.gate_b import evaluate_gate_b
from evaluation.gate_evidence import hash_matches, read_json
from evaluation.leakage_ci import run_leakage_ci
from evaluation.live_demo_audit import verify_live_demo
from evaluation.quality_audit import read_quality_status, verify_quality_bundle
from evaluation.support_adaptation_audit import audit_support_adaptation


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    benchmark_config = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    benchmark = cast(Mapping[str, Any], benchmark_config["benchmark"])
    gate_b_config = cast(Mapping[str, Any], load_toml(root / "configs" / "gate_b.toml"))
    expected_subjects = cast(Mapping[str, Any], gate_b_config["subjects"])
    methods = cast(list[str], benchmark["methods"])
    seeds = cast(list[int], benchmark["seeds"])
    expected_records = {
        dataset: int(expected_subjects[dataset]) * len(methods) * len(seeds)
        for dataset in cast(list[str], benchmark["datasets"])
    }
    dataset_subjects = {
        dataset: tuple(
            path.stem
            for path in sorted(
                (root / benchmark_config["datasets"][dataset]["artifact_directory"]).glob(
                    "subject_*.npz"
                )
            )
        )
        for dataset in expected_records
    }
    integrity = audit_benchmark(
        root / "runs" / "benchmark",
        datasets_subjects=dataset_subjects,
        methods=methods,
        seeds=seeds,
        expected_config_sha256=config_digest(benchmark_config),
    )
    counts = integrity["valid_records_by_dataset"]
    benchmark_counts = {
        dataset: {
            "valid_records": counts.get(dataset, 0),
            "expected_records": expected,
            "complete": counts.get(dataset, 0) == expected,
        }
        for dataset, expected in expected_records.items()
    }
    inventory = read_json(root / "runs" / "dataset_inventory.json")
    artifact_audit = read_json(root / "runs" / "artifact_audit_status.json")
    threshold_audit = read_json(root / "runs" / "artifact_threshold_audit.json")
    leakage = run_leakage_ci(root)
    lsl = read_json(root / "runs" / "lsl_loopback_60s.json")
    labram = read_json(root / "runs" / "labram_ready_state.json")
    gpu_demo = read_json(root / "runs" / "replay_demo_subject_09_cuda.json")
    cpu_demo = read_json(root / "runs" / "replay_demo_subject_08_cpu.json")
    quality = read_quality_status(root)
    quality_passed = verify_quality_bundle(root, quality)
    contract_frozen = verify_contract_freeze(root)
    prompt_smoke = read_json(root / "runs" / "prompt_transformer_smoke.json")
    prompt_config = load_toml(root / "configs" / "prompt_standin.toml")
    prompt_modes = prompt_smoke.get("modes", {})
    prompt_standin_passed = bool(
        prompt_smoke.get("passed") is True
        and prompt_smoke.get("config") == prompt_config
        and prompt_smoke.get("config_sha256") == config_digest(prompt_config)
        and quality_passed
        and prompt_smoke.get("source", {}).get("source_sha256")
        == quality.get("source_sha256_after")
        and set(prompt_modes) == {"temporal_prefix", "per_block_prefix"}
        and all(
            all(
                row.get(key) is True
                for key in (
                    "passed",
                    "base_model_unchanged",
                    "finite_query_logits",
                    "frozen_backbone_unchanged",
                    "query_did_not_update_state_or_prompts",
                )
            )
            and row.get("prompt_maximum_change", 0) > 0
            and row.get("query_output_maximum_change", 0) > 0
            for row in prompt_modes.values()
        )
    )
    live_demo_passed = verify_live_demo(root)
    gate_settings = gate_b_config["gate_b"]
    policy = cast(Mapping[str, Any], load_toml(root / "configs" / "artifact_rejection.toml"))[
        "policy"
    ]
    gate_a_signed = gate_settings.get("upstream_gate_a_signed") is True
    # Re-evaluate current evidence and the current upstream decision. A cached
    # gate_b_status.json (even for this benchmark snapshot) is not an approval.
    gate_b = evaluate_gate_b(
        root / "runs" / "benchmark",
        project_root=root,
        dataset_subjects={
            name: dataset_subjects[name] for name in gate_settings["required_datasets"]
        },
        methods=tuple(gate_settings["required_methods"]),
        seeds=tuple(gate_settings["seeds"]),
        preprocessing_frozen=policy["frozen"] is True and bool(policy["freeze_date"]),
        margin_source_dataset=gate_settings["margin_source_dataset"],
        margin_source_method=gate_settings["margin_source_method"],
        target_power=gate_settings["target_power"],
        alpha=gate_settings["alpha"],
        expected_config_sha256=config_digest(benchmark_config),
        artifact_audit_passed=artifact_audit.get("passed") is True,
        demonstrator_passed=live_demo_passed,
        upstream_gate_a_signed=gate_a_signed,
    ).as_dict()
    reports_complete = gate_b["reporting_bundle_complete"] is True
    review_complete = gate_b["plausibility_review_complete"] is True
    margin_frozen = gate_b["equivalence_margin_frozen"] is True
    corpus_current = gate_b["corpus_duplicate_audit_current"] is True
    no_exact_copies = gate_b["no_exact_train_query_copies"] is True

    calibration_smoke = read_json(root / "runs" / "calibration_smoke" / "result.json")
    calibration_diagram_passed = bool(
        calibration_smoke.get("passed") is True
        and calibration_smoke.get("synthetic_only") is True
        and quality_passed
        and calibration_smoke.get("source", {}).get("source_sha256")
        == quality.get("source_sha256_after")
        and hash_matches(
            root / "runs" / "calibration_smoke" / "reliability_and_coverage.png",
            calibration_smoke.get("figure_sha256"),
        )
    )
    support_settings = cast(
        Mapping[str, Any], load_toml(root / "configs" / "eegnet_support_adaptation.toml")
    )
    support_dataset = str(support_settings["episode"]["dataset"])
    support_audit = audit_support_adaptation(
        root / "runs" / "support_adaptation" / support_dataset,
        settings=support_settings,
        subjects=dataset_subjects[support_dataset],
        benchmark_sha256=config_digest(benchmark_config),
    )
    local_evidence_complete = bool(
        inventory.get("complete")
        and artifact_audit.get("passed")
        and threshold_audit.get("frozen")
        and leakage.passed
        and lsl.get("passed")
        and labram.get("finite_logits")
        and gpu_demo.get("frames")
        and cpu_demo.get("frames")
        and all(item["complete"] for item in benchmark_counts.values())
        and integrity["complete"]
        and review_complete
        and reports_complete
        and quality_passed
        and contract_frozen
        and prompt_standin_passed
        and calibration_diagram_passed
        and live_demo_passed
        and no_exact_copies
        and margin_frozen
        and support_audit["complete"]
        and gate_b.get("local_deliverables_complete")
        and gate_b.get("record_snapshot_sha256") == integrity["record_snapshot_sha256"]
        and (root / "docs" / "falsification_criteria.md").is_file()
    )
    report = {
        "local_evidence_complete": local_evidence_complete,
        "scientifically_signed": bool(
            local_evidence_complete and gate_a_signed and gate_b.get("passed") is True
        ),
        "gate_a_signed": gate_a_signed,
        "gate_b": gate_b,
        "benchmark": benchmark_counts,
        "benchmark_integrity_passed": integrity["complete"],
        "benchmark_invalid_records": integrity["invalid_records"],
        "benchmark_unexpected_records": integrity["unexpected_records"],
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        "plausibility_review_complete": review_complete,
        "benchmark_reporting_bundle_complete": reports_complete,
        "current_source_quality_passed": quality_passed,
        "local_contract_v1_frozen": contract_frozen,
        "prompt_attention_standin_passed": prompt_standin_passed,
        "calibration_diagram_smoke_passed": calibration_diagram_passed,
        "integrated_lsl_native_demo_passed": live_demo_passed,
        "corpus_duplicate_audit_current": corpus_current,
        "no_exact_train_query_copies": no_exact_copies,
        "equivalence_margin_frozen": margin_frozen,
        "source_then_support_baseline": support_audit,
        "public_datasets_complete": bool(inventory.get("complete")),
        "artifact_audit_passed": bool(artifact_audit.get("passed")),
        "preprocessing_frozen": bool(threshold_audit.get("frozen")),
        "leakage_ci_passed": leakage.passed,
        "current_source_controls_passed": leakage.current_source_controls_passed,
        "lsl_loopback_passed": bool(lsl.get("passed")),
        "labram_ready": bool(labram.get("finite_logits")),
        "gpu_demo_recorded": bool(gpu_demo.get("frames")),
        "cpu_fallback_recorded": bool(cpu_demo.get("frames")),
    }
    output = root / "runs" / "phase1_status.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
