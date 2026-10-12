"""Record four explicitly delegated design choices; no execution or gate signature."""

import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import source_check, write_json

OWNER_PATH = ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json"
OWNER_SHA = "2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400"
raw = OWNER_PATH.read_bytes()
assert hashlib.sha256(raw).hexdigest() == OWNER_SHA
packet = json.loads(raw)
source = source_check(ROOT)
assert source == packet["canonical_source_sha256"]
for row in packet["current_configuration_pins"]:
    assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
candidate = packet["candidate_template"]["pin"]
candidate_raw = (ROOT / candidate["path"]).read_bytes()
assert hashlib.sha256(candidate_raw).hexdigest() == candidate["sha256"]
assert json.loads(candidate_raw) == packet["candidate_template"]["complete_proposal"]
proposal = packet["reviewed_proposal"]
assert hashlib.sha256((ROOT / proposal["path"]).read_bytes()).hexdigest() == proposal["sha256"]
assert packet["original_case"]["remaining_attempts"] == 0

recorded = datetime.now(UTC).isoformat()
adopted = {
    "cho_scope_and_candidates", "primary_analysis", "secondary_superiority_family",
    "margin_interpretation",
}
responses = copy.deepcopy(packet["owner_responses"])
for name in adopted:
    responses[name] = {
        "approved": True,
        "decision": "adopt_exact_pinned_proposed_design",
        "status": "adopted_under_explicit_user_delegation",
        "decision_maker": "pro3_root_exercising_user_delegation",
        "recorded_utc": recorded,
        "direct_human_scientific_signature": None,
    }
scope = copy.deepcopy(packet["proposed_tranche"])
scope["status"] = "adopted_design_pending_gate_a_provenance_and_freeze"
template = copy.deepcopy(packet["candidate_template"]["complete_proposal"])
template["status"] = "adopted_design_not_executable_or_frozen"
primary = copy.deepcopy(packet["proposed_primary_analysis"])
secondary = copy.deepcopy(packet["proposed_secondary_analysis"])
margin = copy.deepcopy(packet["proposed_margin_display"])
for section in (primary, secondary, margin):
    section["ratified"] = True
question = (
    "Do you ratify the four proposed Cho study-design decisions in the "
    "[pinned owner packet](https://github.com/RAMZI0TO99/thinking-interfaces/blob/"
    "2aeee666f58b74be35099b103bf5db2c1d07edc8/docs/phase2/cho_owner_decision_packet_20261010.md): "
    "the 52-subject/four-method/five-seed scope and candidate settings, primary analysis, "
    "empty secondary superiority family, and exploratory margin rule? The packet requires "
    "an explicit owner decision; engineering work cannot supply it. Gate A, checkpoint "
    "provenance and the experiment freeze would stay pending, with no training authorized."
)
result = {
    "schema": "pro3_four_design_choices_adopted_under_explicit_delegation_v1",
    "recorded_utc": recorded,
    "authorization": {
        "source": "user response in this project conversation",
        "thread_id": "01a115a0-5f96-7472-880f-e1d92e46d853",
        "question_call_id": "call_93681765521d462c8b31d50d90d5364c",
        "question": question,
        "verbatim_user_response": "do what you see fit!",
        "interpretation": "Explicit delegation to choose among the four named design decisions; root adopts their exact pinned proposed versions",
        "direct_human_review_of_full_proposal_established": False,
        "human_signature_inferred": False,
    },
    "baseline_owner_packet": {"path": OWNER_PATH.relative_to(ROOT).as_posix(), "sha256": OWNER_SHA},
    "baseline_proposal": proposal,
    "baseline_candidate_template": candidate,
    "canonical_source_sha256": source,
    "current_configuration_pins": packet["current_configuration_pins"],
    "owner_responses": responses,
    "adopted_decisions": sorted(adopted),
    "remaining_decisions": ["gate_a", "checkpoint_cohort_and_overlap", "experiment_freeze"],
    "adopted_design": {
        "scope": scope,
        "candidate_template": template,
        "primary_analysis": primary,
        "secondary_analysis": secondary,
        "margin_display": margin,
    },
    "selection_rationale": "Retain the already reviewed exact scope and paired subject analysis, descriptive secondary comparisons and exploratory margin; introduce no retrospective tolerance or new claim family",
    "historical_pilot_outcomes_known_before_adoption": True,
    "no_retroactive_prespecification_of_historical_cases_claimed": True,
    "known_runtime_limitations": [
        "Optimizer/search implementation and runtime pilot still require qualification",
        "A feasible complete roster must preserve the exhausted original case without reset, renamed equivalent or score substitution",
        "Real-worker environment, resources, storage, runtime pins and fresh coordination/admission remain separate",
    ],
    "actual_checkpoint_recording_coverage": "unknown",
    "evaluation_overlap": "unknown",
    "original_case": packet["original_case"],
    "original_case_attempts_remaining": 0,
    "scientific_gate_a_signed": False,
    "experiment_freeze_signed": False,
    "scientific_execution_budget_admitted": False,
    "model_training_or_case_authorized": False,
    "active_protocol_configurations_modified": False,
    "executable": False,
}
assert {name for name, row in responses.items() if row["approved"]} == adopted
for name in result["remaining_decisions"]:
    assert responses[name]["approved"] is False and responses[name]["decision"] is None
assert source_check(ROOT) == source
assert hashlib.sha256(OWNER_PATH.read_bytes()).hexdigest() == OWNER_SHA
write_json(ROOT / "docs/phase2/cho_design_decisions_20261012.json", result)
print(json.dumps({"adopted_decisions": sorted(adopted), "remaining_decisions": result["remaining_decisions"], "config_pins_verified": len(packet["current_configuration_pins"]), "scientific_gate_a_signed": False, "experiment_freeze_signed": False, "scientific_execution_budget_admitted": False}, indent=2))
