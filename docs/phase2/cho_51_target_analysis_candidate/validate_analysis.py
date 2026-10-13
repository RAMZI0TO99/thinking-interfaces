"""Bounded synthetic checks of the unadopted candidate; never a scientific run."""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-directory', required=True, type=Path)
parser.add_argument('--pins', required=True, type=Path)
args = parser.parse_args()
OUT = args.output_directory.resolve()
assert OUT.is_relative_to(ROOT/'runs/coordination/cho51_synthetic_analysis_20261013_v1')
OUT.mkdir(exist_ok=False)
temp = OUT/'tmp'
temp.mkdir()
os.environ['TEMP'] = os.environ['TMP'] = str(temp)
sys.path.append(str(ROOT/'.venv/Lib/site-packages'))
sys.dont_write_bytecode = True
pins = json.loads(args.pins.read_bytes())
for relative, digest in pins['files'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest, relative

denied = []
pause_paths = [Path(r'D:\Aenv\pro2\WORK')/folder/'coordination/PRO2_REQUEST_PRO3_PAUSE.json' for folder in ('resume-20261007-001','resume-20261012-001','resume-20261013-001')]

def audit(event, values):
    refused = event.startswith('socket.') or event in {'subprocess.Popen','os.system','os.startfile','os.startfile/2','os.fork','os.posix_spawn'}
    if event == 'open' and values and isinstance(values[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(values[0])).resolve()
        mode = values[1] if len(values) > 1 else None
        flags = values[2] if len(values) > 2 else 0
        writing = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        refused = refused or path.suffix.lower() in {'.npy','.npz','.edf','.mat','.pt','.pth','.ckpt','.safetensors'} or (writing and not path.is_relative_to(OUT))
    if event in {'os.remove','os.rmdir','os.mkdir','os.rename','os.replace'}:
        candidates = values[:2] if event in {'os.rename','os.replace'} else values[:1]
        for item in candidates:
            if isinstance(item,(str,bytes,os.PathLike)):
                path = Path(os.fsdecode(item)).resolve()
                if not path.is_relative_to(OUT): refused = True
    if refused:
        denied.append({'event':event})
        raise PermissionError('synthetic scope refused '+event)

sys.addaudithook(audit)
namespace = {'__name__':'_cho51_candidate', '__file__':str(Path(__file__).parent/'synthetic_analysis.py')}
candidate_path = Path(namespace['__file__'])
exec(compile(candidate_path.read_bytes(),str(candidate_path),'exec',dont_inherit=True),namespace)
started = time.monotonic()
D = namespace['dependencies'](ROOT)
H,A,B,C,P,R = D
S = namespace['SUBJECTS']
reports = {}

def report(name):
    if name not in reports: reports[name] = namespace['build_fixture_report'](D,name)
    return reports[name]

def ratio(value):
    return Fraction(value['numerator'],value['denominator'])

class CandidateChecks(unittest.TestCase):
    def setUp(self):
        self.assertFalse(any(p.exists() for p in pause_paths),'genuine peer pause requested')

    def test_complete_retained_roster(self):
        value=report('zero')
        self.assertEqual((value['fabricated_cells'],value['five_seed_means'],value['subject_count']),(1020,204,51))
        self.assertEqual((value['student_t_df'],value['sample_variance_denominator']),(50,50))
        self.assertEqual(value['available_cohort_subjects'],52)
        self.assertNotIn('subject_01',value['evaluation_target_ids'])

    def test_zero_point_interval(self):
        value=report('zero')
        self.assertEqual(ratio(value['exact_mean_difference']),0)
        self.assertEqual(ratio(value['exact_sample_variance']),0)
        self.assertEqual(value['wilcoxon_p_value_unrounded'],1.0)
        self.assertEqual(value['zero_count'],51)
        self.assertEqual(value['paired_mean_ci_95'],[0.0,0.0])
        self.assertEqual(value['paired_mean_ci_90'],[0.0,0.0])

    def test_positive_and_negative(self):
        pos,neg=report('positive'),report('negative')
        self.assertEqual(ratio(pos['exact_mean_difference']),Fraction(1,10))
        self.assertEqual(ratio(neg['exact_mean_difference']),Fraction(-1,10))
        self.assertLess(pos['wilcoxon_p_value_unrounded'],0.05)
        self.assertGreater(neg['wilcoxon_p_value_unrounded'],0.95)
        self.assertTrue(pos['synthetic_numeric_conditions_met'])
        self.assertFalse(neg['synthetic_numeric_conditions_met'])
        self.assertEqual(pos['paired_mean_ci_95'],[0.1,0.1])

    def test_known_uniform_ramp_moments_and_df(self):
        value=report('ramp')
        self.assertEqual(ratio(value['exact_mean_difference']),Fraction(1,4))
        self.assertEqual(ratio(value['exact_sample_variance']),Fraction(221,10000))
        from scipy.stats import t
        se=math.sqrt(221/510000)
        for confidence,key in ((0.95,'paired_mean_ci_95'),(0.90,'paired_mean_ci_90')):
            endpoints=value[key]
            critical=t.ppf((1+confidence)/2,50)
            self.assertAlmostEqual(endpoints[0],0.25-critical*se,places=14)
            self.assertAlmostEqual(endpoints[1],0.25+critical*se,places=14)
            self.assertGreater(abs(endpoints[1]-(0.25+t.ppf((1+confidence)/2,51)*se)),1e-6)

    def test_ties_and_pratt_zeros(self):
        value=report('ties')
        self.assertEqual((value['zero_count'],value['nonzero_tied_subject_count'],value['nonzero_absolute_tie_class_count']),(13,38,2))
        self.assertEqual(ratio(value['exact_mean_difference']),Fraction(4,85))
        levels=[(0,1,-1,2)[i%4] for i in range(51)]
        self.assertEqual([row[1] for row in value['signed_rank_levels']],levels)
        from scipy.stats import wilcoxon
        oracle=wilcoxon(levels,zero_method='pratt',alternative='greater',method='asymptotic',correction=False)
        self.assertEqual(value['wilcoxon_p_value_unrounded'],float(oracle.pvalue))
        self.assertEqual(value['wilcoxon_statistic'],float(oracle.statistic))

    def test_rank_and_mean_disagreement(self):
        value=report('rank_mean_disagree')
        self.assertLess(value['wilcoxon_p_value_unrounded'],0.05)
        self.assertEqual(ratio(value['exact_mean_difference']),Fraction(-3,340))
        self.assertFalse(value['synthetic_numeric_conditions_met'])

    def test_exact_seed_aggregation(self):
        rows=namespace['fabricate'](A,P,'ties')
        aggregated,_=namespace['collect'](A,rows)
        for item in aggregated.means:
            self.assertEqual(item.contributing_cells,5)
            index=S.index(item.subject)
            expected={'labram_linear':Fraction(1,2),'labram_lora':Fraction(1,2)+namespace['difference']('ties',index),'labram_full':Fraction(9,20),'eegnet':Fraction(11,20)}[item.method]
            self.assertEqual(Fraction(item.numerator,item.denominator),expected)

    def test_missing_cell_refused(self):
        rows=namespace['fabricate'](A,P,'zero')
        with self.assertRaisesRegex(ValueError,'missing score rows'): namespace['collect'](A,rows[:-1])

    def test_duplicate_cell_refused(self):
        rows=namespace['fabricate'](A,P,'zero')
        with self.assertRaisesRegex(ValueError,'duplicate score row'): namespace['collect'](A,rows+[rows[0]])

    def test_subject01_row_refused(self):
        rows=namespace['fabricate'](A,P,'zero')
        rows[0]=A.ScoreRow(A.ExpectedCell('cho2017','subject_01','labram_linear',5,11),1,2,'1'*64)
        with self.assertRaisesRegex(ValueError,'outside the expected roster'): namespace['collect'](A,rows)

    def test_wrong_seed_or_shots_refused(self):
        for shots,seed in ((5,99),(10,11)):
            rows=namespace['fabricate'](A,P,'zero')
            rows[0]=A.ScoreRow(A.ExpectedCell('cho2017','subject_02','labram_linear',shots,seed),1,2,'2'*64)
            with self.assertRaisesRegex(ValueError,'outside the expected roster'): namespace['collect'](A,rows)

    def test_reused_cell_digest_refused(self):
        rows=namespace['fabricate'](A,P,'zero')
        row=rows[1]
        rows[1]=A.ScoreRow(row.key,row.numerator,row.denominator,rows[0].cell_sha256)
        with self.assertRaisesRegex(ValueError,'cannot fill two roster cells'): namespace['collect'](A,rows)

    def test_fifty_or_fiftytwo_pairs_refused(self):
        pairs=[(s,Fraction()) for s in S]
        for values in (pairs[:-1],pairs+[('subject_01',Fraction())]):
            with self.assertRaisesRegex(ValueError,'exactly 51 paired differences'): C.calculate_51_target_paired_inference(values,expected_subjects=S)
        with self.assertRaisesRegex(ValueError,'51 distinct'): C.calculate_51_target_paired_inference(pairs,expected_subjects=B.CHO_SUBJECTS)

    def test_duplicate_pair_refused(self):
        pairs=[(s,Fraction()) for s in S]
        pairs[-1]=pairs[0]
        with self.assertRaisesRegex(ValueError,'duplicate paired subject'): C.calculate_51_target_paired_inference(pairs,expected_subjects=S)

    def test_float_and_out_of_range_refused(self):
        for value in (0.1,Fraction(2),Fraction(-2)):
            pairs=[(s,Fraction()) for s in S];pairs[0]=(S[0],value)
            with self.assertRaisesRegex(ValueError,'exact Fractions'): C.calculate_51_target_paired_inference(pairs,expected_subjects=S)

    def test_underflow_refused(self):
        pairs=[(s,Fraction(1,10**400)) for s in S]
        with self.assertRaisesRegex(ValueError,'nonzero finite float'): C.calculate_51_target_paired_inference(pairs,expected_subjects=S)

    def test_order_independent(self):
        pairs=[(s,Fraction(i,100)) for i,s in enumerate(S)]
        self.assertEqual(C.calculate_51_target_paired_inference(pairs,expected_subjects=S),C.calculate_51_target_paired_inference(pairs[::-1],expected_subjects=S[::-1]))

    def test_case_identity_change_refused(self):
        value=deepcopy(P);value['proposed_case_rows'][0]['case_id']='3'*64
        with self.assertRaisesRegex(ValueError,'case identity changed'): namespace['validate_scope'](value,R)

    def test_partial_subject_exclusion_refused(self):
        value=deepcopy(P);value['excluded_case_rows'].pop()
        with self.assertRaisesRegex(ValueError,'all20'): namespace['validate_scope'](value,R)

    def test_adoption_or_retry_claim_refused(self):
        for key,new in (('adopted',True),('scientific_execution_budget_admitted',True),('original_case_attempts_remaining',1)):
            value=deepcopy(P);value[key]=new
            with self.assertRaises(ValueError): namespace['validate_scope'](value,R)

    def test_original52_contract_preserved(self):
        pairs=[(s,Fraction()) for s in B.CHO_SUBJECTS]
        value=B.calculate_cho_paired_inference(pairs,expected_subjects=B.CHO_SUBJECTS)
        self.assertEqual(value.subject_count,52)
        with self.assertRaisesRegex(ValueError,'all 52'): B.calculate_cho_paired_inference([(s,Fraction()) for s in S],expected_subjects=S)

    def test_authority_always_false_and_no_real_interface(self):
        for name in ('zero','positive','negative','ties','rank_mean_disagree','ramp'):
            value=report(name)
            self.assertEqual(value['authority'],namespace['AUTHORITY'])
            self.assertFalse(value['authority']['scientific_claim_issued'])
            self.assertFalse(value['production_route_recorder_or_real_cell_admission_qualified'])
            self.assertEqual(value['secondary_superiority_p_values'],[])
            self.assertIsNone(value['formal_equivalence_decision'])
        self.assertEqual(denied,[])

suite=unittest.defaultTestLoader.loadTestsFromTestCase(CandidateChecks)
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful(): raise SystemExit(1)
for relative,digest in pins['files'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
assert not any(p.exists() for p in pause_paths)
assert denied == []
loaded={}
for module in tuple(sys.modules.values()):
    filename=getattr(module,'__file__',None)
    if filename and Path(filename).is_file():
        path=Path(filename).resolve()
        loaded[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
for name,value in reports.items():
    with (OUT/(name+'.json')).open('x',encoding='utf-8',newline='\n') as stream: json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
for path,digest in loaded.items(): assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
summary={'schema':'cho51_synthetic_qualification_v1','passed':True,'tests_run':result.testsRun,'fixtures':sorted(reports),'duration_seconds':time.monotonic()-started,'loaded_module_files':len(loaded),'observed_loaded_module_hashes':loaded,'selected_execution_git':pins['execution_git'],'canonical_source_sha256':pins['canonical_source_sha256'],'candidate_and_input_pins':pins['files'],'numpy_version':sys.modules['numpy'].__version__,'scipy_version':sys.modules['scipy'].__version__,'denied_operations':denied,'design_amendment_adopted':False,'scientific_admission':False,'production_route_or_real_cells_qualified':False,'original_case_attempts_remaining':0,'original52_source_unchanged':True}
with (OUT/'qualification.json').open('x',encoding='utf-8',newline='\n') as stream: json.dump(summary,stream,sort_keys=True,indent=2,allow_nan=False)
print(json.dumps({key:summary[key] for key in ('passed','tests_run','fixtures','duration_seconds','loaded_module_files','numpy_version','scipy_version','scientific_admission')}))
