"""Retain exact all52 binder code, pins, results and closed native Job evidence."""
import hashlib,json
from pathlib import Path
root=Path.cwd();run=Path(__file__).resolve().parent
packet=root/'evidence/cho51-episode-bindings-20261013';packet.mkdir(exist_ok=False)
guard=root/'runs/migration/20261013T085955Z_a1d41f3724'
receipt=json.loads((guard/'receipt.json').read_bytes())
assert receipt['accepted'] and receipt['job_absent'] and receipt['native_state']['job_closed'] and receipt['native_state']['job_empty_before_close']
items=[]
for name in ('prepare_candidate_001.py','prepare_candidate_002.py','prepare_pins_001.py','pins_001.json','assemble_evidence_001.py'):items.append((run/name,'recipes/'+name))
items.append((root/'docs/phase2/cho51_episode_bindings_v1/validate_bindings.py','candidate/validate_bindings.py'))
for name in ('admission.json','deadline.json','command-result.json','command.log','receipt.json'):items.append((guard/name,'guard/'+name))
for name in ('route.json','qualification.json','sample_binding.json','all_bindings.json'):items.append((run/'validation_001'/name,'results/'+name))
items.append((root/'runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json','inputs/retained_cohort_audit.json'))
items.append((root/'evidence/cho51-adoption-route-20261013/owner/adoption.json','inputs/direct_owner_adoption.json'))
files=[]
for source,relative in items:
    raw=source.read_bytes();path=packet/relative;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    assert path.read_bytes()==raw
    files.append({'path':relative,'original_path':source.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
index={'schema':'cho51_all52_real_episode_binding_packet_v1','files':files,'tests_passed':18,'real_available_subject_bindings':52,'real_evaluation_target_bindings':51,'subject01_binding_role':'source_only','data_files_hashed':208,'data_bytes_hashed':13970094982,'fresh_source_context_pins':445,'raw_recordings_decoded':False,'model_or_recorder_or_prediction_or_fitted_selector_executed':False,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,'canonical_source_sha256':'3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'}
with (packet/'index.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(index,stream,sort_keys=True,indent=2)
with (packet/'.gitattributes').open('xb') as stream:stream.write(b'* -text\n')
print(json.dumps({'packet':packet.relative_to(root).as_posix(),'artifacts':len(files),'bytes':sum(v['bytes'] for v in files),'raw_arrays_or_weights_uploaded':False}))
