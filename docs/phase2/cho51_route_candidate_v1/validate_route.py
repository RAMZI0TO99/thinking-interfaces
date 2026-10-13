"""Fresh finite fixture qualification of owner-bound metadata route planning."""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import MappingProxyType
import unittest

ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pins',required=True,type=Path)
parser.add_argument('--output-directory',required=True,type=Path)
args=parser.parse_args()
OUT=args.output_directory.resolve()
assert OUT.is_relative_to(ROOT/'runs/coordination/cho51_adoption_route_20261013_v1')
OUT.mkdir(exist_ok=False)
pins=json.loads(args.pins.read_bytes())
for relative,digest in pins['files'].items():assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
pause_paths=[Path(r'D:\Aenv\pro2\WORK')/folder/'coordination/PRO2_REQUEST_PRO3_PAUSE.json' for folder in ('resume-20261007-001','resume-20261012-001','resume-20261013-001')]
denied=[]

def audit(event,values):
    refused=event.startswith('socket.') or event in {'subprocess.Popen','os.system','os.startfile','os.startfile/2','os.fork','os.posix_spawn'}
    if event=='import' and values[0].split('.')[0] in {'numpy','scipy','torch','mne','moabb','safetensors','data','encoder','adaptation'}:refused=True
    if event=='open' and values and isinstance(values[0],(str,bytes,os.PathLike)):
        path=Path(os.fsdecode(values[0])).resolve()
        mode,flags=values[1],values[2]
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and not path.is_relative_to(OUT):refused=True
        if not writing and path.is_relative_to(ROOT) and not(path.is_relative_to(OUT) or path in {ROOT/p for p in pins['files']}):refused=True
        if path.suffix.lower() in {'.npy','.npz','.edf','.mat','.pt','.pth','.ckpt','.safetensors'}:refused=True
    if event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.utime','os.truncate','os.rename','os.replace','os.link','os.symlink'}:
        count=2 if event in {'os.rename','os.replace','os.link','os.symlink'} else 1
        for item in values[:count]:
            if isinstance(item,(str,bytes,os.PathLike)) and not Path(os.fsdecode(item)).resolve().is_relative_to(OUT):refused=True
    if refused:
        denied.append({'event':event})
        raise PermissionError('metadata route scope refused '+event)

sys.addaudithook(audit)
path=Path(__file__).parent/'route_contract.py'
spec=importlib.util.spec_from_file_location('_route51',path)
M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M
exec(compile(path.read_bytes(),str(path),'exec',dont_inherit=True),M.__dict__)
started=time.monotonic()
D=M.load_dependencies(ROOT)
AD,P,R,PROTOCOL,CasePlan=D
CATALOGS=M.fixture_catalogs(PROTOCOL)
ROUTE=M.prepare_route_contract(D,CATALOGS)

