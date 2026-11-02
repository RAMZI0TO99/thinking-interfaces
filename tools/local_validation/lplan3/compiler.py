"""Bounded, non-executing AST observation; never produces a plan."""
import ast
import hashlib
import json
import re
import tokenize
from io import BytesIO

SCHEMA = 'cho51_l_inventory_spec_v1'
HARD = {'max_modules': 5, 'max_source_bytes': 4 * 1024**3,
        'max_module_bytes': 8 * 1024**2, 'max_nodes': 2_000_000,
        'max_depth': 128, 'max_output_files': 256, 'max_output_bytes': 64 * 1024**2}

class Refusal(ValueError):
    pass

def need(ok, message):
    if not ok:
        raise Refusal(message)

def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys), 'closed schema')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')

def pin(value):
    closed(value, ('bytes', 'sha256'))
    need(type(value['bytes']) is int and 0 <= value['bytes'] <= HARD['max_module_bytes'], 'pin size')
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None, 'pin hash')

def validate(spec, physical):
    closed(spec, ('schema', 'modules', 'limits', 'migration_ref'))
    need(spec['schema'] == SCHEMA, 'schema')
    limits = spec['limits']
    closed(limits, HARD)
    for key, maximum in HARD.items():
        need(type(limits[key]) is int and 1 <= limits[key] <= maximum, 'limit ' + key)
    modules = spec['modules']
    need(type(modules) is list and len(modules) == 5 and len(modules) <= limits['max_modules'], 'five modules required')
    need(type(physical) is dict, 'physical map')
    names, paths, total = set(), set(), 0
    for row in modules:
        closed(row, ('module', 'path', 'phase', 'pin'))
        for key in ('module', 'path', 'phase'):
            need(type(row[key]) is str and 0 < len(row[key]) <= 1024 and '\x00' not in row[key], 'module field')
        need(re.fullmatch(r'[A-Za-z_]\w*(\.[A-Za-z_]\w*)*', row['module'], re.ASCII) is not None, 'module name')
        need(row['module'].casefold() not in names and row['path'].casefold() not in paths, 'duplicate module')
        names.add(row['module'].casefold()); paths.add(row['path'].casefold())
        pin(row['pin']); total += row['pin']['bytes']
        need(row['pin']['bytes'] <= limits['max_module_bytes'], 'module bytes')
        item = physical.get(row['path'])
        need(type(item) is dict and all(item.get(k) == v for k, v in row['pin'].items()), 'physical pin')
    need(total <= limits['max_source_bytes'], 'source bytes')
    ref = spec['migration_ref']
    if ref is not None:
        closed(ref, ('path', 'bytes', 'sha256'))
        need(type(ref['path']) is str and 0 < len(ref['path']) <= 1024, 'migration path')
        pin({'bytes': ref['bytes'], 'sha256': ref['sha256']})
    return limits

def source_text(raw):
    try:
        encoding, _ = tokenize.detect_encoding(BytesIO(raw).readline)
        need(encoding.lower().replace('_', '-') in ('utf-8', 'utf-8-sig', 'ascii'), 'unsupported encoding')
        return raw.decode(encoding)
    except (SyntaxError, UnicodeError, LookupError):
        raise Refusal('unsupported encoding') from None

def diagnostic(exc, text):
    result = {'kind': type(exc).__name__, 'message': 'parser rejected source', 'line': None,
              'character_column_1based': None, 'utf8_byte_column_0based': None,
              'end_line': None, 'end_character_column_1based': None,
              'end_utf8_byte_column_0based': None}
    if isinstance(exc, SyntaxError):
        # Never publish interpreter suggestions containing source snippets.
        safe = ('invalid syntax', "expected ':'", "'(' was never closed", "'[' was never closed",
                "'{' was never closed", 'unexpected indent', 'unexpected EOF while parsing')
        if exc.msg in safe:
            result['message'] = exc.msg
        result['line'] = exc.lineno if type(exc.lineno) is int and exc.lineno > 0 else None
        offset = exc.offset if type(exc.offset) is int and exc.offset > 0 else None
        result['character_column_1based'] = offset
        lines = text.splitlines()
        if result['line'] is not None and offset is not None and result['line'] <= len(lines):
            line = lines[result['line'] - 1]
            if offset - 1 <= len(line):
                result['utf8_byte_column_0based'] = len(line[:offset - 1].encode('utf-8'))
        end_line = exc.end_lineno if type(exc.end_lineno) is int and exc.end_lineno > 0 else None
        end_offset = exc.end_offset if type(exc.end_offset) is int and exc.end_offset > 0 else None
        result['end_line'] = end_line
        result['end_character_column_1based'] = end_offset
        if end_line is not None and end_offset is not None and end_line <= len(lines):
            line = lines[end_line - 1]
            if end_offset - 1 <= len(line):
                result['end_utf8_byte_column_0based'] = len(line[:end_offset - 1].encode('utf-8'))
    return result

def child_context(node, field, scope, epoch, node_id):
    # Conservative labels: all unresolved execution semantics stay unknown.
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and field == 'body':
        return node_id, 'deferred'
    if isinstance(node, ast.ClassDef) and field == 'body':
        return node_id, epoch
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        return node_id, 'unknown'
    if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and field in ('returns', 'type_params')) or (isinstance(node, ast.arg) and field == 'annotation') or (isinstance(node, ast.AnnAssign) and field == 'annotation'):
        return scope, 'unknown'
    return scope, epoch

