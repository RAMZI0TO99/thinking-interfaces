import copy
import unittest
from .authority import enrich,validate_chain,validate_environment,ENVIRONMENT_REQUIRED,ENVIRONMENT_FIXED
from ..l1.protocol import Refusal
from ..l1.test_support import retained

class AuthorityTests(unittest.TestCase):
    def fixture(self):
        descriptor=retained();reference={k:descriptor[k] for k in ('path','bytes','sha256','role')}
        class Reader:
            def retain(self,path,pin):return descriptor
        return descriptor,reference,Reader()
    def test_current_identity_enrichment(self):
        descriptor,reference,reader=self.fixture()
        result=enrich(reference,{descriptor['path']:descriptor},reader,lambda:True)
        self.assertEqual(result['native_identity'],descriptor['native_identity'])
        self.assertEqual(result['sharing'],dict(read=True,write=False,delete=False))
    def test_old_p_missing_new_source(self):
        descriptor,reference,reader=self.fixture()
        with self.assertRaises(Refusal):enrich(reference,{},reader,lambda:True)
    def test_p_pin_drift(self):
        descriptor,reference,reader=self.fixture();bad=dict(descriptor,sha256='f'*64)
        with self.assertRaises(Refusal):enrich(reference,{descriptor['path']:bad},reader,lambda:True)
    def test_p_native_identity_drift(self):
        descriptor,reference,reader=self.fixture();bad=copy.deepcopy(descriptor);bad['native_identity']['file_id']='f'*32
        with self.assertRaises(Refusal):enrich(reference,{descriptor['path']:bad},reader,lambda:True)
    def environment(self):return dict({key:'D:/owned' for key in ENVIRONMENT_REQUIRED},**ENVIRONMENT_FIXED)
    def test_environment_allowlist(self):
        value=self.environment();self.assertIs(validate_environment(value),value)
    def test_environment_ambient_override(self):
        value=self.environment();value['PYTHONPATH']='D:/foreign'
        with self.assertRaises(Refusal):validate_environment(value)
    def test_environment_unknown_variable(self):
        value=self.environment();value['UNREVIEWED_PACKAGE_CONFIG']='foreign'
        with self.assertRaises(Refusal):validate_environment(value)
    def test_environment_case_alias(self):
        value=self.environment();value['path']='D:/foreign'
        with self.assertRaises(Refusal):validate_environment(value)
    def test_environment_missing_windows_variable(self):
        value=self.environment();del value['SystemRoot']
        with self.assertRaises(Refusal):validate_environment(value)
    def test_environment_thread_cap(self):
        value=self.environment();value['MKL_NUM_THREADS']='2'
        with self.assertRaises(Refusal):validate_environment(value)
    def test_environment_nul_before_native(self):
        value=self.environment();value['PATH']='D:/owned\0D:/foreign'
        with self.assertRaises(Refusal):validate_environment(value)
    def chain(self):
        from .authority import PROJECT,L_PHASE,BOOTSTRAP,LIMITS,fixed_command
        from ..l1.protocol import SAFETY
        def reference(name):
            row=retained(PROJECT+'/fixture/'+name+'.json');return {k:row[k] for k in ('path','bytes','sha256','role')}
        refs={name:reference(name) for name in ('adoption','plan','review','q','p','result','index','source_manifest',
              'runtime_manifest','design','design_review','q_source','q_actual','p_source','p_actual','coverage','request')}
        when='2026-10-31T00:00:00Z';operation='00000000-0000-4000-8000-000000000003'
        environment=self.environment();environment['PYTHONPYCACHEPREFIX']=L_PHASE+'/disabled-bytecode/'+operation
        safe=dict(zip(SAFETY,[False]*5+[0,0]))
        request=dict(schema='cho51_l_request_v1',stage='L',operation_id=operation,created_utc=when,
            adoption=refs['adoption'],plan=refs['plan'],source_manifest=refs['source_manifest'],runtime_manifest=refs['runtime_manifest'],
            preparation_p=refs['p'],preparation_result=refs['result'],preparation_index=refs['index'],
            predecessor_reviews=[refs[k] for k in ('q_source','q_actual','p_source','p_actual')],
            command=[],cwd=PROJECT,roots=dict(project=PROJECT,runtime='C:/Python',site=PROJECT+'/.venv/Lib/site-packages'),
            control_inputs=[],attempt_root=L_PHASE+'/attempts/'+operation,stop_path=PROJECT+'/runs/coordination/PROJECT_STOP.json',
            environment=environment,limits=copy.deepcopy(LIMITS),
            forbidden_effects=['candidate_execution','fixtures','subprocess','network','git','data','weights','model','GPU','scientific_admission'],
            requested_window=dict(starts_utc=when,expires_utc='2026-10-31T00:10:00Z'),safety=safe)
        request['command']=fixed_command(request)
        admission=dict(schema='cho51_l_admission_v1',issuer='project_root',created_utc=when,stage='L',operation_id=operation,
            request=refs['request'],implementation_review=refs['review'],adoption=refs['adoption'],
            admitted_window=copy.deepcopy(request['requested_window']),resource_observation={},limits=copy.deepcopy(LIMITS),
            permitted_command=list(request['command']),attempt_root=request['attempt_root'],stop_path=request['stop_path'],
            authorized_new_l_only=True,safety=copy.deepcopy(safe))
        sources={path:dict(bytes=1,sha256='a'*64) for path in (BOOTSTRAP,PROJECT+'/tools/local_validation/lhost1/invoke_l.ps1',PROJECT+'/fixture/design.md')}
        def review(status,reviewer):return dict(status=status,reviewer=reviewer,authors=['fixture_author'],findings=[],created_utc=when)
        qsource=review('ACCEPTED_SOURCE_LQ1','q_source');qsource['sources']=copy.deepcopy(sources)
        psource=review('ACCEPTED_SOURCE_LP1','p_source');psource['sources']=copy.deepcopy(sources)
        lreview=review('ACCEPTED_SOURCE_L1','l_source');lreview.update(sources=copy.deepcopy(sources),runtime_manifest=refs['runtime_manifest'])
        qop='00000000-0000-4000-8000-000000000001';pop='00000000-0000-4000-8000-000000000002'
        qactual=review('ACCEPTED_LQ1_TESTED_SCOPE','actual');qactual.update(operation_id=qop,source_review_sha256=refs['q_source']['sha256'],actual_tool_exit_code=0,new_operation_owned_lifecycle_closed=True)
        pactual=review('ACCEPTED_LP1_PHYSICAL_ONLY','actual');pactual.update(operation_id=pop,source_review_sha256=refs['p_source']['sha256'],actual_tool_exit_code=0,new_operation_owned_lifecycle_closed=True,
            final_full_input_verification_completed_before_release=True,input_identity_verified_before_release=True,output_identity_verified_before_release=True,
            accepted_result=refs['result'],accepted_physical_index=refs['index'],coverage_review_sha256=refs['coverage']['sha256'])
        design_files={PROJECT+'/fixture/design.md':sources[PROJECT+'/fixture/design.md']}
        design_review=review('ACCEPTED_DESIGN_ONLY','design_reviewer');design_review['design_files']=design_files
        records={refs['adoption']['path']:dict(schema='cho51_l_adoption_v1',author='project_root',created_utc=when,
                    design=refs['design'],implementation_review=refs['review'],qualification_q=refs['q'],preparation_p=refs['p'],plan=refs['plan'],
                    scoped_policy_replacement='local-contract-only; original-full-restart-claim-unchanged',safety=safe),
                 refs['review']['path']:lreview,refs['q_source']['path']:qsource,refs['q_actual']['path']:qactual,
                 refs['p_source']['path']:psource,refs['p_actual']['path']:pactual,
                 refs['coverage']['path']:review('ACCEPTED_PROPOSED_P2_PHYSICAL_COVERAGE','coverage_reviewer'),
                 refs['source_manifest']['path']:dict(schema='cho51_l_source_manifest_v1',project_root=PROJECT,
                     files=[dict(path=path,**pin,role='source') for path,pin in sources.items()]),
                 refs['runtime_manifest']['path']:dict(schema='cho51_l_runtime_manifest_v1',root='C:/Python',executable='C:/Python/python.exe',
                     files=[dict(path='C:/Python/python.exe',bytes=1,sha256='a'*64,role='runtime')],census=[]),
                 refs['design']['path']:dict(schema='cho51_l_root_design_acceptance_v1',author='project_root',created_utc=when,
                     status='ACCEPTED_DESIGN_ONLY',review=refs['design_review'],design_files=design_files),
                 refs['design_review']['path']:design_review,
                 refs['q']['path']:dict(author='project_root',status='QUALIFIED_LQ1_MECHANISMS_ONLY',created_utc=when,operation_id=qop,
                     source_review=refs['q_source'],actual_review=refs['q_actual']),
                 refs['p']['path']:dict(author='project_root',status='QUALIFIED_LP1_PHYSICAL_ONLY',created_utc=when,operation_id=pop,
                     references=dict(source_review=refs['p_source'],actual_review=refs['p_actual'],coverage_review=refs['coverage'],q_qualification=refs['q']),
                     accepted_result=refs['result'],accepted_index=refs['index']),
                 refs['plan']['path']:{},refs['result']['path']:{},refs['index']['path']:{} }
        return request,admission,records,refs
    def test_chain_exact_roles(self):
        request,admission,records,_=self.chain();validate_chain(request,admission,records)
    def test_chain_cannot_reuse_l_operation(self):
        request,admission,records,refs=self.chain();records[refs['q']['path']]['operation_id']=request['operation_id']
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_chain_self_source_review_refused(self):
        request,admission,records,refs=self.chain();records[refs['review']['path']]['reviewer']='fixture_author'
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_chain_qualifications_not_interchangeable(self):
        request,admission,records,refs=self.chain();records[refs['q']['path']]['status']='QUALIFIED_LP1_PHYSICAL_ONLY'
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_fixed_command_positive(self):
        from .authority import validate
        request,admission,_,_=self.chain();validate(request,admission,dict(utc=request['created_utc']))
    def test_fixed_command_rejects_each_executable_mode_and_argument_change(self):
        from .authority import validate
        for index in (0,1,4,5,6,7,8,16):
            request,admission,_,_=self.chain();request['command'][index]='arbitrary'
            admission['permitted_command']=list(request['command'])
            with self.assertRaises(Refusal):validate(request,admission,dict(utc=request['created_utc']))
    def test_fixed_command_extra_code_and_missing_argument(self):
        from .authority import validate
        for addition in (True,False):
            request,admission,_,_=self.chain()
            if addition:request['command']+=['-c','arbitrary()']
            else:request['command'].pop()
            admission['permitted_command']=list(request['command'])
            with self.assertRaises(Refusal):validate(request,admission,dict(utc=request['created_utc']))
    def test_fixed_command_roots_cwd_attempt_and_cache(self):
        from .authority import validate
        for key in ('cwd','attempt_root','stop_path','project','site','cache'):
            request,admission,_,_=self.chain()
            if key in ('project','site'):request['roots'][key]='D:/foreign'
            elif key=='cache':request['environment']['PYTHONPYCACHEPREFIX']='D:/foreign'
            else:
                request[key]='D:/foreign'
                if key in admission:admission[key]='D:/foreign'
            with self.assertRaises(Refusal):validate(request,admission,dict(utc=request['created_utc']))
    def test_changed_manifest_cannot_borrow_source_review(self):
        request,admission,records,refs=self.chain()
        records[refs['source_manifest']['path']]['files'][0]['sha256']='f'*64
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_unreviewed_runtime_manifest(self):
        request,admission,records,refs=self.chain()
        records[refs['review']['path']]['runtime_manifest']=dict(refs['runtime_manifest'],sha256='f'*64)
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_command_executable_must_match_reviewed_runtime(self):
        request,admission,records,refs=self.chain()
        records[refs['runtime_manifest']['path']]['executable']='C:/Python/arbitrary.exe'
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_stale_q_does_not_qualify_changed_l_sources(self):
        request,admission,records,refs=self.chain()
        sources=records[refs['q_source']['path']]['sources'];sources[next(iter(sources))]['sha256']='f'*64
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_changed_design_or_wrong_acceptance_status(self):
        for field,value in (('status','PROPOSED'),('author','not_root')):
            request,admission,records,refs=self.chain();records[refs['design']['path']][field]=value
            with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_exact_predecessor_review_set(self):
        request,admission,records,refs=self.chain();request['predecessor_reviews'][-1]=refs['q_actual']
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_q_and_p_must_join_same_qualification(self):
        request,admission,records,refs=self.chain()
        records[refs['p']['path']]['references']['q_qualification']=dict(refs['q'],sha256='f'*64)
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_actual_review_separate_role_and_positive_lifecycle(self):
        for field,value in (('reviewer','q_source'),('new_operation_owned_lifecycle_closed',False),('actual_tool_exit_code',True)):
            request,admission,records,refs=self.chain();records[refs['q_actual']['path']][field]=value
            with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_p_final_verification_and_result_join(self):
        request,admission,records,refs=self.chain();records[refs['p_actual']['path']]['final_full_input_verification_completed_before_release']=False
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
        request,admission,records,refs=self.chain();records[refs['p_actual']['path']]['accepted_result']=dict(refs['result'],sha256='f'*64)
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_review_and_adoption_order(self):
        request,admission,records,refs=self.chain();records[refs['q_actual']['path']]['created_utc']='2026-10-31T01:00:00Z'
        with self.assertRaises(Refusal):validate_chain(request,admission,records)
    def test_finite_chain_loading_and_conflicting_pins(self):
        from .authority import retain_chain
        request,admission,records,refs=self.chain();seen=[]
        def read(row):seen.append(row['path']);return records[row['path']]
        loaded=retain_chain(request,admission,read);validate_chain(request,admission,loaded)
        self.assertEqual(len(seen),len(set(seen)))
        request['control_inputs']=[dict(refs['plan'],sha256='f'*64)]
        with self.assertRaises(Refusal):retain_chain(request,admission,read)
    def plan_acceptance(self):
        request,_,_,refs=self.chain();safe=request['safety'];when=request['created_utc']
        acceptance=dict(schema='cho51_l_complete_plan_acceptance_v1',author='project_root',status='ACCEPTED_COMPLETE_L_PLAN',
            created_utc=when,plan=refs['plan'],derivation=refs['index'],review=refs['review'],safety=safe)
        review=dict(schema='cho51_l_complete_plan_review_v1',status='ACCEPTED_COMPLETE_L_PLAN_SOURCE',reviewer='independent',
            authors=['project_root'],created_utc=when,plan=refs['plan'],derivation=refs['index'],findings=[],checks=['supplied fixture'],limitations=['not execution'],safety=safe)
        derivation=dict(schema='cho51_l_plan_derivation_v1',status='COMPLETE_REQUIRES_INDEPENDENT_REVIEW',plan_ref=refs['plan'],
            pages=[],candidate_imports=0,third_party_imports=0,executed_code_from_inputs=0,launch_authorized=False)
        return request,acceptance,review,derivation
    def test_independent_complete_plan_review_positive(self):
        from .authority import validate_plan_acceptance
        validate_plan_acceptance(*self.plan_acceptance())
    def test_complete_plan_review_wrong_role_and_self_review(self):
        from .authority import validate_plan_acceptance
        for key,value in (('reviewer','project_root'),('status','ACCEPTED_DESIGN_ONLY'),('findings',['unresolved'])):
            request,acceptance,review,derivation=self.plan_acceptance();review[key]=value
            with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,derivation)
    def test_complete_plan_review_exact_plan_and_derivation(self):
        from .authority import validate_plan_acceptance
        for key in ('plan','derivation'):
            request,acceptance,review,derivation=self.plan_acceptance();review[key]=dict(review[key],sha256='f'*64)
            with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,derivation)
    def test_complete_plan_review_before_acceptance(self):
        from .authority import validate_plan_acceptance
        request,acceptance,review,derivation=self.plan_acceptance();review['created_utc']='2026-10-31T00:01:00Z'
        with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,derivation)
    def test_complete_plan_cannot_hide_refusals_or_execution(self):
        from .authority import validate_plan_acceptance
        for key,value in (('status','INCOMPLETE_REFUSED'),('pages',[dict(kind='refusals')]),('candidate_imports',1),('launch_authorized',True)):
            request,acceptance,review,derivation=self.plan_acceptance();derivation[key]=value
            with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,derivation)
    def test_complete_plan_closed_review(self):
        from .authority import validate_plan_acceptance
        request,acceptance,review,derivation=self.plan_acceptance();review['authority_override']=True
        with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,derivation)
    def plan_reader(self):
        from ..l1.protocol import encode
        import hashlib
        raw=encode(dict(value=1));descriptor=retained();descriptor.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        class Reader:
            def __init__(self):self.calls=0;self.descriptor=copy.deepcopy(descriptor)
            def retain(self,path,pin):
                self.calls+=1
                if path!=descriptor['path'] or pin!={k:descriptor[k] for k in ('bytes','sha256')}:raise Refusal('wrong reader pin')
                return self.descriptor
            def read_small(self,path,pin):
                self.retain(path,pin);return raw
        return descriptor,Reader()
    def test_enriched_preparation_recipe_and_both_roster_reads(self):
        from .supervisor import pinned_json
        descriptor,reader=self.plan_reader();reference={k:descriptor[k] for k in ('path','bytes','sha256','role')}
        plan=enrich(dict(preparation_recipe=reference,static_roster=reference),{descriptor['path']:descriptor},reader,lambda:True)
        for key in ('preparation_recipe','static_roster','static_roster'):
            self.assertEqual(pinned_json(reader,plan[key]),dict(value=1))
        self.assertGreaterEqual(reader.calls,11)
    def test_enriched_plan_read_rejects_changed_native_identity(self):
        from .supervisor import pinned_json
        descriptor,reader=self.plan_reader();reader.descriptor['native_identity']['file_id']='f'*32
        with self.assertRaises(Refusal):pinned_json(reader,descriptor)
    def test_plain_control_read_keeps_exact_pin(self):
        from .supervisor import pinned_json
        descriptor,reader=self.plan_reader();reference={k:descriptor[k] for k in ('path','bytes','sha256','role')}
        self.assertEqual(pinned_json(reader,reference),dict(value=1))
        reference['sha256']='f'*64
        with self.assertRaises(Refusal):pinned_json(reader,reference)
    def test_enriched_plan_read_rejects_incomplete_custody_shape(self):
        from .supervisor import pinned_json
        descriptor,reader=self.plan_reader();del descriptor['sharing']
        with self.assertRaises(Refusal):pinned_json(reader,descriptor)
