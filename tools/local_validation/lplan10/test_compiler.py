"""Supplied-byte fixtures only. Execution requires separate project admission."""
import hashlib
import json
import sys
import unittest
from tools.local_validation.lplan10 import compiler as c


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

from tools.local_validation.lplan10 import migration as m

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
    from tools.local_validation.lp13 import supervisor as host
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
        protocol = sys.modules['tools.local_validation.lq13.protocol']
        prefix = 'tools.local_validation.lplan10.test_compiler.'
        names = [prefix+cls.__name__+'.'+name for cls in (ResolverTests,FrontierTests,LosslessTests)
                 for name in dir(cls) if name.startswith('test_')]
        self.assertEqual('lossless',protocol.qualification_cohort(names))
        inherited_name = 'tools.local_validation.lq13.test_protocol.ProtocolTests.test_complete_window'
        for bad in (names[:-1],names+names[:1],names[:-1]+[inherited_name]):
            with self.assertRaises(ValueError): protocol.qualification_cohort(bad)
        # Admission/report/control integration is exercised by the separately
        # discovered inherited ProtocolTests.test_complete_window and
        # test_report_omissions_failures_and_false_authority; this method tests
        # this exact new100 roster rather than duplicating those controls.
    def test_ls28_no_execution_authority(self):
        supervisor = sys.modules['tools.local_validation.lp13.supervisor']
        with self.assertRaisesRegex(ValueError,'Q-library-only'): supervisor.main(None,None,None,None,None)
        fixture_module = sys.modules['tools.local_validation.lp13.test_protocol']
        protocol = sys.modules['tools.local_validation.lp13.protocol']
        request, review, adoption, qualification, coverage, source, actual, mapping, plan = fixture_module.fixtures()
        aggregate, material = fixture_module.aggregate_fixture(request,qualification,source,actual)
        self.assertEqual([384,40],protocol.validate_aggregate(request,aggregate,material,qualification)['counts'])
        aggregate['schema'] = 'cho51_lossless_q_aggregate_v1'; aggregate['expected_counts']['resolver'] = 100
        with self.assertRaises(protocol.r.Refusal): protocol.validate_aggregate(request,aggregate,material,qualification)
