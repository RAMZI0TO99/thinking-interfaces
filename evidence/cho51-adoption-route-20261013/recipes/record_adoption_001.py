"""Record the direct owner answer; preserve every earlier proposal/decision byte."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path.cwd()
COMMIT='c1a989d6ce8f9aa7ef8452c94f623731a7d46830'
MD='docs/phase2/cho_51_target_amendment_proposal_20261012.md'
JSON='docs/phase2/cho_51_target_amendment_proposal_20261012.json'
EXPECTED={MD:'ab1c313956907a13a1039430442ce791db63c44b5c3acbbb2a2702d85bfa0634',JSON:'26edbf77961af89fdc31941cbf0425c97ebd81ed263dff706a21aac933e9b965'}
for relative,digest in EXPECTED.items():
    raw=(ROOT/relative).read_bytes()
    git_raw=subprocess.run(['git','show',COMMIT+':'+relative],check=True,stdout=subprocess.PIPE).stdout
    assert hashlib.sha256(raw).hexdigest()==hashlib.sha256(git_raw).hexdigest()==digest
proposal=json.loads((ROOT/JSON).read_bytes())
previous=json.loads((ROOT/'docs/phase2/gate_a_acceptance_20261012.json').read_bytes())
primary=deepcopy(proposal['proposed_primary_analysis']);primary['ratified']=True
question='Do you adopt the [published 51-target amendment](https://github.com/RAMZI0TO99/thinking-interfaces/blob/c1a989d6ce8f9aa7ef8452c94f623731a7d46830/docs/phase2/cho_51_target_amendment_proposal_20261012.md)? It excludes all 20 subject01 evaluation rows consistently, keeps all 52 subjects available as source data, and changes the analysis to 51 subjects with 50 degrees of freedom. The synthetic candidate now passes 22 checks. I can continue reversible engineering preparation, but adopting this change to your existing study design needs your explicit choice.'
value={
    'schema':'cho51_direct_owner_amendment_adoption_v1',
    'recorded_utc':datetime.now(timezone.utc).isoformat(),
    'authorization':{'source':'direct owner answer in this project conversation','thread_id':'01a115a0-5f96-7472-880f-e1d92e46d853','question_call_id':'call_650aebd78fb8478e896a42934678f8b9','question_item_id':'["request_user_input_async","call_650aebd78fb8478e896a42934678f8b9",0]','verbatim_question':question,'verbatim_user_response':'Adopt 51 targets (Recommended)','direct_owner_choice_received':True,'scientific_signature_inferred_from_engineering_delegation':False,'original_user_message_utc':None,'timestamp_note':'recorded_utc is recording time; original message time is not inferred','owner_read_entire_document_independently_verified':False},
    'accepted_proposal':{'commit':COMMIT,'markdown_path':MD,'json_path':JSON,'markdown_git_and_local_sha256':EXPECTED[MD],'json_git_and_local_sha256':EXPECTED[JSON],'url':'https://github.com/RAMZI0TO99/thinking-interfaces/blob/'+COMMIT+'/'+MD},
    'design_amendment_adopted':True,
    'retrospective_amendment_after_known_engineering_history':True,
    'current_evaluation_target_ids':proposal['evaluation_target_ids'],
    'evaluation_target_count':51,
    'available_cohort_subject_ids':proposal['available_cohort_subject_ids'],
    'available_cohort_subject_count':52,
    'excluded_evaluation_target_ids':['subject_01'],
    'excluded_all_methods_and_seeds_cells':20,
    'expected_cells':1020,
    'methods':proposal['methods'],
    'model_seeds':proposal['model_seeds'],
    'shots_per_class':5,
    'repetition':1,
    'retained_case_ids_and_method_templates_unchanged':True,
    'source_policy':proposal['source_policy'],
    'subject01_available_as_source_or_inner_validation_for_other_targets':True,
    'per_case_source_pool_subjects':51,
    'per_inner_fold_training_subjects':50,
    'adopted_primary_analysis':primary,
    'secondary_superiority_family':[],
    'exploratory_margin':proposal['exploratory_margin'],
    'secondary_and_margin_intervals_subjects':51,
    'secondary_and_margin_intervals_df':50,
    'formal_equivalence_or_interchangeability_claim':False,
    'selection_steps_per_case':5253,
    'planned_selection_steps_total':5358060,
    'planned_target_support_steps_total':1020,
    'original52_target_scope_superseded_for_future_evaluation':True,
    'original52_target_implementation_and_history_preserved':True,
    'original52_target_plan_claimed_completed':False,
    'original_case':proposal['original_case'],
    'original_case_attempts_remaining':0,
    'original_case_recovery_reset_third_attempt_or_rename_authorized':False,
    'canonical_source_sha256':proposal['canonical_source_sha256'],
    'canonical_files':432,
    'active_protocol_configurations_modified':False,
    'executable':False,
    'adopted_decisions':previous['adopted_decisions'],
    'remaining_decisions':previous['remaining_decisions'],
    'scientific_gate_a_accepted_under_exact_retrospective_amendment':True,
    'actual_checkpoint_recording_coverage':'unknown',
    'evaluation_overlap':'unknown',
    'experiment_freeze_signed':False,
    'scientific_execution_budget_admitted':False,
    'model_training_or_case_authorized_by_this_decision':False,
    'production51_route_collector_and_worker_qualified':False,
    'prior_decision_pins':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('docs/phase2/cho_design_decisions_20261012.json','docs/phase2/gate_a_acceptance_20261012.json')},
    'current_configuration_pins':previous['current_configuration_pins'],
}
path=ROOT/'docs/phase2/cho_51_target_amendment_adoption_20261013.json'
raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
with path.open('xb') as stream:stream.write(raw)
print(json.dumps({'decision':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'recorded_utc':value['recorded_utc'],'adopted':True,'remaining_decisions':value['remaining_decisions']}))
