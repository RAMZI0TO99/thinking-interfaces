"""Unexecuted source examples for supplied CM4 contracts, not native witnesses."""
import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError

from ..hb1 import common as c
from ..cm1.collection import LOADER
from ..cm2 import registry as cm2
from ..cm3 import registry as cm3
from . import registry, collection, tables, terminal, join

OP = '11111111-2222-4333-8444-555555555555'
OTHER = '22222222-3333-4444-8555-666666666666'


def ok(): return True


def wire(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def census():
    modules = [dict(module=name, bytes=size, sha256=sha, loader=LOADER, load_tests=False, partial=False)
               for name, size, sha in registry.expected_modules()]
    rows = []
    for name in registry.expected_ids():
        module, cls, method = name.rsplit('.', 2)
        rows.append(dict(id=name, module=module, class_name=cls, method_name=method,
                         source_module=module, source_qualname=cls + '.' + method,
                         skipped=False, deselected=False, expected_failure=False, xfail=False))
    return dict(schema='cho51_cm4_supplied_collection_v1', operation=OP, roster=registry.FULL_DIGEST,
                selection=registry.SELECTION_DIGEST, complete=True, modules=modules, tests=rows)


def references():
    return dict(schema='cho51_cm4_supplied_tables_v1', operation=OP, roster=registry.FULL_DIGEST,
                selection=registry.SELECTION_DIGEST, codes=[[1, 1]], fixtures=[])


def transcript(negative=False):
    rows = []

    def emit(event, **fields):
        row = dict(schema='cho51_cm4_event_v1', seq=len(rows)+1, op=OP, roster=registry.FULL_DIGEST,
                   event=event, case=None, sub=None, fixture=None, kind='NONE', code=None,
                   line=None, count=None, prefix=None)
        row.update(fields)
        rows.append(wire(row))
    emit('HEADER', count=registry.SELECTED_COUNT)
    emit('SUITE_OPEN')
    order = registry.selected_ordinals()
    for case in (order[:1] if negative else order):
        emit('CASE_START', case=case)
        if negative:
            emit('ERROR', case=case, kind='EXCEPTION', count=1)
            emit('TRACE', case=case, kind='EXCEPTION', code=1, line=1, count=1)
        emit('CLEANUP_DONE', case=case)
        emit('DURATION', case=case, count=0)
        if not negative:
            emit('PASS', case=case)
        emit('CASE_END', case=case, count=0)
    for name in ('SUITE_CLOSE', 'RESTORED', 'INPUTS_VERIFIED'):
        emit(name)
    emit('FOOTER', count=len(rows), prefix=hashlib.sha256(b''.join(rows)).hexdigest())
    return b''.join(rows)


def snapshot(raw):
    return dict(schema='cho51_cm4_supplied_terminal_v1', operation=OP, roster=registry.FULL_DIGEST,
                selection=registry.SELECTION_DIGEST, events=pin(raw),
                boundary='SUPPLIED_SEALED_CHANNEL_SNAPSHOT', attempts=1, settled=1, in_flight=0,
                post_footer_attempts=0, first_refusal=None, refused=False, producer_detached=True)


def bundle(*, collected=None, event_raw=None, refs=None, final=None):
    craw = wire(census() if collected is None else collected)
    eraw = transcript() if event_raw is None else event_raw
    traw = wire(references() if refs is None else refs)
    sraw = wire(snapshot(eraw) if final is None else final)
    desc = dict(schema='cho51_cm4_supplied_evidence_join_v1', operation=OP,
                roster=registry.FULL_DIGEST, selection=registry.SELECTION_DIGEST,
                source_set='a'*64, runtime_set='b'*64, producer_set='c'*64,
                collection=pin(craw), events=pin(eraw), tables=pin(traw), terminal=pin(sraw))
    return wire(desc), craw, eraw, traw, sraw


class CM4ContractTests(unittest.TestCase):
    def test_full_collection_and_distinct_projections(self):
        value = census()
        raw = wire(value)
        facts = collection.verify_collection(raw, OP, check=ok)
        self.assertEqual(facts.report_sha256, pin(raw)['sha256'])
        self.assertEqual((len(facts.ids), len(facts.selection)), (836, 320))
        self.assertEqual(facts.operation, OP)
        old_ids, old_modules = set(cm2.expected_ids()), {x[0] for x in cm2.expected_modules()}
        projected = dict(schema='cho51_cm2_supplied_collection_v1', complete=True,
                         modules=[r for r in value['modules'] if r['module'] in old_modules],
                         tests=[r for r in value['tests'] if r['id'] in old_ids])
        self.assertEqual(facts.cm2_projection_sha256, pin(wire(projected))['sha256'])
        self.assertEqual(len({facts.report_sha256, facts.cm2_projection_sha256,
                              facts.cm1_projection_sha256, facts.hb1_projection_sha256}), 4)

    def test_collection_omissions_duplicates_and_excluded_rows(self):
        for mode in ('new_omitted', 'duplicate', 'reverse', 'excluded_flag'):
            value = census()
            if mode == 'new_omitted':
                value['tests'] = [r for r in value['tests'] if r['id'] != registry.NEW_IDS[0]]
            elif mode == 'duplicate': value['tests'][-1] = value['tests'][0]
            elif mode == 'reverse': value['tests'].reverse()
            else:
                row = next(r for r in value['tests'] if r['id'] not in registry.selected_ids())
                row['deselected'] = True
            with self.assertRaises(c.Refusal): collection.verify_collection(wire(value), OP, check=ok)

    def test_collection_context_and_historical_roster_refuse(self):
        for key, bad in (('schema', 'cho51_cm2_supplied_collection_v1'), ('operation', OTHER),
                         ('roster', cm3.FULL_DIGEST), ('selection', cm3.SELECTION_DIGEST),
                         ('complete', 1)):
            value = census()
            value[key] = bad
            with self.assertRaises(c.Refusal): collection.verify_collection(wire(value), OP, check=ok)
        with self.assertRaises(c.Refusal): collection.verify_collection(wire(census()), '0'*36, check=ok)

    def test_collection_module_pins_loader_and_code_owner(self):
        for key, bad in (('bytes', True), ('sha256', '0'*64), ('loader', 'alternate'),
                         ('load_tests', True), ('partial', True)):
            value = census()
            value['modules'][0][key] = bad
            with self.assertRaises(c.Refusal): collection.verify_collection(wire(value), OP, check=ok)
        for key in ('id', 'source_module', 'source_qualname', 'method_name'):
            value = census()
            value['tests'][-1][key] = 'substituted'
            with self.assertRaises(c.Refusal): collection.verify_collection(wire(value), OP, check=ok)

    def test_full_collection_precedes_event_semantics(self):
        value = census()
        value['tests'].pop()
        inputs = bundle(collected=value, event_raw=b'not events\n')
        with self.assertRaisesRegex(c.Refusal, 'full case count'):
            join.join_supplied(*inputs, check=ok)

    def test_current_fixture_owner_and_affected_conservation(self):
        ids, order = registry.expected_ids(), registry.selected_ordinals()
        owner = 'tools.local_validation.cm4.test_contracts.CM4ContractTests'
        affected = [i for i in order if ids[i].rsplit('.', 1)[0] == owner]
        self.assertEqual(len(affected), 20)
        value = references()
        value['fixtures'] = [dict(slot=0, owner=owner, phase='cleanup', affected=affected)]
        facts = tables.parse_tables(wire(value), OP, check=ok)
        self.assertEqual(facts.fixtures[0][3], tuple(affected))
        for bad in (affected[:-1], affected[::-1], affected+[affected[0]], [True]):
            value['fixtures'][0]['affected'] = bad
            with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)
        value['fixtures'][0]['affected'] = affected
        value['fixtures'][0]['owner'] = owner + '.prefix'
        with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)

    def test_table_slot_phase_context_and_canonical_rules(self):
        ids, order = registry.expected_ids(), registry.selected_ordinals()
        owner = ids[order[0]].rsplit('.', 1)[0]
        affected = [i for i in order if ids[i].rsplit('.', 1)[0] == owner]
        value = references()
        row = dict(slot=0, owner=owner, phase='cleanup', affected=affected)
        value['fixtures'] = [row, dict(row, slot=1)]
        self.assertEqual(len(tables.parse_tables(wire(value), OP, check=ok).fixtures), 2)
        for bad in (dict(row), dict(row, slot=True), dict(row, phase='body')):
            value['fixtures'][1] = bad
            with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)
        for key, bad in (('operation', OTHER), ('roster', cm3.FULL_DIGEST), ('selection', 'f'*64)):
            value = references()
            value[key] = bad
            with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)
        with self.assertRaises(c.Refusal): tables.parse_tables(wire(references())+b' ', OP, check=ok)

    def test_code_pair_limits_and_table_aggregate_caps(self):
        value = references()
        value['codes'] = [[i, 1] for i in range(4096)]
        self.assertEqual(len(tables.parse_tables(wire(value), OP, check=ok).codes), 4096)
        value['codes'].append([4096, 1])
        with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)
        for codes in ([[1, 1], [1, 1]], [[2, 1], [1, 1]], [[True, 1]], [[65536, 1]],
                      [[1, 0]], [[1, 2147483648]], [[1, 1, 1]]):
            value['codes'] = codes
            with self.assertRaises(c.Refusal): tables.parse_tables(wire(value), OP, check=ok)
        with self.assertRaises(c.Refusal): tables.parse_tables(b' '*1048577, OP, check=ok)
        with self.assertRaises(c.Refusal): tables.validate_tables([], (), check=ok)
        with self.assertRaises(c.Refusal): tables.validate_tables((), ((),)*4097, check=ok)

    def test_terminal_complete_and_refused_snapshots(self):
        value = snapshot(transcript())
        good = terminal.parse_terminal(wire(value), OP, check=ok)
        self.assertFalse(good.refused)
        self.assertEqual(good.attempts, 1)
        value.update(attempts=2, settled=2, post_footer_attempts=1, first_refusal=2, refused=True)
        bad = terminal.parse_terminal(wire(value), OP, check=ok)
        self.assertTrue(bad.refused)
        self.assertEqual(bad.events_sha256, good.events_sha256)
        self.assertEqual((bad.post_footer_attempts, bad.first_refusal), (1, 2))

    def test_terminal_counter_algebra_and_latch_types(self):
        base = snapshot(transcript())
        for changes in (dict(attempts=0), dict(attempts=True), dict(attempts=65536),
                        dict(settled=0), dict(in_flight=1), dict(post_footer_attempts=2),
                        dict(post_footer_attempts=1), dict(first_refusal=True, refused=True),
                        dict(first_refusal=0, refused=True), dict(first_refusal=2, refused=True),
                        dict(refused=True), dict(first_refusal=1), dict(refused=0),
                        dict(producer_detached=False), dict(producer_detached=1)):
            with self.assertRaises(c.Refusal): terminal.parse_terminal(wire(dict(base, **changes)), OP, check=ok)
        base.update(attempts=65535, settled=65535, post_footer_attempts=65535,
                    first_refusal=1, refused=True)
        self.assertEqual(terminal.parse_terminal(wire(base), OP, check=ok).settled, 65535)

    def test_terminal_schema_context_and_event_pin(self):
        base = snapshot(transcript())
        for key, bad in (('schema', 'old'), ('operation', OTHER), ('roster', cm3.FULL_DIGEST),
                         ('selection', '0'*64), ('boundary', 'AUTHENTICATED'),
                         ('events', dict(bytes=True, sha256='a'*64)),
                         ('events', dict(bytes=2097153, sha256='a'*64)),
                         ('events', dict(bytes=1, sha256='A'*64))):
            with self.assertRaises(c.Refusal): terminal.parse_terminal(wire(dict(base, **{key: bad})), OP, check=ok)
        with self.assertRaises(c.Refusal): terminal.parse_terminal(wire(dict(base, extra=1)), OP, check=ok)
        with self.assertRaises(c.Refusal): terminal.parse_terminal(wire(base).replace(b'\n', b'\r\n'), OP, check=ok)

    def test_raw_join_pins_and_distinct_projections(self):
        inputs = bundle()
        facts = join.join_supplied(*inputs, check=ok)
        for raw, sha in zip(inputs, (facts.descriptor_sha256, facts.collection_sha256,
                                    facts.events_sha256, facts.tables_sha256, facts.terminal_sha256)):
            self.assertEqual(pin(raw)['sha256'], sha)
        self.assertEqual(facts.disposition, 'SUPPLIED_LIFECYCLE_CONSISTENT')
        self.assertEqual(facts.event_facts.passed, 320)
        self.assertEqual(len({facts.collection_sha256, facts.cm2_projection_sha256,
                              facts.cm1_projection_sha256, facts.hb1_projection_sha256}), 4)

    def test_negative_events_and_late_refusal_cannot_be_erased(self):
        raw = transcript()
        final = snapshot(raw)
        final.update(attempts=2, settled=2, post_footer_attempts=1, first_refusal=2, refused=True)
        positive = join.join_supplied(*bundle(event_raw=raw), check=ok)
        late = join.join_supplied(*bundle(event_raw=raw, final=final), check=ok)
        self.assertEqual(positive.events_sha256, late.events_sha256)
        self.assertEqual(late.disposition, 'SUPPLIED_NEGATIVE_LIFECYCLE')
        negative = join.join_supplied(*bundle(event_raw=transcript(True)), check=ok)
        self.assertFalse(negative.terminal_facts.refused)
        self.assertTrue(negative.event_facts.negative)
        self.assertEqual(negative.disposition, 'SUPPLIED_NEGATIVE_LIFECYCLE')

    def test_join_descriptor_and_raw_substitution(self):
        inputs = bundle()
        for name in ('collection', 'events', 'tables', 'terminal'):
            desc = json.loads(inputs[0])
            desc[name]['sha256'] = '0'*64
            with self.assertRaises(c.Refusal): join.join_supplied(wire(desc), *inputs[1:], check=ok)
            desc = json.loads(inputs[0])
            desc[name]['bytes'] = True
            with self.assertRaises(c.Refusal): join.join_supplied(wire(desc), *inputs[1:], check=ok)
        for key, bad in (('schema', 'old'), ('operation', OTHER), ('roster', cm3.FULL_DIGEST),
                         ('selection', '0'*64), ('source_set', 1), ('runtime_set', 'A'*64),
                         ('producer_set', None)):
            desc = json.loads(inputs[0])
            desc[key] = bad
            with self.assertRaises(c.Refusal): join.join_supplied(wire(desc), *inputs[1:], check=ok)

    def test_terminal_must_pin_exact_whole_event_bytes(self):
        raw = transcript()
        for event_pin in (dict(bytes=len(raw)-1, sha256=pin(raw)['sha256']),
                          dict(bytes=len(raw), sha256='0'*64)):
            final = snapshot(raw)
            final['events'] = event_pin
            with self.assertRaisesRegex(c.Refusal, 'terminal whole event join'):
                join.join_supplied(*bundle(event_raw=raw, final=final), check=ok)

    def test_closed_canonical_json_and_exact_input_types(self):
        inputs = bundle()
        for raw in (inputs[0]+b' ', b' '+inputs[0], inputs[0].replace(b'{', b'{"schema":"duplicate",', 1),
                    inputs[0].replace(b'"source_set":', b'"unexpected":null,"source_set":', 1)):
            with self.assertRaises(c.Refusal): join.join_supplied(raw, *inputs[1:], check=ok)
        for index in range(5):
            changed = list(inputs)
            changed[index] = bytearray(changed[index])
            with self.assertRaises(c.Refusal): join.join_supplied(*changed, check=ok)

    def test_all_five_input_caps_and_missing_data(self):
        inputs = bundle()
        for index, cap in enumerate((65536, 1048576, 2097152, 1048576, 65536)):
            for raw in (b'', b' '* (cap+1)):
                changed = list(inputs)
                changed[index] = raw
                with self.assertRaises(c.Refusal): join.join_supplied(*changed, check=ok)

    def test_checkpoints_refuse_and_do_not_create_authority(self):
        inputs = bundle()
        with self.assertRaises(c.Refusal): join.join_supplied(*inputs, check=lambda: 1)
        calls = []

        def bounded():
            calls.append(1)
            return len(calls) < 30
        with self.assertRaises(c.Refusal): join.join_supplied(*inputs, check=bounded)
        self.assertEqual(len(calls), 30)
        for parser, raw in ((collection.verify_collection, inputs[1]), (tables.parse_tables, inputs[3]),
                            (terminal.parse_terminal, inputs[4])):
            with self.assertRaises(c.Refusal): parser(raw, OP, check=lambda: False)

    def test_frozen_facts_reparse_and_dispatch_refusal(self):
        inputs = bundle()
        facts = join.join_supplied(*inputs, check=ok)
        for value in (facts, facts.event_facts, facts.terminal_facts,
                      collection.verify_collection(inputs[1], OP, check=ok),
                      tables.parse_tables(inputs[3], OP, check=ok)):
            self.assertIs(value.authenticated, False)
            self.assertIs(value.execution_accepted, False)
            with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                value.authenticated = True
        with self.assertRaises(c.Refusal): join.join_supplied(inputs[0], facts, *inputs[2:], check=ok)
        self.assertIn('future_activity_exclusion', facts.unavailable)
        self.assertIn('observer_cutoff_custody', facts.unavailable)
        with self.assertRaises(c.Refusal): join.dispatch(facts)

    def test_current_roster_and_conditional_budget_successor(self):
        self.assertEqual((len(registry.expected_ids()), len(registry.expected_modules()),
                          len(registry.selected_ids()), len(registry.NEW_IDS)), (836, 36, 320, 40))
        self.assertEqual(len(set(registry.expected_ids())-set(registry.selected_ids())), 516)
        self.assertEqual(tuple(registry.expected_ids()[i] for i in registry.selected_ordinals()),
                         registry.selected_ids())
        self.assertEqual(registry.roster_digest(ok), registry.FULL_DIGEST)
        self.assertEqual(registry.selection_digest(ok), registry.SELECTION_DIGEST)
        self.assertNotEqual(registry.FULL_DIGEST, cm3.FULL_DIGEST)
        self.assertEqual(5*320+3*254+6, 2368)
        self.assertEqual(2368*512, 1212416)