def inventory(raw, row, limits, remaining, checkpoint):
    text = source_text(raw)
    try:
        tree = ast.parse(raw, filename=row['path'], mode='exec')
    except (SyntaxError, ValueError, RecursionError) as exc:
        return [], diagnostic(exc, text)
    # Parse coordinates are UTF-8 byte offsets into decoded text; BOM is excluded.
    lines = re.findall(rb'.*?(?:\r\n|\r|\n|$)', text.encode('utf-8'), re.DOTALL)
    if lines and not lines[-1]:
        lines.pop()
    starts = []; offset = 3 if raw.startswith(b'\xef\xbb\xbf') else 0
    for line in lines:
        starts.append(offset); offset += len(line)
    records, stack = [], [(tree, None, '$', 0, '$', 'eager', False)]
    scope_parents = {'$': None}
    while stack:
        node, parent, path, depth, scope, epoch, done = stack.pop()
        if done:
            rec = records[node[0]]
            fields = []
            for name, value in ast.iter_fields(node[1]):
                if isinstance(value, ast.AST):
                    fields.append([name, {'node': value._lplan_hash}])
                elif isinstance(value, list):
                    fields.append([name, [{'node': v._lplan_hash} if isinstance(v, ast.AST) else repr(v) for v in value]])
                else:
                    fields.append([name, repr(value)])
            node[1]._lplan_hash = digest(encode([type(node[1]).__name__, fields]))
            rec['shape_sha256'] = node[1]._lplan_hash
            continue
        need(depth <= limits['max_depth'], 'AST depth limit')
        need(len(records) < remaining, 'AST node limit')
        if len(records) % 256 == 0:
            need(checkpoint() is True, 'checkpoint refused')
        idx = len(records)
        ident = digest(encode([row['module'], row['pin']['sha256'], path]))
        coords = [getattr(node, key, None) for key in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')]
        span_hash = None
        if all(type(x) is int for x in coords):
            a, b, c, d = coords
            need(1 <= a <= c <= len(starts) and 0 <= b <= len(lines[a-1]) and 0 <= d <= len(lines[c-1]), 'invalid AST span')
            begin, end = starts[a-1] + b, starts[c-1] + d
            need(begin <= end <= len(raw), 'invalid raw span')
            span_hash = digest(raw[begin:end])
        else:
            coords = None
        rec = {'id': ident, 'parent': parent, 'path': path, 'scope': scope, 'kind': type(node).__name__,
               'scope_parent': scope_parents.get(scope), 'span_utf8': coords, 'raw_span_sha256': span_hash, 'shape_sha256': None,
               'context': type(getattr(node, 'ctx', None)).__name__ if hasattr(node, 'ctx') else 'unknown',
               'epoch': epoch, 'analysis': 'unresolved'}
        records.append(rec)
        stack.append(((idx, node), parent, path, depth, scope, epoch, True))
        children = []
        for name, value in ast.iter_fields(node):
            vals = enumerate(value) if isinstance(value, list) else [(None, value)]
            for pos, child in vals:
                if isinstance(child, ast.AST):
                    child_path = path + '/' + name + (':' + str(pos) if pos is not None else '')
                    child_scope, child_epoch = child_context(node, name, scope, epoch, ident)
                    if child_scope == ident:
                        scope_parents.setdefault(ident, scope)
                    children.append((child, ident, child_path, depth + 1, child_scope, child_epoch, False))
        stack.extend(reversed(children))
    return records, None

def publish_inventory(reader, spec, physical, outputs, checkpoint):
    limits = validate(spec, physical)
    need(callable(checkpoint), 'checkpoint')
    pages, pending, total_nodes, total_bytes, count = [], [], 0, 0, 0
    def write(name, value):
        nonlocal total_bytes, count
        raw = encode(value)
        need(len(raw) <= 8 * 1024**2, 'page bytes')
        need(count + 1 <= limits['max_output_files'] and total_bytes + len(raw) <= limits['max_output_bytes'], 'output budget')
        ref = outputs.write(name, raw)
        total_bytes += len(raw); count += 1
        return ref
    def flush():
        if pending:
            number = len(pages)
            ref = write('l-inventory-%03d.json' % number, {'schema': 'cho51_l_inventory_page_v1', 'rows': pending[:]})
            pages.append(ref); pending.clear()
    diagnostics = []
    for row in spec['modules']:
        need(checkpoint() is True, 'checkpoint refused')
        raw = reader.read_small(row['path'], row['pin'])
        need(type(raw) is bytes and len(raw) == row['pin']['bytes'] and digest(raw) == row['pin']['sha256'], 'retained bytes')
        records, error = inventory(raw, row, limits, limits['max_nodes'] - total_nodes, checkpoint)
        if error is not None:
            diagnostics.append({'module': row['module'], 'source': row['pin'], 'diagnostic': error})
        for record in records:
            record.update(module=row['module'], source=row['pin'], phase=row['phase'])
            pending.append(record)
            if len(pending) == 256:
                flush()
        total_nodes += len(records)
    flush()
    index = {'schema': 'cho51_l_inventory_index_v1', 'status': 'INCOMPLETE_REFUSED',
             'pages': pages, 'diagnostics': diagnostics, 'nodes': total_nodes,
             'migration_ref': spec['migration_ref'], 'launch_authorized': False,
             'candidate_imports': 0, 'executed_input_code': 0,
             'unresolved': 'all effects, bindings, closure and decisions'}
    write('l-inventory-index.json', index)
    return index



