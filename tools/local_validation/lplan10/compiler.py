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

# The frontier kernel below is deliberately separate from the source observer.
# It accepts an asserted graph only and has no reader, parser, or writer hook.
FRONTIER_SCHEMA = 'cho51_supplied_frontier_v1'
FRONTIER_LIMITS = {'modules': 128, 'source_bytes': 16 * 1024**2,
                   'module_bytes': 2 * 1024**2, 'nodes': 200000,
                   'depth': 128, 'rows': 24000, 'edges': 10000,
                   'pages': 100, 'page_rows': 256, 'output_bytes': 16 * 1024**2,
                   'file_bytes': 8 * 1024**2, 'snapshots': 128,
                   'call_steps': 1000, 'history_bytes': 16 * 1024**2}

class FrontierCheckpointRefusal(Refusal):
    """A trusted live guard refused or failed; no successor is committed."""

def _frontier_guard(checkpoint):
    if not callable(checkpoint):
        raise FrontierCheckpointRefusal('live checkpoint required')
    try:
        allowed = checkpoint()
    except Exception as error:
        raise FrontierCheckpointRefusal('live checkpoint failed') from error
    if allowed is not True:
        raise FrontierCheckpointRefusal('live checkpoint refused')

def frontier_id(tag, *values):
    """Return a domain-separated identity for JSON-shaped supplied values."""
    return _frontier_id(None, tag, *values)

def _frontier_id(checkpoint, tag, *values):
    if checkpoint is not None:
        _frontier_guard(checkpoint)
    need(type(tag) is str and re.fullmatch(r'[a-z][a-z0-9_]{0,31}', tag) is not None,
         'frontier id tag')
    _frontier_payload(list(values), 0, checkpoint=checkpoint)
    result = digest(encode([tag] + list(values)))
    if checkpoint is not None:
        _frontier_guard(checkpoint)
    return result

def _frontier_payload(value, depth, budget=None, checkpoint=None):
    if checkpoint is not None:
        _frontier_guard(checkpoint)
    if budget is None:
        budget = [FRONTIER_LIMITS['file_bytes']]
    need(depth <= FRONTIER_LIMITS['depth'], 'payload depth')
    budget[0] -= 2
    need(budget[0] >= 0, 'capacity: payload bytes')
    if value is None or type(value) is bool:
        budget[0] -= 5
        need(budget[0] >= 0, 'capacity: payload bytes')
        return
    if type(value) is int:
        need(-(2**63) <= value < 2**63, 'payload integer')
        budget[0] -= len(str(value))
        need(budget[0] >= 0, 'capacity: payload bytes')
        return
    if type(value) is str:
        need(len(value) <= 65536, 'payload string')
        budget[0] -= len(json.dumps(value, ensure_ascii=True))
        need(budget[0] >= 0, 'capacity: payload bytes')
        return
    if type(value) is list:
        need(len(value) <= FRONTIER_LIMITS['rows'], 'payload list')
        for item in value:
            _frontier_payload(item, depth + 1, budget, checkpoint)
        return
    need(type(value) is dict and len(value) <= FRONTIER_LIMITS['rows'], 'payload type')
    for key, item in value.items():
        need(type(key) is str and 0 < len(key) <= 256 and key.isascii(), 'payload key')
        budget[0] -= len(json.dumps(key, ensure_ascii=True)) + 1
        need(budget[0] >= 0, 'capacity: payload bytes')
        _frontier_payload(item, depth + 1, budget, checkpoint)

def _frontier_name(value):
    need(type(value) is str and len(value) <= 256 and
         re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*', value, re.ASCII)
         is not None, 'frontier module')

def _frontier_token(value):
    need(type(value) is str and re.fullmatch(r'[A-Za-z0-9_./:-]{1,256}', value, re.ASCII)
         is not None, 'frontier token')

def _frontier_hash(value):
    need(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None, 'frontier hash')

def _frontier_binding(binding):
    closed(binding, ('algorithm', 'source', 'runtime', 'spec', 'roots', 'seeds', 'predecessor'))
    need(binding['algorithm'] == FRONTIER_SCHEMA, 'frontier algorithm')
    for key in ('source', 'runtime', 'spec', 'roots', 'seeds', 'predecessor'):
        _frontier_hash(binding[key])

def _frontier_graph(graph, checkpoint):
    _frontier_guard(checkpoint)
    _frontier_payload(graph, 0, checkpoint=checkpoint)
    closed(graph, ('modules', 'seeds', 'obligations'))
    for key in graph:
        need(type(graph[key]) is list and len(graph[key]) <= FRONTIER_LIMITS['rows'], 'graph list')
    need(len(graph['modules']) <= FRONTIER_LIMITS['modules'], 'module capacity')
    modules, names, edge_ids = {}, set(), set()
    source_bytes = nodes = edge_count = record_count = 0
    for module in graph['modules']:
        _frontier_guard(checkpoint)
        closed(module, ('name', 'origin', 'source_bytes', 'nodes', 'depth', 'records', 'edges'))
        name = module['name']; _frontier_name(name)
        need(name.casefold() not in names, 'module collision'); names.add(name.casefold())
        closed(module['origin'], ('identity', 'sha256'))
        _frontier_token(module['origin']['identity']); _frontier_hash(module['origin']['sha256'])
        for key, limit in (('source_bytes', FRONTIER_LIMITS['module_bytes']),
                           ('nodes', FRONTIER_LIMITS['nodes']), ('depth', FRONTIER_LIMITS['depth'])):
            need(type(module[key]) is int and 0 <= module[key] <= limit, 'module ' + key)
        source_bytes += module['source_bytes']; nodes += module['nodes']
        need(type(module['records']) is list and type(module['edges']) is list, 'module lists')
        need(len(module['records']) <= module['nodes'], 'record node count')
        record_count += len(module['records'])
        need(record_count <= FRONTIER_LIMITS['rows'], 'capacity: records')
        for index, record in enumerate(module['records']):
            _frontier_guard(checkpoint)
            closed(record, ('id', 'payload')); _frontier_payload(record['payload'], 0, checkpoint=checkpoint)
            need(record['id'] == _frontier_id(checkpoint, 'record', name, index, record['payload']), 'record id')
        for edge in module['edges']:
            _frontier_guard(checkpoint)
            closed(edge, ('id', 'target', 'site', 'epoch', 'conditional', 'kind'))
            _frontier_name(edge['target']); _frontier_token(edge['site']); _frontier_token(edge['kind'])
            need(edge['epoch'] in ('eager', 'deferred') and type(edge['epoch']) is str, 'edge epoch')
            need(type(edge['conditional']) is bool, 'edge conditional')
            expected = _frontier_id(checkpoint, 'edge', name, edge['target'], edge['site'], edge['epoch'],
                                   edge['conditional'], edge['kind'])
            need(edge['id'] == expected and expected not in edge_ids, 'edge id')
            edge_ids.add(expected); edge_count += 1
            need(edge_count <= FRONTIER_LIMITS['edges'], 'edge capacity')
        modules[name] = module
    need(source_bytes <= FRONTIER_LIMITS['source_bytes'] and nodes <= FRONTIER_LIMITS['nodes'],
         'source or node capacity')
    need(edge_count <= FRONTIER_LIMITS['edges'], 'edge capacity')
    seed_ids, seed_keys, seed_prefix_count = set(), set(), 0
    for seed in graph['seeds']:
        _frontier_guard(checkpoint)
        closed(seed, ('id', 'module', 'phase', 'prefixes'))
        _frontier_name(seed['module'])
        need(type(seed['phase']) is str and seed['phase'] in ('L2', 'L3', 'L4'), 'seed phase')
        parts = seed['module'].split('.')
        prefixes = ['.'.join(parts[:i]) for i in range(1, len(parts) + 1)]
        need(type(seed['prefixes']) is list and seed['prefixes'] == prefixes, 'seed prefixes')
        seed_prefix_count += len(prefixes)
        # Each prefix produces at least one fact and one seed link.
        need(2 * seed_prefix_count <= FRONTIER_LIMITS['rows'], 'capacity: seed prefixes')
        expected = _frontier_id(checkpoint, 'seed', seed['module'], seed['phase'], prefixes)
        key = (seed['module'], seed['phase'])
        need(seed['id'] == expected and expected not in seed_ids and key not in seed_keys, 'seed id')
        seed_ids.add(expected); seed_keys.add(key)
    debt_ids = set()
    for debt in graph['obligations']:
        _frontier_guard(checkpoint)
        closed(debt, ('id', 'kind', 'origin', 'payload'))
        _frontier_token(debt['kind']); _frontier_token(debt['origin'])
        _frontier_payload(debt['payload'], 0, checkpoint=checkpoint)
        # A hash or locator alone cannot stand in for retained debt content.
        # Opaque fields cannot establish semantic completeness of an assertion.
        references = {'id', 'digest', 'sha256', 'ref', 'reference', 'path', 'uri', 'bytes', 'size'}
        need(type(debt['payload']) is dict and
             any(key.casefold() not in references and value is not None
                 for key, value in debt['payload'].items()), 'obligation payload required')
        expected = _frontier_id(checkpoint, 'obligation', debt['kind'], debt['origin'], debt['payload'])
        need(debt['id'] == expected and expected not in debt_ids, 'obligation id')
        debt_ids.add(expected)
    need(2 * len(graph['modules']) + record_count + edge_count + len(graph['seeds']) +
         len(graph['obligations']) + 2 * seed_prefix_count <= FRONTIER_LIMITS['rows'],
         'capacity: initial graph rows')
    # A folded spelling must not introduce another identity through an edge or seed.
    spellings = {}
    names_to_check = []
    for module in graph['modules']:
        _frontier_guard(checkpoint)
        names_to_check.append(module['name'])
        for edge in module['edges']:
            _frontier_guard(checkpoint)
            names_to_check.append(edge['target'])
    for seed in graph['seeds']:
        for prefix in seed['prefixes']:
            _frontier_guard(checkpoint)
            names_to_check.append(prefix)
    for name in names_to_check:
        _frontier_guard(checkpoint)
        need(name.casefold() not in spellings or spellings[name.casefold()] == name, 'name collision')
        spellings[name.casefold()] = name
    return modules, edge_count

def _frontier_add_fact(frame, module, phase, requester, modules, checkpoint):
    _frontier_guard(checkpoint)
    ident = _frontier_id(checkpoint, 'fact', module, phase, requester)
    for fact in frame['facts']:
        _frontier_guard(checkpoint)
        if fact['id'] == ident:
            return ident
    frame['facts'].append({'id': ident, 'module': module, 'phase': phase, 'requester': requester})
    frame['work'].append({'fact': ident, 'cursor': 0, 'blocked': module not in modules})
    return ident

def _frontier_add_link(frame, kind, source, edge, target, checkpoint):
    _frontier_guard(checkpoint)
    ident = _frontier_id(checkpoint, 'link', kind, source, edge, target)
    for link in frame['links']:
        _frontier_guard(checkpoint)
        if link['id'] == ident:
            return
    frame['links'].append({'id': ident, 'kind': kind, 'source': source,
                           'edge': edge, 'target': target})

def _frontier_initial(graph, modules, checkpoint):
    frame = {'steps': 0, 'retained_before': 0, 'facts': [], 'links': [], 'work': []}
    for seed in graph['seeds']:
        _frontier_guard(checkpoint)
        for name in seed['prefixes']:
            _frontier_guard(checkpoint)
            target = _frontier_add_fact(frame, name, seed['phase'], seed['id'], modules, checkpoint)
            _frontier_add_link(frame, 'seed', seed['id'], None, target, checkpoint)
    return frame

def _frontier_transition(frame, modules, checkpoint):
    _frontier_guard(checkpoint)
    # Blocked entries retain their position and cannot prevent later work.
    position = None
    for i, item in enumerate(frame['work']):
        _frontier_guard(checkpoint)
        if not item['blocked']:
            position = i
            break
    if position is None:
        return False
    item = frame['work'][position]
    fact = None
    for current in frame['facts']:
        _frontier_guard(checkpoint)
        if current['id'] == item['fact']:
            fact = current
            break
    need(fact is not None, 'work fact join')
    edges = modules[fact['module']]['edges']
    if not edges:
        frame['work'].pop(position)
    else:
        edge = edges[item['cursor']]
        target = _frontier_add_fact(frame, edge['target'], fact['phase'], fact['requester'], modules, checkpoint)
        _frontier_add_link(frame, 'edge', fact['id'], edge['id'], target, checkpoint)
        item['cursor'] += 1
        if item['cursor'] == len(edges):
            frame['work'].pop(position)
    frame['steps'] += 1
    return True

def _frontier_snapshot(binding, graph, frames, predecessor):
    return {'schema': FRONTIER_SCHEMA, 'binding': binding, 'graph': graph, 'frames': frames,
            'sequence': len(frames) - 1, 'predecessor': predecessor,
            'status': 'INCOMPLETE_REFUSED', 'g2_complete': False,
            'launch_authorized': False, 'capabilities_accepted': False,
            'saturated': not frames[-1]['work']}

def _frontier_capacity(snapshot, graph_edges, checkpoint):
    _frontier_guard(checkpoint)
    _frontier_payload(snapshot, 0, checkpoint=checkpoint)
    graph = snapshot['graph']; frames = snapshot['frames']
    base = 2 * len(graph['modules']) + len(graph['seeds']) + len(graph['obligations'])
    for module in graph['modules']:
        _frontier_guard(checkpoint)
        base += len(module['records']) + len(module['edges'])
    # Each retained snapshot contains its graph and all frames through that
    # boundary. Count repeated historical payloads as well as the newest copy.
    count = len(frames)
    rows, edges = base * count, graph_edges * count
    for i, frame in enumerate(frames):
        _frontier_guard(checkpoint)
        rows += (count - i) * (len(frame['facts']) + len(frame['links']) + len(frame['work']) + 1)
        edges += (count - i) * len(frame['links'])
    need(rows <= FRONTIER_LIMITS['rows'], 'capacity: rows')
    need((rows + FRONTIER_LIMITS['page_rows'] - 1) // FRONTIER_LIMITS['page_rows']
         <= FRONTIER_LIMITS['pages'], 'capacity: pages')
    need(edges <= FRONTIER_LIMITS['edges'], 'capacity: edges')
    need(len(frames) <= FRONTIER_LIMITS['snapshots'], 'capacity: snapshots')
    _frontier_guard(checkpoint)
    size = len(encode(snapshot))
    _frontier_guard(checkpoint)
    need(size <= FRONTIER_LIMITS['file_bytes'] and size <= FRONTIER_LIMITS['output_bytes'],
         'capacity: snapshot bytes')
    need(frames[-1]['retained_before'] + size <= FRONTIER_LIMITS['history_bytes'],
         'capacity: history bytes')
    return size

