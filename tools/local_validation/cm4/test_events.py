"""Independent synthetic wire fixtures; source-only, no producer replay."""
import hashlib
import json
import unittest
from dataclasses import replace
from ..hb1.common import Refusal
from . import registry
from .events import verify_events, hash_bytes, dispatch

OP = '11111111-1111-1111-1111-111111111111'
CHECK = lambda: True
CODES = ((1, 10), (2, 20))


def _line(seq, event, **fields):
    row = dict(schema='cho51_cm4_event_v1', seq=seq, op=OP, roster=registry.FULL_DIGEST,
               event=event, case=None, sub=None, fixture=None, kind='NONE', code=None,
               line=None, count=None, prefix=None)
    row.update(fields)
    return (json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode('ascii')


def _report(body):
    events = [('HEADER', {'count': registry.SELECTED_COUNT}), ('SUITE_OPEN', {})] + body
    events += [('SUITE_CLOSE', {}), ('RESTORED', {}), ('INPUTS_VERIFIED', {})]
    lines = [_line(i, ev, **fields) for i, (ev, fields) in enumerate(events, 1)]
    prefix = b''.join(lines)
    return prefix + _line(len(lines)+1, 'FOOTER', count=len(lines), prefix=hashlib.sha256(prefix).hexdigest())


def _passes():
    return [(ev, dict(case=case, **({'count': 0} if ev in ('DURATION','CASE_END') else {})))
            for case in registry.selected_ordinals()
            for ev in ('CASE_START','CLEANUP_DONE','DURATION','PASS','CASE_END')]


def _triplet(case, sub, fail=False):
    result = [('SUB_ENTER', dict(case=case, sub=sub))]
    if fail:
        result += [('SUBFAIL', dict(case=case, sub=sub, kind='ASSERT', count=1)),
                   ('TRACE', dict(case=case, sub=sub, kind='ASSERT', count=1, code=1, line=10))]
    else: result += [('SUBPASS', dict(case=case, sub=sub))]
    return result + [('SUB_EXIT', dict(case=case, sub=sub))]


def _failure(ev='FAIL', kind='ASSERT', frames=1):
    case = registry.selected_ordinals()[0]
    return [(ev, dict(case=case, kind=kind, count=frames))] + [
        ('TRACE', dict(case=case, kind=kind, count=i, code=1, line=10)) for i in range(1, frames+1)]


def _negative():
    case = registry.selected_ordinals()[0]
    return [('CASE_START', {'case': case})] + _failure() + [
        ('CLEANUP_DONE', {'case': case}), ('DURATION', {'case': case, 'count': 0}),
        ('CASE_END', {'case': case, 'count': 0})]


def _verify(raw, **kw): return verify_events(raw, OP, check=CHECK, **kw)


class CM4EventTests(unittest.TestCase):
    def test_complete_current_lifecycle(self):
        facts = _verify(_report(_passes()))
        self.assertEqual((facts.records, facts.started, facts.passed, facts.ended), (1606,320,320,320))
        self.assertEqual(facts.not_started, ())
        self.assertTrue(facts.declared_suite_closed and facts.declared_restored and facts.declared_inputs_verified)

    def test_duration_required_and_integer_range(self):
        for value in (0, 2**63-1):
            body = _passes(); body[2][1]['count'] = value
            self.assertFalse(_verify(_report(body)).negative)
        for value in (None, True, -1, 2**63, 0.0):
            body = _passes(); body[2][1]['count'] = value
            with self.assertRaises(Refusal): _verify(_report(body))
        body = _passes(); del body[2]
        with self.assertRaises(Refusal): _verify(_report(body))

    def test_cleanup_duration_and_primary_order(self):
        for a, b in ((1,2),(2,3),(1,3)):
            body = _passes(); body[a], body[b] = body[b], body[a]
            with self.assertRaises(Refusal): _verify(_report(body))
        for index in (1,2,3):
            body = _passes(); body.insert(index, body[index])
            with self.assertRaises(Refusal): _verify(_report(body))

    def test_closed_subcase_triplets(self):
        case = registry.selected_ordinals()[0]
        body = _passes(); body[4][1]['count'] = 2
        body[1:1] = _triplet(case,1) + _triplet(case,2)
        self.assertEqual(_verify(_report(body)).subcases, 2)
        for offset in (1,2):
            broken = body[:]; broken.insert(1+offset, ('CLEANUP_DONE', {'case': case}))
            with self.assertRaisesRegex(Refusal, 'closed subcase interval'): _verify(_report(broken))
        # D01's exact counterexample: parent failure after SUBPASS, before exit.
        broken = body[:]; broken[3:3] = _failure()
        with self.assertRaisesRegex(Refusal, 'closed subcase interval'):
            _verify(_report(broken), codes=CODES)

    def test_subcase_missing_duplicate_nested_and_owner(self):
        case = registry.selected_ordinals()[0]
        for fragment in (_triplet(case,1)[:-1], _triplet(case,1)[1:],
                         [_triplet(case,1)[0]] + _triplet(case,1),
                         _triplet(case,1)[:2] + [_triplet(case,1)[1]] + _triplet(case,1)[2:],
                         _triplet(case,2)):
            body = _passes(); body[1:1] = fragment
            with self.assertRaises(Refusal): _verify(_report(body))

    def test_failed_subcase_exit_then_cleanup_failures(self):
        case = registry.selected_ordinals()[0]
        body = [('CASE_START', {'case':case})] + _triplet(case,1,True) + _failure('ERROR') + [
            ('CLEANUP_DONE', {'case':case}), ('DURATION', {'case':case,'count':0}),
            ('CASE_END', {'case':case,'count':1})]
        facts = _verify(_report(body), codes=CODES)
        self.assertEqual((facts.subcases,facts.passed), (1,0))
        broken = body[:]; broken.insert(3, ('ERROR', {'case':case,'kind':'ASSERT','count':1}))
        with self.assertRaises(Refusal): _verify(_report(broken), codes=CODES)

    def test_sticky_negative_exact_suffix(self):
        body = _negative()
        facts = _verify(_report(body), codes=CODES)
        self.assertEqual(facts.not_started, registry.selected_ordinals()[1:])
        for event in (('CASE_START', {'case':registry.selected_ordinals()[1]}),
                      ('PASS', {'case':registry.selected_ordinals()[0]})):
            with self.assertRaises(Refusal): _verify(_report(body+[event]), codes=CODES)

    def test_skip_and_mixed_cleanup(self):
        case = registry.selected_ordinals()[0]
        body = [('CASE_START', {'case':case}), ('SKIP', {'case':case,'count':0})]
        body += _failure() + _failure('ERROR','SYSTEM_EXIT') + _negative()[-3:]
        self.assertTrue(_verify(_report(body), codes=CODES).negative)
        body.insert(-1, _failure()[0])
        with self.assertRaises(Refusal): _verify(_report(body), codes=CODES)

    def test_xfail_xpass_and_exception_kinds(self):
        case = registry.selected_ordinals()[0]
        for kind in ('ASSERT','EXCEPTION','SYSTEM_EXIT','KEYBOARD_INTERRUPT'):
            body = _negative()[:1] + _negative()[-3:-1] + _failure('XFAIL',kind) + _negative()[-1:]
            self.assertTrue(_verify(_report(body), codes=CODES).negative)
        body = _negative()[:1] + _negative()[-3:-1] + [('XPASS', {'case':case,'count':0})] + _negative()[-1:]
        self.assertTrue(_verify(_report(body)).negative)
        with self.assertRaises(Refusal): _verify(_report(_negative()[:1]+_failure('XFAIL')+_negative()[-3:]),codes=CODES)

    def test_fixture_slots_phases_and_late_negation(self):
        order, ids = registry.selected_ordinals(), registry.expected_ids()
        owner = ids[order[0]].rsplit('.',1)[0]
        affected = tuple(i for i in order if ids[i].rsplit('.',1)[0] == owner)
        event = ('FIXTURE_ERROR', {'fixture':0,'count':0})
        setup = ((0,owner,'setup',affected),)
        self.assertTrue(_verify(_report([event]),fixtures=setup).negative)
        with self.assertRaises(Refusal): _verify(_report([event,event]),fixtures=setup)
        with self.assertRaises(Refusal): _verify(_report([event]),fixtures=((0,owner,'cleanup',affected),))
        facts = _verify(_report(_passes()+[event]),fixtures=((0,owner,'cleanup',affected),))
        self.assertEqual(facts.passed,320); self.assertTrue(facts.negative)

    def test_trace_owner_location_and_null_rejection(self):
        for key, value in (('case',registry.selected_ordinals()[1]),('sub',1),('fixture',0),
                           ('code',None),('line',None),('line',20),('count',2),('kind','EXCEPTION')):
            body = _negative(); body[2][1][key] = value
            with self.assertRaises(Refusal): _verify(_report(body),codes=CODES)

    def test_trace_128_positive_129_refused(self):
        for frames in (128,129):
            body = _negative()[:1] + _failure(frames=frames) + _negative()[-3:]
            if frames == 128: self.assertTrue(_verify(_report(body),codes=CODES).negative)
            else:
                with self.assertRaises(Refusal): _verify(_report(body),codes=CODES)
        with self.assertRaises(Refusal): _verify(_report(_negative()[:1]+_failure(kind='UNSUPPORTED')+_negative()[-3:]),codes=CODES)

    def test_suite_closure_and_final_claim_order(self):
        raw = _report(_passes())
        for ev in ('SUITE_OPEN','SUITE_CLOSE','RESTORED','INPUTS_VERIFIED'):
            with self.assertRaises(Refusal): _verify(raw.replace(('"event":"'+ev+'"').encode(),b'"event":"PASS"',1))
        with self.assertRaises(Refusal): _verify(_report([]))
        body = _passes(); body.append(('SUITE_CLOSE',{}))
        with self.assertRaises(Refusal): _verify(_report(body))

    def test_closed_canonical_encoding(self):
        raw = _report(_negative())
        for altered in (raw.replace(b'"case":null',b'"case": null',1),
                        raw.replace(b'"case":null',b'"case":null,"case":null',1),
                        raw.replace(b'"count":320',b'"count":320.0',1),
                        raw.replace(b'"count":320',b'"count":NaN',1),
                        raw.replace(b'{"case":null',b'{"alien":0,"case":null',1),
                        raw.replace(b'\n',b'\r\n',1),raw[:-1],b'\xff'+raw[1:]):
            with self.assertRaises(Refusal): _verify(altered,codes=CODES)

    def test_exact_primitive_types_and_null_fields(self):
        for index,key,value in ((0,'case',True),(0,'sub',1),(1,'count',True),
                                (2,'code',True),(2,'line',True),(3,'count',0),
                                (3,'fixture',0),(4,'sub',1)):
            body = _negative(); body[index][1][key] = value
            with self.assertRaises(Refusal): _verify(_report(body),codes=CODES)
        raw = _report(_negative()).replace(b'"seq":1,',b'"seq":true,',1)
        with self.assertRaises(Refusal): _verify(raw,codes=CODES)

    def test_context_sequence_and_closed_schema(self):
        raw = _report(_negative())
        for altered in (raw.replace(OP.encode(),b'22222222-2222-2222-2222-222222222222',1),
                        raw.replace(registry.FULL_DIGEST.encode(),b'0'*64,1),
                        raw.replace(b'"count":320',b'"count":319',1),
                        raw.replace(b'"seq":2,',b'"seq":3,',1),
                        raw.replace(b'cho51_cm4_event_v1',b'cho51_cm2_event_v1',1)):
            with self.assertRaises(Refusal): _verify(altered,codes=CODES)

    def test_whole_prefix_hash_and_footer_integrity(self):
        raw = _report(_negative()); facts = _verify(raw,codes=CODES)
        prefix = raw[:raw.rfind(b'\n',0,len(raw)-1)+1]
        self.assertEqual(facts.whole_sha256,hashlib.sha256(raw).hexdigest())
        self.assertEqual(facts.prefix_sha256,hashlib.sha256(prefix).hexdigest())
        with self.assertRaises(Refusal): _verify(raw.replace(facts.prefix_sha256.encode(),b'0'*64),codes=CODES)
        with self.assertRaises(Refusal): _verify(raw+raw.splitlines(keepends=True)[-1],codes=CODES)

    def test_full_4096_record_boundary_and_4097_refusal(self):
        case = registry.selected_ordinals()[0]
        body = _passes(); body[4][1]['count'] = 830
        body[1:1] = [event for sub in range(1,831) for event in _triplet(case,sub)]
        self.assertEqual(_verify(_report(body)).records,4096)
        # 6 envelope + 4 case lifecycle + 1361*3 triplet + 4 failure/trace = 4097.
        body = [('CASE_START',{'case':case})]
        body += [event for sub in range(1,1362) for event in _triplet(case,sub)]
        body += _failure()+_failure('ERROR')+_negative()[-3:]
        body[-1][1]['count'] = 1361
        self.assertEqual(_report(body).count(b'\n'),4097)
        with self.assertRaises(Refusal): _verify(_report(body),codes=CODES)
        for invalid in (b'',b'x'*513+b'\n',b'x'*2097153):
            with self.assertRaises(Refusal): _verify(invalid)

    def test_chunked_hash_and_final_checkpoints(self):
        raw = b'a'*2097152; calls = []
        self.assertEqual(hash_bytes(raw,check=lambda: calls.append(1) or True),hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(calls),66)
        with self.assertRaises(Refusal): hash_bytes(raw,check=lambda: False)
        for invalid in (bytearray(b'a'),b'',raw+b'a'):
            with self.assertRaises(Refusal): hash_bytes(invalid,check=CHECK)
        transcript = _report(_passes()); checkpoints = []
        verify_events(transcript,OP,check=lambda: checkpoints.append(1) or True)
        remaining = [len(checkpoints)]
        def last_false():
            remaining[0] -= 1
            return remaining[0] != 0
        with self.assertRaises(Refusal): verify_events(transcript,OP,check=last_false)

    def test_immutable_provisional_facts_and_dispatch(self):
        facts = _verify(_report(_passes()))
        self.assertEqual(facts.disposition,'SUPPLIED_LIFECYCLE_CONSISTENT')
        self.assertFalse(facts.authenticated); self.assertFalse(facts.execution_accepted)
        self.assertIn('observer_cutoff_custody',facts.unavailable)
        self.assertIn('actual_subcase_population',facts.unavailable)
        for key in ('authenticated','execution_accepted'):
            with self.assertRaises(TypeError): replace(facts,**{key:True})
        with self.assertRaises(Refusal): dispatch()

