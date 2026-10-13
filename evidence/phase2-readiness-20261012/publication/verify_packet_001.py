"""Finite metadata integrity review; no model or numerical study execution."""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import digest, source_check, write_json

PACKET = ROOT / "evidence/phase2-readiness-20261012"
OUT = ROOT / "runs/coordination/phase2_readiness_20261012_v1/packet_review_001"
before = source_check(ROOT)
index = json.loads((PACKET / "index.json").read_bytes())
assert len(index["files"]) == len({row["path"] for row in index["files"]}) == 51
for row in index["files"]:
    path = PACKET / row["path"]
    assert path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], row["path"]
for row in index["current_configuration_pins"]:
    assert digest(ROOT / row["path"]) == row["sha256"]
audit = json.loads((PACKET / "reference/audit.json").read_bytes())
assert audit["retained_records_verified"] == len(audit["records"]) == 450
assert audit["saved_probability_auc_and_record_validation_passed"] is True
assert audit["new_training_or_inference"] is False and audit["raw_input_audit_replayed"] is False
env = json.loads((PACKET / "worker/environment.json").read_bytes())
assert env["import_probe_passed"] and env["loaded_module_file_count"] == len(env["loaded_module_file_hashes"]) == 3928
assert env["expected_denied_import_capability_probe_count"] == 1 and env["unexpected_denied_operation_count"] == 0
assert not env["worker_numerical_execution_qualified"] and not env["model_factory_selector_or_recorder_invoked"]
assert not env["raw_or_processed_array_or_checkpoint_opened"]
denial = env["forbidden_operation_attempts"][0]
assert denial["event"] == "socket.bind" and denial["bind_address"] == ["::1", 0]
assert env["project_and_worker_input_pins"][".venv/Lib/site-packages/urllib3/util/connection.py"] == "2633bbdb69731e5ccb5cf4e4afd65605d86c7979cc5633126f50c92d5ad74a74"
roster = json.loads((PACKET / "worker/roster.json").read_bytes())
base = {row["case_id"]: row for row in roster["cases"]}
assert len(base) == roster["planned_cases"] == 1040
assert len(roster["original_exhausted_case_conflicts"]) == 1
assert roster["original_case_claims"] == roster["original_case_failures"] == 2
assert not roster["complete_roster_feasible_under_unchanged_case_rules"]
assert roster["live_selection_gradient_ceiling"] == roster["declared_selection_steps_per_case"] == 5253
proposal_path = ROOT / "docs/phase2/cho_51_target_amendment_proposal_20261012.json"
assert digest(proposal_path) == digest(PACKET / "proposed-51-target-amendment.json")
p = json.loads(proposal_path.read_bytes())
assert not p["adopted"] and not p["experiment_freeze_signed"] and not p["scientific_execution_budget_admitted"]
actual = {(r["target_subject"], r["method"], r["model_seed"]) for r in p["proposed_case_rows"]}
expected = {(f"subject_{s:02d}", method, seed) for s in range(2, 53) for method in ("labram_linear", "labram_lora", "labram_full", "eegnet") for seed in (11, 23, 37, 53, 71)}
assert actual == expected and len(p["proposed_case_rows"]) == len(actual) == p["expected_cells"] == 1020
assert len({r["case_id"] for r in p["proposed_case_rows"]}) == 1020
assert all(row == base[row["case_id"]] for row in p["proposed_case_rows"])
assert len(p["excluded_case_rows"]) == 20 and all(row["target_subject"] == "subject_01" for row in p["excluded_case_rows"])
assert set(base) == {r["case_id"] for r in p["proposed_case_rows"] + p["excluded_case_rows"]}
assert p["original_case"]["id"] not in {r["case_id"] for r in p["proposed_case_rows"]}
assert p["original_case"]["id"] == "af0f24764e577f2223db4759582852aacc2b1b2b0b0a549f1d4b43f8f14998b5"
assert p["original_case_attempts_remaining"] == 0 and not p["original_case_recovery_reset_third_attempt_or_rename_authorized"]
assert p["available_cohort_subject_count"] == 52 and p["evaluation_target_count"] == 51
assert p["selection_steps_per_case"] == 5253 and p["planned_selection_steps_total"] == 5358060
assert p["planned_target_support_steps_total"] == 1020
primary = p["proposed_primary_analysis"]
assert primary["subjects"] == 51 and primary["complete_verified_cells_required"] == 1020
assert primary["paired_mean_interval"]["df"] == primary["paired_mean_interval"]["sample_variance_denominator"] == 50
assert not primary["imputation_allowed"] and not primary["ratified"]
assert not p["active_configuration_or_canonical_implementation_changed"]
assert p["actual_checkpoint_cohort_and_overlap"] == "unknown"
capture = json.loads((PACKET / "provenance/receipt.json").read_bytes())
assert capture["complete"] and capture["comment_count"] == 0 and not capture["cohort_coverage_verified"]
peer = json.loads((PACKET / "coordination/source028-response.json").read_bytes())
assert peer["shared_maximum_agents_including_both_roots_and_all_children_and_overlap"] == 5
assert not peer["functional_lease_issued_extended_or_prepared"] and not peer["original_parser_native8_metadata_sampling_freshthree_fixtures_c8_actual6_runtime_or_science_granted"]
assert peer["source_interval_end_utc"] == "2026-10-12T23:00:00+00:00"
assert source_check(ROOT) == before
OUT.mkdir(exist_ok=False)
result = {"schema": "pro3_readiness_packet_metadata_integrity_review_v1", "observed_utc": datetime.now(UTC).isoformat(), "passed": True, "canonical_source_sha256": before, "copied_artifacts_verified": 51, "configuration_pins_verified": 13, "reference_audit_receipt_records": 450, "worker_loaded_file_identities_retained": 3928, "original_current_case_ids": 1040, "proposed_unchanged_case_ids": 1020, "excluded_subject01_rows": 20, "original_case_attempts_remaining": 0, "proposal_adopted": False, "numerical_study_qualified": False, "scientific_admission": False, "metadata_review_not_independent_acceptance": True}
write_json(OUT / "review.json", result)
print(json.dumps(result, indent=2))