def _frontier_copy(value, checkpoint):
    # JSON round-trip also prevents the returned checkpoint aliasing caller data.
    _frontier_guard(checkpoint)
    result = json.loads(encode(value).decode('ascii'))
    _frontier_guard(checkpoint)
    return result

def frontier_start(binding, graph, checkpoint):
    """Construct a bounded initial checkpoint from an asserted finite graph."""
    _frontier_guard(checkpoint)
    _frontier_binding(binding)
    modules, graph_edges = _frontier_graph(graph, checkpoint)
    need(binding['seeds'] == digest(encode(graph['seeds'])), 'ordered seeds digest')
    # Bound the input before making any copy of potentially large payloads.
    need(len(encode(graph)) <= FRONTIER_LIMITS['file_bytes'], 'capacity: graph bytes')
    snapshot = _frontier_snapshot(binding, graph, [_frontier_initial(graph, modules, checkpoint)], None)
    _frontier_capacity(snapshot, graph_edges, checkpoint)
    return _frontier_copy(snapshot, checkpoint)

def _frontier_verify(snapshot, expected_digest, expected_binding, checkpoint):
    _frontier_guard(checkpoint)
    closed(snapshot, ('schema', 'binding', 'graph', 'frames', 'status', 'g2_complete',
                      'launch_authorized', 'capabilities_accepted', 'saturated', 'sequence', 'predecessor'))
    _frontier_hash(expected_digest); _frontier_binding(expected_binding)
    need(snapshot['schema'] == FRONTIER_SCHEMA, 'snapshot schema')
    _frontier_binding(snapshot['binding'])
    need(snapshot['binding'] == expected_binding, 'binding drift')
    need(snapshot['status'] == 'INCOMPLETE_REFUSED' and snapshot['g2_complete'] is False and
         snapshot['launch_authorized'] is False and snapshot['capabilities_accepted'] is False and
         type(snapshot['saturated']) is bool, 'snapshot authority')
    modules, graph_edges = _frontier_graph(snapshot['graph'], checkpoint)
    need(snapshot['binding']['seeds'] == digest(encode(snapshot['graph']['seeds'])), 'ordered seeds digest')
    frames = snapshot['frames']
    need(type(frames) is list and 1 <= len(frames) <= FRONTIER_LIMITS['snapshots'], 'frame count')
    # Reject non-JSON values before encoding and enforce an input-size ceiling.
    _frontier_payload(snapshot, 0, checkpoint=checkpoint)
    need(len(encode(snapshot)) <= FRONTIER_LIMITS['file_bytes'], 'capacity: snapshot bytes')
    need(digest(encode(snapshot)) == expected_digest, 'predecessor digest')
    _frontier_guard(checkpoint)
    expected = _frontier_initial(snapshot['graph'], modules, checkpoint)
    retained = 0
    predecessor = None
    for index, supplied in enumerate(frames):
        _frontier_guard(checkpoint)
        closed(supplied, ('steps', 'retained_before', 'facts', 'links', 'work'))
        need(type(supplied['steps']) is int and type(supplied['retained_before']) is int,
             'frame counters')
        if index:
            difference = supplied['steps'] - expected['steps']
            need(1 <= difference <= FRONTIER_LIMITS['call_steps'], 'frame step count')
            expected['retained_before'] = retained
            for unused in range(difference):
                _frontier_guard(checkpoint)
                need(_frontier_transition(expected, modules, checkpoint), 'fabricated transition')
                intermediate = _frontier_snapshot(snapshot['binding'], snapshot['graph'],
                                                  frames[:index] + [expected], predecessor)
                _frontier_capacity(intermediate, graph_edges, checkpoint)
        expected['retained_before'] = retained
        # Python equality equates True and 1; canonical bytes preserve exact
        # JSON types in cursors, blocked flags and every nested field.
        need(encode(supplied) == encode(expected), 'frame replay mismatch')
        prefix = _frontier_snapshot(snapshot['binding'], snapshot['graph'], frames[:index + 1], predecessor)
        retained += _frontier_capacity(prefix, graph_edges, checkpoint)
        if index == len(frames) - 1:
            need(type(snapshot['sequence']) is int and snapshot['sequence'] == index and
                 snapshot['predecessor'] == predecessor, 'snapshot predecessor join')
        _frontier_guard(checkpoint)
        predecessor = digest(encode(prefix))
        _frontier_guard(checkpoint)
    need(snapshot['saturated'] == (not frames[-1]['work']), 'saturation mismatch')
    return modules, graph_edges, retained

def frontier_continue(snapshot, expected_digest, expected_binding, steps, checkpoints, checkpoint):
    """Replay-validate and transactionally advance an immutable checkpoint.

    checkpoints is a supplied boolean per requested transition. Any false entry
    refuses the entire call; it is not a callback or execution capability.
    """
    _frontier_guard(checkpoint)
    need(type(steps) is int and 1 <= steps <= FRONTIER_LIMITS['call_steps'], 'step limit')
    need(type(checkpoints) is list and len(checkpoints) == steps and
         all(type(value) is bool for value in checkpoints), 'checkpoint list')
    modules, graph_edges, retained = _frontier_verify(snapshot, expected_digest, expected_binding, checkpoint)
    if not all(checkpoints):
        return {'result': 'CHECKPOINT_REFUSED', 'reason': 'checkpoint', 'snapshot': _frontier_copy(snapshot, checkpoint)}
    frame = _frontier_copy(snapshot['frames'][-1], checkpoint)
    frame['retained_before'] = retained
    advanced = 0
    try:
        for unused in range(steps):
            _frontier_guard(checkpoint)
            if not _frontier_transition(frame, modules, checkpoint):
                break
            advanced += 1
            candidate = _frontier_snapshot(snapshot['binding'], snapshot['graph'], snapshot['frames'] + [frame], expected_digest)
            _frontier_capacity(candidate, graph_edges, checkpoint)
    except FrontierCheckpointRefusal:
        raise
    except Refusal as error:
        return {'result': 'CAPACITY_REFUSED', 'reason': str(error), 'snapshot': _frontier_copy(snapshot, checkpoint)}
    if not advanced:
        return {'result': 'NO_WORK', 'reason': 'blocked' if frame['work'] else 'saturated',
                'snapshot': _frontier_copy(snapshot, checkpoint)}
    candidate = _frontier_snapshot(snapshot['binding'], snapshot['graph'], snapshot['frames'] + [frame], expected_digest)
    return {'result': 'ADVANCED', 'reason': None, 'snapshot': _frontier_copy(candidate, checkpoint)}


# Supplied-only transport. This does not dispatch P or read paths in evidence.
LOSSLESS_SCHEMA = 'cho51_lossless_state_transport_v1'
LOSSLESS_RESULT = 'cho51_lossless_verification_result_v1'
LOSSLESS_CHUNK = 1024 * 1024

class LosslessCheckpointRefusal(Refusal):
    """The trusted live guard failed; no result or bundle is committed."""

def _ls_guard(checkpoint):
    try:
        _frontier_guard(checkpoint)
    except FrontierCheckpointRefusal as error:
        raise LosslessCheckpointRefusal('live checkpoint') from error

def _ls_hash(raw, checkpoint):
    need(type(raw) is bytes, 'bytes required')
    h = hashlib.sha256()
    for start in range(0, len(raw), 65536):
        _ls_guard(checkpoint)
        h.update(raw[start:start + 65536])
    _ls_guard(checkpoint)
    return h.hexdigest()

def _ls_blocks(value, checkpoint, limit):
    """Canonical JSON tokens; string-escaping library calls see <=4096 chars."""
    total = 0
    def emit(text):
        nonlocal total
        _ls_guard(checkpoint); block = text.encode('ascii')
        total += len(block); need(total <= limit, 'capacity: canonical bytes')
        return block
    def string(text):
        need(type(text) is str and len(text) <= 65536, 'JSON string capacity')
        yield emit('"')
        for start in range(0, len(text), 4096):
            _ls_guard(checkpoint)
            # ensure_ascii escapes each Unicode code point independently; the
            # surrounding quotes are emitted once, including for empty strings.
            yield emit(json.dumps(text[start:start+4096], ensure_ascii=True)[1:-1])
        yield emit('"')
    def visit(item, depth):
        _ls_guard(checkpoint); need(depth <= 128, 'JSON depth')
        if item is None: yield emit('null')
        elif type(item) is bool: yield emit('true' if item else 'false')
        elif type(item) is int:
            _ls_int(item, -(2**63), 2**63-1, 'JSON integer'); yield emit(str(item))
        elif type(item) is str: yield from string(item)
        elif type(item) is list:
            need(len(item) <= 24000, 'JSON array capacity'); yield emit('[')
            for i, child in enumerate(item):
                if i: yield emit(',')
                yield from visit(child, depth+1)
            yield emit(']')
        elif type(item) is dict:
            need(len(item) <= 24000 and all(type(k) is str and len(k) <= 65536 for k in item), 'JSON object capacity')
            _ls_guard(checkpoint); keys = sorted(item); _ls_guard(checkpoint)
            yield emit('{')
            for i, key in enumerate(keys):
                if i: yield emit(',')
                yield from string(key); yield emit(':'); yield from visit(item[key], depth+1)
            yield emit('}')
        else: raise Refusal('JSON value type')
    yield from visit(value, 0)
    _ls_guard(checkpoint)

def _ls_encode(value, checkpoint, limit=None):
    result = bytearray()
    for block in _ls_blocks(value, checkpoint, FRONTIER_LIMITS['file_bytes'] if limit is None else limit):
        result.extend(block)
    _ls_guard(checkpoint); raw = bytes(result); _ls_guard(checkpoint)
    return raw

def _ls_hash_json(value, checkpoint):
    h = hashlib.sha256()
    for block in _ls_blocks(value, checkpoint, FRONTIER_LIMITS['output_bytes']): h.update(block)
    _ls_guard(checkpoint); return h.hexdigest()

def _ls_asset_id(kind, size, sha, checkpoint):
    return _ls_hash_json(['asset',kind,size,sha],checkpoint)

def _ls_int(value, low, high, message):
    need(type(value) is int and low <= value <= high, message)

def _ls_pin(value):
    closed(value, ('bytes', 'sha256'))
    _ls_int(value['bytes'], 1, FRONTIER_LIMITS['file_bytes'], 'pin bytes')
    _frontier_hash(value['sha256'])

def _ls_allocation(value):
    closed(value, ('resolver_bytes', 'resolver_pages', 'p_bytes', 'p_files'))
    for key in value:
        _ls_int(value[key], 0, 2**63 - 1, 'allocation integer')
    need(value['p_bytes'] >= value['resolver_bytes'] and value['p_files'] >= value['resolver_pages'],
         'allocation overlap')

def _ls_json(raw, checkpoint, canonical=False):
    """Parse bounded JSON as data, with guarded byte and token traversal."""
    need(type(raw) is bytes and 0 < len(raw) <= FRONTIER_LIMITS['file_bytes'], 'JSON size')
    n = len(raw); pos = 0; traversed = 0
    def tick():
        nonlocal traversed
        traversed += 1
        if traversed >= 65536:
            _ls_guard(checkpoint); traversed = 0
    def take():
        nonlocal pos
        need(pos < n, 'JSON truncated')
        b = raw[pos]; pos += 1; tick(); return b
    def ws():
        while pos < n and raw[pos] in (9, 10, 13, 32): take()
    def string():
        need(take() == 34, 'JSON string')
        pieces = []; segment = bytearray(); characters = 0
        def append(text):
            nonlocal characters
            characters += len(text); need(characters <= 65536 and len(pieces) < 65536, 'JSON string capacity')
            pieces.append(text)
        def flush():
            if segment:
                _ls_guard(checkpoint)
                try: append(bytes(segment).decode('utf-8', 'strict'))
                except UnicodeDecodeError as error: raise Refusal('JSON UTF-8') from error
                segment.clear()
        while True:
            b = take()
            if b == 34: break
            need(b >= 32, 'JSON control character')
            if b != 92:
                segment.append(b)
                if len(segment) >= 65532 and (pos >= n or not 128 <= raw[pos] <= 191): flush()
            else:
                flush(); escaped = take()
                simple = {34:'"', 92:'\\', 47:'/', 98:'\b', 102:'\f', 110:'\n', 114:'\r', 116:'\t'}
                if escaped in simple: append(simple[escaped])
                else:
                    need(escaped == 117, 'JSON escape')
                    def hex4():
                        digits = bytes(take() for unused in range(4))
                        need(all(c in b'0123456789abcdefABCDEF' for c in digits), 'JSON unicode')
                        return int(digits, 16)
                    code = hex4()
                    if 0xd800 <= code <= 0xdbff and pos + 6 <= n and raw[pos:pos+2] == b'\\u':
                        digits = raw[pos+2:pos+6]
                        if all(c in b'0123456789abcdefABCDEF' for c in digits) and 0xdc00 <= int(digits,16) <= 0xdfff:
                            take(); take(); lower = hex4()
                            code = 0x10000 + ((code - 0xd800) << 10) + lower - 0xdc00
                    append(chr(code))
            need(len(segment) <= 65536 and len(pieces) <= 65536, 'JSON string capacity')
        flush(); _ls_guard(checkpoint); result = ''.join(pieces); _ls_guard(checkpoint)
        need(len(result) <= 65536, 'JSON string capacity')
        return result
    def value(depth):
        _ls_guard(checkpoint); need(depth <= 128, 'JSON depth'); ws()
        need(pos < n, 'JSON value'); b = raw[pos]
        if b == 34: return string()
        if b == 123:
            take(); result = {}; ws()
            if pos < n and raw[pos] == 125: take(); return result
            while True:
                ws(); need(pos < n and raw[pos] == 34, 'JSON object key')
                key = string(); need(key not in result, 'duplicate JSON key')
                ws(); need(take() == 58, 'JSON colon'); result[key] = value(depth + 1)
                need(len(result) <= 24000, 'JSON object capacity'); ws(); sep = take()
                if sep == 125: return result
                need(sep == 44, 'JSON object separator')
        if b == 91:
            take(); result = []; ws()
            if pos < n and raw[pos] == 93: take(); return result
            while True:
                result.append(value(depth + 1)); need(len(result) <= 24000, 'JSON array capacity')
                ws(); sep = take()
                if sep == 93: return result
                need(sep == 44, 'JSON array separator')
        for literal, result in ((b'true', True), (b'false', False), (b'null', None)):
            if raw[pos:pos + len(literal)] == literal:
                for unused in literal: take()
                return result
        start = pos
        if b == 45: take()
        need(pos < n and 48 <= raw[pos] <= 57, 'JSON number')
        if raw[pos] == 48: take(); need(pos >= n or not 48 <= raw[pos] <= 57, 'JSON leading zero')
        else:
            while pos < n and 48 <= raw[pos] <= 57:
                take(); need(pos - start <= 20, 'JSON integer capacity')
        result = int(raw[start:pos]); _ls_int(result, -(2**63), 2**63 - 1, 'JSON integer')
        return result
    result = value(0); ws(); need(pos == n, 'JSON trailing material'); _ls_guard(checkpoint)
    if canonical:
        need(_ls_encode(result, checkpoint) == raw, 'JSON canonical')
    return result

