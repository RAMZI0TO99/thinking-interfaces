"""Unexecuted full collection and projection contract scenarios."""
import unittest
from dataclasses import FrozenInstanceError
from ..hb1 import common as c
from ..cm4 import registry as h
from . import collection
from .test_context import OP, args, descriptor, extra, raw, report

class CollectionTests(unittest.TestCase):
    def check(self, d, r): return collection.verify_collection(raw(r), *args(d))
    def denied(self, d, r):
        with self.assertRaises(c.Refusal): self.check(d, r)
    def test_baseline_full(self): self.assertEqual(len(self.check(descriptor(), report(descriptor())).ids), 876)
    def test_baseline_held(self): self.assertEqual(len(self.check(descriptor(), report(descriptor())).held), 516)
    def test_q_count(self): self.assertEqual(len(self.check(descriptor(), report(descriptor())).cohort), 360)
    def test_h_target_unchanged(self): self.assertEqual((len(h.expected_ids()), len(h.expected_modules()), len(h.selected_ids())), (836, 36, 320))
    def test_new_held(self):
        from . import registry
        pins = {n: (s, h) for n, s, h in registry.NEW_MODULE_PINS}
        d=descriptor(tuple((n, *pins[n.rsplit('.', 2)[0]]) for n in registry.NEW_IDS))
        f=self.check(d,report(d))
        self.assertEqual(f.ids, registry.expected_ids())
        self.assertEqual(len(f.held),576)
    def test_mapping(self):
        d=descriptor(extra('a.b.C.test_first')); f=self.check(d,report(d)); self.assertEqual(tuple(f.ids[i] for i in f.q_to_c),f.cohort)
    def test_facts_frozen(self):
        d=descriptor(); f=self.check(d,report(d))
        with self.assertRaises(FrozenInstanceError): f.context='x'
    def test_auth_flags(self):
        d=descriptor(); f=self.check(d,report(d))
        self.assertFalse(f.authenticated or f.execution_accepted or f.debt_discharged)
        self.assertTrue(f.independent_adoption_required)
    def test_complete_exact(self):
        d=descriptor(); r=report(d); r['complete']=1; self.denied(d,r)
    def test_wrong_context(self):
        d=descriptor(); r=report(d); r['context']='0'*64; self.denied(d,r)
    def test_wrong_operation(self):
        d=descriptor(); r=report(d); r['operation']='0'; self.denied(d,r)
    def test_missing_module(self):
        d=descriptor(); r=report(d); r['modules'].pop(); self.denied(d,r)
    def test_module_pin(self):
        d=descriptor(); r=report(d); r['modules'][0]['sha256']='0'*64; self.denied(d,r)
    def test_loader(self):
        d=descriptor(); r=report(d); r['modules'][0]['loader']='other'; self.denied(d,r)
    def test_partial(self):
        d=descriptor(); r=report(d); r['modules'][0]['partial']=True; self.denied(d,r)
    def test_load_tests(self):
        d=descriptor(); r=report(d); r['modules'][0]['load_tests']=True; self.denied(d,r)
    def test_missing_test(self):
        d=descriptor(); r=report(d); r['tests'].pop(); self.denied(d,r)
    def test_equal_count_swap(self):
        d=descriptor(); r=report(d); r['tests'][0],r['tests'][1]=r['tests'][1],r['tests'][0]; self.denied(d,r)
    def test_held_flag_before_projection(self):
        for flag in ('skipped','deselected','expected_failure','xfail'):
            d=descriptor(extra()); r=report(d)
            next(x for x in r['tests'] if x['id']==extra()[0][0])[flag]=True
            self.denied(d,r)
    def test_owner_substitution(self):
        d=descriptor(); r=report(d); r['tests'][0]['source_qualname']='Other.test_name'; self.denied(d,r)
