"""Unexecuted supplied fixtures; synthetic set hashes carry no authority."""
import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError
from ..cm5 import registry as base
from ..hb1 import common as c
from ..cm1.collection import LOADER
from . import context

OP = '11111111-1111-1111-1111-111111111111'
OP2 = '22222222-2222-2222-2222-222222222222'

def raw(value): return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')
def pin(value): return (len(value), hashlib.sha256(value).hexdigest())
def sha(value): return hashlib.sha256(value).hexdigest()
def cohort():
    return raw(dict(schema='cho51_cm6_qualification_cohort_v1', name='CM6-Q360-20261103', count=360, ids=list(base.selected_ids()), ids_sha256=context.Q_DIGEST))
def descriptor(extra=()):
    ids = sorted(base.expected_ids() + tuple(n for n, _, _ in extra)); selected = set(base.selected_ids()); baseline = set(base.expected_ids())
    mods = list(base.expected_modules()) + [(n.rsplit('.', 2)[0], size, h) for n, size, h in extra]
    mods = sorted(set(mods))
    rows = []
    for n in ids:
        debt = None if n in selected else dict(kind='BASELINE_HELD' if n in baseline else 'NEW_TEST_UNQUALIFIED', id_sha256=sha(n.encode('ascii')))
        rows.append(dict(id=n, schedule='COHORT' if n in selected else 'HELD', obligation=debt))
    return dict(schema='cho51_cm6_expected_census_v1', cohort=dict(name='CM6-Q360-20261103', count=360, ids_sha256=context.Q_DIGEST, bytes=context.Q_PIN[0], sha256=context.Q_PIN[1]), census=dict(count=len(ids), module_count=len(mods), ids_sha256=sha(('\n'.join(ids)+'\n').encode('ascii'))), modules=[dict(module=n, bytes=s, sha256=h) for n,s,h in mods], tests=rows, source_set='1'*64, runtime_set='2'*64, producer_set='3'*64)
def args(d, operation=OP):
    q = cohort(); dr = raw(d); return q, dr, context.Q_PIN, pin(dr), operation
def report(d, operation=OP):
    q, dr, qp, dp, op = args(d, operation); f = context.parse_expected_context(q, dr, qp, dp, op)
    modules = [dict(module=n, bytes=s, sha256=h, loader=LOADER, load_tests=False, partial=False) for n,s,h in f.modules]
    tests = []
    for name in f.ids:
        m, cl, method = name.rsplit('.', 2)
        tests.append(dict(id=name, module=m, class_name=cl, method_name=method, source_module=m, source_qualname=cl+'.'+method, skipped=False, deselected=False, expected_failure=False, xfail=False))
    return dict(schema='cho51_cm6_supplied_collection_v1', operation=op, context=f.context, complete=True, modules=modules, tests=tests)
def extra(name='tools.local_validation.cm6_extra.test_sample.Sample.test_added'):
    return ((name, 25, 'a'*64),)

class ContextTests(unittest.TestCase):
    def check(self, d): return context.parse_expected_context(*args(d))
    def denied(self, d):
        with self.assertRaises(c.Refusal): self.check(d)
    def test_canonical_anchor_pin(self): self.assertEqual(pin(cohort()), context.Q_PIN)
    def test_baseline_counts(self): self.assertEqual((len(self.check(descriptor()).ids), len(self.check(descriptor()).modules)), (876, 38))
    def test_held_baseline(self): self.assertEqual(sum(x[2] == 'BASELINE_HELD' for x in self.check(descriptor()).obligations), 516)
    def test_new_held(self):
        name = extra()[0][0]
        row = next(x for x in self.check(descriptor(extra())).obligations if x[0] == name)
        self.assertEqual(row, (name, 'HELD', 'NEW_TEST_UNQUALIFIED', sha(name.encode('ascii'))))
    def test_immutable_facts(self):
        with self.assertRaises(FrozenInstanceError): self.check(descriptor()).context = 'x'
    def test_current_registry_census(self):
        from . import registry
        self.assertEqual((len(registry.expected_ids()), len(registry.expected_modules()), len(registry.selected_ids())), (936, 41, 360))
        self.assertEqual(len(set(registry.expected_ids()) - set(registry.selected_ids())), 576)
        pins = {n: (s, h) for n, s, h in registry.NEW_MODULE_PINS}
        d = descriptor(tuple((n, *pins[n.rsplit('.', 2)[0]]) for n in registry.NEW_IDS))
        facts = self.check(d)
        self.assertEqual(facts.ids, registry.expected_ids())
        self.assertEqual(facts.modules, registry.expected_modules())
        self.assertEqual(facts.census_digest, registry.FULL_DIGEST)
    def test_bad_external_q_pin(self):
        q,d,_,dp,op = args(descriptor())
        with self.assertRaises(c.Refusal): context.parse_expected_context(q,d,(1,'0'*64),dp,op)
    def test_bad_external_d_pin(self):
        q,d,qp,_,op = args(descriptor())
        with self.assertRaises(c.Refusal): context.parse_expected_context(q,d,qp,(1,'0'*64),op)
    def test_noncanonical(self):
        q,d,qp,_,op = args(descriptor())
        for bad in (d[:-1] + b' \n', b'{"schema":"duplicate",' + d[1:], b'[' * 25 + b'0' + b']' * 25, b' ' * (context.CAP + 1)):
            with self.assertRaises(c.Refusal): context.parse_expected_context(q,bad,qp,pin(bad),op)
        with self.assertRaises(c.Refusal): context.parse_expected_context(q,bytearray(d),qp,pin(d),op)
    def test_unknown_field(self):
        d=descriptor(); d['unexpected']=1; self.denied(d)
    def test_bool_count(self):
        d=descriptor(); d['census']['count']=True; self.denied(d)
    def test_count_bound(self):
        d=descriptor(); d['census']['count']=4097; self.denied(d)
    def test_missing_baseline(self):
        d=descriptor(extra()); d['tests']=[x for x in d['tests'] if x['id'] != base.expected_ids()[0]]
        d['census']['count']=len(d['tests'])
        d['census']['ids_sha256']=sha(('\n'.join(x['id'] for x in d['tests'])+'\n').encode('ascii'))
        self.denied(d)
    def test_baseline_module_pin(self):
        d=descriptor(); d['modules'][0]['sha256']='0'*64; self.denied(d)
    def test_held_schedule(self):
        d=descriptor(); next(x for x in d['tests'] if x['schedule']=='HELD')['schedule']='COHORT'; self.denied(d)
    def test_held_digest(self):
        d=descriptor(); next(x for x in d['tests'] if x['schedule']=='HELD')['obligation']['id_sha256']='0'*64; self.denied(d)
    def test_cohort_obligation(self):
        d=descriptor(); next(x for x in d['tests'] if x['schedule']=='COHORT')['obligation']={}; self.denied(d)
    def test_bad_set_hash(self):
        d=descriptor(); d['source_set']='fixture'; self.denied(d)
    def test_operation_binding(self):
        d=descriptor(); f=self.check(d)
        expected=dict(domain='cho51_cm6_context_v1', operation=OP, cohort=context.Q_DIGEST, census=d['census']['ids_sha256'], descriptor=dict(bytes=len(raw(d)), sha256=sha(raw(d))))
        self.assertEqual(f.context, sha(raw(expected)))
        self.assertNotEqual(f.context, context.parse_expected_context(*args(d, OP2)).context)
    def test_dispatch_refuses(self):
        with self.assertRaises(c.Refusal): context.runtime_dispatch()