def _ls_text(value, limit=65536):
    need(type(value) is str and len(value) <= limit, 'historical text')

def _ls_source_pin(value):
    closed(value, ('bytes','sha256'))
    _ls_int(value['bytes'], 0, HARD['max_module_bytes'], 'historical source bytes')
    _frontier_hash(value['sha256'])

def _ls_descriptor(value):
    closed(value, ('schema','path','native_identity','file_type','reparse_point','link_count','bytes','sha256'))
    need(value['schema'] == 'cho51_lv_file_descriptor_v1' and value['file_type'] == 'regular' and
         value['reparse_point'] is False and type(value['link_count']) is int and value['link_count'] == 1 and
         _resolver_path(value['path']), 'historical descriptor')
    _ls_int(value['bytes'], 0, 2**63-1, 'historical descriptor bytes'); _frontier_hash(value['sha256'])
    ident = value['native_identity']; closed(ident, ('schema','volume_serial','file_id','volume_kind','filesystem'))
    need(ident['schema'] == 'cho51_lv_native_identity_v1' and ident['volume_kind'] == 'local_fixed' and
         ident['filesystem'] in ('NTFS','ReFS'), 'historical native identity')
    for key, width in (('volume_serial',16),('file_id',32)):
        need(type(ident[key]) is str and re.fullmatch('[0-9a-f]{%d}' % width, ident[key]) is not None and
             ident[key] != '0'*width, 'historical native identity')

def _ls_origin(origin, module, checkpoint, depth=0):
    _ls_guard(checkpoint); need(depth <= 128 and type(origin) is dict, 'historical origin depth')
    kind = origin.get('kind'); keys = ['kind','module']
    if kind in ('source','package','extension','extension_package'): keys += ['path','pin','physical_descriptor']
    elif kind == 'namespace_unresolved': keys += ['paths']
    elif kind == 'missing_origin':
        # The final fallback can omit paths, but no other optional keys exist.
        if 'paths' in origin: keys += ['paths']
    elif kind == 'parent_unresolved': keys += ['parent']
    else: need(kind in ('builtin','frozen'), 'historical origin kind')
    closed(origin, keys); _frontier_name(origin['module'])
    need(origin['module'] == module, 'historical origin module')
    if 'pin' in origin:
        _ls_descriptor(origin['physical_descriptor'])
        if kind in ('source','package'):
            _ls_source_pin(origin['pin'])
            _ls_int(origin['pin']['bytes'],0,RESOLVER_HARD['max_module_bytes'],'historical source module bytes')
        else:
            # This is a descriptor of an image, not transported image bytes.
            closed(origin['pin'], ('bytes','sha256'))
            _ls_int(origin['pin']['bytes'],0,2**63-1,'historical native metadata bytes')
            _frontier_hash(origin['pin']['sha256'])
        desc = origin['physical_descriptor']
        need(origin['path'] == desc['path'] and origin['pin'] == {'bytes':desc['bytes'],'sha256':desc['sha256']}, 'historical origin pin')
    if 'paths' in origin:
        need(type(origin['paths']) is list and len(origin['paths']) <= 128, 'historical origin paths')
        for path in origin['paths']: _ls_guard(checkpoint); need(_resolver_path(path), 'historical origin path')
        need(bool(origin['paths']) == (kind == 'namespace_unresolved'), 'historical namespace paths')
    if 'parent' in origin:
        parent = origin['parent']; need(type(parent) is dict, 'historical parent')
        _frontier_name(parent.get('module'))
        need(module.startswith(parent['module']+'.') and parent.get('kind') != 'package', 'historical parent join')
        _ls_origin(parent, parent['module'], checkpoint, depth+1)

def _ls_node(row, family, checkpoint):
    _ls_guard(checkpoint); need(type(row) is dict, 'historical node')
    base = ['id','parent','path','scope','kind','span_utf8','raw_span_sha256','epoch','module','source']
    kind = row.get('kind'); need(type(kind) is str and re.fullmatch('[A-Za-z_][A-Za-z_0-9]{0,127}',kind) is not None,
                               'historical node kind')
    if family == 'inventory':
        keys = base + ['scope_parent','shape_sha256','context','analysis','phase']
    else:
        keys = base + ['scope_kind','conditional','resolution','capability']
        if kind in ('Global','Nonlocal'): keys += ['binding_kind','names']
        if kind in ('FunctionDef','AsyncFunctionDef','ClassDef','arg','Name'): keys += ['binding_kind','name']
        if kind == 'alias': keys += ['binding_kind','name','alias']
        if kind == 'Name' and row.get('binding_kind') == 'Load': keys += ['binding_candidates']
        if kind == 'Call': keys += ['lexical_targets','import_candidate','runtime_binding_proven']
        # These are the only conditional fields emitted by the observer.
        keys += [key for key in ('effect','refusal','possible_dynamic_effect') if key in row]
        if kind == 'Name' and 'import_candidate' in row: keys += ['import_candidate']
    closed(row, keys); _frontier_name(row['module']); _ls_source_pin(row['source'])
    path = row['path']; need(type(path) is str and len(path) <= 65536 and
        path.count('/') <= 128 and re.fullmatch(r'\$(?:/[A-Za-z_][A-Za-z_0-9]*(?::[0-9]+)?)*',path) is not None, 'historical node path')
    _frontier_hash(row['id']); need(row['id'] == _ls_hash_json([row['module'],row['source']['sha256'],path],checkpoint), 'historical node id')
    need((path == '$') == (row['parent'] is None) and (path != '$' or kind == 'Module'), 'historical root')
    if row['parent'] is not None: _frontier_hash(row['parent'])
    if row['scope'] != '$': _frontier_hash(row['scope'])
    need(family == 'inventory' or row['scope'] != '$', 'historical scope sentinel')
    need(row['epoch'] in (('eager','deferred','unknown') if family == 'inventory' else
                         ('eager','deferred','future_annotation_unknown')), 'historical epoch')
    coords = row['span_utf8']
    if coords is None: need(row['raw_span_sha256'] is None, 'historical span hash')
    else:
        need(type(coords) is list and len(coords) == 4, 'historical span')
        for i, value in enumerate(coords): _ls_int(value, 1 if i in (0,2) else 0, 2**63-1, 'historical span integer')
        need(coords[0] <= coords[2] and (coords[0] != coords[2] or coords[1] <= coords[3]), 'historical span order')
        _frontier_hash(row['raw_span_sha256'])
    if family == 'inventory':
        _frontier_hash(row['shape_sha256']); need(row['analysis'] == 'unresolved' and row['phase'] in ('L2','L3','L4'), 'historical inventory flags')
        need(row['context'] in ('Load','Store','Del','unknown'), 'historical context')
        if row['scope_parent'] not in (None,'$'): _frontier_hash(row['scope_parent'])
    else:
        effects = {}
        for names, effect in (
            ('Call','call_callback_dynamic'),('Attribute','attribute_dispatch'),('Subscript','subscript_protocol'),
            ('BinOp UnaryOp','operator_protocol'),('Compare','comparison_protocol'),('BoolOp If IfExp','truth_protocol'),
            ('While','truth_iteration'),('For comprehension','iteration_protocol'),('AsyncFor','async_iteration_protocol'),
            ('With','context_protocol'),('AsyncWith','async_context_protocol'),('Try TryStar Raise','exception_protocol'),
            ('ExceptHandler','exception_matching'),('Assert','truth_exception'),('Await','await_protocol'),
            ('Yield','generator_protocol'),('YieldFrom','iteration_protocol'),('Delete','delete_write'),
            ('Assign AnnAssign NamedExpr','binding_write'),('AugAssign','operator_write'),('Import ImportFrom','import'),
            ('Match','pattern_protocol'),('FormattedValue JoinedStr','format_protocol'),
            ('ListComp','comprehension_protocol'),('GeneratorExp','generator_protocol'),('DictComp','hash_iteration_protocol'),
            ('SetComp','hash_iteration_protocol'),('FunctionDef AsyncFunctionDef Lambda','definition_creation'),
            ('ClassDef','class_creation'),('Dict Set','hash_protocol'),('Starred','unpack_iteration_protocol'),
            ('keyword','keyword_unpack_protocol'),('MatchValue','pattern_comparison_protocol'),
            ('MatchSequence','pattern_sequence_protocol'),('MatchMapping','pattern_mapping_protocol'),
            ('MatchClass','pattern_attribute_protocol')):
            for name in names.split(): effects[name] = effect
        need(('effect' in row) == (kind in effects) and row.get('effect') == effects.get(kind), 'historical effect schema')
        if 'refusal' in row:
            need(row['refusal'] in ('unsupported_ast_construct','unsupported_annotation_scope','comprehension_namedexpr_unmodeled',
                 'nonlocal_target_unknown','alias_depth_limit','alias_cycle','multiple_bindings','decorated_definition_unknown',
                 'conditional_or_deleted_binding','late_binding','deferred_external_binding','assignment_value_unknown',
                 'unbound_or_builtin_unknown','definition_header_not_bound'), 'historical refusal')
        need('possible_dynamic_effect' not in row or kind == 'Call', 'historical dynamic effect kind')
        need('import_candidate' not in row or kind == 'Call' or (kind == 'Name' and row.get('binding_kind') == 'Load'),
             'historical import candidate kind')
        need(row['scope_kind'] in ('module','function','class','comprehension') and type(row['conditional']) is bool and
             row['capability'] == 'pending' and row['resolution'] in ('unresolved','lexical_candidate'), 'historical resolver flags')
        if 'binding_kind' in row:
            expected = {'Global':'global','Nonlocal':'nonlocal','FunctionDef':'definition','AsyncFunctionDef':'definition',
                        'ClassDef':'definition','arg':'parameter','alias':'import_alias'}
            need(row['binding_kind'] in (('Load','Store','Del') if kind == 'Name' else (expected[kind],)), 'historical binding kind')
        for key in ('name','alias','import_candidate','possible_dynamic_effect','effect','refusal'):
            if key in row:
                need(row[key] is not None or key in ('alias','import_candidate','possible_dynamic_effect'), 'historical node null')
                if row[key] is not None: _ls_text(row[key])
        if 'names' in row:
            need(type(row['names']) is list and len(row['names']) <= 24000, 'historical declaration')
            for value in row['names']: _ls_guard(checkpoint); _ls_text(value)
        for key in ('binding_candidates','lexical_targets'):
            if key in row:
                need(type(row[key]) is list and len(row[key]) <= 1, 'historical target count')
                for value in row[key]: _frontier_hash(value)
        if kind == 'Name' and row['binding_kind'] == 'Load':
            need(bool(row['binding_candidates']) == (row['resolution'] == 'lexical_candidate'), 'historical binding resolution')
        else: need(row['resolution'] == 'unresolved', 'historical resolution')
        if kind == 'Call': need(row['runtime_binding_proven'] is False, 'historical runtime binding')

def _ls_node_joins(nodes, family, checkpoint):
    identities = {}; paths = {}; modules = {}
    for row in nodes:
        _ls_node(row, family, checkpoint); ident = row['id']
        # Inventory ordinal uses can repeat exact rows. A differing row under
        # the same identity, or a duplicate resolver observation, is invalid.
        need(ident not in identities or (family == 'inventory' and identities[ident] == row), 'historical node duplicate')
        identities[ident] = row; key = (row['module'],row['path'])
        need(key not in paths or paths[key] == ident, 'historical path identity'); paths[key] = ident
        source = modules.setdefault(row['module'],row['source']); need(source == row['source'], 'historical source join')
    need(len(modules) <= (HARD['max_modules'] if family == 'inventory' else RESOLVER_HARD['max_modules']), 'historical module limit')
    need(len({m.casefold() for m in modules}) == len(modules), 'historical module case collision')
    for row in nodes:
        _ls_guard(checkpoint)
        root = paths.get((row['module'],'$')); need(root is not None, 'historical root join')
        if row['parent'] is not None:
            parent = identities.get(row['parent']); need(parent is not None and parent['module'] == row['module'] and
                row['path'].rsplit('/',1)[0] == parent['path'], 'historical parent join')
        scope = root if row['scope'] == '$' else row['scope']
        need(scope in identities and identities[scope]['module'] == row['module'], 'historical scope join')
        owner = identities[scope]
        scope_kinds = {'Module':'module','FunctionDef':'function','AsyncFunctionDef':'function','Lambda':'function',
                       'ClassDef':'class','ListComp':'comprehension','SetComp':'comprehension',
                       'DictComp':'comprehension','GeneratorExp':'comprehension'}
        need(owner['kind'] in scope_kinds and (scope == root or row['path'].startswith(owner['path']+'/')), 'historical scope owner')
        if family == 'inventory':
            ancestor = row['scope_parent']
            if ancestor not in (None,'$'): need(ancestor in identities and identities[ancestor]['module'] == row['module'], 'historical scope parent')
            need(ancestor == (None if row['scope'] == '$' else owner['scope']), 'historical scope ancestry')
        else:
            need(row['scope_kind'] == scope_kinds[owner['kind']] and row['source']['bytes'] <= RESOLVER_HARD['max_module_bytes'], 'historical scope kind')
            for key in ('binding_candidates','lexical_targets'):
                for target in row.get(key,[]):
                    need(target in identities and identities[target]['module'] == row['module'] and
                         'binding_kind' in identities[target], 'historical binding target')
                    if key == 'lexical_targets': need(identities[target]['binding_kind'] == 'definition', 'historical lexical target')
    return identities, modules

