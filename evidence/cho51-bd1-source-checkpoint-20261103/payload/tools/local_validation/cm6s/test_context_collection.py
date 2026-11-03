import hashlib
import json
import unittest
from ..hb1.common import Refusal
from ..cm6.context import parse_expected_context
from . import fixtures as f
from .context import parse_expected_context_s, dispatch
from .collection import verify_collection_s

class ContextCollectionTests(unittest.TestCase):
    def setUp(self): self.a = f.inputs()
    def context(self):
        q,s,d,e,c,t,qp,sp,dp,ep,op=self.a
        return parse_expected_context_s(q,s,d,e,qp,sp,dp,ep,op)
    def collection(self):
        q,s,d,e,c,t,qp,sp,dp,ep,op=self.a
        return verify_collection_s(c,q,s,d,e,qp,sp,dp,ep,op)
    def test_valid_s_is_held_and_disjoint(self):
        x=self.context(); self.assertEqual(len(x.supplement),140); self.assertFalse(set(x.supplement)&set(x.baseline.cohort)); self.assertTrue(set(x.supplement).issubset({r[0] for r in x.baseline.obligations if r[1]=='HELD'}))
    def test_context_domains_differ(self): self.assertNotEqual(self.context().context,self.context().baseline.context)
    def test_flags(self):
        x=self.collection(); self.assertFalse(x.authenticated or x.execution_accepted or x.debt_discharged)
    def test_mapping(self):
        x=self.collection(); self.assertEqual(tuple(x.baseline.ids[i] for i in x.s_to_c),x.supplement)
    def test_s_pin_refuses(self):
        self.a=list(self.a); self.a[7]=(1,'0'*64)
        with self.assertRaises(Refusal): self.context()
    def test_e_pin_refuses(self):
        self.a=list(self.a); self.a[9]=(1,'0'*64)
        with self.assertRaises(Refusal): self.context()
    def test_e_manifest_reference_refuses(self):
        self.a=list(self.a); e=json.loads(self.a[3]); e['source_set']='d'*64; self.a[3]=f.wire(e); self.a[9]=f.pin(self.a[3])
        with self.assertRaises(Refusal): self.context()
    def test_collection_held_flag_refuses(self):
        self.a=list(self.a); c=json.loads(self.a[4]); c['tests'][-1]['skipped']=True; self.a[4]=f.wire(c)
        with self.assertRaises(Refusal): self.collection()
    def test_collection_missing_row_refuses(self):
        self.a=list(self.a); c=json.loads(self.a[4]); c['tests'].pop(); self.a[4]=f.wire(c)
        with self.assertRaises(Refusal): self.collection()
    def test_dispatch_refused(self):
        with self.assertRaises(Refusal): dispatch()

    def test_missing_successor_identity_refused_after_repin(self):
        self.a=list(self.a); d=json.loads(self.a[2]); d['tests']=[r for r in d['tests'] if r['id'] != f.registry.NEW_IDS[0]]; ids=[r['id'] for r in d['tests']]; d['census']['count']=len(ids); d['census']['ids_sha256']=hashlib.sha256(('\n'.join(ids)+'\n').encode('ascii')).hexdigest(); self.a[2]=f.wire(d); self.a[8]=f.pin(self.a[2]); e=json.loads(self.a[3]); e['descriptor']=f.pinobj(self.a[2]); self.a[3]=f.wire(e); self.a[9]=f.pin(self.a[3])
        parse_expected_context(self.a[0],self.a[2],self.a[6],self.a[8],self.a[10])
        with self.assertRaises(Refusal): self.context()


    def test_successor_module_pin_after_repin(self):
        self.a=list(self.a); d=json.loads(self.a[2]); name=f.registry.NEW_MODULE_PINS[0][0]; row=next(r for r in d['modules'] if r['module']==name); row['sha256']='0'*64; self.a[2]=f.wire(d); self.a[8]=f.pin(self.a[2]); e=json.loads(self.a[3]); e['descriptor']=f.pinobj(self.a[2]); self.a[3]=f.wire(e); self.a[9]=f.pin(self.a[3])
        parse_expected_context(self.a[0],self.a[2],self.a[6],self.a[8],self.a[10])
        with self.assertRaises(Refusal): self.context()
    def test_e_wrong_descriptor_pin_after_repin(self):
        self.a=list(self.a); e=json.loads(self.a[3]); e['descriptor']['sha256']='0'*64; self.a[3]=f.wire(e); self.a[9]=f.pin(self.a[3])
        with self.assertRaises(Refusal): self.context()
    def test_facts_immutable(self):
        x=self.context()
        with self.assertRaises((AttributeError,TypeError)): x.context='0'*64
        self.assertFalse(x.authenticated or x.execution_accepted or x.debt_discharged)
