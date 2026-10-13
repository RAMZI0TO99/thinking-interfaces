"""Recheck retained reference output bytes and arithmetic without fitting or EEG reads."""

import hashlib
import importlib.util
import json
import math
import statistics
import sys
import tomllib
import types
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import source_check, write_json
sys.path.insert(0, str(ROOT / ".venv/Lib/site-packages"))
import numpy, scipy, sklearn
dependency_versions = {"numpy": numpy.__version__, "scipy": scipy.__version__, "scikit-learn": sklearn.__version__}

# Load the unchanged pure modules directly. The general core package initializer
# imports sklearn; it is unnecessary for saved-record arithmetic and is excluded.
for package in ("core", "evaluation"):
    namespace = types.ModuleType(package)
    namespace.__path__ = [str(ROOT / package)]
    sys.modules[package] = namespace


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load("core.config", ROOT / "core/config.py")
plan_module = load("evaluation.moabb_reference_plan", ROOT / "evaluation/moabb_reference_plan.py")
record_module = load("evaluation.moabb_reference_records", ROOT / "evaluation/moabb_reference_records.py")
ReferencePlan = plan_module.ReferencePlan
validate_reference_record = record_module.validate_reference_record

BASE = ROOT / "runs/moabb_reference/evaluation/75135218cfb8104fb74a879e2a73c2e2ac19c876bf551c71ff6526afe56b0a93"
OUT = ROOT / "runs/coordination/phase2_readiness_20261012_v1/reference_audit_002"
INTEGRITY_SHA = "7906cab224131e8affba78705cdfb2d499d4b2f0ebff7939c215c92bb0bbb8df"
INPUT_AUDIT_SHA = "e80ed6a7e0a3d21b453c031733671f149f44536055e06145459c5d3ca0e3922a"
SNAPSHOT = "196b419bf2f15c02fd55b9046fd78260605e2be869e3695bb09196616921427e"
EXECUTION_SHA = "ea84cc79dc1e233504b441e05cc365b3879fc0bc91f16cab83cac7ff2b14cf45"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


source = source_check(ROOT)
decision_path = ROOT / "docs/phase2/gate_a_acceptance_20261012.json"
assert digest(decision_path) == "0870b98fc957df04cae925fec411929a7759fe3a9a8be6bcb2108f6270356e93"
decision = json.loads(decision_path.read_bytes())
assert decision["scientific_gate_a_signed"] and not decision["experiment_freeze_signed"] and not decision["scientific_execution_budget_admitted"]
assert digest(BASE / "integrity.json") == INTEGRITY_SHA
integrity = json.loads((BASE / "integrity.json").read_bytes())
input_path = ROOT / "runs/moabb_reference/input_audits/20260901T202959749411Z.json"
assert digest(input_path) == INPUT_AUDIT_SHA
input_audit = json.loads(input_path.read_bytes())
assert input_audit["complete"] and input_audit["existing_inputs_match"] and not input_audit["mismatches"]
assert input_audit["record_snapshot_sha256"] == integrity["record_snapshot_sha256"] == SNAPSHOT
assert input_audit["record_files"] == integrity["record_files"]
config = tomllib.loads((ROOT / "configs/moabb_reference_evaluation.toml").read_text(encoding="utf-8"))
environment = tomllib.loads((ROOT / "configs/moabb_reference_environment.toml").read_text(encoding="utf-8"))
plan = ReferencePlan.from_config(config)
scores = {}
rows = []
for unit in plan.units:
    name = unit.key + ".json"
    path = BASE / name
    raw = path.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    assert actual_sha == integrity["record_files"][name]
    payload = json.loads(raw)
    assert payload["execution_sha256"] == EXECUTION_SHA
    assert payload["record"]["config"] == {"environment": environment, "evaluation": config, "unit": asdict(unit)}
    # Raw-file hashes are historical declarations, checked against the pinned
    # prior input audit, not refreshed by opening any raw recordings here.
    raw_hashes = payload["result"]["raw_file_sha256"]
    score = validate_reference_record(
        payload, unit=unit, resolved_config=payload["record"]["config"],
        execution_sha256=EXECUTION_SHA, raw_hashes=raw_hashes,
    )
    scores[(unit.model_seed, unit.subject, unit.session, unit.fold_index)] = score
    rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": actual_sha, "roc_auc": score, "unit": asdict(unit)})
assert len(rows) == len(integrity["record_files"]) == 450
anchor_sessions = [statistics.fmean(scores[(42, subject, session, fold)] for fold in range(5))
    for subject in range(1, 10) for session in ("0train", "1test")]
anchor = statistics.fmean(anchor_sessions)
repeat_subjects = {str(subject): statistics.fmean(
    scores[(seed, subject, session, fold)]
    for seed in (11, 23, 37, 53) for session in ("0train", "1test") for fold in range(5)
) for subject in range(1, 10)}
repeat_mean = statistics.fmean(repeat_subjects.values())
owner = json.loads((ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json").read_bytes())
previous = owner["historical_phase_i"]["summary"]
assert math.isclose(anchor, previous["reference_seed_result"]["mean_roc_auc"], rel_tol=0, abs_tol=1e-14)
assert math.isclose(repeat_mean, previous["repeat_seed_subject_interval"]["mean"], rel_tol=0, abs_tol=1e-14)
for subject, value in repeat_subjects.items():
    assert math.isclose(value, previous["repeat_seed_subject_interval"]["subject_means"][subject], rel_tol=0, abs_tol=1e-14)
assert source_check(ROOT) == source
assert digest(BASE / "integrity.json") == INTEGRITY_SHA and digest(input_path) == INPUT_AUDIT_SHA
result = {
    "schema": "retained_gate_a_reference_output_reaudit_v1",
    "observed_utc": datetime.now(UTC).isoformat(),
    "canonical_source_sha256": source,
    "retained_records_verified": 450,
    "audit_dependency_versions": dependency_versions,
    "historical_environment_recreated": False,
    "historical_record_snapshot_sha256": SNAPSHOT,
    "historical_integrity_sha256": INTEGRITY_SHA,
    "historical_input_audit_sha256": INPUT_AUDIT_SHA,
    "saved_probability_auc_and_record_validation_passed": True,
    "anchor_fits": 90, "repeat_fits": 360, "independent_subject_count": 9,
    "published_mean_roc_auc": 0.7715,
    "reference_seed_mean_roc_auc": anchor,
    "reference_seed_difference": anchor - 0.7715,
    "reference_seed_subject_session_means": anchor_sessions,
    "repeat_seed_subject_mean_roc_auc": repeat_mean,
    "repeat_seed_subject_means": repeat_subjects,
    "repeat_interval_recomputed": False,
    "confidence_interval_is_acceptance_band": False,
    "published_sd_is_acceptance_band": False,
    "scientific_gate_a_signed": True,
    "audit_supplies_scientific_signature": False,
    "direct_owner_gate_a_decision_sha256": digest(decision_path),
    "current_source_training_recertified": False,
    "raw_input_audit_replayed": False,
    "new_training_or_inference": False,
    "actual_checkpoint_recording_coverage": "unknown",
    "scientific_admission": False,
    "original_case_attempts_remaining": 0,
    "records": rows,
}
OUT.mkdir(exist_ok=False)
write_json(OUT / "audit.json", result)
print(json.dumps({k: v for k, v in result.items() if k not in ("records", "reference_seed_subject_session_means", "repeat_seed_subject_means")}, indent=2))