def _ls_resolver_rows(rows, index, checkpoint):
    front = []; queue = []; origins = []; edges = []; nodes = []; stage = 0
    for row in rows:
        _ls_guard(checkpoint); need(type(row) is dict, 'historical resolver row'); kind = row.get('kind')
        rank = 1 if kind == 'edge' else 2 if kind == 'frontier' else 3 if kind == 'queued' else 0
        need(rank >= stage, 'historical row order'); stage = rank
        if kind == 'origin':
            closed(row, ('kind','module','phase','origin','via','capability')); _frontier_name(row['module'])
            need(row['phase'] in ('L2','L3','L4') and row['capability'] == 'pending', 'historical origin flags')
            if row['via'] is not None: _frontier_hash(row['via'])
            _ls_origin(row['origin'],row['module'],checkpoint); origins.append(row)
        elif kind == 'edge':
            closed(row, ('kind','from','to','site','phase','epoch','conditional'))
            _frontier_name(row['from']); _frontier_name(row['to']); _frontier_hash(row['site'])
            need(row['phase'] in ('L2','L3','L4') and row['epoch'] in ('eager','deferred') and type(row['conditional']) is bool, 'historical edge')
            edges.append(row)
        elif kind == 'queued':
            closed(row, ('kind','module','phase','via')); _frontier_name(row['module'])
            need(row['phase'] in ('L2','L3','L4'), 'historical queued phase')
            if row['via'] is not None: _frontier_hash(row['via'])
            queue.append({k:v for k,v in row.items() if k != 'kind'})
        elif kind == 'frontier':
            reason = row.get('reason'); keys = ['kind','reason']
            if reason == 'capacity': keys += ['limit']
            else:
                keys += ['module']
                if reason == 'module_case_collision': keys += ['other']
                elif reason == 'parse_or_analysis_refusal': keys += ['detail']
                elif reason == 'multi_phase_join_unresolved': keys += ['contexts']
                elif reason in ('star_export_unresolved','attribute_or_submodule_unresolved'): keys += ['site','base','member']
                elif reason == 'dynamic_call_unresolved': keys += ['site','candidate']
                elif reason in ('unsupported_ast_construct','unsupported_annotation_scope','comprehension_namedexpr_unmodeled',
                                'relative_import_beyond_root','empty_import_target','invalid_import_target','deferred_or_conditional_import'): keys += ['site']
                else: need(reason in ('extension','extension_package','namespace_unresolved','missing_origin','parent_unresolved'), 'historical frontier reason')
            closed(row, keys)
            if 'module' in row: _frontier_name(row['module'])
            if 'site' in row: _frontier_hash(row['site'])
            if 'other' in row:
                _frontier_name(row['other']); need(row['module'] != row['other'] and row['module'].casefold() == row['other'].casefold(), 'historical case collision')
            if 'detail' in row: need(row['detail'] in ('SyntaxError','UnicodeDecodeError','UnicodeError','ValueError','Refusal','RecursionError'), 'historical parse detail')
            if 'base' in row: _frontier_name(row['base']); _ls_text(row['member'])
            if 'candidate' in row and row['candidate'] is not None: _ls_text(row['candidate'],512)
            if 'limit' in row:
                need(row['limit'] in ('max_modules','source_bytes','max_nodes','rows_or_edges','output_pages_or_bytes','AST node limit','AST depth limit','alias_depth_limit'), 'historical capacity limit')
            if 'contexts' in row:
                need(type(row['contexts']) is list and 2 <= len(row['contexts']) <= 24000, 'historical contexts')
                pairs = []
                for context in row['contexts']:
                    _ls_guard(checkpoint); closed(context, ('phase','via')); need(context['phase'] in ('L2','L3','L4'), 'historical context phase')
                    if context['via'] is not None: _frontier_hash(context['via'])
                    pairs.append((context['phase'],context['via'] or ''))
                need(pairs == sorted(set(pairs)) and len({p for p,v in pairs}) > 1, 'historical multi phase')
            front.append({k:v for k,v in row.items() if k != 'kind'})
        else: nodes.append(row)
    identities, sources = _ls_node_joins(nodes,'resolver',checkpoint)
    by_module = {}
    for row in origins:
        _ls_guard(checkpoint); need(row['module'] not in by_module and row['module'].casefold() not in {m.casefold() for m in by_module}, 'historical origin duplicate')
        by_module[row['module']] = row
    need(len(origins) <= RESOLVER_HARD['max_modules'], 'historical origins limit')
    for module, source in sources.items():
        need(module in by_module and by_module[module]['origin'].get('kind') in ('source','package') and
             by_module[module]['origin']['pin'] == source, 'historical node origin join')
    for row in origins:
        if row['via'] is not None: need(row['via'] in identities and identities[row['via']]['kind'] in ('Import','ImportFrom'), 'historical via join')
    for edge in edges:
        _ls_guard(checkpoint); site = identities.get(edge['site'])
        need(edge['from'] in by_module and site is not None and site['module'] == edge['from'] and
             site['kind'] in ('Import','ImportFrom') and edge['phase'] == by_module[edge['from']]['phase'] and
             edge['epoch'] == site['epoch'] and edge['conditional'] == site['conditional'], 'historical edge join')
    for row in front + queue:
        _ls_guard(checkpoint)
        if 'site' in row: need(row['site'] in identities and identities[row['site']]['module'] == row['module'], 'historical frontier site join')
        if row.get('via') is not None: need(row['via'] in identities and identities[row['via']]['kind'] in ('Import','ImportFrom'), 'historical queued via join')
    need(len({(q['module'],q['phase'],q['via']) for q in queue}) == len(queue), 'historical queue duplicate')
    caps = [row['limit'] for row in front if row['reason'] == 'capacity']
    need(caps == ([] if index['cap_refusal'] is None else [index['cap_refusal']]) and
         index['graph_fixed_point'] == (not front and not queue), 'historical fixed point')
    need(index['components'] == _components(by_module,edges,lambda: (_ls_guard(checkpoint) or True)), 'historical components')
    need(index['published_rows'] == len(rows) <= RESOLVER_HARD['max_rows'] and index['modules'] == len(origins) and
         index['nodes'] == len(nodes) <= RESOLVER_HARD['max_nodes'] and index['module_rows'] == len(origins)+len(nodes) and
         index['edges'] == len(edges) <= RESOLVER_HARD['max_edges'] and index['import_frontier_count'] == len(front) and
         index['queue_count'] == len(queue) and index['frontier_sha256'] == _ls_hash_json(front,checkpoint) and
         index['queue_sha256'] == _ls_hash_json(queue,checkpoint), 'resolver row counts')
    need(index['binding_count'] == sum('binding_kind' in r for r in nodes) and index['effect_count'] == sum('effect' in r for r in nodes) and
         index['binding_frontier_count'] == sum(r.get('binding_kind') == 'Load' and r['resolution'] == 'unresolved' for r in nodes) and
         index['effect_frontier_count'] == index['effect_count'], 'resolver embedded counts')
    ordered = [by_module[module]['origin'] for module in sorted(by_module)]
    need(index['source_bytes'] == sum(o['pin']['bytes'] for o in ordered if o['kind'] in ('source','package')) <= RESOLVER_HARD['max_source_bytes'] and
         index['source_pins_sha256'] == _ls_hash_json(ordered,checkpoint), 'resolver source counts')

def _ls_evidence(expected, raw_families, checkpoint):
    need(type(expected) is list and type(raw_families) is list and len(expected) <= 2, 'evidence families')
    need(len(expected) == len(raw_families), 'evidence membership')
    previous = -1
    for exp, family in zip(expected, raw_families):
        _ls_guard(checkpoint)
        closed(exp, ('family', 'index', 'pages')); closed(family, ('family', 'index', 'pages'))
        name = exp['family']; need(name in ('resolver', 'inventory') and family['family'] == name, 'evidence family')
        ordinal = ('resolver', 'inventory').index(name); need(ordinal > previous, 'evidence family order'); previous = ordinal
        _ls_pin(exp['index']); need(type(exp['pages']) is list and type(family['pages']) is list and
                                  len(exp['pages']) == len(family['pages']) <= 100, 'evidence pages')
        need(type(family['index']) is bytes and len(family['index']) == exp['index']['bytes'] and
             _ls_hash(family['index'], checkpoint) == exp['index']['sha256'], 'evidence index pin')
        index = _ls_json(family['index'], checkpoint)
        if name == 'inventory':
            closed(index, ('schema','status','pages','diagnostics','nodes','migration_ref','launch_authorized',
                           'candidate_imports','executed_input_code','unresolved'))
            need(index['schema'] == 'cho51_l_inventory_index_v1' and index['launch_authorized'] is False and
                 type(index['candidate_imports']) is int and index['candidate_imports'] == 0 and
                 type(index['executed_input_code']) is int and index['executed_input_code'] == 0 and
                 type(index['diagnostics']) is list, 'inventory index')
        else:
            closed(index, ('schema','status','g2_complete','launch_authorized','graph_fixed_point','modules',
                           'nodes','module_rows','published_rows','edges','source_bytes','binding_count','effect_count',
                           'binding_frontier_count','effect_frontier_count','source_pins_sha256','import_frontier_count',
                           'frontier_sha256','frontier_paged','queue_paged','queue_count','queue_sha256','cap_refusal',
                           'components','component_order_is_execution_grant','spec_sha256','pages'))
            need(index['schema'] == 'cho51_l_resolver_index_v1' and index['g2_complete'] is False and
                 index['launch_authorized'] is False and index['frontier_paged'] is True and
                 index['queue_paged'] is True and index['component_order_is_execution_grant'] is False and
                 type(index['graph_fixed_point']) is bool and type(index['components']) is list, 'resolver index')
            for key in ('source_pins_sha256','frontier_sha256','queue_sha256','spec_sha256'): _frontier_hash(index[key])
        need(index['status'] == 'INCOMPLETE_REFUSED' and type(index['pages']) is list and
             len(index['pages']) == len(exp['pages']), 'index page count')
        rows = []; paths = set(); identities = set()
        for i, (pin_value, data, descriptor) in enumerate(zip(exp['pages'], family['pages'], index['pages'])):
            _ls_guard(checkpoint); _ls_pin(pin_value)
            need(type(data) is bytes and len(data) == pin_value['bytes'] and
                 _ls_hash(data, checkpoint) == pin_value['sha256'], 'evidence page pin')
            closed(descriptor, ('schema','path','native_identity','file_type','reparse_point','link_count','bytes','sha256'))
            ident = descriptor['native_identity']; closed(ident, ('schema','volume_serial','file_id','volume_kind','filesystem'))
            need(descriptor['schema'] == 'cho51_lv_file_descriptor_v1' and descriptor['file_type'] == 'regular' and
                 descriptor['reparse_point'] is False and type(descriptor['link_count']) is int and descriptor['link_count'] == 1 and
                 descriptor['bytes'] == pin_value['bytes'] and type(descriptor['bytes']) is int and
                 descriptor['sha256'] == pin_value['sha256'], 'historical descriptor')
            need(ident['schema'] == 'cho51_lv_native_identity_v1' and ident['volume_kind'] == 'local_fixed' and
                 ident['filesystem'] in ('NTFS','ReFS') and type(ident['volume_serial']) is str and
                 re.fullmatch('[0-9a-f]{16}', ident['volume_serial']) is not None and ident['volume_serial'] != '0'*16 and
                 type(ident['file_id']) is str and re.fullmatch('[0-9a-f]{32}', ident['file_id']) is not None and
                 ident['file_id'] != '0'*32, 'historical identity')
            native_key = (ident['volume_serial'], ident['file_id'])
            need(native_key not in identities, 'historical native alias'); identities.add(native_key)
            path = descriptor['path']
            need(type(path) is str and path.isascii() and len(path) <= 4096 and
                 re.fullmatch(r'[A-Z]:/[^\\:*?"<>|]+', path) is not None, 'historical path')
            segments = path[3:].split('/'); need(len(segments) <= 128, 'historical path depth')
            for segment in segments:
                _ls_guard(checkpoint)
                stem = segment.split('.',1)[0].rstrip(' ').upper()
                need(segment not in ('','.','..') and len(segment) <= 255 and segment == segment.strip() and
                     not segment.endswith('.') and all(ord(ch) >= 32 and ord(ch) != 127 and ch != '~' for ch in segment) and
                     stem not in ('CON','PRN','AUX','NUL','CLOCK$','CONIN$','CONOUT$') and
                     re.fullmatch(r'(?:COM|LPT)[1-9]',stem) is None, 'historical path alias')
            need(path.casefold() not in paths, 'historical path collision'); paths.add(path.casefold())
            page = _ls_json(data, checkpoint); closed(page, ('schema','rows'))
            need(page['schema'] == 'cho51_l_' + name + '_page_v1' and type(page['rows']) is list and
                 1 <= len(page['rows']) <= 256 and (i == len(exp['pages']) - 1 or len(page['rows']) == 256), 'historical page')
            need(all(type(row) is dict and type(row.get('kind')) is str for row in page['rows']), 'historical row')
            need(len(rows) + len(page['rows']) <= (RESOLVER_HARD['max_rows'] if name == 'resolver' else HARD['max_nodes']),
                 'capacity: historical rows')
            rows.extend(page['rows'])
        for key in (('nodes',) if name == 'inventory' else ('modules','nodes','module_rows','published_rows','edges',
                    'source_bytes','binding_count','effect_count','binding_frontier_count','effect_frontier_count',
                    'import_frontier_count','queue_count')):
            _ls_int(index[key], 0, 2**63 - 1, 'historical counter')
        if name == 'inventory':
            need(index['nodes'] == len(rows) <= HARD['max_nodes'] and
                 index['unresolved'] == 'all effects, bindings, closure and decisions', 'inventory count or debt')
            _ls_node_joins(rows,'inventory',checkpoint)
            migration = index['migration_ref']
            if migration is not None:
                closed(migration, ('path','bytes','sha256')); _ls_text(migration['path']); _ls_source_pin({k:v for k,v in migration.items() if k != 'path'})
            need(len(index['diagnostics']) <= HARD['max_modules'], 'historical diagnostics count')
            for entry in index['diagnostics']:
                _ls_guard(checkpoint); closed(entry, ('module','source','diagnostic')); _frontier_name(entry['module']); _ls_source_pin(entry['source'])
                diag = entry['diagnostic']; closed(diag, ('kind','message','line','character_column_1based','utf8_byte_column_0based',
                    'end_line','end_character_column_1based','end_utf8_byte_column_0based'))
                need(diag['kind'] in ('SyntaxError','ValueError','RecursionError') and diag['message'] in ('parser rejected source',
                     'invalid syntax', "expected ':'", "'(' was never closed", "'[' was never closed", "'{' was never closed",
                     'unexpected indent','unexpected EOF while parsing'), 'historical diagnostic')
                for key in ('line','character_column_1based','utf8_byte_column_0based','end_line','end_character_column_1based','end_utf8_byte_column_0based'):
                    if diag[key] is not None: _ls_int(diag[key],0 if 'byte' in key else 1,2**63-1,'historical diagnostic coordinate')
        else: _ls_resolver_rows(rows,index,checkpoint)

