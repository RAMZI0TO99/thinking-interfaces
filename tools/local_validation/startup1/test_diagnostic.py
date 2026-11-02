"""Supplied capsule/receipt/marker contract controls, no process or file access.

Fresh SQ invokes the production PowerShell controller for fast/stall controls;
these tests do not pretend to simulate its native lifecycle or timer callback.
"""
import copy
import json
import unittest
from . import contract as c

class DiagnosticContractTests(unittest.TestCase):
    def reference(self,path):return dict(path=path,bytes=1,sha256='1'*64)
    def fixture(self,role='Q_STARTUP_CONTROL',probe='fast'):
        root='D:/Aenv/pro3';operation='00000000-0000-4000-8000-000000000003';output=root+'/runs/coordination/owned/attempts/'+operation
        ref=self.reference
        environment=dict(SystemRoot='C:/Windows',WINDIR='C:/Windows',PATH='C:/pwsh;C:/Windows/System32',HOME=output,USERPROFILE=output,TEMP=output,TMP=output,
            OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='-1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
        value=dict(schema='cho51_startup_capsule_v1',issuer='project_root',operation_id=operation,role=role,probe=probe,
            created_utc='2026-10-31T00:00:00Z',expires_utc='2026-10-31T00:01:00Z',project_root=root,
            stop_path=root+'/runs/coordination/PROJECT_STOP.json',output_root=output,
            helper=dict(ref(root+'/runs/coordination/owned/helper.dll'),native_identity='1'*16+':'+'2'*32),
            q2_qualification=ref(root+'/runs/coordination/owned/q2.json'),q2_actual_review=ref(root+'/runs/coordination/owned/actual.json'),
            source_review=ref(root+'/runs/coordination/owned/source.json'),adoption=ref(root+'/runs/coordination/owned/adoption.json'),
            qualification=None if role=='Q_STARTUP_CONTROL' else ref(root+'/runs/coordination/owned/qualification.json'),
            sources={root+'/tools/local_validation/startup1/'+name:dict(bytes=1,sha256='1'*64) for name in c.SOURCE_LEAVES},
            caller_runtime=dict(executable=ref('C:/pwsh/pwsh.exe'),version='owned',files=[ref('C:/pwsh/pwsh.exe')]),
            environment=environment,limits=dict(c.LIMITS),safety=dict(c.SAFETY),
            enclosing_q=dict(operation_id='00000000-0000-4000-8000-000000000002',admission=ref(root+'/runs/coordination/owned/q.json'),limits=dict(process_mib=512,job_mib=768)) if role=='Q_STARTUP_CONTROL' else None)
        return value
    def validate(self,value):return c.validate_capsule(value,'2026-10-31T00:00:01Z')
    def receipt(self):
        capsule=self.fixture();origin=dict(utc='2026-10-31T00:00:01Z',qpc=1000,frequency=1000)
        sample=dict(qpc_begin=1000,qpc_end=1010,ram_sample_bytes=4*1024**3,minimum_disk_bytes_so_far=20*1024**3,
            peak_caller_private_bytes_so_far=128*1024**2,managed_current_private_bytes=128*1024**2,native_predicates_passed=True)
        guard=dict(ready=True,stop=True,done=True,error=None,last=6200,samples=10,first=sample,second=dict(sample,qpc_begin=1210,qpc_end=1220),joined=True,closed=True,completion_wait_closed=True)
        custody={name:True for name in c.CUSTODY_TRUE};custody.update(StdoutOverflow=False,StderrOverflow=False,Fault=None,CleanupError=None,StdoutError=None,StderrError=None,CreationFileTime=1,Pid=1)
        outputs=[dict(self.reference(capsule['output_root']+'/'+name),native_identity='1'*16+':'+'2'*32) for name in ('claim.json','stdout.bin','stderr.bin','observation.json','journal.json')]
        value=dict(schema='cho51_startup_external_return_v1',operation_id=capsule['operation_id'],role=capsule['role'],probe=capsule['probe'],status='observed_diagnostic_only',failure=None,origin=origin,
            caller=dict(pid=1,creation_filetime=1),elapsed_seconds=5.2,authority_verified=True,native_ids_bound=True,dispose_registration_joined=True,owned_lifecycle_closed=True,custody=custody,
            original_streams_closed=True,final_input_verification=True,final_output_verification=True,guard=guard,observation=outputs[3],outputs=outputs,actual_tool_return_pending=True,
            exit_code=None,termination_cause='unobserved',**c.SAFETY)
        return capsule,value
    def markers(self,probe='fast'):
        origin=dict(utc='2026-10-31T00:00:01Z',qpc=1000,frequency=1000)
        rows=[dict(schema='cho51_startup_probe_marker_v1',sequence=i,event=event,origin_utc=origin['utc'],origin_qpc=1000,frequency=1000,qpc=2000+i*100,elapsed_seconds=1+i*.1,detail='') for i,event in enumerate(c.MARKERS[probe])]
        return origin,rows
    def source_review(self):
        value=self.fixture()
        review=dict(schema='cho51_startup_source_review_v1',status='ACCEPTED_SOURCE_STARTUP1',reviewer='owned_reviewer',authors=['owned_author'],
            created_utc='2026-10-31T00:00:00Z',sources=copy.deepcopy(value['sources']),design=self.reference('D:/owned/design.md'),
            design_acceptance=self.reference('D:/owned/design-acceptance.json'),findings=[],checks=['owned contract fixture'],limitations=['not real-controller qualification'])
        return value['sources'],review
    def test_exact_q_capsule(self):
        value=self.fixture();self.assertIs(self.validate(value),value)
    def test_exact_d_capsule(self):self.assertEqual(self.validate(self.fixture('D','pdh'))['role'],'D')
    def test_production_cannot_select_fixture(self):
        with self.assertRaises(c.Refusal):self.validate(self.fixture('D','fast'))
    def test_q_cannot_select_pdh(self):
        with self.assertRaises(c.Refusal):self.validate(self.fixture('Q_STARTUP_CONTROL','pdh'))
    def test_no_self_qualification(self):
        value=self.fixture();value['qualification']=self.reference('D:/owned/future.json')
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_missing_source(self):
        value=self.fixture();value['sources'].pop(next(iter(value['sources'])))
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_unknown_source(self):
        value=self.fixture();value['sources']['D:/foreign.py']=dict(bytes=1,sha256='1'*64)
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_startup_clock_not_extended(self):
        value=self.fixture();value['limits']['startup_seconds']=6
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_bool_not_budget_integer(self):
        value=self.fixture();value['limits']['startup_seconds']=True
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_original_interval_not_child_reset(self):
        value=self.fixture();value['expires_utc']='2026-10-31T00:00:15Z'
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_unknown_capsule_key(self):
        value=self.fixture();value['run_anything']=True
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_environment_ambient_override(self):
        value=self.fixture();value['environment']['PYTHONPATH']='foreign'
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_environment_home_outside_attempt(self):
        value=self.fixture();value['environment']['HOME']='D:/shared'
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_runtime_executable_missing(self):
        value=self.fixture();value['caller_runtime']['files']=[self.reference('C:/pwsh/other.dll')]
        with self.assertRaises(c.Refusal):self.validate(value)
    def test_duplicate_json(self):
        with self.assertRaises(c.Refusal):c.parse(b'{"x":1,"x":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(c.Refusal):c.parse(b'{"x":1e999}')
    def test_json_depth(self):
        value=1
        for unused in range(17):value=[value]
        with self.assertRaises(c.Refusal):c.parse(json.dumps(value).encode())
    def test_fast_marker_protocol(self):
        origin,rows=self.markers();self.assertTrue(c.validate_markers(rows,'fast',origin))
    def test_stall_marker_prefix(self):
        origin,rows=self.markers('stall');self.assertTrue(c.validate_markers(rows,'stall',origin))
    def test_marker_reordered(self):
        origin,rows=self.markers();rows[1]['event']='fixture_fast_begin'
        with self.assertRaises(c.Refusal):c.validate_markers(rows,'fast',origin)
    def test_marker_wrong_origin(self):
        origin,rows=self.markers();rows[0]['origin_qpc']=999
        with self.assertRaises(c.Refusal):c.validate_markers(rows,'fast',origin)
    def test_marker_clock_range(self):
        origin,rows=self.markers();rows[0]['qpc']=6001;rows[0]['elapsed_seconds']=5.001
        with self.assertRaises(c.Refusal):c.validate_markers(rows,'fast',origin)
    def test_receipt_complete_supplied_evidence(self):
        capsule,value=self.receipt();self.assertIs(c.validate_external_return(value,capsule),value)
    def test_disposed_boolean_not_registration_join(self):
        capsule,value=self.receipt();value['dispose_registration_joined']=False
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_owner_fault_not_cleanup_success(self):
        capsule,value=self.receipt();value['custody']['Fault']='resource'
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_missing_pipe_closure(self):
        capsule,value=self.receipt();value['custody']['StdoutReaderClosed']=False
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_final_input_check_required(self):
        capsule,value=self.receipt();value['final_input_verification']=False
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_guard_join_required(self):
        capsule,value=self.receipt();value['guard']['joined']=False
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_sample_spacing_required(self):
        capsule,value=self.receipt();value['guard']['second']['qpc_begin']=1209
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_observed_exit_cannot_be_invented(self):
        capsule,value=self.receipt();value['exit_code']=0
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_output_native_identity_required(self):
        capsule,value=self.receipt();value['outputs'][0]['native_identity']='basename'
        with self.assertRaises(c.Refusal):c.validate_external_return(value,capsule)
    def test_empty_markers_refused(self):
        origin,rows=self.markers()
        with self.assertRaises(c.Refusal):c.validate_markers([],'fast',origin)
    def test_partial_fast_markers_refused(self):
        origin,rows=self.markers()
        with self.assertRaises(c.Refusal):c.validate_markers(rows[:1],'fast',origin)
    def test_nonempty_pdh_prefix_is_not_full_success(self):
        origin,rows=self.markers('pdh');self.assertFalse(c.validate_markers(rows[:1],'pdh',origin))
    def test_source_review_exact_acceptance(self):
        sources,review=self.source_review();self.assertIs(c.validate_source_review(review,sources),review)
    def test_source_review_unresolved_findings(self):
        sources,review=self.source_review();review['findings']=[dict(id='owned_blocker',status='unresolved')]
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
    def test_source_review_reviewer_object_refused(self):
        sources,review=self.source_review();review['reviewer']={'name':'owned_reviewer'}
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
    def test_source_review_reviewer_cannot_author(self):
        sources,review=self.source_review();review['reviewer']='owned_author'
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
    def test_source_review_author_identity_typed(self):
        sources,review=self.source_review();review['authors']=[7]
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
    def test_source_review_duplicate_authors(self):
        sources,review=self.source_review();review['authors']=['owned_author','owned_author']
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
    def test_production_cannot_select_negative_probe(self):
        with self.assertRaises(c.Refusal):self.validate(self.fixture('D','malformed'))
    def test_source_review_unknown_authority_key(self):
        sources,review=self.source_review();review['ignore_findings']=True
        with self.assertRaises(c.Refusal):c.validate_source_review(review,sources)
