"""Supplied-byte fixtures only. Execution requires separate project admission."""
import hashlib
import json
import sys
import unittest
from tools.local_validation.lplan15 import compiler as c


def frontier_fixture(adjacency=None, seeds=None, debts=None):
    """Asserted tiny graph; this helper never reads or parses a source file."""
    if adjacency is None:
        adjacency = {'a': ['b'], 'b': []}
    modules = []
    for name, targets in adjacency.items():
        payload = {'node': 'opaque', 'original_id': name + '/node0'}
        records = [{'id': c.frontier_id('record', name, 0, payload), 'payload': payload}]
        edges = []
        for index, target in enumerate(targets):
            fields = dict(target=target, site=name + '/import' + str(index),
                          epoch='eager', conditional=False, kind='literal')
            fields['id'] = c.frontier_id('edge', name, target, fields['site'],
                                         fields['epoch'], fields['conditional'], fields['kind'])
            edges.append(fields)
        modules.append(dict(name=name, origin={'identity': name + '.py', 'sha256': 'a' * 64},
                            source_bytes=5, nodes=1, depth=1, records=records, edges=edges))
    seed_rows = []
    for name, phase in (seeds if seeds is not None else [('a', 'L2')]):
        pieces = name.split('.')
        prefixes = ['.'.join(pieces[:i]) for i in range(1, len(pieces) + 1)]
        seed_rows.append(dict(id=c.frontier_id('seed', name, phase, prefixes),
                              module=name, phase=phase, prefixes=prefixes))
    obligations = []
    for kind, payload in (debts or []):
        obligations.append(dict(id=c.frontier_id('obligation', kind, 'historical', payload),
                                kind=kind, origin='historical', payload=payload))
    graph = dict(modules=modules, seeds=seed_rows, obligations=obligations)
    binding = dict(algorithm=c.FRONTIER_SCHEMA, source='1' * 64, runtime='2' * 64,
                   spec='3' * 64, roots='4' * 64, predecessor='5' * 64,
                   seeds=c.digest(c.encode(seed_rows)))
    return binding, graph


def frontier_clone(value):
    return json.loads(c.encode(value))


class FrontierTests(unittest.TestCase):
    def start(self, adjacency=None, seeds=None, debts=None):
        binding, graph = frontier_fixture(adjacency, seeds, debts)
        return c.frontier_start(binding, graph, lambda: True)

    def advance(self, state, steps=100, signals=None, guard=None):
        return c.frontier_continue(state, c.digest(c.encode(state)), state['binding'],
                                   steps, [True] * steps if signals is None else signals,
                                   (lambda: True) if guard is None else guard)

    def lowered(self, key, value, action):
        original = c.FRONTIER_LIMITS[key]
        self.assertLessEqual(value, original)
        try:
            c.FRONTIER_LIMITS[key] = value
            return action()
        finally:
            c.FRONTIER_LIMITS[key] = original

    def assert_invalid(self, state):
        with self.assertRaises(c.Refusal):
            self.advance(state, 1)

    def test_fc01_closed_schemas(self):
        for target in ('graph', 'module', 'origin', 'record', 'edge', 'seed', 'debt'):
            binding, graph = frontier_fixture(debts=[('effect', {'detail': 'unknown'})])
            objects = dict(graph=graph, module=graph['modules'][0], origin=graph['modules'][0]['origin'],
                           record=graph['modules'][0]['records'][0], edge=graph['modules'][0]['edges'][0],
                           seed=graph['seeds'][0], debt=graph['obligations'][0])
            objects[target]['unexpected'] = None
            with self.subTest(target=target), self.assertRaises(c.Refusal):
                c.frontier_start(binding, graph, lambda: True)
        state = self.start(); state['unexpected'] = None; self.assert_invalid(state)
        state = self.start(); state['frames'][0].pop('work'); self.assert_invalid(state)

    def test_fc02_exact_types_and_identifiers(self):
        mutations = [('source_bytes', True), ('source_bytes', 1.0), ('nodes', -1), ('depth', 129), ('name', 'a-b')]
        for field, value in mutations:
            binding, graph = frontier_fixture(); graph['modules'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(c.Refusal):
                c.frontier_start(binding, graph, lambda: True)
        for value in ('A' * 64, '1' * 63, True):
            binding, graph = frontier_fixture(); binding['source'] = value
            with self.assertRaises(c.Refusal): c.frontier_start(binding, graph, lambda: True)
        for value in (1.5, 2**63, object()):
            with self.assertRaises(c.Refusal): c.frontier_id('payload', value)

    def test_fc03_duplicate_and_case_collisions(self):
        for category in ('modules', 'seeds', 'obligations', 'edges', 'case'):
            binding, graph = frontier_fixture(debts=[('effect', {'detail': 'unknown'})])
            if category == 'edges': graph['modules'][0]['edges'] *= 2
            elif category == 'case': graph['modules'].append(dict(graph['modules'][0], name='A'))
            else: graph[category].append(frontier_clone(graph[category][0]))
            binding['seeds'] = c.digest(c.encode(graph['seeds']))
            with self.subTest(category=category), self.assertRaises(c.Refusal):
                c.frontier_start(binding, graph, lambda: True)

    def test_fc04_ids_and_reference_replay(self):
        for target in ('record', 'edge', 'seed', 'debt'):
            binding, graph = frontier_fixture(debts=[('effect', {'detail': 'unknown'})])
            objects = dict(record=graph['modules'][0]['records'][0], edge=graph['modules'][0]['edges'][0],
                           seed=graph['seeds'][0], debt=graph['obligations'][0])
            objects[target]['id'] = '0' * 64; binding['seeds'] = c.digest(c.encode(graph['seeds']))
            with self.assertRaises(c.Refusal): c.frontier_start(binding, graph, lambda: True)
        state = self.start(); state['frames'][0]['links'][0]['target'] = '0' * 64
        self.assert_invalid(state)

    def test_fc05_external_binding_and_digest(self):
        state = self.start()
        for key in state['binding']:
            binding = dict(state['binding']); binding[key] = '9' * 64
            with self.subTest(key=key), self.assertRaises(c.Refusal):
                c.frontier_continue(state, c.digest(c.encode(state)), binding, 1, [True], lambda: True)
        with self.assertRaises(c.Refusal):
            c.frontier_continue(state, '0' * 64, state['binding'], 1, [True], lambda: True)

    def test_fc06_seed_prefix_requester(self):
        state = self.start({'a': [], 'a.b': []}, [('a.b', 'L4')])
        requester = state['graph']['seeds'][0]['id']
        self.assertEqual([(f['module'], f['phase'], f['requester']) for f in state['frames'][0]['facts']],
                         [('a', 'L4', requester), ('a.b', 'L4', requester)])
        self.assertEqual(len(state['frames'][0]['links']), 2)

    def test_fc07_late_phase_reaches_descendants(self):
        state = self.start({'a': ['b'], 'b': ['d'], 'd': [], 'z': ['y'], 'y': ['a']},
                           [('a', 'L2'), ('z', 'L4')])
        result = self.advance(state)
        self.assertEqual(result['result'], 'ADVANCED')
        facts = result['snapshot']['frames'][-1]['facts']
        self.assertEqual({f['phase'] for f in facts if f['module'] == 'd'}, {'L2', 'L4'})

    def test_fc08_same_phase_distinct_requesters(self):
        state = self.start({'a': ['shared'], 'z': ['shared'], 'shared': ['leaf'], 'leaf': []},
                           [('a', 'L3'), ('z', 'L3')])
        result = self.advance(state)['snapshot']
        leaves = [f for f in result['frames'][-1]['facts'] if f['module'] == 'leaf']
        self.assertEqual(len(leaves), 2)
        self.assertEqual({f['requester'] for f in leaves}, {s['id'] for s in state['graph']['seeds']})

    def test_fc09_diamond_preserves_links(self):
        state = self.start({'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': []})
        frame = self.advance(state)['snapshot']['frames'][-1]
        targets = [f['id'] for f in frame['facts'] if f['module'] == 'd']
        self.assertEqual(len(targets), 1)
        incoming = [link for link in frame['links'] if link['target'] == targets[0]]
        self.assertEqual(len(incoming), 2)
        self.assertEqual(len({link['source'] for link in incoming}), 2)

    def test_fc10_cycle_is_finite_and_propagates(self):
        state = self.start({'a': ['b'], 'b': ['a'], 'z': ['a']}, [('a', 'L2'), ('z', 'L4')])
        result = self.advance(state)['snapshot']; frame = result['frames'][-1]
        self.assertTrue(result['saturated']); self.assertEqual(len(frame['facts']), 5)
        self.assertEqual({f['phase'] for f in frame['facts'] if f['module'] == 'b'}, {'L2', 'L4'})
        self.assertEqual(self.advance(result)['result'], 'NO_WORK')

    def test_fc11_deferred_conditional_may_reach(self):
        binding, graph = frontier_fixture()
        edge = graph['modules'][0]['edges'][0]; edge.update(epoch='deferred', conditional=True)
        edge['id'] = c.frontier_id('edge', 'a', 'b', edge['site'], 'deferred', True, 'literal')
        state = c.frontier_start(binding, graph, lambda: True)
        final = self.advance(state)['snapshot']
        self.assertIn('b', [f['module'] for f in final['frames'][-1]['facts']])
        self.assertEqual(final['graph']['modules'][0]['edges'][0], edge)
        self.assertIn(edge['id'], [link['edge'] for link in final['frames'][-1]['links']])

    def test_fc12_missing_origin_blocks(self):
        state = self.start({'a': ['missing']})
        final = self.advance(state)['snapshot']
        self.assertFalse(final['saturated'])
        self.assertEqual(len(final['frames'][-1]['work']), 1)
        self.assertTrue(final['frames'][-1]['work'][0]['blocked'])
        result = self.advance(final)
        self.assertEqual((result['result'], result['reason']), ('NO_WORK', 'blocked'))
        self.assertEqual(result['snapshot'], final)

    def test_fc13_all_debt_kinds_preserved(self):
        kinds = ('dynamic', 'native', 'export', 'binding', 'effect', 'legacy_multi_phase')
        state = self.start(debts=[(kind, {'detail': kind, 'nested': [1, False, None]}) for kind in kinds])
        final = self.advance(state)['snapshot']
        self.assertEqual(final['graph']['obligations'], state['graph']['obligations'])
        self.assertEqual({x['kind'] for x in final['graph']['obligations']}, set(kinds))

    def test_fc14_saturation_is_not_authority(self):
        state = self.start({'a': []}, debts=[('effect', {'detail': 'unresolved'})])
        final = self.advance(state)['snapshot']
        self.assertTrue(final['saturated']); self.assertEqual(final['status'], 'INCOMPLETE_REFUSED')
        for key in ('g2_complete', 'launch_authorized', 'capabilities_accepted'):
            self.assertIs(final[key], False)

    def test_fc15_chunked_and_single_run_equivalence(self):
        original = self.start({'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': ['a']})
        single = self.advance(original)['snapshot']; chunked = original
        for unused in range(16):
            result = self.advance(chunked, 1)
            if result['result'] == 'NO_WORK': break
            self.assertEqual(result['result'], 'ADVANCED'); chunked = result['snapshot']
        self.assertTrue(chunked['saturated'])
        for key in ('steps', 'facts', 'links', 'work'):
            self.assertEqual(chunked['frames'][-1][key], single['frames'][-1][key])

    def test_fc16_each_boundary_conserves_payloads(self):
        state = self.start({'a': ['b'], 'b': ['c'], 'c': []}, debts=[('binding', {'detail': ['x', 'y']})])
        original = frontier_clone(state['graph'])
        for unused in range(3):
            result = self.advance(state, 1); self.assertEqual(result['result'], 'ADVANCED')
            state = result['snapshot']; self.assertEqual(state['graph'], original)
        self.assertTrue(state['saturated'])

    def test_fc17_atomic_cap_refusal(self):
        state = self.start({'a': []}); before = c.encode(state)
        result = self.lowered('rows', 18, lambda: self.advance(state, 1))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED')
        self.assertEqual(c.encode(result['snapshot']), before)
        self.assertEqual(c.encode(state), before)
        self.assertEqual(result['snapshot']['frames'][0]['steps'], 0)

    def test_fc18_complete_row_accounting(self):
        # Two modules+origins, two records, edge, seed and initial work frame = twelve.
        self.lowered('rows', 12, self.start)
        with self.assertRaises(c.Refusal):
            self.lowered('rows', 11, self.start)
        state = self.start()
        self.assertEqual(self.lowered('rows', 30, lambda: self.advance(state, 1))['result'], 'ADVANCED')

    def test_fc19_module_source_node_depth_limits(self):
        for field, bad in (('source_bytes', 2 * 1024**2 + 1), ('nodes', 200001), ('depth', 129)):
            binding, graph = frontier_fixture(); graph['modules'][0][field] = bad
            with self.subTest(field=field), self.assertRaises(c.Refusal):
                c.frontier_start(binding, graph, lambda: True)
        with self.assertRaises(c.Refusal): self.lowered('modules', 1, self.start)
        with self.assertRaises(c.Refusal): self.lowered('source_bytes', 9, self.start)
        with self.assertRaises(c.Refusal): self.lowered('nodes', 1, self.start)

    def test_fc20_edge_page_and_serialized_caps(self):
        state = self.start({'a': []})
        result = self.lowered('edges', 2, lambda: self.advance(state, 1))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED'); self.assertIn('edges', result['reason'])
        result = self.lowered('page_rows', 8, lambda: self.lowered('pages', 1, lambda: self.advance(state, 1)))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED'); self.assertIn('pages', result['reason'])
        size = len(c.encode(state))
        with self.assertRaises(c.Refusal): self.lowered('file_bytes', size - 1, lambda: self.advance(state, 1))
        with self.assertRaises(c.Refusal): self.lowered('output_bytes', size - 1, lambda: self.advance(state, 1))

    def test_fc21_chain_count_and_byte_caps(self):
        state = self.start({'a': []})
        result = self.lowered('snapshots', 1, lambda: self.advance(state, 1))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED')
        result = self.lowered('history_bytes', len(c.encode(state)) + 1, lambda: self.advance(state, 1))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED'); self.assertIn('history', result['reason'])

    def test_fc22_forged_cursor_and_completed_state(self):
        for mutation in ('cursor', 'steps', 'fact', 'link', 'bool_cursor'):
            state = self.start()
            frame = state['frames'][0]
            if mutation == 'cursor': frame['work'][0]['cursor'] = 1
            elif mutation == 'steps': frame['steps'] = 1
            elif mutation == 'fact': frame['facts'][0]['module'] = 'b'
            elif mutation == 'link': frame['links'][0]['source'] = '0' * 64
            else: frame['work'][0]['cursor'] = False
            with self.subTest(mutation=mutation): self.assert_invalid(state)

    def test_fc23_exact_pending_work_order(self):
        for mutation in ('missing', 'extra', 'reverse'):
            state = self.start({'a': [], 'z': []}, [('a', 'L2'), ('z', 'L4')])
            work = state['frames'][0]['work']
            if mutation == 'missing': work.pop()
            elif mutation == 'extra': work.append(dict(work[0]))
            else: work.reverse()
            with self.subTest(mutation=mutation): self.assert_invalid(state)

    def test_fc24_sequence_predecessor_and_graph_drift(self):
        original = self.start(); final = self.advance(original, 1)['snapshot']
        self.assertEqual(final['sequence'], 1)
        self.assertEqual(final['predecessor'], c.digest(c.encode(original)))
        for field, value in (('sequence', 0), ('predecessor', '0' * 64)):
            state = frontier_clone(final); state[field] = value; self.assert_invalid(state)
        changed = frontier_clone(final); changed['graph']['modules'][0]['source_bytes'] += 1
        with self.assertRaises(c.Refusal):
            c.frontier_continue(changed, c.digest(c.encode(final)), final['binding'], 1, [True], lambda: True)

    def test_fc25_live_guard_and_supplied_refusal(self):
        state = self.advance(self.start(), 1)['snapshot']; before = c.encode(state)
        for index in range(3):
            signals = [True] * 3; signals[index] = False
            result = self.advance(state, 3, signals)
            self.assertEqual(result['result'], 'CHECKPOINT_REFUSED')
            self.assertEqual(c.encode(result['snapshot']), before)
        calls = [0]
        def count(): calls[0] += 1; return True
        self.advance(state, 1, guard=count)
        for stop in (1, max(2, calls[0] // 2), calls[0]):
            remaining = [stop]
            def guard(): remaining[0] -= 1; return remaining[0] > 0
            with self.assertRaises(c.Refusal): self.advance(state, 1, guard=guard)
            self.assertEqual(c.encode(state), before)
        with self.assertRaises(c.Refusal): self.advance(state, 1, guard=lambda: 1)

    def test_fc26_deterministic_canonical_output(self):
        first = self.start(); second = self.start()
        self.assertEqual(c.encode(first), c.encode(second))
        left = self.advance(first, 1); right = self.advance(second, 1)
        self.assertEqual(c.encode(left), c.encode(right))
        self.assertEqual(c.digest(c.encode(left)), c.digest(c.encode(right)))
        self.assertEqual(c.frontier_id('test', {'b': 2, 'a': 1}), c.frontier_id('test', {'a': 1, 'b': 2}))

    def test_fc27_payloads_are_inert(self):
        text = '__import__("unavailable_candidate_module").execute()'
        state = self.start(debts=[('dynamic', {'detail': text})])
        old_parse = c.ast.parse
        def forbidden(*args, **kwargs): raise AssertionError('unexpected parser use')
        try:
            c.ast.parse = forbidden
            final = self.advance(state)['snapshot']
        finally:
            c.ast.parse = old_parse
        self.assertEqual(final['graph']['obligations'][0]['payload']['detail'], text)

    def test_fc28_no_input_or_output_aliasing(self):
        binding, graph = frontier_fixture(debts=[('effect', {'detail': ['untouched']})])
        before = c.encode([binding, graph]); state = c.frontier_start(binding, graph, lambda: True)
        state['graph']['obligations'][0]['payload']['detail'].append('new')
        self.assertEqual(c.encode([binding, graph]), before)
        state = c.frontier_start(binding, graph, lambda: True); original = c.encode(state)
        result = self.advance(state, 1); result['snapshot']['graph']['obligations'].clear()
        self.assertEqual(c.encode(state), original)

    def test_fc29_complete_history_and_debt_content(self):
        state = self.start(); final = self.advance(state, 1)['snapshot']
        self.assertEqual(final['frames'][:-1], state['frames'])
        self.assertEqual(final['frames'][-1]['retained_before'], len(c.encode(state)))
        for payload in ({}, {'sha256': 'a' * 64}, {'ref': 'missing'}, {'detail': None}):
            binding, graph = frontier_fixture(debts=[('effect', payload)])
            with self.assertRaises(c.Refusal): c.frontier_start(binding, graph, lambda: True)

    def test_fc30_oversized_atomic_fanout_refuses(self):
        state = self.start({'a': ['b', 'c'], 'b': [], 'c': []})
        before = c.encode(state)
        # The first commit needs a complete extra frame, not only its new edge.
        result = self.lowered('rows', 30, lambda: self.advance(state, 2))
        self.assertEqual(result['result'], 'CAPACITY_REFUSED')
        self.assertEqual(c.encode(state), before); self.assertEqual(c.encode(result['snapshot']), before)

    def test_fc31_zero_edge_once_and_blocked_fairness(self):
        state = self.start({'a': []}, [('missing', 'L2'), ('a', 'L4')])
        final = self.advance(state)['snapshot']
        self.assertEqual(final['frames'][-1]['steps'], 1)
        self.assertEqual(len(final['frames'][-1]['work']), 1)
        self.assertTrue(final['frames'][-1]['work'][0]['blocked'])
        self.assertEqual(self.advance(final)['result'], 'NO_WORK')

    def test_fc32_authority_injection_refuses(self):
        for key, value in (('g2_complete', True), ('launch_authorized', True),
                           ('capabilities_accepted', True), ('status', 'ACCEPTED'), ('saturated', True)):
            state = self.start(); state[key] = value
            with self.subTest(key=key): self.assert_invalid(state)


def fixture(raw=b'x = 1\n'):
    pin = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    rows = [{'module': 'candidate.m%d' % n, 'path': 'fixture/%d.py' % n,
             'phase': 'L4', 'pin': dict(pin)} for n in range(5)]
    spec = {'schema': c.SCHEMA, 'modules': rows, 'limits': dict(c.HARD), 'migration_ref': None}
    class Reader:
        def read_small(self, path, expected):
            return raw
    class Outputs:
        def __init__(self): self.saved = {}
        def write(self, name, data):
            self.saved[name] = json.loads(data)
            return {'name': name, 'sha256': hashlib.sha256(data).hexdigest()}
    return spec, {r['path']: dict(pin) for r in rows}, Reader(), Outputs()

class InventoryTests(unittest.TestCase):
    def test_pages_and_no_authority(self):
        spec, physical, reader, out = fixture()
        c.publish_inventory(reader, spec, physical, out, lambda: True)
        index = out.saved['l-inventory-index.json']
        self.assertEqual(index['status'], 'INCOMPLETE_REFUSED')
        self.assertFalse(index['launch_authorized'])
        self.assertEqual(index['nodes'], 25)
        self.assertTrue(all(row['analysis'] == 'unresolved' for row in out.saved['l-inventory-000.json']['rows']))

    def test_bounds_and_closed_schema(self):
        for key, value in [('max_nodes', True), ('max_depth', 129), ('max_module_bytes', 0)]:
            with self.subTest(key=key):
                spec, physical, reader, out = fixture(); spec['limits'][key] = value
                with self.assertRaises(c.Refusal): c.publish_inventory(reader, spec, physical, out, lambda: True)
                self.assertFalse(out.saved)
        spec, physical, reader, out = fixture(); spec['extra'] = 1
        with self.assertRaises(c.Refusal): c.validate(spec, physical)

    def test_pin_and_retained_integrity(self):
        spec, physical, reader, out = fixture()
        physical[spec['modules'][0]['path']]['sha256'] = '0' * 64
        with self.assertRaises(c.Refusal): c.validate(spec, physical)
        spec, physical, reader, out = fixture(); reader.read_small = lambda *args: b'other'
        with self.assertRaises(c.Refusal): c.publish_inventory(reader, spec, physical, out, lambda: True)

    def test_syntax_diagnostic_columns_no_source(self):
        spec, physical, reader, out = fixture('é = (\n'.encode())
        c.publish_inventory(reader, spec, physical, out, lambda: True)
        diagnostic = out.saved['l-inventory-index.json']['diagnostics'][0]['diagnostic']
        self.assertEqual(diagnostic['kind'], 'SyntaxError')
        self.assertNotIn('é', json.dumps(diagnostic))
        self.assertIsNotNone(diagnostic['character_column_1based'])
        self.assertGreater(diagnostic['utf8_byte_column_0based'], diagnostic['character_column_1based'] - 1)
        malformed = (b"@param('x', [\n 1,\n]):\ndef first(): pass\n"
                     b"@param('x', [\n 2,\n]):\ndef second(): pass\n")
        for raw, line in ((malformed, 3), (malformed.replace(b']):', b'])', 1), 7)):
            spec, physical, reader, out = fixture(raw)
            c.publish_inventory(reader, spec, physical, out, lambda: True)
            d = out.saved['l-inventory-index.json']['diagnostics'][0]['diagnostic']
            self.assertEqual(d['line'], line)
            self.assertEqual(d['message'], 'invalid syntax')
            self.assertIn('end_character_column_1based', d)

    def test_bom_spans_and_shapes(self):
        raw = b'\xef\xbb\xbfx = 1\n'
        spec, physical, reader, out = fixture(raw)
        c.publish_inventory(reader, spec, physical, out, lambda: True)
        rows = out.saved['l-inventory-000.json']['rows']
        names = [r for r in rows if r['kind'] == 'Name']
        self.assertEqual(names[0]['raw_span_sha256'], hashlib.sha256(b'x').hexdigest())
        self.assertTrue(all(len(r['shape_sha256']) == 64 for r in rows))
        self.assertEqual(len({r['id'] for r in rows}), len(rows))

    def test_scope_and_epochs(self):
        raw = b'@deco\ndef f(x=call()):\n return work(x)\n'
        spec, physical, reader, out = fixture(raw)
        c.publish_inventory(reader, spec, physical, out, lambda: True)
        rows = [r for r in out.saved['l-inventory-000.json']['rows'] if r['module'] == 'candidate.m0']
        self.assertTrue(any(r['kind'] == 'Call' and r['epoch'] == 'eager' for r in rows))
        self.assertTrue(any(r['kind'] == 'Call' and r['epoch'] == 'deferred' and r['scope'] != '$' for r in rows))

    def test_limits_refuse_without_index(self):
        spec, physical, reader, out = fixture(); spec['limits']['max_nodes'] = 1
        with self.assertRaises(c.Refusal): c.publish_inventory(reader, spec, physical, out, lambda: True)
        self.assertNotIn('l-inventory-index.json', out.saved)
        spec, physical, reader, out = fixture(); spec['limits']['max_output_bytes'] = 1
        with self.assertRaises(c.Refusal): c.publish_inventory(reader, spec, physical, out, lambda: True)
        self.assertNotIn('l-inventory-index.json', out.saved)

    def test_encoding_refuses(self):
        spec, physical, reader, out = fixture(b'# coding: latin-1\nx = "\xe9"\n')
        with self.assertRaises(c.Refusal): c.publish_inventory(reader, spec, physical, out, lambda: True)

from tools.local_validation.lplan15 import migration as m

def migration_fixture():
    old = {m.OLD + name: (b'core ' + name.encode()) for name in m.FILES}
    old[m.OLD + 'test_mapping.py'] = (b'from docs.phase2.cho51_p3_adapter_v1 import contracts as Contracts\n'
        b'from docs.phase2.cho51_p3_adapter_v1 import mapping as Mapping\n')
    old[m.OLD + 'test_telemetry.py'] = (b'@pytest.mark.parametrize("x", [1]):\ndef test_segment_rejects_malformed_contract(x): pass\n'
        b'@pytest.mark.parametrize("x", [1]):\ndef test_join_rejects_cross_domain_and_order_errors(x): pass\n')
    new = {m.NEW + name: old[m.OLD + name] for name in m.FILES}
    edits = []
    for name, removed, inserted in [('test_mapping.py', b'docs.phase2.cho51_p3_adapter_v1', b'docs.phase2.cho51_p3_adapter_v2'),
                                    ('test_telemetry.py', b']):', b'])')]:
        raw = old[m.OLD + name]; result = bytearray(); position = 0
        while True:
            at = raw.find(removed, position)
            if at < 0: break
            result.extend(raw[position:at]); offset = at if name == 'test_mapping.py' else at + 2
            if name == 'test_telemetry.py': result.extend(b'])')
            edits.append({'original_path': m.OLD + name, 'successor_path': m.NEW + name,
                          'original_offset': offset, 'successor_offset': len(result),
                          'removed_hex': (removed if name == 'test_mapping.py' else b':').hex(),
                          'inserted_hex': (inserted if name == 'test_mapping.py' else b'').hex()})
            if name == 'test_mapping.py': result.extend(inserted)
            position = at + len(removed)
        result.extend(raw[position:]); new[m.NEW + name] = bytes(result)
    functions = []
    for n in range(25):
        name = 'test_mapping.py' if n < 13 else 'test_telemetry.py'
        count = 3 if n < 13 else (7 if n < 19 else 6)
        module = m.OLD + name
        functions.append({'module': module, 'node_prefix': module + '::test_%d' % n, 'expected_cases': count})
    def ref(path, data): return {'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    roster = json.dumps({'executed': False, 'function_count': 25, 'expected_total': 117, 'functions': functions,
                         'candidate_source_pins': {path: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for path, raw in old.items()}}).encode()
    controls = b'fixture control roster'
    record = {'schema': 'cho51_candidate_migration_v1', 'original_roster_ref': ref('roster', roster),
              'control_roster_ref': ref('controls', controls),
              'original_source_refs': [ref(path, raw) for path, raw in old.items()],
              'successor_source_refs': [ref(path, raw) for path, raw in new.items()], 'allowed_edits': edits,
              'function_map': [{'original_module': r['module'], 'original_node_prefix': r['node_prefix'],
                                'successor_module': m.NEW + r['module'][len(m.OLD):],
                                'successor_node_prefix': m.NEW + r['node_prefix'][len(m.OLD):],
                                'expected_cases': r['expected_cases']} for r in functions],
              'independent_review': {'required': True, 'binding': 'external_source_review_and_root_adoption'},
              'safety': {'launch_authorized': False, 'scientific_admission': False, 'original_executed': False, 'successor_executed': False}}
    return record, old, new, roster, controls

class MigrationTests(unittest.TestCase):
    def test_valid_fixture(self):
        self.assertFalse(m.validate_migration(*migration_fixture())['launch_authorized'])

    def test_patch_and_pin_refusal(self):
        for mutation in ('production', 'edit', 'control', 'offset'):
            with self.subTest(mutation=mutation):
                record, old, new, roster, controls = migration_fixture()
                if mutation == 'production': new[m.NEW + 'mapping.py'] += b'x'
                if mutation == 'edit': record['allowed_edits'][0]['inserted_hex'] = '00'
                if mutation == 'offset': record['allowed_edits'][0]['successor_offset'] += 1
                if mutation == 'control': controls += b'x'
                with self.assertRaises(m.Refusal): m.validate_migration(record, old, new, roster, controls)

    def test_map_refusal(self):
        record, old, new, roster, controls = migration_fixture()
        record['function_map'][0]['successor_node_prefix'] += '[invented]'
        with self.assertRaises(m.Refusal): m.validate_migration(record, old, new, roster, controls)


class AdditionalRefusalTests(unittest.TestCase):
    def test_checkpoint_requires_literal_true(self):
        for result in (False, None, 1):
            with self.subTest(result=result):
                spec, physical, reader, out = fixture()
                with self.assertRaises(c.Refusal):
                    c.publish_inventory(reader, spec, physical, out, lambda: result)
                self.assertNotIn('l-inventory-index.json', out.saved)

    def test_migration_roster_and_types(self):
        for mutation in ('roster_pin', 'duplicate_roster', 'bool_offset', 'bool_cases'):
            with self.subTest(mutation=mutation):
                record, old, new, roster, controls = migration_fixture()
                if mutation == 'roster_pin':
                    value = json.loads(roster); value['candidate_source_pins'][m.OLD + 'mapping.py']['bytes'] += 1
                    roster = json.dumps(value).encode()
                    record['original_roster_ref']['bytes'] = len(roster)
                    record['original_roster_ref']['sha256'] = hashlib.sha256(roster).hexdigest()
                if mutation == 'duplicate_roster':
                    value = json.loads(roster); value['functions'][1] = value['functions'][0]
                    roster = json.dumps(value).encode()
                    record['original_roster_ref']['bytes'] = len(roster)
                    record['original_roster_ref']['sha256'] = hashlib.sha256(roster).hexdigest()
                if mutation == 'bool_offset': record['allowed_edits'][0]['original_offset'] = True
                if mutation == 'bool_cases': record['function_map'][0]['expected_cases'] = True
                with self.assertRaises(m.Refusal): m.validate_migration(record, old, new, roster, controls)


def host_fixture():
    from tools.local_validation.lp18 import supervisor as host
    from tools.local_validation.v1 import records
    comparison, old, new, roster, controls = migration_fixture()
    comparison['original_roster_ref']['path'] = host.ROSTER_PATH
    comparison['control_roster_ref']['path'] = host.CONTROL_PATH
    content = dict(old, **new)
    content.update({host.ROSTER_PATH: roster, host.CONTROL_PATH: controls,
                    host.MIGRATION_PATH: json.dumps(comparison).encode()})
    pins = {path: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for path, raw in content.items()}
    source_paths = set(new) | {host.ROSTER_PATH, host.CONTROL_PATH, host.MIGRATION_PATH}
    request = {'sources': {path: pins[path] for path in source_paths}}
    absolute = {(host.ROOT/path).as_posix(): raw for path, raw in content.items()}
    physical = {(host.ROOT/path).as_posix(): pin for path, pin in pins.items()}
    class Reader:
        def read_small(self, path, pin):
            return absolute[path]
    modules = [dict(module=(m.NEW+name)[:-3].replace('/','.'),
                    path=(host.ROOT/(m.NEW+name)).as_posix(),
                    phase='L4' if name.startswith('test_') else 'L3', pin=pins[m.NEW+name])
               for name in m.FILES[:5]]
    spec = dict(schema=c.SCHEMA, modules=modules, limits=dict(host.INVENTORY_LIMITS),
                migration_ref=dict(path=host.MIGRATION_PATH, **pins[host.MIGRATION_PATH]))
    return host, request, spec, physical, Reader(), records


class ConsumerBindingTests(unittest.TestCase):
    def test_exact_five_and_trusted_roster_join(self):
        host, *args = host_fixture()
        result = host.candidate_inventory_binding(*args, m)
        self.assertEqual(result['expected_total'],117)
        self.assertEqual(result['collected_ids'],0)
        self.assertFalse(result['launch_authorized'])

    def test_scope_and_trusted_pin_refusals(self):
        for change in ('phase','module','limit','roster','control','migration'):
            with self.subTest(change=change):
                host, request, spec, physical, reader, records = host_fixture()
                if change=='phase': spec['modules'][0]['phase']='L2'
                if change=='module': spec['modules'][0]['module']='candidate.other'
                if change=='limit': spec['limits']['max_nodes']+=1
                if change in ('roster','control'):
                    path=host.ROSTER_PATH if change=='roster' else host.CONTROL_PATH
                    request['sources'][path]=dict(bytes=0,sha256='0'*64)
                if change=='migration': spec['migration_ref']['path']='unreviewed.json'
                with self.assertRaises(ValueError):
                    host.candidate_inventory_binding(request,spec,physical,reader,records,m)

    def test_physical_and_retained_refusals(self):
        for change in ('missing','physical','retained'):
            with self.subTest(change=change):
                host, request, spec, physical, reader, records = host_fixture()
                path=(host.ROOT/(m.NEW+'contracts.py')).as_posix()
                if change=='missing': physical.pop(path)
                if change=='physical': physical[path]=dict(bytes=0,sha256='0'*64)
                if change=='retained':
                    original=reader.read_small
                    reader.read_small=lambda p,pin: b'changed' if p==path else original(p,pin)
                with self.assertRaises(ValueError):
                    host.candidate_inventory_binding(request,spec,physical,reader,records,m)

# Supplied-byte resolver fixtures. No candidate or installed dependency imports.
def resolver_fixture(raw=b'x = 1\n'):
    from contextlib import contextmanager
    import ast
    path = 'C:/fixture/sample.py'
    pin = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    spec = {'schema': c.RESOLVER_SCHEMA, 'roots': ['C:/fixture'],
            'seeds': [{'module': 'sample', 'phase': 'L4'}],
            'builtin_modules': [], 'frozen_modules': [], 'extension_suffixes': ['.pyd'],
            'limits': dict(c.RESOLVER_HARD)}
    class Reader:
        def read_small(self, name, expected): return raw
    @contextmanager
    def parser(name, data):
        yield ast.parse(data, filename=name, mode='exec')
    return spec, {path: pin}, Reader(), fixture()[3], parser

class ResolverTests(unittest.TestCase):
    """Direct supplied-byte AST fixtures; execution requires separate admission."""
    def analyze(self, source):
        import ast
        raw = source.encode('utf-8')
        pin = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        rows, imports, meta = c._resolver_rows(ast.parse(raw), 'fixture', pin, raw, dict(c.RESOLVER_HARD), lambda: True)
        return rows, imports, meta
    def one(self, rows, kind, name=None):
        found = [r for r in rows if r['kind'] == kind and (name is None or r.get('name') == name)]
        self.assertEqual(len(found), 1)
        return found[0]
    def test_module_definition_call_candidate(self):
        rows, _, _ = self.analyze('def f(): pass\nf()\n')
        self.assertEqual(self.one(rows, 'Call')['lexical_targets'], [self.one(rows, 'FunctionDef')['id']])
        self.assertFalse(self.one(rows, 'Call')['runtime_binding_proven'])
    def test_call_before_definition_refused(self):
        rows, _, _ = self.analyze('f()\ndef f(): pass\n')
        self.assertEqual(self.one(rows, 'Name', 'f')['refusal'], 'late_binding')
    def test_function_parameter_scope(self):
        rows, _, _ = self.analyze('def f(x):\n return x\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['binding_candidates'], [self.one(rows, 'arg', 'x')['id']])
    def test_parameter_is_not_module_binding(self):
        rows, _, _ = self.analyze('def f(x): pass\nx()\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['refusal'], 'unbound_or_builtin_unknown')
    def test_default_in_enclosing_scope(self):
        rows, _, _ = self.analyze('def x(): pass\ndef f(a=x): pass\n')
        use = self.one(rows, 'Name', 'x')
        self.assertEqual(use['scope_kind'], 'module')
        self.assertEqual(use['binding_candidates'], [self.one(rows, 'FunctionDef', 'x')['id']])
    def test_decorator_in_enclosing_scope(self):
        rows, _, _ = self.analyze('def deco(x): pass\n@deco\ndef f(): pass\n')
        use = self.one(rows, 'Name', 'deco')
        self.assertEqual(use['scope_kind'], 'module')
        self.assertEqual(use['epoch'], 'eager')
        self_ref, _, _ = self.analyze('@f\ndef f(): pass\n')
        self.assertEqual(self.one(self_ref, 'Name', 'f')['refusal'], 'decorated_definition_unknown')
    def test_class_base_in_enclosing_scope(self):
        rows, _, _ = self.analyze('class Base: pass\nclass C(Base): pass\n')
        self.assertEqual(self.one(rows, 'Name', 'Base')['scope_kind'], 'module')
    def test_class_body_scope(self):
        rows, _, _ = self.analyze('class C:\n x = 1\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['scope_kind'], 'class')
    def test_method_body_deferred(self):
        rows, _, _ = self.analyze('class C:\n def f(self):\n  return self\n')
        self.assertEqual(self.one(rows, 'Name', 'self')['epoch'], 'deferred')
    def test_method_skips_class_scope(self):
        rows, _, _ = self.analyze('class C:\n def x(): pass\n def f(self):\n  return x\n')
        self.assertFalse(self.one(rows, 'Name', 'x')['binding_candidates'])
    def test_lambda_parameter_scope(self):
        rows, _, _ = self.analyze('f = lambda x: x\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['binding_candidates'], [self.one(rows, 'arg', 'x')['id']])
    def test_lambda_default_outer(self):
        rows, _, _ = self.analyze('def x(): pass\nf = lambda a=x: a\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['scope_kind'], 'module')
    def test_comprehension_first_iterator_outer(self):
        rows, _, _ = self.analyze('values = []\ny = [x for x in values]\n')
        use = [r for r in rows if r.get('name') == 'values' and r.get('binding_kind') == 'Load'][0]
        self.assertEqual(use['scope_kind'], 'module')
    def test_comprehension_target_inner(self):
        rows, _, _ = self.analyze('y = [x for x in values]\n')
        names = [r for r in rows if r.get('name') == 'x']
        self.assertTrue(all(r['scope_kind'] == 'comprehension' for r in names))
    def test_comprehension_no_module_leak(self):
        rows, _, _ = self.analyze('y = [x for x in values]\nx()\n')
        uses = [r for r in rows if r.get('name') == 'x' and r.get('binding_kind') == 'Load']
        self.assertEqual([r for r in uses if r['scope_kind'] == 'module'][0]['refusal'], 'unbound_or_builtin_unknown')
    def test_multiple_bindings_refused(self):
        rows, _, _ = self.analyze('def f(): pass\ndef f(): pass\nf()\n')
        self.assertEqual(self.one(rows, 'Name', 'f')['refusal'], 'multiple_bindings')
    def test_conditional_definition_refused(self):
        rows, _, _ = self.analyze('if flag:\n def f(): pass\nf()\n')
        self.assertEqual(self.one(rows, 'Name', 'f')['refusal'], 'conditional_or_deleted_binding')
    def test_delete_invalidates_binding(self):
        rows, _, _ = self.analyze('def f(): pass\ndel f\nf()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_simple_alias_chain(self):
        rows, _, _ = self.analyze('def f(): pass\na = f\nb = a\nb()\n')
        self.assertEqual(self.one(rows, 'Call')['lexical_targets'], [self.one(rows, 'FunctionDef')['id']])
    def test_alias_to_unknown_refused(self):
        rows, _, _ = self.analyze('a = missing\na()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_alias_cycle_refused(self):
        rows, _, _ = self.analyze('a = b\nb = a\na()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_import_alias_candidate(self):
        rows, imports, _ = self.analyze('import pkg as p\np()\n')
        self.assertEqual(self.one(rows, 'Call')['import_candidate'], 'pkg')
        self.assertEqual(len(imports), 1)
    def test_from_import_candidate(self):
        rows, _, _ = self.analyze('from pkg import f as g\ng()\n')
        self.assertEqual(self.one(rows, 'Call')['import_candidate'], 'f')
    def test_import_rebinding_refused(self):
        rows, _, _ = self.analyze('import pkg as p\np = other\np()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_deferred_external_refused(self):
        rows, _, _ = self.analyze('def x(): pass\ndef f():\n return x()\n')
        self.assertEqual(self.one(rows, 'Name', 'x')['refusal'], 'deferred_external_binding')
    def test_global_declaration(self):
        rows, _, _ = self.analyze('def f():\n global x\n x = 1\n')
        self.assertEqual(self.one(rows, 'Global')['binding_kind'], 'global')
        rows, _, _ = self.analyze('def original(): pass\ndef writer():\n global x\n x = original\nx()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_nonlocal_declaration(self):
        rows, _, _ = self.analyze('def f():\n x = 1\n def g():\n  nonlocal x\n  x = 2\n')
        self.assertEqual(self.one(rows, 'Nonlocal')['binding_kind'], 'nonlocal')
    def test_exception_target_is_conditional(self):
        rows, _, _ = self.analyze('try:\n pass\nexcept Exception as e:\n e()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_match_target_is_conditional(self):
        rows, _, _ = self.analyze('match subject:\n case x:\n  x()\n')
        self.assertFalse(self.one(rows, 'Call')['lexical_targets'])
    def test_future_annotation_not_eager_grant(self):
        rows, _, meta = self.analyze('from __future__ import annotations\nx: T\n')
        self.assertTrue(meta['future_annotations'])
        self.assertEqual(self.one(rows, 'Name', 'T')['epoch'], 'future_annotation_unknown')
    def test_annotation_without_future_eager(self):
        rows, _, _ = self.analyze('x: T\n')
        self.assertEqual(self.one(rows, 'Name', 'T')['epoch'], 'eager')
        for source in ('def T(): pass\ntype Alias[T] = T\n',
                       'def T(): pass\ndef f[T](x: T): pass\n'):
            with self.subTest(source=source):
                rows, _, _ = self.analyze(source)
                self.assertTrue(any(r.get('refusal') == 'unsupported_annotation_scope' for r in rows))
                self.assertTrue(all(not r.get('binding_candidates') for r in rows
                                    if r.get('kind') == 'Name' and r.get('binding_kind') == 'Load'))
    def test_dynamic_builtins_are_possible_only(self):
        for name in ('__import__', 'compile', 'exec', 'eval', 'getattr'):
            with self.subTest(name=name):
                rows, _, meta = self.analyze(name + '("x")\n')
                self.assertEqual(self.one(rows, 'Call')['possible_dynamic_effect'], name)
                self.assertFalse(self.one(rows, 'Call')['runtime_binding_proven'])
                self.assertEqual(meta['dynamic_imports'][0]['reason'], 'runtime_identity_unproved')
    def test_attribute_call_dynamic_unknown(self):
        rows, _, meta = self.analyze('obj.f()\n')
        self.assertEqual(self.one(rows, 'Call')['possible_dynamic_effect'], 'attribute_dispatch')
        self.assertEqual(meta['dynamic_imports'][0]['reason'], 'attribute_dispatch_unknown')
    def test_protocol_effects(self):
        for source, kind in [('x + y', 'BinOp'), ('x < y', 'Compare'), ('x and y', 'BoolOp'),
                             ('if x: pass', 'If'), ('for x in y: pass', 'For'), ('with x: pass', 'With'),
                             ('raise x', 'Raise'), ('x[y]', 'Subscript')]:
            with self.subTest(kind=kind):
                rows, _, _ = self.analyze(source + '\n')
                self.assertIn('effect', self.one(rows, kind))
    def graph(self, sources, seed='sample', edit=None, output=None):
        from contextlib import contextmanager
        import ast
        raws = {'C:/fixture/' + name: value.encode('utf-8') for name, value in sources.items()}
        physical = {path: {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for path, raw in raws.items()}
        spec = {'schema': c.RESOLVER_SCHEMA, 'roots': ['C:/fixture'],
                'seeds': [{'module': seed, 'phase': 'L4'}], 'builtin_modules': [], 'frozen_modules': [],
                'extension_suffixes': ['.pyd'], 'limits': dict(c.RESOLVER_HARD)}
        if edit: edit(spec, physical)
        class Reader:
            def read_small(self, name, expected):
                if set(expected) != {'bytes', 'sha256'}: raise ValueError('non-content read pin')
                return raws[name]
        @contextmanager
        def parser(path, raw): yield ast.parse(raw, filename=path, mode='exec')
        out = output if output is not None else fixture()[3]
        index = c.resolve_sources(Reader(), spec, physical, out, lambda: True, parser)
        rows = [row for name, page in out.saved.items() if name.startswith('l-resolver-0') for row in page['rows']]
        return index, rows
    def test_graph_source_and_literal_closure(self):
        index, rows = self.graph({'sample.py': 'import other\n', 'other.py': 'pass\n'})
        self.assertTrue(index['graph_fixed_point'])
        self.assertFalse(index['g2_complete'])
        self.assertTrue(any(r.get('to') == 'other' for r in rows))
        self.assertEqual(index['nodes'], 5)
        _, ancestry = self.graph({'sample.py': 'import other\n', 'other.py': 'def f(x):\n return x\n'})
        nodes = [r for r in ancestry if 'id' in r]
        by_module = {}
        for row in nodes: by_module.setdefault(row['module'], set()).add(row['id'])
        for row in nodes:
            self.assertIn(row['scope'], by_module[row['module']])
            if row['parent'] is not None: self.assertIn(row['parent'], by_module[row['module']])
        self.assertTrue({'Module', 'arguments', 'Return'}.issubset({r['kind'] for r in nodes if r['module'] == 'other'}))
        identity = {'schema': 'cho51_lv_native_identity_v1', 'volume_serial': '1' * 16,
                    'file_id': '2' * 32, 'volume_kind': 'local_fixed', 'filesystem': 'NTFS'}
        def descriptor(spec, physical):
            path = 'C:/fixture/sample.py'; pin = physical[path]
            physical[path] = {'schema': 'cho51_lv_file_descriptor_v1', 'path': path,
                              'native_identity': identity, 'file_type': 'regular', 'reparse_point': False,
                              'bytes': pin['bytes'], 'sha256': pin['sha256'], 'link_count': 1}
        _, descriptor_rows = self.graph({'sample.py': 'pass\n'}, edit=descriptor)
        origin = next(r['origin'] for r in descriptor_rows if r.get('kind') == 'origin')
        self.assertEqual(origin['physical_descriptor']['native_identity'], identity)
        self.assertEqual(set(origin['pin']), {'bytes', 'sha256'})
        def bad_descriptor(spec, physical):
            descriptor(spec, physical)
            physical['C:/fixture/sample.py']['native_identity']['file_id'] = '0' * 32
        with self.assertRaises(c.Refusal): self.graph({'sample.py': 'pass\n'}, edit=bad_descriptor)
    def test_graph_parent_shadow_and_precedence(self):
        sources = {'sample.py': 'import pkg.child\n', 'pkg/__init__.py': 'pass\n',
                   'pkg.py': 'pass\n', 'pkg/child.py': 'pass\n'}
        index, rows = self.graph(sources)
        origins = {r['module']: r['origin'] for r in rows if r.get('kind') == 'origin'}
        self.assertEqual(origins['pkg']['kind'], 'package')
        self.assertEqual(origins['pkg.child']['path'], 'C:/fixture/pkg/child.py')
        self.assertTrue(index['graph_fixed_point'])
        spec = {'roots': ['C:/first', 'C:/second'], 'builtin_modules': [], 'frozen_modules': [], 'extension_suffixes': ['.pyd']}
        pin = {'bytes': 0, 'sha256': '0' * 64}
        physical = {'C:/first/pkg/__init__.py': pin, 'C:/second/pkg/child.py': pin}
        self.assertEqual(c._origin('pkg.child', spec, physical)['kind'], 'missing_origin')
        self.assertFalse(c._resolver_path('C:/fixture/../escape.py'))
        self.assertFalse(c._resolver_path('C:\\fixture\\sample.py'))
    def test_graph_unresolved_dynamic(self):
        index, rows = self.graph({'sample.py': '__import__("other")\n', 'other.py': 'pass\n'})
        self.assertFalse(index['graph_fixed_point'])
        self.assertEqual(index['modules'], 1)
        self.assertTrue(any(r.get('reason') == 'dynamic_call_unresolved' for r in rows))
        for source in (
            'def f(): pass\n[[(f := __import__) for x in y] for z in w]\nf()\n',
            'def f(): pass\ndef g():\n global f\n [(f := __import__) for x in y]\n',
            'def outer():\n def f(): pass\n def inner():\n  nonlocal f\n  [[(f := __import__) for x in y] for z in w]\n  f()\n'):
            with self.subTest(source=source):
                result, observed = self.graph({'sample.py': source})
                self.assertFalse(result['graph_fixed_point'])
                self.assertTrue(any(r.get('reason') == 'comprehension_namedexpr_unmodeled' for r in observed))
                self.assertTrue(all(not r.get('binding_candidates') for r in observed
                                    if r.get('kind') == 'Name' and r.get('name') == 'f' and r.get('binding_kind') == 'Load'))
    def test_graph_from_and_star_proof(self):
        index, _ = self.graph({'sample.py': 'from pkg import *\n',
                               'pkg/__init__.py': '__all__ = ["f"]\ndef f(): pass\n'})
        self.assertTrue(index['graph_fixed_point'])
        refused, rows = self.graph({'sample.py': 'from pkg import *\n', 'pkg/__init__.py': 'pass\n'})
        self.assertFalse(refused['graph_fixed_point'])
        self.assertTrue(any(r.get('reason') == 'star_export_unresolved' for r in rows))
    def test_graph_relative_import_and_cycle(self):
        index, rows = self.graph({'pkg/__init__.py': 'pass\n', 'pkg/a.py': 'from . import b\n',
                                  'pkg/b.py': 'import pkg.a\n'}, seed='pkg.a')
        self.assertFalse(index['graph_fixed_point'])
        self.assertTrue(any(set(group) == {'pkg.a', 'pkg.b'} for group in index['components']))
        self.assertFalse(index['component_order_is_execution_grant'])
        sources = {'alpha.py': 'import shared\n', 'beta.py': 'import shared\n', 'shared.py': 'pass\n'}
        def phases(reverse):
            def configure(spec, physical):
                seeds = [{'module': 'alpha', 'phase': 'L3'}, {'module': 'beta', 'phase': 'L4'}]
                spec['seeds'] = list(reversed(seeds)) if reverse else seeds
            return self.graph(sources, edit=configure)
        first, first_rows = phases(False); second, second_rows = phases(True)
        self.assertFalse(first['graph_fixed_point']); self.assertFalse(second['graph_fixed_point'])
        joins = lambda rows: [r for r in rows if r.get('reason') == 'multi_phase_join_unresolved']
        self.assertEqual(joins(first_rows), joins(second_rows))
        self.assertEqual({e['phase'] for e in first_rows if e.get('kind') == 'edge' and e.get('to') == 'shared'}, {'L3', 'L4'})
    def test_graph_capacity_and_checkpoint(self):
        index, _ = self.graph({'sample.py': 'import other\n', 'other.py': 'pass\n'},
                              edit=lambda s, p: s['limits'].update(max_modules=1))
        self.assertFalse(index['graph_fixed_point'])
        self.assertEqual(index['cap_refusal'], 'max_modules')
        self.assertGreater(index['queue_count'], 0)
        out = fixture()[3]
        with self.assertRaises(c.Refusal):
            self.graph({'sample.py': 'x = 1\n'}, edit=lambda s, p: s['limits'].update(max_rows=1), output=out)
        self.assertFalse(out.saved)
        for sources, edit in (
            ({'sample.py': 'x()\n' * 55}, lambda spec, physical: spec['limits'].update(max_pages=1)),
            ({'sample.py': 'pass\n'}, lambda spec, physical: spec['limits'].update(max_output_bytes=512 * 1024 + 1))):
            out = fixture()[3]
            with self.subTest(sources=sources), self.assertRaises(c.Refusal):
                self.graph(sources, edit=edit, output=out)
            self.assertFalse(out.saved)
        import ast
        raw = b'x = 1\n'; pin = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        with self.assertRaises(c.Refusal):
            c._resolver_rows(ast.parse(raw), 'fixture', pin, raw, dict(c.RESOLVER_HARD), lambda: False)

class LosslessTests(unittest.TestCase):
    """Small supplied fixtures; delegated inherited controls are identified."""
    def state(self):
        binding, graph = frontier_fixture()
        return c.frontier_start(binding, graph, lambda: True)

    def allocation(self):
        return {'resolver_bytes': 0, 'resolver_pages': 0, 'p_bytes': 0, 'p_files': 0}

    def bundle(self, state):
        return c.pack_supplied_chain(state, [], self.allocation(), lambda: True)

    def verify(self, bundle, state, allocation=None, guard=None):
        return c.verify_supplied_bundle(bundle, {'bytes': len(bundle['manifest']), 'sha256': c.digest(bundle['manifest'])},
            c.digest(c.encode(state)), state['binding'], [], allocation or self.allocation(), guard or (lambda: True))

    def rewrite(self, bundle, change):
        manifest = json.loads(bundle['manifest']); change(manifest)
        return {'manifest': c.encode(manifest), 'chunks': bundle['chunks'][:]}

    def inherited(self, name):
        getattr(FrontierTests(name), name)()

    def historical(self, family='inventory', repeated=False):
        """Fully shaped asserted records; no source parser or real evidence."""
        source = {'bytes':1,'sha256':c.digest(b'\n')}
        def descriptor(raw, ordinal=1, path=None):
            return {'schema':'cho51_lv_file_descriptor_v1','path':path or 'C:/evidence/page%d.json'%ordinal,
                'native_identity':{'schema':'cho51_lv_native_identity_v1','volume_serial':'1'*16,
                    'file_id':format(ordinal,'032x'),'volume_kind':'local_fixed','filesystem':'NTFS'},
                'file_type':'regular','reparse_point':False,'link_count':1,'bytes':len(raw),'sha256':c.digest(raw)}
        def node(path, kind, **extra):
            parent = None if path == '$' else c.digest(c.encode(['a',source['sha256'],path.rsplit('/',1)[0]]))
            result = {'id':c.digest(c.encode(['a',source['sha256'],path])),'parent':parent,'path':path,
                'scope':'$' if family == 'inventory' else c.digest(c.encode(['a',source['sha256'],'$'])),
                'kind':kind,'span_utf8':None,'raw_span_sha256':None,'epoch':'eager','module':'a','source':source}
            if family == 'inventory': result.update(scope_parent=None,shape_sha256='7'*64,context='unknown',analysis='unresolved',phase='L2')
            else: result.update(scope_kind='module',conditional=False,resolution='unresolved',capability='pending')
            result.update(extra); return result
        if family == 'inventory':
            rows = [node('$','Module')]*(256 if repeated else 1)
            diag = {'kind':'SyntaxError','message':'parser rejected source','line':9223372036854775807,
                'character_column_1based':None,'utf8_byte_column_0based':None,'end_line':None,
                'end_character_column_1based':None,'end_utf8_byte_column_0based':None}
            index = {'schema':'cho51_l_inventory_index_v1','status':'INCOMPLETE_REFUSED','pages':[],
                'diagnostics':[{'module':'broken','source':source,'diagnostic':diag}],
                'nodes':len(rows)*(2 if repeated else 1),'migration_ref':None,'launch_authorized':False,
                'candidate_imports':0,'executed_input_code':0,'unresolved':'all effects, bindings, closure and decisions'}
        else:
            root = node('$','Module'); imp = node('$/body:0','Import',effect='import')
            alias = node('$/body:0/names:0','alias',name='dep',alias=None,binding_kind='import_alias')
            expr = node('$/body:1','Expr')
            call = node('$/body:1/value','Call',effect='call_callback_dynamic',lexical_targets=[],
                import_candidate=None,runtime_binding_proven=False,possible_dynamic_effect='unresolved_callable')
            name = node('$/body:1/value/func','Name',name='opaque',binding_kind='Load',binding_candidates=[],refusal='unbound_or_builtin_unknown')
            context = node('$/body:1/value/func/ctx','Load')
            origin = {'kind':'source','module':'a','path':'C:/fixture/a.py','pin':source,
                      'physical_descriptor':descriptor(b'\n',999,'C:/fixture/a.py')}
            origin_row = {'kind':'origin','module':'a','phase':'L2','origin':origin,'via':None,'capability':'pending'}
            edge = {'kind':'edge','from':'a','to':'dep','site':imp['id'],'phase':'L2','epoch':'eager','conditional':False}
            front = {'module':'a','site':call['id'],'reason':'dynamic_call_unresolved','candidate':None}
            queue = {'module':'dep','phase':'L2','via':imp['id']}
            rows = [origin_row,root,imp,alias,expr,call,name,context,edge,dict(kind='frontier',**front),dict(kind='queued',**queue)]
            index = {'schema':'cho51_l_resolver_index_v1','status':'INCOMPLETE_REFUSED','g2_complete':False,
                'launch_authorized':False,'graph_fixed_point':False,'modules':1,'nodes':7,'module_rows':8,'published_rows':11,
                'edges':1,'source_bytes':1,'binding_count':2,'effect_count':2,'binding_frontier_count':1,'effect_frontier_count':2,
                'source_pins_sha256':c.digest(c.encode([origin])),'import_frontier_count':1,'frontier_sha256':c.digest(c.encode([front])),
                'frontier_paged':True,'queue_paged':True,'queue_count':1,'queue_sha256':c.digest(c.encode([queue])),
                'cap_refusal':None,'components':[['a']],'component_order_is_execution_grant':False,'spec_sha256':'8'*64,'pages':[]}
        def raw_json(value):
            # Only serializer-created layout newlines become CRLF. A comma in
            # a JSON string is payload, never a whitespace insertion point.
            text = json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)
            return text.replace('\n','\r\n').encode('ascii') + b'\r\n'
        page = raw_json({'schema':'cho51_l_'+family+'_page_v1','rows':rows})
        pages = [page,page] if repeated else [page]
        index['pages'] = [descriptor(raw,i+1) for i,raw in enumerate(pages)]
        raw = [{'family':family,'index':raw_json(index),'pages':pages}]
        return raw, self.evidence_pins(raw)

    def evidence_pins(self, raw):
        def pin(data): return {'bytes':len(data),'sha256':c.digest(data)}
        return [{'family':f['family'],'index':pin(f['index']),'pages':[pin(p) for p in f['pages']]} for f in raw]

    def evidence_verify(self, state, raw, expected=None):
        bundle = c.pack_supplied_chain(state,raw,self.allocation(),lambda: True)
        result = c.verify_supplied_bundle(bundle,{'bytes':len(bundle['manifest']),'sha256':c.digest(bundle['manifest'])},
            c.digest(c.encode(state)),state['binding'],self.evidence_pins(raw) if expected is None else expected,
            self.allocation(),lambda: True)
        return bundle, result

    def test_ls01_closed_schemas(self):
        state = self.state(); bundle = self.bundle(state)
        for change in (lambda x: x.update(extra=1), lambda x: x.pop('history')):
            self.assertEqual('INVALID_INPUT', self.verify(self.rewrite(bundle, change), state)['outcome'])
        for owner in ('assets','chunks','history','binding'):
            for missing in (False,True):
                def change(m, owner=owner, missing=missing):
                    obj = m[owner] if owner == 'binding' else m[owner][0]
                    if missing: obj.pop(next(iter(obj)))
                    else: obj['extra'] = None
                with self.subTest(owner=owner,missing=missing):
                    self.assertEqual('INVALID_INPUT',self.verify(self.rewrite(bundle,change),state)['outcome'])
        raw, pins = self.historical()
        index = json.loads(raw[0]['index']); index['pages'][0]['extra'] = 1
        bad = [{'family':'inventory','index':c.encode(index),'pages':raw[0]['pages']}]
        with self.assertRaises(c.Refusal): c._ls_evidence(self.evidence_pins(bad),bad,lambda: True)

    def test_ls02_types_duplicate_keys(self):
        for raw in (b'{"a":1,"a":2}', b'[1.0]', b'9223372036854775808', b'1 trailing'):
            with self.subTest(raw=raw), self.assertRaises(c.Refusal): c._ls_json(raw, lambda: True)
        self.assertIs(c._ls_json(b'true', lambda: True), True)
        state = self.state(); bundle = self.bundle(state)
        for change in (lambda m:m['chunks'][0].update(ordinal=False),lambda m:m['assets'][0].update(bytes=True),
                       lambda m:m['history'][0].update(bytes=1.0),lambda m:m['assets'][0].update(sha256='A'*64)):
            self.assertEqual('INVALID_INPUT',self.verify(self.rewrite(bundle,change),state)['outcome'])

    def test_ls03_roundtrip_exact(self):
        state = self.state(); result = self.verify(self.bundle(state), state)
        self.assertEqual('VERIFIED_SUPPLIED_STATE', result['outcome']); self.assertEqual(c.encode(state), c.encode(result['snapshot']))
        self.assertEqual({'v': 9223372036854775807}, c._ls_json(b'{\r\n "v": 9223372036854775807\r\n}', lambda: True))
        raw, pins = self.historical()
        self.assertEqual('all effects, bindings, closure and decisions',json.loads(raw[0]['index'])['unresolved'])
        self.assertIn(b'all effects, bindings, closure and decisions',raw[0]['index'])
        bundle, result = self.evidence_verify(state,raw)
        self.assertEqual('VERIFIED_SUPPLIED_STATE',result['outcome'])
        manifest = json.loads(bundle['manifest']); physical = b''.join(bundle['chunks'])
        assets = {a['id']:b''.join(bundle['chunks'][p['chunk']][p['offset']:p['offset']+p['bytes']] for p in a['parts']) for a in manifest['assets']}
        self.assertEqual(raw[0]['index'],assets[manifest['evidence'][0]['index_asset']])
        self.assertEqual(raw[0]['pages'][0],assets[manifest['evidence'][0]['page_assets'][0]])
        self.assertIn(b'9223372036854775807',physical); self.assertIn(b'\r\n',physical)
        for value in ({'unicode':'\U0001f642\ud800','signed':-(2**63)},state):
            self.assertEqual(c.encode(value),c._ls_encode(value,lambda: True))

    def test_ls04_kind_separation(self):
        pin = c.digest(b'x')
        self.assertNotEqual(c.digest(c.encode(['asset','graph',1,pin])), c.digest(c.encode(['asset','raw',1,pin])))
        state = self.state(); self.assertEqual(self.bundle(state), self.bundle(state))
        bundle = self.bundle(state)
        self.assertEqual('INVALID_INPUT',self.verify(self.rewrite(bundle,lambda m:m.update(graph=m['frames'][0])),state)['outcome'])
        raw, pins = self.historical(repeated=True)
        raw[0]['pages'][1] = raw[0]['pages'][1].replace(b'\r\n',b'\n ',1)
        index = json.loads(raw[0]['index'])
        index['pages'][1]['sha256'] = c.digest(raw[0]['pages'][1]); raw[0]['index'] = c.encode(index)
        original = c._ls_asset_id
        def collide(kind,size,sha,guard):
            return '1'*64 if kind == 'raw' and size == len(raw[0]['pages'][0]) else original(kind,size,sha,guard)
        try:
            c._ls_asset_id = collide
            with self.assertRaisesRegex(c.Refusal,'collision'):
                c.pack_supplied_chain(state,raw,self.allocation(),lambda: True)
        finally: c._ls_asset_id = original

    def test_ls05_assets_and_families(self):
        state = self.state(); bundle = self.bundle(state)
        for change in (lambda m: m['assets'].append(m['assets'][0]), lambda m: m['frames'].append('0'*64)):
            self.assertEqual('INVALID_INPUT', self.verify(self.rewrite(bundle, change), state)['outcome'])
        out = c.verify_supplied_bundle(bundle, {'bytes': len(bundle['manifest']), 'sha256': c.digest(bundle['manifest'])},
            c.digest(c.encode(state)), state['binding'], [{'family':'resolver','index':{},'pages':[]}], self.allocation(), lambda: True)
        self.assertEqual('INVALID_INPUT', out['outcome'])

    def test_ls06_partition_and_chunks(self):
        state = self.state(); bundle = self.bundle(state)
        bad = self.rewrite(bundle, lambda m: m['assets'][0]['parts'][0].update(offset=1))
        self.assertEqual('INVALID_INPUT', self.verify(bad, state)['outcome'])
        self.assertEqual('INVALID_INPUT', self.verify({'manifest':bundle['manifest'], 'chunks':[bundle['chunks'][0]+b'x']}, state)['outcome'])
        for change in (lambda m:m['assets'][0]['parts'][0].update(bytes=1),
                       lambda m:m['assets'].reverse(),lambda m:m['assets'][0]['parts'].append(m['assets'][0]['parts'][0])):
            self.assertEqual('INVALID_INPUT',self.verify(self.rewrite(bundle,change),state)['outcome'])

    def test_ls07_descriptor_count(self):
        state = self.state(); bundle = self.bundle(state)
        bad = self.rewrite(bundle, lambda m: m['assets'].extend([m['assets'][0]]*512))
        self.assertEqual('INVALID_INPUT', self.verify(bad, state)['outcome'])
        bad = {'manifest':bundle['manifest'], 'chunks':[b'x']*65}
        self.assertEqual('INVALID_INPUT',self.verify(bad,state)['outcome'])
        binding, graph = frontier_fixture({'a':[]}); module = graph['modules'][0]; module['nodes'] = 20
        module['records'] = []
        for i in range(20):
            payload = {'text':str(i).zfill(2) + 'x'*54998}
            module['records'].append({'id':c.frontier_id('record','a',i,payload),'payload':payload})
        large = c.frontier_start(binding,graph,lambda: True); transport = self.bundle(large)
        self.assertEqual(1024*1024,len(transport['chunks'][0])); self.assertEqual(2,len(transport['chunks']))
        self.assertEqual(large,self.verify(transport,large)['snapshot'])
        old = c.FRONTIER_LIMITS['file_bytes']
        try:
            c.FRONTIER_LIMITS['file_bytes'] = 4096
            with self.assertRaises(c.Refusal): c._ls_json(b'"'+b'x'*4095+b'"',lambda: True)
        finally: c.FRONTIER_LIMITS['file_bytes'] = old
        # One actual nominal 8MiB input boundary; no giant semantic fixture.
        exact = b'0'+b' '*(8*1024**2-1)
        self.assertEqual(0,c._ls_json(exact,lambda: True))
        with self.assertRaisesRegex(c.Refusal,'JSON size'): c._ls_json(exact+b' ',lambda: True)
        for count in (512,513):
            bad = self.rewrite(bundle,lambda m,count=count:m.update(assets=[m['assets'][0]]*count))
            outcome = self.verify(bad,state)
            self.assertEqual('INVALID_INPUT',outcome['outcome'])
            self.assertEqual(count == 513,outcome['reason'] == 'manifest counts')
        bad = self.rewrite(bundle,lambda m:m['assets'][0].update(parts=[m['assets'][0]['parts'][0]]*1025))
        self.assertEqual('INVALID_INPUT',self.verify(bad,state)['outcome'])

    def test_ls08_binding_and_manifest_pin(self):
        state = self.state(); bundle = self.bundle(state)
        bad = self.rewrite(bundle, lambda m: m['binding'].update(source='f'*64))
        self.assertEqual('INVALID_INPUT', self.verify(bad, state)['outcome'])
        out = c.verify_supplied_bundle(bundle, {'bytes':len(bundle['manifest']), 'sha256':'0'*64}, c.digest(c.encode(state)), state['binding'], [], self.allocation(), lambda: True)
        self.assertEqual('INVALID_INPUT', out['outcome'])
        for key in ('source','runtime','spec','roots','predecessor'):
            expected = dict(state['binding']); expected[key] = 'e'*64
            result = c.verify_supplied_bundle(bundle,{'bytes':len(bundle['manifest']),'sha256':c.digest(bundle['manifest'])},
                c.digest(c.encode(state)),expected,[],self.allocation(),lambda: True)
            with self.subTest(key=key): self.assertEqual('INVALID_INPUT',result['outcome'])
        result = c.verify_supplied_bundle(bundle,{'bytes':len(bundle['manifest']),'sha256':c.digest(bundle['manifest'])},
            '0'*64,state['binding'],[],self.allocation(),lambda: True)
        self.assertEqual('INVALID_INPUT',result['outcome'])

    def test_ls09_expected_family(self):
        state = self.state(); bundle = self.bundle(state)
        with self.assertRaises(c.Refusal): c._ls_evidence([{'family':'inventory','index':{},'pages':[]}], [], lambda: True)
        self.assertEqual('VERIFIED_SUPPLIED_STATE', self.verify(bundle, state)['outcome'])
        raw, pins = self.historical(repeated=True)
        bundle, result = self.evidence_verify(state,raw)
        uses = json.loads(bundle['manifest'])['evidence'][0]['page_assets']; self.assertEqual(uses[0],uses[1])
        self.assertEqual('VERIFIED_SUPPLIED_STATE',result['outcome'])
        pins[0]['pages'][0]['sha256'] = '0'*64
        result = c.verify_supplied_bundle(bundle,{'bytes':len(bundle['manifest']),'sha256':c.digest(bundle['manifest'])},
            c.digest(c.encode(state)),state['binding'],pins,self.allocation(),lambda: True)
        self.assertEqual('INVALID_INPUT',result['outcome'])

    def test_ls10_payload_preservation(self):
        binding, graph = frontier_fixture(debts=[('effect', {'effect': {'call':'opaque'}})])
        state = c.frontier_start(binding, graph, lambda: True)
        self.assertEqual(state, self.verify(self.bundle(state), state)['snapshot'])
        raw, pins = self.historical('resolver'); bundle, result = self.evidence_verify(state,raw)
        self.assertEqual('VERIFIED_SUPPLIED_STATE',result['outcome'])
        index = json.loads(raw[0]['index']); page = json.loads(raw[0]['pages'][0])
        # Exact retained emitter values; these are supplied rows, not source parsing.
        generator = dict(page['rows'][4],kind='GeneratorExp',effect='generator_protocol')
        multiple = dict(page['rows'][6],refusal='multiple_bindings')
        annotation = dict(page['rows'][6],epoch='future_annotation_unknown')
        for row,key,bad_value in ((generator,'effect','comprehension_protocol'),
                                  (multiple,'refusal','multiple_binding'),
                                  (annotation,'epoch','future_annotation_known')):
            with self.subTest(field=key):
                c._ls_node(row,'resolver',lambda: True)
                with self.assertRaises(c.Refusal):
                    c._ls_node(dict(row,**{key:bad_value}),'resolver',lambda: True)
        original_origin = page['rows'][0]['origin']
        for kind in ('extension','extension_package'):
            native = frontier_clone(original_origin); native['kind'] = kind
            native['pin']['bytes'] = 8*1024**2+1
            native['physical_descriptor']['bytes'] = native['pin']['bytes']
            with self.subTest(kind=kind):
                c._ls_origin(native,'a',lambda: True)
                for bad_value in (True,-1,2**63):
                    bad = frontier_clone(native); bad['pin']['bytes'] = bad_value
                    with self.assertRaises(c.Refusal): c._ls_origin(bad,'a',lambda: True)
                bad = frontier_clone(native); bad['physical_descriptor']['bytes'] -= 1
                with self.assertRaises(c.Refusal): c._ls_origin(bad,'a',lambda: True)
                bad = frontier_clone(native); bad['pin']['sha256'] = '0'*64
                with self.assertRaises(c.Refusal): c._ls_origin(bad,'a',lambda: True)
                for source_kind in ('source','package'):
                    bad = frontier_clone(native); bad['kind'] = source_kind
                    with self.assertRaises(c.Refusal): c._ls_origin(bad,'a',lambda: True)
        for change in (lambda p:p['rows'][3].pop('binding_kind'), lambda p:p['rows'][5].pop('effect'),
                       lambda p:p['rows'][6].update(binding_candidates=['0'*64]),lambda p:p['rows'][2].update(parent='0'*64),
                       lambda p:p['rows'][1].update(unexpected=1),lambda p:p['rows'][9].update(candidate={'digest':'0'*64})):
            altered = json.loads(c.encode(page)); change(altered)
            badpage = c.encode(altered); altered_index = json.loads(c.encode(index))
            altered_index['pages'][0].update(bytes=len(badpage),sha256=c.digest(badpage))
            bad = [{'family':'resolver','index':c.encode(altered_index),'pages':[badpage]}]
            with self.subTest(change=change), self.assertRaises(c.Refusal): c._ls_evidence(self.evidence_pins(bad),bad,lambda: True)
        for key,value in (('graph_fixed_point',True),('components',[]),('cap_refusal','max_modules'),
                          ('binding_count',1),('source_bytes',2),('queue_sha256','0'*64)):
            altered_index = dict(index); altered_index[key] = value
            bad = [{'family':'resolver','index':c.encode(altered_index),'pages':raw[0]['pages']}]
            with self.subTest(key=key), self.assertRaises(c.Refusal): c._ls_evidence(self.evidence_pins(bad),bad,lambda: True)

    def test_ls11_prefix_history(self):
        state = self.state(); advanced = c.frontier_continue(state,c.digest(c.encode(state)),state['binding'],1,[True],lambda: True)['snapshot']
        bundle = self.bundle(advanced); self.assertEqual(c.digest(c.encode(state)), json.loads(bundle['manifest'])['history'][0]['sha256'])
        for prefix, descriptor in zip((state,advanced),json.loads(bundle['manifest'])['history']):
            self.assertEqual(c.encode(prefix),c._ls_encode(prefix,lambda: True))
            self.assertEqual({'bytes':len(c.encode(prefix)),'sha256':c.digest(c.encode(prefix))},
                             {k:descriptor[k] for k in ('bytes','sha256')})
        self.assertEqual(advanced, self.verify(bundle, advanced)['snapshot'])
        def padded(count):
            binding, graph = frontier_fixture(); record = graph['modules'][0]['records'][0]
            record['payload']['pad'] = 'x'*count
            record['id'] = c.frontier_id('record','a',0,record['payload'])
            return c.frontier_start(binding,graph,lambda: True)
        baseline = len(c.encode(padded(0)))
        for size in (9999,10000):
            initial = padded(size-baseline); self.assertEqual(size,len(c.encode(initial)))
            successor = c.frontier_continue(initial,c.digest(c.encode(initial)),initial['binding'],1,[True],lambda: True)['snapshot']
            self.assertEqual(size,successor['frames'][1]['retained_before'])
            self.assertEqual(successor,self.verify(self.bundle(successor),successor)['snapshot'])

    def test_ls12_expanded_accounting(self):
        self.inherited('test_fc18_complete_row_accounting')
        state = self.state(); bundle = self.bundle(state)
        self.assertEqual(state, self.verify(bundle,state)['snapshot'])
        old = c.FRONTIER_LIMITS['rows']
        try:
            c.FRONTIER_LIMITS['rows'] = 11
            self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,state)['outcome'])
        finally: c.FRONTIER_LIMITS['rows'] = old
    def test_ls13_capacity_controls(self):
        self.inherited('test_fc20_edge_page_and_serialized_caps')
        state = self.state(); bundle = self.bundle(state)
        old = c.FRONTIER_LIMITS['edges']
        try:
            c.FRONTIER_LIMITS['edges'] = 1
            self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,state)['outcome'])
        finally: c.FRONTIER_LIMITS['edges'] = old
        synthetic = frontier_clone(state); synthetic['graph']['modules'] = synthetic['graph']['modules'][:1]
        module = synthetic['graph']['modules'][0]; module['records'] = [None]*23993; module['edges'] = []
        self.assertGreater(c._frontier_capacity(synthetic,0,lambda: True),0)
        module['records'].append(None)
        with self.assertRaisesRegex(c.Refusal,'capacity: rows'): c._frontier_capacity(synthetic,0,lambda: True)
        module['records'] = []
        self.assertGreater(c._frontier_capacity(synthetic,9999,lambda: True),0)
        with self.assertRaisesRegex(c.Refusal,'capacity: edges'): c._frontier_capacity(synthetic,10000,lambda: True)
    def test_ls14_history_bytes(self):
        self.inherited('test_fc21_chain_count_and_byte_caps')
        state = self.state(); bundle = self.bundle(state); old = c.FRONTIER_LIMITS['history_bytes']
        try:
            c.FRONTIER_LIMITS['history_bytes'] = len(c.encode(state))-1
            self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,state)['outcome'])
        finally: c.FRONTIER_LIMITS['history_bytes'] = old
        # The pre-expansion lower bound counts repeated frame references before
        # parsing copies; use a reduced history cap, without a huge fixture.
        manifest = json.loads(bundle['manifest']); sizes = {a['id']:a['bytes'] for a in manifest['assets']}
        lower = 128*sizes[manifest['graph']] + sum(range(1,129))*sizes[manifest['frames'][0]]
        repeated = self.rewrite(bundle,lambda m:m.update(frames=m['frames']*128,history=m['history']*128))
        try:
            c.FRONTIER_LIMITS['history_bytes'] = lower-1
            result = self.verify(repeated,state)
            self.assertEqual('CAPACITY_REFUSED',result['outcome']); self.assertEqual('capacity: expanded asset bytes',result['reason'])
        finally: c.FRONTIER_LIMITS['history_bytes'] = old
    def test_ls15_structural_payload(self):
        self.inherited('test_fc02_exact_types_and_identifiers')
        state = self.state(); state['graph']['modules'][0]['records'][0]['payload'] = {'number': 1.5}
        with self.assertRaises(c.Refusal): self.bundle(state)
    def test_ls16_history_identity(self):
        state = self.state(); bad = self.rewrite(self.bundle(state), lambda m: m['history'][0].update(sequence=1))
        self.assertEqual('INVALID_INPUT', self.verify(bad, state)['outcome']); self.inherited('test_fc24_sequence_predecessor_and_graph_drift')
    def test_ls17_intermediate_capacity(self):
        self.inherited('test_fc17_atomic_cap_refusal')
        state = self.state(); state = c.frontier_continue(state,c.digest(c.encode(state)),state['binding'],1,[True],lambda: True)['snapshot']
        bundle = self.bundle(state); old = c.FRONTIER_LIMITS['rows']
        try:
            c.FRONTIER_LIMITS['rows'] = 18
            self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,state)['outcome'])
        finally: c.FRONTIER_LIMITS['rows'] = old
        binding, graph = frontier_fixture({'a':[],'b':[]},[('a','L2'),('b','L2')])
        initial = c.frontier_start(binding,graph,lambda: True)
        endpoint = c.frontier_continue(initial,c.digest(c.encode(initial)),binding,2,[True,True],lambda: True)['snapshot']
        bundle = self.bundle(endpoint); old = c.FRONTIER_LIMITS['rows']
        try:
            c.FRONTIER_LIMITS['rows'] = 35
            self.assertGreater(c._frontier_capacity(endpoint,0,lambda: True),0)
            # After the first work-item removal rows=36; final rows=35.
            self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,endpoint)['outcome'])
            with self.assertRaisesRegex(c.Refusal,'capacity: rows'): self.bundle(endpoint)
        finally: c.FRONTIER_LIMITS['rows'] = old
    def test_ls18_cycles_debts_blocked(self):
        for name in ('test_fc09_diamond_preserves_links','test_fc10_cycle_is_finite_and_propagates','test_fc12_missing_origin_blocks','test_fc13_all_debt_kinds_preserved'):
            with self.subTest(name=name): self.inherited(name)
        binding, graph = frontier_fixture({'a':['b'],'b':['a']},debts=[('effect',{'effect':'unresolved'})])
        state = c.frontier_start(binding,graph,lambda: True)
        state = c.frontier_continue(state,c.digest(c.encode(state)),binding,2,[True,True],lambda: True)['snapshot']
        self.assertEqual(state,self.verify(self.bundle(state),state)['snapshot'])
    def test_ls19_no_mutation(self):
        state = self.state(); before = c.encode(state); result = self.verify(self.bundle(state),state)
        result['snapshot']['frames'].clear(); self.assertEqual(before,c.encode(state)); self.inherited('test_fc28_no_input_or_output_aliasing')
    def test_ls20_source_limits(self):
        self.inherited('test_fc19_module_source_node_depth_limits')
        state = self.state(); state['graph']['modules'][0]['source_bytes'] = 2*1024**2+1
        with self.assertRaises(c.Refusal): self.bundle(state)
    def test_ls21_live_guard(self):
        state = self.state(); bundle = self.bundle(state)
        with self.assertRaises(c.LosslessCheckpointRefusal): self.verify(bundle,state,guard=lambda: False)
        with self.assertRaises(c.LosslessCheckpointRefusal): c.pack_supplied_chain(state,[],self.allocation(),lambda: False)
        count = [0]
        def delayed():
            count[0] += 1
            return count[0] < 20
        with self.assertRaises(c.LosslessCheckpointRefusal): self.verify(bundle,state,guard=delayed)
        self.assertEqual(20,count[0])
        count = [0]
        def tally(): count[0] += 1; return True
        self.assertEqual('VERIFIED_SUPPLIED_STATE',self.verify(bundle,state,guard=tally)['outcome'])
        final_call = count[0]; count[0] = 0
        def late(): count[0] += 1; return count[0] < final_call
        with self.assertRaises(c.LosslessCheckpointRefusal): self.verify(bundle,state,guard=late)
        before = c.encode(state)
        for operation in (lambda guard:c._ls_hash(b'x'*131073,guard),
                          lambda guard:c._ls_encode({'text':'x'*65536},guard),
                          lambda guard:c._ls_json(b'0'+b' '*131073,guard)):
            count[0] = 0
            def during(): count[0] += 1; return count[0] < 3
            with self.subTest(operation=operation), self.assertRaises(c.LosslessCheckpointRefusal): operation(during)
        def exception(): raise RuntimeError('stop fixture')
        with self.assertRaises(c.LosslessCheckpointRefusal): self.verify(bundle,state,guard=exception)
        original = c._frontier_verify; in_replay = [False]
        def marked(*args):
            in_replay[0] = True
            try: return original(*args)
            finally: in_replay[0] = False
        try:
            c._frontier_verify = marked
            with self.assertRaises(c.LosslessCheckpointRefusal): self.verify(bundle,state,guard=lambda: not in_replay[0])
        finally: c._frontier_verify = original
        self.assertEqual(before,c.encode(state))
    def test_ls22_no_authority(self):
        state = self.state(); result = self.verify(self.bundle(state),state)
        for key in ('g2_complete','launch_authorized','capabilities_accepted','scientific_admission'): self.assertIs(result[key],False)
    def test_ls23_lower_bound_arithmetic(self):
        state = self.state(); advanced = c.frontier_continue(state,c.digest(c.encode(state)),state['binding'],1,[True],lambda: True)['snapshot']
        graph = state['graph']; base = 2*len(graph['modules'])+len(graph['seeds'])+len(graph['obligations'])
        base += sum(len(m['records'])+len(m['edges']) for m in graph['modules'])
        old = c.FRONTIER_LIMITS['rows']
        try:
            c.FRONTIER_LIMITS['rows'] = 2*base
            with self.assertRaises(c.Refusal): self.bundle(advanced)
        finally: c.FRONTIER_LIMITS['rows'] = old
        # Direct counter-path witnesses, deliberately not valid graphs or real
        # reconstructed records. Their list multiplicities enter the unchanged
        # capacity function before serialization; no 15k-record replay is needed.
        synthetic = frontier_clone(state); synthetic['graph']['modules'][0]['records'] = [None]*15498
        synthetic['graph']['modules'][0]['edges'] = []; synthetic['graph']['obligations'] = []
        synthetic['graph']['modules'] = synthetic['graph']['modules'][:1]
        synthetic['graph']['seeds'] = synthetic['graph']['seeds'][:1]
        synthetic['frames'] = synthetic['frames'][:1]
        self.assertGreater(c._frontier_capacity(synthetic,0,lambda: True),0)
        synthetic['frames'].append(frontier_clone(synthetic['frames'][0]))
        with self.assertRaisesRegex(c.Refusal,'capacity: rows'): c._frontier_capacity(synthetic,0,lambda: True)
        synthetic['frames'] = synthetic['frames'][:1]
        module = synthetic['graph']['modules'][0]; module['records'] = [None]*14446
        synthetic['graph']['modules'].append(dict(module,records=[None]*14446))
        with self.assertRaisesRegex(c.Refusal,'capacity: rows'): c._frontier_capacity(synthetic,0,lambda: True)
    def test_ls24_allocation(self):
        state = self.state(); bundle = self.bundle(state)
        size = len(bundle['manifest']) + sum(map(len,bundle['chunks'])); files = 1 + len(bundle['chunks'])
        for key,value in (('resolver_bytes',16*1024**2-size),('resolver_pages',100-files),
                          ('p_bytes',64*1024**2-size),('p_files',256-files)):
            allocation = self.allocation(); allocation[key] = value
            if key == 'resolver_bytes': allocation['p_bytes'] = value + 1
            if key == 'resolver_pages': allocation['p_files'] = value + 1
            with self.subTest(key=key):
                self.assertEqual('VERIFIED_SUPPLIED_STATE',self.verify(bundle,state,allocation=allocation)['outcome'])
                allocation[key] += 1
                self.assertEqual('CAPACITY_REFUSED',self.verify(bundle,state,allocation=allocation)['outcome'])
        allocation = self.allocation(); allocation['p_files'] = 1
        self.assertEqual('VERIFIED_SUPPLIED_STATE',self.verify(bundle,state,allocation=allocation)['outcome'])
        allocation = self.allocation(); allocation['resolver_bytes'] = 1
        self.assertEqual('INVALID_INPUT',self.verify(bundle,state,allocation=allocation)['outcome'])
    def test_ls25_refusal_result(self):
        state = self.state(); bad = self.rewrite(self.bundle(state),lambda m:m.update(status='ok')); result = self.verify(bad,state)
        self.assertIsNone(result['snapshot']); self.assertIsNone(result['logical_digest']); self.assertEqual(['external_and_allocation'],result['checks_completed'])
    def test_ls26_path_is_inert(self):
        self.assertEqual('C:/bad/../file',c._ls_json(b'{"path":"C:/bad/../file"}',lambda: True)['path'])
        raw, pins = self.historical(); index = json.loads(raw[0]['index'])
        for path in ('C:/bad/../file','C:/CON.json','C:/bad/file.','C:/bad/*','//remote/share/file','C:/bad/COM1.log'):
            bad_index = json.loads(c.encode(index)); bad_index['pages'][0]['path'] = path
            bad = [{'family':'inventory','index':c.encode(bad_index),'pages':raw[0]['pages']}]
            with self.subTest(path=path),self.assertRaises(c.Refusal): c._ls_evidence(self.evidence_pins(bad),bad,lambda: True)
    def test_ls27_supplied_result_schema(self):
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        prefix = 'tools.local_validation.lplan15.test_compiler.'
        names = [prefix+cls.__name__+'.'+name for cls in (ResolverTests,FrontierTests,LosslessTests)
                 for name in dir(cls) if name.startswith('test_')]
        self.assertEqual('lossless',protocol.qualification_cohort(names))
        inherited_name = 'tools.local_validation.lq18.test_protocol.ProtocolTests.test_complete_window'
        for bad in (names[:-1],names+names[:1],names[:-1]+[inherited_name]):
            with self.assertRaises(ValueError): protocol.qualification_cohort(bad)
        # Admission/report/control integration is exercised by the separately
        # discovered inherited ProtocolTests.test_complete_window and
        # test_report_omissions_failures_and_false_authority; this method tests
        # this exact new100 roster rather than duplicating those controls.
    def test_ls28_no_execution_authority(self):
        supervisor = sys.modules['tools.local_validation.lp18.supervisor']
        with self.assertRaisesRegex(ValueError,'Q-library-only'): supervisor.main(None,None,None,None,None)
        fixture_module = sys.modules['tools.local_validation.lp18.test_protocol']
        protocol = sys.modules['tools.local_validation.lp18.protocol']
        request, review, adoption, qualification, coverage, source, actual, mapping, plan = fixture_module.fixtures()
        aggregate, material = fixture_module.aggregate_fixture(request,qualification,source,actual)
        self.assertEqual([384,40],protocol.validate_aggregate(request,aggregate,material,qualification)['counts'])
        aggregate['schema'] = 'cho51_lossless_q_aggregate_v1'; aggregate['expected_counts']['resolver'] = 100
        with self.assertRaises(protocol.r.Refusal): protocol.validate_aggregate(request,aggregate,material,qualification)


def source_probe_fixture():
    """Exact supplied fixture; no runtime path access."""
    source = bytes.fromhex(
        '2320546869732066696c65206973206475616c206c6963656e73656420756e64657220746865207465726d73206f662074686520417061636865204c'
        '6963656e73652c2056657273696f6e0a2320322e302c20616e642074686520425344204c6963656e73652e2053656520746865204c4943454e534520'
        '66696c6520696e2074686520726f6f74206f662074686973207265706f7369746f72790a2320666f7220636f6d706c6574652064657461696c732e0a'
        '0a5f5f7469746c655f5f203d20227061636b6167696e67220a5f5f73756d6d6172795f5f203d2022436f7265207574696c697469657320666f722050'
        '7974686f6e207061636b61676573220a5f5f7572695f5f203d202268747470733a2f2f6769746875622e636f6d2f707970612f7061636b6167696e67'
        '220a0a5f5f76657273696f6e5f5f203d202232362e33220a0a5f5f617574686f725f5f203d2022446f6e616c642053747566667420616e6420696e64'
        '6976696475616c20636f6e7472696275746f7273220a5f5f656d61696c5f5f203d2022646f6e616c64407374756666742e696f220a0a5f5f6c696365'
        '6e73655f5f203d20224253442d322d436c61757365206f72204170616368652d322e30220a5f5f636f707972696768745f5f203d2066223230313420'
        '7b5f5f617574686f725f5f7d220a'
    )
    index = bytes.fromhex(
        '7b2262696e64696e675f636f756e74223a343735362c2262696e64696e675f66726f6e746965725f636f756e74223a313738362c226361705f726566'
        '7573616c223a22726f77735f6f725f6564676573222c22636f6d706f6e656e745f6f726465725f69735f657865637574696f6e5f6772616e74223a66'
        '616c73652c22636f6d706f6e656e7473223a5b5b22627261696e6465636f6465225d2c5b22636f6c6f72616d61225d2c5b226576616c756174696f6e'
        '225d2c5b22696e69636f6e666967225d2c5b226d6e65225d2c5b226e756d7079225d2c5b227061636b6167696e67225d2c5b22706c75676779225d2c'
        '5b22707974657374225d2c5b227361666574656e736f7273225d2c5b227361666574656e736f72732e746f726368225d2c5b227363697079225d2c5b'
        '22736b6c6561726e225d2c5b22746f726368225d2c5b22746f726368617564696f225d5d2c226564676573223a3738362c226566666563745f636f75'
        '6e74223a333937322c226566666563745f66726f6e746965725f636f756e74223a333937322c2266726f6e746965725f7061676564223a747275652c'
        '2266726f6e746965725f736861323536223a226266306639363936336362313066326138303134393436353130633064623633326362393739616634'
        '6535613434323339336332356635653033383232336461222c2267325f636f6d706c657465223a66616c73652c2267726170685f66697865645f706f'
        '696e74223a66616c73652c22696d706f72745f66726f6e746965725f636f756e74223a313738322c226c61756e63685f617574686f72697a6564223a'
        '66616c73652c226d6f64756c655f726f7773223a31353530312c226d6f64756c6573223a31352c226e6f646573223a31353438362c22706167657322'
        '3a5b7b226279746573223a3136323037302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e617469'
        '76655f6964656e74697479223a7b2266696c655f6964223a223964376235663030303030303032303030303030303030303030303030303030222c22'
        '66696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c2276'
        '6f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333356165326622'
        '7d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32'
        '303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d72'
        '65736f6c7665722d3030302e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66'
        '696c655f64657363726970746f725f7631222c22736861323536223a2266613837373537373434383561663662626139356465303835623066663766'
        '646134316534383037623863323335343432333262303730313631386533343730227d2c7b226279746573223a3136363636392c2266696c655f7479'
        '7065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2239'
        '65376235663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61'
        '223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c'
        '22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e'
        '732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f336433653163'
        '39622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3030312e6a736f6e222c2272657061727365'
        '5f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536'
        '223a22616333333230643730316166386535646161303338346338376536393633326438353030313137386631653530353439656561626437393266'
        '39383666636136227d2c7b226279746573223a3137313833302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e7422'
        '3a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22396637623566303030303030303230303030303030303030303030'
        '3030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974'
        '795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137633335663637'
        '63333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265'
        '736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932'
        '613739352f6c2d7265736f6c7665722d3030322e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a226368'
        '6f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223337613036343764326463643434663439663437366239'
        '3332616663303432363164646637653365333032376366393437343433326235346333653636343936227d2c7b226279746573223a3136383135332c'
        '2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c'
        '655f6964223a226130376235663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e54465322'
        '2c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c'
        '5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f'
        '70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074'
        '732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3030332e6a736f6e222c'
        '22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f763122'
        '2c22736861323536223a2266376236313031623530623934666431383561366435393337613464363333353435343235323638616665343461356364'
        '343461646232393766653530623262227d2c7b226279746573223a3137303930342c2266696c655f74797065223a22726567756c6172222c226c696e'
        '6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2261323762356630303030303030323030303030'
        '30303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e6174697665'
        '5f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237'
        '613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f'
        '35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d'
        '6362646461363932613739352f6c2d7265736f6c7665722d3030342e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368'
        '656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22626265363636353135396363633039'
        '34666337393539356563393165663135626536636339323730623365336538393530626663363134336432666432363539227d2c7b22627974657322'
        '3a3137373132352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e746974'
        '79223a7b2266696c655f6964223a226133376235663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d'
        '223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64'
        '223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22'
        '443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f7032'
        '2f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3030'
        '352e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f646573637269'
        '70746f725f7631222c22736861323536223a226233306264633937646365633231323736303433306561353038316635303465366530306465333564'
        '6235323835326165316464326364363433313365323264227d2c7b226279746573223a3136373230312c2266696c655f74797065223a22726567756c'
        '6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a226134376235663030303030'
        '303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c'
        '765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f7365'
        '7269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e61'
        '74696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d3431'
        '62342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3030362e6a736f6e222c22726570617273655f706f696e74223a6661'
        '6c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2266303439303230'
        '336663386230656434663738353631633664373632386361666433653639356331356661356565663431313961633131653463393164353236227d2c'
        '7b226279746573223a3136363533302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e6174697665'
        '5f6964656e74697479223a7b2266696c655f6964223a223132376335663030303030303032303030303030303030303030303030303030222c226669'
        '6c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c'
        '756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c'
        '2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f323032'
        '36313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d726573'
        '6f6c7665722d3030372e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c'
        '655f64657363726970746f725f7631222c22736861323536223a22623035386564346530613864666233326538343430386136373332353834356438'
        '64663230393362333361383434623332616630383836386466303363623938227d2c7b226279746573223a3136313432392c2266696c655f74797065'
        '223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22313337'
        '6335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a'
        '2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c2276'
        '6f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f'
        '636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f3364336531633962'
        '2d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3030382e6a736f6e222c22726570617273655f70'
        '6f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a'
        '223338343764346361323963386262353265653464623265323266633636386363636263623633633339616435393963393230663661653065306436'
        '3463343731227d2c7b226279746573223a3136363735362c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a31'
        '2c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223134376335663030303030303032303030303030303030303030303030'
        '303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f'
        '7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333'
        '3561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f'
        '6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464613639326137'
        '39352f6c2d7265736f6c7665722d3030392e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35'
        '315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2265326638353034393436323165616264323537663437373363'
        '373334343238336636666337333262363132313136643938666334336231663466383531393430227d2c7b226279746573223a3136363936392c2266'
        '696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f'
        '6964223a223135376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22'
        '736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f66'
        '69786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f7072'
        '6f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f'
        '33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031302e6a736f6e222c2272'
        '6570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22'
        '736861323536223a22626361326534653335353361316339323735633035326332393765653633373330326434633039313937666262356238643765'
        '39313562646365653137376365227d2c7b226279746573223a3136353330352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f'
        '636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22313637633566303030303030303230303030303030'
        '3030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f69'
        '64656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137'
        '63333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f3531'
        '5f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362'
        '646461363932613739352f6c2d7265736f6c7665722d3031312e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d'
        '61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223765626437653962333534623638343034'
        '3531346364643931666635396139323238306563626338333361363432646230393336373336613237626535653264227d2c7b226279746573223a31'
        '36313831362c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e7469747922'
        '3a7b2266696c655f6964223a223137376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a'
        '224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a'
        '226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a'
        '2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f61'
        '7474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031322e'
        '6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f6465736372697074'
        '6f725f7631222c22736861323536223a2264356336383138313930386536343438386565326235656464383562376665363861313933613735353035'
        '666138386233633233346234333137616665303563227d2c7b226279746573223a3136353436382c2266696c655f74797065223a22726567756c6172'
        '222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2231383763356630303030303030'
        '32303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f'
        '6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269'
        '616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e617469'
        '6f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d34316234'
        '2d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031332e6a736f6e222c22726570617273655f706f696e74223a66616c73'
        '652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22396662333832353361'
        '33366564616162303363383366356138646163303139386137353439663034366237353738666339346435633063323933363466646265227d2c7b22'
        '6279746573223a3136373834382c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f69'
        '64656e74697479223a7b2266696c655f6964223a223139376335663030303030303032303030303030303030303030303030303030222c2266696c65'
        '73797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d'
        '655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270'
        '617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f3230323631'
        '3033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c'
        '7665722d3031342e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f'
        '64657363726970746f725f7631222c22736861323536223a223962316135383534643166393539386637306164616366353532373333373830383732'
        '3536336332383338386530396632376135646338633666343639346266227d2c7b226279746573223a3136373138382c2266696c655f74797065223a'
        '22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223161376335'
        '663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263'
        '686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c'
        '756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f'
        '6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d32'
        '6266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031352e6a736f6e222c22726570617273655f706f69'
        '6e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2234'
        '396465633261316261373730633163393566366564366137633631353530653966353234643334356361323534323736613032653630643835643732'
        '316265227d2c7b226279746573223a3136353939312c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c22'
        '6e61746976655f6964656e74697479223a7b2266696c655f6964223a2231623763356630303030303030323030303030303030303030303030303030'
        '30222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631'
        '222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561'
        '653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c76'
        '65725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d636264646136393261373935'
        '2f6c2d7265736f6c7665722d3031362e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f'
        '6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22353162626439326232613062333131343032323162363939396465'
        '37386365353963613132323266653230626333623731653634633566613361346661353335227d2c7b226279746573223a3136363734332c2266696c'
        '655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964'
        '223a223163376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c227363'
        '68656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f666978'
        '6564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f33'
        '2f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f3364'
        '3365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031372e6a736f6e222c22726570'
        '617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c227368'
        '61323536223a223931323735656462616566636262386138623564353230373733343430393032643664633566303437306236333634633861666463'
        '6535623266653736343933227d2c7b226279746573223a3136353537382c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f'
        '756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223164376335663030303030303032303030303030303030'
        '303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f696465'
        '6e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333'
        '3566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70'
        '335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464'
        '61363932613739352f6c2d7265736f6c7665722d3031382e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d6122'
        '3a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2231663565656364313836306139316532356161'
        '613565326665633535613233663934386264306235343935643438386664646566356138303361303834636662227d2c7b226279746573223a313636'
        '3336322c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b'
        '2266696c655f6964223a223166376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e'
        '544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c'
        '6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41'
        '656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474'
        '656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3031392e6a73'
        '6f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f72'
        '5f7631222c22736861323536223a22616439643234376539393834383063353363623830633130323566353737616161366265373338363333376233'
        '64336665616564663962363234333837613631227d2c7b226279746573223a3136363735382c2266696c655f74797065223a22726567756c6172222c'
        '226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22323037633566303030303030303230'
        '3030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61'
        '746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c'
        '223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e'
        '2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d38'
        '3963362d6362646461363932613739352f6c2d7265736f6c7665722d3032302e6a736f6e222c22726570617273655f706f696e74223a66616c73652c'
        '22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a226664363161376661356561'
        '3936616233333535396136623837386463333439626433323633636533623365613564656361653437313864653130646163336264227d2c7b226279'
        '746573223a3136343135302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f696465'
        '6e74697479223a7b2266696c655f6964223a223231376335663030303030303032303030303030303030303030303030303030222c2266696c657379'
        '7374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f'
        '6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c22706174'
        '68223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033'
        '315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665'
        '722d3032312e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f6465'
        '7363726970746f725f7631222c22736861323536223a2230326532623637643335383334633433343539323837666333343864313861326534363933'
        '336432356263613939633435663931343730343962343330346531227d2c7b226279746573223a3136363530302c2266696c655f74797065223a2272'
        '6567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2232323763356630'
        '30303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f'
        '35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d'
        '655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f72'
        '64696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266'
        '322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3032322e6a736f6e222c22726570617273655f706f696e74'
        '223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22396133'
        '633632303965383732353936663463383730396532323232366365623632396666613838373263613632633566323966366230386230626438306132'
        '37227d2c7b226279746573223a3136343136332c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61'
        '746976655f6964656e74697479223a7b2266696c655f6964223a22323337633566303030303030303230303030303030303030303030303030303022'
        '2c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c'
        '22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137633335663637633335616532'
        '66227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c766572'
        '5f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c'
        '2d7265736f6c7665722d3032332e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c76'
        '5f66696c655f64657363726970746f725f7631222c22736861323536223a226465396466666434383638353361663666656466323439613432303737'
        '3439356639333763636239363165656632633536393733363264376166373964383037227d2c7b226279746573223a3136353139312c2266696c655f'
        '74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a'
        '223234376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c2273636865'
        '6d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564'
        '222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72'
        '756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365'
        '316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3032342e6a736f6e222c227265706172'
        '73655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c2273686132'
        '3536223a2264643836643161383361306436643066376432613035626164623633656261333164326133383638303235356666613431353762333566'
        '326663633964346637227d2c7b226279746573223a3136343834312c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e'
        '74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2232353763356630303030303030323030303030303030303030'
        '30303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e74'
        '6974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566'
        '363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f'
        '7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d636264646136'
        '3932613739352f6c2d7265736f6c7665722d3032352e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a22'
        '63686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22666663353037303032313336663938306466353762'
        '30343062303738376430336361646566363262663238353736623632326437363339356438323939343137227d2c7b226279746573223a3136343336'
        '352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266'
        '696c655f6964223a223236376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e5446'
        '53222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63'
        '616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e'
        '762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d'
        '7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3032362e6a736f6e'
        '222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f76'
        '31222c22736861323536223a226139613231633532636164396162666565663535623765616263363333383263626635346264363633353166383163'
        '6634343964313438636634383661356330227d2c7b226279746573223a3136353232382c2266696c655f74797065223a22726567756c6172222c226c'
        '696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223237376335663030303030303032303030'
        '303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e617469'
        '76655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a'
        '2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63'
        '686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963'
        '362d6362646461363932613739352f6c2d7265736f6c7665722d3032372e6a736f6e222c22726570617273655f706f696e74223a66616c73652c2273'
        '6368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2238373332376236623161346161'
        '386263643866323837336264383735313734313735333237326135376164323736353433643466626464353939363461376265227d2c7b2262797465'
        '73223a3136373036382c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74'
        '697479223a7b2266696c655f6964223a223261376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374'
        '656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b69'
        '6e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c227061746822'
        '3a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f'
        '70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d'
        '3032382e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363'
        '726970746f725f7631222c22736861323536223a22613733316163363166363131376432383530646435336237346161356136373630343432303739'
        '65336436613363356335633839623061353333386334363061227d2c7b226279746573223a3136353137332c2266696c655f74797065223a22726567'
        '756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22326237633566303030'
        '3030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f3531'
        '5f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f'
        '73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f726469'
        '6e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d'
        '343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3032392e6a736f6e222c22726570617273655f706f696e74223a'
        '66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223635343839'
        '646638383139316231383261656239633238663163303936366661386365356339316464613565366433363864346365346539663165653134623922'
        '7d2c7b226279746573223a3136343836352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e617469'
        '76655f6964656e74697479223a7b2266696c655f6964223a223263376335663030303030303032303030303030303030303030303030303030222c22'
        '66696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c2276'
        '6f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333356165326622'
        '7d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32'
        '303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d72'
        '65736f6c7665722d3033302e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66'
        '696c655f64657363726970746f725f7631222c22736861323536223a2261613564666465663432656463373766363936363463353137653966626566'
        '363132353837363761333065376631633562356135313466313335623035663561227d2c7b226279746573223a3136333937392c2266696c655f7479'
        '7065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2232'
        '64376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61'
        '223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c'
        '22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e'
        '732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f336433653163'
        '39622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3033312e6a736f6e222c2272657061727365'
        '5f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536'
        '223a22383964393133623239633830313431326336663834376563363034623364373335646565343633663534386462323166376364383833396665'
        '38646632333464227d2c7b226279746573223a3136353239382c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e7422'
        '3a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22326537633566303030303030303230303030303030303030303030'
        '3030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974'
        '795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137633335663637'
        '63333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265'
        '736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932'
        '613739352f6c2d7265736f6c7665722d3033322e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a226368'
        '6f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223464393934386131386165363233353263643665306331'
        '6362666439643934326236666366646264336636633531386266336263656165313934333734313536227d2c7b226279746573223a3136343531372c'
        '2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c'
        '655f6964223a223266376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e54465322'
        '2c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c'
        '5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f'
        '70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074'
        '732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3033332e6a736f6e222c'
        '22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f763122'
        '2c22736861323536223a2234313762393434646134346431646635343134653033653465313964393431393264366238623138323434353363366639'
        '356566333137656162613932306232227d2c7b226279746573223a3136383230342c2266696c655f74797065223a22726567756c6172222c226c696e'
        '6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2233303763356630303030303030323030303030'
        '30303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e6174697665'
        '5f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237'
        '613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f'
        '35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d'
        '6362646461363932613739352f6c2d7265736f6c7665722d3033342e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368'
        '656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22316165336366653433363733366532'
        '66323737353238313434643830633563643337306362623134393739646230613163613364326639633935383762313964227d2c7b22627974657322'
        '3a3136383639342c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e746974'
        '79223a7b2266696c655f6964223a223332376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d'
        '223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64'
        '223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22'
        '443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f7032'
        '2f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3033'
        '352e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f646573637269'
        '70746f725f7631222c22736861323536223a226338303463363233643461646265386664373466373265316137663330343138376663303866653361'
        '3633376535643664353362303036303835353738383639227d2c7b226279746573223a3136353835322c2266696c655f74797065223a22726567756c'
        '6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223333376335663030303030'
        '303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c'
        '765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f7365'
        '7269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e61'
        '74696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d3431'
        '62342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3033362e6a736f6e222c22726570617273655f706f696e74223a6661'
        '6c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2230626139326332'
        '316536366164656564353933666634643061373663663861653733346235396337613431653461623034373331656231656539373230616562227d2c'
        '7b226279746573223a3136333735352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e6174697665'
        '5f6964656e74697479223a7b2266696c655f6964223a223334376335663030303030303032303030303030303030303030303030303030222c226669'
        '6c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c'
        '756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c'
        '2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f323032'
        '36313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d726573'
        '6f6c7665722d3033372e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c'
        '655f64657363726970746f725f7631222c22736861323536223a22643966346632636662613436366466383333643061663362316266626432633333'
        '36326638373662663462383533653135363663653562613463613530333836227d2c7b226279746573223a3136363230342c2266696c655f74797065'
        '223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22333537'
        '6335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a'
        '2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c2276'
        '6f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f'
        '636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f3364336531633962'
        '2d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3033382e6a736f6e222c22726570617273655f70'
        '6f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a'
        '223439343533636264646462646533316539383136373063646630343130356538336235396334643033336365353039646665316437346632363364'
        '6537323331227d2c7b226279746573223a3136353833352c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a31'
        '2c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223336376335663030303030303032303030303030303030303030303030'
        '303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f'
        '7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333'
        '3561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f'
        '6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464613639326137'
        '39352f6c2d7265736f6c7665722d3033392e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35'
        '315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2238633636633861333238303837393133303463366332343061'
        '396439613265396233646365633036383265393061383765616534306337643363323365303566227d2c7b226279746573223a3136333638302c2266'
        '696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f'
        '6964223a223337376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22'
        '736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f66'
        '69786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f7072'
        '6f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f'
        '33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034302e6a736f6e222c2272'
        '6570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22'
        '736861323536223a22313331613233326330376436653839326264376361373737353034613865343261666663323432376631623365646139353333'
        '63393763393961303834323861227d2c7b226279746573223a3136363535342c2266696c655f74797065223a22726567756c6172222c226c696e6b5f'
        '636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22333837633566303030303030303230303030303030'
        '3030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f69'
        '64656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137'
        '63333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f3531'
        '5f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362'
        '646461363932613739352f6c2d7265736f6c7665722d3034312e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d'
        '61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223933393737626165633962643761643230'
        '3034343330373432323266643766373131356464353339396165653936376332666634306432666139656163356637227d2c7b226279746573223a31'
        '36373237302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e7469747922'
        '3a7b2266696c655f6964223a223339376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a'
        '224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a'
        '226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a'
        '2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f61'
        '7474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034322e'
        '6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f6465736372697074'
        '6f725f7631222c22736861323536223a2238346463303638366430666661646235613162333039656464396437613232626131366265333232303936'
        '303935393136313837363765326436396237303461227d2c7b226279746573223a3136373335382c2266696c655f74797065223a22726567756c6172'
        '222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2233613763356630303030303030'
        '32303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f'
        '6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269'
        '616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e617469'
        '6f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d34316234'
        '2d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034332e6a736f6e222c22726570617273655f706f696e74223a66616c73'
        '652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22396531363430303633'
        '31336332396635373332613962613536643064653438666431623632626361623466383135656434386236333437643033613033653865227d2c7b22'
        '6279746573223a3136373831392c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f69'
        '64656e74697479223a7b2266696c655f6964223a223362376335663030303030303032303030303030303030303030303030303030222c2266696c65'
        '73797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d'
        '655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270'
        '617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f3230323631'
        '3033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c'
        '7665722d3034342e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f'
        '64657363726970746f725f7631222c22736861323536223a223463623138323663383062353062363861663239303865633837666336393232306134'
        '6363376435326264633764613265653066373065636630333939393861227d2c7b226279746573223a3136383333332c2266696c655f74797065223a'
        '22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223363376335'
        '663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263'
        '686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c'
        '756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f'
        '6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d32'
        '6266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034352e6a736f6e222c22726570617273655f706f69'
        '6e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2239'
        '306162663165326462613061326232303639313766353839306233383066656639353166356639376664393232663835626436363836333238316633'
        '633232227d2c7b226279746573223a3136383232312c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c22'
        '6e61746976655f6964656e74697479223a7b2266696c655f6964223a2233653763356630303030303030323030303030303030303030303030303030'
        '30222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631'
        '222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561'
        '653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c76'
        '65725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d636264646136393261373935'
        '2f6c2d7265736f6c7665722d3034362e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f'
        '6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22653732393139633731323738353165373665343066623730363065'
        '39663831356261353032616631613163613531373465336361633663336537323135303230227d2c7b226279746573223a3136363434342c2266696c'
        '655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964'
        '223a223366376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c227363'
        '68656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f666978'
        '6564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f33'
        '2f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f3364'
        '3365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034372e6a736f6e222c22726570'
        '617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c227368'
        '61323536223a223631343236396564336361663633643338646635363935653562626430303666643564333264386539333265663263353161346332'
        '3836633834653565643032227d2c7b226279746573223a3136343335302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f'
        '756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223430376335663030303030303032303030303030303030'
        '303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f696465'
        '6e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333'
        '3566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70'
        '335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464'
        '61363932613739352f6c2d7265736f6c7665722d3034382e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d6122'
        '3a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2265313961373736366438356164393762333865'
        '643765636239303963313064363032353532333961346131653438623761313239303332303838386639363431227d2c7b226279746573223a313636'
        '3534362c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b'
        '2266696c655f6964223a223431376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e'
        '544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c'
        '6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41'
        '656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474'
        '656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3034392e6a73'
        '6f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f72'
        '5f7631222c22736861323536223a22656563626538383337623934326538346630616562323531643434613439333939623463363562363363393336'
        '37313632373965353338386663633833316533227d2c7b226279746573223a3136363833332c2266696c655f74797065223a22726567756c6172222c'
        '226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22343237633566303030303030303230'
        '3030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61'
        '746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c'
        '223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e'
        '2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d38'
        '3963362d6362646461363932613739352f6c2d7265736f6c7665722d3035302e6a736f6e222c22726570617273655f706f696e74223a66616c73652c'
        '22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223839616235316266313564'
        '6433623637323463396539633439653463613566386563646232613863303862333864303139393037653661646137396265646339227d2c7b226279'
        '746573223a3136373930362c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f696465'
        '6e74697479223a7b2266696c655f6964223a223433376335663030303030303032303030303030303030303030303030303030222c2266696c657379'
        '7374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f'
        '6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c22706174'
        '68223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033'
        '315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665'
        '722d3035312e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f6465'
        '7363726970746f725f7631222c22736861323536223a2237373561613465386566663139396234353337636234363839643262396266336334326164'
        '653936336437666135343337613431633262373966393031633365227d2c7b226279746573223a3136323733342c2266696c655f74797065223a2272'
        '6567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2234343763356630'
        '30303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f'
        '35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d'
        '655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f72'
        '64696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266'
        '322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3035322e6a736f6e222c22726570617273655f706f696e74'
        '223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22356434'
        '346637303463613435623266383261656463636336653332633334646536306161613832616132383164306561393832383337333064656338393338'
        '37227d2c7b226279746573223a3136333435332c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61'
        '746976655f6964656e74697479223a7b2266696c655f6964223a22343537633566303030303030303230303030303030303030303030303030303022'
        '2c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c'
        '22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a22376137633335663637633335616532'
        '66227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c766572'
        '5f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c'
        '2d7265736f6c7665722d3035332e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c76'
        '5f66696c655f64657363726970746f725f7631222c22736861323536223a223239383935643666646439393466636431386236616439396139653466'
        '3262643765616161393332326666663837633266376635646533366430376365656137227d2c7b226279746573223a3136303032392c2266696c655f'
        '74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a'
        '223436376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c2273636865'
        '6d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564'
        '222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72'
        '756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365'
        '316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3035342e6a736f6e222c227265706172'
        '73655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c2273686132'
        '3536223a2232363939636132623065303536313836616634653663303037626364663438333162396537633632323230346265343234333637333566'
        '616139623830613265227d2c7b226279746573223a3136323533302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e'
        '74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a2234373763356630303030303030323030303030303030303030'
        '30303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e74'
        '6974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566'
        '363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f'
        '7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d636264646136'
        '3932613739352f6c2d7265736f6c7665722d3035352e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a22'
        '63686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22313634386561336565346462636263346432393265'
        '37353061633630336635383961636232656535626135653537633065303763663538336563303037366239227d2c7b226279746573223a3136333637'
        '322c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266'
        '696c655f6964223a223439376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e5446'
        '53222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63'
        '616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e'
        '762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d'
        '7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3035362e6a736f6e'
        '222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f76'
        '31222c22736861323536223a223839623539343761633836353263303039633431306164383330336664383863663463656137316231316631666365'
        '3637663465343534343833613866316665227d2c7b226279746573223a3136353835322c2266696c655f74797065223a22726567756c6172222c226c'
        '696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223461376335663030303030303032303030'
        '303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e617469'
        '76655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a'
        '2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63'
        '686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963'
        '362d6362646461363932613739352f6c2d7265736f6c7665722d3035372e6a736f6e222c22726570617273655f706f696e74223a66616c73652c2273'
        '6368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2236613465356439366363343139'
        '376163616335343732653436376264303532643936393839346631396461643133326131393466626231353561666432316436227d2c7b2262797465'
        '73223a3136333935302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74'
        '697479223a7b2266696c655f6964223a223462376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374'
        '656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b69'
        '6e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c227061746822'
        '3a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f'
        '70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d'
        '3035382e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363'
        '726970746f725f7631222c22736861323536223a22613335643565633937623564316335613364393337373433363931323964666237666236383733'
        '62326563333164356164303038613838653732396438383339227d2c7b226279746573223a3136353530392c2266696c655f74797065223a22726567'
        '756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22346337633566303030'
        '3030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f3531'
        '5f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f'
        '73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f726469'
        '6e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d'
        '343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3035392e6a736f6e222c22726570617273655f706f696e74223a'
        '66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a223339636262'
        '663532303763336531333932633437303261313737343361623865303533336331353461346235623964383666383139653866643634376431326222'
        '7d2c7b226279746573223a3131303031322c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e617469'
        '76655f6964656e74697479223a7b2266696c655f6964223a223464376335663030303030303032303030303030303030303030303030303030222c22'
        '66696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c2276'
        '6f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333356165326622'
        '7d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32'
        '303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d72'
        '65736f6c7665722d3036302e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66'
        '696c655f64657363726970746f725f7631222c22736861323536223a2232636634336434323632393439356530613734663365303731666437623733'
        '303364373463613164343732366330323265656337353030323666313431356231227d2c7b226279746573223a34343339362c2266696c655f747970'
        '65223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223465'
        '376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d6122'
        '3a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22'
        '766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e73'
        '2f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339'
        '622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3036312e6a736f6e222c22726570617273655f'
        '706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c2273686132353622'
        '3a2233666663393966333332343939383938353862366630613235323433646638366339356331616462356639336430616165363238656465316338'
        '636636393536227d2c7b226279746573223a34343538362c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a31'
        '2c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223466376335663030303030303032303030303030303030303030303030'
        '303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f'
        '7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333'
        '3561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f'
        '6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464613639326137'
        '39352f6c2d7265736f6c7665722d3036322e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35'
        '315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2233643766343837346636393961363864373732643938356166'
        '626138626530376561353066343862396334366637656535306133343630346265363838663039227d2c7b226279746573223a34333933332c226669'
        '6c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f69'
        '64223a223530376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c2273'
        '6368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669'
        '786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f'
        '332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33'
        '643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3036332e6a736f6e222c227265'
        '70617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c2273'
        '6861323536223a2231633836333163373431363938343764666562613062653838663664353231316431393832613039323862326366633463373439'
        '386130363961616430666566227d2c7b226279746573223a34313736322c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f'
        '756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223531376335663030303030303032303030303030303030'
        '303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f696465'
        '6e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333'
        '3566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70'
        '335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464'
        '61363932613739352f6c2d7265736f6c7665722d3036342e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d6122'
        '3a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2235646632313565646336623164366261363934'
        '636666356438333766313736613366346265313238383634663463343030393062623665653662346163633830227d2c7b226279746573223a343138'
        '32302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b22'
        '66696c655f6964223a223532376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e54'
        '4653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f'
        '63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f4165'
        '6e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f61747465'
        '6d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3036352e6a736f'
        '6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f'
        '7631222c22736861323536223a2231663963373531356436353766393231373863393238633964383461656430653064323563353239393239623966'
        '353766653863393138343037393437333131227d2c7b226279746573223a34323836312c2266696c655f74797065223a22726567756c6172222c226c'
        '696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223533376335663030303030303032303030'
        '303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e617469'
        '76655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a'
        '2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63'
        '686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963'
        '362d6362646461363932613739352f6c2d7265736f6c7665722d3036362e6a736f6e222c22726570617273655f706f696e74223a66616c73652c2273'
        '6368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2234656231663466323630653530'
        '333263346563353364613863356536663639643636393538373965386330313762333534663930663662353032386130653863227d2c7b2262797465'
        '73223a34383832342c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e7469'
        '7479223a7b2266696c655f6964223a223534376335663030303030303032303030303030303030303030303030303030222c2266696c657379737465'
        '6d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e'
        '64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a'
        '22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70'
        '322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d30'
        '36372e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f6465736372'
        '6970746f725f7631222c22736861323536223a2263633939643532373163366231626562626564633836653561633430623064326637353337323135'
        '386462646466646665316533386435353935383139636531227d2c7b226279746573223a35303337302c2266696c655f74797065223a22726567756c'
        '6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223536376335663030303030'
        '303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c'
        '765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f7365'
        '7269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e61'
        '74696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d3431'
        '62342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3036382e6a736f6e222c22726570617273655f706f696e74223a6661'
        '6c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2230383234306337'
        '633962346662376361643431323135396364313538353339653738373734386465376337343533343930346664646564613863363266366463227d2c'
        '7b226279746573223a35333030332c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f'
        '6964656e74697479223a7b2266696c655f6964223a223537376335663030303030303032303030303030303030303030303030303030222c2266696c'
        '6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c75'
        '6d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c22'
        '70617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236'
        '313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f'
        '6c7665722d3036392e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c65'
        '5f64657363726970746f725f7631222c22736861323536223a2263303661663733346632383964353135373033636435636235623462626366383163'
        '663830653762336339353661653732386331333663343637363862343264227d2c7b226279746573223a34323632302c2266696c655f74797065223a'
        '22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223538376335'
        '663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263'
        '686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c'
        '756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f'
        '6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d32'
        '6266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3037302e6a736f6e222c22726570617273655f706f69'
        '6e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2230'
        '386532363335363762653761393433363631663961636566303861626464303965616238646237626236613165363562343231393330626461613162'
        '643636227d2c7b226279746573223a33323535302c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e'
        '61746976655f6964656e74697479223a7b2266696c655f6964223a223539376335663030303030303032303030303030303030303030303030303030'
        '222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f763122'
        '2c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636376333356165'
        '3266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665'
        '725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d6362646461363932613739352f'
        '6c2d7265736f6c7665722d3037312e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c'
        '765f66696c655f64657363726970746f725f7631222c22736861323536223a2233343339626134656632323135663530653930383536313964646361'
        '323965653165386164643765333262623437326433643531623765616463373664626539227d2c7b226279746573223a33323935342c2266696c655f'
        '74797065223a22726567756c6172222c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a'
        '223561376335663030303030303032303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c2273636865'
        '6d61223a2263686f35315f6c765f6e61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564'
        '222c22766f6c756d655f73657269616c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72'
        '756e732f636f6f7264696e6174696f6e2f63686f35315f70335f7265736f6c7665725f32303236313033315f70322f617474656d7074732f33643365'
        '316339622d326266322d343162342d383963362d6362646461363932613739352f6c2d7265736f6c7665722d3037322e6a736f6e222c227265706172'
        '73655f706f696e74223a66616c73652c22736368656d61223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c2273686132'
        '3536223a2262306430633839643062653535393139383235353562353665613464346163356333323733373863643837643838303837666261633238'
        '333830396162646463227d2c7b226279746573223a31333438322c2266696c655f74797065223a22726567756c6172222c226c696e6b5f636f756e74'
        '223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223562376335663030303030303032303030303030303030303030'
        '303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61746976655f6964656e7469'
        '74795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c223a223761376333356636'
        '3763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f72756e732f636f6f7264696e6174696f6e2f63686f35315f70335f72'
        '65736f6c7665725f32303236313033315f70322f617474656d7074732f33643365316339622d326266322d343162342d383963362d63626464613639'
        '32613739352f6c2d7265736f6c7665722d3037332e6a736f6e222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263'
        '686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2231653461333231393062366535346231666132353536'
        '346361353035393438623832643564363364393865653638343931306432393963623064396434383437227d5d2c227075626c69736865645f726f77'
        '73223a31383739332c2271756575655f636f756e74223a3732342c2271756575655f7061676564223a747275652c2271756575655f73686132353622'
        '3a2233643232616462343366383435656266613466306532336431316635623530383139623732313864646263343963383835383435383630326138'
        '653637303266222c22736368656d61223a2263686f35315f6c5f7265736f6c7665725f696e6465785f7631222c22736f757263655f6279746573223a'
        '3139353735322c22736f757263655f70696e735f736861323536223a2261653038336463363966616438656439303066313437356261316137323937'
        '323730313833666566303061656666363733396532393962303135383831646633222c22737065635f736861323536223a2234623233613462323039'
        '386634316136616563313538396232303136366663613064323033396436376464316631303835613565356439306233366533306534222c22737461'
        '747573223a22494e434f4d504c4554455f52454655534544227d'
    )
    page = bytes.fromhex(
        '7b22726f7773223a5b7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a'
        '226561676572222c226964223a2264326336623336616334393931333562656538326635316431363531363839303263633431306530363362356662'
        '333034636131363737626432303935666631222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '223637313266363163623066636162616565366638393562333262646231313464316562633032663761336230373434373062323136636135383365'
        '3464313163222c2270617468223a22242f626f64793a31332f746573742f76616c7565733a312f636f6d70617261746f72733a302f617267733a302f'
        '637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138'
        '64306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368613235'
        '36223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134'
        '3934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974'
        '696f6e616c223a747275652c22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a226263316366623239'
        '3465366234663061396131376238646539353861353964626565666239623736363932653362353332663265633434623537623865353433222c226b'
        '696e64223a22496d706f7274222c226d6f64756c65223a227363697079222c22706172656e74223a2238616564383037333566346263373766356334'
        '633034663265623662383763626532626162376166623339636334336234666564653461396231663038623530222c2270617468223a22242f626f64'
        '793a31332f626f64793a30222c227261775f7370616e5f736861323536223a2236633037353331653338313134646530316361633132376566393666'
        '333236303136333139653162646339663738636565383364623932373034613233366136222c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338'
        '6235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a34'
        '3635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364'
        '616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38322c342c38322c31395d7d2c7b22616c696173223a6e756c6c'
        '2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22636f6e6469'
        '74696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a2266343364396638626562333236633362303739646135313036'
        '613931326132366662343866316432323936396239626630313834346535363731383261653130222c226b696e64223a22616c696173222c226d6f64'
        '756c65223a227363697079222c226e616d65223a227761726e696e6773222c22706172656e74223a2262633163666232393465366234663061396131'
        '376238646539353861353964626565666239623736363932653362353332663265633434623537623865353433222c2270617468223a22242f626f64'
        '793a31332f626f64793a302f6e616d65733a30222c227261775f7370616e5f736861323536223a223232373639306437633330333063383132643933'
        '6434653039323935383331663665383230616238363665306438353138353266316235653463353063356432222c227265736f6c7574696f6e223a22'
        '756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132'
        '63343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22'
        '6279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638'
        '3332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38322c31312c38322c31395d7d2c7b226361'
        '706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a'
        '223731366466316131653131333964373762363330303437633838333935333939336436633430653265333530396566336435633230346634613231'
        '6636353738222c226b696e64223a2245787072222c226d6f64756c65223a227363697079222c22706172656e74223a22386165643830373335663462'
        '63373766356334633034663265623662383763626532626162376166623339636334336234666564653461396231663038623530222c227061746822'
        '3a22242f626f64793a31332f626f64793a31222c227261775f7370616e5f736861323536223a22373935393233633932653863623230373962653061'
        '33313563623838373634366434353965313335336534663234633436306233326536326635623666363861222c227265736f6c7574696f6e223a2275'
        '6e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263'
        '343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262'
        '79746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833'
        '32316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38332c342c38362c34345d7d2c7b2263617061'
        '62696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c6261636b'
        '5f64796e616d6963222c2265706f6368223a226561676572222c226964223a2239613766383062656261646532636139393061343663623439623036'
        '366237656562333062643434633038333965366161333830666437323838323231613238222c22696d706f72745f63616e646964617465223a6e756c'
        '6c2c226b696e64223a2243616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223731366466316131653131333964373762363330303437633838333935333939336436633430653265333530396566336435633230346634'
        '6132316636353738222c2270617468223a22242f626f64793a31332f626f64793a312f76616c7565222c22706f737369626c655f64796e616d69635f'
        '656666656374223a226174747269627574655f6469737061746368222c227261775f7370616e5f736861323536223a22373935393233633932653863'
        '62323037396265306133313563623838373634366434353965313335336534663234633436306233326536326635623666363861222c227265736f6c'
        '7574696f6e223a22756e7265736f6c766564222c2272756e74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a5b38332c342c38362c34345d7d2c7b226361706162696c697479223a2270656e64696e67222c2263'
        '6f6e646974696f6e616c223a747275652c22656666656374223a226174747269627574655f6469737061746368222c2265706f6368223a2265616765'
        '72222c226964223a22396536326464376365393034363933393962613764383936623637326163393232656539636437316233633836366633643463'
        '37346663373132323735663134222c226b696e64223a22417474726962757465222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '223961376638306265626164653263613939306134366362343962303636623765656233306264343463303833396536616133383066643732383832'
        '3231613238222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f66756e63222c227261775f7370616e5f736861323536'
        '223a22346235323665303937643464386463303132363566626639373766363364383661343039323238633532326532333933313531343962386161'
        '63366664373137222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663'
        '666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e'
        '64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a5b38332c342c38332c31375d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c'
        '6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a2265616765'
        '72222c226964223a22333236643765633262333033663339376462373862336235346565366534303463306165653432386365353563353435393866'
        '63626463376531656336643838222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a227761726e696e'
        '6773222c22706172656e74223a2239653632646437636539303436393339396261376438393662363732616339323265653963643731623363383636'
        '663364346337346663373132323735663134222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f66756e632f76616c75'
        '65222c227261775f7370616e5f736861323536223a223232373639306437633330333063383132643933643465303932393538333166366538323061'
        '6238363665306438353138353266316235653463353063356432222c227265667573616c223a22636f6e646974696f6e616c5f6f725f64656c657465'
        '645f62696e64696e67222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266'
        '6663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432'
        '336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f'
        '75746638223a5b38332c342c38332c31325d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a7472'
        '75652c2265706f6368223a226561676572222c226964223a226334396430346432343965336433653163383834383034366137626630376334393638'
        '6334383038333264386335636630636464336165376436333532643061222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079'
        '222c22706172656e74223a22333236643765633262333033663339376462373862336235346565366534303463306165653432386365353563353435'
        '39386663626463376531656336643838222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f66756e632f76616c75652f'
        '637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138'
        '64306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368613235'
        '36223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134'
        '3934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974'
        '696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a223834613034356432633065363737393461333934366365326363'
        '6630366531346638333033363038396566356439613838353633383363326566613034653334222c226b696e64223a224c6f6164222c226d6f64756c'
        '65223a227363697079222c22706172656e74223a22396536326464376365393034363933393962613764383936623637326163393232656539636437'
        '31623363383636663364346337346663373132323735663134222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f6675'
        '6e632f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226561676572222c2269'
        '64223a223237323166633432386663396635313233346561623962653765383264656530656364633033643434373632323437626461383138386439'
        '6436393066393961222c226b696e64223a224a6f696e6564537472222c226d6f64756c65223a227363697079222c22706172656e74223a2239613766'
        '383062656261646532636139393061343663623439623036366237656562333062643434633038333965366161333830666437323838323231613238'
        '222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a30222c227261775f7370616e5f736861323536223a22'
        '373332326164656237613335646630366431323836653734376330363265346331366665366230653033386363653963623261363433346536653364'
        '37386235222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565'
        '353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a'
        '226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261'
        '30643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574663822'
        '3a5b38332c31382c38352c34395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22'
        '65706f6368223a226561676572222c226964223a22333132373961653561623739343866313232353461383136623637386633356238666435333162'
        '38313032396564653765346639333362323230356465366437222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079'
        '222c22706172656e74223a22323732316663343238666339663531323334656162396265376538326465653065636463303364343437363232343762'
        '64613831383864396436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c75'
        '65733a30222c227261775f7370616e5f736861323536223a226230353432356636613766303531323064626262363663383937666565346565373463'
        '6165393932663134343866646534363736343066386365623634303266222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a5b38332c32302c38332c33385d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a22'
        '6561676572222c226964223a223433303633353034393939313163633034663837313661656265646532313336646639633962626232323936306635'
        '3633316435393631366437343833363136222c226b696e64223a22466f726d617474656456616c7565222c226d6f64756c65223a227363697079222c'
        '22706172656e74223a223237323166633432386663396635313233346561623962653765383264656530656364633033643434373632323437626461'
        '3831383864396436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c756573'
        '3a31222c227261775f7370616e5f736861323536223a2234613530356666326665373261323930383762373333363032333833303264633639313638'
        '623731633566613364383936366232663764356133343435353663222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f70'
        '65223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531'
        '3864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273686132'
        '3536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561'
        '343934313862393266227d2c227370616e5f75746638223a5b38332c33382c38332c35335d7d2c7b2262696e64696e675f63616e6469646174657322'
        '3a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e61'
        '6c223a747275652c2265706f6368223a226561676572222c226964223a22373437333361633566653962356432356236623163346231323036323661'
        '34376238366339353734316666373733366234393961306565373164613666626233222c226b696e64223a224e616d65222c226d6f64756c65223a22'
        '7363697079222c226e616d65223a226e705f6d696e76657273696f6e222c22706172656e74223a223433303633353034393939313163633034663837'
        '3136616562656465323133366466396339626262323239363066353633316435393631366437343833363136222c2270617468223a22242f626f6479'
        '3a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a312f76616c7565222c227261775f7370616e5f736861323536223a2231'
        '663439316232656637626466393633633663343864363666653131363033363030646563656463383662376434636530326530656165333932663334'
        '393032222c227265667573616c223a2261737369676e6d656e745f76616c75655f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265'
        '736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961'
        '643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262797465'
        '73223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166'
        '30343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38332c33392c38332c35325d7d2c7b22636170616269'
        '6c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22633461'
        '626539373132376232313733373236316265393333393931363663623632333034356363653135326430663334616633616337636364363161653263'
        '38222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2237343733336163356665396235643235'
        '623662316334623132303632366134376238366339353734316666373733366234393961306565373164613666626233222c2270617468223a22242f'
        '626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a312f76616c75652f637478222c227261775f7370616e5f7368'
        '61323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266'
        '6663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432'
        '336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f'
        '75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f63'
        '68223a226561676572222c226964223a2234643535333664333630623964653138343332306332643834663437623137336334653264346337346236'
        '656331366539313863313135613364363662643462222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c2270'
        '6172656e74223a2232373231666334323866633966353132333465616239626537653832646565306563646330336434343736323234376264613831'
        '383864396436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a32'
        '222c227261775f7370616e5f736861323536223a22633362363066376533663035393835383936363138376463663361336333613435316363376336'
        '32396465336533353232386264353830343236373339653065222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f706522'
        '3a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864'
        '306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536'
        '223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439'
        '34313862393266227d2c227370616e5f75746638223a5b38332c35332c38332c35395d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a2265616765'
        '72222c226964223a22306130313366643931303131636439343138366231633934343839326461616165336661353534616232323330373666313166'
        '30323939323265356566663862222c226b696e64223a22466f726d617474656456616c7565222c226d6f64756c65223a227363697079222c22706172'
        '656e74223a22323732316663343238666339663531323334656162396265376538326465653065636463303364343437363232343762646138313838'
        '64396436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a33222c'
        '227261775f7370616e5f736861323536223a226561313633333134613132333564373166656564303830626361356134623932346638383334393636'
        '6230656530646262396139646639633130346237376636222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a5b38332c35392c38332c37345d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c'
        '2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a74'
        '7275652c2265706f6368223a226561676572222c226964223a2233636534633866646262313364333337633262363764666366383037636331346164'
        '376665313936363862613238353236316338303539633766633531616164222c226b696e64223a224e616d65222c226d6f64756c65223a2273636970'
        '79222c226e616d65223a226e705f6d617876657273696f6e222c22706172656e74223a22306130313366643931303131636439343138366231633934'
        '34383932646161616533666135353461623232333037366631316630323939323265356566663862222c2270617468223a22242f626f64793a31332f'
        '626f64793a312f76616c75652f617267733a302f76616c7565733a332f76616c7565222c227261775f7370616e5f736861323536223a223333366237'
        '306333646133643139306135326332353634633862653235663139363033356662333064356331353934363139326262396432386666383431623822'
        '2c227265667573616c223a2261737369676e6d656e745f76616c75655f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338'
        '6235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a34'
        '3635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364'
        '616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38332c36302c38332c37335d7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a2230343565363463'
        '373439343933663839363631643838633963653034393465646332353836633163346435626165613235643834623563376537353535656137222c22'
        '6b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a223363653463386664626231336433333763326236'
        '3764666366383037636331346164376665313936363862613238353236316338303539633766633531616164222c2270617468223a22242f626f6479'
        '3a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a332f76616c75652f637478222c227261775f7370616e5f736861323536'
        '223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665'
        '65353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332'
        '6130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638'
        '223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22'
        '6561676572222c226964223a223334646665393565343766353962356438306531343039386337623934383062336564363137383337326161353231'
        '3363613036316630306438653561393465222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223237323166633432386663396635313233346561623962653765383264656530656364633033643434373632323437626461383138386439'
        '6436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a34222c2272'
        '61775f7370616e5f736861323536223a2266396439393331643264393133643731653637373463386564616537356430666630333437653939356232'
        '613832663565386535633332323338326638633134222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132'
        '323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335'
        '3161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261'
        '313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862'
        '393266227d2c227370616e5f75746638223a5b38342c32302c38352c32385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f'
        '6e646974696f6e616c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226561676572222c22'
        '6964223a2232346464626633643430366566333963623766366532326138333731306165396164366236313233653061353132366634313466363866'
        '636639636666386335222c226b696e64223a22466f726d617474656456616c7565222c226d6f64756c65223a227363697079222c22706172656e7422'
        '3a2232373231666334323866633966353132333465616239626537653832646565306563646330336434343736323234376264613831383864396436'
        '393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a35222c22726177'
        '5f7370616e5f736861323536223a22336162346362346362373334316234323063306231336663303336623334636235663761366531643863386535'
        '39373563616162373639316162313763653166222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233'
        '366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161'
        '222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131'
        '616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138623932'
        '66227d2c227370616e5f75746638223a5b38352c32382c38352c34375d7d2c7b2262696e64696e675f63616e64696461746573223a5b226165643962'
        '383063333439636263393436396439633637636663316331366261306231383865623933663832633433333130633364613665383135393062616122'
        '5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a747275652c2265706f6368223a226561676572222c226964223a223365363965643963326461383162663537626430336637396364336263393437'
        '3461353338363735306162633361636563383563363261653464323033633531222c22696d706f72745f63616e646964617465223a225f5f76657273'
        '696f6e5f5f222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a225f5f6e756d70795f76657273696f'
        '6e5f5f222c22706172656e74223a22323464646266336434303665663339636237663665323261383337313061653961643662363132336530613531'
        '32366634313466363866636639636666386335222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76'
        '616c7565733a352f76616c7565222c227261775f7370616e5f736861323536223a223438653035386635313064386536373865323732306135393839'
        '3333383366313038666562643864376463393335346531383762656661656136373634613134222c227265736f6c7574696f6e223a226c6578696361'
        '6c5f63616e646964617465222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231'
        '3263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b'
        '226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036'
        '383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38352c32392c38352c34365d7d2c7b2263'
        '61706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c22696422'
        '3a2262613333626362663665373036373361323764663632383061633064386334313732383636333830633836613964376134316538616234346134'
        '323262616534222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a223365363965643963326461'
        '3831626635376264303366373963643362633934373461353338363735306162633361636563383563363261653464323033633531222c2270617468'
        '223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c7565733a352f76616c75652f637478222c227261775f7370'
        '616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136'
        '62303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c227363'
        '6f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131'
        '6561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c22'
        '7370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c'
        '2265706f6368223a226561676572222c226964223a226663613338376133343761373238666166326164323764303364633262366566366336363662'
        '3530383461653634633331363035623236373834376662623666222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a2273636970'
        '79222c22706172656e74223a223237323166633432386663396635313233346561623962653765383264656530656364633033643434373632323437'
        '6264613831383864396436393066393961222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f617267733a302f76616c'
        '7565733a36222c227261775f7370616e5f736861323536223a2262613565633531643037613461633065393531363038373034343331643539613032'
        '623231613465393531616363313035303561386463343037633530316565222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273'
        '636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732'
        '6265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273'
        '6861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435'
        '353561343934313862393266227d2c227370616e5f75746638223a5b38352c34372c38352c34385d7d2c7b2262696e64696e675f63616e6469646174'
        '6573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e64697469'
        '6f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22663634643232656664623861353637656531396333326432633136'
        '33623035626133363330646265383466393538326139303230613633636363333464353961222c226b696e64223a224e616d65222c226d6f64756c65'
        '223a227363697079222c226e616d65223a22557365725761726e696e67222c22706172656e74223a2239613766383062656261646532636139393061'
        '343663623439623036366237656562333062643434633038333965366161333830666437323838323231613238222c2270617468223a22242f626f64'
        '793a31332f626f64793a312f76616c75652f617267733a31222c227261775f7370616e5f736861323536223a22333530383365383631303466373466'
        '61383063383261366261613962306434333864633933333234336139343661643562623031363233363530366634326635222c227265667573616c22'
        '3a22756e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f'
        '7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265'
        '313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861'
        '323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535'
        '61343934313862393266227d2c227370616e5f75746638223a5b38362c31382c38362c32395d7d2c7b226361706162696c697479223a2270656e6469'
        '6e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22396464633562633065663034343031'
        '33313362613534363833393635656436646164356631663539373638626163643534326232316430373832636436356237222c226b696e64223a224c'
        '6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2266363464323265666462386135363765653139633332643263313633'
        '623035626133363330646265383466393538326139303230613633636363333464353961222c2270617468223a22242f626f64793a31332f626f6479'
        '3a312f76616c75652f617267733a312f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e'
        '7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334'
        '3961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279'
        '746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332'
        '316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a22'
        '70656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a226b6579776f72645f756e7061636b5f70726f746f636f'
        '6c222c2265706f6368223a226561676572222c226964223a226565303164393939363463303561393565383262643931393737373965326161373533'
        '6339656533393066613931316539326161393766363462316333343333222c226b696e64223a226b6579776f7264222c226d6f64756c65223a227363'
        '697079222c22706172656e74223a22396137663830626562616465326361393930613436636234396230363662376565623330626434346330383339'
        '65366161333830666437323838323231613238222c2270617468223a22242f626f64793a31332f626f64793a312f76616c75652f6b6579776f726473'
        '3a30222c227261775f7370616e5f736861323536223a2262356338303233303335373361326631623139663038303538326130653665356439323865'
        '343537313965356434333263623933303464323262613931323765222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f70'
        '65223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531'
        '3864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273686132'
        '3536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561'
        '343934313862393266227d2c227370616e5f75746638223a5b38362c33312c38362c34335d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a2232373662646665626235393566363165'
        '353532333261386634623662393235663961653934313637313265666661323231326236396535336438316165616238222c226b696e64223a22436f'
        '6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2265653031643939393634633035613935653832626439313937'
        '373739653261613735336339656533393066613931316539326161393766363462316333343333222c2270617468223a22242f626f64793a31332f62'
        '6f64793a312f76616c75652f6b6579776f7264733a302f76616c7565222c227261775f7370616e5f736861323536223a226434373335653361323635'
        '6531366565653033663539373138623962356430333031396330376438623663353166393064613361363636656563313361623335222c227265736f'
        '6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361'
        '38636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c2273'
        '6f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536'
        '6337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38362c34322c38362c'
        '34335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2264'
        '656c6574655f7772697465222c2265706f6368223a226561676572222c226964223a2234346132346232313534323438666435616338306531643164'
        '396362373232663938303461343031643131616165363137333765623233666361626331623839222c226b696e64223a2244656c657465222c226d6f'
        '64756c65223a227363697079222c22706172656e74223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2270617468223a22242f626f64793a3134222c227261775f7370616e5f73'
        '6861323536223a2237393138643635346436346166393538613265303633613463333837666637646139366364343066663138363063396462383762'
        '613831633961313236633138222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230'
        '3362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70'
        '655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561'
        '663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370'
        '616e5f75746638223a5b38372c302c38372c31385d7d2c7b2262696e64696e675f6b696e64223a2244656c222c226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2232353761356536383266'
        '646636363361383561303938643838333932396562313537643962316130656436623232306139356532326334656630373837633536222c226b696e'
        '64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a2256657273696f6e222c22706172656e74223a22343461323462'
        '32313534323438666435616338306531643164396362373232663938303461343031643131616165363137333765623233666361626331623839222c'
        '2270617468223a22242f626f64793a31342f746172676574733a30222c227261775f7370616e5f736861323536223a22646431363739303564653064'
        '65666361663732646536373365653434633037343331373730643132396363666661623238366264326564666461663632333936222c227265736f6c'
        '7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138'
        '636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f'
        '75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663'
        '37626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b38372c342c38372c3131'
        '5d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2265616765'
        '72222c226964223a22393534393738366138373038653764653736393739653666393935353733383361303666313533333734643433306633626133'
        '36333539623430333232336333222c226b696e64223a2244656c222c226d6f64756c65223a227363697079222c22706172656e74223a223235376135'
        '653638326664663636336138356130393864383833393239656231353764396231613065643662323230613935653232633465663037383763353622'
        '2c2270617468223a22242f626f64793a31342f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262'
        '336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c'
        '22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962'
        '65366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b22'
        '62696e64696e675f6b696e64223a2244656c222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c'
        '73652c2265706f6368223a226561676572222c226964223a226461633939323563376332343532323964656363626435313032666433326233373833'
        '3435353238343732393665353331386264376438326663623839323238222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079'
        '222c226e616d65223a227061727365222c22706172656e74223a22343461323462323135343234386664356163383065316431643963623732326639'
        '38303461343031643131616165363137333765623233666361626331623839222c2270617468223a22242f626f64793a31342f746172676574733a31'
        '222c227261775f7370616e5f736861323536223a22333063343731663661616662636137303835363430363533656565663535356538356562306466'
        '31363032633938613636323831346332373736376431313838222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f706522'
        '3a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864'
        '306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536'
        '223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439'
        '34313862393266227d2c227370616e5f75746638223a5b38372c31332c38372c31385d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223364656435643865323765616630373732'
        '6635376332623066303237386335323936646636623637636564313265313961636265353332346230343132306564222c226b696e64223a2244656c'
        '222c226d6f64756c65223a227363697079222c22706172656e74223a2264616339393235633763323435323239646563636264353130326664333262'
        '333738333435353238343732393665353331386264376438326663623839323238222c2270617468223a22242f626f64793a31342f74617267657473'
        '3a312f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c22656666656374223a22657863657074696f6e5f70726f746f636f6c222c2265706f6368223a226561676572'
        '222c226964223a2235653131313862356137356136336561666665373437393465316534313336663235623434616462656539333937333532663764'
        '633763383263393463373262222c226b696e64223a22547279222c226d6f64756c65223a227363697079222c22706172656e74223a22313232333665'
        '65613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c'
        '2270617468223a22242f626f64793a3135222c227261775f7370616e5f736861323536223a2238643465663437646230633735626530333463333636'
        '373964373732643735326337343638323965386237376461613530653037333535376162313832663739222c227265736f6c7574696f6e223a22756e'
        '7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334'
        '3961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279'
        '746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332'
        '316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b39342c302c3130302c33335d7d2c7b2263617061'
        '62696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22696d706f7274222c2265706f63'
        '68223a226561676572222c226964223a2235653664613834316431653436626336383562633536373937373734396537633734656463633366646562'
        '633535393863653338306565636431326438326235222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a227363697079222c'
        '22706172656e74223a223565313131386235613735613633656166666537343739346531653431333666323562343461646265653933393733353266'
        '3764633763383263393463373262222c2270617468223a22242f626f64793a31352f626f64793a30222c227261775f7370616e5f736861323536223a'
        '226537653961313932626235373135333038356435616165363333336630333339643365373733643766383565636165313534616365323238336339'
        '6638616634222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665'
        '65353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332'
        '6130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638'
        '223a5b39352c342c39352c35345d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c2269'
        '64223a223930643063633630336636323434363838303462653531666338386266396338333361323164323264366131386235376562616332313335'
        '6538303034623235222c226b696e64223a22616c696173222c226d6f64756c65223a227363697079222c226e616d65223a224c6f774c6576656c4361'
        '6c6c61626c65222c22706172656e74223a22356536646138343164316534366263363835626335363739373737343965376337346564636333666465'
        '62633535393863653338306565636431326438326235222c2270617468223a22242f626f64793a31352f626f64793a302f6e616d65733a30222c2272'
        '61775f7370616e5f736861323536223a2232613238633932313036613961633062653335643932653036346132313033353337646132623230653937'
        '383837326161393865363763386632623430366363222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132'
        '323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335'
        '3161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261'
        '313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862'
        '393266227d2c227370616e5f75746638223a5b39352c33382c39352c35345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f'
        '6e646974696f6e616c223a747275652c22656666656374223a22657863657074696f6e5f6d61746368696e67222c2265706f6368223a226561676572'
        '222c226964223a2262626664653033326538663735393630303864633865393630656232643336313633396339376337346638303763363866363864'
        '616439626562316436383134222c226b696e64223a2245786365707448616e646c6572222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223565313131386235613735613633656166666537343739346531653431333666323562343461646265653933393733353266376463376338'
        '3263393463373262222c2270617468223a22242f626f64793a31352f68616e646c6572733a30222c227261775f7370616e5f736861323536223a2233'
        '376536643532616139653063376136363631336330623638336234613035626339376339316638363939373437303666616565306163316434643330'
        '613135222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535'
        '3262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a22'
        '6d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130'
        '643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a'
        '5b39362c302c3130302c33335d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164'
        '222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c'
        '226964223a22616631303266396430356132386361623363623035666633393930646533313237393630613961336136613661313236323662623837'
        '35663363373938336339222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a22496d706f7274457272'
        '6f72222c22706172656e74223a2262626664653033326538663735393630303864633865393630656232643336313633396339376337346638303763'
        '363866363864616439626562316436383134222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f74797065222c227261775f'
        '7370616e5f736861323536223a2235653331663065393838346162646531623639653432623239313139616464643238356136613762636331323961'
        '353564326338393463396630373533313137222c227265667573616c223a22756e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c22'
        '7265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135'
        '6262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65'
        '222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663'
        '396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b39362c372c'
        '39362c31385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22'
        '6561676572222c226964223a223035663731363866373238393163653766303737663662646264346639313466373063663064323434323336333130'
        '3263666432376630356335643261666565222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22'
        '616631303266396430356132386361623363623035666633393930646533313237393630613961336136613661313236323662623837356633633739'
        '38336339222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f747970652f637478222c227261775f7370616e5f7368613235'
        '36223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366'
        '6565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64'
        '223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433'
        '326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f757466'
        '38223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265666665637422'
        '3a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964223a22343032353033373337313433316430646564646134'
        '34366234336461623332626261316633653631396561326331316634643162306630383930616138343731222c226b696e64223a2241737369676e22'
        '2c226d6f64756c65223a227363697079222c22706172656e74223a226262666465303332653866373539363030386463386539363065623264333631'
        '3633396339376337346638303763363866363864616439626562316436383134222c2270617468223a22242f626f64793a31352f68616e646c657273'
        '3a302f626f64793a30222c227261775f7370616e5f736861323536223a22616562366233313262353230393136346639363234313834313530623165'
        '36373333373432303465376462623061333362626436636264303465613065653566222c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235'
        '356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635'
        '392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163'
        '64326435353561343934313862393266227d2c227370616e5f75746638223a5b39372c342c39392c33365d7d2c7b2262696e64696e675f6b696e6422'
        '3a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22'
        '6561676572222c226964223a226636653564643464653062633862646561386530356133653537663038653932376334306331653231393431636335'
        '3138663339363432613839643036326534222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226d73'
        '67222c22706172656e74223a223430323530333733373134333164306465646461343436623433646162333262626131663365363139656132633131'
        '6634643162306630383930616138343731222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a302f7461726765'
        '74733a30222c227261775f7370616e5f736861323536223a226534366233323031363565656339316536333434666131303334306435623332303833'
        '3034643663616432396430643561656431383436366431643964383065222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a5b39372c342c39372c375d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a2265623030303861366536393433653462'
        '376636303435376235303836313363393835623132306634636561646633353261353130323236346531393034363235222c226b696e64223a225374'
        '6f7265222c226d6f64756c65223a227363697079222c22706172656e74223a2266366535646434646530626338626465613865303561336535376630'
        '386539323763343063316532313934316363353138663339363432613839643036326534222c2270617468223a22242f626f64793a31352f68616e64'
        '6c6572733a302f626f64793a302f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574'
        '696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366'
        '30336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572'
        '6365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762'
        '6538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162'
        '696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a226f70657261746f725f70726f746f'
        '636f6c222c2265706f6368223a226561676572222c226964223a22613239646265626638366634306261353366373461666461653239643038393735'
        '31373135656361353630366566663734313663613630633162386563373338222c226b696e64223a2242696e4f70222c226d6f64756c65223a227363'
        '697079222c22706172656e74223a22343032353033373337313433316430646564646134343662343364616233326262613166336536313965613263'
        '31316634643162306630383930616138343731222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a302f76616c'
        '7565222c227261775f7370616e5f736861323536223a2266396232633961306232663632353563613637306437313063626163613562646362333764'
        '306636643766653639336463616531333931653862373130626634222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f70'
        '65223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531'
        '3864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273686132'
        '3536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561'
        '343934313862393266227d2c227370616e5f75746638223a5b39372c31302c39392c33365d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a747275652c22656666656374223a226f70657261746f725f70726f746f636f6c222c2265706f6368223a22'
        '6561676572222c226964223a223464373431373366646261646234613564346364313961303631313238636365623466323136366539666164363133'
        '6638656162323364633663306635613630222c226b696e64223a2242696e4f70222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '226132396462656266383666343062613533663734616664616532396430383937353137313565636135363036656666373431366361363063316238'
        '6563373338222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a302f76616c75652f6c656674222c227261775f'
        '7370616e5f736861323536223a2235396438643835623562613630343239623639623438653532346565643831376165623663333865313362383533'
        '363665353764656237363765383039333237222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336'
        '656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335316122'
        '2c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161'
        '643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266'
        '227d2c227370616e5f75746638223a5b39372c31302c39382c35325d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e6469'
        '74696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a2233633336346133613735326235623136373963623461623466'
        '353734313830383133613633376433373262386538323231366162636366326339663261353135222c226b696e64223a22436f6e7374616e74222c22'
        '6d6f64756c65223a227363697079222c22706172656e74223a2234643734313733666462616462346135643463643139613036313132386363656234'
        '663231363665396661643631336638656162323364633663306635613630222c2270617468223a22242f626f64793a31352f68616e646c6572733a30'
        '2f626f64793a302f76616c75652f6c6566742f6c656674222c227261775f7370616e5f736861323536223a2262626561626466393631616633363833'
        '326161373565363339653065393633373938396232396365653263333738343361643563363431333262323264316233222c227265736f6c7574696f'
        '6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033'
        '6262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365'
        '223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538'
        '363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b39372c31302c39372c36365d7d2c'
        '7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c22'
        '6964223a2234666661643639343763356238326130633765353635383638376164343239386561323265336639313038396362326633386339333332'
        '356531366539386266222c226b696e64223a22416464222c226d6f64756c65223a227363697079222c22706172656e74223a22346437343137336664'
        '62616462346135643463643139613036313132386363656234663231363665396661643631336638656162323364633663306635613630222c227061'
        '7468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a302f76616c75652f6c6566742f6f70222c227261775f7370616e5f7368'
        '61323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266'
        '6663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432'
        '336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f'
        '75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f63'
        '68223a226561676572222c226964223a2236386439306233616239396362616533623030336338663637353263386237396137313365666432343463'
        '393866373632386433666331386266353833656232222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c2270'
        '6172656e74223a2234643734313733666462616462346135643463643139613036313132386363656234663231363665396661643631336638656162'
        '323364633663306635613630222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a302f76616c75652f6c656674'
        '2f7269676874222c227261775f7370616e5f736861323536223a22643532646661616236636435663262373063393735386639323137306239666161'
        '61393937316336646239363061626234623234613633326636633436346132222c227265736f6c7574696f6e223a22756e7265736f6c766564222c22'
        '73636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337'
        '326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22'
        '736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264'
        '35353561343934313862393266227d2c227370616e5f75746638223a5b39382c31302c39382c35325d7d2c7b226361706162696c697479223a227065'
        '6e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22393430626235313266343032'
        '34373933313461323839616235393261363033306135376538343436306235656664616333626634326439366131626435393039222c226b696e6422'
        '3a22416464222c226d6f64756c65223a227363697079222c22706172656e74223a226132396462656266383666343062613533663734616664616532'
        '3964303839373531373135656361353630366566663734313663613630633162386563373338222c2270617468223a22242f626f64793a31352f6861'
        '6e646c6572733a302f626f64793a302f76616c75652f6f70222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c69'
        '7479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a223134366361'
        '363366666661663235393234663130393061366166343035623565636135653463613966656432376663343638326636333262393861323766346422'
        '2c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a226132396462656266383666343062'
        '6135336637346166646165323964303839373531373135656361353630366566663734313663613630633162386563373338222c2270617468223a22'
        '242f626f64793a31352f68616e646c6572733a302f626f64793a302f76616c75652f7269676874222c227261775f7370616e5f736861323536223a22'
        '636566306365343266613839353064623561303932313931633165316638333531656437666439333238313433663937366531363962303866393039'
        '61663634222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565'
        '353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a'
        '226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261'
        '30643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574663822'
        '3a5b39392c31302c39392c33365d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22'
        '656666656374223a22657863657074696f6e5f70726f746f636f6c222c2265706f6368223a226561676572222c226964223a22363565623563356338'
        '35656132363937383835383565623332353732373632386232636163303864663835633161353538383236396139356230356266393736222c226b69'
        '6e64223a225261697365222c226d6f64756c65223a227363697079222c22706172656e74223a22626266646530333265386637353936303038646338'
        '65393630656232643336313633396339376337346638303763363866363864616439626562316436383134222c2270617468223a22242f626f64793a'
        '31352f68616e646c6572733a302f626f64793a31222c227261775f7370616e5f736861323536223a2262333863623733306237373937353536376435'
        '653262333661303665366236386239323664373033353031623238393765313530623064346166353663326239222c227265736f6c7574696f6e223a'
        '22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231'
        '3263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b'
        '226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036'
        '383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130302c342c3130302c33335d7d2c7b22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c'
        '6261636b5f64796e616d6963222c2265706f6368223a226561676572222c226964223a22346436343837363436636236303230363031353162333966'
        '64386461346637613830376165623562653735393964613637313031613665326237663735666330222c22696d706f72745f63616e64696461746522'
        '3a6e756c6c2c226b696e64223a2243616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c2270'
        '6172656e74223a2236356562356335633835656132363937383835383565623332353732373632386232636163303864663835633161353538383236'
        '396139356230356266393736222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f657863222c22706f7373'
        '69626c655f64796e616d69635f656666656374223a22756e7265736f6c7665645f63616c6c61626c65222c227261775f7370616e5f73686132353622'
        '3a2233623334323562383364666162323762323663316562316637376134643333323666346234643162636362633965633364316436333338636638'
        '306339613965222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2272756e74696d655f62696e64696e675f70726f76656e223a66'
        '616c73652c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533'
        '386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a'
        '343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433'
        '64616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130302c31302c3130302c32365d7d2c7b2262696e64696e67'
        '5f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22313436646263336666306238616337353034'
        '33363663623862303138323565396163353333623464303933313434656466613161343732643536616131313735222c226b696e64223a224e616d65'
        '222c226d6f64756c65223a227363697079222c226e616d65223a22496d706f72744572726f72222c22706172656e74223a2234643634383736343663'
        '623630323036303135316233396664386461346637613830376165623562653735393964613637313031613665326237663735666330222c22706174'
        '68223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f6578632f66756e63222c227261775f7370616e5f736861323536223a'
        '223565333166306539383834616264653162363965343262323931313961646464323835613661376263633132396135356432633839346339663037'
        '3533313137222c227265667573616c223a22756e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c227265736f6c7574696f6e223a22'
        '756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132'
        '63343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22'
        '6279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638'
        '3332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130302c31302c3130302c32315d7d2c7b22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964'
        '223a22313662313066343065633438373134326534333234363039636236386239353263633734643461333564613164383437656537396436656166'
        '61366366383065222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2231343664626333666630'
        '623861633735303433363663623862303138323565396163353333623464303933313434656466613161343732643536616131313735222c22706174'
        '68223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f6578632f66756e632f637478222c227261775f7370616e5f73686132'
        '3536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663'
        '666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e'
        '64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a6e756c6c7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361'
        '706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a'
        '223865336533663839643531643936313036373835306166346635653531346438303166386233396531363665386239366132346464306232333637'
        '3364613733222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226d7367222c22706172656e74223a'
        '223464363438373634366362363032303630313531623339666438646134663761383037616562356265373539396461363731303161366532623766'
        '3735666330222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f6578632f617267733a30222c227261775f'
        '7370616e5f736861323536223a2265343662333230313635656563393165363334346661313033343064356233323038333034643663616432396430'
        '643561656431383436366431643964383065222c227265667573616c223a226d756c7469706c655f62696e64696e6773222c227265736f6c7574696f'
        '6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033'
        '6262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365'
        '223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538'
        '363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130302c32322c3130302c32355d'
        '7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22656167657222'
        '2c226964223a223766353462356465613738353631383262613264613831393436643537343139353665343230613437373735343762373139333439'
        '3861346665643733333931222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22386533653366'
        '38396435316439363130363738353061663466356535313464383031663862333965313636653862393661323464643062323336373364613733222c'
        '2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f6578632f617267733a302f637478222c227261775f737061'
        '6e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662'
        '303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f'
        '70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165'
        '61663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c2273'
        '70616e5f75746638223a6e756c6c7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f61'
        '64222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22656167657222'
        '2c226964223a223133613965323265333239626466353733386135386466336538376465326461383233643763343463363739353533643036323033'
        '6532623436323638323465222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a2265222c2270617265'
        '6e74223a2236356562356335633835656132363937383835383565623332353732373632386232636163303864663835633161353538383236396139'
        '356230356266393736222c2270617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f6361757365222c227261775f73'
        '70616e5f736861323536223a223366373962623762343335623035333231363531646165666433373463646336383164633036666161363565333734'
        '6533383333376238386361303436646561222c227265667573616c223a226d756c7469706c655f62696e64696e6773222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130302c33322c3130302c33335d7d'
        '2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c'
        '226964223a22356534636430333466626237393230623038376261643037326231613934393761663638313061343539373037346430303363343238'
        '32353631333362323534222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2231336139653232'
        '653332396264663537333861353864663365383764653264613832336437633434633637393535336430363230336532623436323638323465222c22'
        '70617468223a22242f626f64793a31352f68616e646c6572733a302f626f64793a312f63617573652f637478222c227261775f7370616e5f73686132'
        '3536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663'
        '666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e'
        '64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c226566666563'
        '74223a22696d706f7274222c2265706f6368223a226561676572222c226964223a223337326363613865333162653637366134636532366165643830'
        '3337633264336138356236393665363935623538313461313536646438373538303436346465222c226b696e64223a22496d706f727446726f6d222c'
        '226d6f64756c65223a227363697079222c22706172656e74223a22313232333665656136623033626666636665653532623363613562623361386366'
        '30336262313263343961643533386235356337326265313864306133353161222c2270617468223a22242f626f64793a3136222c227261775f737061'
        '6e5f736861323536223a2238346566343034653737663532626363383533303764346635383639626364386261316436653536623537663139303063'
        '303630313462363831373936373839222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561'
        '3662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273'
        '636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861'
        '316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c'
        '227370616e5f75746638223a5b3130332c302c3130332c34365d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d'
        '706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f63'
        '68223a226561676572222c226964223a2264363933306165323331356130343331353932303239353531616362653539303630313033383533636633'
        '653639356566386632623237343561323961356361222c226b696e64223a22616c696173222c226d6f64756c65223a227363697079222c226e616d65'
        '223a22507974657374546573746572222c22706172656e74223a22333732636361386533316265363736613463653236616564383033376332643361'
        '38356236393665363935623538313461313536646438373538303436346465222c2270617468223a22242f626f64793a31362f6e616d65733a30222c'
        '227261775f7370616e5f736861323536223a223236386131343432343239396638343462306339643537346665336464653330343133613561346634'
        '6139323962373264653664353734616162313732323836222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a5b3130332c33342c3130332c34365d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572'
        '222c226964223a2231346638623334326466626433336338313535343133626261363431333963393435613637626566643361323661356432633030'
        '323337323831316163393063222c226b696e64223a2241737369676e222c226d6f64756c65223a227363697079222c22706172656e74223a22313232'
        '333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061333531'
        '61222c2270617468223a22242f626f64793a3137222c227261775f7370616e5f736861323536223a2233633965373538663966616232643730326264'
        '326666373231336461653437613131326565346137383330383564346239326334323663616234643062373764222c227265736f6c7574696f6e223a'
        '22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231'
        '3263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b'
        '226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036'
        '383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130342c302c3130342c32395d7d2c7b22'
        '62696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66'
        '616c73652c2265706f6368223a226561676572222c226964223a22333133313962333763666435333864313365306561666135363139653730303961'
        '62323431633439373035663261323761656563636662393465643538393664222c226b696e64223a224e616d65222c226d6f64756c65223a22736369'
        '7079222c226e616d65223a2274657374222c22706172656e74223a223134663862333432646662643333633831353534313362626136343133396339'
        '3435613637626566643361323661356432633030323337323831316163393063222c2270617468223a22242f626f64793a31372f746172676574733a'
        '30222c227261775f7370616e5f736861323536223a223966383664303831383834633764363539613266656161306335356164303135613362663466'
        '3162326230623832326364313564366331356230663030613038222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138'
        '64306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368613235'
        '36223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134'
        '3934313862393266227d2c227370616e5f75746638223a5b3130342c302c3130342c345d7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2262306130633338626635336238626435'
        '616261626239623861353738363135636164353330666561373039643536353432306364613733363963613137663338222c226b696e64223a225374'
        '6f7265222c226d6f64756c65223a227363697079222c22706172656e74223a2233313331396233376366643533386431336530656166613536313965'
        '373030396162323431633439373035663261323761656563636662393465643538393664222c2270617468223a22242f626f64793a31372f74617267'
        '6574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c'
        '2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563'
        '37326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c'
        '22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432'
        '6435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c22656666656374223a2263616c6c5f63616c6c6261636b5f64796e616d6963222c2265706f6368223a'
        '226561676572222c226964223a2236646434333930346462316134316636356466653635383133623639336137353962613130396362336364653661'
        '356636643365623661323463643466663732222c22696d706f72745f63616e646964617465223a6e756c6c2c226b696e64223a2243616c6c222c226c'
        '65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e74223a223134663862333432646662643333'
        '6338313535343133626261363431333963393435613637626566643361323661356432633030323337323831316163393063222c2270617468223a22'
        '242f626f64793a31372f76616c7565222c22706f737369626c655f64796e616d69635f656666656374223a22756e7265736f6c7665645f63616c6c61'
        '626c65222c227261775f7370616e5f736861323536223a22313937323161366533383531633237306265663432366131323765636164333537633831'
        '62356536356334333239396538323265623936306163393465333637222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2272756e'
        '74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a22313232333665656136623033626666636665653532623363'
        '61356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f6475'
        '6c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464'
        '3663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b313034'
        '2c372c3130342c32395d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c2269'
        '64223a223365663063663533353164643062613463376165646536653736336536353939356237303834353034336361383936303432666138613064'
        '6164356534623634222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a225079746573745465737465'
        '72222c22706172656e74223a223664643433393034646231613431663635646665363538313362363933613735396261313039636233636465366135'
        '6636643365623661323463643466663732222c2270617468223a22242f626f64793a31372f76616c75652f66756e63222c227261775f7370616e5f73'
        '6861323536223a2232363861313434323432393966383434623063396435373466653364646533303431336135613466346139323962373264653664'
        '353734616162313732323836222c227265667573616c223a226d756c7469706c655f62696e64696e6773222c227265736f6c7574696f6e223a22756e'
        '7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334'
        '3961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279'
        '746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332'
        '316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130342c372c3130342c31395d7d2c7b22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a'
        '223232363165613639653134313764313863393064666132353731363832353465663331343038316637323337373636376462326535303835626265'
        '3233396566222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22336566306366353335316464'
        '30626134633761656465366537363365363539393562373038343530343363613839363034326661386130646164356534623634222c227061746822'
        '3a22242f626f64793a31372f76616c75652f66756e632f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630'
        '336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b2262696e64696e'
        '675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2232316536326630643463653137353737'
        '313062393064636265363439653936346666323336363634636631623036386265336539393137363230306535356331222c226b696e64223a224e61'
        '6d65222c226d6f64756c65223a227363697079222c226e616d65223a225f5f6e616d655f5f222c22706172656e74223a223664643433393034646231'
        '6134316636356466653635383133623639336137353962613130396362336364653661356636643365623661323463643466663732222c2270617468'
        '223a22242f626f64793a31372f76616c75652f617267733a30222c227261775f7370616e5f736861323536223a223232326364356261373139343564'
        '3234636631613435663333333239386264333736623165613464666631313238643039656330393562653664326233303736222c227265667573616c'
        '223a22756e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a5b3130342c32302c3130342c32385d7d2c7b226361706162696c697479223a227065'
        '6e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223435323238353033313663'
        '3330363631396365623961353931363934343339373765633664376561396530623134336136626132646139326262626636343537222c226b696e64'
        '223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22323165363266306434636531373537373130623930646362'
        '65363439653936346666323336363634636631623036386265336539393137363230306535356331222c2270617468223a22242f626f64793a31372f'
        '76616c75652f617267733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e726573'
        '6f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164'
        '3533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573'
        '223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630'
        '343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e'
        '64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2264656c6574655f7772697465222c2265706f6368223a2265'
        '61676572222c226964223a22363038353464613363346530333836393230393236363661316132363664646263613164336564633761303662626666'
        '66326633613363663662336238653334222c226b696e64223a2244656c657465222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430'
        '6133353161222c2270617468223a22242f626f64793a3138222c227261775f7370616e5f736861323536223a22303434613962313164336533393962'
        '31376135346662376637343265626136303665373236396633366561343937616536363362376330666563363439623739222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630'
        '336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130352c302c3130352c31365d'
        '7d2c7b2262696e64696e675f6b696e64223a2244656c222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a66616c73652c2265706f6368223a226561676572222c226964223a2262396166326664333761306665666166333835386336393737616133383966'
        '626438656162396634313866663630616161663438383339663864356362326536222c226b696e64223a224e616d65222c226d6f64756c65223a2273'
        '63697079222c226e616d65223a22507974657374546573746572222c22706172656e74223a2236303835346461336334653033383639323039323636'
        '366131613236366464626361316433656463376130366262666666326633613363663662336238653334222c2270617468223a22242f626f64793a31'
        '382f746172676574733a30222c227261775f7370616e5f736861323536223a2232363861313434323432393966383434623063396435373466653364'
        '646533303431336135613466346139323962373264653664353734616162313732323836222c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338'
        '6235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a34'
        '3635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364'
        '616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130352c342c3130352c31365d7d2c7b226361706162696c6974'
        '79223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a226261663838'
        '346235346238316234316361386439623332643132386665343733373964663536613665326438616264626438353337326130633065333562353322'
        '2c226b696e64223a2244656c222c226d6f64756c65223a227363697079222c22706172656e74223a2262396166326664333761306665666166333835'
        '386336393737616133383966626438656162396634313866663630616161663438383339663864356362326536222c2270617468223a22242f626f64'
        '793a31382f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e72'
        '65736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439'
        '61643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22627974'
        '6573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231'
        '6630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f636822'
        '3a226561676572222c226964223a22666530623764616463313931656431643461303934313434663866356435666166393761303364346463643266'
        '62646164663037643763663831396231623135222c226b696e64223a2241737369676e222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531'
        '3864306133353161222c2270617468223a22242f626f64793a3139222c227261775f7370616e5f736861323536223a22363533313265373263386438'
        '35353364633138666362386138333437366537306137323138613562663031386633323831393432363735316233323539643538222c227265736f6c'
        '7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138'
        '636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f'
        '75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663'
        '37626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130382c302c3132372c'
        '315d7d2c7b2262696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f'
        '6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22646135363832626665336439646562313430386164316435383431'
        '62323633303538613062623964313932373931623162313933353161353438396337363335222c226b696e64223a224e616d65222c226d6f64756c65'
        '223a227363697079222c226e616d65223a227375626d6f64756c6573222c22706172656e74223a226665306237646164633139316564316434613039'
        '3431343466386635643566616639376130336434646364326662646164663037643763663831396231623135222c2270617468223a22242f626f6479'
        '3a31392f746172676574733a30222c227261775f7370616e5f736861323536223a226161336636333832323739306362316131636636613166643533'
        '3166333636643961616266633937616263636537383961656534633364393138346231333539222c227265736f6c7574696f6e223a22756e7265736f'
        '6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435'
        '33386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22627974657322'
        '3a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034'
        '3364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130382c302c3130382c31305d7d2c7b226361706162696c'
        '697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22333737'
        '346438313937353334326266386633366332386662653933313464356430616666633734616136383439303638623836316362303633613733363433'
        '63222c226b696e64223a2253746f7265222c226d6f64756c65223a227363697079222c22706172656e74223a22646135363832626665336439646562'
        '31343038616431643538343162323633303538613062623964313932373931623162313933353161353438396337363335222c2270617468223a2224'
        '2f626f64793a31392f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a'
        '22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231'
        '3263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b'
        '226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036'
        '383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22316437643064'
        '39666331646433343464376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c'
        '226b696e64223a224c697374222c226d6f64756c65223a227363697079222c22706172656e74223a2266653062376461646331393165643164346130'
        '393431343466386635643566616639376130336434646364326662646164663037643763663831396231623135222c2270617468223a22242f626f64'
        '793a31392f76616c7565222c227261775f7370616e5f736861323536223a223631313165386539393463383636353333643439626662633166623733'
        '6437613939313636656331323034356661333239306431366239373636653838333135222c227265736f6c7574696f6e223a22756e7265736f6c7665'
        '64222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862'
        '35356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3436'
        '35392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461'
        '6364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130382c31332c3132372c315d7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22333938656566'
        '61346332373736366235646338333135376162376531626237393435656562376235303936376531346139623537333162323361356434316361222c'
        '226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a22316437643064396663316464333434'
        '64376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a2224'
        '2f626f64793a31392f76616c75652f656c74733a30222c227261775f7370616e5f736861323536223a22333961363464316135633262373636323539'
        '62366634633762663731303339313566333030326164396434613666323561376430366236653664323937356166222c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262'
        '313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a'
        '7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630'
        '36383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3130392c342c3130392c31335d7d2c7b'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22'
        '6964223a2230346162336235323733313961316632616664633435363962303264393138336533623438323832386162646336326336316666306439'
        '396537323661326634222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764'
        '306439666331646433343464376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761'
        '222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a31222c227261775f7370616e5f736861323536223a2261373362613066'
        '366239346635393362393865356135333732626533653562303565393235346438613166643833383432656333626632636236383763653133222c22'
        '7265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135'
        '6262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65'
        '222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663'
        '396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3131302c34'
        '2c3131302c31355d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368'
        '223a226561676572222c226964223a223936643531393261663361646230383431643065663061653332633064373232623566306363343139376437'
        '3831323266646137646562653164623930636132222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c227061'
        '72656e74223a223164376430643966633164643334346437636237393936633435636361353232353964393637306436613538653262633139663333'
        '6338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a32222c227261775f7370616e5f7368613235'
        '36223a223234393739643165316335376536623431396332656530326231666539323365306337633338306439313332656361363730333636663464'
        '6137363537626539222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666'
        '63666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b69'
        '6e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233'
        '6433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75'
        '746638223a5b3131312c342c3131312c31345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66'
        '616c73652c2265706f6368223a226561676572222c226964223a22346561343666636431626465353063323336346438356263373731343134313037'
        '62393863656239353337336334636661616433343836316633613837666539222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a'
        '227363697079222c22706172656e74223a22316437643064396663316464333434643763623739393663343563636135323235396439363730643661'
        '35386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a33222c22726177'
        '5f7370616e5f736861323536223a22656434326431326262626166656632306235383365343131313339633164373265386464376335663861336363'
        '33366233653530313938643466623334316436222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233'
        '366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161'
        '222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131'
        '616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138623932'
        '66227d2c227370616e5f75746638223a5b3131322c342c3131322c31395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2261326364356563306138653536326165366436383838'
        '303031386462633039313965386361626265636634396332623465316630316266376364643763383336222c226b696e64223a22436f6e7374616e74'
        '222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764306439666331646433343464376362373939366334356363613532'
        '323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f65'
        '6c74733a34222c227261775f7370616e5f736861323536223a2230613733656338366232623361313065393531666535376166383038663463303333'
        '616537343939316437343636653533323139393031363438646337306166222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273'
        '636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732'
        '6265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273'
        '6861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435'
        '353561343934313862393266227d2c227370616e5f75746638223a5b3131332c342c3131332c395d7d2c7b226361706162696c697479223a2270656e'
        '64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22356133353933313235333731'
        '66386461633664633836646163633163656239663230303165363835613437656239333466616436376436356536313238376330222c226b696e6422'
        '3a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a22316437643064396663316464333434643763623739'
        '39366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a'
        '31392f76616c75652f656c74733a35222c227261775f7370616e5f736861323536223a22386163666433636165663434376634346562653066306236'
        '34343136383563623064326332396166313131333936383464366537316265376434346466323031222c227265736f6c7574696f6e223a22756e7265'
        '736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961'
        '643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262797465'
        '73223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166'
        '30343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3131342c342c3131342c31335d7d2c7b226361706162'
        '696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2237'
        '353762323332623030623337613637306365313762326164376137646432363161316165396362376131333765663339633438373864386566376563'
        '666564222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764306439666331'
        '646433343464376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c22706174'
        '68223a22242f626f64793a31392f76616c75652f656c74733a36222c227261775f7370616e5f736861323536223a2262386563306264383632356461'
        '323834656461313838633161373961336363666535663731633133626533393762366334626362643761313461346434653437222c227265736f6c75'
        '74696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863'
        '6630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75'
        '726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337'
        '626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3131352c342c3131352c31'
        '355d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22656167'
        '6572222c226964223a223163333461616163393532313964393237343532393231633337343238663835376363656631366231373064353332613739'
        '3437313965663563613566626236222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '223164376430643966633164643334346437636237393936633435636361353232353964393637306436613538653262633139663333633837363963'
        '3066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a37222c227261775f7370616e5f736861323536223a223964'
        '363765346330316235386636613963383638386163373936373366393162353464633736613961353235653131306165346566313436396630613334'
        '3932222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532'
        '62336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d'
        '6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064'
        '3364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b'
        '3131362c342c3131362c31375d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22'
        '65706f6368223a226561676572222c226964223a22366264393566653538396666666334343035323731393533613764643830383336303866393864'
        '35396335376532333264313166383236396234396138366437222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079'
        '222c22706172656e74223a22316437643064396663316464333434643763623739393663343563636135323235396439363730643661353865326263'
        '31396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a38222c227261775f7370616e5f'
        '736861323536223a22363438613862366639653535353861663262626261646431323461616264643134366263633138636433326237323865343039'
        '64383964383132633866656161222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662'
        '303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f'
        '70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165'
        '61663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c2273'
        '70616e5f75746638223a5b3131372c342c3131372c385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e61'
        '6c223a66616c73652c2265706f6368223a226561676572222c226964223a226439333436316264373438303434353862346461363734373930653466'
        '6230666334666661366434656266316338323436626138356233336265656337316231222c226b696e64223a22436f6e7374616e74222c226d6f6475'
        '6c65223a227363697079222c22706172656e74223a223164376430643966633164643334346437636237393936633435636361353232353964393637'
        '3064366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a39222c'
        '227261775f7370616e5f736861323536223a223830363037316237333532616235366439633737656639653965346531373033343435623935333135'
        '6233653264623631653735646233643539363065646334222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a5b3131382c342c3131382c31325d7d2c7b226361706162696c697479223a2270656e64696e67222c'
        '22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22663862616164326439633931623464343637'
        '34643834323931383435326631616630633832653364393461336533336264613539343038306431393033353132222c226b696e64223a22436f6e73'
        '74616e74222c226d6f64756c65223a227363697079222c22706172656e74223a22316437643064396663316464333434643763623739393663343563'
        '63613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c'
        '75652f656c74733a3130222c227261775f7370616e5f736861323536223a223539353438653438396635323733323132626564323232333062393033'
        '3539396434303865323836356263343334656536373765323063633637626439363530222c227265736f6c7574696f6e223a22756e7265736f6c7665'
        '64222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862'
        '35356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3436'
        '35392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461'
        '6364326435353561343934313862393266227d2c227370616e5f75746638223a5b3131392c342c3131392c31335d7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22383265363037'
        '37383833326665663834613135323138396430636237626639353535376364336435636430646265336138663432363333613337653739663465222c'
        '226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a22316437643064396663316464333434'
        '64376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a2224'
        '2f626f64793a31392f76616c75652f656c74733a3131222c227261775f7370616e5f736861323536223a226261353638633363376461356635663461'
        '3834623439633365663138313834383535613765363365396239373438633236373662666263323336666338616666222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3132302c342c3132302c395d7d2c7b'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22'
        '6964223a2264356132353035316634373133646434623263363134343134333263316635666533653135616631336362653132633030386464363364'
        '333033393965316562222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764'
        '306439666331646433343464376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761'
        '222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a3132222c227261775f7370616e5f736861323536223a22653765353633'
        '32343663343865623661366339646165303039353335313038306561653439323736323439396466663264653631386262346437376530363463222c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361'
        '356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c'
        '65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436'
        '63396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3132312c'
        '342c3132312c31345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f63'
        '68223a226561676572222c226964223a2230306266643237396366636138613034346632303630356630643336373738396266623363323336666461'
        '663838653731303634303264653238633739393863222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c2270'
        '6172656e74223a2231643764306439666331646433343464376362373939366334356363613532323539643936373064366135386532626331396633'
        '336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a3133222c227261775f7370616e5f736861'
        '323536223a22653161326638383930653033623965356639376439353065646437616266303434363833363563616462343062616365313738306538'
        '39643135316639396533222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362'
        '666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f'
        '6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634'
        '32336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e'
        '5f75746638223a5b3132322c342c3132322c31325d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a66616c73652c2265706f6368223a226561676572222c226964223a2232616565343535616139656165626636326632653462663864613437333134'
        '336166633466336434336166316133343635393832336137303033393464336132222c226b696e64223a22436f6e7374616e74222c226d6f64756c65'
        '223a227363697079222c22706172656e74223a2231643764306439666331646433343464376362373939366334356363613532323539643936373064'
        '366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a3134222c22'
        '7261775f7370616e5f736861323536223a22353330613433623434663032346536663632336130373535363565623966373866323831376330336361'
        '35326632656135343062663238313361336433326565222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231'
        '323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133'
        '353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22'
        '613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138'
        '62393266227d2c227370616e5f75746638223a5b3132332c342c3132332c31325d7d2c7b226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2263656230373466323236363964623837626134'
        '343638363964376366636162323437313962653062383866396536666230643835353238363462326534616131222c226b696e64223a22436f6e7374'
        '616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764306439666331646433343464376362373939366334356363'
        '613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a22242f626f64793a31392f76616c75'
        '652f656c74733a3135222c227261775f7370616e5f736861323536223a22326335396264653837326164326230363032633033393663396531323935'
        '35613562306165323961653834366530616161306636356361376230663133626437222c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235'
        '356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635'
        '392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163'
        '64326435353561343934313862393266227d2c227370616e5f75746638223a5b3132342c342c3132342c31335d7d2c7b226361706162696c69747922'
        '3a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2261373735663132'
        '326265366465343664343537636366653230303832636338393934363063666130643235623564303166343833613362336563356434343034222c22'
        '6b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764306439666331646433343464'
        '376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761222c2270617468223a22242f'
        '626f64793a31392f76616c75652f656c74733a3136222c227261775f7370616e5f736861323536223a22663030326532653835386264623962343637'
        '30336566333961376366356530353437343431373336333637383537393066363636326438393131376236613465222c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262'
        '313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a'
        '7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630'
        '36383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3132352c342c3132352c31335d7d2c7b'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22'
        '6964223a2263393830396233383934656339306639643634383634303330373537666637386633343864306638666261333963643761363130376638'
        '656530316138623536222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2231643764'
        '306439666331646433343464376362373939366334356363613532323539643936373064366135386532626331396633336338373639633066353761'
        '222c2270617468223a22242f626f64793a31392f76616c75652f656c74733a3137222c227261775f7370616e5f736861323536223a22653832366337'
        '35333534633332373237326565346266653134383831383130666233633562393133633262643863353937313165623431613039633037376233222c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361'
        '356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c'
        '65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436'
        '63396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3132362c'
        '342c3132362c31315d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f63'
        '68223a226561676572222c226964223a2236336434653864663861646362343839333839376336396635383764653434366165326234333562393464'
        '326634306239643663366530386339323834643562222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223164376430643966633164643334346437636237393936633435636361353232353964393637306436613538653262633139663333633837'
        '3639633066353761222c2270617468223a22242f626f64793a31392f76616c75652f637478222c227261775f7370616e5f736861323536223a6e756c'
        '6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233'
        '6361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64'
        '756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364'
        '643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c'
        '6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d70'
        '6f7274222c2265706f6368223a226561676572222c226964223a22373035343039613263666666393965383531323639636136303433383831366139'
        '63623264633333353263653062323938393061373462356237343661663765222c226b696e64223a22496d706f7274222c226d6f64756c65223a2273'
        '63697079222c22706172656e74223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164'
        '3533386235356337326265313864306133353161222c2270617468223a22242f626f64793a3230222c227261775f7370616e5f736861323536223a22'
        '646532616261646538333263386533353061316264633938636663646231653230326163343734396335666335316134613937306434313733366236'
        '64663563222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565'
        '353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a'
        '226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261'
        '30643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574663822'
        '3a5b3133302c302c3133302c395d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22'
        '6964223a2239396235313839323938303035663235306236643333303130336166323164373834363337383366366435396264643161363530643135'
        '323735626136656162222c226b696e64223a22616c696173222c226d6f64756c65223a227363697079222c226e616d65223a226f73222c2270617265'
        '6e74223a2237303534303961326366666639396538353132363963613630343338383136613963623264633333353263653062323938393061373462'
        '356237343661663765222c2270617468223a22242f626f64793a32302f6e616d65733a30222c227261775f7370616e5f736861323536223a22383430'
        '613864636665616539353936366138373062306235323537393937636539346362633139646439373934303964313637316432653933613965306465'
        '36222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262'
        '336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f'
        '64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433'
        '64643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b31'
        '33302c372c3133302c395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c226566'
        '66656374223a2274727574685f70726f746f636f6c222c2265706f6368223a226561676572222c226964223a22626632396461643930363736373565'
        '39343065313763363364376131373066626633613466353962616265373533663164636230663566613237623738393166222c226b696e64223a2249'
        '66222c226d6f64756c65223a227363697079222c22706172656e74223a22313232333665656136623033626666636665653532623363613562623361'
        '38636630336262313263343961643533386235356337326265313864306133353161222c2270617468223a22242f626f64793a3231222c227261775f'
        '7370616e5f736861323536223a2263376238646661643237633638303139623533363661666465303233626264613064356134643737336235653437'
        '643464323163626665616333396665643131222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336'
        '656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335316122'
        '2c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161'
        '643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266'
        '227d2c227370616e5f75746638223a5b3133312c302c3133322c32385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e64'
        '6974696f6e616c223a747275652c22656666656374223a226f70657261746f725f70726f746f636f6c222c2265706f6368223a226561676572222c22'
        '6964223a2235316361346465623331353666373563316439343835613131376561363962303064353730313039393930386134623563346138383435'
        '663732333436633630222c226b696e64223a22556e6172794f70222c226d6f64756c65223a227363697079222c22706172656e74223a226266323964'
        '616439303637363735653934306531376336336437613137306662663361346635396261626537353366316463623066356661323762373839316622'
        '2c2270617468223a22242f626f64793a32312f74657374222c227261775f7370616e5f736861323536223a2266613162373938626335343862666432'
        '623364663832396166393761613838623130633838653130363733323333356638333765343935313863343161636434222c227265736f6c7574696f'
        '6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033'
        '6262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365'
        '223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538'
        '363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133312c332c3133312c32385d7d'
        '2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c'
        '226964223a22396335333065643430376339386131626663626664376564373864306234386238336336656261323838336239356430663138353935'
        '36353562646134356136222c226b696e64223a224e6f74222c226d6f64756c65223a227363697079222c22706172656e74223a223531636134646562'
        '3331353666373563316439343835613131376561363962303064353730313039393930386134623563346138383435663732333436633630222c2270'
        '617468223a22242f626f64793a32312f746573742f6f70222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262'
        '313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a'
        '7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630'
        '36383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c6974'
        '79223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c6261636b5f64796e61'
        '6d6963222c2265706f6368223a226561676572222c226964223a22303866303137316136356663383630656565303832623539376434366663616663'
        '30363538343266663066623261623039333432366562666231626237363634222c22696d706f72745f63616e646964617465223a6e756c6c2c226b69'
        '6e64223a2243616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e74223a2235'
        '316361346465623331353666373563316439343835613131376561363962303064353730313039393930386134623563346138383435663732333436'
        '633630222c2270617468223a22242f626f64793a32312f746573742f6f706572616e64222c22706f737369626c655f64796e616d69635f6566666563'
        '74223a226174747269627574655f6469737061746368222c227261775f7370616e5f736861323536223a226132313434633065643563653332346537'
        '3138653239376435356563666436626537356636656334316132323933653163303032643431613038396439643866222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2272756e74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a223132323336'
        '656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335316122'
        '2c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161'
        '643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266'
        '227d2c227370616e5f75746638223a5b3133312c372c3133312c32385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e64'
        '6974696f6e616c223a747275652c22656666656374223a226174747269627574655f6469737061746368222c2265706f6368223a226561676572222c'
        '226964223a22393031396166653564633163326563363839356363316666366465376338316432366237633836353262646336633363323937656365'
        '63383164376265316634222c226b696e64223a22417474726962757465222c226d6f64756c65223a227363697079222c22706172656e74223a223038'
        '663031373161363566633836306565653038326235393764343666636166633036353834326666306662326162303933343236656266623162623736'
        '3634222c2270617468223a22242f626f64793a32312f746573742f6f706572616e642f66756e63222c227261775f7370616e5f736861323536223a22'
        '343366393965313935373238386161393965383231373963653637396264353034323333623863663462613536373533653337643937376530666465'
        '31353962222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565'
        '353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a'
        '226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261'
        '30643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574663822'
        '3a5b3133312c372c3133312c32315d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c'
        '22656666656374223a226174747269627574655f6469737061746368222c2265706f6368223a226561676572222c226964223a223337393362376137'
        '3465313739653432656261666334393732326534393366393831326365373136343061616338373239373931323132396537663263613365222c226b'
        '696e64223a22417474726962757465222c226d6f64756c65223a227363697079222c22706172656e74223a2239303139616665356463316332656336'
        '383935636331666636646537633831643236623763383635326264633663336332393765636563383164376265316634222c2270617468223a22242f'
        '626f64793a32312f746573742f6f706572616e642f66756e632f76616c7565222c227261775f7370616e5f736861323536223a226566623730396264'
        '6637646461626536326334373034623766303062346339386238656262333230306638626562356262306539636662663931623239343335222c2272'
        '65736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562'
        '62336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c6522'
        '2c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339'
        '6265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133312c372c'
        '3133312c31345d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a22'
        '336230356635386534633638393034626138396439636466353539333262636332633338626665313337633765373465346266386564393161636438'
        '32626438222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226f73222c22706172656e74223a2233'
        '373933623761373465313739653432656261666334393732326534393366393831326365373136343061616338373239373931323132396537663263'
        '613365222c2270617468223a22242f626f64793a32312f746573742f6f706572616e642f66756e632f76616c75652f76616c7565222c227261775f73'
        '70616e5f736861323536223a223834306138646366656165393539363661383730623062353235373939376365393463626331396464393739343039'
        '6431363731643265393361396530646536222c227265667573616c223a226d756c7469706c655f62696e64696e6773222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133312c372c3133312c395d7d2c7b'
        '226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c2269'
        '64223a226238663162623935313365613130353536616362306363343635656165323064626164623363353533656231663339663438663139346238'
        '6335643432646130222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22336230356635386534'
        '63363839303462613839643963646635353933326263633263333862666531333763376537346534626638656439316163643832626438222c227061'
        '7468223a22242f626f64793a32312f746573742f6f706572616e642f66756e632f76616c75652f76616c75652f637478222c227261775f7370616e5f'
        '736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033'
        '62666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f7065'
        '5f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166'
        '3432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c22737061'
        '6e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c226570'
        '6f6368223a226561676572222c226964223a223366363864656364383434373232623466346666363261346262333431633435323436623536343037'
        '6366306137373566666332316433663065663337313664222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172'
        '656e74223a22333739336237613734653137396534326562616663343937323265343933663938313263653731363430616163383732393739313231'
        '32396537663263613365222c2270617468223a22242f626f64793a32312f746573742f6f706572616e642f66756e632f76616c75652f637478222c22'
        '7261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232'
        '333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061333531'
        '61222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131'
        '316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431386239'
        '3266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a747275652c2265706f6368223a226561676572222c226964223a223136316433376431643864323330326437623963303961343539623533366666'
        '6435356463613439383466643133353534616239643365343738643632383438222c226b696e64223a224c6f6164222c226d6f64756c65223a227363'
        '697079222c22706172656e74223a22393031396166653564633163326563363839356363316666366465376338316432366237633836353262646336'
        '63336332393765636563383164376265316634222c2270617468223a22242f626f64793a32312f746573742f6f706572616e642f66756e632f637478'
        '222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e'
        '616c223a747275652c2265706f6368223a226561676572222c226964223a226334376361336464666436376233613762386430396161626138323233'
        '3734393166613431326361366665653961386338303462306238663363663335333336222c226b696e64223a22436f6e7374616e74222c226d6f6475'
        '6c65223a227363697079222c22706172656e74223a223038663031373161363566633836306565653038326235393764343666636166633036353834'
        '3266663066623261623039333432366562666231626237363634222c2270617468223a22242f626f64793a32312f746573742f6f706572616e642f61'
        '7267733a30222c227261775f7370616e5f736861323536223a2262613536386333633764613566356634613834623439633365663138313834383535'
        '613765363365396239373438633236373662666263323336666338616666222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273'
        '636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732'
        '6265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c2273'
        '6861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435'
        '353561343934313862393266227d2c227370616e5f75746638223a5b3133312c32322c3133312c32375d7d2c7b226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964223a223237616434636439303534'
        '3664623232333965643539626230643838663831646439643931376562376131393132383831616466656333653666613962663335222c226b696e64'
        '223a2245787072222c226d6f64756c65223a227363697079222c22706172656e74223a22626632396461643930363736373565393430653137633633'
        '64376131373066626633613466353962616265373533663164636230663566613237623738393166222c2270617468223a22242f626f64793a32312f'
        '626f64793a30222c227261775f7370616e5f736861323536223a22646162623633313537393233396363626662393161613832306563386338626634'
        '32326161396334353533383932636535323035626165656430626262643936222c227265736f6c7574696f6e223a22756e7265736f6c766564222c22'
        '73636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337'
        '326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22'
        '736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264'
        '35353561343934313862393266227d2c227370616e5f75746638223a5b3133322c342c3133322c32385d7d2c7b226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c6261636b5f64796e616d6963222c'
        '2265706f6368223a226561676572222c226964223a226461396532353237313438666235636137643539323535313064356338343065616461663233'
        '3532333230656463636535626335343963336337643634343230222c22696d706f72745f63616e646964617465223a6e756c6c2c226b696e64223a22'
        '43616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e74223a22323761643463'
        '64393035343664623232333965643539626230643838663831646439643931376562376131393132383831616466656333653666613962663335222c'
        '2270617468223a22242f626f64793a32312f626f64793a302f76616c7565222c22706f737369626c655f64796e616d69635f656666656374223a2261'
        '74747269627574655f6469737061746368222c227261775f7370616e5f736861323536223a2264616262363331353739323339636362666239316161'
        '383230656338633862663432326161396334353533383932636535323035626165656430626262643936222c227265736f6c7574696f6e223a22756e'
        '7265736f6c766564222c2272756e74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a2231323233366565613662'
        '303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f'
        '70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165'
        '61663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c2273'
        '70616e5f75746638223a5b3133322c342c3133322c32385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e'
        '616c223a747275652c22656666656374223a226174747269627574655f6469737061746368222c2265706f6368223a226561676572222c226964223a'
        '226562366438623330393630346336313837386464386433313965663363393466626432636666323062323131393734336531313837656335663734'
        '3835666335222c226b696e64223a22417474726962757465222c226d6f64756c65223a227363697079222c22706172656e74223a2264613965323532'
        '373134386662356361376435393235353130643563383430656164616632333532333230656463636535626335343963336337643634343230222c22'
        '70617468223a22242f626f64793a32312f626f64793a302f76616c75652f66756e63222c227261775f7370616e5f736861323536223a223736316535'
        '323262623562396261313262313034353337353865646362333535343530333532623861306434656339376136396434633861633639373732343522'
        '2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363'
        '61356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f6475'
        '6c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464'
        '3663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b313332'
        '2c342c3133322c32315d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226561676572222c226964'
        '223a22393763623631616434643165393830613537646235613139636263646339336466306662396463656331396337313935646362316434306564'
        '36633663363439222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a227375626d6f64756c6573222c'
        '22706172656e74223a226562366438623330393630346336313837386464386433313965663363393466626432636666323062323131393734336531'
        '3138376563356637343835666335222c2270617468223a22242f626f64793a32312f626f64793a302f76616c75652f66756e632f76616c7565222c22'
        '7261775f7370616e5f736861323536223a22616133663633383232373930636231613163663661316664353331663336366439616162666339376162'
        '63636537383961656534633364393138346231333539222c227265667573616c223a2261737369676e6d656e745f76616c75655f756e6b6e6f776e22'
        '2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363'
        '61356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f6475'
        '6c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464'
        '3663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b313332'
        '2c342c3133322c31345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f63'
        '68223a226561676572222c226964223a2237666535656235646139356630613732336231383461396333366466356665346162313166366233313939'
        '393865663435323333356237653138343264633066222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223937636236316164346431653938306135376462356131396362636463393364663066623964636563313963373139356463623164343065'
        '6436633663363439222c2270617468223a22242f626f64793a32312f626f64793a302f76616c75652f66756e632f76616c75652f637478222c227261'
        '775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336'
        '656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335316122'
        '2c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161'
        '643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266'
        '227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a74'
        '7275652c2265706f6368223a226561676572222c226964223a2238623135623838646337353335373765636462363132336634383433386365666664'
        '353933346461393931396665366237393232343265386363666631643864222c226b696e64223a224c6f6164222c226d6f64756c65223a2273636970'
        '79222c22706172656e74223a226562366438623330393630346336313837386464386433313965663363393466626432636666323062323131393734'
        '3365313138376563356637343835666335222c2270617468223a22242f626f64793a32312f626f64793a302f76616c75652f66756e632f637478222c'
        '227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132'
        '323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430613335'
        '3161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261'
        '313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862'
        '393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c'
        '223a747275652c2265706f6368223a226561676572222c226964223a2264373837636165343532653336626635323631363136333235383433656466'
        '663837343930616132323936633938306562336634336362303462323138363764222c226b696e64223a22436f6e7374616e74222c226d6f64756c65'
        '223a227363697079222c22706172656e74223a2264613965323532373134386662356361376435393235353130643563383430656164616632333532'
        '333230656463636535626335343963336337643634343230222c2270617468223a22242f626f64793a32312f626f64793a302f76616c75652f617267'
        '733a30222c227261775f7370616e5f736861323536223a22626135363863336337646135663566346138346234396333656631383138343835356137'
        '65363365396239373438633236373662666263323336666338616666222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f'
        '7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265'
        '313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861'
        '323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535'
        '61343934313862393266227d2c227370616e5f75746638223a5b3133322c32322c3133322c32375d7d2c7b226361706162696c697479223a2270656e'
        '64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2264656c6574655f7772697465222c2265706f6368223a2265'
        '61676572222c226964223a22326430333130666334613262396666333162373363313631643730386639383964303863656331613561336333303933'
        '35373334373538633765346465353135222c226b696e64223a2244656c657465222c226d6f64756c65223a227363697079222c22706172656e74223a'
        '223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164353338623535633732626531386430'
        '6133353161222c2270617468223a22242f626f64793a3232222c227261775f7370616e5f736861323536223a22356565303936383236633862666439'
        '64333839623666643561303036313537336263396233356333353937323339393664343264353836323037306434366636222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630'
        '336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133332c302c3133332c365d7d'
        '2c7b2262696e64696e675f6b696e64223a2244656c222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a'
        '66616c73652c2265706f6368223a226561676572222c226964223a223631373135366466333535623830393035623163343766376139326137303330'
        '3864323332346362366339323464353566373266336637663837643831383137222c226b696e64223a224e616d65222c226d6f64756c65223a227363'
        '697079222c226e616d65223a226f73222c22706172656e74223a22326430333130666334613262396666333162373363313631643730386639383964'
        '30386365633161356133633330393335373334373538633765346465353135222c2270617468223a22242f626f64793a32322f746172676574733a30'
        '222c227261775f7370616e5f736861323536223a22383430613864636665616539353936366138373062306235323537393937636539346362633139'
        '64643937393430396431363731643265393361396530646536222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f706522'
        '3a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864'
        '306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536'
        '223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439'
        '34313862393266227d2c227370616e5f75746638223a5b3133332c342c3133332c365d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223062333736333363623863663837366239'
        '3237643331316631386663616162333064623463653633363062636236353461366435643337633563613331626333222c226b696e64223a2244656c'
        '222c226d6f64756c65223a227363697079222c22706172656e74223a2236313731353664663335356238303930356231633437663761393261373033'
        '303864323332346362366339323464353566373266336637663837643831383137222c2270617468223a22242f626f64793a32322f74617267657473'
        '3a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964'
        '223a22326265633436623030613965656133326565313263343138656239336461356333306363373534386136323939646264343939616362636362'
        '35386461393332222c226b696e64223a2241737369676e222c226d6f64756c65223a227363697079222c22706172656e74223a223132323336656561'
        '3662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2270'
        '617468223a22242f626f64793a3233222c227261775f7370616e5f736861323536223a22386331393461383165313061326661313265323564363861'
        '31663731613264623630653833396337363264396233626261313338666561646431373138323935222c227265736f6c7574696f6e223a22756e7265'
        '736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961'
        '643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262797465'
        '73223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166'
        '30343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133352c302c3134302c315d7d2c7b2262696e64696e'
        '675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22'
        '65706f6368223a226561676572222c226964223a22363137363434626266636463396431643539663331333662306563616561353838363234326561'
        '34306662643236623639313463323436376332343033346132222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e'
        '616d65223a225f5f616c6c5f5f222c22706172656e74223a223262656334366230306139656561333265653132633431386562393364613563333063'
        '6337353438613632393964626434393961636263636235386461393332222c2270617468223a22242f626f64793a32332f746172676574733a30222c'
        '227261775f7370616e5f736861323536223a223035316166333736313939646563323136623438303736323366616537353561326330313339313164'
        '3832313961613630373738376231376533656439636437222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262653138643061'
        '33353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a'
        '226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431'
        '3862393266227d2c227370616e5f75746638223a5b3133352c302c3133352c375d7d2c7b226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2237316362616333373361663239656438353262'
        '646230383230653162663162636234626563326530326162653135386434313761316464303362373434383064222c226b696e64223a2253746f7265'
        '222c226d6f64756c65223a227363697079222c22706172656e74223a2236313736343462626663646339643164353966333133366230656361656135'
        '383836323432656134306662643236623639313463323436376332343033346132222c2270617468223a22242f626f64793a32332f74617267657473'
        '3a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c227368'
        '61323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535'
        '3561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c22656666656374223a226f70657261746f725f70726f746f636f6c222c2265706f6368223a22656167657222'
        '2c226964223a223735356362616433626665376132326438623135633965386638636261336566366534363163383532333034346235616137363733'
        '3932393762383266393331222c226b696e64223a2242696e4f70222c226d6f64756c65223a227363697079222c22706172656e74223a223262656334'
        '366230306139656561333265653132633431386562393364613563333063633735343861363239396462643439396163626363623538646139333222'
        '2c2270617468223a22242f626f64793a32332f76616c7565222c227261775f7370616e5f736861323536223a22333034313966613530653563653630'
        '37663533663862363134313565633761313864663466653133363636623362613364353339396265356565613932653631222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630'
        '336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133352c31302c3134302c315d'
        '7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22343435393736'
        '38373864313964336434663831633932346663396663616362356331356265643832343130376162393130393432656237343264383036313738222c'
        '226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a227375626d6f64756c6573222c22706172656e74223a'
        '223735356362616433626665376132326438623135633965386638636261336566366534363163383532333034346235616137363733393239376238'
        '3266393331222c2270617468223a22242f626f64793a32332f76616c75652f6c656674222c227261775f7370616e5f736861323536223a2261613366'
        '363338323237393063623161316366366131666435333166333636643961616266633937616263636537383961656534633364393138346231333539'
        '222c227265667573616c223a2261737369676e6d656e745f76616c75655f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c'
        '766564222c2273636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533'
        '386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a'
        '343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433'
        '64616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133352c31302c3133352c32305d7d2c7b226361706162696c'
        '697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22323664'
        '323237316435393636666466623037353965613031623734376165653463333337633738356534356332356565376537323233623165303462313364'
        '39222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2234343539373638373864313964336434'
        '663831633932346663396663616362356331356265643832343130376162393130393432656237343264383036313738222c2270617468223a22242f'
        '626f64793a32332f76616c75652f6c6566742f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a'
        '22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231'
        '3263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b'
        '226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036'
        '383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22393162306634'
        '31343063326562376437303835376337313661666361653865323434333966663232656465636466656233613339393961323537316164653839222c'
        '226b696e64223a22416464222c226d6f64756c65223a227363697079222c22706172656e74223a223735356362616433626665376132326438623135'
        '6339653866386362613365663665343631633835323330343462356161373637333932393762383266393331222c2270617468223a22242f626f6479'
        '3a32332f76616c75652f6f70222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c7665'
        '64222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862'
        '35356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3436'
        '35392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461'
        '6364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2265623634336264626565613838633862'
        '373337663566316332356165306263303339313963336433623332336362616164386437363261613034386435343835222c226b696e64223a224c69'
        '7374222c226d6f64756c65223a227363697079222c22706172656e74223a223735356362616433626665376132326438623135633965386638636261'
        '3365663665343631633835323330343462356161373637333932393762383266393331222c2270617468223a22242f626f64793a32332f76616c7565'
        '2f7269676874222c227261775f7370616e5f736861323536223a22623831333463303537636566623465366362343137393233613164626366326334'
        '37386334643862306234323962343231653535626636666235333033633461222c227265736f6c7574696f6e223a22756e7265736f6c766564222c22'
        '73636f7065223a2231323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337'
        '326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22'
        '736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264'
        '35353561343934313862393266227d2c227370616e5f75746638223a5b3133352c32332c3134302c315d7d2c7b226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2234393465653631636134'
        '613032363764663832386165626564326337336636353435376661333665653035643564636364643263326138613432346332646261222c226b696e'
        '64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2265623634336264626565613838633862373337'
        '663566316332356165306263303339313963336433623332336362616164386437363261613034386435343835222c2270617468223a22242f626f64'
        '793a32332f76616c75652f72696768742f656c74733a30222c227261775f7370616e5f736861323536223a2239303934343363636563303966383732'
        '366334613336393766616364323436356664333233376662336336343539303266343935633738626238366333333330222c227265736f6c7574696f'
        '6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033'
        '6262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365'
        '223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538'
        '363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133362c342c3133362c32325d7d'
        '2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22656167657222'
        '2c226964223a223134383838363530333237316533363539373630613030623134303738666635396633646432623130333034666265343236373864'
        '3165653265613433316264222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a226562'
        '363433626462656561383863386237333766356631633235616530626330333931396333643362333233636261616438643736326161303438643534'
        '3835222c2270617468223a22242f626f64793a32332f76616c75652f72696768742f656c74733a31222c227261775f7370616e5f736861323536223a'
        '223665393461306165663231386664376165663138623235376630626139666333336339326132626339373838666337353138363865343361623339'
        '3831333766222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665'
        '65353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332'
        '6130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638'
        '223a5b3133372c342c3133372c31305d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73'
        '652c2265706f6368223a226561676572222c226964223a22326633303830663431383261613633326463656537613661636338353363303931313232'
        '39356336376132626231643161373061633262333061613764386135222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363'
        '697079222c22706172656e74223a22656236343362646265656138386338623733376635663163323561653062633033393139633364336233323363'
        '62616164386437363261613034386435343835222c2270617468223a22242f626f64793a32332f76616c75652f72696768742f656c74733a32222c22'
        '7261775f7370616e5f736861323536223a22306131623264633566636639346266326664343735633833636564383138326338626566626261343630'
        '39363162306466373362623361383234666462303134222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2231'
        '323233366565613662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133'
        '353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22'
        '613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138'
        '62393266227d2c227370616e5f75746638223a5b3133382c342c3133382c31375d7d2c7b226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2236376636326435623765653932393461643933'
        '316131383932376664383866396239353064373235623363343037653835353631313633663662316531626261222c226b696e64223a22436f6e7374'
        '616e74222c226d6f64756c65223a227363697079222c22706172656e74223a2265623634336264626565613838633862373337663566316332356165'
        '306263303339313963336433623332336362616164386437363261613034386435343835222c2270617468223a22242f626f64793a32332f76616c75'
        '652f72696768742f656c74733a33222c227261775f7370616e5f736861323536223a2238363565643037613033646230393234303566366663366138'
        '613266393739373532306530343764313430623235373538303938633932643331303862633464222c227265736f6c7574696f6e223a22756e726573'
        '6f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233613863663033626231326334396164'
        '3533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573'
        '223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630'
        '343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3133392c342c3133392c31375d7d2c7b22636170616269'
        '6c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223032'
        '656462633530656638333363303461336462653465373632363663613031326130366637363133323838643636626262316662373062316664343531'
        '6535222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22656236343362646265656138386338'
        '62373337663566316332356165306263303339313963336433623332336362616164386437363261613034386435343835222c2270617468223a2224'
        '2f626f64793a32332f76616c75652f72696768742f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22313232333665656136623033626666636665653532623363613562623361386366303362'
        '62313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b2262696e64696e675f'
        '6b696e64223a22646566696e6974696f6e222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73'
        '652c22656666656374223a22646566696e6974696f6e5f6372656174696f6e222c2265706f6368223a226561676572222c226964223a226362316236'
        '353563383963346564616534396337646137623565613734393937386465643530316237376632626461633465613535383665393338663963343122'
        '2c226b696e64223a2246756e6374696f6e446566222c226d6f64756c65223a227363697079222c226e616d65223a225f5f6469725f5f222c22706172'
        '656e74223a22313232333665656136623033626666636665653532623363613562623361386366303362623132633439616435333862353563373262'
        '65313864306133353161222c2270617468223a22242f626f64793a3234222c227261775f7370616e5f736861323536223a2265383532366661643437'
        '616234393138363930646464373837396631326365656134316435383138636361316138366334323034636434326164643038383630222c22726573'
        '6f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561366230336266666366656535326233636135626233'
        '6138636630336262313263343961643533386235356337326265313864306133353161222c2273636f70655f6b696e64223a226d6f64756c65222c22'
        '736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265'
        '366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134332c302c3134'
        '342c31385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22'
        '6561676572222c226964223a226639326231653136323632353136386236336565356638343334326434363331616236353937366332663539656337'
        '3162663332346336356335623237323730222c226b696e64223a22617267756d656e7473222c226d6f64756c65223a227363697079222c2270617265'
        '6e74223a2263623162363535633839633465646165343963376461376235656137343939373864656435303162373766326264616334656135353836'
        '653933386639633431222c2270617468223a22242f626f64793a32342f61726773222c227261775f7370616e5f736861323536223a6e756c6c2c2272'
        '65736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22636231623635356338396334656461653439633764613762356561'
        '37343939373864656435303162373766326264616334656135353836653933386639633431222c2273636f70655f6b696e64223a2266756e6374696f'
        '6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436'
        '63396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d'
        '2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22646566657272'
        '6564222c226964223a223965393661373734343035306336303334653335386664333839346166613763363765663465313938356136376631653035'
        '3436666139356632373033663465222c226b696e64223a2252657475726e222c226d6f64756c65223a227363697079222c22706172656e74223a2263'
        '623162363535633839633465646165343963376461376235656137343939373864656435303162373766326264616334656135353836653933386639'
        '633431222c2270617468223a22242f626f64793a32342f626f64793a30222c227261775f7370616e5f736861323536223a2236663234383264323561'
        '353763316538353438303163666261393964346563656533333339333639613039373865306334366234353339613432663130313835222c22726573'
        '6f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226362316236353563383963346564616534396337646137623565613734'
        '3939373864656435303162373766326264616334656135353836653933386639633431222c2273636f70655f6b696e64223a2266756e6374696f6e22'
        '2c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339'
        '6265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134342c342c'
        '3134342c31385d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226465666572726564222c2269'
        '64223a226239306162623734323435343061316662366166306130393138663032373639333835653866313061356531383263303462306531613464'
        '3164616235613861222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a225f5f616c6c5f5f222c2270'
        '6172656e74223a2239653936613737343430353063363033346533353866643338393461666137633637656634653139383561363766316530353436'
        '666139356632373033663465222c2270617468223a22242f626f64793a32342f626f64793a302f76616c7565222c227261775f7370616e5f73686132'
        '3536223a2230353161663337363139396465633231366234383037363233666165373535613263303133393131643832313961613630373738376231'
        '376533656439636437222c227265667573616c223a2264656665727265645f65787465726e616c5f62696e64696e67222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22636231623635356338396334656461653439633764613762356561373439393738646564'
        '35303162373766326264616334656135353836653933386639633431222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134342c31312c3134342c3138'
        '5d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2264656665'
        '72726564222c226964223a22356661316635343434623330386439643631393063636632323066663631363261306130373737393863303134666332'
        '30376434313364633333393863393436222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2262'
        '393061626237343234353430613166623661663061303931386630323736393338356538663130613565313832633034623065316134643164616235'
        '613861222c2270617468223a22242f626f64793a32342f626f64793a302f76616c75652f637478222c227261775f7370616e5f736861323536223a6e'
        '756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22636231623635356338396334656461653439633764'
        '61376235656137343939373864656435303162373766326264616334656135353836653933386639633431222c2273636f70655f6b696e64223a2266'
        '756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261'
        '30643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574663822'
        '3a6e756c6c7d2c7b2262696e64696e675f6b696e64223a22646566696e6974696f6e222c226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c22656666656374223a22646566696e6974696f6e5f6372656174696f6e222c2265706f6368223a2265'
        '61676572222c226964223a22383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934'
        '35303330616330613164366337666631222c226b696e64223a2246756e6374696f6e446566222c226d6f64756c65223a227363697079222c226e616d'
        '65223a225f5f676574617474725f5f222c22706172656e74223a22313232333665656136623033626666636665653532623363613562623361386366'
        '30336262313263343961643533386235356337326265313864306133353161222c2270617468223a22242f626f64793a3235222c227261775f737061'
        '6e5f736861323536223a2239383936386462616638636439316138363730383264636639323239373965633735366236616161396139333739353839'
        '306233363631633434326134313962222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223132323336656561'
        '3662303362666663666565353262336361356262336138636630336262313263343961643533386235356337326265313864306133353161222c2273'
        '636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861'
        '316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c'
        '227370616e5f75746638223a5b3134372c302c3135362c31335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e64697469'
        '6f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223238376162353666636465343566656664663639643636383131'
        '3432623565343062343232643062373332323239336262326435653538363962653036353661222c226b696e64223a22617267756d656e7473222c22'
        '6d6f64756c65223a227363697079222c22706172656e74223a2238323164613338363261643463356135363864356139383530363339373364303133'
        '343661666361656633396265393435303330616330613164366337666631222c2270617468223a22242f626f64793a32352f61726773222c22726177'
        '5f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231646133'
        '38363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c'
        '2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131'
        '616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138623932'
        '66227d2c227370616e5f75746638223a6e756c6c7d2c7b2262696e64696e675f6b696e64223a22706172616d65746572222c226361706162696c6974'
        '79223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223236346562'
        '653931333764393334613134333336613832353037336333373863333663326236323062616462643765333433383539343133653530303565623622'
        '2c226b696e64223a22617267222c226d6f64756c65223a227363697079222c226e616d65223a226e616d65222c22706172656e74223a223238376162'
        '353666636465343566656664663639643636383131343262356534306234323264306237333232323933626232643565353836396265303635366122'
        '2c2270617468223a22242f626f64793a32352f617267732f617267733a30222c227261775f7370616e5f736861323536223a22383261333533376666'
        '30646263653765656333356436396564633361313839656536663137643832663335336135353366396161393663623062653363653839222c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339'
        '373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e'
        '222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663'
        '396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134372c31'
        '362c3134372c32305d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265666665'
        '6374223a2274727574685f70726f746f636f6c222c2265706f6368223a226465666572726564222c226964223a223133623465333139386164353239'
        '6166373862616337343639393066373561343466626662303661386239323964313638383436613934643336353238373539222c226b696e64223a22'
        '4966222c226d6f64756c65223a227363697079222c22706172656e74223a223832316461333836326164346335613536386435613938353036333937'
        '3364303133343661666361656633396265393435303330616330613164366337666631222c2270617468223a22242f626f64793a32352f626f64793a'
        '30222c227261775f7370616e5f736861323536223a223535353039656566623838303861613033373638326538373839646433663430623332663035'
        '3565343636623439613431666530643763633534613239383263222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131'
        '64366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861'
        '323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535'
        '61343934313862393266227d2c227370616e5f75746638223a5b3134382c342c3135362c31335d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22636f6d70617269736f6e5f70726f746f636f6c222c2265706f63'
        '68223a226465666572726564222c226964223a2231353436376535633964636263373432653634643135383037353036666362393739656562306338'
        '663162373538376438393065613562353331663565363934222c226b696e64223a22436f6d70617265222c226d6f64756c65223a227363697079222c'
        '22706172656e74223a223133623465333139386164353239616637386261633734363939306637356134346662666230366138623932396431363838'
        '3436613934643336353238373539222c2270617468223a22242f626f64793a32352f626f64793a302f74657374222c227261775f7370616e5f736861'
        '323536223a22333462353339326362386130356163383935613833633639623364356439613035666565656232393362366439336163383933383134'
        '36623566643033666465222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463'
        '356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f'
        '6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561'
        '663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370'
        '616e5f75746638223a5b3134382c372c3134382c32355d7d2c7b2262696e64696e675f63616e64696461746573223a5b223236346562653931333764'
        '3933346131343333366138323530373363333738633336633262363230626164626437653334333835393431336535303035656236225d2c2262696e'
        '64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c'
        '2265706f6368223a226465666572726564222c226964223a223830386165646164663962333837373633386237326562636139653336373238643131'
        '6266343338626565356332653633353830323334393466633732343930222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079'
        '222c226e616d65223a226e616d65222c22706172656e74223a2231353436376535633964636263373432653634643135383037353036666362393739'
        '656562306338663162373538376438393065613562353331663565363934222c2270617468223a22242f626f64793a32352f626f64793a302f746573'
        '742f6c656674222c227261775f7370616e5f736861323536223a22383261333533376666306462636537656563333564363965646333613138396565'
        '36663137643832663335336135353366396161393663623062653363653839222c227265736f6c7574696f6e223a226c65786963616c5f63616e6469'
        '64617465222c2273636f7065223a22383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962'
        '65393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b2262797465'
        '73223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166'
        '30343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134382c372c3134382c31315d7d2c7b226361706162'
        '696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a'
        '223838303061623164373037333432636266613235303233383830333365346133663965303165333730633438366434346161303538633334353434'
        '6462326566222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22383038616564616466396233'
        '38373736333862373265626361396533363732386431316266343338626565356332653633353830323334393466633732343930222c227061746822'
        '3a22242f626f64793a32352f626f64793a302f746573742f6c6566742f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339'
        '373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e'
        '222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663'
        '396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c'
        '7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564'
        '222c226964223a2236666530373563333736626336303136313533623133643263336539383861303661323832393633356533626430613664393733'
        '383765643261353762626365222c226b696e64223a22496e222c226d6f64756c65223a227363697079222c22706172656e74223a2231353436376535'
        '633964636263373432653634643135383037353036666362393739656562306338663162373538376438393065613562353331663565363934222c22'
        '70617468223a22242f626f64793a32352f626f64793a302f746573742f6f70733a30222c227261775f7370616e5f736861323536223a6e756c6c2c22'
        '7265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461333836326164346335613536386435613938353036'
        '3339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e637469'
        '6f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464'
        '3663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c'
        '7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a2237363836'
        '663630343761396465306364636430353566376161396665323865313263393463393464346532383639363365613565616336303562313361633539'
        '222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a227375626d6f64756c6573222c22706172656e74'
        '223a22313534363765356339646362633734326536346431353830373530366663623937396565623063386631623735383764383930656135623533'
        '31663565363934222c2270617468223a22242f626f64793a32352f626f64793a302f746573742f636f6d70617261746f72733a30222c227261775f73'
        '70616e5f736861323536223a226161336636333832323739306362316131636636613166643533316633363664396161626663393761626363653738'
        '3961656534633364393138346231333539222c227265667573616c223a2264656665727265645f65787465726e616c5f62696e64696e67222c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339'
        '373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e'
        '222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663'
        '396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134382c31'
        '352c3134382c32355d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368'
        '223a226465666572726564222c226964223a226339623263396631363736333534366261313166623632343466616165353035663737656534393133'
        '6432343839373430376663356663396232333237613731222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172'
        '656e74223a22373638366636303437613964653063646364303535663761613966653238653132633934633934643465323836393633656135656163'
        '36303562313361633539222c2270617468223a22242f626f64793a32352f626f64793a302f746573742f636f6d70617261746f72733a302f63747822'
        '2c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238'
        '323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337'
        '666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c2273686132353622'
        '3a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934'
        '313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f'
        '6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a2264393736393832323737373530353236303736323630313632'
        '373864323035653530663539366332356562306533303566303432363835616162396637663538222c226b696e64223a2252657475726e222c226d6f'
        '64756c65223a227363697079222c22706172656e74223a22313362346533313938616435323961663738626163373436393930663735613434666266'
        '62303661386239323964313638383436613934643336353238373539222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a'
        '30222c227261775f7370616e5f736861323536223a223264386463383636313463353866636230616239316136333332626133663666303438353635'
        '3232306130356630326261363935643261346136653433343235222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131'
        '64366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861'
        '323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535'
        '61343934313862393266227d2c227370616e5f75746638223a5b3134392c382c3134392c35365d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c6261636b5f64796e616d6963222c226570'
        '6f6368223a226465666572726564222c226964223a226136376666626636343435383632336430343564326533356165303866333832636662346534'
        '3534633864343061623034373731646236613737393236373262222c22696d706f72745f63616e646964617465223a6e756c6c2c226b696e64223a22'
        '43616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e74223a22643937363938'
        '32323737373530353236303736323630313632373864323035653530663539366332356562306533303566303432363835616162396637663538222c'
        '2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c7565222c22706f737369626c655f64796e616d69635f656666'
        '656374223a226174747269627574655f6469737061746368222c227261775f7370616e5f736861323536223a22636639646364326132306161313938'
        '63353435366565636233353363306234656239633237363239633531303230376565666266343664653930386339633534222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2272756e74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a22383231'
        '646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131643663376666'
        '31222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22'
        '613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138'
        '62393266227d2c227370616e5f75746638223a5b3134392c31352c3134392c35365d7d2c7b226361706162696c697479223a2270656e64696e67222c'
        '22636f6e646974696f6e616c223a747275652c22656666656374223a226174747269627574655f6469737061746368222c2265706f6368223a226465'
        '666572726564222c226964223a2264633265323539626634643434333431306164333063306438646538613331336634353266623562366235333465'
        '373237653162646166623939633137643331222c226b696e64223a22417474726962757465222c226d6f64756c65223a227363697079222c22706172'
        '656e74223a22613637666662663634343538363233643034356432653335616530386633383263666234653435346338643430616230343737316462'
        '36613737393236373262222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c75652f66756e63222c22726177'
        '5f7370616e5f736861323536223a22356535636531353964386466336131393733643461356565306131643531336534336666356235363037386266'
        '66316338363833393862333133633736623766222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164'
        '613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631'
        '222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261'
        '313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862'
        '393266227d2c227370616e5f75746638223a5b3134392c31352c3134392c33395d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c'
        '2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a74'
        '7275652c2265706f6368223a226465666572726564222c226964223a2237306238613266646464383962323561323531336165373261646361653537'
        '653930353135646132636331323065643434316365353631333261316365376639222c226b696e64223a224e616d65222c226d6f64756c65223a2273'
        '63697079222c226e616d65223a225f696d706f72746c6962222c22706172656e74223a22646332653235396266346434343334313061643330633064'
        '38646538613331336634353266623562366235333465373237653162646166623939633137643331222c2270617468223a22242f626f64793a32352f'
        '626f64793a302f626f64793a302f76616c75652f66756e632f76616c7565222c227261775f7370616e5f736861323536223a22393833643832623562'
        '30396430343066356566623566663736336235393764663133363632333831333562613263663061323634663635616163353363656264222c227265'
        '667573616c223a2264656665727265645f65787465726e616c5f62696e64696e67222c227265736f6c7574696f6e223a22756e7265736f6c76656422'
        '2c2273636f7065223a223832316461333836326164346335613536386435613938353036333937336430313334366166636165663339626539343530'
        '3330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a3436'
        '35392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461'
        '6364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134392c31352c3134392c32355d7d2c7b226361706162696c6974'
        '79223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a22613066'
        '633331353631616237316330373937323461346330663530646666633763383235613037333434386465353239323265306662613034346164383766'
        '38222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2237306238613266646464383962323561'
        '323531336165373261646361653537653930353135646132636331323065643434316365353631333261316365376639222c2270617468223a22242f'
        '626f64793a32352f626f64793a302f626f64793a302f76616c75652f66756e632f76616c75652f637478222c227261775f7370616e5f736861323536'
        '223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231646133383632616434633561353638'
        '64356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e6422'
        '3a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f636822'
        '3a226465666572726564222c226964223a22303636656435633061343165653530323961363766663063316436356635353934366464633439393130'
        '38306631303535666336616530653464343638393165222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c2270617265'
        '6e74223a2264633265323539626634643434333431306164333063306438646538613331336634353266623562366235333465373237653162646166'
        '623939633137643331222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c75652f66756e632f637478222c22'
        '7261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231'
        '646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131643663376666'
        '31222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22'
        '613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138'
        '62393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e61'
        '6c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226465666572726564222c226964223a22'
        '666539653662636235363664646131303334323738343539643338323161373265386566636131303735636531303063396631623130383230383137'
        '61306466222c226b696e64223a224a6f696e6564537472222c226d6f64756c65223a227363697079222c22706172656e74223a226136376666626636'
        '3434353836323364303435643265333561653038663338326366623465343534633864343061623034373731646236613737393236373262222c2270'
        '617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c75652f617267733a30222c227261775f7370616e5f736861323536'
        '223a22356261316435623531626536326665336234386439396538396631303937383763656264643930323938376161323131393835313034376436'
        '33353431333262222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135'
        '363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e'
        '64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432'
        '336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f'
        '75746638223a5b3134392c34302c3134392c35355d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a747275652c2265706f6368223a226465666572726564222c226964223a226231356230633735353436353132663538396162323932366636396533'
        '3064333631353764333666363932623337366637306164643165633337353032613163222c226b696e64223a22436f6e7374616e74222c226d6f6475'
        '6c65223a227363697079222c22706172656e74223a226665396536626362353636646461313033343237383435396433383231613732653865666361'
        '3130373563653130306339663162313038323038313761306466222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f'
        '76616c75652f617267733a302f76616c7565733a30222c227261775f7370616e5f736861323536223a22626264643862346233333836333837333466'
        '32313264663965616661333563343938306231306136376139636566383238363432626436666338313539666262222c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339373364303133343661'
        '666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365'
        '223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538'
        '363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134392c34322c3134392c34385d'
        '7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22666f726d61'
        '745f70726f746f636f6c222c2265706f6368223a226465666572726564222c226964223a223331376237346132323063646661616537326538613764'
        '3365336535386163633138653731343765333430313936636436613730303239656333393837373236222c226b696e64223a22466f726d6174746564'
        '56616c7565222c226d6f64756c65223a227363697079222c22706172656e74223a226665396536626362353636646461313033343237383435396433'
        '3832316137326538656663613130373563653130306339663162313038323038313761306466222c2270617468223a22242f626f64793a32352f626f'
        '64793a302f626f64793a302f76616c75652f617267733a302f76616c7565733a31222c227261775f7370616e5f736861323536223a22356532393164'
        '37626362326464383437353837626132373430646464383237313764313938613964636137623031366665323661623834616366353864383536222c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530'
        '363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374'
        '696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364'
        '643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134'
        '392c34382c3134392c35345d7d2c7b2262696e64696e675f63616e64696461746573223a5b2232363465626539313337643933346131343333366138'
        '323530373363333738633336633262363230626164626437653334333835393431336535303035656236225d2c2262696e64696e675f6b696e64223a'
        '224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465'
        '666572726564222c226964223a2263376433346233316466336165656265346133626562316437393539333733356137663433346463373839383062'
        '656632326533343531653135623964303532222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226e'
        '616d65222c22706172656e74223a22333137623734613232306364666161653732653861376433653365353861636331386537313437653334303139'
        '36636436613730303239656333393837373236222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c75652f61'
        '7267733a302f76616c7565733a312f76616c7565222c227261775f7370616e5f736861323536223a2238326133353337666630646263653765656333'
        '356436396564633361313839656536663137643832663335336135353366396161393663623062653363653839222c227265736f6c7574696f6e223a'
        '226c65786963616c5f63616e646964617465222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339373364'
        '303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22'
        '736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265'
        '366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3134392c34392c31'
        '34392c35335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a22'
        '6465666572726564222c226964223a226134323436396335386561376336646665626466363436653963313565643930653366373464393039623134'
        '6330653961663663373561616232616130363331222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74'
        '223a22633764333462333164663361656562653461336265623164373935393337333561376634333464633738393830626566323265333435316531'
        '35623964303532222c2270617468223a22242f626f64793a32352f626f64793a302f626f64793a302f76616c75652f617267733a302f76616c756573'
        '3a312f76616c75652f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c7665'
        '64222c2273636f7065223a22383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934'
        '35303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a'
        '343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433'
        '64616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e6469'
        '6e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22657863657074696f6e5f70726f746f636f6c222c2265706f636822'
        '3a226465666572726564222c226964223a22376637336162376466383036383639303662373766623038623363313364353931313938636633353332'
        '33643462363332656230316663333035316431323361222c226b696e64223a22547279222c226d6f64756c65223a227363697079222c22706172656e'
        '74223a223133623465333139386164353239616637386261633734363939306637356134346662666230366138623932396431363838343661393464'
        '3336353238373539222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a30222c227261775f7370616e5f7368613235'
        '36223a226535643635313730363163316631386538373036326634363736316362656430633463353465336434643134313736626264653463313938'
        '3130653335373131222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231646133383632616434633561'
        '35363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b69'
        '6e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634'
        '32336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e'
        '5f75746638223a5b3135312c382c3135362c31335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a747275652c2265706f6368223a226465666572726564222c226964223a223862316365613535633738336330656264363063373964373831613164'
        '6266653863366263363062323361366363313333333337396430306530613931316133222c226b696e64223a2252657475726e222c226d6f64756c65'
        '223a227363697079222c22706172656e74223a2237663733616237646638303638363930366237376662303862336331336435393131393863663335'
        '333233643462363332656230316663333035316431323361222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f'
        '626f64793a30222c227261775f7370616e5f736861323536223a22323938323030363039623837373363613432343238356538373931336635383665'
        '66313131336535633532396565333333316335366335366634633739396162222c227265736f6c7574696f6e223a22756e7265736f6c766564222c22'
        '73636f7065223a2238323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330'
        '616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a34363539'
        '2c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364'
        '326435353561343934313862393266227d2c227370616e5f75746638223a5b3135322c31322c3135322c33345d7d2c7b226361706162696c69747922'
        '3a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a227375627363726970745f70726f746f636f6c222c'
        '2265706f6368223a226465666572726564222c226964223a223932303333623866663463386538363264303335343337383033363039343734326566'
        '6134633865346137666433393936653634353035383530306436393666222c226b696e64223a22537562736372697074222c226d6f64756c65223a22'
        '7363697079222c22706172656e74223a2238623163656135356337383363306562643630633739643738316131646266653863366263363062323361'
        '366363313333333337396430306530613931316133222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64'
        '793a302f76616c7565222c227261775f7370616e5f736861323536223a22636365306331646639663538623330303534393166336130346135393135'
        '63306666353661633536343431363534303237366361343835353732386433323336222c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435'
        '303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a34'
        '3635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364'
        '616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135322c31392c3135322c33345d7d2c7b226361706162696c69'
        '7479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2263616c6c5f63616c6c6261636b5f64796e'
        '616d6963222c2265706f6368223a226465666572726564222c226964223a226365356563653262393438373139393031366135336663393361646430'
        '6133393265356464363162303465663134373538376566653236666439383631613462222c22696d706f72745f63616e646964617465223a6e756c6c'
        '2c226b696e64223a2243616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65223a227363697079222c22706172656e74'
        '223a22393230333362386666346338653836326430333534333738303336303934373432656661346338653461376664333939366536343530353835'
        '30306436393666222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64793a302f76616c75652f76616c75'
        '65222c22706f737369626c655f64796e616d69635f656666656374223a22756e7265736f6c7665645f63616c6c61626c65222c227261775f7370616e'
        '5f736861323536223a223030633430626562373330333465346166366565303037346630653361366539363733353531306330313839363936386439'
        '3265633635346538666339633638222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2272756e74696d655f62696e64696e675f70'
        '726f76656e223a66616c73652c2273636f7065223a223832316461333836326164346335613536386435613938353036333937336430313334366166'
        '6361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f7572636522'
        '3a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836'
        '3036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135322c31392c3135322c32385d7d'
        '2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c69747922'
        '3a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a223463656137'
        '356337313465336133376336646636613534306261393539353035616366386135653064623265336631393433323534336463356266323830363022'
        '2c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a22676c6f62616c73222c22706172656e74223a2263'
        '653565636532623934383731393930313661353366633933616464306133393265356464363162303465663134373538376566653236666439383631'
        '613462222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64793a302f76616c75652f76616c75652f6675'
        '6e63222c227261775f7370616e5f736861323536223a2232373466326539613462343066623834366362613134623365643136636639656564343832'
        '326231323461646432633930376330353736393834386232366261222c227265667573616c223a22756e626f756e645f6f725f6275696c74696e5f75'
        '6e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461333836326164346335613536'
        '3864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64'
        '223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233'
        '6433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75'
        '746638223a5b3135322c31392c3135322c32365d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a'
        '747275652c2265706f6368223a226465666572726564222c226964223a22333964303836376138393863363362333836356630326136306532353866'
        '31656634326265353338653238306266623534306334333630613830356630323165222c226b696e64223a224c6f6164222c226d6f64756c65223a22'
        '7363697079222c22706172656e74223a2234636561373563373134653361333763366466366135343062613935393530356163663861356530646232'
        '653366313934333235343364633562663238303630222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64'
        '793a302f76616c75652f76616c75652f66756e632f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22383231646133383632616434633561353638643561393835303633393733643031333436'
        '61666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f757263'
        '65223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433646436633962653663376265'
        '38363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c6c7d2c7b2262696e64696e'
        '675f63616e64696461746573223a5b223236346562653931333764393334613134333336613832353037336333373863333663326236323062616462'
        '6437653334333835393431336535303035656236225d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a223933383839333431'
        '3032306434303936366435336265643935383135633034616135616565336466653131616363373535396538356239326638383265646263222c226b'
        '696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226e616d65222c22706172656e74223a2239323033336238'
        '666634633865383632643033353433373830333630393437343265666134633865346137666433393936653634353035383530306436393666222c22'
        '70617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64793a302f76616c75652f736c696365222c227261775f7370'
        '616e5f736861323536223a22383261333533376666306462636537656563333564363965646333613138396565366631376438326633353361353533'
        '66396161393663623062653363653839222c227265736f6c7574696f6e223a226c65786963616c5f63616e646964617465222c2273636f7065223a22'
        '383231646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131643663'
        '37666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536'
        '223a22613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439'
        '34313862393266227d2c227370616e5f75746638223a5b3135322c32392c3135322c33335d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a2266653938303134643139363666'
        '373130376663633236303637336266346265333239653962663130363732386231353238393334393634326435666235623233222c226b696e64223a'
        '224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a223933383839333431303230643430393636643533626564393538'
        '3135633034616135616565336466653131616363373535396538356239326638383265646263222c2270617468223a22242f626f64793a32352f626f'
        '64793a302f6f72656c73653a302f626f64793a302f76616c75652f736c6963652f637478222c227261775f7370616e5f736861323536223a6e756c6c'
        '2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231646133383632616434633561353638643561393835'
        '30363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e63'
        '74696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364333261306433'
        '64643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e75'
        '6c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a2264656665'
        '72726564222c226964223a22393131393363306536383931613766306630393738653636613135363935383330306538613163646632303937313833'
        '32343738336661346364396431653166222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2239'
        '323033336238666634633865383632643033353433373830333630393437343265666134633865346137666433393936653634353035383530306436'
        '393666222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f626f64793a302f76616c75652f637478222c227261'
        '775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461'
        '333836326164346335613536386435613938353036333937336430313334366166636165663339626539343530333061633061316436633766663122'
        '2c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131'
        '316164386131656166343233643332613064336464366339626536633762653836303638333231663034336461636432643535356134393431386239'
        '3266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a747275652c22656666656374223a22657863657074696f6e5f6d61746368696e67222c2265706f6368223a226465666572726564222c226964223a'
        '223762383964646633373466313737336361656238613430353364633639363664323730306334343164656638343635323061323131616263623432'
        '3435613332222c226b696e64223a2245786365707448616e646c6572222c226d6f64756c65223a227363697079222c22706172656e74223a22376637'
        '336162376466383036383639303662373766623038623363313364353931313938636633353332336434623633326562303166633330353164313233'
        '61222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a30222c227261775f7370616e5f73'
        '6861323536223a2234623262356530636635343463663261376633336364383131613331306336323664323363393731656132373930363736306236'
        '326636663764396137333961222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461333836326164'
        '3463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70'
        '655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131'
        '6561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c22'
        '7370616e5f75746638223a5b3135332c382c3135362c31335d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e67'
        '5f6b696e64223a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f'
        '6368223a226465666572726564222c226964223a22333732653865656638623439343266346365666638333535623036373431323733333634343837'
        '36326365376430643133346561326162313933383536653234222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e'
        '616d65223a224b65794572726f72222c22706172656e74223a2237623839646466333734663137373363616562386134303533646336393636643237'
        '303063343431646566383436353230613231316162636234323435613332222c2270617468223a22242f626f64793a32352f626f64793a302f6f7265'
        '6c73653a302f68616e646c6572733a302f74797065222c227261775f7370616e5f736861323536223a22663066306564663836376134323133666165'
        '37663934303530343938633634336133343566646232303465363539313963633063333531313665353931366535222c227265667573616c223a2275'
        '6e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f706522'
        '3a2238323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164'
        '366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c2273686132'
        '3536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561'
        '343934313862393266227d2c227370616e5f75746638223a5b3135332c31352c3135332c32335d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a226466316430383337306130'
        '6539646361303965323465346531313132333263323561623731633934393331666233323966646266656463636631353630616565222c226b696e64'
        '223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a22333732653865656638623439343266346365666638333535'
        '62303637343132373333363434383736326365376430643133346561326162313933383536653234222c2270617468223a22242f626f64793a32352f'
        '626f64793a302f6f72656c73653a302f68616e646c6572733a302f747970652f637478222c227261775f7370616e5f736861323536223a6e756c6c2c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530'
        '363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374'
        '696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364'
        '643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a6e756c'
        '6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a2265786365'
        '7074696f6e5f70726f746f636f6c222c2265706f6368223a226465666572726564222c226964223a2236636534386433323230353131613365396536'
        '396234663061653461613234666130323030373837656162396535626336383262376562643438626566643463222c226b696e64223a225261697365'
        '222c226d6f64756c65223a227363697079222c22706172656e74223a2237623839646466333734663137373363616562386134303533646336393636'
        '643237303063343431646566383436353230613231316162636234323435613332222c2270617468223a22242f626f64793a32352f626f64793a302f'
        '6f72656c73653a302f68616e646c6572733a302f626f64793a30222c227261775f7370616e5f736861323536223a2231373630313430646463306434'
        '626136313666366162656362653136666664393831396538363338616533353936333166396636333233623239663736623231222c227265736f6c75'
        '74696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461333836326164346335613536386435613938353036333937336430'
        '3133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c2273'
        '6f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536'
        '6337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135342c31322c3135'
        '362c31335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c22656666656374223a22'
        '63616c6c5f63616c6c6261636b5f64796e616d6963222c2265706f6368223a226465666572726564222c226964223a22396438633736313764306362'
        '66633764343131386230303532353239643661373336326635363534313564396366383664636538346333633165656637666538222c22696d706f72'
        '745f63616e646964617465223a6e756c6c2c226b696e64223a2243616c6c222c226c65786963616c5f74617267657473223a5b5d2c226d6f64756c65'
        '223a227363697079222c22706172656e74223a2236636534386433323230353131613365396536396234663061653461613234666130323030373837'
        '656162396535626336383262376562643438626566643463222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f'
        '68616e646c6572733a302f626f64793a302f657863222c22706f737369626c655f64796e616d69635f656666656374223a22756e7265736f6c766564'
        '5f63616c6c61626c65222c227261775f7370616e5f736861323536223a22633661316463313861636336666666313330343961636539666632663037'
        '33336163393166646538303538353435323162393465613734643437623066376566222c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2272756e74696d655f62696e64696e675f70726f76656e223a66616c73652c2273636f7065223a22383231646133383632616434633561353638'
        '64356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e6422'
        '3a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a5b3135342c31382c3135362c31335d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e6422'
        '3a224c6f6164222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a2264'
        '65666572726564222c226964223a22396537323530366464656231623335313636306432393562376231626232353035316363313234383837623666'
        '33376637616439326633373239316531383437222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a22'
        '4174747269627574654572726f72222c22706172656e74223a2239643863373631376430636266633764343131386230303532353239643661373336'
        '326635363534313564396366383664636538346333633165656637666538222c2270617468223a22242f626f64793a32352f626f64793a302f6f7265'
        '6c73653a302f68616e646c6572733a302f626f64793a302f6578632f66756e63222c227261775f7370616e5f736861323536223a2264303630353334'
        '333461363232653730393138373830326566303764656634623532653035383339663337613866356639303536643563303530666136336131222c22'
        '7265667573616c223a22756e626f756e645f6f725f6275696c74696e5f756e6b6e6f776e222c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a223832316461333836326164346335613536386435613938353036333937336430313334366166636165663339626539'
        '3435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b22627974657322'
        '3a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536633762653836303638333231663034'
        '3364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135342c31382c3135342c33325d7d2c7b22636170616269'
        '6c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a22'
        '303736373534656664386137336539626331393939643861356663336133363663333361613335383533636364383835393239366334633839373864'
        '30666433222c226b696e64223a224c6f6164222c226d6f64756c65223a227363697079222c22706172656e74223a2239653732353036646465623162'
        '333531363630643239356237623162623235303531636331323438383762366633376637616439326633373239316531383437222c2270617468223a'
        '22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a302f626f64793a302f6578632f66756e632f637478222c22'
        '7261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231'
        '646133383632616434633561353638643561393835303633393733643031333436616663616566333962653934353033306163306131643663376666'
        '31222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22'
        '613131616438613165616634323364333261306433646436633962653663376265383630363833323166303433646163643264353535613439343138'
        '62393266227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e61'
        '6c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226465666572726564222c226964223a22'
        '633737666430666338646531323861613737616533353030373039343836373865353465353230356534626666653933373230636437343431323133'
        '65323431222c226b696e64223a224a6f696e6564537472222c226d6f64756c65223a227363697079222c22706172656e74223a223964386337363137'
        '6430636266633764343131386230303532353239643661373336326635363534313564396366383664636538346333633165656637666538222c2270'
        '617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a302f626f64793a302f6578632f617267733a30'
        '222c227261775f7370616e5f736861323536223a22653061613464316464343761623463356634653233383737366633656165373935633838303363'
        '36353638383934393833373037366161653030303432376664222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f706522'
        '3a2238323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164'
        '366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c2273686132'
        '3536223a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561'
        '343934313862393266227d2c227370616e5f75746638223a5b3135352c31362c3135352c35395d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564222c226964223a226638336361363634663235'
        '6435643865386530646537636230323163633738303235323934333936623362363439343336656463643035633339343637353861222c226b696e64'
        '223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22706172656e74223a226337376664306663386465313238616137376165'
        '3335303037303934383637386535346535323035653462666665393337323063643734343132313365323431222c2270617468223a22242f626f6479'
        '3a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a302f626f64793a302f6578632f617267733a302f76616c7565733a30222c22'
        '7261775f7370616e5f736861323536223a22346437666336663162303230666161343532316662393231623962643339336563356134303338363461'
        '63323237663366396664666537646565363637613866222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238'
        '323164613338363261643463356135363864356139383530363339373364303133343661666361656633396265393435303330616330613164366337'
        '666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c2273686132353622'
        '3a2261313161643861316561663432336433326130643364643663396265366337626538363036383332316630343364616364326435353561343934'
        '313862393266227d2c227370616e5f75746638223a5b3135352c31382c3135352c35315d7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a747275652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a22646566'
        '6572726564222c226964223a226139353864333734366434646535303232363238313839643566633432373332613939623661313063326631666539'
        '3738616636356434366231343035333033222c226b696e64223a22466f726d617474656456616c7565222c226d6f64756c65223a227363697079222c'
        '22706172656e74223a226337376664306663386465313238616137376165333530303730393438363738653534653532303565346266666539333732'
        '3063643734343132313365323431222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a30'
        '2f626f64793a302f6578632f617267733a302f76616c7565733a31222c227261775f7370616e5f736861323536223a22356532393164376263623264'
        '64383437353837626132373430646464383237313764313938613964636137623031366665323661623834616366353864383536222c227265736f6c'
        '7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2238323164613338363261643463356135363864356139383530363339373364'
        '303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c22'
        '736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433326130643364643663396265'
        '366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135352c35312c31'
        '35352c35375d7d2c7b2262696e64696e675f63616e64696461746573223a5b2232363465626539313337643933346131343333366138323530373363'
        '333738633336633262363230626164626437653334333835393431336535303035656236225d2c2262696e64696e675f6b696e64223a224c6f616422'
        '2c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f6368223a226465666572726564'
        '222c226964223a2266626363643331613636353633333461326638356532656533363437326136303462633563333636356232343136393633646534'
        '366266646438666538363238222c226b696e64223a224e616d65222c226d6f64756c65223a227363697079222c226e616d65223a226e616d65222c22'
        '706172656e74223a22613935386433373436643464653530323236323831383964356663343237333261393962366131306332663166653937386166'
        '36356434366231343035333033222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a302f'
        '626f64793a302f6578632f617267733a302f76616c7565733a312f76616c7565222c227261775f7370616e5f736861323536223a2238326133353337'
        '666630646263653765656333356436396564633361313839656536663137643832663335336135353366396161393663623062653363653839222c22'
        '7265736f6c7574696f6e223a226c65786963616c5f63616e646964617465222c2273636f7065223a2238323164613338363261643463356135363864'
        '356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a'
        '2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a2261313161643861316561663432336433'
        '326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f757466'
        '38223a5b3135352c35322c3135352c35365d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a7472'
        '75652c2265706f6368223a226465666572726564222c226964223a226432383338653962613666643031623163643235323734333731316439396465'
        '3061653431373961633239626133323331316264663563306338636335613931222c226b696e64223a224c6f6164222c226d6f64756c65223a227363'
        '697079222c22706172656e74223a22666263636433316136363536333334613266383565326565333634373261363034626335633336363562323431'
        '36393633646534366266646438666538363238222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c'
        '6572733a302f626f64793a302f6578632f617267733a302f76616c7565733a312f76616c75652f637478222c227261775f7370616e5f736861323536'
        '223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22383231646133383632616434633561353638'
        '64356139383530363339373364303133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e6422'
        '3a2266756e6374696f6e222c22736f75726365223a7b226279746573223a343635392c22736861323536223a22613131616438613165616634323364'
        '33326130643364643663396265366337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f7574'
        '6638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a747275652c2265706f636822'
        '3a226465666572726564222c226964223a22303362666233646236353237316363376332633334363138363338306162306465646263363663623938'
        '64616133333630633830323566383730383464373733222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227363697079222c22'
        '706172656e74223a22633737666430666338646531323861613737616533353030373039343836373865353465353230356534626666653933373230'
        '63643734343132313365323431222c2270617468223a22242f626f64793a32352f626f64793a302f6f72656c73653a302f68616e646c6572733a302f'
        '626f64793a302f6578632f617267733a302f76616c7565733a32222c227261775f7370616e5f736861323536223a2232363566646131376133343631'
        '316231353333643861323831666636383064633537393162306365306131316332356233356531316338653735363835353039222c227265736f6c75'
        '74696f6e223a22756e7265736f6c766564222c2273636f7065223a223832316461333836326164346335613536386435613938353036333937336430'
        '3133343661666361656633396265393435303330616330613164366337666631222c2273636f70655f6b696e64223a2266756e6374696f6e222c2273'
        '6f75726365223a7b226279746573223a343635392c22736861323536223a226131316164386131656166343233643332613064336464366339626536'
        '6337626538363036383332316630343364616364326435353561343934313862393266227d2c227370616e5f75746638223a5b3135352c35372c3135'
        '352c35385d7d2c7b226361706162696c697479223a2270656e64696e67222c226b696e64223a226f726967696e222c226d6f64756c65223a22706163'
        '6b6167696e67222c226f726967696e223a7b226b696e64223a227061636b616765222c226d6f64756c65223a227061636b6167696e67222c22706174'
        '68223a22443a2f41656e762f70726f332f2e76656e762f4c69622f736974652d7061636b616765732f7061636b6167696e672f5f5f696e69745f5f2e'
        '7079222c22706879736963616c5f64657363726970746f72223a7b226279746573223a3439342c2266696c655f74797065223a22726567756c617222'
        '2c226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a223234653030363030303030303031'
        '303030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e'
        '61746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f7365726961'
        '6c223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f2e76656e762f4c69622f736974652d70'
        '61636b616765732f7061636b6167696e672f5f5f696e69745f5f2e7079222c22726570617273655f706f696e74223a66616c73652c22736368656d61'
        '223a2263686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a22366537353863646430303238623263616437'
        '34633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c2270696e223a7b22627974'
        '6573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233'
        '30363238306238373862666535396433393231396235227d7d2c227068617365223a224c32222c22766961223a6e756c6c7d2c7b226361706162696c'
        '697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22623337'
        '366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662633535316663323935'
        '36222c226b696e64223a224d6f64756c65222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a6e756c6c2c227061746822'
        '3a2224222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662633535'
        '31666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536'
        '223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738626665353964'
        '33393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e64697469'
        '6f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964223a2230'
        '323733333361303065376530313535643239333662376261343166316465643333316135616464626265613136373136366234323036333631343332'
        '626330222c226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a226233373661653139'
        '6466633966646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2270'
        '617468223a22242f626f64793a30222c227261775f7370616e5f736861323536223a2261343333623661346632356333663138366266373936663963'
        '636635363030353365653137396634303833626262303134383539383332656266396234373734222c227265736f6c7574696f6e223a22756e726573'
        '6f6c766564222c2273636f7065223a226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135'
        '6538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573'
        '223a3439342c22736861323536223a223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036'
        '3238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b352c302c352c32335d7d2c7b2262696e64696e675f6b696e'
        '64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368'
        '223a226561676572222c226964223a226661326532633333626636316236653432376535626632313631373839636263313135316661336162313933'
        '3431336134613963363631356130643764386237222c226b696e64223a224e616d65222c226d6f64756c65223a227061636b6167696e67222c226e61'
        '6d65223a225f5f7469746c655f5f222c22706172656e74223a2230323733333361303065376530313535643239333662376261343166316465643333'
        '316135616464626265613136373136366234323036333631343332626330222c2270617468223a22242f626f64793a302f746172676574733a30222c'
        '227261775f7370616e5f736861323536223a223562623330303066326430333232613138383166313334663238636233343034313165353037323036'
        '6431636365363336646536323837323362333166313638222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662633535316663'
        '32393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a22'
        '366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738626665353964333932'
        '31396235227d2c227370616e5f75746638223a5b352c302c352c395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e6469'
        '74696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22376362373837613837613765653833363230666665643262'
        '33343332306337313538663734313733386339623634363638636565323537333530333231636463222c226b696e64223a2253746f7265222c226d6f'
        '64756c65223a227061636b6167696e67222c22706172656e74223a226661326532633333626636316236653432376535626632313631373839636263'
        '3131353166613361623139333431336134613963363631356130643764386237222c2270617468223a22242f626f64793a302f746172676574733a30'
        '2f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f70'
        '65223a226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135653835366335663636626335'
        '3531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c227368613235'
        '36223a223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036323830623837386266653539'
        '6433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974'
        '696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2265323063663436653062663837623038356364613432616262'
        '663664363363616236656436376164353061316437643563316332623138396230623462653863222c226b696e64223a22436f6e7374616e74222c22'
        '6d6f64756c65223a227061636b6167696e67222c22706172656e74223a22303237333333613030653765303135356432393336623762613431663164'
        '65643333316135616464626265613136373136366234323036333631343332626330222c2270617468223a22242f626f64793a302f76616c7565222c'
        '227261775f7370616e5f736861323536223a223730396238303839363331663332643261653934336239393765326630633462386238643166353532'
        '3437393865346166303634346636663037663733653037222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662633535316663'
        '32393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a22'
        '366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738626665353964333932'
        '31396235227d2c227370616e5f75746638223a5b352c31322c352c32335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964'
        '223a22343938303064303437613738663933303163313435376263303261323666656163623866316332353831343137386566336634373632656662'
        '36653433383261222c226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2262333736'
        '616531396466633966646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536'
        '222c2270617468223a22242f626f64793a31222c227261775f7370616e5f736861323536223a22313565373933353232333962643863333865663661'
        '35663866646639303531636266626462383938353265636462373537363830363563396334636165646633222c227265736f6c7574696f6e223a2275'
        '6e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433'
        '306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262'
        '79746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035343933'
        '323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b362c302c362c35305d7d2c7b2262696e64696e67'
        '5f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265'
        '706f6368223a226561676572222c226964223a2232363130313838376330626535386562333836633837653363323266663331333731613531323639'
        '643565336635363530616438626261393739383838393633222c226b696e64223a224e616d65222c226d6f64756c65223a227061636b6167696e6722'
        '2c226e616d65223a225f5f73756d6d6172795f5f222c22706172656e74223a2234393830306430343761373866393330316331343537626330326132'
        '366665616362386631633235383134313738656633663437363265666236653433383261222c2270617468223a22242f626f64793a312f7461726765'
        '74733a30222c227261775f7370616e5f736861323536223a226664323031623838396163326338646639663134366163653364353530393266306637'
        '3837663366333637663634303533616233363434613631653861636363222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662'
        '63353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861'
        '323536223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738626665'
        '35396433393231396235227d2c227370616e5f75746638223a5b362c302c362c31315d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223330343037336165386131653334336333'
        '3439343830396230366237336238323430336335646439626563353735613563626131636363363637303766346132222c226b696e64223a2253746f'
        '7265222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2232363130313838376330626535386562333836633837653363'
        '323266663331333731613531323639643565336635363530616438626261393739383838393633222c2270617468223a22242f626f64793a312f7461'
        '72676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433306361356538353663'
        '356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343934'
        '2c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035343933323330363238306238'
        '373862666535396433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c'
        '22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22663131646430636166303062336537616436'
        '38386630323639353234616331643038656461653932313062343163663761326534623266383161303131316232222c226b696e64223a22436f6e73'
        '74616e74222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a223439383030643034376137386639333031633134353762'
        '6330326132366665616362386631633235383134313738656633663437363265666236653433383261222c2270617468223a22242f626f64793a312f'
        '76616c7565222c227261775f7370616e5f736861323536223a2261646536363436336632333831373632313437386162646230633936353763376264'
        '386138636363373731333839363532646263303362346135373131623737222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273'
        '636f7065223a226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135653835366335663636'
        '6263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c227368'
        '61323536223a223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036323830623837386266'
        '6535396433393231396235227d2c227370616e5f75746638223a5b362c31342c362c35305d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a22656167'
        '6572222c226964223a223663383831366236393434643834646137383934616633383963633262616634613864656535346439666464626134643962'
        '3839303031303564656335396139222c226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67222c22706172656e74'
        '223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566363662633535'
        '31666332393536222c2270617468223a22242f626f64793a32222c227261775f7370616e5f736861323536223a223064333963333333336166343936'
        '6336626264646632373536326238326330366230376133633966383238663135383561353631393865616433353365643062222c227265736f6c7574'
        '696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134396663633762373430'
        '30663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572'
        '6365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962396164633963396630'
        '36663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b372c302c372c34355d7d2c7b22'
        '62696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66'
        '616c73652c2265706f6368223a226561676572222c226964223a22623563346234356164333334343530643762393230353761356636323666653664'
        '39613766653434313938373462366332616166316466336334643537306139222c226b696e64223a224e616d65222c226d6f64756c65223a22706163'
        '6b6167696e67222c226e616d65223a225f5f7572695f5f222c22706172656e74223a2236633838313662363934346438346461373839346166333839'
        '636332626166346138646565353464396664646261346439623839303031303564656335396139222c2270617468223a22242f626f64793a322f7461'
        '72676574733a30222c227261775f7370616e5f736861323536223a223432383262386139373766633965323633363338313861626662616266343262'
        '6232393630393466303164336132346663653936623162643661346666623835222c227265736f6c7574696f6e223a22756e7265736f6c766564222c'
        '2273636f7065223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566'
        '36366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22'
        '736861323536223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738'
        '62666535396433393231396235227d2c227370616e5f75746638223a5b372c302c372c375d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22376433313761353934303063326661'
        '61363063353661396133336461623236313664616264636465376139363939363866323033613365373863383634373066222c226b696e64223a2253'
        '746f7265222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a226235633462343561643333343435306437623932303537'
        '6135663632366665366439613766653434313938373462366332616166316466336334643537306139222c2270617468223a22242f626f64793a322f'
        '746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135653835'
        '3663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a34'
        '39342c22736861323536223a223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036323830'
        '6238373862666535396433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2265633230333662646437666632363764'
        '373437613035633732643165326637343861316463343037393236363230633037646237386166633662383162303666222c226b696e64223a22436f'
        '6e7374616e74222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a22366338383136623639343464383464613738393461'
        '66333839636332626166346138646565353464396664646261346439623839303031303564656335396139222c2270617468223a22242f626f64793a'
        '322f76616c7565222c227261775f7370616e5f736861323536223a223764646433633164326466646430366330653331316235666135613738653539'
        '6437656135356130666261323037326331333334613735656364346630316638222c227265736f6c7574696f6e223a22756e7265736f6c766564222c'
        '2273636f7065223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536633566'
        '36366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22'
        '736861323536223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632383062383738'
        '62666535396433393231396235227d2c227370616e5f75746638223a5b372c31302c372c34355d7d2c7b226361706162696c697479223a2270656e64'
        '696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a2265'
        '61676572222c226964223a22633831353232613731653133646665363465616638663164356564373062666261613865626236663062333633653334'
        '37623166353734633333623333356264222c226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67222c2270617265'
        '6e74223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433306361356538353663356636366263'
        '353531666332393536222c2270617468223a22242f626f64793a33222c227261775f7370616e5f736861323536223a22666334616161346466366439'
        '32663861323565373938333034623239333931383339633566653465396165623733353931303439633831356533663562323636222c227265736f6c'
        '7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237'
        '343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f'
        '75726365223a7b226279746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339'
        '663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b392c302c392c32305d7d2c'
        '7b2262696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a66616c73652c2265706f6368223a226561676572222c226964223a2237623634643636316339636637623138363730353639333136386639343461'
        '313038396330636538666562343364333735376230346437623831616566373130222c226b696e64223a224e616d65222c226d6f64756c65223a2270'
        '61636b6167696e67222c226e616d65223a225f5f76657273696f6e5f5f222c22706172656e74223a2263383135323261373165313364666536346561'
        '663866316435656437306266626161386562623666306233363365333437623166353734633333623333356264222c2270617468223a22242f626f64'
        '793a332f746172676574733a30222c227261775f7370616e5f736861323536223a223361326530393235336133626234336635393764656439653962'
        '3239333437383730303335383366303461303432316134646436636633663363376662313866222c227265736f6c7574696f6e223a22756e7265736f'
        '6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565'
        '38353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22627974657322'
        '3a3439342c22736861323536223a22366537353863646430303238623263616437346337333962396164633963396630366630353439333233303632'
        '38306238373862666535396433393231396235227d2c227370616e5f75746638223a5b392c302c392c31315d7d2c7b226361706162696c697479223a'
        '2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223134316130383339'
        '6537626334326264303938373662663330663233303239656335386335373936656464363336313162353634393831646436376361653737222c226b'
        '696e64223a2253746f7265222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2237623634643636316339636637623138'
        '363730353639333136386639343461313038396330636538666562343364333735376230346437623831616566373130222c2270617468223a22242f'
        '626f64793a332f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a2275'
        '6e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433'
        '306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262'
        '79746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035343933'
        '323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a22'
        '70656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22303666646136363764'
        '32633761353236613530396235663630636662623634373463633934623136346462353630653939383434626464653263373263353135222c226b69'
        '6e64223a22436f6e7374616e74222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a226338313532326137316531336466'
        '6536346561663866316435656437306266626161386562623666306233363365333437623166353734633333623333356264222c2270617468223a22'
        '242f626f64793a332f76616c7565222c227261775f7370616e5f736861323536223a2266393961343537333339333730383762623164383739373437'
        '346136616439613361373737353132353361646464363339333539393763303237373165326564222c227265736f6c7574696f6e223a22756e726573'
        '6f6c766564222c2273636f7065223a226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135'
        '6538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573'
        '223a3439342c22736861323536223a223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036'
        '3238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b392c31342c392c32305d7d2c7b226361706162696c697479'
        '223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e675f7772697465222c226570'
        '6f6368223a226561676572222c226964223a226130633235653665303966666434323231306439303038366532303964366531303838616662626164'
        '6634623264613336353530376264653238666136363164222c226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67'
        '222c22706172656e74223a22623337366165313964666339666461623131623762653134396663633762373430306637313734333063613565383536'
        '63356636366263353531666332393536222c2270617468223a22242f626f64793a34222c227261775f7370616e5f736861323536223a223563616433'
        '376561346164336637643531313463653536376664366230343837663435663330396135326231373434326539386362613937366538383064363422'
        '2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134'
        '39666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f6475'
        '6c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962'
        '39616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31312c30'
        '2c31312c35365d7d2c7b2262696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e'
        '646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2239316137303332363464326666326566376662326564'
        '343461643138653837323734663232326631616366343463356130666135633532303866313736616662222c226b696e64223a224e616d65222c226d'
        '6f64756c65223a227061636b6167696e67222c226e616d65223a225f5f617574686f725f5f222c22706172656e74223a226130633235653665303966'
        '6664343232313064393030383665323039643665313038386166626261646634623264613336353530376264653238666136363164222c2270617468'
        '223a22242f626f64793a342f746172676574733a30222c227261775f7370616e5f736861323536223a22346332643934663135336163356631626462'
        '34663366616165323031616234653530336333306536323865623234336533353735666435373066663362613634222c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731'
        '373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a'
        '7b226279746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035'
        '343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31312c302c31312c31305d7d2c7b226361'
        '706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22696422'
        '3a2236363566616631386433346534653666306661633133303031656536386338356631663331326337346333613663333236383061653566323936'
        '623830373830222c226b696e64223a2253746f7265222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a22393161373033'
        '32363464326666326566376662326564343461643138653837323734663232326631616366343463356130666135633532303866313736616662222c'
        '2270617468223a22242f626f64793a342f746172676574733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f'
        '6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134396663633762'
        '37343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c2273'
        '6f75726365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962396164633963'
        '39663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a'
        '223234303637303261386430386235336230353334636465646564623235663339663339336561343562333639323563326236336233363563313433'
        '6334653532222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2261306332'
        '356536653039666664343232313064393030383665323039643665313038386166626261646634623264613336353530376264653238666136363164'
        '222c2270617468223a22242f626f64793a342f76616c7565222c227261775f7370616e5f736861323536223a22393435383465353430373934323031'
        '36396266396536383038393737383262303430396662326233393465333733643361626231326239313463613833613635222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030'
        '663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036'
        '663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31312c31332c31312c35365d7d2c'
        '7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a2262696e64696e'
        '675f7772697465222c2265706f6368223a226561676572222c226964223a223263303465303266393063643535363230393036316531613134313834'
        '3864353263636361306534306130633130393533666134613539353536616136613833222c226b696e64223a2241737369676e222c226d6f64756c65'
        '223a227061636b6167696e67222c22706172656e74223a22623337366165313964666339666461623131623762653134396663633762373430306637'
        '31373433306361356538353663356636366263353531666332393536222c2270617468223a22242f626f64793a35222c227261775f7370616e5f7368'
        '61323536223a226132383163326566663235663465316133326234373266323565303161636165623566336533333931623936363566303666623366'
        '3838313663633034616233222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339'
        '66646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f7065'
        '5f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238'
        '62326361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e'
        '5f75746638223a5b31322c302c31322c33305d7d2c7b2262696e64696e675f6b696e64223a2253746f7265222c226361706162696c697479223a2270'
        '656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2232626639636666616434'
        '393337346632386436616430343539363662623431333139626566396666313661306637393232613737333561653531613030336465222c226b696e'
        '64223a224e616d65222c226d6f64756c65223a227061636b6167696e67222c226e616d65223a225f5f656d61696c5f5f222c22706172656e74223a22'
        '326330346530326639306364353536323039303631653161313431383438643532636363613065343061306331303935336661346135393535366161'
        '36613833222c2270617468223a22242f626f64793a352f746172676574733a30222c227261775f7370616e5f736861323536223a2263616236613039'
        '383932366334623136313165363035366662613832356231366265316663333633313666646230373830663033653232346336376462386262222c22'
        '7265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233373661653139646663396664616231316237626531343966'
        '6363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65'
        '222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665373538636464303032386232636164373463373339623961'
        '6463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31322c302c31'
        '322c395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2265'
        '61676572222c226964223a22336263393636393632326230313132633362613038343165353033326231373366316331633234393831376265306665'
        '31666332376663383838623930386236222c226b696e64223a2253746f7265222c226d6f64756c65223a227061636b6167696e67222c22706172656e'
        '74223a223262663963666661643439333734663238643661643034353936366262343133313962656639666631366130663739323261373733356165'
        '3531613030336465222c2270617468223a22242f626f64793a352f746172676574733a302f637478222c227261775f7370616e5f736861323536223a'
        '6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233373661653139646663396664616231316237'
        '6265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a22'
        '6d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665373538636464303032386232636164373463'
        '3733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a6e'
        '756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561'
        '676572222c226964223a2231656236623562623238353433623337343733346130336265346433323464326662386637323265663630356532373137'
        '316537326234653038373362643864222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227061636b6167696e67222c22706172'
        '656e74223a22326330346530326639306364353536323039303631653161313431383438643532636363613065343061306331303935336661346135'
        '39353536616136613833222c2270617468223a22242f626f64793a352f76616c7565222c227261775f7370616e5f736861323536223a223333323135'
        '393064643563313033643563393731396135366162363165373330353761336561306639636363356136613235303535656366303734333438636322'
        '2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134'
        '39666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f6475'
        '6c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962'
        '39616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31322c31'
        '322c31322c33305d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c226566666563'
        '74223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964223a2233353965313739643932363634303930323331'
        '353135303163396331653439356339663638343863316163383234316636373039616339626133663061343435222c226b696e64223a224173736967'
        '6e222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a226233373661653139646663396664616231316237626531343966'
        '6363376237343030663731373433306361356538353663356636366263353531666332393536222c2270617468223a22242f626f64793a36222c2272'
        '61775f7370616e5f736861323536223a2266313930343238383832376561306461643061316161623535666339363430353735353864653539636265'
        '353330316138633538323132356531646637356665222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233'
        '373661653139646663396664616231316237626531343966636337623734303066373137343330636135653835366335663636626335353166633239'
        '3536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665'
        '373538636464303032386232636164373463373339623961646339633966303666303534393332333036323830623837386266653539643339323139'
        '6235227d2c227370616e5f75746638223a5b31342c302c31342c34325d7d2c7b2262696e64696e675f6b696e64223a2253746f7265222c2263617061'
        '62696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22'
        '623863643931386333333861666439393461313231626639313437613132666533653335663364626562336262366363343561333733373465613235'
        '32333438222c226b696e64223a224e616d65222c226d6f64756c65223a227061636b6167696e67222c226e616d65223a225f5f6c6963656e73655f5f'
        '222c22706172656e74223a22333539653137396439323636343039303233313531353031633963316534393563396636383438633161633832343166'
        '36373039616339626133663061343435222c2270617468223a22242f626f64793a362f746172676574733a30222c227261775f7370616e5f73686132'
        '3536223a2231306364656664343562666462633135656639363733623935366262303433323835396533316662386361343466373761623961306331'
        '313639653639373932222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233373661653139646663396664'
        '6162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665373538636464303032386232'
        '6361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75'
        '746638223a5b31342c302c31342c31315d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c'
        '73652c2265706f6368223a226561676572222c226964223a226464623932653766383837326436656463666339656538333663343432623439623364'
        '3265613465313032376434356335386334623863313139396230386164222c226b696e64223a2253746f7265222c226d6f64756c65223a227061636b'
        '6167696e67222c22706172656e74223a2262386364393138633333386166643939346131323162663931343761313266653365333566336462656233'
        '626236636334356133373337346561323532333438222c2270617468223a22242f626f64793a362f746172676574733a302f637478222c227261775f'
        '7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531'
        '396466633966646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c22'
        '73636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a2236653735386364'
        '643030323862326361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c'
        '227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73'
        '652c2265706f6368223a226561676572222c226964223a22343663313734346165396437666335623063626562656237386461613162353638353363'
        '65366634393766383537633463326639353031393533353332633364222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227061'
        '636b6167696e67222c22706172656e74223a223335396531373964393236363430393032333135313530316339633165343935633966363834386331'
        '6163383234316636373039616339626133663061343435222c2270617468223a22242f626f64793a362f76616c7565222c227261775f7370616e5f73'
        '6861323536223a2232636464393439383237656363633364343561303966313333393531383732336563326438356465633632313861353463613035'
        '386138663931306232656432222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233373661653139646663'
        '3966646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70'
        '655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665373538636464303032'
        '3862326361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c22737061'
        '6e5f75746638223a5b31342c31342c31342c34325d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c22'
        '3a66616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964223a22393430346665'
        '64646531346331393866316535323965303439353830356166376135626536616662653733656562336161633237343736323537383265333738222c'
        '226b696e64223a2241737369676e222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2262333736616531396466633966'
        '646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2270617468223a'
        '22242f626f64793a37222c227261775f7370616e5f736861323536223a22633335613164656630613130643434626138343438363965653861643835'
        '65336363613033333061643238616239353438636466343039376132373335393033222c227265736f6c7574696f6e223a22756e7265736f6c766564'
        '222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433306361356538353663'
        '356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a343934'
        '2c22736861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035343933323330363238306238'
        '373862666535396433393231396235227d2c227370616e5f75746638223a5b31352c302c31352c33365d7d2c7b2262696e64696e675f6b696e64223a'
        '2253746f7265222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22'
        '6561676572222c226964223a223330623662313530653066393137386338396638383766396431623938373633613164666331323338303663393238'
        '6333363539363065643730356564343362222c226b696e64223a224e616d65222c226d6f64756c65223a227061636b6167696e67222c226e616d6522'
        '3a225f5f636f707972696768745f5f222c22706172656e74223a22393430346665646465313463313938663165353239653034393538303561663761'
        '35626536616662653733656562336161633237343736323537383265333738222c2270617468223a22242f626f64793a372f746172676574733a3022'
        '2c227261775f7370616e5f736861323536223a2230306335386531626638393634643838353062363839613036323631643765333730303764643735'
        '376336373561373666643031326533613938323635363532222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a'
        '226233373661653139646663396664616231316237626531343966636337623734303066373137343330636135653835366335663636626335353166'
        '6332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a'
        '223665373538636464303032386232636164373463373339623961646339633966303666303534393332333036323830623837386266653539643339'
        '3231396235227d2c227370616e5f75746638223a5b31352c302c31352c31335d7d2c7b226361706162696c697479223a2270656e64696e67222c2263'
        '6f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a226461616238323963363066323231373130633936'
        '6361666461356463323461353362343863653133393332383937343830663139346266373961636137613238222c226b696e64223a2253746f726522'
        '2c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a2233306236623135306530663931373863383966383837663964316239'
        '383736336131646663313233383036633932386333363539363065643730356564343362222c2270617468223a22242f626f64793a372f7461726765'
        '74733a302f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c22'
        '73636f7065223a2262333736616531396466633966646162313162376265313439666363376237343030663731373433306361356538353663356636'
        '366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c2273'
        '6861323536223a2236653735386364643030323862326361643734633733396239616463396339663036663035343933323330363238306238373862'
        '666535396433393231396235227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f'
        '6e646974696f6e616c223a66616c73652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226561676572222c'
        '226964223a22613532646666616331383939333939633538633930393163386437373565356662323463333761616534366638323633376365323238'
        '62386237396135663063222c226b696e64223a224a6f696e6564537472222c226d6f64756c65223a227061636b6167696e67222c22706172656e7422'
        '3a2239343034666564646531346331393866316535323965303439353830356166376135626536616662653733656562336161633237343736323537'
        '383265333738222c2270617468223a22242f626f64793a372f76616c7565222c227261775f7370616e5f736861323536223a22366637343530383639'
        '39393463386230383634613766386538623965366234323533343961343530646136666365616639383031643730663633346236633439222c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363'
        '376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c'
        '22736f75726365223a7b226279746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463'
        '396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31352c31362c3135'
        '2c33365d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2265'
        '61676572222c226964223a22633963626663313561663437323161376164323039313035636334313931326366623165316230363136663533383738'
        '38383936636232643535653332316565222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a227061636b6167696e67222c227061'
        '72656e74223a226135326466666163313839393339396335386339303931633864373735653566623234633337616165343666383236333763653232'
        '3862386237396135663063222c2270617468223a22242f626f64793a372f76616c75652f76616c7565733a30222c227261775f7370616e5f73686132'
        '3536223a2261333333316232376334633261353962353064303738623066363662393363356163646439613838613762386339663335323336623938'
        '396564623566326432222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226233373661653139646663396664'
        '6162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a223665373538636464303032386232'
        '6361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75'
        '746638223a5b31352c31382c31352c32335d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a6661'
        '6c73652c22656666656374223a22666f726d61745f70726f746f636f6c222c2265706f6368223a226561676572222c226964223a2266643032623261'
        '353831616165643162616532336632663432663237633732396239353961346561613932353334336432653634333862643838626531303234222c22'
        '6b696e64223a22466f726d617474656456616c7565222c226d6f64756c65223a227061636b6167696e67222c22706172656e74223a22613532646666'
        '61633138393933393963353863393039316338643737356535666232346333376161653436663832363337636532323862386237396135663063222c'
        '2270617468223a22242f626f64793a372f76616c75652f76616c7565733a31222c227261775f7370616e5f736861323536223a223965326538666636'
        '3963356361336438363534376138656335393730633463636563383031666437623431623031333861386639363065363139386135643262222c2272'
        '65736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22623337366165313964666339666461623131623762653134396663'
        '63376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c6522'
        '2c22736f75726365223a7b226279746573223a3439342c22736861323536223a22366537353863646430303238623263616437346337333962396164'
        '63396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31352c32332c31'
        '352c33355d7d2c7b2262696e64696e675f63616e64696461746573223a5b5d2c2262696e64696e675f6b696e64223a224c6f6164222c226361706162'
        '696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2261'
        '666431613766643533313766326666633463326630373535663634313335643931626563663633383535333739616233333732383864613565646534'
        '356364222c226b696e64223a224e616d65222c226d6f64756c65223a227061636b6167696e67222c226e616d65223a225f5f617574686f725f5f222c'
        '22706172656e74223a226664303262326135383161616564316261653233663266343266323763373239623935396134656161393235333433643265'
        '3634333862643838626531303234222c2270617468223a22242f626f64793a372f76616c75652f76616c7565733a312f76616c7565222c227261775f'
        '7370616e5f736861323536223a2234633264393466313533616335663162646234663366616165323031616234653530336333306536323865623234'
        '336533353735666435373066663362613634222c227265667573616c223a2261737369676e6d656e745f76616c75655f756e6b6e6f776e222c227265'
        '736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466633966646162313162376265313439666363'
        '376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f70655f6b696e64223a226d6f64756c65222c'
        '22736f75726365223a7b226279746573223a3439342c22736861323536223a2236653735386364643030323862326361643734633733396239616463'
        '396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370616e5f75746638223a5b31352c32342c3135'
        '2c33345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2265'
        '61676572222c226964223a22653264343236663231386232376264346136396532393338333364313963346665396331613963333635666138373334'
        '62656564303135643566393661363432222c226b696e64223a224c6f6164222c226d6f64756c65223a227061636b6167696e67222c22706172656e74'
        '223a22616664316137666435333137663266666334633266303735356636343133356439316265636636333835353337396162333337323838646135'
        '65646534356364222c2270617468223a22242f626f64793a372f76616c75652f76616c7565733a312f76616c75652f637478222c227261775f737061'
        '6e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2262333736616531396466'
        '633966646162313162376265313439666363376237343030663731373433306361356538353663356636366263353531666332393536222c2273636f'
        '70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3439342c22736861323536223a2236653735386364643030'
        '323862326361643734633733396239616463396339663036663035343933323330363238306238373862666535396433393231396235227d2c227370'
        '616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c226b696e64223a226f726967696e222c226d6f6475'
        '6c65223a22706c75676779222c226f726967696e223a7b226b696e64223a227061636b616765222c226d6f64756c65223a22706c75676779222c2270'
        '617468223a22443a2f41656e762f70726f332f2e76656e762f4c69622f736974652d7061636b616765732f706c756767792f5f5f696e69745f5f2e70'
        '79222c22706879736963616c5f64657363726970746f72223a7b226279746573223a3831312c2266696c655f74797065223a22726567756c6172222c'
        '226c696e6b5f636f756e74223a312c226e61746976655f6964656e74697479223a7b2266696c655f6964223a22623564663036303030303030303130'
        '3030303030303030303030303030303030222c2266696c6573797374656d223a224e544653222c22736368656d61223a2263686f35315f6c765f6e61'
        '746976655f6964656e746974795f7631222c22766f6c756d655f6b696e64223a226c6f63616c5f6669786564222c22766f6c756d655f73657269616c'
        '223a2237613763333566363763333561653266227d2c2270617468223a22443a2f41656e762f70726f332f2e76656e762f4c69622f736974652d7061'
        '636b616765732f706c756767792f5f5f696e69745f5f2e7079222c22726570617273655f706f696e74223a66616c73652c22736368656d61223a2263'
        '686f35315f6c765f66696c655f64657363726970746f725f7631222c22736861323536223a2230666137363964363039383430653362343361376338'
        '343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c2270696e223a7b226279746573223a'
        '3831312c22736861323536223a2230666137363964363039383430653362343361376338343063313037336561616238316162613539636265323239'
        '366461656139306230646466613066366438227d7d2c227068617365223a224c32222c22766961223a6e756c6c7d2c7b226361706162696c69747922'
        '3a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2266373039396231'
        '303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c22'
        '6b696e64223a224d6f64756c65222c226d6f64756c65223a22706c75676779222c22706172656e74223a6e756c6c2c2270617468223a2224222c2272'
        '61775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039'
        '396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464'
        '222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137'
        '363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438'
        '227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66'
        '616c73652c22656666656374223a2262696e64696e675f7772697465222c2265706f6368223a226561676572222c226964223a223765373836326639'
        '6130653831336232623437343232303434353034383561623131323730373565623062363236303966363138663861623164613862653132222c226b'
        '696e64223a2241737369676e222c226d6f64756c65223a22706c75676779222c22706172656e74223a22663730393962313034346635363730346134'
        '36643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2270617468223a22242f626f'
        '64793a30222c227261775f7370616e5f736861323536223a223938613938646334353938643135303634346365626334373539653362626131373239'
        '6565636334313332303935383566376631343736363432666263666338222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766306333333431'
        '35383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861'
        '323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362653232393664616561393062'
        '30646466613066366438227d2c227370616e5f75746638223a5b312c302c31362c315d7d2c7b2262696e64696e675f6b696e64223a2253746f726522'
        '2c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c'
        '226964223a22623666643965316566653866343535336331323539666230626134336561343966326661353231393361626634633538666434393366'
        '34323539356330386366222c226b696e64223a224e616d65222c226d6f64756c65223a22706c75676779222c226e616d65223a225f5f616c6c5f5f22'
        '2c22706172656e74223a2237653738363266396130653831336232623437343232303434353034383561623131323730373565623062363236303966'
        '363138663861623164613862653132222c2270617468223a22242f626f64793a302f746172676574733a30222c227261775f7370616e5f7368613235'
        '36223a223035316166333736313939646563323136623438303736323366616537353561326330313339313164383231396161363037373837623137'
        '6533656439636437222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730'
        '34613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b69'
        '6e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533'
        '62343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f7574'
        '6638223a5b312c302c312c375d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22'
        '65706f6368223a226561676572222c226964223a22373037326139393961623832666239646338663037313838333431326436313039366334303037'
        '30656634663062356663383634633663396661663665663737222c226b696e64223a2253746f7265222c226d6f64756c65223a22706c75676779222c'
        '22706172656e74223a226236666439653165666538663435353363313235396662306261343365613439663266613532313933616266346335386664'
        '3439336634323539356330386366222c2270617468223a22242f626f64793a302f746172676574733a302f637478222c227261775f7370616e5f7368'
        '61323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226637303939623130343466353637'
        '3034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b'
        '696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a223066613736396436303938343065'
        '3362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75'
        '746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f63'
        '68223a226561676572222c226964223a2234306661636332366536363362363563643064653163346137306665373165613330656239303166313635'
        '356662386662373230396234316437363234653732222c226b696e64223a224c697374222c226d6f64756c65223a22706c75676779222c2270617265'
        '6e74223a2237653738363266396130653831336232623437343232303434353034383561623131323730373565623062363236303966363138663861'
        '623164613862653132222c2270617468223a22242f626f64793a302f76616c7565222c227261775f7370616e5f736861323536223a22313135666339'
        '63646333636539346564303839366132663532363738646563663138633662353238323862303838383362316364666266363230313533623263222c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166'
        '393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c'
        '65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338343063'
        '313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b312c31302c'
        '31362c315d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a22'
        '6561676572222c226964223a223161636563343163633263363731313132623239343966336666303433396263363131336163393438303361306332'
        '6162376665323236393162313563326532222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c2270617265'
        '6e74223a2234306661636332366536363362363563643064653163346137306665373165613330656239303166313635356662386662373230396234'
        '316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a30222c227261775f7370616e5f736861323536223a'
        '223237333835396662636633366364616162376234383561613330393735326661323836623830363036636661613766323764366531636534656264'
        '3533663364222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134'
        '36643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433'
        '61376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f7574663822'
        '3a5b322c342c322c31375d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c226570'
        '6f6368223a226561676572222c226964223a226331313863376636303237613533623032646230326237306263643433383539343533656462616266'
        '6637313834346564616332313639643165646338666362222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c7567677922'
        '2c22706172656e74223a2234306661636332366536363362363563643064653163346137306665373165613330656239303166313635356662386662'
        '373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a31222c227261775f7370616e5f7368'
        '61323536223a223432623632393530393132323563306530633334643464393233653432613134376530623261386461333436393766336530633661'
        '6161383066333665663939222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635'
        '36373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f7065'
        '5f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834'
        '30653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e'
        '5f75746638223a5b332c342c332c31395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c'
        '73652c2265706f6368223a226561676572222c226964223a223235343732353336386233393462626432663064373930323061313062643562366666'
        '6638346230313635646437643162353530306335343539616638313765222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a2270'
        '6c75676779222c22706172656e74223a2234306661636332366536363362363563643064653163346137306665373165613330656239303166313635'
        '356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a32222c227261775f73'
        '70616e5f736861323536223a226563353639373137323165316431306336626638616163333364323139383766373561373133333530343635613031'
        '6537373630373930346136613738353638222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962'
        '31303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c'
        '2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639'
        '64363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d'
        '2c227370616e5f75746638223a5b342c342c342c32375d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e61'
        '6c223a66616c73652c2265706f6368223a226561676572222c226964223a226630643564326631353161613435613231643538333838626130653163'
        '3431623730613262346536306339616361656262353134363463636132303738393264222c226b696e64223a22436f6e7374616e74222c226d6f6475'
        '6c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362363563643064653163346137306665373165613330656239'
        '303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a33222c'
        '227261775f7370616e5f736861323536223a226230353033386637363638343264303035636365346261333565623339396538356264363632633638'
        '3131323233656635653030346538643433613930663361222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22'
        '663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766306333333431353838393065'
        '33353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22'
        '306661373639643630393834306533623433613763383430633130373365616162383161626135396362653232393664616561393062306464666130'
        '66366438227d2c227370616e5f75746638223a5b352c342c352c31365d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e64'
        '6974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a226330666533626233643964613534306630363334333162'
        '3266393539653136316663633365366232326231613163636532656334393961383162366333383962222c226b696e64223a22436f6e7374616e7422'
        '2c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362363563643064653163346137306665373165'
        '613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c'
        '74733a34222c227261775f7370616e5f736861323536223a223332323634663832393461353031306435346661336437336536666131646337643438'
        '6433333438626638343232393061336139343135666232643931663438222c227265736f6c7574696f6e223a22756e7265736f6c766564222c227363'
        '6f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766306333333431'
        '35383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861'
        '323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362653232393664616561393062'
        '30646466613066366438227d2c227370616e5f75746638223a5b362c342c362c31395d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a226638663565336564323438646566643837'
        '3436646337646362323962613766326366346163613762333939386335326234616439303034626539656633393531222c226b696e64223a22436f6e'
        '7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362363563643064653163346137'
        '306665373165613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f7661'
        '6c75652f656c74733a35222c227261775f7370616e5f736861323536223a223735323536366430363262356566323239376631323136613064336466'
        '3765653333393533393465313566616237373635386264303730613135613334613065222c227265736f6c7574696f6e223a22756e7265736f6c7665'
        '64222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766'
        '30633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831'
        '312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362653232393664'
        '61656139306230646466613066366438227d2c227370616e5f75746638223a5b372c342c372c31385d7d2c7b226361706162696c697479223a227065'
        '6e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223566613339663735663765'
        '6564633033663464366439333739663630626233393635623864326464643436346537613835366334306634346237373565383039222c226b696e64'
        '223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362363563643064'
        '653163346137306665373165613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64'
        '793a302f76616c75652f656c74733a36222c227261775f7370616e5f736861323536223a223636653137623466313834356130653433626239623861'
        '6532306161626330303163623961343031613237326432366234343563623262303335666431383262222c227265736f6c7574696f6e223a22756e72'
        '65736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438'
        '34626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22627974'
        '6573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362'
        '65323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b382c342c382c31385d7d2c7b226361706162696c6974'
        '79223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223332613030'
        '303834383039353732363037366264326462316561396436373638343861633231633835633766353039393565323264636662353966386566363522'
        '2c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362'
        '363563643064653163346137306665373165613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a'
        '22242f626f64793a302f76616c75652f656c74733a37222c227261775f7370616e5f736861323536223a223365353161613932343863643533376334'
        '3865353038373631376337373839626564306663663236616136666634306464656630353137346535343563333134222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231'
        '36643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161'
        '62613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b392c342c392c31345d7d2c7b22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a'
        '226264626634303433383461343538333965616238633762336139356433323538373564653363343031633632333163383537303235663663353863'
        '3030646432222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332'
        '366536363362363563643064653163346137306665373165613330656239303166313635356662386662373230396234316437363234653732222c22'
        '70617468223a22242f626f64793a302f76616c75652f656c74733a38222c227261775f7370616e5f736861323536223a223737303065303664643961'
        '6639333061663139346339316430613339386233663938346331393331376232326634616539616532373235613731613230356134222c227265736f'
        '6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131'
        '32663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c2273'
        '6f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365'
        '61616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b31302c342c31302c3135'
        '5d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a2265616765'
        '72222c226964223a22363037396139656566366666613562653434393264353862373337646265353833303264373937613832383830366362613731'
        '39623965376665653732383939222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a'
        '223430666163633236653636336236356364306465316334613730666537316561333065623930316631363535666238666237323039623431643736'
        '3234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a39222c227261775f7370616e5f736861323536223a22623262'
        '343264666233306566316266303133346630663363613530326364383361636430396434323735366362666534616235373637313331393534343636'
        '65222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966'
        '393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f'
        '64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338'
        '343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b3131'
        '2c342c31312c32305d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f63'
        '68223a226561676572222c226964223a2230376334346235636335376436666362633334373534323932363663303961303063393430333036393732'
        '303964353136643161613438343935356164656566222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22706c75676779222c22'
        '706172656e74223a22343066616363323665363633623635636430646531633461373066653731656133306562393031663136353566623866623732'
        '30396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a3130222c227261775f7370616e5f736861'
        '323536223a22316331386434633937396132343235623134363563326165613335616664633336313439323432316132666466376165386136646336'
        '31666531643039306132222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536'
        '373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f'
        '6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137363964363039383430'
        '653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f'
        '75746638223a5b31322c342c31322c32305d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a6661'
        '6c73652c2265706f6368223a226561676572222c226964223a2261633237623337366333383464666332303632666135343036333762326262626334'
        '623833386437666662343331613035313264366332326436326661353362222c226b696e64223a22436f6e7374616e74222c226d6f64756c65223a22'
        '706c75676779222c22706172656e74223a22343066616363323665363633623635636430646531633461373066653731656133306562393031663136'
        '35356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c74733a3131222c22726177'
        '5f7370616e5f736861323536223a22333764386134303438336564343837653263613231363365396436326232623865636463363238373737336232'
        '34306135366461353461613561383531643138222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039'
        '396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464'
        '222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137'
        '363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438'
        '227d2c227370616e5f75746638223a5b31332c342c31332c31325d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974'
        '696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2231306463613530316639373038653732646365643635316534'
        '363838643135643135326133373065316331376439653637343466623439396431643866656439222c226b696e64223a22436f6e7374616e74222c22'
        '6d6f64756c65223a22706c75676779222c22706172656e74223a22343066616363323665363633623635636430646531633461373066653731656133'
        '30656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76616c75652f656c7473'
        '3a3132222c227261775f7370616e5f736861323536223a22616235336664376564636132303136303036626334356164626434373736356361633436'
        '38613032646139666137373032636138646230613265316530623538222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f'
        '7065223a2266373039396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135'
        '383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c2273686132'
        '3536223a2230666137363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230'
        '646466613066366438227d2c227370616e5f75746638223a5b31342c342c31342c31395d7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2234323462643131656530613637626665'
        '386339633966613734363534353161663431663539373239363438396339383564313835386332313061376435653835222c226b696e64223a22436f'
        '6e7374616e74222c226d6f64756c65223a22706c75676779222c22706172656e74223a22343066616363323665363633623635636430646531633461'
        '37306665373165613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64793a302f76'
        '616c75652f656c74733a3133222c227261775f7370616e5f736861323536223a22653061326465373033393633623663623830663163343238353264'
        '33333165636165646130383861353238323738333337303631643138386532363066306162222c227265736f6c7574696f6e223a22756e7265736f6c'
        '766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166393238313132663037323136643731643834626562'
        '376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a'
        '3831312c22736861323536223a2230666137363964363039383430653362343361376338343063313037336561616238316162613539636265323239'
        '366461656139306230646466613066366438227d2c227370616e5f75746638223a5b31352c342c31352c33335d7d2c7b226361706162696c69747922'
        '3a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2262323538623033'
        '666531356237383864346565613564653662316335393363316630663932333863336363663238313566356639646663333533303033636133222c22'
        '6b696e64223a224c6f6164222c226d6f64756c65223a22706c75676779222c22706172656e74223a2234306661636332366536363362363563643064'
        '653163346137306665373165613330656239303166313635356662386662373230396234316437363234653732222c2270617468223a22242f626f64'
        '793a302f76616c75652f637478222c227261775f7370616e5f736861323536223a6e756c6c2c227265736f6c7574696f6e223a22756e7265736f6c76'
        '6564222c2273636f7065223a226637303939623130343466353637303461343664396639316639323831313266303732313664373164383462656237'
        '6630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a38'
        '31312c22736861323536223a223066613736396436303938343065336234336137633834306331303733656161623831616261353963626532323936'
        '6461656139306230646466613066366438227d2c227370616e5f75746638223a6e756c6c7d2c7b226361706162696c697479223a2270656e64696e67'
        '222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c22696422'
        '3a2231663030333135343639636631626134363532383539653762643464323265656339376133353861313235383964663736366364643231356266'
        '363731366433222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a2266373039'
        '396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464'
        '222c2270617468223a22242f626f64793a31222c227261775f7370616e5f736861323536223a22383961366636626661636666316466303433616330'
        '66656365356166373362356439626530363761353132393736346636346264316538353562303338346665222c227265736f6c7574696f6e223a2275'
        '6e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166393238313132663037323136643731'
        '643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b2262'
        '79746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338343063313037336561616238316162613539'
        '636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b31372c302c31372c33305d7d2c7b22616c696173'
        '223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c'
        '22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22376236323964636662663235616332353038'
        '39653365353135653433386666353539333666393139333764636565363031373036303734323830346464356438222c226b696e64223a22616c6961'
        '73222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b43616c6c6572222c22706172656e74223a22316630303331353436'
        '39636631626134363532383539653762643464323265656339376133353861313235383964663736366364643231356266363731366433222c227061'
        '7468223a22242f626f64793a312f6e616d65733a30222c227261775f7370616e5f736861323536223a22643431613537386435346161653864376437'
        '30346363376633353263356230636161353563356433326330303330306365656131643933323862656461363766222c227265736f6c7574696f6e22'
        '3a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166393238313132663037323136'
        '643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a'
        '7b226279746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338343063313037336561616238316162'
        '613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b31372c32302c31372c33305d7d2c7b2263'
        '61706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c22'
        '65706f6368223a226561676572222c226964223a22383466333661333236396432623863396564323730303534333062643035353634653835313236'
        '66363138323336356334386566313031613461316466356262222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c75'
        '676779222c22706172656e74223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265'
        '62376630633333343135383839306533353464222c2270617468223a22242f626f64793a32222c227261775f7370616e5f736861323536223a223135'
        '373464353061656535366664323766366266633739616263613338333332333337633539366234393036376434666563623835363332393165323564'
        '3966222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439'
        '66393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d'
        '6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433613763'
        '38343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b31'
        '382c302c31382c32385d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c22636170'
        '6162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a'
        '226134653136343039383263643030326634633337663535393436376634376163633161666332643935386636633261333335363139373537333835'
        '3437616139222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b496d706c222c2270'
        '6172656e74223a2238346633366133323639643262386339656432373030353433306264303535363465383531323666363138323336356334386566'
        '313031613461316466356262222c2270617468223a22242f626f64793a322f6e616d65733a30222c227261775f7370616e5f736861323536223a2261'
        '613930313034336235616634383737346635326336313665653137633638666632306562346666636533653735353964653564303130663238656632'
        '366436222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226637303939623130343466353637303461343664'
        '3966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a22'
        '6d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a223066613736396436303938343065336234336137'
        '6338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b'
        '31382c32302c31382c32385d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265'
        '6666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a2265373435363262613936373439326539366436306538'
        '373962326637616235323932653838333566363163343231663861363266326635346439363534316366222c226b696e64223a22496d706f72744672'
        '6f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a2266373039396231303434663536373034613436643966393166393238'
        '313132663037323136643731643834626562376630633333343135383839306533353464222c2270617468223a22242f626f64793a33222c22726177'
        '5f7370616e5f736861323536223a22656562303436306364376666363434306464613966343530616138393363643833666131623839316364666665'
        '37376262393036383630613739623266356462222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039'
        '396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464'
        '222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137'
        '363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438'
        '227d2c227370616e5f75746638223a5b31392c302c31392c33345d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a2269'
        '6d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f'
        '6368223a226561676572222c226964223a22333539373765316564623163633032343965633637376531303362636439663536303237353037383966'
        '64376131306136613430356434646334313234623034222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c226e61'
        '6d65223a22486f6f6b696d706c4d61726b6572222c22706172656e74223a226537343536326261393637343932653936643630653837396232663761'
        '6235323932653838333566363163343231663861363266326635346439363534316366222c2270617468223a22242f626f64793a332f6e616d65733a'
        '30222c227261775f7370616e5f736861323536223a223539386461613465633663666334393039373262336432363132316363623863303635333061'
        '3231353861376164643533323438663037386366616264356532222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065'
        '223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766306333333431353838'
        '39306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536'
        '223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362653232393664616561393062306464'
        '66613066366438227d2c227370616e5f75746638223a5b31392c32302c31392c33345d7d2c7b226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a'
        '223732366235636331336138353565353630636264343639323962326636633837636261303331633361376563346339666535656434633139636633'
        '6461396666222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a226637303939'
        '623130343466353637303461343664396639316639323831313266303732313664373164383462656237663063333334313538383930653335346422'
        '2c2270617468223a22242f626f64793a34222c227261775f7370616e5f736861323536223a2232616334333938623563393930326161343335636663'
        '393139313162396131386439633932356531646238373534616165333030323064666666343639376230222c227265736f6c7574696f6e223a22756e'
        '7265736f6c766564222c2273636f7065223a226637303939623130343466353637303461343664396639316639323831313266303732313664373164'
        '3834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279'
        '746573223a3831312c22736861323536223a223066613736396436303938343065336234336137633834306331303733656161623831616261353963'
        '6265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32302c302c32302c33325d7d2c7b22616c69617322'
        '3a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22'
        '636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a2234356132613238653061373163313066646134'
        '303462313563323434323132333531363163666233383030323065376266313361643831633536393263333536222c226b696e64223a22616c696173'
        '222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b696d706c4f707473222c22706172656e74223a223732366235636331'
        '3361383535653536306362643436393239623266366338376362613033316333613765633463396665356564346331396366336461396666222c2270'
        '617468223a22242f626f64793a342f6e616d65733a30222c227261775f7370616e5f736861323536223a223634356636633938303865313864376330'
        '6633393730356334393637356264666238356166643963343837636161376166323364333134336365663064663338222c227265736f6c7574696f6e'
        '223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231'
        '36643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f7572636522'
        '3a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161'
        '62613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32302c32302c32302c33325d7d2c7b22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c'
        '2265706f6368223a226561676572222c226964223a223830306439623135633562643964343735636436343261393531363663316232626638363461'
        '6235663262386535323330643166343566313531366432363733222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c'
        '75676779222c22706172656e74223a226637303939623130343466353637303461343664396639316639323831313266303732313664373164383462'
        '6562376630633333343135383839306533353464222c2270617468223a22242f626f64793a35222c227261775f7370616e5f736861323536223a2235'
        '393030393563336232613933623362376334373164346134396438356139353033613230613531616233653236343936643732653532666231386463'
        '363034222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226637303939623130343466353637303461343664'
        '3966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a22'
        '6d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a223066613736396436303938343065336234336137'
        '6338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b'
        '32312c302c32312c32395d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361'
        '706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c22696422'
        '3a2232333739626434353431333462333961633364333561303762383831303637626161333162633032396639393666653461333735613562356332'
        '616534656433222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b52656c6179222c'
        '22706172656e74223a223830306439623135633562643964343735636436343261393531363663316232626638363461623566326238653532333064'
        '3166343566313531366432363733222c2270617468223a22242f626f64793a352f6e616d65733a30222c227261775f7370616e5f736861323536223a'
        '223136333933663364303031333839656234626465653131656533316338386334333036353264636439663539353735623066613064356436613862'
        '3637653964222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134'
        '36643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433'
        '61376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f7574663822'
        '3a5b32312c32302c32312c32395d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c'
        '22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a226663376237316265353464343630346137333836'
        '3536616333663830643130393965623931353733386239643139636436666438653961323933623839333361222c226b696e64223a22496d706f7274'
        '46726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a226637303939623130343466353637303461343664396639316639'
        '3238313132663037323136643731643834626562376630633333343135383839306533353464222c2270617468223a22242f626f64793a36222c2272'
        '61775f7370616e5f736861323536223a2235323265666137383330356239376564656662373030363637623433303734313262616133303536656635'
        '376162323234303239336463663632626535336163222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a226637'
        '303939623130343466353637303461343664396639316639323831313266303732313664373164383462656237663063333334313538383930653335'
        '3464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a223066'
        '613736396436303938343065336234336137633834306331303733656161623831616261353963626532323936646165613930623064646661306636'
        '6438227d2c227370616e5f75746638223a5b32322c302c32322c33345d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a'
        '22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265'
        '706f6368223a226561676572222c226964223a2264313533366361666638393531333565613939623162656664663936373765383261363865313738'
        '313933313637333839613964643862616236336637613162222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c22'
        '6e616d65223a22486f6f6b737065634d61726b6572222c22706172656e74223a22666337623731626535346434363034613733383635366163336638'
        '30643130393965623931353733386239643139636436666438653961323933623839333361222c2270617468223a22242f626f64793a362f6e616d65'
        '733a30222c227261775f7370616e5f736861323536223a22323362343831306334366637313538333064616361346330323433386631613537316261'
        '36356462323836636138356638663139373038333938396536303063222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f'
        '7065223a2266373039396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135'
        '383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c2273686132'
        '3536223a2230666137363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230'
        '646466613066366438227d2c227370616e5f75746638223a5b32322c32302c32322c33345d7d2c7b226361706162696c697479223a2270656e64696e'
        '67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964'
        '223a22616430313265333433333463643563373632333631373939616233653133356563323663663830613830396536306664386163396465646334'
        '63656363343166222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a22663730'
        '393962313034346635363730346134366439663931663932383131326630373231366437316438346265623766306333333431353838393065333534'
        '64222c2270617468223a22242f626f64793a37222c227261775f7370616e5f736861323536223a226264366664346664356234653730643932383238'
        '6233653336646430333231643638346561376535326638616338653035393532613037613764343239316432222c227265736f6c7574696f6e223a22'
        '756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437'
        '31643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22'
        '6279746573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135'
        '39636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32332c302c32332c33325d7d2c7b22616c6961'
        '73223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e6722'
        '2c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a223831663336653762343165663761613665'
        '3031343262343162613934303966623866393237626330653064393935613065346539336139663262303364313361222c226b696e64223a22616c69'
        '6173222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b737065634f707473222c22706172656e74223a22616430313265'
        '33343333346364356337363233363137393961623365313335656332366366383061383039653630666438616339646564633463656363343166222c'
        '2270617468223a22242f626f64793a372f6e616d65733a30222c227261775f7370616e5f736861323536223a22626133363737306538636664663961'
        '63626531366533613330343164646563643931613164353139333232313164663663363761653261313436376566626638222c227265736f6c757469'
        '6f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166393238313132663037'
        '323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f757263'
        '65223a7b226279746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338343063313037336561616238'
        '316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32332c32302c32332c33325d7d2c'
        '7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274'
        '222c2265706f6368223a226561676572222c226964223a22326238313436366364613832636235343166653264626636343137636635633038646138'
        '66363031366135346361653162336566633330336562313062373263222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22'
        '706c75676779222c22706172656e74223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438'
        '34626562376630633333343135383839306533353464222c2270617468223a22242f626f64793a38222c227261775f7370616e5f736861323536223a'
        '226239316166653433303730633835333431393731616265376539353862353930353365666232323334333833633033353863353434386363343465'
        '3939333730222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134'
        '36643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433'
        '61376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f7574663822'
        '3a5b32342c302c32342c33355d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c22'
        '6361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c2269'
        '64223a223030633333363866353462363532613062653932376363393338656134333138343338623137396362643831333034646636313532613332'
        '6630656136303364222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c226e616d65223a22506c7567696e4d616e'
        '61676572222c22706172656e74223a223262383134363663646138326362353431666532646266363431376366356330386461386636303136613534'
        '6361653162336566633330336562313062373263222c2270617468223a22242f626f64793a382f6e616d65733a30222c227261775f7370616e5f7368'
        '61323536223a223763313265646437666163356232333932643135666361653830313133336462636535663337396630633861646163626266633336'
        '3537313138383535653034222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635'
        '36373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f7065'
        '5f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834'
        '30653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e'
        '5f75746638223a5b32342c32322c32342c33355d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a'
        '66616c73652c22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a223333366665376235313039383935'
        '3931323962393231346430396437633562303032356230323665383233333234346136383132613635323632303331336234222c226b696e64223a22'
        '496d706f727446726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a226637303939623130343466353637303461343664'
        '3966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2270617468223a22242f626f6479'
        '3a39222c227261775f7370616e5f736861323536223a2237386236353334373334326439303339383235663364633834626134396464326261343233'
        '316336393865626462656334336334646464616166396365303330222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f70'
        '65223a226637303939623130343466353637303461343664396639316639323831313266303732313664373164383462656237663063333334313538'
        '3839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c227368613235'
        '36223a223066613736396436303938343065336234336137633834306331303733656161623831616261353963626532323936646165613930623064'
        '6466613066366438227d2c227370616e5f75746638223a5b32352c302c32352c34335d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f'
        '6b696e64223a22696d706f72745f616c696173222c226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a6661'
        '6c73652c2265706f6368223a226561676572222c226964223a2261366363313162326366393938353961663962343661346135363866663964633136'
        '323330623236633139366638663139366166636634633033346463363435222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75'
        '676779222c226e616d65223a22506c7567696e56616c69646174696f6e4572726f72222c22706172656e74223a223333366665376235313039383935'
        '3931323962393231346430396437633562303032356230323665383233333234346136383132613635323632303331336234222c2270617468223a22'
        '242f626f64793a392f6e616d65733a30222c227261775f7370616e5f736861323536223a226162373535373961356566663038353764333738376238'
        '6339393837316663366539623431366239316630643237356564636533353736353432323965313932222c227265736f6c7574696f6e223a22756e72'
        '65736f6c766564222c2273636f7065223a22663730393962313034346635363730346134366439663931663932383131326630373231366437316438'
        '34626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b22627974'
        '6573223a3831312c22736861323536223a22306661373639643630393834306533623433613763383430633130373365616162383161626135396362'
        '65323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32352c32322c32352c34335d7d2c7b22636170616269'
        '6c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c22656666656374223a22696d706f7274222c2265706f6368'
        '223a226561676572222c226964223a223839626563646430396363373834653461333861653364366164386237323332333361363438626364386536'
        '6431633131386362666136323464656533353463222c226b696e64223a22496d706f727446726f6d222c226d6f64756c65223a22706c75676779222c'
        '22706172656e74223a226637303939623130343466353637303461343664396639316639323831313266303732313664373164383462656237663063'
        '3333343135383839306533353464222c2270617468223a22242f626f64793a3130222c227261775f7370616e5f736861323536223a22643132303334'
        '63313031386362653833353436333337393963383763313338333131326537616439626564653333363064316332623933653862393939666336222c'
        '227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266373039396231303434663536373034613436643966393166'
        '393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e64223a226d6f64756c'
        '65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230666137363964363039383430653362343361376338343063'
        '313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f75746638223a5b32362c302c'
        '32362c33345d7d2c7b22616c696173223a6e756c6c2c2262696e64696e675f6b696e64223a22696d706f72745f616c696173222c226361706162696c'
        '697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c2265706f6368223a226561676572222c226964223a22323736'
        '313636383832666433666337613361636532626165333961306133323737363862613539623539643230373239396562356433653736616435653864'
        '65222c226b696e64223a22616c696173222c226d6f64756c65223a22706c75676779222c226e616d65223a22486f6f6b43616c6c4572726f72222c22'
        '706172656e74223a22383962656364643039636337383465346133386165336436616438623732333233336136343862636438653664316331313863'
        '62666136323464656533353463222c2270617468223a22242f626f64793a31302f6e616d65733a30222c227261775f7370616e5f736861323536223a'
        '223138353332393366323166316365316332336437316533366432326363333163346132646462383138636235353832346162393434376333613734'
        '3038656237222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a22663730393962313034346635363730346134'
        '36643966393166393238313132663037323136643731643834626562376630633333343135383839306533353464222c2273636f70655f6b696e6422'
        '3a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a22306661373639643630393834306533623433'
        '61376338343063313037336561616238316162613539636265323239366461656139306230646466613066366438227d2c227370616e5f7574663822'
        '3a5b32362c32312c32362c33345d7d2c7b226361706162696c697479223a2270656e64696e67222c22636f6e646974696f6e616c223a66616c73652c'
        '22656666656374223a22696d706f7274222c2265706f6368223a226561676572222c226964223a226363653964633765393438613532313532643830'
        '3039383933633637323962326639306330303834383437396533386163643864646565313735623738393962222c226b696e64223a22496d706f7274'
        '46726f6d222c226d6f64756c65223a22706c75676779222c22706172656e74223a226637303939623130343466353637303461343664396639316639'
        '3238313132663037323136643731643834626562376630633333343135383839306533353464222c2270617468223a22242f626f64793a3131222c22'
        '7261775f7370616e5f736861323536223a22636536393333336632643266393166666466393566336666333739346532386661336566666265633537'
        '33303336303237633962376466656465623934303533222c227265736f6c7574696f6e223a22756e7265736f6c766564222c2273636f7065223a2266'
        '373039396231303434663536373034613436643966393166393238313132663037323136643731643834626562376630633333343135383839306533'
        '353464222c2273636f70655f6b696e64223a226d6f64756c65222c22736f75726365223a7b226279746573223a3831312c22736861323536223a2230'
        '666137363964363039383430653362343361376338343063313037336561616238316162613539636265323239366461656139306230646466613066'
        '366438227d2c227370616e5f75746638223a5b32372c302c32372c32375d7d5d2c22736368656d61223a2263686f35315f6c5f7265736f6c7665725f'
        '706167655f7631227d'
    )
    request = dict(schema='cho51_source_probe_request_v1', case_id='packaging_source_v1',
        module='packaging', source_pin=dict(c._sp_pins()[0]),
        index_pin=dict(c._sp_pins()[1]), page_pin=dict(c._sp_pins()[2]),
        page_ordinal=54, selected_ordinals=list(range(176, 214)),
        global_resolver_rows=18793, global_inventory_rows=13406,
        desired_product='syntax_observation_only')
    return request, source, index, page

class SourceProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = source_probe_fixture()
        cls.observed = c.observe_selected_source(*cls.fixture, lambda: True)

    def call(self, request=None, source=None, index=None, page=None, guard=lambda: True):
        req, src, idx, pg = self.fixture
        return c.observe_selected_source(req if request is None else request,
            src if source is None else source, idx if index is None else index,
            pg if page is None else page, guard)

    def changed(self, **fields):
        request = dict(self.fixture[0]); request.update(fields); return request

    def test_rs01_fixed_supplied_case(self):
        self.assertEqual(self.observed['outcome'], 'OBSERVED_SELECTED_SOURCE')
        self.assertIsNone(self.observed['reason'])

    def test_rs02_closed_schema_and_types(self):
        missing = dict(self.fixture[0]); del missing['module']
        for req in (missing, self.changed(extra=1), self.changed(page_ordinal=True),
                    self.changed(global_resolver_rows=18793.0), self.changed(source_pin={'bytes': 494, 'sha256': 'G'*64})):
            self.assertEqual(self.call(request=req)['reason'], 'schema')

    def test_rs03_fixed_selection(self):
        for req in (self.changed(module='other'), self.changed(page_ordinal=53),
                    self.changed(selected_ordinals=list(range(177, 214))+[176]),
                    self.changed(selected_ordinals=[176]*38)):
            self.assertEqual(self.call(request=req)['reason'], 'selection')
        self.assertEqual(self.call(request=self.changed(desired_product='checkpoint'))['reason'], 'unsupported_product')

    def test_rs04_raw_pin_before_parse(self):
        for name in ('source', 'index', 'page'):
            data = self.fixture[{'source': 1, 'index': 2, 'page': 3}[name]]
            self.assertEqual(self.call(**{name: data + b' '})['reason'], 'pin')

    def test_rs05_historical_descriptor(self):
        idx = c._sp_json(self.fixture[2], lambda: True)
        page = c._sp_json(self.fixture[3], lambda: True)
        idx['pages'][54]['sha256'] = '0' * 64
        with self.assertRaises(c.Refusal): c._sp_page_membership(idx, page, lambda: True)
        idx['pages'][54]['sha256'] = self.fixture[0]['page_pin']['sha256']
        page['rows'][178]['parent'] = page['rows'][180]['id']
        with self.assertRaises(c.Refusal): c._sp_page_membership(idx, page, lambda: True)

    def test_rs06_full_page_and_index(self):
        page = c._sp_json(self.fixture[3], lambda: True)
        self.assertEqual(len(page['rows']), 256)
        self.assertNotEqual(page['rows'][0].get('module'), 'packaging')
        self.assertEqual(len(c._sp_json(self.fixture[2], lambda: True)['pages']), 74)

    def test_rs07_strict_json(self):
        for raw in (b'{"x":1,"x":2}', b'[]x', b'NaN', b'1.0', b'['*34+b']'*34,
                    b'[' + b'0,'*4096 + b'0]', b'"' + b'a'*65537 + b'"'):
            with self.assertRaises(c.Refusal): c._sp_json(raw, lambda: True)
        for raw, expected in ((b'"'+b'a'*65536+b'"', 'a'*65536),
                              (b'"\\u00e9\\n"', '\u00e9\n'),
                              (b'{"x":-9223372036854775808}', {'x': -(2**63)})):
            self.assertEqual(c._sp_json(raw, lambda: True), expected)
        for raw in (b'{"x":9223372036854775808}', b'"\xff"', b'"\\uZZZZ"',
                    b'{"'+b'a'*65537+b'":0}', b'{"x":[1,]}'):
            with self.assertRaises(c.Refusal): c._sp_json(raw, lambda: True)
        # A whitespace-only byte traversal and a dense value traversal exercise
        # both finite checkpoint budgets without a native resource sensor.
        for raw in (b' '*65536+b'0', b'['+b'0,'*1023+b'0]'):
            count = [0]
            def allowed():
                count[0] += 1
                return True
            c._sp_json(raw, allowed)
            self.assertGreaterEqual(count[0], 6)
            for boundary in range(1, count[0]+1):
                seen = [0]
                def denied():
                    seen[0] += 1
                    return seen[0] != boundary
                with self.assertRaises(c.SourceProbeCheckpointRefusal): c._sp_json(raw, denied)

    def test_rs08_origin_is_not_custody(self):
        report = self.observed['report']
        self.assertTrue(report['origin_pin_equal'])
        self.assertFalse(report['authority']['historical_custody_closed'])

    def test_rs09_full_field_traversal(self):
        rows = self.observed['report']['observations']
        self.assertEqual(len(rows), 37)
        self.assertEqual(rows[0]['path'], '$')
        self.assertIn('$/body:0/targets:0/ctx', [x['path'] for x in rows])
        self.assertTrue(self.observed['report']['selected_syntax_equal'])

    def test_rs10_parent_identity(self):
        rows = self.observed['report']['observations']
        for row in rows[1:]:
            self.assertIn(row['parent'], {x['id'] for x in rows})
        self.assertNotEqual(rows[1]['id'], rows[2]['id'])

    def test_rs11_bom_crlf_null_spans(self):
        rows = c._sp_observe(b'\xef\xbb\xbfx = 1\r\n', lambda: True)
        self.assertIsNone(rows[0]['span_utf8'])
        self.assertEqual(rows[1]['span_utf8'], [1, 0, 1, 5])
        self.assertEqual(rows[1]['raw_span_sha256'], hashlib.sha256(b'x = 1').hexdigest())
        unicode_rows = c._sp_observe(b"x='\xc3\xa9'\n", lambda: True)
        literal = next(row for row in unicode_rows if row['kind'] == 'Constant')
        self.assertEqual(literal['span_utf8'], [1, 2, 1, 6])
        self.assertEqual(literal['raw_span_sha256'], hashlib.sha256(b"'\xc3\xa9'").hexdigest())
        invalid = c.ast.Name(id='x', ctx=c.ast.Load(), lineno=1, col_offset=9,
                             end_lineno=1, end_col_offset=10)
        with self.assertRaises(c.Refusal): c._sp_span(invalid, b'x\n', [b'x\n'], [0], lambda: True)

    def test_rs12_extra_node_changes_count(self):
        rows = self.observed['report']['observations']
        comparisons, equal = c._sp_compare(rows, rows[:-1], lambda: True)
        self.assertFalse(equal); self.assertIsNone(comparisons[-1]['observed_id'])
        extra = dict(rows[-1], id='f'*64, path='$/extra')
        self.assertFalse(c._sp_compare(rows, rows + [extra], lambda: True)[1])

    def test_rs13_comparison_has_six_fields(self):
        row = self.observed['report']['comparisons'][0]
        self.assertEqual(row['compared_fields'], list(c._SOURCE_PROBE_FIELDS))
        self.assertEqual(row['outcome'], 'SYNTAX_FIELDS_EQUAL')
        rows = self.observed['report']['observations']; changed = [dict(x) for x in rows]
        changed[1]['kind'] = 'Changed'
        comparisons, equal = c._sp_compare(rows, changed, lambda: True)
        self.assertFalse(equal); self.assertEqual(comparisons[1]['outcome'], 'SYNTAX_FIELDS_DIFFER')

    def test_rs14_distinct_observation_identities(self):
        rows = self.observed['report']['observations']
        self.assertEqual(len({x['id'] for x in rows}), len(rows))
        self.assertEqual(len({x['path'] for x in rows}), len(rows))
        with self.assertRaises(c.Refusal): c._sp_compare(rows, rows + [dict(rows[0])], lambda: True)
        with self.assertRaises(c.Refusal): c._sp_compare(rows + [dict(rows[0])], rows, lambda: True)

    def test_rs15_semantics_stay_unresolved(self):
        rows = c._sp_json(self.fixture[3], lambda: True)['rows'][176:214]
        self.assertEqual(sum('effect' in row for row in rows), 10)
        self.assertEqual(sum(row.get('binding_kind') == 'Load' and row.get('resolution') == 'unresolved' for row in rows), 1)
        self.assertFalse(self.observed['report']['authority']['capabilities_accepted'])

    def test_rs16_conservation(self):
        scope = self.observed['report']['global_scope']
        self.assertEqual((scope['resolver_rows'], scope['inventory_rows'], scope['selected_rows'], scope['unselected_resolver_rows']), (18793, 13406, 38, 18755))
        self.assertEqual(scope['obligations_discharged'], 0)
        self.assertIs(scope['global_ledger_mutated'], False)

    def test_rs17_forbidden_products(self):
        for product in ('continuation', 'full_reconciliation', 'scope_sweep', 'p_consumer'):
            self.assertEqual(self.call(request=self.changed(desired_product=product))['outcome'], 'REFUSED_SCOPE')

    def test_rs18_report_schema_is_not_state(self):
        report = self.observed['report']
        self.assertEqual(report['schema'], c.SOURCE_PROBE_REPORT)
        self.assertNotEqual(report['schema'], c.FRONTIER_SCHEMA)
        self.assertNotEqual(report['schema'], c.LOSSLESS_SCHEMA)
        with self.assertRaises(c.Refusal): c._frontier_verify(report, '0'*64, {}, lambda: True)
        result = c.verify_supplied_bundle(report, {}, '0'*64, {}, {}, {}, lambda: True)
        self.assertNotEqual(result['outcome'], 'VERIFIED_SUPPLIED_STATE')

    def test_rs19_safe_parser_refusal(self):
        with self.assertRaises(c.Refusal) as failure: c._sp_observe(b'if :\n', lambda: True)
        self.assertEqual(str(failure.exception), 'parser')
        with self.assertRaises(c.Refusal) as failure: c._sp_observe(b'# coding: latin-1\n', lambda: True)
        self.assertEqual(str(failure.exception), 'source_encoding')

    def test_rs20_source_and_node_bounds(self):
        self.assertTrue(c._sp_observe(b' '*4096, lambda: True))
        with self.assertRaises(c.Refusal): c._sp_observe(b' '*4097, lambda: True)
        self.assertEqual(len(c._sp_observe(b'pass\n'*127, lambda: True)), 128)
        with self.assertRaises(c.Refusal): c._sp_observe(b'pass\n'*128, lambda: True)
        self.assertTrue(c._sp_observe(b'-'*30 + b'1\n', lambda: True))
        with self.assertRaises(c.Refusal): c._sp_observe(b'-'*31 + b'1\n', lambda: True)

    def test_rs21_encoder_bound(self):
        value = ['a'*65536, 'a'*65536, 'a'*65536, 'a'*65523]
        self.assertEqual(len(c._sp_encode(value, lambda: True, 262144)), 262144)
        value[-1] += 'a'
        with self.assertRaises(c.Refusal): c._sp_encode(value, lambda: True, 262144)
        for fixture in (None, True, -(2**63), 2**63-1, [], {},
                        {'z':'\U0001f600\ud800\n\\"', 'a':['\u00e9', 0, False]},
                        'x'*65536, self.observed['report']):
            expected = json.dumps(fixture, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
            self.assertEqual(c._sp_encode(fixture, lambda: True, 262144), expected)
            self.assertEqual(c._sp_encode(fixture, lambda: True, 262144), c._ls_encode(fixture, lambda: True, 262144))
        for fixture in (1.0, 2**63, -(2**63)-1, 'x'*65537, {1:'x'}, tuple()):
            with self.assertRaises(c.Refusal): c._sp_encode(fixture, lambda: True, 262144)
        counts = [0]
        def allowed():
            counts[0] += 1
            return True
        dense = list(range(1024))
        c._sp_encode(dense, allowed, 262144)
        self.assertGreaterEqual(counts[0], 10)
        for boundary in range(1, counts[0]+1):
            seen = [0]
            def denied():
                seen[0] += 1
                return seen[0] != boundary
            with self.assertRaises(c.SourceProbeCheckpointRefusal): c._sp_encode(dense, denied, 262144)

    def test_rs22_report_is_bounded(self):
        self.assertLessEqual(len(c._sp_encode(self.observed['report'], lambda: True, 262144)), 262144)
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        self.assertEqual(sum(x[0] for x in protocol.ALLOCATION.values()), 256)
        self.assertEqual(sum(x[1] for x in protocol.ALLOCATION.values()), 64*1024**2)
        for bucket, (files, size) in protocol.ALLOCATION.items():
            protocol.validate_allocation(bucket, files, size, min(size, 8*1024**2))
            for args in ((files+1, size, 1), (files, size+1, 1), (True, 1, 1),
                         (1, 1, 2), (0, 1, 0), (1, 8*1024**2+1, 8*1024**2+1)):
                with self.assertRaises(ValueError): protocol.validate_allocation(bucket, *args)

    def test_rs23_raw_assets_counted(self):
        self.assertEqual(sum(map(len, self.fixture[1:])), 199609)
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        asset = sum(map(len, self.fixture[1:]))
        copies = asset * 2
        protocol.validate_allocation('fixtures', 6, copies, len(self.fixture[3]))
        with self.assertRaises(ValueError):
            protocol.validate_allocation('fixtures', 161, copies, len(self.fixture[3]))
        assets = {name: [raw[i:i+2048].hex() for i in range(0, len(raw), 2048)]
                  for (name, _, _), raw in zip(protocol.PROBE_ASSETS, self.fixture[1:])}
        calls = [0]
        def allowed():
            calls[0] += 1
            return True
        decoded = protocol.validate_probe_assets(assets, 'probe', allowed)
        self.assertEqual(tuple(decoded[name] for name, _, _ in protocol.PROBE_ASSETS), self.fixture[1:])
        self.assertGreater(calls[0], 15)
        with self.assertRaises(ValueError): protocol.validate_probe_assets(assets, 'probe')
        for boundary in range(1, calls[0]+1):
            seen = [0]
            def denied():
                seen[0] += 1
                return seen[0] != boundary
            with self.assertRaises(RuntimeError): protocol.validate_probe_assets(assets, 'probe', denied)
        for bad_guard in (lambda: 1, lambda: (_ for _ in ()).throw(RuntimeError('late transport fault'))):
            with self.assertRaises(RuntimeError): protocol.validate_probe_assets(assets, 'probe', bad_guard)
        tampered = {name: list(parts) for name, parts in assets.items()}
        tampered['source'][0] = '00' + tampered['source'][0][2:]
        with self.assertRaises(ValueError): protocol.validate_probe_assets(tampered, 'probe', lambda: True)

    def test_rs24_guard_refusal(self):
        for guard in (lambda: False, lambda: 1, lambda: (_ for _ in ()).throw(RuntimeError('private'))):
            with self.assertRaises(c.SourceProbeCheckpointRefusal): self.call(guard=guard)
        for limit in (2, 4, 20):
            count = [0]
            def guard():
                count[0] += 1
                return count[0] < limit
            with self.assertRaises(c.SourceProbeCheckpointRefusal): self.call(guard=guard)
        for operation in (lambda g: c._sp_observe(b'x=1\n', g),
                          lambda g: c._sp_compare(self.observed['report']['observations'], self.observed['report']['observations'], g),
                          lambda g: c._sp_encode(self.observed['report'], g, 262144)):
            for limit in (1, 2, 3):
                count = [0]
                def guard():
                    count[0] += 1
                    return count[0] < limit
                with self.assertRaises(c.SourceProbeCheckpointRefusal): operation(guard)
        # Arm only after a production helper has detected the late failure (or
        # completed final encoding). Earlier guard samples cannot satisfy this.
        for boundary in ('scope', 'pin', 'capacity', 'success'):
            armed = [False]
            original_encode, original_hash = c._sp_encode, c._sp_hash
            def encoded(value, guard, limit):
                result = original_encode(value, guard, limit)
                if (boundary == 'scope' and limit == 16384) or (boundary in ('capacity', 'success') and limit == 262144):
                    armed[0] = True
                    if boundary == 'capacity': raise c.Refusal('bound')
                return result
            def hashed(raw, guard):
                result = original_hash(raw, guard)
                if boundary == 'pin' and raw == self.fixture[1]:
                    armed[0] = True
                    return '0' * 64
                return result
            def late_guard():
                if armed[0] and boundary == 'capacity': raise RuntimeError('late private fault')
                return not armed[0]
            try:
                c._sp_encode, c._sp_hash = encoded, hashed
                request = self.changed(desired_product='checkpoint') if boundary == 'scope' else None
                with self.assertRaises(c.SourceProbeCheckpointRefusal):
                    if request is None: self.call(guard=late_guard)
                    else: self.call(request=request, guard=late_guard)
                self.assertTrue(armed[0])
            finally:
                c._sp_encode, c._sp_hash = original_encode, original_hash

    def test_rs25_deterministic_immutable(self):
        before = tuple(self.fixture[1:])
        self.assertEqual(self.call(), self.observed)
        self.assertEqual(self.fixture[1:], before)

    def test_rs26_self_certified_pin_refused(self):
        pin = dict(self.fixture[0]['source_pin']); pin['sha256'] = hashlib.sha256(b'x').hexdigest(); pin['bytes'] = 1
        self.assertEqual(self.call(request=self.changed(source_pin=pin), source=b'x')['reason'], 'pin')

    def test_rs27_refusal_has_no_report(self):
        result = self.call(source=b'wrong')
        self.assertIsNone(result['report'])
        self.assertEqual(result['checks_completed'], [])
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        protocol.validate_probe_observation(self.observed, 'probe')
        for altered in (result, dict(self.observed, checks_completed=[]),
                        dict(self.observed, outcome='REFUSED_INPUT', report=None)):
            with self.assertRaises(ValueError): protocol.validate_probe_observation(altered, 'probe')
        for cohort in ('inherited', 'lossless'):
            protocol.validate_probe_observation(None, cohort)
            with self.assertRaises(ValueError): protocol.validate_probe_observation(self.observed, cohort)

    def test_rs28_no_custody_grant(self):
        self.assertFalse(self.observed['report']['authority']['current_p_custody_refreshed'])
        self.assertFalse(self.observed['report']['authority']['historical_custody_closed'])
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        for key in self.observed['report']['authority']:
            bad = json.loads(c.encode(self.observed)); bad['report']['authority'][key] = True
            with self.assertRaises(ValueError): protocol.validate_probe_observation(bad, 'probe')

    def test_rs29_no_progress_state(self):
        report = self.observed['report']
        for key in ('cursor', 'history', 'frame', 'checkpoint', 'aggregate'):
            self.assertNotIn(key, report)
        self.assertEqual(report['global_scope']['obligations_discharged'], 0)

    def test_rs30_exact_probe_roster(self):
        names = [name for name in dir(type(self)) if name.startswith('test_rs')]
        self.assertEqual(len(names), 32)
        self.assertEqual({name[5:9] for name in names}, {'rs%02d' % n for n in range(1, 33)})
        protocol = sys.modules['tools.local_validation.lq18.protocol']
        prefix = 'tools.local_validation.lplan15.test_compiler.'
        probe = [prefix+'SourceProbeTests.'+name for name in names]
        lossless = [prefix+cls.__name__+'.'+name for cls in (ResolverTests, FrontierTests, LosslessTests)
                    for name in dir(cls) if name.startswith('test_')]
        inherited = ['inherited.case_%03d' % i for i in range(384)]
        self.assertEqual([protocol.qualification_cohort(x) for x in (inherited, lossless, probe)],
                         ['inherited', 'lossless', 'probe'])
        self.assertEqual(len(set(inherited + lossless + probe)), 516)
        for bad in (probe[:-1], probe + probe[:1], probe[:-1] + lossless[:1]):
            with self.assertRaises(ValueError): protocol.qualification_cohort(bad)

    def test_rs31_original_kernel_limit(self):
        self.assertEqual(c.FRONTIER_LIMITS['rows'], 24000)
        self.assertGreater(31002, c.FRONTIER_LIMITS['rows'])

    def test_rs32_all_authority_false(self):
        self.assertTrue(all(value is False for value in self.observed['report']['authority'].values()))
        self.assertFalse(self.observed['report']['global_scope']['global_ledger_mutated'])
        supervisor = sys.modules['tools.local_validation.lp18.supervisor']
        with self.assertRaisesRegex(ValueError, 'Q-library-only'):
            supervisor.main(None, None, None, None, None)
