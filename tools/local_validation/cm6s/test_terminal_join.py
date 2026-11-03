import json
import unittest
from ..hb1.common import Refusal
from . import fixtures as f
from .join import join_supplied, dispatch
from .terminal import parse_terminal
from .context import parse_expected_context_s

class TerminalJoinTests(unittest.TestCase):
    def test_valid_negative_join(self):
        x=join_supplied(*f.bundle(True)); self.assertEqual(x.disposition,'SUPPLIED_NEGATIVE_SUPPLEMENT'); self.assertFalse(x.authenticated or x.execution_accepted or x.debt_discharged)
    def test_valid_pass_join(self): self.assertEqual(join_supplied(*f.bundle()).disposition,'SUPPLIED_SUPPLEMENT_CONSISTENT')
    def test_wrong_join_pin(self):
        a=list(f.bundle(True)); j=json.loads(a[0]); j['events']['sha256']='0'*64; a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)
    def test_wrong_retained_pin(self):
        a=list(f.bundle(True)); v=json.loads(a[8]); v['inputs']['tables']['sha256']='0'*64; a[8]=f.wire(v); j=json.loads(a[0]); j['terminal']=f.pinobj(a[8]); a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)
    def test_terminal_unsettled(self):
        a=list(f.bundle(True)); v=json.loads(a[8]); v['settled']-=1; a[8]=f.wire(v); j=json.loads(a[0]); j['terminal']=f.pinobj(a[8]); a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)
    def test_terminal_detachment(self):
        a=list(f.bundle(True)); v=json.loads(a[8]); v['producer_detached']=False; a[8]=f.wire(v); j=json.loads(a[0]); j['terminal']=f.pinobj(a[8]); a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)
    def test_extra_join_field(self):
        a=list(f.bundle(True)); j=json.loads(a[0]); j['extra']=0; a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)
    def test_dispatch_refused(self):
        with self.assertRaises(Refusal): dispatch()

    def test_valid_changed_table_rejected_by_terminal_join(self):
        a=list(f.bundle(True)); t=json.loads(a[6]); t['codes'].append([2,20]); a[6]=f.wire(t); j=json.loads(a[0]); j['tables']=f.pinobj(a[6]); a[0]=f.wire(j)
        with self.assertRaises(Refusal): join_supplied(*a)

    def test_pass_events_refused_terminal_is_negative(self):
        q,s,d,e,c,t,qp,sp,dp,ep,op=f.inputs(); m=f.ProducerModel(q,s,d,e,c,t,qp,sp,dp,ep,op); f.passing(m); f.finish(m)
        with self.assertRaises(Refusal): m.apply(('BEGIN',))
        seal=m.seal(); events=seal['raw']; terminal=seal['terminal']
        context=parse_expected_context_s(q,s,d,e,qp,sp,dp,ep,op).context
        join=f.wire(dict(schema='cho51_cm6s_supplied_join_v1',operation=op,context=context,anchor=f.pinobj(q),supplement=f.pinobj(s),descriptor=f.pinobj(d),expected=f.pinobj(e),collection=f.pinobj(c),tables=f.pinobj(t),events=f.pinobj(events),terminal=f.pinobj(terminal)))
        x=join_supplied(join,q,s,d,e,c,t,events,terminal,qp,sp,dp,ep,op); self.assertFalse(x.events.negative); self.assertTrue(x.terminal.refused); self.assertEqual(x.disposition,'SUPPLIED_NEGATIVE_SUPPLEMENT')
