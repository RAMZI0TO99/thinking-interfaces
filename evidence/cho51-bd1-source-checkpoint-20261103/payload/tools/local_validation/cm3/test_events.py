"""Independent textual fixtures for supplied CM2 event verification."""
import hashlib
import json
import unittest
from dataclasses import replace

from ..cm2 import registry
from ..cm2.callbacks import CallbackModel
from ..hb1.common import Refusal
from .events import hash_bytes, verify_events, dispatch

OP = '11111111-1111-1111-1111-111111111111'
ROSTER = 'ef626570e8ba7c74e42d8229edafba76c2b27ba8fe9955cdca7e58e5f5f22a11'
CHECK = lambda: True
CODES = ((1, 10), (2, 20))


def _line(seq, event, **fields):
    row = dict(schema='cho51_cm2_event_v1', seq=seq, op=OP, roster=ROSTER,
               event=event, case=None, sub=None, fixture=None, kind='NONE',
               code=None, line=None, count=None, prefix=None)
    row.update(fields)
    return (json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')


def _report(events):
    lines = [_line(1, 'HEADER', count=248)]
    for event, fields in events:
        lines.append(_line(len(lines) + 1, event, **fields))
    prefix = b''.join(lines)
    return prefix + _line(len(lines) + 1, 'FOOTER', count=len(lines),
                          prefix=hashlib.sha256(prefix).hexdigest())


def _pass_events():
    return [(event, {'case': ordinal, **({'count': 0} if event == 'CASE_END' else {})})
            for ordinal in registry.selected_ordinals() for event in ('CASE_START', 'PASS', 'CASE_END')]


def _negative(event='FAIL', kind='ASSERT'):
    ordinal = registry.selected_ordinals()[0]
    return [('CASE_START', {'case': ordinal}),
            (event, {'case': ordinal, 'kind': kind, 'count': 1}),
            ('TRACE', {'case': ordinal, 'kind': kind, 'code': 1, 'line': 10, 'count': 1}),
            ('CASE_END', {'case': ordinal, 'count': 0})]


def _verify(raw, **kwargs):
    return verify_events(raw, OP, check=CHECK, **kwargs)


class CM3EventTests(unittest.TestCase):
    def test_minimal_passing_transcript(self):
        facts = _verify(_report(_pass_events()))
        self.assertEqual((facts.records, facts.started, facts.passed, facts.ended), (746, 248, 248, 248))
        self.assertEqual(facts.disposition, 'SUPPLIED_TRANSCRIPT_CONSISTENT')
        self.assertEqual(facts.not_started, ())

    def test_negative_suffix_and_failfast(self):
        events = _negative()
        facts = _verify(_report(events), codes=CODES)
        self.assertTrue(facts.negative)
        self.assertEqual(facts.not_started, registry.selected_ordinals()[1:])
        self.assertEqual(facts.disposition, 'SUPPLIED_NEGATIVE_TRANSCRIPT')
        events.append(('CASE_START', {'case': registry.selected_ordinals()[1]}))
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)

    def test_skip_then_mixed_cleanup(self):
        case = registry.selected_ordinals()[0]
        events = [('CASE_START', {'case': case}), ('SKIP', {'case': case, 'count': 0})]
        for event in ('FAIL', 'ERROR'):
            events += [(event, {'case': case, 'kind': 'EXCEPTION', 'count': 1}),
                       ('TRACE', {'case': case, 'kind': 'EXCEPTION', 'code': 1, 'line': 10, 'count': 1})]
        events += [('CASE_END', {'case': case, 'count': 0})]
        self.assertTrue(_verify(_report(events), codes=CODES).negative)

    def test_special_outcomes_and_primary_order(self):
        case = registry.selected_ordinals()[0]
        for event in ('SKIP', 'XPASS'):
            events = [('CASE_START', {'case': case}), (event, {'case': case, 'count': 0}),
                      ('CASE_END', {'case': case, 'count': 0})]
            self.assertTrue(_verify(_report(events)).negative)
        self.assertTrue(_verify(_report(_negative('XFAIL')), codes=CODES).negative)
        events = _negative('XFAIL')
        events.insert(-1, ('PASS', {'case': case}))
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)

    def test_subcase_counts_and_ownership(self):
        case = registry.selected_ordinals()[0]
        events = [('CASE_START', {'case': case}), ('SUBPASS', {'case': case, 'sub': 1}),
                  ('SUBFAIL', {'case': case, 'sub': 2, 'kind': 'ASSERT', 'count': 1}),
                  ('TRACE', {'case': case, 'sub': 2, 'kind': 'ASSERT', 'count': 1, 'code': 1, 'line': 10}),
                  ('CASE_END', {'case': case, 'count': 2})]
        self.assertEqual(_verify(_report(events), codes=CODES).subcases, 2)
        events[-1][1]['count'] = 1
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)

    def test_fixture_ownership_phase_and_reuse(self):
        order = registry.selected_ordinals()
        ids = registry.expected_ids()
        owner = ids[order[0]].rsplit('.', 1)[0]
        affected = tuple(i for i in order if ids[i].rsplit('.', 1)[0] == owner)
        fixtures = ((0, owner, 'setup', affected),)
        event = ('FIXTURE_ERROR', {'fixture': 0, 'count': 0})
        self.assertTrue(_verify(_report([event]), fixtures=fixtures).negative)
        with self.assertRaises(Refusal): _verify(_report([event, event]), fixtures=fixtures)
        with self.assertRaises(Refusal): _verify(_report([event]), fixtures=((0, owner, 'teardown', affected),))
        late = _pass_events() + [event]
        facts = _verify(_report(late), fixtures=((0, owner, 'cleanup', affected),))
        self.assertEqual(facts.passed, 248)
        self.assertTrue(facts.negative)
        repeated = [event, ('FIXTURE_ERROR', {'fixture': 1, 'count': 0})]
        self.assertTrue(_verify(_report(repeated), fixtures=(fixtures[0],
                              (1, owner, 'setup', affected))).negative)

    def test_trace_groups_and_locations(self):
        events = _negative()
        self.assertTrue(_verify(_report(events), codes=CODES).negative)
        events[2][1]['line'] = 20
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        events = _negative()
        events[2][1]['case'] = registry.selected_ordinals()[1]
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        case = registry.selected_ordinals()[0]
        # Membership verifies supplied order, not the original traceback order.
        for pairs in (CODES, tuple(reversed(CODES))):
            sequence = [('CASE_START', {'case': case}),
                        ('FAIL', {'case': case, 'kind': 'ASSERT', 'count': 2})]
            sequence += [('TRACE', {'case': case, 'kind': 'ASSERT', 'count': i,
                                    'code': code, 'line': line})
                         for i, (code, line) in enumerate(pairs, 1)]
            sequence += [('CASE_END', {'case': case, 'count': 0})]
            facts = _verify(_report(sequence), codes=CODES)
            self.assertTrue(facts.negative)
            self.assertFalse(facts.authenticated)

    def test_trace_128_129_and_unknown_kind(self):
        case = registry.selected_ordinals()[0]
        for size in (128, 129):
            events = [('CASE_START', {'case': case}), ('FAIL', {'case': case, 'kind': 'ASSERT', 'count': size})]
            events += [('TRACE', {'case': case, 'kind': 'ASSERT', 'count': i, 'code': 1, 'line': 10}) for i in range(1, size + 1)]
            events += [('CASE_END', {'case': case, 'count': 0})]
            if size == 128: self.assertTrue(_verify(_report(events), codes=CODES).negative)
            else:
                with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        events = _negative(kind='UNSUPPORTED')
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)

    def test_header_operation_and_roster(self):
        raw = _report(_negative())
        for altered in (raw.replace(OP.encode(), b'22222222-2222-2222-2222-222222222222', 1),
                        raw.replace(ROSTER.encode(), b'0'*64, 1), raw.replace(b'"count":248', b'"count":247', 1)):
            with self.assertRaises(Refusal): _verify(altered, codes=CODES)

    def test_canonical_json_and_encoding(self):
        raw = _report(_negative())
        for altered in (raw.replace(b'"case":null', b'"case": null', 1),
                        raw.replace(b'"case":null', b'"case":null,"case":null', 1),
                        raw.replace(b'"count":248', b'"count":248.0', 1),
                        raw.replace(b'"count":248', b'"count":NaN', 1),
                        raw.replace(b'{"case":null', b'{"alien":1,"case":null', 1),
                        raw.replace(b'\n', b'\r\n', 1), raw[:-1], b'\xff' + raw[1:]):
            with self.assertRaises(Refusal): _verify(altered, codes=CODES)

    def test_exact_types_and_nullability(self):
        events = _negative()
        events[0][1]['case'] = True
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        events = _negative()
        events[0][1]['sub'] = 1
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        for index, key in ((0, 'case'), (1, 'count'), (2, 'code'), (2, 'line'), (2, 'count')):
            changed = _negative(); changed[index][1][key] = True
            with self.assertRaises(Refusal): _verify(_report(changed), codes=CODES)
        raw = _report(_negative()).replace(b'"seq":1,', b'"seq":true,', 1)
        with self.assertRaises(Refusal): _verify(raw, codes=CODES)

    def test_start_pass_end_and_footer_order(self):
        events = _negative()
        for invalid in (events[1:], events[:-1], events + [('PASS', {'case': registry.selected_ordinals()[0]})]):
            with self.assertRaises(Refusal): _verify(_report(invalid), codes=CODES)
        with self.assertRaises(Refusal): _verify(_report([]))

    def test_prefix_and_whole_hashes(self):
        raw = _report(_negative())
        facts = _verify(raw, codes=CODES)
        prefix = raw[:raw.rfind(b'\n', 0, len(raw)-1)+1]
        self.assertEqual(facts.whole_sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(facts.prefix_sha256, hashlib.sha256(prefix).hexdigest())
        with self.assertRaises(Refusal): _verify(raw.replace(facts.prefix_sha256.encode(), b'0'*64), codes=CODES)

    def test_record_line_and_stream_caps(self):
        raw = _report(_negative())
        for invalid in (b'', raw + b'x', b'x'*513 + b'\n', b'x'*(2097152+1)):
            with self.assertRaises(Refusal): _verify(invalid, codes=CODES)
        events = _negative()
        events[1][1]['count'] = 2
        with self.assertRaises(Refusal): _verify(_report(events), codes=CODES)
        # A complete positive boundary, not merely malformed oversized bytes.
        case = registry.selected_ordinals()[0]
        for size in (3350, 3351):
            events = _pass_events()
            events[2][1]['count'] = size
            events[1:1] = [('SUBPASS', {'case': case, 'sub': n})
                           for n in range(1, size + 1)]
            boundary = _report(events)
            if size == 3350:
                facts = _verify(boundary)
                self.assertEqual((facts.records, facts.subcases), (4096, 3350))
            else:
                with self.assertRaises(Refusal): _verify(boundary)

    def test_hash_above_one_mib_and_checkpoints(self):
        raw = b'a' * (1048576 + 1)
        calls = []
        self.assertEqual(hash_bytes(raw, check=lambda: calls.append(1) or True), hashlib.sha256(raw).hexdigest())
        self.assertGreaterEqual(len(calls), 36)
        with self.assertRaises(Refusal): hash_bytes(raw, check=lambda: False)
        with self.assertRaises(Refusal): hash_bytes(b'a' * (2097152 + 1), check=CHECK)

    def test_hidden_lifecycle_and_no_authority(self):
        raw = _report(_pass_events())
        first, second = _verify(raw), _verify(raw)
        self.assertEqual(first, second)
        self.assertFalse(first.authenticated)
        self.assertFalse(first.execution_accepted)
        self.assertIn('final_producer_refusal_latch', first.unavailable)
        self.assertIn('suite_closure', first.unavailable)
        self.assertIn('actual_subcase_population', first.unavailable)
        with self.assertRaises(TypeError): replace(first, authenticated=True)
        with self.assertRaises(TypeError): replace(first, execution_accepted=True)
        with self.assertRaises(Refusal): dispatch()
        # Explicit cross-check only: the parser never imports or replays this producer.
        model = CallbackModel(OP, check=CHECK)
        for case in registry.selected_ordinals():
            model.start(case); model.cleanup_done(case); model.outcome(case, 'PASS'); model.stop(case)
        model.close_suite(); model.finish()
        before = model.raw_bytes()
        self.assertTrue(model.facts().supplied_success)
        with self.assertRaises(Refusal): model.start(registry.selected_ordinals()[0])
        self.assertTrue(model.facts().refused)
        self.assertFalse(model.facts().supplied_success)
        self.assertEqual(before, model.raw_bytes())
        self.assertEqual(_verify(before), _verify(model.raw_bytes()))
