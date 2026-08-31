"""Tiny disk-backed completion fixtures; no model, controls or real EEG is run."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from core.config import config_digest
from core.provenance import SourceProvenance
from core.run_record import RunRecord
from evaluation.benchmark_audit import audit_benchmark
from evaluation.equivalence_freeze import source_margin_record
from evaluation.gate_b import evaluate_gate_b
from evaluation.gate_evidence import read_json
from scripts import evaluate_gate_b as gate_cli
from scripts import phase1_status

BENCHMARK = """[benchmark]
methods = ["eegnet"]
datasets = ["cho2017"]
seeds = [11, 23]
shots_per_class = 1
[datasets.cho2017]
artifact_directory = "artifacts"
"""
SUBJECTS = {"cho2017": ("subject_001", "subject_002")}
REQUIRED = (
    "configs/benchmark.toml",
    "runs/benchmark_status.json",
    "runs/benchmark_table.csv",
    "runs/benchmark_diagnostics.csv",
    "runs/figures/manifest.json",
    "runs/figures/cho2017_benchmark.png",
    "runs/plausibility_review.json",
    "runs/equivalence_margin_freeze.json",
    "runs/corpus_duplicate_audit.json",
)


@pytest.fixture(autouse=True)
def fixture_provenance():
    # Metadata only: keep these tiny fixtures independent of repository size
    # and Git subprocesses. Record hashing and H2 reconstruction remain real.
    with patch(
        "evaluation.equivalence_freeze.capture_source",
        return_value=SourceProvenance("fixture", "a" * 64, False),
    ):
        yield


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def bundle(root: Path, *, omit: str = "", signed: bool = False) -> dict:
    """Four records, two tiny hash-only artifacts and existing-format receipts."""

    def save(name: str, value: object) -> None:
        if name != omit:
            write_json(root / name, value)

    def raw(name: str, value: bytes) -> None:
        if name != omit:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)

    config = tomllib.loads(BENCHMARK)
    raw("configs/benchmark.toml", BENCHMARK.encode())
    raw(
        "configs/gate_b.toml",
        (
            '[gate_b]\nrequired_datasets = ["cho2017"]\nrequired_methods = ["eegnet"]\n'
            'seeds = [11, 23]\nmargin_source_dataset = "cho2017"\n'
            'margin_source_method = "eegnet"\ntarget_power = 0.8\nalpha = 0.05\n'
            f"upstream_gate_a_signed = {str(signed).lower()}\n[subjects]\ncho2017 = 2\n"
        ).encode(),
    )
    raw("configs/artifact_rejection.toml", b'[policy]\nfrozen = true\nfreeze_date = "test"\n')
    run_root = root / "runs" / "benchmark"
    for seed in (11, 23):
        for subject, correct in zip(SUBJECTS["cho2017"], (6, 7), strict=True):
            score = correct / 10
            RunRecord.create(
                config=config,
                seed=seed,
                git_commit="fixture",
                dataset="cho2017",
                fold=subject,
                metrics={
                    "benchmark_schema_version": 2.0,
                    "seed": float(seed),
                    "balanced_accuracy": score,
                    "cohen_kappa": 2 * score - 1,
                    "class_support_left": 10.0,
                    "class_support_right": 10.0,
                    "confusion_true_left_pred_left": float(correct),
                    "confusion_true_left_pred_right": float(10 - correct),
                    "confusion_true_right_pred_left": float(10 - correct),
                    "confusion_true_right_pred_right": float(correct),
                    "query_trials": 20.0,
                    "support_trials": 2.0,
                    "dataset_input_trials": 50.0,
                    "dataset_rejected_trials": 0.0,
                    "fit_seconds": 1.0,
                    "prediction_seconds": 0.1,
                    "expected_calibration_error": 0.1,
                    "coverage_at_threshold": 0.0,
                },
            ).write_json(run_root / "cho2017" / "eegnet" / f"seed_{seed}" / f"{subject}.json")
    integrity = audit_benchmark(
        run_root,
        datasets_subjects=SUBJECTS,
        methods=("eegnet",),
        seeds=(11, 23),
        expected_config_sha256=config_digest(config),
    )
    common = {key: integrity[key] for key in ("record_snapshot_sha256", "config_sha256")}
    artifact_hashes = {}
    for subject in SUBJECTS["cho2017"]:
        name = f"artifacts/{subject}.npz"
        # Only content hashes are consumed by this checker, not NPZ decoding.
        raw(name, subject.encode())
        artifact_hashes[name] = digest(subject.encode())
    artifact_snapshot = digest(
        "\n".join(f"{name}:{value}" for name, value in sorted(artifact_hashes.items())).encode()
    )
    save(
        "runs/corpus_duplicate_audit.json",
        {
            "complete": True,
            "config_sha256": config_digest(config),
            "artifact_files": artifact_hashes,
            "subject_count": 2,
            "artifact_snapshot_sha256": artifact_snapshot,
            "no_exact_train_query_copies": True,
        },
    )
    table, diagnostics, figure = b"tiny primary table\n", b"tiny diagnostics\n", b"tiny figure"
    raw("runs/benchmark_table.csv", table)
    raw("runs/benchmark_diagnostics.csv", diagnostics)
    raw("runs/figures/cho2017_benchmark.png", figure)
    save(
        "runs/benchmark_status.json",
        {
            **common,
            "complete": True,
            "table_sha256": digest(table),
            "diagnostics_sha256": digest(diagnostics),
        },
    )
    save(
        "runs/figures/manifest.json",
        {
            **common,
            "complete": True,
            "files": {"cho2017_benchmark.png": digest(figure)},
        },
    )
    save(
        "runs/plausibility_review.json",
        {
            **common,
            "local_review_complete": True,
            "artifact_snapshot_sha256": artifact_snapshot,
        },
    )
    freeze = source_margin_record(
        run_root,
        dataset="cho2017",
        method="eegnet",
        subjects=SUBJECTS["cho2017"],
        seeds=(11, 23),
        expected_config_sha256=config_digest(config),
        target_power=0.8,
        alpha=0.05,
    )
    save("runs/equivalence_margin_freeze.json", asdict(freeze))
    save("runs/artifact_audit_status.json", {"passed": True})
    return integrity


def evaluate(root: Path, *, signed: bool = False):
    return evaluate_gate_b(
        root / "runs" / "benchmark",
        project_root=root,
        dataset_subjects=SUBJECTS,
        methods=("eegnet",),
        seeds=(11, 23),
        preprocessing_frozen=True,
        margin_source_dataset="cho2017",
        margin_source_method="eegnet",
        target_power=0.8,
        alpha=0.05,
        expected_config_sha256=config_digest(tomllib.loads(BENCHMARK)),
        artifact_audit_passed=True,
        demonstrator_passed=True,
        upstream_gate_a_signed=signed,
    )


def test_complete_bundle_is_local_only_and_freeze_bytes_are_preserved(tmp_path):
    bundle(tmp_path)
    freeze = tmp_path / "runs/equivalence_margin_freeze.json"
    before = freeze.read_bytes()
    result = evaluate(tmp_path)
    assert result.local_deliverables_complete
    assert not result.passed
    assert result.equivalence_margin == read_json(freeze)["metrics"]["equivalence_margin"]
    assert freeze.read_bytes() == before


@pytest.mark.parametrize("missing", REQUIRED)
def test_missing_required_evidence_fails_closed(tmp_path, missing):
    bundle(tmp_path, omit=missing)
    result = evaluate(tmp_path, signed=True)
    assert result.benchmark_integrity_passed
    assert not result.local_deliverables_complete
    assert not result.passed


@pytest.mark.parametrize("name", REQUIRED[1:])
def test_changed_or_malformed_evidence_fails_closed(tmp_path, name):
    bundle(tmp_path)
    (tmp_path / name).write_bytes(b"tampered or malformed")
    assert not evaluate(tmp_path, signed=True).local_deliverables_complete


@pytest.mark.parametrize(
    ("name", "field", "value"),
    [
        ("benchmark_status.json", "record_snapshot_sha256", "0" * 64),
        ("benchmark_status.json", "config_sha256", "0" * 64),
        ("benchmark_status.json", "complete", "true"),
        ("figures/manifest.json", "record_snapshot_sha256", "0" * 64),
        ("figures/manifest.json", "config_sha256", "0" * 64),
        ("figures/manifest.json", "files", {}),
        ("figures/manifest.json", "files", []),
        ("figures/manifest.json", "files", {"../escape.png": "0" * 64}),
        ("plausibility_review.json", "record_snapshot_sha256", "0" * 64),
        ("plausibility_review.json", "config_sha256", "0" * 64),
        ("plausibility_review.json", "artifact_snapshot_sha256", "0" * 64),
        ("plausibility_review.json", "local_review_complete", False),
        ("plausibility_review.json", "local_review_complete", "true"),
        ("plausibility_review.json", "local_review_complete", 1),
        ("equivalence_margin_freeze.json", "config_sha256", "0" * 64),
    ],
)
def test_stale_or_invalid_receipt_fields_fail_closed(tmp_path, name, field, value):
    bundle(tmp_path)
    path = tmp_path / "runs" / name
    receipt = read_json(path)
    receipt[field] = value
    write_json(path, receipt)
    assert not evaluate(tmp_path, signed=True).local_deliverables_complete


@pytest.mark.parametrize(
    "mutation", ["source_snapshot", "margin", "boolean_config", "artifact", "record"]
)
def test_changed_freeze_source_or_inputs_cannot_reuse_completion(tmp_path, mutation):
    bundle(tmp_path)
    path = tmp_path / "runs/equivalence_margin_freeze.json"
    receipt = read_json(path)
    if mutation == "source_snapshot":
        receipt["config"]["source_record_snapshot_sha256"] = "0" * 64
        receipt["config_sha256"] = config_digest(receipt["config"])
        write_json(path, receipt)
    elif mutation == "margin":
        receipt["metrics"]["equivalence_margin"] += 0.01
        write_json(path, receipt)
    elif mutation == "boolean_config":
        # Python considers True == 1; the stored config must still hash exactly.
        receipt["config"]["frozen"] = 1
        write_json(path, receipt)
    elif mutation == "artifact":
        (tmp_path / "artifacts/subject_001.npz").write_bytes(b"changed input")
    else:
        record = tmp_path / "runs/benchmark/cho2017/eegnet/seed_11/subject_001.json"
        value = read_json(record)
        value["metrics"]["fit_seconds"] += 1
        write_json(record, value)
    assert not evaluate(tmp_path, signed=True).local_deliverables_complete


def run_phase_status(root: Path) -> dict:
    # Stub only unrelated expensive/completed checks. Gate B, exported-file
    # hashes, corpus identity, review binding and margin validation remain real.
    write_json(root / "runs/dataset_inventory.json", {"complete": True})
    write_json(root / "runs/artifact_threshold_audit.json", {"frozen": True})
    write_json(root / "runs/lsl_loopback_60s.json", {"passed": True})
    write_json(root / "runs/labram_ready_state.json", {"finite_logits": True})
    for device in ("09_cuda", "08_cpu"):
        write_json(root / f"runs/replay_demo_subject_{device}.json", {"frames": [1]})
    (root / "configs/prompt_standin.toml").write_text('name = "fixture"\n', encoding="utf-8")
    (root / "configs/eegnet_support_adaptation.toml").write_text(
        '[episode]\ndataset = "cho2017"\n',
        encoding="utf-8",
    )
    mode = dict.fromkeys(
        (
            "passed",
            "base_model_unchanged",
            "finite_query_logits",
            "frozen_backbone_unchanged",
            "query_did_not_update_state_or_prompts",
        ),
        True,
    )
    mode.update(prompt_maximum_change=1, query_output_maximum_change=1)
    write_json(
        root / "runs/prompt_transformer_smoke.json",
        {
            "passed": True,
            "config": {"name": "fixture"},
            "config_sha256": config_digest({"name": "fixture"}),
            "source": {"source_sha256": "test"},
            "modes": {name: mode for name in ("temporal_prefix", "per_block_prefix")},
        },
    )
    write_json(
        root / "runs/calibration_smoke/result.json",
        {
            "passed": True,
            "synthetic_only": True,
            "source": {"source_sha256": "test"},
            "figure_sha256": digest(b"calibration"),
        },
    )
    (root / "runs/calibration_smoke/reliability_and_coverage.png").write_bytes(b"calibration")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/falsification_criteria.md").write_text("fixture", encoding="utf-8")
    with (
        patch.object(phase1_status, "__file__", str(root / "scripts/phase1_status.py")),
        patch.object(
            phase1_status,
            "run_leakage_ci",
            return_value=SimpleNamespace(
                passed=True,
                current_source_controls_passed=True,
            ),
        ),
        patch.object(
            phase1_status, "read_quality_status", return_value={"source_sha256_after": "test"}
        ),
        patch.object(phase1_status, "verify_quality_bundle", return_value=True),
        patch.object(phase1_status, "verify_contract_freeze", return_value=True),
        patch.object(phase1_status, "verify_live_demo", return_value=True),
        patch.object(phase1_status, "audit_support_adaptation", return_value={"complete": True}),
        patch("builtins.print"),
    ):
        phase1_status.main()
    return read_json(root / "runs/phase1_status.json")


@pytest.mark.parametrize(("signed", "cached_passed"), [(False, True), (True, False)])
def test_phase1_uses_current_upstream_not_cached_gate_pass(tmp_path, signed, cached_passed):
    integrity = bundle(tmp_path, signed=signed)
    cached = {
        "passed": cached_passed,
        "local_deliverables_complete": True,
        "upstream_gate_a_signed": cached_passed,
        "record_snapshot_sha256": integrity["record_snapshot_sha256"],
    }
    cache_path = tmp_path / "runs/gate_b_status.json"
    write_json(cache_path, cached)
    before = cache_path.read_bytes()
    status = run_phase_status(tmp_path)
    assert status["local_evidence_complete"]
    assert status["gate_a_signed"] is signed
    assert status["scientifically_signed"] is signed
    assert status["gate_b"]["upstream_gate_a_signed"] is signed
    assert status["gate_b"]["passed"] is signed
    assert cache_path.read_bytes() == before


@pytest.mark.parametrize(
    "missing",
    [
        "runs/benchmark_table.csv",
        "runs/plausibility_review.json",
        "runs/equivalence_margin_freeze.json",
    ],
)
def test_phase1_rechecks_current_evidence_despite_cached_pass(tmp_path, missing):
    integrity = bundle(tmp_path, omit=missing, signed=True)
    write_json(
        tmp_path / "runs/gate_b_status.json",
        {
            "passed": True,
            "local_deliverables_complete": True,
            "upstream_gate_a_signed": True,
            "record_snapshot_sha256": integrity["record_snapshot_sha256"],
        },
    )
    status = run_phase_status(tmp_path)
    assert status["gate_a_signed"]
    assert not status["local_evidence_complete"]
    assert not status["scientifically_signed"]
    assert not status["gate_b"]["passed"]


def test_cli_requires_shared_evidence_even_with_valid_demo_and_upstream(tmp_path):
    bundle(tmp_path, omit="runs/benchmark_table.csv", signed=True)
    with (
        patch.object(gate_cli, "__file__", str(tmp_path / "scripts/evaluate_gate_b.py")),
        patch.object(gate_cli, "verify_live_demo", return_value=True),
        patch("builtins.print"),
        pytest.raises(SystemExit) as stopped,
    ):
        gate_cli.main()
    assert stopped.value.code == 1
    result = read_json(tmp_path / "runs/gate_b_status.json")
    assert result["benchmark_integrity_passed"]
    assert not result["reporting_bundle_complete"]
    assert not result["local_deliverables_complete"]
    assert not result["passed"]
