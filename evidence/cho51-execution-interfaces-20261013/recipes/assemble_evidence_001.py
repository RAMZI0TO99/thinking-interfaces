"""Retain real-route and fabricated-record interface qualification evidence."""
import hashlib,json
from pathlib import Path
root=Path.cwd();run=Path(__file__).resolve().parent
packet=root/'evidence/cho51-execution-interfaces-20261013';packet.mkdir(exist_ok=False)
guard=root/'runs/migration/20261013T090634Z_01e9cd03ac'
receipt=json.loads((guard/'receipt.json').read_bytes())
assert receipt['accepted'] and receipt['job_absent'] and receipt['native_state']['job_closed'] and receipt['native_state']['job_empty_before_close']
items=[]
for name in ('prepare_candidate_001.py','prepare_pins_001.py','prepare_pins_002.py','pins_001.json','pins_002.json','interfaces_draft_001.py','assemble_evidence_001.py'):items.append((run/name,'recipes/'+name))
for name in ('interfaces.py','validate_interfaces.py'):items.append((root/'docs/phase2/cho51_execution_interfaces_v1'/name,'candidate/'+name))
for name in ('admission.json','deadline.json','command-result.json','command.log','receipt.json'):items.append((guard/name,'guard/'+name))
for name in ('route.json','qualification.json','sample_binding.json','sweep_schedule.json','fabricated_pairs.json'):items.append((run/'validation_001'/name,'results/'+name))
items.append((root/'runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json','inputs/retained_cohort_audit.json'))
items.append((root/'evidence/cho51-adoption-route-20261013/owner/adoption.json','inputs/direct_owner_adoption.json'))
files=[]
for source,relative in items:
    raw=source.read_bytes();path=packet/relative;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    assert path.read_bytes()==raw
    files.append({'path':relative,'original_path':source.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
index={'schema':'cho51_read_only_execution_interfaces_packet_v1','files':files,'tests_passed':36,'actual_case_plans':1020,'real_available_subject_catalogs':52,'fabricated_pin_and_score_fixture_cells':1020,'exact_fixture_five_seed_means':204,'fixture_subject_pairs':51,'bounded_case_selection_qualified':True,'sweep_planning_only':True,'verified_resume_or_recorder_publication_or_tensor_restore':False,'data_file_hashes_verified':157,'fresh_source_context_pins':446,'model_or_recorder_or_prediction_or_fitted_selector_or_sweep_executed':False,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,'canonical_source_sha256':'3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'}
with (packet/'index.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(index,stream,sort_keys=True,indent=2)
with (packet/'.gitattributes').open('xb') as stream:stream.write(b'* -text\n')
print(json.dumps({'packet':packet.relative_to(root).as_posix(),'artifacts':len(files),'bytes':sum(v['bytes'] for v in files),'raw_arrays_or_weights_uploaded':False}))
