"""Prepare metadata/stat pins; large real data are hashed only inside the guard."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path

root=Path.cwd()
run=Path(__file__).resolve().parent
cohort_rel='runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json'
cohort_raw=(root/cohort_rel).read_bytes()
assert hashlib.sha256(cohort_raw).hexdigest()=='4c6bc85467c94908385f47762a67c0f2703eb87332573d4df1139b441b30b57d'
cohort=json.loads(cohort_raw)
data={}
for row in cohort['rows']:
    subject=row['subject']
    data[f'data/processed/cho2017/profile_a/{subject}.npz']=row['profile_a_sha256']
    data[f'data/processed/cho2017/profile_b_60hz_v1/{subject}.npz']=row['variant_artifact_sha256']
    data[f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json']=row['variant_manifest_sha256']
raw_sources={}
for row in cohort['rows']:
    subject=row['subject']
    rel=f'data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json'
    raw=(root/rel).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==data[rel]
    manifest=json.loads(raw)
    raw_rel=manifest['source_file'];raw_path=(root/raw_rel).resolve()
    assert raw_path.is_relative_to((root/'data/raw/moabb/cho2017').resolve()) and raw_path==root/raw_rel
    assert manifest['source_sha256']==row['raw_source_sha256']
    assert raw_rel not in data
    data[raw_rel]=manifest['source_sha256'];raw_sources[subject]=raw_rel
sample=json.loads((root/'data/processed/cho2017/profile_b_60hz_v1/subject_02.manifest.json').read_bytes())
raw_rel=raw_sources['subject_02']
assert len(data)==208 and len(raw_sources)==52
stats={}
for rel in data:
    path=root/rel
    assert path.is_file() and path.resolve()==path
    stat=path.stat();stats[rel]={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
paths=[cohort_rel,'configs/benchmark.toml','configs/base.toml','docs/phase2/cho_design_decisions_20261012.json','docs/phase2/cho51_route_candidate_v1/route_contract.py','evidence/cho51-adoption-route-20261013/owner/adoption.json','evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json','evidence/phase2-readiness-20261012/worker/roster.json','.venv/Lib/site-packages/urllib3/util/connection.py']
paths += ['docs/phase2/cho51_worker_bridge_v1/worker_bridge.py','docs/phase2/cho51_episode_bindings_v1/validate_bindings.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_candidate_001.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_pins_001.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_candidate_002.py','evidence/cho51-worker-bridge-20261013/index.json']
files={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}
source=json.loads((root/'tools/migration/source-files.json').read_bytes())
for row in source['files']:files[row['path']]=row['sha256']
value={'schema':'cho51_all52_episode_fresh_pins_v1','prepared_utc':datetime.now(timezone.utc).isoformat(),'execution_git':'706a449b469b9e84235869e875bb8b0bf5907727','canonical_source_sha256':source['source_sha256'],'files':files,'data_files':data,'prepared_data_stats':stats,'data_hash_basis':'historical committed cohort declarations; fresh actual hashes must be checked during guarded validation','raw_sources':raw_sources,'sample_raw_source':raw_rel,'sample_raw_source_sha256':sample['source_sha256'],'input_route_pins':{'protocol_config_sha256':files['configs/phase2/protocol.toml'],'threshold_config_sha256':files['configs/benchmark.toml'],'cohort_audit_sha256':files[cohort_rel],'variant_config_sha256':files['configs/phase2/cho_profile_b_60hz.toml']},'seconds':600,'process_mib':2048,'job_mib':3072,'startup_ram_gib':10,'active_ram_gib':4,'disk_gib':20,'native_threads':1,'pro3_roots':1,'pro3_children':0,'scientific_execution_budget_admitted':False,'original_case_attempts_remaining':0}
with (run/'pins_001.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2)
for path in (root/'docs/phase2/cho51_episode_bindings_v1').glob('*.py'):compile(path.read_bytes(),str(path),'exec')
print(json.dumps({'syntax':'pass','file_pins':len(files),'data_paths':len(data),'declared_data_bytes':sum(s['bytes'] for s in stats.values()),'sample_raw_source':raw_rel,'large_data_hashed_during_preparation':False}))
