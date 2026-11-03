"""Unexecuted supplied raw-join/table cases; no filesystem or real collector."""
import hashlib
import json
import unittest
from dataclasses import FrozenInstanceError, replace

from ..hb1 import common as c
from ..cm2 import collection, registry as target
from . import join, tables, registry as current

OP = '11111111-1111-1111-1111-111111111111'


def yes(): return True


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
            + '\n').encode('ascii')


def pin(raw): return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def collection_value():
    tests = []
    for identity in target.expected_ids():
        module, cls, method = identity.rsplit('.', 2)
        tests.append(dict(id=identity, module=module, class_name=cls, method_name=method,
                          source_module=module, source_qualname=cls + '.' + method,
                          skipped=False, deselected=False, expected_failure=False, xfail=False))
    return dict(schema='cho51_cm2_supplied_collection_v1', complete=True, tests=tests,
                modules=[dict(module=n, bytes=b, sha256=s, loader=collection.cm1.LOADER,
                              load_tests=False, partial=False)
                         for n, b, s in target.expected_modules()])


def table_value(): return dict(schema='cho51_cm3_supplied_tables_v1', codes=[], fixtures=[])


def fixture_row(slot=0, phase='setup'):
    ids, order = target.expected_ids(), target.selected_ordinals()
    owner = ids[order[0]].rsplit('.', 1)[0]
    return dict(slot=slot, owner=owner, phase=phase,
                affected=[i for i in order if ids[i].rsplit('.', 1)[0] == owner])


def transcript(*, negative=False, trace=False):
    lines = []
    def emit(event, **fields):
        row = dict(schema='cho51_cm2_event_v1', seq=len(lines) + 1, op=OP,
                   roster=target.FULL_DIGEST, event=event, case=None, sub=None,
                   fixture=None, kind='NONE', code=None, line=None, count=None, prefix=None)
        row.update(fields)
        lines.append(encoded(row))
    emit('HEADER', count=248)
    for case in target.selected_ordinals():
        emit('CASE_START', case=case)
        if trace:
            emit('FAIL', case=case, kind='ASSERT', count=1)
            emit('TRACE', case=case, kind='ASSERT', code=1, line=10, count=1)
        elif negative:
            emit('SKIP', case=case, count=0)
        else:
            emit('PASS', case=case)
        emit('CASE_END', case=case, count=0)
        if negative or trace: break
    prefix = b''.join(lines)
    emit('FOOTER', count=len(lines), prefix=hashlib.sha256(prefix).hexdigest())
    return b''.join(lines)


def descriptor(collected, observed, references):
    return dict(schema='cho51_cm3_supplied_evidence_join_v1', operation=OP,
                roster=target.FULL_DIGEST, selection=target.SELECTION_DIGEST,
                source_set='a' * 64, runtime_set='b' * 64, producer_set='c' * 64,
                collection=pin(collected), events=pin(observed), tables=pin(references))


def packet():
    a, b, d = encoded(collection_value()), transcript(), encoded(table_value())
    return encoded(descriptor(a, b, d)), a, b, d


def checked(a, b, d):
    return join.join_supplied(encoded(descriptor(a, b, d)), a, b, d, check=yes)


