"""Unexecuted supplied prior-debt reconciliation scenarios."""
import unittest
from dataclasses import FrozenInstanceError
from ..hb1 import common as c
from . import reconciliation as rec
from .test_context import OP, OP2, args, cohort, descriptor, extra, pin, raw, report

class ReconciliationTests(unittest.TestCase):
    def run_pair(self, before, after, prior_report=None, current_report=None):
        q=cohort(); pd=raw(before); cd=raw(after)
        return rec.reconcile_prior(q,pd,cd,raw(report(before,OP) if prior_report is None else prior_report),raw(report(after,OP2) if current_report is None else current_report),pin(q),pin(pd),pin(cd),OP,OP2)
    def test_noop_preserves_all(self): self.assertEqual(len(self.run_pair(descriptor(),descriptor()).preserved),876)
    def test_noop_no_additions(self): self.assertEqual(self.run_pair(descriptor(),descriptor()).additions,())
    def test_new_module_addition(self):
        self.assertEqual(len(self.run_pair(descriptor(),descriptor(extra())).additions),1)
        old=descriptor(extra())
        other=extra('tools.local_validation.cm6_extra.test_sample.Sample.test_second')
        new=descriptor(extra()+other)
        prior_report=report(old,OP); current_report=report(new,OP2)
        with self.assertRaises(c.Refusal): self.run_pair(old,new,prior_report,current_report)
    def test_added_debt_held(self): self.assertEqual(self.run_pair(descriptor(),descriptor(extra())).additions[0][1:3],('HELD','NEW_TEST_UNQUALIFIED'))
    def test_preserved_held_count(self): self.assertEqual(len(self.run_pair(descriptor(),descriptor()).held),516)
    def test_current_held_count(self): self.assertEqual(len(self.run_pair(descriptor(),descriptor(extra())).held),517)
    def test_drop_prior_addition(self):
        with self.assertRaises(c.Refusal): self.run_pair(descriptor(extra()),descriptor())
    def test_prior_pin_change(self):
        old=descriptor(extra()); new=descriptor(extra())
        module=extra()[0][0].rsplit('.',2)[0]
        next(x for x in new['modules'] if x['module']==module)['sha256']='b'*64
        prior_report=report(old,OP); current_report=report(new,OP2)
        with self.assertRaises(c.Refusal): self.run_pair(old,new,prior_report,current_report)
    def test_prior_debt_mutation(self):
        old=descriptor(extra()); new=descriptor(extra()); next(x for x in new['tests'] if x['id']==extra()[0][0])['obligation']['kind']='BASELINE_HELD'
        with self.assertRaises(c.Refusal): self.run_pair(old,new)
    def test_prior_promotion(self):
        old=descriptor(extra()); new=descriptor(extra()); next(x for x in new['tests'] if x['id']==extra()[0][0])['schedule']='COHORT'
        with self.assertRaises(c.Refusal): self.run_pair(old,new)
    def test_prior_rename(self):
        with self.assertRaises(c.Refusal): self.run_pair(descriptor(extra()),descriptor(extra('tools.local_validation.cm6_extra.test_sample.Sample.test_renamed')))
    def test_prior_report_incomplete(self):
        d=descriptor(); r=report(d,OP); r['complete']=False
        with self.assertRaises(c.Refusal): self.run_pair(d,d,prior_report=r)
    def test_current_report_incomplete(self):
        d=descriptor(); r=report(d,OP2); r['complete']=False
        with self.assertRaises(c.Refusal): self.run_pair(d,d,current_report=r)
    def test_contexts_separate(self):
        f=self.run_pair(descriptor(),descriptor()); self.assertNotEqual(f.prior_context,f.current_context)
    def test_prior_collection_pin(self):
        d=descriptor(); self.assertEqual(self.run_pair(d,d).prior_collection_pin,pin(raw(report(d,OP))))
    def test_current_collection_pin(self):
        d=descriptor(); self.assertEqual(self.run_pair(d,d).current_collection_pin,pin(raw(report(d,OP2))))
    def test_descriptor_pins(self):
        d=descriptor(); f=self.run_pair(d,d); self.assertEqual(f.prior_descriptor_pin,pin(raw(d)))
    def test_immutable(self):
        f=self.run_pair(descriptor(),descriptor())
        with self.assertRaises(FrozenInstanceError): f.held=()
    def test_unauthenticated(self):
        f=self.run_pair(descriptor(),descriptor())
        self.assertFalse(f.authenticated or f.debt_discharged)
    def test_execution_unaccepted(self):
        f=self.run_pair(descriptor(),descriptor())
        self.assertFalse(f.execution_accepted)
        self.assertTrue(f.independent_adoption_required)
