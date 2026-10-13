"""Guarded read-only real input/type checks; no prediction, fitting or recorder."""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins',required=True,type=Path)
parser.add_argument('--output-directory',required=True,type=Path)
args=parser.parse_args()
OUT=args.output_directory.resolve()
assert OUT.is_relative_to(ROOT/'runs/coordination/cho51_worker_bridge_20261013_v1')
OUT.mkdir(exist_ok=False)
sys.path[:0]=[str(ROOT),str(ROOT/'.venv/Lib/site-packages'),str(ROOT/'tools/migration')]
from common import digest,source_check
pins=json.loads(args.pins.read_bytes())
for rel,sha in pins['files'].items():assert digest(ROOT/rel)==sha,rel
source_before=source_check(ROOT)
for key,folder in {'MPLCONFIGDIR':'matplotlib','_MNE_FAKE_HOME_DIR':'mne-home','HF_HOME':'huggingface','TMP':'temp','TEMP':'temp','TMPDIR':'temp'}.items():
    path=OUT/folder;path.mkdir(exist_ok=True);os.environ[key]=str(path)
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
allowed_data={ROOT/rel for rel in pins['data_files']}
data_stats={str(path):(path.stat().st_size,path.stat().st_mtime_ns) for path in allowed_data}
denied=[];hostname_queries=0;explicit_forbidden_calls=[]
pause_paths=[Path(r'D:\Aenv\pro2\WORK')/folder/'coordination/PRO2_REQUEST_PRO3_PAUSE.json' for folder in ('resume-20261007-001','resume-20261012-001','resume-20261013-001')]

def deny(event,detail):
    frames=[];frame=sys._getframe(1)
    for _ in range(10):
        if frame is None:break
        frames.append({'file':frame.f_code.co_filename,'function':frame.f_code.co_name,'line':frame.f_lineno});frame=frame.f_back
    denied.append({'event':event,'detail':str(detail)[:200],'bind_address':list(detail) if event=='socket.bind' and isinstance(detail,tuple) else None,'call_stack':frames})
    raise PermissionError('worker bridge excludes '+event)

def normalize_path(value):
    text=os.fsdecode(value)
    if text.startswith('\\\\?\\') and len(text)>6 and text[4].isalpha() and text[5]==':' and text[6]=='\\':
        text=text[4:]
    return Path(text).resolve()

def audit(event,values):
    global hostname_queries
    if event=='socket.gethostname':hostname_queries+=1
    elif event=='socket.bind':deny(event,values[1])
    elif event in {'socket.connect','socket.getaddrinfo','socket.gethostbyname','socket.gethostbyaddr','socket.sendto','subprocess.Popen','os.system','os.startfile','os.startfile/2'} or event.startswith(('os.exec','os.spawn')):deny(event,'network/DNS/subprocess')
    elif event=='open' and values and isinstance(values[0],(str,bytes,os.PathLike)):
        path=normalize_path(values[0]);mode,flags=values[1],values[2]
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and not path.is_relative_to(OUT):deny(event,path)
        if not writing:
            if path.suffix.lower() in {'.pth','.pt','.ckpt','.safetensors'} or path.is_relative_to(ROOT/'weights'):deny(event,path)
            if (path.is_relative_to(ROOT/'data/raw') or path.is_relative_to(ROOT/'data/processed') or path.suffix.lower() in {'.npz','.npy','.mat','.edf','.gdf'}) and path not in allowed_data:deny(event,path)
    elif event in {'os.mkdir','os.remove','os.rmdir','os.rename','os.replace','os.link','os.symlink','os.chmod','os.utime','os.truncate'}:
        count=2 if event in {'os.rename','os.replace','os.link','os.symlink'} else 1
        for value in values[:count]:
            if isinstance(value,(str,bytes,os.PathLike)):
                path=normalize_path(value)
                if not path.is_relative_to(OUT) and not(event=='os.mkdir' and path.is_dir()):deny(event,path)