class CM3JoinTests(unittest.TestCase):
    def test_full_raw_join_and_separate_projections(self):
        args = packet()
        facts = join.join_supplied(*args, check=yes)
        self.assertEqual(facts.disposition, 'SUPPLIED_TRANSCRIPT_CONSISTENT')
        self.assertEqual(facts.collection_sha256, pin(args[1])['sha256'])
        self.assertEqual(facts.events_sha256, pin(args[2])['sha256'])
        self.assertEqual(len({facts.collection_sha256, facts.cm1_projection_sha256,
                              facts.hb1_projection_sha256}), 3)
        self.assertEqual((facts.event_facts.started, facts.event_facts.passed), (248, 248))

    def test_collection_before_event_semantics(self):
        value = collection_value(); value['tests'].pop()
        # Both raw hashes match, but collection is incomplete and events malformed.
        with self.assertRaisesRegex(c.Refusal, 'full case count'):
            checked(encoded(value), b'not-events\n', encoded(table_value()))

    def test_collection_omission_and_substitution(self):
        for mode in ('omit', 'duplicate', 'reorder', 'flag', 'module'):
            value = collection_value()
            if mode == 'omit': value['tests'].pop()
            elif mode == 'duplicate': value['tests'][-1] = value['tests'][0]
            elif mode == 'reorder': value['tests'].reverse()
            elif mode == 'flag': value['tests'][-1]['deselected'] = True
            else: value['modules'][-1]['sha256'] = '0' * 64
            with self.assertRaises(c.Refusal):
                checked(encoded(value), transcript(), encoded(table_value()))

    def test_descriptor_closed_canonical_and_pins(self):
        _, a, b, d = packet()
        for mode in ('unknown', 'size', 'digest', 'bool', 'roster', 'selection'):
            value = descriptor(a, b, d)
            if mode == 'unknown': value['accepted'] = True
            elif mode == 'size': value['events']['bytes'] -= 1
            elif mode == 'digest': value['tables']['sha256'] = '0' * 64
            elif mode == 'bool': value['collection']['bytes'] = True
            else: value[mode] = '0' * 64
            with self.assertRaises(c.Refusal):
                join.join_supplied(encoded(value), a, b, d, check=yes)
        raw = encoded(descriptor(a, b, d))
        for invalid in (b' ' + raw, raw[:-1], raw.replace(b'"events":', b'"events":0,"events":', 1)):
            with self.assertRaises(c.Refusal): join.join_supplied(invalid, a, b, d, check=yes)

    def test_operation_and_context_types(self):
        _, a, b, d = packet()
        for key, value in (('operation', '22222222-2222-2222-2222-222222222222'),
                           ('operation', '00000000-0000-0000-0000-000000000000'),
                           ('source_set', True), ('runtime_set', 'B' * 64), ('producer_set', 'g' * 64)):
            desc = descriptor(a, b, d); desc[key] = value
            with self.assertRaises(c.Refusal):
                join.join_supplied(encoded(desc), a, b, d, check=yes)

    def test_input_bounds_and_immutability(self):
        args = packet()
        for index, cap in enumerate((65536, 1048576, 2097152, 1048576)):
            for raw in (b'', b'x' * (cap + 1), bytearray(args[index]), memoryview(args[index])):
                changed = list(args); changed[index] = raw
                with self.assertRaises(c.Refusal): join.join_supplied(*changed, check=yes)

    def test_raw_table_schema_and_canonical_order(self):
        value = table_value(); value['codes'] = [[1, 10], [2, 20]]
        facts = tables.parse_tables(encoded(value), check=yes)
        self.assertEqual(facts.codes, ((1, 10), (2, 20)))
        value['codes'].reverse()
        with self.assertRaises(c.Refusal): tables.parse_tables(encoded(value), check=yes)
        for raw in (b'{}\n', b' ' + encoded(table_value()), encoded(table_value())[:-1]):
            with self.assertRaises(c.Refusal): tables.parse_tables(raw, check=yes)

    def test_code_pair_bounds_and_duplicates(self):
        for codes in (((True, 10),), ((1, False),), ((-1, 10),), ((65536, 10),),
                      ((1, 0),), ((1, 2147483648),), ((1, 10), (1, 10)), ([1, 10],)):
            with self.assertRaises(c.Refusal): tables.validate_tables(codes, (), check=yes)
        facts = tables.validate_tables(((0, 1), (65535, 2147483647)), (), check=yes)
        self.assertEqual(facts[0][-1], (65535, 2147483647))

    def test_fixture_exact_owner_and_affected_set(self):
        for mode in ('owner', 'omit', 'duplicate', 'reverse', 'bool'):
            row = fixture_row()
            if mode == 'owner': row['owner'] = 'tools.local_validation'
            elif mode == 'omit': row['affected'].pop()
            elif mode == 'duplicate': row['affected'][-1] = row['affected'][0]
            elif mode == 'reverse': row['affected'].reverse()
            else: row['affected'][0] = True
            value = table_value(); value['fixtures'] = [row]
            with self.assertRaises(c.Refusal): tables.parse_tables(encoded(value), check=yes)

    def test_fixture_slots_phases_and_duplicates(self):
        value = table_value(); value['fixtures'] = [fixture_row(0), fixture_row(1)]
        self.assertEqual(len(tables.parse_tables(encoded(value), check=yes).fixtures), 2)
        for key, invalid in (('slot', True), ('slot', 4096), ('phase', 'body'), ('affected', [])):
            changed = table_value(); row = fixture_row(); row[key] = invalid
            changed['fixtures'] = [row]
            with self.assertRaises(c.Refusal): tables.parse_tables(encoded(changed), check=yes)
        value['fixtures'].reverse()
        with self.assertRaises(c.Refusal): tables.parse_tables(encoded(value), check=yes)
        value['fixtures'] = [fixture_row(0), fixture_row(0)]
        with self.assertRaises(c.Refusal): tables.parse_tables(encoded(value), check=yes)

    def test_table_aggregate_limits(self):
        codes = tuple((i, 1) for i in range(4096))
        self.assertEqual(len(tables.validate_tables(codes, (), check=yes)[0]), 4096)
        with self.assertRaises(c.Refusal): tables.validate_tables(codes + ((4096, 1),), (), check=yes)
        with self.assertRaises(c.Refusal): tables.parse_tables(b'x' * 1048577, check=yes)
        row = fixture_row()
        fixtures = tuple((i, row['owner'], row['phase'], tuple(row['affected'])) for i in range(4096))
        self.assertEqual(len(tables.validate_tables((), fixtures, check=yes)[1]), 4096)
        with self.assertRaises(c.Refusal): tables.validate_tables((), fixtures + (fixtures[-1],), check=yes)

    def test_negative_join_preserved(self):
        facts = checked(encoded(collection_value()), transcript(negative=True), encoded(table_value()))
        self.assertEqual(facts.disposition, 'SUPPLIED_NEGATIVE_TRANSCRIPT')
        self.assertEqual(facts.event_facts.not_started, target.selected_ordinals()[1:])
        self.assertFalse(facts.execution_accepted)

    def test_tables_bound_to_events(self):
        a, b = encoded(collection_value()), transcript(trace=True)
        value = table_value(); value['codes'] = [[1, 10]]
        good = encoded(value)
        self.assertTrue(checked(a, b, good).event_facts.negative)
        value['codes'] = [[1, 11]]; changed = encoded(value)
        with self.assertRaises(c.Refusal):
            join.join_supplied(encoded(descriptor(a, b, good)), a, b, changed, check=yes)
        with self.assertRaises(c.Refusal): checked(a, b, changed)

    def test_reparse_not_caller_facts(self):
        args = packet(); facts = join.join_supplied(*args, check=yes)
        self.assertEqual(join.join_supplied(*args, check=yes), facts)
        with self.assertRaises(c.Refusal): join.join_supplied(facts, *args[1:], check=yes)
        with self.assertRaises(c.Refusal): join.join_supplied(*args, check=lambda: False)
        a = collection_value(); a['tests'].pop()
        with self.assertRaises(c.Refusal): checked(encoded(a), args[2], args[3])

    def test_frozen_results_and_refusal(self):
        facts = join.join_supplied(*packet(), check=yes)
        self.assertFalse(facts.authenticated)
        self.assertFalse(facts.execution_accepted)
        self.assertIn('original_same_operation_collection', facts.unavailable)
        with self.assertRaises(FrozenInstanceError): facts.operation = OP
        with self.assertRaises(TypeError): replace(facts, authenticated=True)
        with self.assertRaises(c.Refusal): join.dispatch()

    def test_current_roster_is_separate_target(self):
        self.assertEqual((len(current.expected_ids()), len(current.expected_modules()),
                          len(current.selected_ids())), (796, 34, 280))
        self.assertEqual((len(target.expected_ids()), len(target.selected_ids())), (764, 248))
        self.assertEqual(set(current.expected_ids()) - set(target.expected_ids()), set(current.NEW_IDS))
        self.assertEqual(len(current.NEW_IDS), 32)
        self.assertEqual(join.join_supplied(*packet(), check=yes).event_facts.started, 248)
