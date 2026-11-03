"""Unexecuted supplied-model cases; no runtime qualification."""
import hashlib
import json
import unittest
from ..hb1.common import Refusal
from . import protocol, refusal, registry

OP = '12345678-1234-1234-1234-123456789abc'
CHECK = lambda: True


def record(event, **changes):
    result = dict(schema='cho51_cm1_event_v1', seq=0, op=OP, roster=registry.roster_digest(CHECK), event=event, case=None, sub=None, fixture=None, kind='NONE', code=None, line=None, count=None, prefix=None)
    result.update(changes)
    return result


def stream(events):
    out = b''
    for i, item in enumerate([record('HEADER', count=216)] + events, 1):
        item = dict(item, seq=i)
        out += json.dumps(item, sort_keys=True, separators=(',', ':')).encode('ascii') + b'\n'
    footer = record('FOOTER', seq=len(events)+2, count=len(events)+1, prefix=hashlib.sha256(out).hexdigest())
    return out + json.dumps(footer, sort_keys=True, separators=(',', ':')).encode('ascii') + b'\n'


def ordinal():
    return registry.expected_ids().index(registry.selected_ids()[0])


def verify(events, **kw):
    return protocol.verify_events(stream(events), OP, check=CHECK, **kw)


class CM1ProtocolTests(unittest.TestCase):
    def test_bounded_record_grammar(self):
        raw = stream([])
        for bad in (raw[:-1], raw.replace(b'"seq":1', b'"seq":1.0', 1), raw.replace(b'"seq":1', b'"seq":1,"seq":1', 1), b'x' * 2097153):
            with self.subTest(size=len(bad)), self.assertRaises(Refusal):
                protocol.verify_events(bad, OP, check=CHECK)
        with self.assertRaises(Refusal):
            verify([record('TRACE', count=1, code=0, line=1)], codes=((0,1),))
        with self.assertRaises(Refusal): protocol.verify_events(b'\n' * 4097, OP, check=CHECK)
        with self.assertRaises(Refusal): protocol.verify_events(b'x' * 512 + b'\n', OP, check=CHECK)

    def test_capture_overflow_consumed(self):
        m = refusal.CaptureModel()
        with self.assertRaises(Refusal): m.append('stdout', b'x' * 1048577, check=CHECK)
        self.assertTrue(m.snapshot().consumed)
        with self.assertRaises(Refusal): m.append('stdout', b'', check=CHECK)
        m = refusal.CaptureModel()
        def nested():
            try: m.append('stderr', b'x', check=CHECK)
            except Refusal: pass
            return True
        with self.assertRaises(Refusal): m.append('stdout', b'x', check=nested)
        self.assertTrue(m.snapshot().consumed)

    def test_expected_failure_and_success_refuse(self):
        n = ordinal()
        for event, kind, count in (('XFAIL','EXCEPTION',1), ('XPASS','NONE',0), ('SKIP','NONE',0)):
            events = [record('CASE_START',case=n), record(event,case=n,kind=kind,count=count)]
            if count: events.append(record('TRACE',case=n,kind=kind,code=0,line=1,count=1))
            events.append(record('CASE_END',case=n,count=0))
            self.assertTrue(verify(events,codes=((0,1),)).negative)

    def test_failure_without_formatting(self):
        class Poison:
            def __str__(self): raise AssertionError('formatted')
            def __repr__(self): raise AssertionError('formatted')
        with self.assertRaises(Refusal): protocol.verify_events(Poison(), OP, check=CHECK)

    def test_final_verification_before_acceptance(self):
        with self.assertRaises(Refusal): refusal.supplied_gates(guard=True, final_verified=False, now=1, original_deadline=3, cleanup_deadline=2, check=CHECK)
        self.assertEqual(refusal.supplied_gates(guard=True, final_verified=True, now=1, original_deadline=3, cleanup_deadline=2, check=CHECK), ('SUPPLIED_MODEL_FACTS', False))

    def test_guard_mock_isolation(self):
        for guard in (1, None, False):
            with self.assertRaises(Refusal): refusal.supplied_gates(guard=guard, final_verified=True, now=1, original_deadline=3, cleanup_deadline=2, check=CHECK)
        with self.assertRaises(Refusal): protocol.verify_events(stream([]), OP, check=lambda: 1)
        binding = refusal.guard_binding(owner='host', clock='clock', patch_surface=('mock.time',), guard_surface=('native.clock',), check=CHECK)
        self.assertFalse(binding.authenticated)
        with self.assertRaises(Refusal): refusal.guard_binding(owner='host', clock='clock', patch_surface=('native.clock',), guard_surface=('native.clock',), check=CHECK)
        with self.assertRaises(Refusal): refusal.guard_binding(owner='same', clock='same', patch_surface=(), guard_surface=('native.clock',), check=CHECK)

    def test_header_and_operation_join(self):
        with self.assertRaises(Refusal): protocol.verify_events(stream([]), '00000000-0000-0000-0000-000000000000', check=CHECK)
        with self.assertRaises(Refusal): protocol.verify_events(stream([]), 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', check=CHECK)

    def test_immutable_parent_reservations(self):
        self.assertEqual(sum(r[1] for r in refusal.RESERVATIONS), 30)
        self.assertEqual(sum(r[2] for r in refusal.RESERVATIONS), 17711104)
        with self.assertRaises(TypeError): refusal.RESERVATIONS[0][1] = 0

    def test_ordinal_and_digest_join(self):
        with self.assertRaises(Refusal): verify([record('CASE_START',case=(ordinal()+1)%732)])
        raw = stream([]).replace(registry.roster_digest(CHECK).encode(), b'0'*64)
        with self.assertRaises(Refusal): protocol.verify_events(raw, OP, check=CHECK)

    def test_original_deadline_cleanup_min(self):
        for now in (2,3):
            with self.assertRaises(Refusal): refusal.supplied_gates(guard=True, final_verified=True, now=now, original_deadline=3, cleanup_deadline=2, check=CHECK)
        self.assertEqual(refusal.deadlines(100, 120, 10, 3), (147,125))
        with self.assertRaises(Refusal): refusal.deadlines(2**63-1, 1, 0, 0)
        with self.assertRaises(Refusal): refusal.deadlines(0, 0, 61, 0)

    def test_raw_stream_separation(self):
        m = refusal.CaptureModel()
        m.append('stdout', b'\xff\r\n', check=CHECK); m.append('stderr', b'\x00', check=CHECK)
        self.assertEqual((m.snapshot().stdout,m.snapshot().stderr),(b'\xff\r\n',b'\x00'))
        self.assertEqual(m.snapshot().chunks, (('stdout',b'\xff\r\n'),('stderr',b'\x00')))

    def test_start_complete_conservation(self):
        n = ordinal(); start = record('CASE_START',case=n); end = record('CASE_END',case=n,count=0); passed = record('PASS',case=n)
        for events in ([start,end], [start,passed,passed,end], [start,start], [start,passed,end,end], [start,record('ERROR',case=n,kind='UNSUPPORTED',count=0),passed,end], [start,record('SUBFAIL',case=n,sub=1,kind='UNSUPPORTED',count=0),passed,end], [start,record('ERROR',case=n,kind='UNSUPPORTED',count=0),end,start]):
            with self.subTest(events=events), self.assertRaises(Refusal): verify(events)
        facts = verify([start,passed,end]); self.assertEqual((facts.started,facts.passed,facts.ended),(1,1,1)); self.assertFalse(facts.authenticated)
        self.assertFalse(facts.supplied_success)
        events = []
        for name in registry.selected_ids():
            i = registry.expected_ids().index(name)
            events.extend((record('CASE_START',case=i), record('PASS',case=i), record('CASE_END',case=i,count=0)))
        facts = verify(events)
        self.assertTrue(facts.supplied_success); self.assertFalse(facts.execution_accepted)
        with self.assertRaises(Refusal): verify([start,passed,record('ERROR',case=n,kind='UNSUPPORTED',count=0),end])
        with self.assertRaises(Refusal): verify([start,record('SKIP',case=n,count=0),record('SKIP',case=n,count=0),end])
        self.assertTrue(verify([start,record('FAIL',case=n,kind='UNSUPPORTED',count=0),record('FAIL',case=n,kind='UNSUPPORTED',count=0),end]).negative)

    def test_subtest_parent_accounting(self):
        n = ordinal(); start = record('CASE_START',case=n)
        facts = verify([start,record('SUBPASS',case=n,sub=1),record('PASS',case=n),record('CASE_END',case=n,count=1)])
        self.assertEqual(facts.passed,1)
        with self.assertRaises(Refusal): verify([start,record('SUBPASS',case=n,sub=2)])

    def test_suite_fixture_error_refuses(self):
        n=ordinal(); fixture=record('FIXTURE_ERROR',fixture=0,kind='NONE',count=0)
        owner=registry.expected_ids()[n].rsplit('.',1)[0]
        affected=tuple(i for i,name in enumerate(registry.expected_ids()) if name in registry.selected_ids() and name.startswith(owner+'.'))
        table=((0,owner,'setup',affected),)
        for events in ([fixture], [record('CASE_START',case=n),record('PASS',case=n),record('CASE_END',case=n,count=0),fixture,fixture]):
            facts=verify(events,fixtures=table); self.assertTrue(facts.negative); self.assertEqual(len(facts.not_started),216-facts.started)
        with self.assertRaises(Refusal): verify([fixture,record('CASE_START',case=n)],fixtures=table)

    def test_unavailable_host_never_authorizes(self):
        with self.assertRaises(Refusal): refusal.dispatch()
        with self.assertRaises(Refusal): refusal.dispatch(True, final_verified=True)

    def test_unknown_code_origin_refuses(self):
        n=ordinal(); start=record('CASE_START',case=n); error=record('ERROR',case=n,kind='EXCEPTION',count=1); trace=record('TRACE',case=n,kind='EXCEPTION',count=1,code=0,line=1); end=record('CASE_END',case=n,count=0)
        for events, codes in (([start,error,end],((0,1),)), ([start,error,trace,end],()), ([start,error,dict(trace,count=2),end],((0,1),)), ([start,error,dict(trace,case=n+1),end],((0,1),)), ([start,error,dict(trace,kind='ASSERT'),end],((0,1),)), ([start,error,trace,trace,end],((0,1),))):
            with self.assertRaises(Refusal): verify(events,codes=codes)
        self.assertTrue(verify([start,error,trace,end],codes=((0,1),)).negative)