assert normalize_path('\\\\?\\'+str(ROOT))==ROOT.resolve()
sys.addaudithook(audit)
started=time.monotonic()
import torch
torch.set_num_threads(1);torch.set_num_interop_threads(1)
from evaluation.phase2_cho_case_inputs import ChoCaseInputPins,ChoCaseInputs
from evaluation.phase2_runner import CasePlan,CaseRecorder,method_configuration,environment_digest
from evaluation.phase2_protocol import TrialCatalog,nested_episode,source_selection,selection_gradient_ceiling
from evaluation.phase2_records import verify_envelope
from evaluation.phase2_profile_binding import load_cho_profile_b_episode,ChoProfileBinding60Hz
from core.config import config_digest

def forbidden(*values,**keywords):
    explicit_forbidden_calls.append('model_or_recorder_constructor_or_checkpoint_loader')
    raise PermissionError('no model, recorder or checkpoint operation admitted')
CaseRecorder.__init__=forbidden
torch.nn.Module.__init__=forbidden
torch.load=forbidden
path=Path(__file__).parent/'worker_bridge.py'
spec=importlib.util.spec_from_file_location('_actual_cho51_bridge',path)
B=importlib.util.module_from_spec(spec);sys.modules[spec.name]=B
exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),B.__dict__)
input_pins=ChoCaseInputPins(**pins['input_route_pins'])
print('Imports complete; verifying all52 real catalogs/assets.',flush=True)
route=B.prepare_cho51_worker_route(ROOT,input_pins=input_pins)
print('Complete52-subject inventory verified; checking adopted1020 worker inputs.',flush=True)
adoption=json.loads((ROOT/'evidence/cho51-adoption-route-20261013/owner/adoption.json').read_bytes())
proposal=json.loads((ROOT/'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json').read_bytes())
catalogs={c.subject:c for c in route.catalogs}
cohort=json.loads((ROOT/'runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json').read_bytes())
cohort_rows={r['subject']:r for r in cohort['rows']}
sample_plan=next(p for p in route.plans if p.target_subject=='subject_02' and p.method=='labram_linear' and p.model_seed==11)
sample_inputs=route.inputs_for(sample_plan)
sample_assets=route.labram_assets['subject_02']
sample=load_cho_profile_b_episode(ROOT,sample_inputs.protocol_config,catalogs['subject_02'],sample_inputs.episode_record,shots_per_class=5,profile_b_artifact_sha256=sample_assets.profile_b_artifact_sha256,profile_b_manifest_sha256=sample_assets.profile_b_manifest_sha256,variant_config_sha256=sample_assets.variant_config_sha256)
print('Subject02 real60Hz episode binding complete.',flush=True)
previous=json.loads((ROOT/'docs/phase2/cho_design_decisions_20261012.json').read_bytes())
template_digests={m['method']:method_configuration(m) for m in previous['adopted_design']['candidate_template']['methods']}

