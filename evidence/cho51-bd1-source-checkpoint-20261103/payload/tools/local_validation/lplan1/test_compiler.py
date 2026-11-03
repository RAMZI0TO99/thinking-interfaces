import copy
import hashlib
import unittest
from .compiler import compile_plan
from ..l1.protocol import Refusal
from ..l1.test_support import retained

class CompilerTests(unittest.TestCase):
    def fixture(self,raw=b'owned_value = 17\n'):
        descriptor=retained('D:/fixture/owned.py',raw)
        spec=dict(schema='cho51_l_plan_compiler_spec_v1',roots=[dict(path='D:/fixture',prefix='',role='project')],
              seeds=['owned'],builtin_modules=[],frozen_modules=[],decisions=[],module_choices={},
              phase_groups={'owned':dict(phase='L2',group_id='owned')},native_policy={'rows':[]},
              resource_policy={'rows':[]},abi_policy={'rows':[]},guard_policy={'rows':[]},pytest_policy={},
              bindings=dict(initialization_groups=[dict(ordinal=0,group_id='owned',phase='L2',modules=[],predecessor_groups=[],allowed_effect_ids=[],postcondition_ids=[])],
                            ordered_sys_path=['D:/fixture'],bootstrap_modules=[],host={}),
              limits=dict(modules=100,edges=100,source_bytes=1048576,ast_nodes=10000,depth=32))
        physical={descriptor['path']:descriptor};data={descriptor['path']:raw}
        return spec,physical,data
    def build(self,spec,physical,data):return compile_plan(spec,physical,lambda row:data[row['path']],lambda:True)
    def test_owned_source_complete(self):
        spec,physical,data=self.fixture();result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'COMPLETE_REQUIRES_INDEPENDENT_REVIEW')
        self.assertEqual(result['executed_code_from_inputs'],0)
    def test_missing_import_decision(self):
        spec,physical,data=self.fixture(b'import os\n');result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'INCOMPLETE_REFUSED')
        self.assertEqual(result['refusals'][0]['kind'],'import')
    def test_exact_import_graph(self):
        raw=b'import owned_dep\n';spec,physical,data=self.fixture(raw)
        extra=retained('D:/fixture/owned_dep.py',b'dep_value = 3\n');physical[extra['path']]=extra;data[extra['path']]=b'dep_value = 3\n'
        spec['phase_groups']['owned_dep']=dict(phase='L2',group_id='owned')
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=1,column=0,kind='import',
                                 action='include',targets=['owned_dep'],rationale='owned literal eager import',effect_ids=[])]
        result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'COMPLETE_REQUIRES_INDEPENDENT_REVIEW');self.assertEqual(result['coverage']['modules'],2)
    def test_dynamic_import_unknown(self):
        spec,physical,data=self.fixture(b'__import__(owned_name)\n');result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'INCOMPLETE_REFUSED');self.assertEqual(result['refusals'][0]['kind'],'dynamic-import')
    def test_source_changed_decision_stale(self):
        spec,physical,data=self.fixture(b'import os\n')
        spec['decisions']=[dict(module='owned',source_sha256='0'*64,line=1,column=0,kind='import',action='exclude',targets=[],rationale='owned dormant fixture',effect_ids=[])]
        result=self.build(spec,physical,data)
        self.assertIn('stale-decision',[r['kind'] for r in result['refusals']])
    def test_foreign_import_target_refused(self):
        raw=b'import os\n';spec,physical,data=self.fixture(raw)
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=1,column=0,kind='import',action='include',targets=['socket'],rationale='invalid target fixture',effect_ids=[])]
        with self.assertRaises(Refusal):self.build(spec,physical,data)
    def test_ambiguous_origin_refused(self):
        spec,physical,data=self.fixture();extra=retained('D:/fixture/owned/__init__.py')
        physical[extra['path']]=extra;data[extra['path']]=b'pass\n'
        result=self.build(spec,physical,data);self.assertEqual(result['refusals'][0]['kind'],'origin')
    def test_unbound_native_mediator_refused(self):
        raw=b'ctypes.CDLL("D:/owned.dll")\n';spec,physical,data=self.fixture(raw)
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=1,column=0,kind='native-load',action='mediate',targets=[],rationale='owned native fixture',effect_ids=['absent-effect'])]
        result=self.build(spec,physical,data);self.assertIn('unbound-effect',[r['kind'] for r in result['refusals']])
    def indirect(self,raw,locations,action='include'):
        spec,physical,data=self.fixture(raw)
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=line,column=column,
            kind='call',action=action,targets=[],rationale='adversarial unresolved callable',effect_ids=['owned_guard'] if action=='mediate' else []) for line,column in locations]
        spec['guard_policy']['rows']=[dict(guard_id='owned_guard')]
        result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'INCOMPLETE_REFUSED')
        self.assertIn('unresolved-call-target',[r['kind'] for r in result['refusals']])
    def test_aliased_import_include_refused(self):
        self.indirect(b'f = __import__\nf(name)\n',[(2,0)])
    def test_getattr_import_include_refused(self):
        self.indirect(b'getattr(importlib, "import_module")(name)\n',[(1,0)])
    def test_aliased_native_include_refused(self):
        self.indirect(b'f = ctypes.CDLL\nf(path)\n',[(2,0)])
    def test_container_effect_include_refused(self):
        self.indirect(b'table[0](path)\n',[(1,0)])
    def test_wrapper_returning_import_refused(self):
        self.indirect(b'factory()(name)\n',[(1,0)])
    def test_unknown_target_cannot_borrow_guard(self):
        self.indirect(b'f(path)\n',[(1,0)],'mediate')
    def test_dynamic_import_nonliteral_target_refused(self):
        raw=b'__import__(name)\n';spec,physical,data=self.fixture(raw)
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=1,column=0,
            kind='dynamic-import',action='include',targets=['invented'],rationale='unresolved nonliteral import',effect_ids=[])]
        result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'INCOMPLETE_REFUSED');self.assertIn('unresolved-import-target',[r['kind'] for r in result['refusals']])
    def test_shadowed_import_builtin_refused(self):
        raw=b'__import__ = other\n__import__("owned")\n';spec,physical,data=self.fixture(raw)
        spec['decisions']=[dict(module='owned',source_sha256=hashlib.sha256(raw).hexdigest(),line=2,column=0,
            kind='dynamic-import',action='include',targets=['owned'],rationale='shadowed builtin adversary',effect_ids=[])]
        result=self.build(spec,physical,data)
        self.assertEqual(result['status'],'INCOMPLETE_REFUSED');self.assertIn('unresolved-call-target',[r['kind'] for r in result['refusals']])
    def test_published_full_descriptor_consumed_by_l_plan_gate(self):
        from .compiler import publish_plan
        from ..lhost1.authority import validate_plan_acceptance,evidence_ref
        from ..l1.protocol import SAFETY
        from ..v1.records import validate_file_descriptor
        spec,physical,data=self.fixture();saved={}
        class Reader:
            def read_small(self,path,pin):
                raw=data[path]
                if pin!={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}:raise Refusal('pin mismatch')
                return raw
        class Outputs:
            def write(self,name,raw):
                row=retained('D:/fixture/'+name,raw)
                descriptor=validate_file_descriptor(dict(schema='cho51_lv_file_descriptor_v1',path=row['path'],
                    bytes=row['bytes'],sha256=row['sha256'],native_identity=row['native_identity'],
                    file_type='regular',reparse_point=False,link_count=1))
                saved[name]=descriptor
                return descriptor
        result=publish_plan(Reader(),spec,physical,Outputs(),lambda:True)
        plan=evidence_ref(result['plan_ref'],'plan');derivation=evidence_ref(saved['l-plan-derivation-index.json'],'derivation')
        when='2026-10-31T00:00:00Z';safe=dict(zip(SAFETY,[False]*5+[0,0]))
        request=dict(plan=plan,created_utc=when)
        acceptance=dict(schema='cho51_l_complete_plan_acceptance_v1',author='project_root',status='ACCEPTED_COMPLETE_L_PLAN',created_utc=when,
            plan=plan,derivation=derivation,review=evidence_ref(saved['l-static-plan.json'],'fixture_review'),safety=safe)
        review=dict(schema='cho51_l_complete_plan_review_v1',status='ACCEPTED_COMPLETE_L_PLAN_SOURCE',reviewer='independent',authors=['project_root'],
            created_utc=when,plan=plan,derivation=derivation,findings=[],checks=['supplied producer/consumer seam'],limitations=['no filesystem'],safety=safe)
        validate_plan_acceptance(request,acceptance,review,result)
        self.assertEqual(result['plan_ref']['schema'],'cho51_lv_file_descriptor_v1')
        for key,value in (('link_count',2),('reparse_point',True),('file_type','directory'),('unknown',True)):
            bad=copy.deepcopy(result);bad['plan_ref'][key]=value
            with self.assertRaises(Refusal):validate_plan_acceptance(request,acceptance,review,bad)