class RouteChecks(unittest.TestCase):
    def setUp(self):self.assertFalse(any(p.exists() for p in pause_paths),'genuine peer pause requested')

    def test_direct_owner_answer_and_remaining_decisions(self):
        self.assertTrue(AD['design_amendment_adopted'])
        self.assertEqual(AD['authorization']['verbatim_user_response'],'Adopt 51 targets (Recommended)')
        self.assertEqual(len(AD['adopted_decisions']),5)
        self.assertEqual(AD['remaining_decisions'],['checkpoint_cohort_and_overlap','experiment_freeze'])

    def test_historical_proposal_stays_false(self):self.assertFalse(P['adopted'])

    def test_complete_case_matrix(self):
        self.assertEqual(len(ROUTE.plans),1020)
        self.assertEqual(len({p.case_id for p in ROUTE.plans}),1020)
        self.assertEqual({p.target_subject for p in ROUTE.plans},set(M.TARGETS))
        self.assertEqual({p.method for p in ROUTE.plans},set(M.METHODS))
        self.assertEqual({p.model_seed for p in ROUTE.plans},set(M.SEEDS))
        self.assertTrue(all(p.shots_per_class==5 and p.repetition==1 for p in ROUTE.plans))

    def test_rederived_case_ids_byte_identical(self):
        self.assertEqual([p.case_id for p in ROUTE.plans],[r['case_id'] for r in P['proposed_case_rows']])
        self.assertEqual(len(R['cases']),1040)
        self.assertEqual(len(P['excluded_case_rows']),20)

    def test_original_exhausted_case_refused(self):
        original=AD['original_case']['id']
        with self.assertRaisesRegex(ValueError,'outside the adopted51'):ROUTE.plan_for(original)
        self.assertEqual(AD['original_case_attempts_remaining'],0)
        self.assertEqual(R['original_case_claims'],2)
        self.assertEqual(R['original_case_failures'],2)

    def test_lookup_retained_case(self):
        self.assertEqual(ROUTE.plan_for(ROUTE.plans[0].case_id),ROUTE.plans[0])

    def test_all_sources_keep_subject01(self):
        for target,selection in ROUTE.selections.items():
            self.assertEqual(len(selection.source_subjects),51)
            self.assertNotIn(target,selection.source_subjects)
            self.assertIn('subject_01',selection.source_subjects)

    def test_every_inner_fold_excludes_target_and_validation(self):
        folds=members=0
        for target,selection in ROUTE.selections.items():
            self.assertEqual(len(selection.inner_folds),51)
            self.assertEqual(tuple(f.validation_subject for f in selection.inner_folds),selection.source_subjects)
            for fold in selection.inner_folds:
                folds+=1;members+=len(fold.training_subjects)
                self.assertEqual(len(fold.training_subjects),50)
                self.assertNotIn(target,fold.training_subjects)
                self.assertNotIn(fold.validation_subject,fold.training_subjects)
                self.assertEqual(set(fold.training_subjects)|{fold.validation_subject},set(selection.source_subjects))
        self.assertEqual((folds,members),(2601,130050))

    def test_subject01_as_inner_validation_and_training(self):
        for selection in ROUTE.selections.values():
            self.assertEqual(sum(f.validation_subject=='subject_01' for f in selection.inner_folds),1)
            self.assertEqual(sum('subject_01' in f.training_subjects for f in selection.inner_folds),50)

    def test_method_templates_unchanged(self):
        self.assertEqual(set(ROUTE.method_config_sha256),set(M.METHODS))
        for row in P['proposed_case_rows']:self.assertEqual(ROUTE.method_config_sha256[row['method']],row['method_config_sha256'])

    def test_missing_subject01_catalog_refused(self):
        with self.assertRaisesRegex(ValueError,'ordered52'):M.prepare_route_contract(D,CATALOGS[1:])

    def test_duplicate_or_unordered_catalogs_refused(self):
        for catalogs in ((CATALOGS[0],)+CATALOGS[:-1],CATALOGS[::-1]):
            with self.assertRaisesRegex(ValueError,'ordered52'):M.prepare_route_contract(D,catalogs)

    def test_wrong_dataset_refused(self):
        catalogs=(replace(CATALOGS[0],dataset='other'),)+CATALOGS[1:]
        with self.assertRaisesRegex(ValueError,'left/right'):M.prepare_route_contract(D,catalogs)

    def test_preprocessing_drift_refused(self):
        catalogs=(replace(CATALOGS[0],preprocessing_sha256='1'*64),)+CATALOGS[1:]
        with self.assertRaisesRegex(ValueError,'share dataset'):M.prepare_route_contract(D,catalogs)

    def test_missing_retained_class_refused(self):
        catalogs=(replace(CATALOGS[0],labels=('left_hand',)*4),)+CATALOGS[1:]
        with self.assertRaisesRegex(ValueError,'every declared class'):M.prepare_route_contract(D,catalogs)

    def test_untyped_catalog_refused(self):
        with self.assertRaisesRegex(ValueError,'typed'):M.prepare_route_contract(D,(object(),)+CATALOGS[1:])

    def test_owner_adoption_cannot_be_inferred(self):
        ad=deepcopy(AD);ad['authorization']['direct_owner_choice_received']=False
        with self.assertRaisesRegex(ValueError,'direct exact owner'):M.validate_decision(ad,P,R)

    def test_execution_and_retry_claims_refused(self):
        for key,value in (('experiment_freeze_signed',True),('scientific_execution_budget_admitted',True),('original_case_attempts_remaining',1)):
            ad=deepcopy(AD);ad[key]=value
            with self.assertRaisesRegex(ValueError,'no execution'):M.validate_decision(ad,P,R)

    def test_target_scope_change_refused(self):
        ad=deepcopy(AD);ad['current_evaluation_target_ids'][0]='subject_01'
        with self.assertRaisesRegex(ValueError,'exact52'):M.validate_decision(ad,P,R)

    def test_seed_shot_repetition_change_refused(self):
        for key,value in (('model_seeds',[11,23,37,53,99]),('shots_per_class',10),('repetition',2)):
            ad=deepcopy(AD);ad[key]=value
            with self.assertRaisesRegex(ValueError,'unchanged method'):M.validate_decision(ad,P,R)

    def test_df_and_subject_units_change_refused(self):
        ad=deepcopy(AD);ad['adopted_primary_analysis']['paired_mean_interval']['df']=51
        with self.assertRaisesRegex(ValueError,'51 subject analysis'):M.validate_decision(ad,P,R)

    def test_changed_case_identity_or_template_refused(self):
        for key,value in (('case_id','2'*64),('method_config_sha256','3'*64),('repetition',2)):
            p=deepcopy(P);p['proposed_case_rows'][0][key]=value
            with self.assertRaises(ValueError):M.validate_decision(AD,p,R)

    def test_partial_exclusion_refused(self):
        p=deepcopy(P);p['excluded_case_rows'].pop()
        with self.assertRaisesRegex(ValueError,'exclusion changed'):M.validate_decision(AD,p,R)

    def test_json_duplicate_or_nonfinite_refused(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(ValueError):M._json(raw)

    def test_route_maps_are_immutable(self):
        with self.assertRaises(TypeError):ROUTE.selections['subject_01']=ROUTE.selections['subject_02']
        with self.assertRaises(TypeError):ROUTE.method_config_sha256['eegnet']='4'*64

    def test_self_constructed_tampered_route_refused(self):
        for route in (replace(ROUTE,plans=ROUTE.plans[:-1]),replace(ROUTE,owner_decision_sha256='5'*64),replace(ROUTE,selections=MappingProxyType({}))):
            with self.assertRaisesRegex(ValueError,'fully rederived'):M.summary(D,route)

    def test_summary_scope_counts_and_false_authority(self):
        value=M.summary(D,ROUTE)
        self.assertEqual((value['available_subject_count'],value['target_count'],value['planned_cases']),(52,51,1020))
        self.assertEqual((value['inner_folds_verified'],value['inner_training_memberships_verified']),(2601,130050))
        self.assertTrue(value['study_design_adopted'])
        self.assertEqual(value['planned_selection_steps_total'],5358060)
        for key in ('catalog_artifact_bytes_verified','trial_episodes_or_real_assets_qualified','full_worker_CasePlan_class_interoperability_qualified','production_recorder_or_sweep_qualified','experiment_freeze_signed','scientific_execution_budget_admitted'):self.assertFalse(value[key])

suite=unittest.defaultTestLoader.loadTestsFromTestCase(RouteChecks)
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():raise SystemExit(1)
contract=M.summary(D,ROUTE)
assert not denied and not any(p.exists() for p in pause_paths)
for relative,digest in pins['files'].items():assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
for name,value in (('route-contract.json',contract),('qualification.json',{'schema':'cho51_adopted_route_metadata_qualification_v1','passed':True,'tests_run':result.testsRun,'duration_seconds':time.monotonic()-started,'study_design_adopted':True,'candidate_input_pins':pins['files'],'canonical_source_sha256':pins['canonical_source_sha256'],'selected_execution_git':pins['execution_git'],'source_CasePlan_ast_isolated':True,'actual_runner_module_imported':False,'denied_operations':denied,'arrays_checkpoints_or_recorder_opened':False,'real_assets_or_episodes_verified':False,'full_worker_class_interoperability_qualified':False,'scientific_execution_budget_admitted':False,'experiment_freeze_signed':False,'original_case_attempts_remaining':0})):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
print(json.dumps({'passed':True,'tests_run':result.testsRun,'cases':len(ROUTE.plans),'outer_sources':51,'inner_training_subjects':50,'inner_folds':2601,'scientific_admission':False}))