class BridgeChecks(unittest.TestCase):
    def setUp(self):self.assertFalse(any(p.exists() for p in pause_paths),'genuine peer pause requested')

    def test_actual_worker_types(self):
        self.assertTrue(all(type(p) is CasePlan for p in route.plans))
        self.assertTrue(all(type(c) is TrialCatalog for c in route.catalogs))
        self.assertEqual(CasePlan.__module__,'evaluation.phase2_runner')
        self.assertEqual(TrialCatalog.__module__,'evaluation.phase2_protocol')

    def test_exact_retained_ids(self):
        self.assertEqual([p.case_id for p in route.plans],[r['case_id'] for r in proposal['proposed_case_rows']])
        self.assertEqual(len(route.plans),1020)
        self.assertEqual(len({p.case_id for p in route.plans}),1020)

    def test_full_source_inventory_preserved(self):
        expected={f'subject_{i:02d}' for i in range(1,53)}
        self.assertEqual(set(catalogs),expected)
        self.assertEqual(set(route.labram_assets),expected)
        self.assertEqual(len(route._full_route.plans),1040)
        self.assertEqual({p.target_subject for p in route.plans},expected-{'subject_01'})

    def test_original_case_input_refused(self):
        original=next(p for p in route._full_route.plans if p.case_id==adoption['original_case']['id'])
        with self.assertRaisesRegex(ValueError,'outside the adopted51'):route.inputs_for(original)
        self.assertEqual(adoption['original_case_attempts_remaining'],0)

    def test_untyped_plan_refused(self):
        with self.assertRaisesRegex(ValueError,'outside the adopted51'):route.inputs_for(object())

    def test_wrong_seed_shot_or_repetition_refused(self):
        for changed in (replace(sample_plan,model_seed=99),replace(sample_plan,shots_per_class=10),replace(sample_plan,repetition=2)):
            with self.assertRaisesRegex(ValueError,'outside the adopted51'):route.inputs_for(changed)

    def test_all1020_inputs_have_correct_types_profiles_and_source_pools(self):
        counts={'cho_profile_a':0,'cho_profile_b_60hz_v1':0}
        for plan in route.plans:
            value=route.inputs_for(plan)
            self.assertIs(type(value),ChoCaseInputs)
            self.assertEqual(value.plan,plan)
            self.assertEqual(len(value.catalogs),52)
            expected='cho_profile_a' if plan.method=='eegnet' else 'cho_profile_b_60hz_v1'
            self.assertEqual(value.profile,expected);counts[value.profile]+=1
            self.assertEqual(len(value.assets),0 if plan.method=='eegnet' else 52)
        self.assertEqual(counts,{'cho_profile_a':255,'cho_profile_b_60hz_v1':765})

    def test_target_records_rederived_from_real_catalogs(self):
        for subject in adoption['current_evaluation_target_ids']:
            plan=next(p for p in route.plans if p.target_subject==subject)
            value=route.inputs_for(plan)
            expected_selection=asdict(source_selection(route.catalogs,target=subject))
            expected_episode=nested_episode(catalogs[subject],shots=(1,5,10,20),protocol_sha256=config_digest(value.protocol_config))
            self.assertTrue(verify_envelope(record=value.selection_record,kind='source_selection',expected_payload=expected_selection))
            self.assertTrue(verify_envelope(record=value.episode_record,kind='episode_manifest',expected_payload=expected_episode.payload()))
            self.assertEqual(len(expected_episode.partition(5).support_indices),10)

    def test_real_source_folds_keep_subject01(self):
        total=0
        for target,selection in route.contract.selections.items():
            self.assertEqual(len(selection.source_subjects),51);self.assertIn('subject_01',selection.source_subjects)
            for fold in selection.inner_folds:
                total+=1;self.assertEqual(len(fold.training_subjects),50)
                self.assertNotIn(target,fold.training_subjects);self.assertNotIn(fold.validation_subject,fold.training_subjects)
        self.assertEqual(total,2601)

    def test_method_templates_unchanged(self):self.assertEqual(dict(route.contract.method_config_sha256),template_digests)

    def test_returned_records_are_independent_copies(self):
        first=route.inputs_for(sample_plan);first.protocol_config['protocol']['model_seeds'].append(99);first.episode_record.clear()
        second=route.inputs_for(sample_plan)
        self.assertEqual(second.protocol_config['protocol']['model_seeds'],[11,23,37,53,71]);self.assertTrue(second.episode_record)

    def test_real_binding_type_hash_and_trial_counts(self):
        self.assertIs(type(sample.binding),ChoProfileBinding60Hz)
        self.assertEqual(sample.binding.sha256,cohort_rows['subject_02']['binding_sha256'])
        self.assertEqual(sample.support_signals.shape,(10,64,800))
        self.assertEqual(sample.query_signals.shape[1:],(64,800))
        self.assertEqual(len(sample.query_labels),cohort_rows['subject_02']['query_trials'])
        self.assertEqual(sample.binding.source_sha256,pins['sample_raw_source_sha256'])

    def test_no_support_query_overlap_or_label_change(self):
        self.assertFalse(set(sample.binding.support_trial_ids)&set(sample.binding.query_trial_ids))
        self.assertEqual(sorted(sample.support_labels.tolist()),[0]*5+[1]*5)
        self.assertEqual(len(sample.binding.support_trial_ids),10)

    def test_bad_full_route_refused(self):
        with self.assertRaisesRegex(ValueError,'complete unchanged'):B.from_verified_full_route(ROOT,replace(route._full_route,plans=route._full_route.plans[:-1]))

    def test_config_ceiling_and_adoption_freeze_boundaries(self):
        self.assertEqual(selection_gradient_ceiling(ROOT),5253)
        self.assertTrue(adoption['design_amendment_adopted'])
        self.assertFalse(adoption['experiment_freeze_signed']);self.assertFalse(adoption['scientific_execution_budget_admitted'])
        self.assertEqual(torch.get_num_threads(),1);self.assertEqual(torch.get_num_interop_threads(),1)
        self.assertEqual(explicit_forbidden_calls,[])

