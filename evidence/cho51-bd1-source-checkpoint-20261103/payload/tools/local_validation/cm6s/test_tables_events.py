import json
import unittest
from ..hb1.common import Refusal
from . import fixtures as f
from .tables import parse_tables
from .events import verify_events

class TablesEventsTests(unittest.TestCase):
    def setUp(self): self.a=list(f.inputs())
    def tables(self):
        q,s,d,e,c,t,qp,sp,dp,ep,op=self.a
        return parse_tables(t,q,s,d,e,c,qp,sp,dp,ep,op)
    def test_valid_table(self): self.assertEqual(self.tables().codes,((1,10),))
    def test_old_schema_refused(self):
        t=json.loads(self.a[5]); t['schema']='cho51_cm6_supplied_tables_v1'; self.a[5]=f.wire(t)
        with self.assertRaises(Refusal): self.tables()
    def test_boolean_code_refused(self):
        t=json.loads(self.a[5]); t['codes']=[[True,10]]; self.a[5]=f.wire(t)
        with self.assertRaises(Refusal): self.tables()
    def test_fixture_uses_s_ordinals(self):
        t=json.loads(self.a[5]); owner=f.registry.supplement_ids()[0].rsplit('.',1)[0]; indices=[i for i,n in enumerate(f.registry.supplement_ids()) if n.rsplit('.',1)[0]==owner]; t['fixtures']=[dict(slot=0,owner=owner,phase='setup',affected=indices)]; self.a[5]=f.wire(t); self.assertEqual(self.tables().fixtures[0][3],tuple(indices))
    def test_fixture_wrong_position_refused(self):
        t=json.loads(self.a[5]); owner=f.registry.supplement_ids()[0].rsplit('.',1)[0]; t['fixtures']=[dict(slot=0,owner=owner,phase='setup',affected=[139])]; self.a[5]=f.wire(t)
        with self.assertRaises(Refusal): self.tables()
    def test_negative_events_suffix(self):
        m=f.model(); f.negative(m); q,s,d,e,c,t,qp,sp,dp,ep,op=self.a; x=verify_events(m.raw_prefix(),t,c,q,s,d,e,qp,sp,dp,ep,op); self.assertTrue(x.negative); self.assertEqual(x.not_started,tuple(range(1,140)))
    def test_truncated_events_refused(self):
        m=f.model(); f.negative(m); q,s,d,e,c,t,qp,sp,dp,ep,op=self.a
        with self.assertRaises(Refusal): verify_events(m.raw_prefix()[:-1],t,c,q,s,d,e,qp,sp,dp,ep,op)

    def verify(self, raw):
        q,s,d,e,c,t,qp,sp,dp,ep,op=self.a
        return verify_events(raw,t,c,q,s,d,e,qp,sp,dp,ep,op)
    def test_independent_pass_stream(self):
        x=self.verify(f.independent_events()); self.assertFalse(x.negative); self.assertEqual((x.started,x.passed,x.ended),(140,140,140))
    def test_independent_negative_stream(self):
        x=self.verify(f.independent_events(True)); self.assertEqual(x.not_started,tuple(range(1,140)))
    def test_q_header_refused_with_valid_footer(self):
        raw=f.mutate_event(f.independent_events(True),0,{'count':360})
        with self.assertRaises(Refusal): self.verify(raw)
    def test_q_ordinal_refused_with_valid_footer(self):
        raw=f.mutate_event(f.independent_events(True),2,{'case':140})
        with self.assertRaises(Refusal): self.verify(raw)
    def test_old_event_schema_refused_with_valid_footer(self):
        raw=f.mutate_event(f.independent_events(True),0,{'schema':'cho51_cm6_event_v1'})
        with self.assertRaises(Refusal): self.verify(raw)
