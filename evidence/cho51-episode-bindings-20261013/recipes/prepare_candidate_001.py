"""Create a new read-only binder qualification from preserved reviewed recipes."""
import hashlib
import json
from pathlib import Path

root = Path.cwd()
run = Path(__file__).resolve().parent
candidate = root / 'docs/phase2/cho51_episode_bindings_v1'
candidate.mkdir(exist_ok=False)
old = root / 'evidence/cho51-worker-bridge-20261013'
index = json.loads((old / 'index.json').read_bytes())

def retained(relative):
    row = next(r for r in index['files'] if r['path'] == relative)
    raw = (old / relative).read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    return raw.decode('utf-8')

def change(text, before, after):
    assert text.count(before) == 1, before[:100]
    return text.replace(before, after)

code = retained('candidate/validate_bridge_002.py')
code = change(code, '"""Guarded read-only real input/type checks; no prediction, fitting or recorder."""', '"""Guarded all52 real60Hz episode joins; no model, prediction or recorder."""')
code = change(code, "ROOT/'runs/coordination/cho51_worker_bridge_20261013_v1'", "ROOT/'runs/coordination/cho51_episode_bindings_20261013_v1'")
code = change(code, "path=Path(__file__).parent/'worker_bridge.py'", "path=ROOT/'docs/phase2/cho51_worker_bridge_v1/worker_bridge.py'")
code = change(code, "data_stats={str(path):(path.stat().st_size,path.stat().st_mtime_ns) for path in allowed_data}", "data_stats={str(path):(path.stat().st_size,path.stat().st_mtime_ns) for path in allowed_data}\nfor rel,value in pins['prepared_data_stats'].items():\n    assert data_stats[str(ROOT/rel)]==(value['bytes'],value['mtime_ns']),rel")
start = code.index("sample=load_cho_profile_b_episode(")
end = code.index("previous=json.loads(", start)
code = code[:start] + '''bindings=[];sample=None
for subject in sorted(catalogs):
    assert not any(p.exists() for p in pause_paths),'genuine peer pause requested'
    # subject01 is checked solely as available source/inner-validation data.
    # No subject01 CasePlan is passed to any case-input or execution interface.
    protocol_config=json.loads(route.protocol_config_json)
    episode_record=json.loads(route._full_route.episode_records_json[subject])
    asset=route.labram_assets[subject]
    value=load_cho_profile_b_episode(ROOT,protocol_config,catalogs[subject],episode_record,shots_per_class=5,profile_b_artifact_sha256=asset.profile_b_artifact_sha256,profile_b_manifest_sha256=asset.profile_b_manifest_sha256,variant_config_sha256=asset.variant_config_sha256)
    row=cohort_rows[subject]
    assert type(value.binding) is ChoProfileBinding60Hz
    assert value.binding.sha256==row['binding_sha256'],subject
    assert value.binding.source_sha256==row['raw_source_sha256'],subject
    assert value.support_signals.shape==(row['support_trials'],64,800),subject
    assert value.query_signals.shape==(row['query_trials'],64,800),subject
    assert not set(value.binding.support_trial_ids)&set(value.binding.query_trial_ids),subject
    assert sorted(value.support_labels.tolist())==[0]*5+[1]*5,subject
    bindings.append({'subject':subject,'role':'available_source_only' if subject=='subject_01' else 'evaluation_target_and_available_source','binding_sha256':value.binding.sha256,'binding':asdict(value.binding),'support_shape':list(value.support_signals.shape),'query_shape':list(value.query_signals.shape),'raw_source_sha256':value.binding.source_sha256})
    if subject=='subject_02':sample=value
    print('Real60Hz support/query join verified: '+subject,flush=True)
    del value
assert sample is not None
''' + code[end:]
code = change(code, 'suite=unittest.defaultTestLoader.loadTestsFromTestCase(BridgeChecks)', '''    def test_all52_bindings_match_retained_cohort(self):
        self.assertEqual([v['subject'] for v in bindings],sorted(catalogs))
        self.assertEqual(len(bindings),52)
        for value in bindings:
            self.assertEqual(value['binding_sha256'],cohort_rows[value['subject']]['binding_sha256'])
            self.assertEqual(value['support_shape'],[10,64,800])
            self.assertEqual(value['query_shape'],[cohort_rows[value['subject']]['query_trials'],64,800])

    def test_all52_raw_sources_are_pinned_and_hash_only(self):
        self.assertEqual(len(pins['raw_sources']),52)
        self.assertEqual(len(pins['data_files']),208)
        for subject,rel in pins['raw_sources'].items():
            self.assertEqual(pins['data_files'][rel],cohort_rows[subject]['raw_source_sha256'])

    def test_subject01_has_only_available_source_binding(self):
        value=next(v for v in bindings if v['subject']=='subject_01')
        self.assertEqual(value['role'],'available_source_only')
        self.assertNotIn('subject_01',{p.target_subject for p in route.plans})
        self.assertEqual(len([v for v in bindings if v['role']=='evaluation_target_and_available_source']),51)

suite=unittest.defaultTestLoader.loadTestsFromTestCase(BridgeChecks)''')
code = change(code, 'full51_profile_b_episode_arrays_verified=False', 'full51_profile_b_episode_arrays_verified=True,all52_available_profile_b_episode_arrays_verified=True')
code = change(code, "'schema':'cho51_actual_worker_real_input_bridge_qualification_v1'", "'schema':'cho51_all52_real_episode_bindings_qualification_v1'")
code = change(code, "'only_raw_recording_rehashed':pins['sample_raw_source']", "'raw_recordings_rehashed':pins['raw_sources'],'real_profile_b_episode_bindings':52,'evaluation_target_bindings':51,'source_only_subject01_binding':True")
code = change(code, "('sample_binding.json',asdict(sample.binding))", "('sample_binding.json',asdict(sample.binding)),('all_bindings.json',bindings)")
code = change(code, "'sample_binding':'subject_02'", "'real_episode_bindings':52,'target_bindings':51,'source_only_bindings':1")
with (candidate/'validate_bindings.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(code)
compile(code,str(candidate/'validate_bindings.py'),'exec')

prep = retained('recipes/prepare_pins_001.py')
start = prep.index("sample_manifest=root/")
end = prep.index('stats={}\n', start)
prep = prep[:start] + '''raw_sources={}
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
''' + prep[end:]
prep = change(prep, "paths += [p.relative_to(root).as_posix() for p in (root/'docs/phase2/cho51_worker_bridge_v1').glob('*.py')]", "paths += ['docs/phase2/cho51_worker_bridge_v1/worker_bridge.py','docs/phase2/cho51_episode_bindings_v1/validate_bindings.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_candidate_001.py','runs/coordination/cho51_episode_bindings_20261013_v1/prepare_pins_001.py','evidence/cho51-worker-bridge-20261013/index.json']")
prep = change(prep, "'schema':'cho51_worker_real_input_fresh_pins_v1'", "'schema':'cho51_all52_episode_fresh_pins_v1'")
prep = change(prep, "'execution_git':'9238c79ab4cd53ebdf7a613f204e67dd5da29378'", "'execution_git':'706a449b469b9e84235869e875bb8b0bf5907727'")
prep = change(prep, "'sample_raw_source':raw_rel", "'raw_sources':raw_sources,'sample_raw_source':raw_rel")
prep = change(prep, "'seconds':300", "'seconds':600")
prep = change(prep, "root/'docs/phase2/cho51_worker_bridge_v1'", "root/'docs/phase2/cho51_episode_bindings_v1'")
with (run/'prepare_pins_001.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(prep)
compile(prep,str(run/'prepare_pins_001.py'),'exec')
print(json.dumps({'candidate_created':True,'previous_files_preserved':True,'syntax':'pass','guarded_binding_subjects':52,'models_or_recorders_admitted':False}))