def _ls_budget(manifest, chunks, allocation):
    total = len(manifest) + sum(len(x) for x in chunks)
    files = 1 + len(chunks)
    need(total + allocation['resolver_bytes'] <= FRONTIER_LIMITS['output_bytes'], 'capacity: transport bytes')
    need(files + allocation['resolver_pages'] <= FRONTIER_LIMITS['pages'], 'capacity: transport pages')
    need(total + allocation['p_bytes'] <= HARD['max_output_bytes'] and
         files + allocation['p_files'] <= HARD['max_output_files'], 'capacity: shared output')

def _ls_result(outcome, reason, checks, logical=None, snapshot=None):
    return {'schema': LOSSLESS_RESULT, 'outcome': outcome, 'reason': reason,
            'checks_completed': checks[:], 'logical_digest': logical, 'snapshot': snapshot,
            'g2_complete': False, 'launch_authorized': False, 'capabilities_accepted': False,
            'scientific_admission': False}

def _ls_decode(bundle, expected_manifest_pin, expected_digest, expected_binding, expected_evidence, allocation, checkpoint, checks):
    _ls_guard(checkpoint); _ls_allocation(allocation); _ls_pin(expected_manifest_pin)
    _frontier_hash(expected_digest); _frontier_binding(expected_binding)
    closed(bundle, ('manifest','chunks')); manifest = bundle['manifest']; chunks = bundle['chunks']
    need(type(manifest) is bytes and type(chunks) is list and 1 <= len(chunks) <= 64 and
         all(type(x) is bytes and 1 <= len(x) <= LOSSLESS_CHUNK for x in chunks), 'transport buffers')
    need(len(manifest) == expected_manifest_pin['bytes'] and _ls_hash(manifest, checkpoint) == expected_manifest_pin['sha256'], 'manifest pin')
    _ls_budget(manifest, chunks, allocation); checks.append('external_and_allocation')
    data = _ls_json(manifest, checkpoint, canonical=True)
    closed(data, ('schema','binding','graph','frames','history','evidence','assets','chunks','status',
                  'g2_complete','launch_authorized','capabilities_accepted','scientific_admission'))
    need(data['schema'] == LOSSLESS_SCHEMA and data['binding'] == expected_binding and
         data['status'] == 'INCOMPLETE_REFUSED' and all(data[k] is False for k in
         ('g2_complete','launch_authorized','capabilities_accepted','scientific_admission')), 'manifest authority or binding')
    need(type(data['frames']) is list and 1 <= len(data['frames']) <= 128 and
         type(data['history']) is list and len(data['history']) == len(data['frames']) and
         type(data['assets']) is list and 1 <= len(data['assets']) <= 512 and
         type(data['chunks']) is list and len(data['chunks']) == len(chunks) and
         type(data['evidence']) is list and len(data['evidence']) <= 2, 'manifest counts')
    for i, (desc, raw) in enumerate(zip(data['chunks'], chunks)):
        _ls_guard(checkpoint); closed(desc, ('ordinal','bytes','sha256'))
        need(type(desc['ordinal']) is int and desc['ordinal'] == i and type(desc['bytes']) is int and
             desc['bytes'] == len(raw) and (i == len(chunks)-1 or len(raw) == LOSSLESS_CHUNK) and
             desc['sha256'] == _ls_hash(raw, checkpoint), 'chunk descriptor')
    assets = {}; position = 0; parts_count = 0; previous = ''
    for desc in data['assets']:
        _ls_guard(checkpoint); closed(desc, ('id','kind','bytes','sha256','parts'))
        kind = desc['kind']; need(kind in ('graph','frame','raw') and type(kind) is str, 'asset kind')
        _frontier_hash(desc['id']); _frontier_hash(desc['sha256']); _ls_int(desc['bytes'], 1, FRONTIER_LIMITS['file_bytes'], 'asset bytes')
        need(desc['id'] > previous and desc['id'] == _ls_asset_id(kind,desc['bytes'],desc['sha256'],checkpoint), 'asset identity')
        previous = desc['id']; need(type(desc['parts']) is list and desc['parts'], 'asset parts')
        remaining = desc['bytes']; pieces = []
        for part in desc['parts']:
            _ls_guard(checkpoint); parts_count += 1; need(parts_count <= 1024, 'asset parts capacity')
            closed(part, ('chunk','offset','bytes')); chunk, offset = divmod(position, LOSSLESS_CHUNK)
            need(chunk < len(chunks), 'asset range'); length = min(remaining, len(chunks[chunk])-offset)
            need(length > 0 and type(part['chunk']) is int and part['chunk'] == chunk and
                 type(part['offset']) is int and part['offset'] == offset and type(part['bytes']) is int and
                 part['bytes'] == length, 'asset partition')
            for start in range(offset, offset + length, 65536):
                _ls_guard(checkpoint); pieces.append(chunks[chunk][start:min(start+65536,offset+length)])
            position += length; remaining -= length
        need(remaining == 0, 'asset missing part'); _ls_guard(checkpoint); raw = b''.join(pieces); _ls_guard(checkpoint)
        need(_ls_hash(raw, checkpoint) == desc['sha256'], 'asset hash'); assets[desc['id']] = (kind, raw)
    need(position == sum(len(x) for x in chunks), 'unused chunk bytes')
    used = set()
    def asset(ident, kind):
        _frontier_hash(ident); need(ident in assets and assets[ident][0] == kind, 'asset use')
        used.add(ident); return assets[ident][1]
    graph_raw = asset(data['graph'], 'graph')
    frame_raw = [asset(ident, 'frame') for ident in data['frames']]
    # Necessary byte lower bounds precede semantic expansion. Every prefix
    # contains these entire canonical assets plus a nonempty wrapper; sharing
    # one frame asset 128 times cannot allocate 128 unchecked parsed copies.
    expanded_lower = len(graph_raw) + sum(map(len,frame_raw)); count = len(frame_raw)
    history_lower = count*len(graph_raw) + sum((count-i)*len(raw) for i,raw in enumerate(frame_raw))
    need(expanded_lower <= FRONTIER_LIMITS['file_bytes'] and expanded_lower <= FRONTIER_LIMITS['output_bytes'] and
         history_lower <= FRONTIER_LIMITS['history_bytes'], 'capacity: expanded asset bytes')
    graph = _ls_json(graph_raw, checkpoint, canonical=True)
    frames = []
    for raw in frame_raw:
        _ls_guard(checkpoint); frame = _ls_json(raw, checkpoint, canonical=True)
        _frontier_payload(frame,0,checkpoint=lambda: (_ls_guard(checkpoint) or True)); frames.append(frame)
    raw_families = []; raw_total = 0
    for family in data['evidence']:
        _ls_guard(checkpoint); closed(family, ('family','index_asset','page_assets'))
        need(type(family['page_assets']) is list and len(family['page_assets']) <= 100, 'page assets')
        index_raw = asset(family['index_asset'],'raw'); raw_total += len(index_raw); pages = []
        for ident in family['page_assets']:
            _ls_guard(checkpoint); page_raw = asset(ident,'raw'); pages.append(page_raw); raw_total += len(page_raw)
            need(raw_total + allocation['resolver_bytes'] <= FRONTIER_LIMITS['output_bytes'] and
                 raw_total + allocation['p_bytes'] <= HARD['max_output_bytes'], 'capacity: raw input bytes')
        need(raw_total + allocation['resolver_bytes'] <= FRONTIER_LIMITS['output_bytes'] and
             raw_total + allocation['p_bytes'] <= HARD['max_output_bytes'], 'capacity: raw input bytes')
        raw_families.append({'family': family['family'], 'index': index_raw, 'pages': pages})
    need(used == set(assets), 'unreferenced asset'); checks.append('transport_partition')
    _ls_evidence(expected_evidence, raw_families, checkpoint); checks.append('historical_content')
    unused_modules, graph_edges = _frontier_graph(graph, lambda: (_ls_guard(checkpoint) or True))
    predecessor = None; snapshot = None
    for i, frame in enumerate(frames):
        _ls_guard(checkpoint); history = data['history'][i]; closed(history, ('sequence','predecessor','sha256','bytes'))
        snapshot = _frontier_snapshot(expected_binding, graph, frames[:i+1], predecessor)
        # Debit the expanded prefix before serializing or hashing it. Repeated
        # physical frame references never bypass the structural and row caps.
        _frontier_capacity(snapshot, graph_edges, lambda: (_ls_guard(checkpoint) or True))
        raw = _ls_encode(snapshot,checkpoint); current = _ls_hash(raw, checkpoint)
        need(type(history['sequence']) is int and history['sequence'] == i and history['predecessor'] == predecessor and
             type(history['bytes']) is int and history['bytes'] == len(raw) and history['sha256'] == current, 'history identity')
        predecessor = current
    need(predecessor == expected_digest, 'expected logical digest')
    _frontier_verify(snapshot, expected_digest, expected_binding, lambda: (_ls_guard(checkpoint) or True))
    checks.append('expanded_replay'); _ls_guard(checkpoint)
    return _frontier_copy(snapshot, lambda: (_ls_guard(checkpoint) or True))

def verify_supplied_bundle(bundle, expected_manifest_pin, expected_digest, expected_binding, expected_evidence, allocation, checkpoint):
    """Verify supplied transport; no filesystem, source, or custody authority."""
    checks = []
    try:
        snapshot = _ls_decode(bundle, expected_manifest_pin, expected_digest, expected_binding, expected_evidence, allocation, checkpoint, checks)
        _ls_guard(checkpoint)
        return _ls_result('VERIFIED_SUPPLIED_STATE', None, checks, expected_digest, snapshot)
    except LosslessCheckpointRefusal:
        raise
    except FrontierCheckpointRefusal as error:
        raise LosslessCheckpointRefusal('live checkpoint') from error
    except (Refusal, ValueError, TypeError, KeyError, IndexError, OverflowError, UnicodeError, RecursionError) as error:
        reason = str(error) if isinstance(error, Refusal) else 'malformed input'
        outcome = 'CAPACITY_REFUSED' if reason.startswith('capacity:') else 'INVALID_INPUT'
        _ls_guard(checkpoint); return _ls_result(outcome, reason, checks)

