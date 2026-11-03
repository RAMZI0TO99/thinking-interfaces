"""Source-only adversarial supplied callback cases; execution is unadmitted."""
import hashlib
import unittest
from dataclasses import FrozenInstanceError

from ..hb1 import common as c
from . import registry
from .callbacks import CallbackModel

OP = '12345678-1234-1234-1234-123456789abc'
CODES = ((0, 1), (1, 2))


def model(**kwargs):
    return CallbackModel(OP, codes=CODES, check=lambda: True, **kwargs)


def good_case(m, case):
    m.start(case)
    m.cleanup_done(case)
    m.duration(case, 0)
    m.outcome(case, 'PASS')
    m.stop(case)


def full(m):
    for case in registry.selected_ordinals():
        good_case(m, case)


class CM2CallbackTests(unittest.TestCase):
    def test_full_selected_lifecycle(self):
        m = model()
        full(m)
        self.assertFalse(m.facts().supplied_success)
        m.close_suite()
        facts = m.finish()
        self.assertTrue(facts.supplied_success)
        self.assertEqual(facts.records, 746)
        self.assertFalse(facts.authenticated)

    def test_start_order_and_duplicates(self):
        order = registry.selected_ordinals()
        for bad in (True, -1, 764, order[1]):
            m = model()
            with self.assertRaises(c.Refusal):
                m.start(bad)
            self.assertTrue(m.facts().refused)
        m = model()
        m.start(order[0])
        with self.assertRaises(c.Refusal):
            m.start(order[0])

    def test_pass_requires_cleanup(self):
        m = model()
        case = registry.selected_ordinals()[0]
        m.start(case)
        with self.assertRaises(c.Refusal):
            m.outcome(case, 'PASS')
        self.assertEqual(m.facts().passed, 0)

    def test_end_requires_outcome(self):
        for cleaned in (False, True):
            m = model()
            case = registry.selected_ordinals()[0]
            m.start(case)
            if cleaned:
                m.cleanup_done(case)
            with self.assertRaises(c.Refusal):
                m.stop(case)
            self.assertEqual(m.facts().ended, 0)

    def test_subtest_parent_and_count(self):
        case = registry.selected_ordinals()[0]
        m = model()
        m.start(case)
        m.subtest(case, 1)
        m.subtest(case, 2)
        m.cleanup_done(case)
        m.outcome(case, 'PASS')
        m.stop(case)
        self.assertIn(b'"count":2', m.raw_bytes())
        for parent, sub, event in ((case, 2, 'SUBPASS'), (case+1, 1, 'SUBPASS'),
                                   (case, True, 'SUBPASS'), (case, 1, 'NESTED')):
            m = model()
            m.start(case)
            with self.assertRaises(c.Refusal):
                m.subtest(parent, sub, event)

    def test_failfast_and_cleanup_errors(self):
        order = registry.selected_ordinals()
        m = model()
        m.start(order[0])
        m.subtest(order[0], 1, 'SUBFAIL', 'ASSERT', ((0, 1),))
        m.outcome(order[0], 'ERROR', 'EXCEPTION', ((1, 2),))
        m.outcome(order[0], 'ERROR', 'EXCEPTION', ((0, 1),))
        m.cleanup_done(order[0])
        m.stop(order[0])
        self.assertFalse(m.facts().refused)
        self.assertTrue(m.facts().negative)
        with self.assertRaises(c.Refusal):
            m.start(order[1])
        m = model()
        m.start(order[0])
        m.outcome(order[0], 'SKIP')
        m.outcome(order[0], 'ERROR', 'EXCEPTION', ((0, 1),))
        m.outcome(order[0], 'ERROR', 'EXCEPTION', ((1, 2),))
        m.cleanup_done(order[0])
        m.duration(order[0], 0)
        m.stop(order[0])
        self.assertFalse(m.facts().refused)
        for cleanup_events in (('FAIL',), ('FAIL', 'ERROR', 'FAIL', 'ERROR')):
            m = model()
            m.start(order[0])
            m.outcome(order[0], 'SKIP')
            for event in cleanup_events:
                kind = 'ASSERT' if event == 'FAIL' else 'EXCEPTION'
                m.outcome(order[0], event, kind, ((0, 1),))
            m.cleanup_done(order[0])
            m.stop(order[0])
            self.assertFalse(m.facts().refused)
            self.assertTrue(m.facts().negative)
            self.assertEqual(m.raw_bytes().count(b'"event":"FAIL"'), cleanup_events.count('FAIL'))
            with self.assertRaises(c.Refusal):
                m.start(order[1])
        for event in ('SKIP', 'XFAIL', 'XPASS'):
            m = model()
            m.start(order[0])
            m.outcome(order[0], 'FAIL', 'ASSERT', ((0, 1),))
            with self.assertRaises(c.Refusal):
                m.outcome(order[0], event)

    def test_fixture_failure_after_passes(self):
        expected = registry.expected_ids()
        order = registry.selected_ordinals()
        owner = expected[order[0]].rsplit('.', 1)[0]
        affected = tuple(i for i in order if expected[i].rsplit('.', 1)[0] == owner)
        m = model(fixtures=((0, owner, 'teardown', affected),))
        full(m)
        m.fixture(0, 'EXCEPTION', ((0, 1),))
        m.close_suite()
        self.assertFalse(m.finish().supplied_success)
        self.assertEqual(m.facts().passed, 248)
        m = model(fixtures=((0, owner, 'setup', affected),
                            (1, owner, 'cleanup', affected),
                            (2, owner, 'cleanup', affected)))
        m.fixture(0, 'NONE')
        m.fixture(1, 'EXCEPTION', ((0, 1),))
        m.fixture(2, 'EXCEPTION', ((1, 2),))
        m.close_suite()
        self.assertFalse(m.finish().supplied_success)
        m = model(fixtures=((0, owner, 'setup', affected),))
        m.fixture(0, 'NONE')
        with self.assertRaises(c.Refusal):
            m.fixture(0, 'NONE')

    def test_trace_owner_and_location(self):
        case = registry.selected_ordinals()[0]
        m = model()
        m.start(case)
        m.outcome(case, 'FAIL', 'ASSERT', ((1, 2), (0, 1)))
        raw = m.raw_bytes()
        self.assertIn(b'"code":1', raw)
        self.assertEqual(raw.count(b'"event":"TRACE"'), 2)
        self.assertEqual(raw.count(('"case":%d' % case).encode('ascii')), 4)
        m = model()
        m.start(case)
        with self.assertRaises(c.Refusal):
            m.outcome(case, 'FAIL', 'ASSERT', ((1, 3),))
        self.assertEqual(m.facts().records, 2)

    def test_trace_bounds_and_exact_types(self):
        case = registry.selected_ordinals()[0]
        for trace in ([], ((True, 1),), ((0, True),), ((0, 1),)*129, ()):
            m = model()
            m.start(case)
            with self.assertRaises(c.Refusal):
                m.outcome(case, 'ERROR', 'EXCEPTION', trace)
        m = model()
        m.start(case)
        m.outcome(case, 'ERROR', 'EXCEPTION', ((0, 1),)*128)
        self.assertEqual(m.facts().records, 131)
        m = model()
        m.start(case)
        prefix = m.raw_bytes()
        with self.assertRaises(c.Refusal):
            m.outcome(case, 'ERROR', 'UNSUPPORTED', ())
        self.assertTrue(m.facts().refused)
        self.assertEqual(m.raw_bytes(), prefix)

    def test_skip_xfail_xpass_refuse_success(self):
        case = registry.selected_ordinals()[0]
        for event, kind, trace in (('SKIP','NONE',()), ('XPASS','NONE',()),
                                   ('XFAIL','ASSERT',((0, 1),))):
            m = model()
            m.start(case)
            if event != 'SKIP':
                m.cleanup_done(case)
            m.outcome(case, event, kind, trace)
            if event == 'SKIP':
                m.cleanup_done(case)
            m.stop(case)
            m.close_suite()
            self.assertFalse(m.finish().supplied_success)
            self.assertFalse(m.facts().refused)
        m = model()
        m.start(case)
        m.outcome(case, 'SKIP')
        with self.assertRaises(c.Refusal):
            m.outcome(case, 'SKIP')
        m = model()
        good_case(m, case)
        with self.assertRaises(c.Refusal):
            m.outcome(case, 'ERROR', 'EXCEPTION', ((0, 1),))

    def test_duration_never_formats(self):
        class Poison:
            def __str__(self):
                raise AssertionError('formatted')
            def __repr__(self):
                raise AssertionError('formatted')
        case = registry.selected_ordinals()[0]
        for value in (Poison(), True, 1.0, -1, 2**63):
            m = model()
            m.start(case)
            m.cleanup_done(case)
            with self.assertRaises(c.Refusal):
                m.duration(case, value)
        m = model()
        m.start(case)
        m.outcome(case, 'SKIP')
        m.cleanup_done(case)
        m.duration(case, 0)
        with self.assertRaises(c.Refusal):
            m.duration(case, 0)
        for event in ('XFAIL', 'XPASS'):
            m = model()
            m.start(case)
            m.cleanup_done(case)
            if event == 'XFAIL':
                m.outcome(case, event, 'ASSERT', ((0, 1),))
            else:
                m.outcome(case, event)
            with self.assertRaises(c.Refusal):
                m.duration(case, 0)

    def test_sticky_reentrant_refusal(self):
        holder = []
        armed = [False]
        def check():
            if armed[0]:
                try:
                    holder[0].start(registry.selected_ordinals()[0])
                except c.Refusal:
                    pass
            return True
        m = CallbackModel(OP, check=check)
        holder.append(m)
        armed[0] = True
        prefix = m.raw_bytes()
        with self.assertRaises(c.Refusal):
            m.start(registry.selected_ordinals()[0])
        self.assertTrue(m.facts().refused)
        self.assertEqual(m.raw_bytes(), prefix)
        with self.assertRaises(c.Refusal):
            m.close_suite()

    def test_event_caps_and_prefix(self):
        m = model()
        case = registry.selected_ordinals()[0]
        m.start(case)
        for sub in range(1, 4094):
            m.subtest(case, sub)
        self.assertEqual(m.facts().records, 4095)
        prefix = m.raw_bytes()
        with self.assertRaises(c.Refusal):
            m.subtest(case, 4094)
        self.assertEqual(m.raw_bytes(), prefix)
        self.assertLessEqual(len(prefix), 2097152)
        self.assertTrue(all(len(line)+1 <= 512 for line in prefix.splitlines()))

    def test_suite_and_final_gates(self):
        for action in ('close_suite', 'finish'):
            m = model()
            with self.assertRaises(c.Refusal):
                getattr(m, action)()
        m = model()
        full(m)
        m.close_suite()
        m.finish()
        prefix = m.raw_bytes()
        with self.assertRaises(c.Refusal):
            m.finish()
        self.assertEqual(m.raw_bytes(), prefix)
        self.assertFalse(m.facts().supplied_success)

    def test_frozen_facts_and_raw_digest(self):
        m = model()
        snapshot = m.facts()
        with self.assertRaises(FrozenInstanceError):
            snapshot.records = 0
        self.assertEqual(snapshot.whole_sha256, hashlib.sha256(m.raw_bytes()).hexdigest())
        self.assertIs(type(m.raw_bytes()), bytes)
        self.assertEqual(len(snapshot.not_started), 248)
        self.assertFalse(snapshot.execution_accepted)

    def test_operational_dispatch_refuses(self):
        m = model()
        with self.assertRaises(c.Refusal):
            m.dispatch()
        self.assertFalse(m.facts().execution_accepted)
