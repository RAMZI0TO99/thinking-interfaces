import hashlib
import json
from pathlib import Path

root=Path.cwd()
run=root/'runs/coordination/cho51_adoption_route_20261013_v1'
packet=root/'evidence/cho51-adoption-route-20261013'
guard=root/'runs/migration/20261013T074128Z_49acddee69'
receipt=json.loads((guard/'receipt.json').read_bytes())
assert receipt['accepted'] and receipt['job_absent'] and receipt['native_state']['job_closed'] and receipt['native_state']['job_empty_before_close']
items=[]
for name in ('record_adoption_001.py','prepare_route_inputs_001.py','validation_pins_001.json','assemble_evidence_001.py'):
    items.append((run/name,'recipes/'+name))
for name in ('route_contract.py','validate_route.py'):
    items.append((root/'docs/phase2/cho51_route_candidate_v1'/name,'candidate/'+name))
for name in ('route-contract.json','qualification.json'):
    items.append((run/'validation_001'/name,'results/'+name))
for name in ('admission.json','deadline.json','command-result.json','command.log','receipt.json'):
    items.append((guard/name,'guard/'+name))
for source,relative in items:
    destination=packet/relative;destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as stream:stream.write(source.read_bytes())
files=[]
for path in sorted(packet.rglob('*')):
    if path.is_file() and path.name!='.gitattributes':
        raw=path.read_bytes()
        files.append({'path':path.relative_to(packet).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert len(files)==18
index={'schema':'cho51_direct_adoption_route_packet_v1','files':files,'direct_owner_design_adopted':True,'tests_passed':27,'available_subjects':52,'evaluation_targets':51,'retained_cases':1020,'inner_folds_verified':2601,'scientific_execution_budget_admitted':False,'real_assets_or_episodes_verified':False,'worker_class_interoperability_qualified':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,'canonical_source_sha256':'3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529'}
with (packet/'index.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(index,stream,sort_keys=True,indent=2)
print(json.dumps({'artifacts':len(files),'bytes':sum(f['bytes'] for f in files),'owner_design_adopted':True,'scientific_admission':False}))