def _ls_pack_supplied_chain(snapshot, raw_evidence, allocation, checkpoint):
    """Pack a verified supplied chain and verify the resulting transport."""
    _ls_guard(checkpoint); _ls_allocation(allocation)
    try:
        _frontier_payload(snapshot, 0, checkpoint=lambda: (_ls_guard(checkpoint) or True))
    except FrontierCheckpointRefusal as error:
        raise LosslessCheckpointRefusal('live checkpoint') from error
    # Validate shape and expanded capacity before allocating a canonical buffer.
    unused_modules, graph_edges = _frontier_graph(snapshot['graph'], lambda: (_ls_guard(checkpoint) or True))
    _frontier_capacity(snapshot, graph_edges, lambda: (_ls_guard(checkpoint) or True))
    logical = _ls_hash(_ls_encode(snapshot,checkpoint), checkpoint)
    try:
        _frontier_verify(snapshot, logical, snapshot['binding'], lambda: (_ls_guard(checkpoint) or True))
    except FrontierCheckpointRefusal as error:
        raise LosslessCheckpointRefusal('live checkpoint') from error
    need(type(raw_evidence) is list and len(raw_evidence) <= 2, 'evidence families')
    raw_total = 0
    for row in raw_evidence:
        _ls_guard(checkpoint); closed(row, ('family','index','pages'))
        need(type(row['index']) is bytes and type(row['pages']) is list and len(row['pages']) <= 100, 'raw evidence')
        for raw in [row['index']] + row['pages']:
            _ls_guard(checkpoint); need(type(raw) is bytes and 0 < len(raw) <= FRONTIER_LIMITS['file_bytes'], 'raw bytes')
            raw_total += len(raw)
            need(raw_total + allocation['resolver_bytes'] <= FRONTIER_LIMITS['output_bytes'] and
                 raw_total + allocation['p_bytes'] <= HARD['max_output_bytes'], 'capacity: raw input bytes')
    expected = []
    for row in raw_evidence:
        _ls_guard(checkpoint); closed(row, ('family','index','pages'))
        need(type(row['index']) is bytes and type(row['pages']) is list, 'raw evidence')
        def raw_pin(raw):
            need(type(raw) is bytes and 0 < len(raw) <= FRONTIER_LIMITS['file_bytes'], 'raw bytes')
            return {'bytes':len(raw), 'sha256':_ls_hash(raw, checkpoint)}
        expected.append({'family':row['family'], 'index':raw_pin(row['index']), 'pages':[raw_pin(x) for x in row['pages']]})
    _ls_evidence(expected, raw_evidence, checkpoint)
    contents = {}; content_bytes = 0
    def add(kind, raw):
        nonlocal content_bytes
        _ls_guard(checkpoint); need(0 < len(raw) <= FRONTIER_LIMITS['file_bytes'], 'asset size')
        sha = _ls_hash(raw, checkpoint); ident = _ls_asset_id(kind,len(raw),sha,checkpoint)
        need(ident not in contents or contents[ident] == (kind,raw), 'asset collision')
        if ident not in contents:
            content_bytes += len(raw)
            need(content_bytes + allocation['resolver_bytes'] < FRONTIER_LIMITS['output_bytes'] and
                 content_bytes + allocation['p_bytes'] < HARD['max_output_bytes'], 'capacity: transport bytes')
            count = (content_bytes + LOSSLESS_CHUNK-1)//LOSSLESS_CHUNK + 1
            need(count + allocation['resolver_pages'] <= FRONTIER_LIMITS['pages'] and
                 count + allocation['p_files'] <= HARD['max_output_files'], 'capacity: transport files')
        contents[ident] = (kind,raw); need(len(contents) <= 512, 'asset count'); return ident
    graph = add('graph', _ls_encode(snapshot['graph'],checkpoint))
    frames = [add('frame', _ls_encode(x,checkpoint)) for x in snapshot['frames']]
    evidence = [{'family':x['family'], 'index_asset':add('raw',x['index']),
                 'page_assets':[add('raw',p) for p in x['pages']]} for x in raw_evidence]
    history = []; predecessor = None
    for i in range(len(frames)):
        _ls_guard(checkpoint); prefix = _frontier_snapshot(snapshot['binding'],snapshot['graph'],snapshot['frames'][:i+1],predecessor)
        _frontier_capacity(prefix,graph_edges,lambda: (_ls_guard(checkpoint) or True))
        raw = _ls_encode(prefix,checkpoint); current = _ls_hash(raw, checkpoint)
        history.append({'sequence':i,'predecessor':predecessor,'sha256':current,'bytes':len(raw)}); predecessor = current
    chunks = []; descriptors = []; current = bytearray(); part_count = 0
    for ident in sorted(contents):
        kind, raw = contents[ident]; parts = []; offset = 0
        while offset < len(raw):
            _ls_guard(checkpoint); amount = min(LOSSLESS_CHUNK-len(current),len(raw)-offset)
            parts.append({'chunk':len(chunks),'offset':len(current),'bytes':amount}); part_count += 1
            need(part_count <= 1024, 'capacity: parts')
            for start in range(offset, offset + amount, 65536):
                _ls_guard(checkpoint); current.extend(raw[start:min(start+65536,offset+amount)])
            offset += amount
            if len(current) == LOSSLESS_CHUNK:
                _ls_guard(checkpoint); chunks.append(bytes(current)); _ls_guard(checkpoint)
                current.clear(); need(len(chunks) <= 64, 'capacity: chunks')
        descriptors.append({'id':ident,'kind':kind,'bytes':len(raw),'sha256':_ls_hash(raw,checkpoint),'parts':parts})
    if current:
        _ls_guard(checkpoint); chunks.append(bytes(current)); _ls_guard(checkpoint)
    need(1 <= len(chunks) <= 64, 'capacity: chunks')
    manifest = _ls_encode({'schema':LOSSLESS_SCHEMA,'binding':snapshot['binding'],'graph':graph,'frames':frames,
        'history':history,'evidence':evidence,'assets':descriptors,
        'chunks':[{'ordinal':i,'bytes':len(x),'sha256':_ls_hash(x,checkpoint)} for i,x in enumerate(chunks)],
        'status':'INCOMPLETE_REFUSED','g2_complete':False,'launch_authorized':False,
        'capabilities_accepted':False,'scientific_admission':False},checkpoint)
    need(len(manifest) <= FRONTIER_LIMITS['file_bytes'], 'capacity: manifest bytes')
    bundle = {'manifest':manifest,'chunks':chunks}; _ls_budget(manifest,chunks,allocation)
    result = verify_supplied_bundle(bundle, {'bytes':len(manifest),'sha256':_ls_hash(manifest,checkpoint)},
                                    logical,snapshot['binding'],expected,allocation,checkpoint)
    need(result['outcome'] == 'VERIFIED_SUPPLIED_STATE', 'packed bundle failed verification')
    _ls_guard(checkpoint); return bundle

def pack_supplied_chain(snapshot, raw_evidence, allocation, checkpoint):
    try:
        return _ls_pack_supplied_chain(snapshot, raw_evidence, allocation, checkpoint)
    except LosslessCheckpointRefusal:
        raise
    except FrontierCheckpointRefusal as error:
        raise LosslessCheckpointRefusal('live checkpoint') from error
    except Refusal:
        raise
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, UnicodeError, RecursionError) as error:
        raise Refusal('malformed input') from error

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




# Resolver v1 is an observation, never an execution or capability grant.
import ntpath
from collections import deque

RESOLVER_SCHEMA = 'cho51_l_resolver_spec_v1'
RESOLVER_HARD = {'max_modules': 128, 'max_source_bytes': 16 * 1024**2,
                 'max_module_bytes': 2 * 1024**2, 'max_nodes': 200000,
                 'max_depth': 128, 'max_rows': 24000, 'max_edges': 10000,
                 'max_pages': 100, 'max_output_bytes': 16 * 1024**2}
_MODULE = re.compile(r'[A-Za-z_]\w*(\.[A-Za-z_]\w*)*\Z', re.ASCII)

def _resolver_name(value):
    return type(value) is str and len(value) <= 512 and _MODULE.fullmatch(value) is not None

def _resolver_path(value):
    if type(value) is not str or not 3 <= len(value) <= 1024 or '\x00' in value:
        return False
    if not re.fullmatch(r'[A-Za-z]:/(?:[^/\\:]+(?:/[^/\\:]+)*)?', value):
        return False
    parts = value[3:].split('/') if len(value) > 3 else []
    return len(parts) <= 32 and all(part not in ('.', '..') and not part.endswith((' ', '.')) and
               not re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', part) and
               not re.search(r'~[0-9]+(?:\.|$)', part) and
               not any(ord(ch) < 32 or ch in '<>"|?*' for ch in part) for part in parts)
