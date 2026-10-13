import hashlib
import json
from pathlib import Path

root=Path.cwd();run=Path(__file__).resolve().parent
packet=root/'evidence/cho51-worker-bridge-20261013'
packet.mkdir(exist_ok=False)
items=[]
for name in ('prepare_pins_001.py','prepare_successor_002.py','pins_001.json','pins_002.json','assemble_evidence_001.py'):
    items.append((run/name,'recipes/'+name))
for name in ('worker_bridge.py','validate_bridge.py','validate_bridge_002.py'):
    items.append((root/'docs/phase2/cho51_worker_bridge_v1'/name,'candidate/'+name))
for folder,label in (('20261013T081749Z_c1c75145d6','failed_guard'),('20261013T082324Z_7502803641','passed_guard')):
    guard=root/'runs/migration'/folder
    receipt=json.loads((guard/'receipt.json').read_bytes())
    assert receipt['job_absent'] and receipt['native_state']['job_closed'] and receipt['native_state']['job_empty_before_close']
    assert receipt['accepted']==(label=='passed_guard')
    for name in ('admission.json','deadline.json','command-result.json','command.log','receipt.json'):items.append((guard/name,label+'/'+name))
for name in ('route.json','qualification.json','sample_binding.json'):items.append((run/'validation_002'/name,'results/'+name))
items.append((root/'runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json','inputs/retained_cohort_audit.json'))
items.append((root/'evidence/cho51-adoption-route-20261013/owner/adoption.json','inputs/direct_owner_adoption.json'))
assert len(items)==23
files=[]
for source,relative in items:
    raw=source.read_bytes();path=packet/relative;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    assert path.read_bytes()==raw
    files.append({'path':relative,'original_path':source.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
index={'schema':'cho51_actual_worker_real_input_bridge_packet_v1','files':files,'tests_passed':15,'actual_worker_types_qualified':True,'real_profile_a_catalogs':52,'real_profile_b_asset_pairs_hashed':52,'real_target_episode_records':51,'retained_cases':1020,'real_profile_b_episode_arrays_verified_subjects':['subject_02'],'data_file_hashes_verified':157,'model_or_recorder_or_prediction_or_selector_executed':False,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,'canonical_source_sha256':'3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'}
with (packet/'index.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(index,stream,sort_keys=True,indent=2)
with (packet/'.gitattributes').open('xb') as stream:stream.write(b'* -text\n')
print(json.dumps({'artifacts':len(files),'bytes':sum(f['bytes'] for f in files),'raw_arrays_and_weights_uploaded':False}))
