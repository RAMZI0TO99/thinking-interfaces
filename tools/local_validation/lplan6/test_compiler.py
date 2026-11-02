"""Supplied-byte fixtures only. Execution requires separate project admission."""
import hashlib
import json
import unittest
from tools.local_validation.lplan6 import compiler as c


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

from tools.local_validation.lplan6 import migration as m

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
    from tools.local_validation.lp9 import supervisor as host
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