suite=unittest.defaultTestLoader.loadTestsFromTestCase(BridgeChecks)
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():raise SystemExit(1)
connection=ROOT/'.venv/Lib/site-packages/urllib3/util/connection.py'
expected=[d for d in denied if d['event']=='socket.bind' and d['bind_address']==['::1',0] and any(f['function']=='_has_ipv6' and Path(f['file']).resolve()==connection.resolve() for f in d['call_stack'])]
assert len(expected)<=1 and not [d for d in denied if d not in expected]
assert digest(connection)==pins['files']['.venv/Lib/site-packages/urllib3/util/connection.py']
verified_data={}
for rel,sha in pins['data_files'].items():
    path=ROOT/rel
    assert (path.stat().st_size,path.stat().st_mtime_ns)==data_stats[str(path)],rel
    assert digest(path)==sha,rel
    verified_data[rel]={'sha256':sha,'bytes':path.stat().st_size}
for rel,sha in pins['files'].items():assert digest(ROOT/rel)==sha,rel
assert source_check(ROOT)==source_before and not explicit_forbidden_calls and not any(p.exists() for p in pause_paths)
loaded={}
for module in tuple(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if name and Path(name).is_file():loaded[str(Path(name).resolve())]=digest(Path(name))
summary=B.route_summary(route)
summary.update(actual_worker_type_interoperability_qualified=True,real52_profile_a_catalogs_verified=True,real52_profile_b_inventory_hashes_verified=True,real51_target_episode_records_verified=True,full51_profile_b_episode_arrays_verified=False,sample_profile_b_episode_subject='subject_02',sample_binding_sha256=sample.binding.sha256,sample_support_shape=list(sample.support_signals.shape),sample_query_shape=list(sample.query_signals.shape),source_folds_verified=2601)
qualification={'schema':'cho51_actual_worker_real_input_bridge_qualification_v1','passed':True,'observed_utc':datetime.now(timezone.utc).isoformat(),'tests_run':result.testsRun,'duration_seconds':time.monotonic()-started,'selected_execution_git':pins['execution_git'],'canonical_source_sha256':source_before,'candidate_input_pins':pins['files'],'data_file_hashes_verified':verified_data,'loaded_module_file_count':len(loaded),'observed_loaded_module_file_hashes':loaded,'loaded_file_hash_note':'File bytes observed after imports and rechecked; historical loaded binaries are not reconstructed','torch_version':str(torch.__version__),'torch_threads':torch.get_num_threads(),'torch_interop_threads':torch.get_num_interop_threads(),'deterministic_algorithms_enabled':torch.are_deterministic_algorithms_enabled(),'phase2_environment_digest':environment_digest(),'hostname_metadata_queries':hostname_queries,'denied_operations':denied,'expected_blocked_ipv6_probes':len(expected),'unexpected_denials':0,'checkpoint_or_model_or_recorder_operation':False,'raw_recordings_decoded':False,'only_raw_recording_rehashed':pins['sample_raw_source'],'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0,'full_selector_sweep_collector_or_numerical_worker_qualified':False}
for name,value in (('route.json',summary),('qualification.json',qualification),('sample_binding.json',asdict(sample.binding))):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
for name,sha in loaded.items():assert digest(Path(name))==sha,name
print(json.dumps({'passed':True,'tests_run':result.testsRun,'cases':1020,'real_catalogs':52,'data_files_verified':len(verified_data),'sample_binding':'subject_02','scientific_admission':False}))
