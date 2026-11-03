import unittest
import json
from ..hb1.common import Refusal
from .join import join_supplied, dispatch
from .fixtures import bundle, wire, pinobj, model, passing, finish

class JoinTests(unittest.TestCase):
    def check(self,b): return join_supplied(*b)
    def change(self,key,value):
        b=list(bundle(True)); v=json.loads(b[0]); v[key]=value; b[0]=wire(v); return b
    def test_complete(self):
        b=list(bundle()); self.assertEqual(self.check(b).disposition,'SUPPLIED_COHORT_CONSISTENT')
        terminal=json.loads(b[6]); terminal.update(attempts=terminal['attempts']+1,settled=terminal['settled']+1,post_footer_attempts=1,first_refusal=terminal['attempts']+1,refused=True)
        b[6]=wire(terminal); join=json.loads(b[0]); join['terminal']=pinobj(b[6]); b[0]=wire(join)
        self.assertEqual(self.check(b).disposition,'SUPPLIED_NEGATIVE_COHORT')
    def test_negative(self): self.assertEqual(self.check(bundle(True)).disposition,'SUPPLIED_NEGATIVE_COHORT')
    def test_held_debt(self): self.assertEqual(len(self.check(bundle(True)).collection.held),656)
    def test_negative_suffix_distinct(self):
        f=self.check(bundle(True)); self.assertEqual((len(f.events.not_started),len(f.collection.held)),(359,656))
    def test_context(self):
        with self.assertRaises(Refusal): self.check(self.change('context','0'*64))
    def test_schema(self):
        with self.assertRaises(Refusal): self.check(self.change('schema','old'))
    def test_operation(self):
        with self.assertRaises(Refusal): self.check(self.change('operation','bad'))
    def test_cohort_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('cohort',{'bytes':1,'sha256':'0'*64}))
    def test_descriptor_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('descriptor',{'bytes':1,'sha256':'0'*64}))
    def test_collection_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('collection',{'bytes':1,'sha256':'0'*64}))
    def test_table_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('tables',{'bytes':1,'sha256':'0'*64}))
    def test_events_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('events',{'bytes':1,'sha256':'0'*64}))
    def test_terminal_pin(self):
        with self.assertRaises(Refusal): self.check(self.change('terminal',{'bytes':1,'sha256':'0'*64}))
    def test_extra_field(self):
        with self.assertRaises(Refusal): self.check(self.change('extra',1))
    def test_noncanonical(self):
        b=list(bundle(True)); b[0]+=b' '
        with self.assertRaises(Refusal): self.check(b)
    def test_table_substitution(self):
        b=list(bundle(True)); table=json.loads(b[4]); table['codes'].append([2,20]); b[4]=wire(table)
        join=json.loads(b[0]); join['tables']=pinobj(b[4]); b[0]=wire(join)
        with self.assertRaises(Refusal): self.check(b)
    def test_terminal_substitution(self):
        b=list(bundle(True)); terminal=json.loads(b[6]); terminal['events']['sha256']='0'*64
        b[6]=wire(terminal); join=json.loads(b[0]); join['terminal']=pinobj(b[6]); b[0]=wire(join)
        with self.assertRaises(Refusal): self.check(b)
    def test_incomplete_event(self):
        b=list(bundle(True)); b[5]=b[5][:-1]
        with self.assertRaises(Refusal): self.check(b)
    def test_unauthenticated(self): self.assertFalse(self.check(bundle(True)).execution_accepted)
    def test_runtime_refusal(self):
        with self.assertRaises(Refusal): dispatch()