def validate_resolver(spec, physical, checkpoint=lambda: True):
    closed(spec, ('schema', 'roots', 'seeds', 'builtin_modules', 'frozen_modules',
                  'extension_suffixes', 'limits'))
    need(spec['schema'] == RESOLVER_SCHEMA, 'resolver schema')
    closed(spec['limits'], RESOLVER_HARD)
    for key, maximum in RESOLVER_HARD.items():
        value = spec['limits'][key]
        need(type(value) is int and 1 <= value <= maximum, 'resolver limit ' + key)
    roots = spec['roots']
    need(type(roots) is list and 0 < len(roots) <= 128 and all(_resolver_path(x) for x in roots), 'roots')
    need(len({x.casefold() for x in roots}) == len(roots), 'root collision')
    seeds = spec['seeds']
    need(type(seeds) is list and 0 < len(seeds) <= 128, 'seeds')
    seen = set()
    for seed in seeds:
        closed(seed, ('module', 'phase'))
        need(_resolver_name(seed['module']) and type(seed['phase']) is str and
             0 < len(seed['phase']) <= 32, 'seed')
        need(seed['module'].casefold() not in seen, 'seed collision')
        seen.add(seed['module'].casefold())
    for key in ('builtin_modules', 'frozen_modules'):
        values = spec[key]
        need(type(values) is list and len(values) <= 4096 and all(_resolver_name(x) for x in values), key)
        need(len({x.casefold() for x in values}) == len(values), key + ' collision')
    need(not ({x.casefold() for x in spec['builtin_modules']} &
              {x.casefold() for x in spec['frozen_modules']}), 'builtin frozen collision')
    suffixes = spec['extension_suffixes']
    need(type(suffixes) is list and len(suffixes) <= 32 and all(type(x) is str and
         0 < len(x) <= 128 and x.startswith('.') and x.endswith('.pyd') and
         '\\' not in x and '/' not in x for x in suffixes), 'extension suffixes')
    need(len({x.casefold() for x in suffixes}) == len(suffixes), 'suffix collision')
    need(type(physical) is dict and len(physical) <= 25000, 'physical map')
    folded = {}
    for index, (path, item) in enumerate(physical.items()):
        if index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        need(_resolver_path(path), 'physical path')
        need(path.casefold() not in folded, 'physical case collision')
        folded[path.casefold()] = path
        need(type(item) is dict, 'physical descriptor')
        if set(item) != {'bytes', 'sha256'}:
            closed(item, ('schema', 'path', 'native_identity', 'file_type', 'reparse_point',
                          'bytes', 'sha256', 'link_count'))
            need(item['schema'] == 'cho51_lv_file_descriptor_v1' and item['path'] == path and
                 item['file_type'] == 'regular' and item['reparse_point'] is False and
                 type(item['link_count']) is int and item['link_count'] == 1, 'physical descriptor facts')
            identity = item['native_identity']
            closed(identity, ('schema', 'volume_serial', 'file_id', 'volume_kind', 'filesystem'))
            need(identity['schema'] == 'cho51_lv_native_identity_v1' and
                 type(identity['volume_serial']) is str and re.fullmatch('[0-9a-f]{16}', identity['volume_serial']) is not None and
                 identity['volume_serial'] != '0' * 16 and type(identity['file_id']) is str and
                 re.fullmatch('[0-9a-f]{32}', identity['file_id']) is not None and identity['file_id'] != '0' * 32 and
                 identity['volume_kind'] == 'local_fixed' and identity['filesystem'] in ('NTFS', 'ReFS'), 'native identity')
        need(type(item.get('bytes')) is int and 0 <= item['bytes'] <= 2 * 1024**3 and
             type(item.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None,
             'physical pin')
    return spec['limits']

def _origin_cache(physical, checkpoint):
    folded, directories = {}, set()
    for index, path in enumerate(physical):
        if index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        folded[path.casefold()] = path
        parent = path.rpartition('/')[0]
        while len(parent) > 2:
            directories.add(parent.casefold())
            parent = parent.rpartition('/')[0]
    return folded, directories

def _origin(module, spec, physical, checkpoint=lambda: True, cache=None):
    """Resolve each component under its selected executable package parent."""
    folded, directories = cache if cache is not None else _origin_cache(physical, checkpoint)
    parts = module.split('.')
    roots = list(spec['roots'])
    for index, part in enumerate(parts):
        current = '.'.join(parts[:index + 1])
        if index == 0 and current in spec['builtin_modules']:
            result = {'kind': 'builtin', 'module': current}
        elif index == 0 and current in spec['frozen_modules']:
            result = {'kind': 'frozen', 'module': current}
        else:
            result = None; namespaces = []
            for root in roots:
                base = root.rstrip('/') + '/' + part
                # FileFinder tries packages before modules, and loader suffixes
                # in the supplied exact order before the .py source suffix.
                choices = [(base + '/__init__' + suffix, 'extension_package') for suffix in spec['extension_suffixes']]
                choices += [(base + '/__init__.py', 'package')]
                choices += [(base + suffix, 'extension') for suffix in spec['extension_suffixes']]
                choices += [(base + '.py', 'source')]
                for candidate, kind in choices:
                    actual = folded.get(candidate.casefold())
                    if actual is not None:
                        descriptor = physical[actual]
                        result = {'kind': kind, 'module': current, 'path': actual,
                                  'pin': {'bytes': descriptor['bytes'], 'sha256': descriptor['sha256']},
                                  'physical_descriptor': descriptor}
                        break
                if result is not None: break
                if base.casefold() in directories:
                    namespaces.append(base)
            if result is None:
                result = {'kind': 'namespace_unresolved' if namespaces else 'missing_origin',
                          'module': current, 'paths': namespaces}
        if index == len(parts) - 1: return result
        if result['kind'] != 'package':
            return {'kind': 'parent_unresolved', 'module': module, 'parent': result}
        roots = [result['path'].rsplit('/', 1)[0]]
    return {'kind': 'missing_origin', 'module': module}
def _resolver_rows(tree, module, pin_value, raw, limits, checkpoint):
    """Observe lexical candidates, not runtime identity or effect certificates.

    All scopes are collected before resolving names, so later, conditional and
    repeated writes cannot accidentally become a unique binding proof.
    """
    text = source_text(raw)
    lines = text.encode('utf-8').splitlines(keepends=True)
    starts, offset = [], 3 if raw.startswith(b'\xef\xbb\xbf') else 0
    for line in lines:
        starts.append(offset); offset += len(line)
    future = any(isinstance(n, ast.ImportFrom) and n.module == '__future__' and
                 any(a.name == 'annotations' for a in n.names) for n in tree.body)
    scopes = {'$': {'kind': 'module', 'parent': None, 'bindings': {}, 'global': set(), 'nonlocal': set()}}
    rows, imports, nodes, calls, dynamic, exports = [], [], {}, [], [], []
    count = 0
    # CPython's documented AST node families; any new family is explicit refusal.
    known = {name for name in ('Module Interactive Expression FunctionType FunctionDef AsyncFunctionDef ClassDef '
        'Return Delete Assign TypeAlias AugAssign AnnAssign For AsyncFor While If With AsyncWith Match Raise Try TryStar '
        'Assert Import ImportFrom Global Nonlocal Expr Pass Break Continue BoolOp NamedExpr BinOp UnaryOp Lambda IfExp '
        'Dict Set ListComp SetComp DictComp GeneratorExp Await Yield YieldFrom Compare Call FormattedValue JoinedStr '
        'Constant Attribute Subscript Starred Name List Tuple Slice Load Store Del And Or Add Sub Mult MatMult Div Mod '
        'Pow LShift RShift BitOr BitXor BitAnd FloorDiv Invert Not UAdd USub Eq NotEq Lt LtE Gt GtE Is IsNot In NotIn '
        'comprehension ExceptHandler arguments arg keyword alias withitem match_case MatchValue MatchSingleton '
        'MatchSequence MatchMapping MatchClass MatchStar MatchAs MatchOr TypeIgnore TypeVar ParamSpec TypeVarTuple').split()}
    effects = {'Call': 'call_callback_dynamic', 'Attribute': 'attribute_dispatch', 'Subscript': 'subscript_protocol',
        'BinOp': 'operator_protocol', 'UnaryOp': 'operator_protocol', 'Compare': 'comparison_protocol',
        'BoolOp': 'truth_protocol', 'If': 'truth_protocol', 'IfExp': 'truth_protocol', 'While': 'truth_iteration',
        'For': 'iteration_protocol', 'AsyncFor': 'async_iteration_protocol', 'comprehension': 'iteration_protocol',
        'With': 'context_protocol', 'AsyncWith': 'async_context_protocol', 'Try': 'exception_protocol',
        'TryStar': 'exception_protocol', 'ExceptHandler': 'exception_matching', 'Raise': 'exception_protocol',
        'Assert': 'truth_exception', 'Await': 'await_protocol', 'Yield': 'generator_protocol',
        'YieldFrom': 'iteration_protocol', 'Delete': 'delete_write', 'Assign': 'binding_write',
        'AnnAssign': 'binding_write', 'AugAssign': 'operator_write', 'NamedExpr': 'binding_write',
        'Import': 'import', 'ImportFrom': 'import', 'Match': 'pattern_protocol',
        'FormattedValue': 'format_protocol', 'JoinedStr': 'format_protocol',
        'ListComp': 'comprehension_protocol', 'SetComp': 'comprehension_protocol',
        'DictComp': 'comprehension_protocol', 'GeneratorExp': 'generator_protocol',
        'FunctionDef': 'definition_creation', 'AsyncFunctionDef': 'definition_creation',
        'ClassDef': 'class_creation', 'Lambda': 'definition_creation',
        'Dict': 'hash_protocol', 'Set': 'hash_protocol', 'DictComp': 'hash_iteration_protocol',
        'SetComp': 'hash_iteration_protocol', 'Starred': 'unpack_iteration_protocol',
        'keyword': 'keyword_unpack_protocol', 'MatchValue': 'pattern_comparison_protocol',
        'MatchSequence': 'pattern_sequence_protocol', 'MatchMapping': 'pattern_mapping_protocol',
        'MatchClass': 'pattern_attribute_protocol'}
    # Traversal order supplies a conservative source-order witness only within a scope.
    stack = [(tree, '$', None, '$', 'eager', 0, False, None)]
    def bind(scope, name, ident, kind, order, conditional, epoch, target=None):
        if type(name) is not str or not name: return
        scopes[scope]['bindings'].setdefault(name, []).append({'id': ident, 'kind': kind,
            'order': order, 'conditional': conditional, 'epoch': epoch, 'alias_name': target})
    while stack:
        node, path, parent, scope, epoch, depth, conditional, role = stack.pop()
        count += 1
        need(count <= limits['max_nodes'], 'AST node limit')
        need(depth <= limits['max_depth'], 'AST depth limit')
        if (count - 1) % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        ident = digest(encode([module, pin_value['sha256'], path]))
        coords = [getattr(node, k, None) for k in ('lineno', 'col_offset', 'end_lineno', 'end_col_offset')]
        span = None
        if all(type(x) is int for x in coords):
            a, b, c, d = coords
            need(1 <= a <= c <= len(starts) and 0 <= b <= len(lines[a-1]) and 0 <= d <= len(lines[c-1]), 'span')
            start, end = starts[a-1] + b, starts[c-1] + d
            need(start <= end <= len(raw), 'span'); span = digest(raw[start:end])
        else: coords = None
        kind = type(node).__name__
        row = {'id': ident, 'parent': parent, 'module': module, 'source': pin_value,
            'path': path, 'scope': scope, 'scope_kind': scopes[scope]['kind'], 'kind': kind,
            'span_utf8': coords, 'raw_span_sha256': span, 'epoch': epoch,
            'conditional': conditional, 'resolution': 'unresolved', 'capability': 'pending'}
        if kind not in known: row['refusal'] = 'unsupported_ast_construct'
        if kind in ('TypeAlias', 'TypeVar', 'ParamSpec', 'TypeVarTuple') or getattr(node, 'type_params', []):
            row['refusal'] = 'unsupported_annotation_scope'
        if isinstance(node, ast.NamedExpr) and scopes[scope]['kind'] == 'comprehension':
            row['refusal'] = 'comprehension_namedexpr_unmodeled'
        if kind in effects: row['effect'] = effects[kind]
        nodes[ident] = (node, row, count); rows.append(row)
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            declaration = kind.lower(); row.update(binding_kind=declaration, names=list(node.names))
            scopes[scope][declaration].update(node.names)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            row.update(name=node.name, binding_kind='definition')
            bind(scope, node.name, ident, 'decorated_definition' if node.decorator_list else 'definition',
                 count, conditional, epoch)
        if isinstance(node, ast.arg):
            row.update(name=node.arg, binding_kind='parameter'); bind(scope, node.arg, ident, 'parameter', count, conditional, epoch)
        if isinstance(node, ast.Name):
            row.update(name=node.id, binding_kind=type(node.ctx).__name__)
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                bind(scope, node.id, ident, 'delete' if isinstance(node.ctx, ast.Del) else 'store',
                     count, conditional or role == 'comprehension_namedexpr_poison', epoch,
                     None if role == 'comprehension_namedexpr_poison' else role)
        if isinstance(node, ast.alias):
            row.update(name=node.name, alias=node.asname, binding_kind='import_alias')
            bound = node.asname or (node.name.split('.')[0] if role == 'import' else node.name)
            if bound != '*': bind(scope, bound, ident, 'import', count, conditional, epoch, node.name)
        if isinstance(node, ast.ExceptHandler) and node.name:
            bind(scope, node.name, ident, 'exception_target', count, True, epoch)
        if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            bind(scope, node.name, ident, 'pattern_target', count, True, epoch)
        if isinstance(node, ast.MatchMapping) and node.rest:
            bind(scope, node.rest, ident, 'pattern_target', count, True, epoch)
        if isinstance(node, (ast.Import, ast.ImportFrom)): imports.append((node, row))
        if isinstance(node, ast.Call): calls.append((node, row))
        # New scopes have an explicit parent. Class namespaces are skipped by
        # function closure lookup below, as Python does not close over them.
        new_scope = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef,
                             ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            scope_kind = ('class' if isinstance(node, ast.ClassDef) else
                          'comprehension' if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) else 'function')
            scopes[ident] = {'kind': scope_kind, 'parent': scope, 'bindings': {}, 'global': set(), 'nonlocal': set()}
            new_scope = ident
        children = []
        for field, value in ast.iter_fields(node):
            values = list(enumerate(value)) if isinstance(value, list) else [(None, value)]
            for pos, child in values:
                if not isinstance(child, ast.AST): continue
                child_path = path + '/' + field + (':' + str(pos) if pos is not None else '')
                cs, ce, cr = scope, epoch, None
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    if field == 'body': cs, ce = new_scope, 'deferred'
                    elif field == 'args': cs, cr = new_scope, ('arguments', scope, epoch)
                elif isinstance(node, ast.ClassDef) and field == 'body': cs = new_scope
                elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    cs, ce = new_scope, 'deferred' if isinstance(node, ast.GeneratorExp) else epoch
                    if field == 'generators' and pos == 0: cr = ('first_generator', scope, epoch)
                if isinstance(node, ast.arguments) and field in ('defaults', 'kw_defaults') and isinstance(role, tuple):
                    cs, ce = role[1], role[2]
                if isinstance(node, ast.arg) and field == 'annotation':
                    # Argument annotations are evaluated in the enclosing scope.
                    cs = scopes[scope]['parent'] or '$'
                    if future: ce = 'future_annotation_unknown'
                if ((isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and field == 'returns') or
                    (isinstance(node, ast.AnnAssign) and field == 'annotation')) and future:
                    ce = 'future_annotation_unknown'
                if isinstance(node, ast.NamedExpr) and field == 'target' and scopes[scope]['kind'] == 'comprehension':
                    cs = scope
                    while scopes[cs]['kind'] == 'comprehension': cs = scopes[cs]['parent']
                    cr = 'comprehension_namedexpr_poison'
                if isinstance(node, ast.comprehension) and field == 'iter' and isinstance(role, tuple):
                    cs, ce = role[1], role[2]
                if isinstance(node, (ast.Import, ast.ImportFrom)) and field == 'names':
                    cr = 'import' if isinstance(node, ast.Import) else 'from_import'
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and field in ('targets', 'target'):
                    value_node = node.value
                    if isinstance(value_node, ast.Name): cr = value_node.id
                cc = conditional or isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
                                                       ast.TryStar, ast.IfExp, ast.Match, ast.match_case))
                children.append((child, child_path, ident, cs, ce, depth + 1, cc, cr))
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            children.sort(key=lambda item: 0 if '/generators:' in item[1][len(path):] else 1)
        if isinstance(node, ast.comprehension):
            children.sort(key=lambda item: 0 if item[1].endswith('/iter') else 1)
        stack.extend(reversed(children))
    # Declarations redirect bindings for the entire lexical block, including
    # assignments textually preceding a declaration in an invalid source.
    for scope_index, (sid, data) in enumerate(scopes.items()):
        if scope_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        for declaration in ('global', 'nonlocal'):
            for name in data[declaration]:
                entries = data['bindings'].pop(name, [])
                destination = '$' if declaration == 'global' else data['parent']
                while destination and declaration == 'nonlocal' and scopes[destination]['kind'] != 'function':
                    destination = scopes[destination]['parent']
                if destination:
                    # Redirected writes run in a different activation and may never run.
                    for entry in entries: entry['conditional'] = True
                    scopes[destination]['bindings'].setdefault(name, []).extend(entries)
                elif entries:
                    for entry in entries: nodes[entry['id']][1]['refusal'] = 'nonlocal_target_unknown'
    def find_binding(scope, name, order, epoch, visited):
        if len(visited) >= limits['max_depth']: return None, 'alias_depth_limit'
        if (scope, name) in visited: return None, 'alias_cycle'
        visited = visited | {(scope, name)}
        current = scope
        while current:
            data = scopes[current]
            if name in data['global'] and current != '$': current = '$'; continue
            if name in data['nonlocal']:
                current = data['parent']
                while current and scopes[current]['kind'] != 'function': current = scopes[current]['parent']
                continue
            candidates = data['bindings'].get(name, [])
            if candidates:
                if len(candidates) != 1: return None, 'multiple_bindings'
                entry = candidates[0]
                if entry['kind'] == 'decorated_definition': return None, 'decorated_definition_unknown'
                if entry['conditional'] or entry['kind'] in ('delete', 'exception_target', 'pattern_target'):
                    return None, 'conditional_or_deleted_binding'
                if entry['order'] >= order: return None, 'late_binding'
                if current != scope and epoch != 'eager': return None, 'deferred_external_binding'
                if entry['kind'] == 'store':
                    if not entry['alias_name']: return None, 'assignment_value_unknown'
                    return find_binding(current, entry['alias_name'], entry['order'], entry['epoch'], visited)
                return entry, None
            parent_scope = data['parent']
            if data['kind'] in ('function', 'comprehension'):
                while parent_scope and scopes[parent_scope]['kind'] == 'class': parent_scope = scopes[parent_scope]['parent']
            current = parent_scope
        return None, 'unbound_or_builtin_unknown'
    unsupported_type_scopes = any(row.get('refusal') == 'unsupported_annotation_scope' for _, row, _ in nodes.values())
    for row_index, (ident, (node, row, order)) in enumerate(nodes.items()):
        if row_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            binding, reason = ((None, 'unsupported_annotation_scope') if unsupported_type_scopes else
                               find_binding(row['scope'], node.id, order, row['epoch'], set()))
            if binding and binding['kind'] == 'definition':
                definition_path = nodes[binding['id']][1]['path']
                if any(row['path'].startswith(definition_path + '/' + field) for field in
                       ('decorator_list:', 'args', 'returns', 'bases:', 'keywords:', 'type_params:')):
                    binding, reason = None, 'definition_header_not_bound'
            row['binding_candidates'] = [binding['id']] if binding else []
            row['resolution'] = 'lexical_candidate' if binding else 'unresolved'
            if reason: row['refusal'] = reason
            if binding and binding['kind'] == 'import': row['import_candidate'] = binding['alias_name']
    for call_index, (node, row) in enumerate(calls):
        if call_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        func_id = digest(encode([module, pin_value['sha256'], row['path'] + '/func']))
        func_row = nodes.get(func_id, (None, {}, 0))[1]
        row['lexical_targets'] = [candidate for candidate in func_row.get('binding_candidates', [])
                                  if nodes[candidate][1].get('binding_kind') == 'definition']
        row['import_candidate'] = func_row.get('import_candidate')
        row['runtime_binding_proven'] = False
        # A spelling or imported alias is only a possible effect, not proof.
        spelling = node.func.id if isinstance(node.func, ast.Name) else None
        possible = (spelling in ('__import__', 'exec', 'eval', 'compile', 'getattr', 'setattr', 'delattr') or
                    row['import_candidate'] in ('__import__', 'exec', 'eval', 'compile', 'getattr', 'setattr', 'delattr', 'import_module'))
        if possible:
            row['possible_dynamic_effect'] = spelling
            literal = (node.args[0].value if node.args and isinstance(node.args[0], ast.Constant)
                       and type(node.args[0].value) is str and len(node.args[0].value) <= 512 else None)
            dynamic.append({'site': row['id'], 'spelling': spelling, 'target': literal,
                            'reason': 'runtime_identity_unproved'})
        elif isinstance(node.func, ast.Attribute):
            row['possible_dynamic_effect'] = 'attribute_dispatch'
            literal = (node.args[0].value if node.args and isinstance(node.args[0], ast.Constant)
                       and type(node.args[0].value) is str and len(node.args[0].value) <= 512 else None)
            dynamic.append({'site': row['id'], 'spelling': node.func.attr, 'target': literal,
                            'reason': 'attribute_dispatch_unknown'})
        elif not row['lexical_targets']:
            row['possible_dynamic_effect'] = 'unresolved_callable'
            dynamic.append({'site': row['id'], 'spelling': spelling, 'target': None,
                            'reason': 'unresolved_callable_may_import'})
    # Export establishment requires independent module/member proof.
    for row_index, (node, row, _) in enumerate(nodes.values()):
        if row_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if isinstance(node, ast.Name) and node.id == '__all__' and isinstance(node.ctx, (ast.Store, ast.Del)):
            exports.append({'site': row['id'], 'status': 'unresolved'})
    # The internal module-scope sentinel is serialized as the actual Module ID,
    # so every published parent and scope anchor joins to a retained node.
    module_id = digest(encode([module, pin_value['sha256'], '$']))
    for row_index, row in enumerate(rows):
        if row_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if row['scope'] == '$': row['scope'] = module_id
    metadata = {'node_count': count, 'definitions': [r['id'] for r in rows if r.get('binding_kind') == 'definition'],
                'exports': exports, 'dynamic_imports': dynamic,
                'scope_count': len(scopes), 'future_annotations': future}
    return rows, imports, metadata

