"""Prepare fresh read-only real-route / fabricated-pin interface qualification."""
import hashlib
import json
from pathlib import Path

root=Path.cwd();run=Path(__file__).resolve().parent
packet=root/'evidence/cho51-worker-bridge-20261013'
index=json.loads((packet/'index.json').read_bytes())
def retained(relative):
    row=next(v for v in index['files'] if v['path']==relative)
    raw=(packet/relative).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
    return raw.decode('utf-8')
def change(text,before,after):
    assert text.count(before)==1,before[:100]
    return text.replace(before,after)
code=retained('candidate/validate_bridge_002.py')
code=change(code,"ROOT/'runs/coordination/cho51_worker_bridge_20261013_v1'","ROOT/'runs/coordination/cho51_execution_interfaces_20261013_v1'")
start=code.index("path=Path(__file__).parent/'worker_bridge.py'")
end=code.index('input_pins=ChoCaseInputPins',start)
code=code[:start]+'''import docs.phase2.cho51_worker_bridge_v1.worker_bridge as B
import docs.phase2.cho51_execution_interfaces_v1.interfaces as I
from core.provenance import SourceProvenance
from evaluation.phase2_cell_aggregation_bridge import PinnedCaseCell
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_subject_aggregation import ExpectedCell,ScoreRow
from fractions import Fraction
'''+code[end:]
before='suite=unittest.defaultTestLoader.loadTestsFromTestCase(BridgeChecks)'
tests='''# These identity/score fixtures are fabricated, not admitted recorder records.
fixture_source=SourceProvenance('1'*40,'2'*64,False)
fixture_pins=[];fixture_rows=[]
for plan in route.plans:
    value=route.inputs_for(plan);key=ExpectedCell(*plan.identity_key)
    identity=CellIdentity(dataset=plan.dataset,target_subject=plan.target_subject,method=plan.method,shots_per_class=5,model_seed=plan.model_seed,support_draw_seed=None,montage_seed=None,protocol_sha256=config_digest(value.protocol_config),episode_sha256=value.episode_record['sha256'],selection_sha256=value.selection_record['sha256'],method_config_sha256=template_digests[plan.method],preprocessing_sha256=catalogs[plan.target_subject].preprocessing_sha256,checkpoint_sha256='3'*64,source_sha256=fixture_source.source_sha256,environment_sha256='4'*64,git_commit=fixture_source.git_commit,git_dirty=False)
    cell_sha=hashlib.sha256(('FABRICATED cell '+plan.case_id).encode()).hexdigest()
    fixture_pins.append(PinnedCaseCell(plan,key,identity,1,cell_sha,'5'*64,'6'*64))
    score=Fraction(3,5) if plan.method=='labram_lora' else Fraction(1,2)
    fixture_rows.append(ScoreRow(key,score.numerator,score.denominator,cell_sha))

class InterfaceChecks(unittest.TestCase):
    def setUp(self):self.assertFalse(any(p.exists() for p in pause_paths))
    def verify(self,values=fixture_pins,source=fixture_source,methods=template_digests):
        I.verify_case_identity_bindings(ROOT,route,values,method_config_sha256=methods,expected_source=source)
    def test_complete_actual_route_and_single_selection(self):
        selected=I.select_plans(ROOT,route,method='labram_linear',subject='subject_02',seed=11)
        self.assertEqual(selected,(sample_plan,));self.assertIs(type(selected[0]),CasePlan)
    def test_bounded_full1020_order(self):self.assertEqual(I.select_plans(ROOT,route,case_limit=1020),route.plans)
    def test_all_broad_filters_need_bound(self):
        for values in ({},{'method':'eegnet'},{'subject':'subject_02'},{'seed':11}):
            with self.assertRaises(ValueError):I.select_plans(ROOT,route,**values)
    def test_subject01_evaluation_selection_refused(self):
        with self.assertRaises(ValueError):I.select_plans(ROOT,route,method='labram_linear',subject='subject_01',seed=11)
    def test_invalid_limits_and_filters(self):
        for limit in (True,0,-1,1021,1.5):
            with self.assertRaises(ValueError):I.select_plans(ROOT,route,case_limit=limit)
        for values in ({'method':'bad'},{'seed':True},{'seed':99},{'subject':'subject_53'}):
            with self.assertRaises(ValueError):I.select_plans(ROOT,route,case_limit=1,**values)
    def test_bounded_method_filter_preserves_ids(self):
        actual=I.select_plans(ROOT,route,method='eegnet',case_limit=20)
        self.assertEqual(actual,tuple(p for p in route.plans if p.method=='eegnet')[:20])
    def test_sweep_schedule_is_planning_without_resume_claim(self):
        result=I.sweep_schedule(ROOT,route,case_limit=3,skip_case_ids=(route.plans[0].case_id,))
        self.assertEqual(result['planned_case_ids'],[p.case_id for p in route.plans[1:3]])
        self.assertFalse(result['verified_resume_or_record_admission']);self.assertFalse(result['model_or_recorder_executed'])
    def test_sweep_refuses_excluded_duplicate_or_untyped_skip_ids(self):
        original=adoption['original_case']['id'];kept=route.plans[0].case_id
        for values in ((original,),(kept,kept),kept,(object(),)):
            with self.assertRaises(ValueError):I.sweep_schedule(ROOT,route,case_limit=3,skip_case_ids=values)
    def test_1020_fabricated_pin_identities(self):self.verify()
    def test_reversed_pin_order_is_accepted(self):self.verify(tuple(reversed(fixture_pins)))
    def test_missing_duplicate_or_untyped_pins_refused(self):
        for values in (fixture_pins[:-1],fixture_pins[:-1]+[fixture_pins[0]],fixture_pins[:-1]+[object()]):
            with self.assertRaises(ValueError):self.verify(values)
    def test_mixed_expected_source_refused(self):
        changed=replace(fixture_pins[0],identity=replace(fixture_pins[0].identity,source_sha256='7'*64))
        with self.assertRaises(ValueError):self.verify([changed]+fixture_pins[1:])
    def test_source_absent_or_unknown_dirty_refused(self):
        for value in (None,replace(fixture_source,git_dirty=None)):
            with self.assertRaises(ValueError):self.verify(source=value)
    def test_method_map_drift_refused(self):
        changed=dict(template_digests);changed['labram_lora']='8'*64
        with self.assertRaises(ValueError):self.verify(methods=changed)
    def test_episode_selection_preprocessing_protocol_or_seed_claim_drift_refused(self):
        for field in ('episode_sha256','selection_sha256','preprocessing_sha256','protocol_sha256'):
            identity=replace(fixture_pins[0].identity,**{field:'9'*64})
            with self.assertRaises(ValueError):self.verify([replace(fixture_pins[0],identity=identity)]+fixture_pins[1:])
        identity=replace(fixture_pins[0].identity,support_draw_seed=99)
        with self.assertRaises(ValueError):self.verify([replace(fixture_pins[0],identity=identity)]+fixture_pins[1:])
    def test_record_envelope_drift_refused(self):
        records=dict(route._full_route.episode_records_json);records['subject_02']='{}'
        bad=replace(route,_full_route=replace(route._full_route,episode_records_json=records))
        with self.assertRaises(ValueError):I.verify_case_identity_bindings(ROOT,bad,fixture_pins,method_config_sha256=template_digests,expected_source=fixture_source)
    def test_wrong_route_type_or_truncated_contract_refused(self):
        for value in (route._full_route,replace(route,contract=replace(route.contract,plans=route.plans[:-1]))):
            with self.assertRaises(ValueError):I.select_plans(ROOT,value,case_limit=1)
    def test_204_exact_five_seed_means_and51_pairs(self):
        result=I.build_paired_inputs(ROOT,route,fixture_rows)
        self.assertEqual(len(result.aggregation.means),204);self.assertEqual(len(result.aggregation.admitted_digests),1020)
        self.assertEqual(result.paired_differences,tuple((s,Fraction(1,10)) for s in I.TARGETS))
    def test_reordered_exact_scores_are_stable(self):
        self.assertEqual(I.build_paired_inputs(ROOT,route,fixture_rows),I.build_paired_inputs(ROOT,route,reversed(fixture_rows)))
    def test_missing_duplicate_or_rounded_scores_refused(self):
        for values in (fixture_rows[:-1],fixture_rows[:-1]+[fixture_rows[0]],[0.5]*1020):
            with self.assertRaises(ValueError):I.build_paired_inputs(ROOT,route,values)
    def test_reused_digest_or_outside_score_refused(self):
        changed=replace(fixture_rows[1],cell_sha256=fixture_rows[0].cell_sha256)
        outside=replace(fixture_rows[0],key=ExpectedCell('cho2017','subject_01','labram_linear',5,11))
        for value in (changed,outside):
            with self.assertRaises(ValueError):I.build_paired_inputs(ROOT,route,[fixture_rows[0],value]+fixture_rows[2:])

suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(BridgeChecks),unittest.defaultTestLoader.loadTestsFromTestCase(InterfaceChecks)))'''
code=change(code,before,tests)
code=change(code,"'schema':'cho51_actual_worker_real_input_bridge_qualification_v1'","'schema':'cho51_read_only_execution_interfaces_qualification_v1'")
code=change(code,"'full_selector_sweep_collector_or_numerical_worker_qualified':False","'bounded_case_selection_qualified':True,'sweep_planning_qualified':True,'identity_and_exact_score_interfaces_qualified_on_fabricated_records':True,'fabricated_pin_and_score_cells':1020,'real_recorder_publication_or_tensor_or_selector_or_sweep_execution_qualified':False,'full_selector_sweep_collector_or_numerical_worker_qualified':False")
code=change(code,"('sample_binding.json',asdict(sample.binding))","('sample_binding.json',asdict(sample.binding)),('sweep_schedule.json',I.sweep_schedule(ROOT,route,case_limit=1020)),('fabricated_pairs.json',[{'subject':s,'numerator':d.numerator,'denominator':d.denominator} for s,d in I.build_paired_inputs(ROOT,route,fixture_rows).paired_differences])")
path=root/'docs/phase2/cho51_execution_interfaces_v1/validate_interfaces.py'
with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(code)
compile(code,str(path),'exec')
prep=retained('recipes/prepare_pins_001.py')
prep=change(prep,"paths += [p.relative_to(root).as_posix() for p in (root/'docs/phase2/cho51_worker_bridge_v1').glob('*.py')]","paths += ['docs/phase2/cho51_worker_bridge_v1/worker_bridge.py','docs/phase2/cho51_execution_interfaces_v1/interfaces.py','docs/phase2/cho51_execution_interfaces_v1/validate_interfaces.py','runs/coordination/cho51_execution_interfaces_20261013_v1/prepare_candidate_001.py','runs/coordination/cho51_execution_interfaces_20261013_v1/prepare_pins_001.py']")
prep=change(prep,"'execution_git':'9238c79ab4cd53ebdf7a613f204e67dd5da29378'","'execution_git':'706a449b469b9e84235869e875bb8b0bf5907727'")
prep=change(prep,"'schema':'cho51_worker_real_input_fresh_pins_v1'","'schema':'cho51_execution_interfaces_fresh_pins_v1'")
prep=change(prep,"root/'docs/phase2/cho51_worker_bridge_v1'","root/'docs/phase2/cho51_execution_interfaces_v1'")
with (run/'prepare_pins_001.py').open('x',encoding='utf-8',newline='\n') as stream:stream.write(prep)
compile(prep,str(run/'prepare_pins_001.py'),'exec')
print(json.dumps({'syntax':'pass','real_input_checks':15,'interface_checks':21,'fabricated_pins_and_scores':1020,'scientific_admission':False}))
