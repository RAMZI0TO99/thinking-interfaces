"""Supplied-byte fixtures only. Execution requires separate project admission."""
import hashlib
import json
import unittest
from tools.local_validation.lplan5 import compiler as c


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

from tools.local_validation.lplan5 import migration as m

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
    from tools.local_validation.lp8 import supervisor as host
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