def _literal_exports(tree, checkpoint):
    """Recognize only an inert, finite module surface; everything else refuses."""
    exports, definitions = None, {}
    for index, node in enumerate(tree.body):
        if index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if isinstance(node, ast.Pass): continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (node.name in definitions or node.decorator_list or node.args.defaults or
                any(x is not None for x in node.args.kw_defaults) or node.returns or
                any(a.annotation for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs) or
                (node.args.vararg and node.args.vararg.annotation) or
                (node.args.kwarg and node.args.kwarg.annotation) or
                getattr(node, 'type_params', [])):
                return None
            definitions[node.name] = True; continue
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and
            isinstance(node.targets[0], ast.Name) and node.targets[0].id == '__all__' and
            exports is None and isinstance(node.value, (ast.List, ast.Tuple)) and
            all(isinstance(x, ast.Constant) and type(x.value) is str and
                re.fullmatch(r'[A-Za-z_]\w*', x.value, re.ASCII) for x in node.value.elts)):
            exports = [x.value for x in node.value.elts]; continue
        return None
    if exports is None or len(exports) != len(set(exports)) or any(x not in definitions for x in exports):
        return None
    return exports

def _components(modules, edges, checkpoint):
    """Deterministic mutual-reachability components; not an execution order."""
    names = sorted(modules); adjacent = {name: set() for name in names}
    for i, edge in enumerate(edges):
        if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if edge['from'] in adjacent and edge['to'] in adjacent: adjacent[edge['from']].add(edge['to'])
    reach = {}
    for name in names:
        visited, todo = set(), [name]
        while todo:
            if len(visited) % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
            item = todo.pop()
            if item in visited: continue
            visited.add(item); todo.extend(sorted(adjacent[item] - visited, reverse=True))
        reach[name] = visited
    groups, remaining = [], set(names)
    while remaining:
        name = min(remaining)
        group = sorted(other for other in remaining if other in reach[name] and name in reach[other])
        groups.append(group); remaining.difference_update(group)
    return groups

def _resolver_pages(records, limits, checkpoint):
    pages = []
    for start in range(0, len(records), 256):
        need(checkpoint() is True, 'checkpoint refused')
        data = encode({'schema': 'cho51_l_resolver_page_v1', 'rows': records[start:start + 256]})
        if len(data) > 8 * 1024**2: return None
        pages.append(data)
    if len(pages) > limits['max_pages']: return None
    if sum(map(len, pages)) + 512 * 1024 > limits['max_output_bytes']: return None
    return pages

def resolve_sources(reader, spec, physical, outputs, checkpoint, parse_scope):
    """Publish bounded graph observations; no capability or execution grant."""
    need(callable(checkpoint) and callable(parse_scope), 'callbacks')
    limits = validate_resolver(spec, physical, checkpoint)
    queue, queued, phase_contexts = deque(), set(), {}
    def enqueue(name, phase, via):
        context = (name, phase, via)
        phase_contexts.setdefault(name, set()).add((phase, via or ''))
        if context not in queued:
            queued.add(context); queue.append(context)
    for seed in spec['seeds']:
        parts = seed['module'].split('.')
        for n in range(1, len(parts) + 1): enqueue('.'.join(parts[:n]), seed['phase'], None)
    origin_cache = _origin_cache(physical, checkpoint)
    seen, case_names, records, edges, graph_frontier, pending_members = {}, {}, [], [], [], []
    source_bytes = node_count = binding_count = effect_count = binding_frontier_count = 0
    cap = None
    while queue:
        need(checkpoint() is True, 'checkpoint refused')
        module, phase, via = queue.popleft()
        if module in seen: continue
        prior = case_names.get(module.casefold())
        if prior is not None and prior != module:
            graph_frontier.append({'module': module, 'reason': 'module_case_collision', 'other': prior}); continue
        if len(seen) >= limits['max_modules']:
            cap = 'max_modules'; queue.appendleft((module, phase, via)); break
        origin = _origin(module, spec, physical, checkpoint, origin_cache)
        origin_row = {'kind': 'origin', 'module': module, 'phase': phase, 'origin': origin,
                      'via': via, 'capability': 'pending'}
        local_rows, local_edges, local_frontier, local_members, discovered = [origin_row], [], [], [], []
        metadata = {'node_count': 0, 'dynamic_imports': []}; size = 0; exports = None
        if origin['kind'] in ('source', 'package'):
            path, pin_value = origin['path'], origin['pin']
            size = pin_value['bytes']
            if size > limits['max_module_bytes'] or source_bytes + size > limits['max_source_bytes']:
                cap = 'source_bytes'; queue.appendleft((module, phase, via)); break
            need(checkpoint() is True, 'checkpoint refused')
            raw = reader.read_small(path, pin_value)
            need(type(raw) is bytes and len(raw) == size and digest(raw) == pin_value['sha256'], 'retained bytes')
            try:
                with parse_scope(path, raw) as tree:
                    need(isinstance(tree, ast.Module), 'parse scope result')
                    observed, imports, metadata = _resolver_rows(tree, module, pin_value, raw, limits, checkpoint)
                    exports = _literal_exports(tree, checkpoint)
            except (SyntaxError, UnicodeError, ValueError, RecursionError) as exc:
                if isinstance(exc, Refusal) and str(exc) == 'checkpoint refused': raise
                if isinstance(exc, Refusal) and 'limit' in str(exc):
                    cap = str(exc); queue.appendleft((module, phase, via)); break
                local_frontier.append({'module': module, 'reason': 'parse_or_analysis_refusal', 'detail': type(exc).__name__})
                observed, imports = [], []
            if node_count + metadata['node_count'] > limits['max_nodes']:
                cap = 'max_nodes'; queue.appendleft((module, phase, via)); break
            # Retain the entire bounded inventory, including structural parents.
            for i, row in enumerate(observed):
                if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
                local_rows.append(row)
                if row.get('refusal') in ('unsupported_ast_construct', 'unsupported_annotation_scope',
                                           'comprehension_namedexpr_unmodeled'):
                    local_frontier.append({'module': module, 'site': row['id'], 'reason': row['refusal']})
            for i, item in enumerate(metadata['dynamic_imports']):
                if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
                local_frontier.append({'module': module, 'site': item['site'], 'reason': 'dynamic_call_unresolved', 'candidate': item.get('target')})
            for i, (node, row) in enumerate(imports):
                if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
                targets = []
                if isinstance(node, ast.Import): targets = [a.name for a in node.names]
                else:
                    package = module if origin['kind'] == 'package' else module.rpartition('.')[0]
                    parts = package.split('.') if package else []
                    if node.level > len(parts):
                        local_frontier.append({'module': module, 'site': row['id'], 'reason': 'relative_import_beyond_root'}); continue
                    base = '.'.join(parts[:len(parts) - node.level + 1]) if node.level else ''
                    target = '.'.join(x for x in (base, node.module or '') if x)
                    if not target:
                        local_frontier.append({'module': module, 'site': row['id'], 'reason': 'empty_import_target'}); continue
                    targets.append(target)
                    for alias_index, alias in enumerate(node.names):
                        if alias_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
                        if alias.name == '*':
                            local_members.append({'module': module, 'site': row['id'], 'base': target, 'member': '*'})
                        else:
                            local_members.append({'module': module, 'site': row['id'], 'base': target, 'member': alias.name})
                            child = target + '.' + alias.name
                            if _resolver_name(child):
                                child_origin = _origin(child, spec, physical, checkpoint, origin_cache)
                                if child_origin['kind'] not in ('missing_origin', 'parent_unresolved'):
                                    targets.append(child)
                for target_index, target in enumerate(targets):
                    if target_index % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
                    if not _resolver_name(target):
                        local_frontier.append({'module': module, 'site': row['id'], 'reason': 'invalid_import_target'}); continue
                    pieces = target.split('.')
                    for n in range(1, len(pieces) + 1):
                        name = '.'.join(pieces[:n])
                        local_edges.append({'from': module, 'to': name, 'site': row['id'],
                                            'phase': phase, 'epoch': row['epoch'], 'conditional': row['conditional']})
                        discovered.append((name, phase, row['id']))
                    if row['epoch'] != 'eager' or row['conditional']:
                        local_frontier.append({'module': module, 'site': row['id'], 'reason': 'deferred_or_conditional_import'})
        elif origin['kind'] not in ('builtin', 'frozen'):
            local_frontier.append({'module': module, 'reason': origin['kind']})
        if (len(records) + len(local_rows) + len(graph_frontier) + len(local_frontier) +
            len(pending_members) + len(local_members) > limits['max_rows'] or
            len(edges) + len(local_edges) > limits['max_edges']):
            cap = 'rows_or_edges'; queue.appendleft((module, phase, via)); break
        trial = records + local_rows + [{'kind': 'edge', **e} for e in edges + local_edges]
        if _resolver_pages(trial, limits, checkpoint) is None:
            cap = 'output_pages_or_bytes'; queue.appendleft((module, phase, via)); break
        # Commit all observations for this module only after all capacity checks.
        records.extend(local_rows); edges.extend(local_edges); graph_frontier.extend(local_frontier)
        pending_members.extend(local_members); source_bytes += size; node_count += metadata['node_count']
        binding_count += sum('binding_kind' in x for x in local_rows)
        effect_count += sum('effect' in x for x in local_rows)
        binding_frontier_count += sum(x.get('binding_kind') == 'Load' and x.get('resolution') == 'unresolved' for x in local_rows)
        seen[module] = {'origin': origin, 'exports': exports}; case_names[module.casefold()] = module
        for i, (name, next_phase, site) in enumerate(discovered):
            if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
            enqueue(name, next_phase, site)
    for i, item in enumerate(pending_members):
        if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        base = seen.get(item['base']); exports = base['exports'] if base else None
        if exports is None or (item['member'] != '*' and item['member'] not in exports):
            graph_frontier.append({**item, 'reason': 'star_export_unresolved' if item['member'] == '*' else 'attribute_or_submodule_unresolved'})
    for i, (name, contexts) in enumerate(sorted(phase_contexts.items())):
        if i % 256 == 0: need(checkpoint() is True, 'checkpoint refused')
        if len({phase for phase, _ in contexts}) > 1:
            graph_frontier.append({'module': name, 'reason': 'multi_phase_join_unresolved',
                                   'contexts': [{'phase': phase, 'via': via or None}
                                                for phase, via in sorted(contexts)]})
    queued_rows = [{'module': m, 'phase': p, 'via': v} for m, p, v in queue]
    if cap: graph_frontier.append({'reason': 'capacity', 'limit': cap})
    frontier_digest = digest(encode(graph_frontier)); queue_digest = digest(encode(queued_rows))
    # No index or page is published unless every frontier and queued context fits.
    front_records = [{'kind': 'frontier', **x} for x in graph_frontier]
    base_records = records + [{'kind': 'edge', **e} for e in edges]
    queue_records = [{'kind': 'queued', **x} for x in queued_rows]
    all_records = base_records + front_records + queue_records
    need(len(all_records) <= limits['max_rows'], 'complete published row limit')
    pages = _resolver_pages(all_records, limits, checkpoint)
    need(pages is not None, 'complete frontier and queue publication exceeds output budget')
    groups = _components(seen, edges, checkpoint)
    index = {'schema': 'cho51_l_resolver_index_v1', 'status': 'INCOMPLETE_REFUSED',
             'g2_complete': False, 'launch_authorized': False,
             'graph_fixed_point': not graph_frontier and not queued_rows,
             'modules': len(seen), 'nodes': node_count, 'module_rows': len(records),
             'published_rows': len(all_records), 'edges': len(edges),
             'source_bytes': source_bytes, 'binding_count': binding_count, 'effect_count': effect_count,
             'binding_frontier_count': binding_frontier_count, 'effect_frontier_count': effect_count,
             'source_pins_sha256': digest(encode([seen[m]['origin'] for m in sorted(seen)])),
             'import_frontier_count': len(graph_frontier), 'frontier_sha256': frontier_digest,
             'frontier_paged': True, 'queue_paged': True,
             'queue_count': len(queued_rows), 'queue_sha256': queue_digest,
             'cap_refusal': cap, 'components': groups, 'component_order_is_execution_grant': False,
             'spec_sha256': digest(encode(spec)), 'pages': []}
    # Reserve the descriptor/index envelope before publication; native output
    # adapter separately enforces the shared P file and byte limits.
    for i, data in enumerate(pages):
        need(checkpoint() is True, 'checkpoint refused')
        index['pages'].append(outputs.write('l-resolver-%03d.json' % i, data))
    data = encode(index)
    need(sum(map(len, pages)) + len(data) <= limits['max_output_bytes'], 'index reservation exceeded')
    outputs.write('l-resolver-index.json', data)
    return index
