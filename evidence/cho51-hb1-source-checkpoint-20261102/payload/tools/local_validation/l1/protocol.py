"""Closed L observation records and bounded authenticated-stream framing.

Authentication is supplied by the parent's original pipe/process ownership;
UUIDs and well formed records are deliberately not treated as authentication.
"""
import hashlib
import json
import math
import re
import struct
import uuid
from ..v1.records import Refusal

FRAME_BYTES = 8 * 1024**2
OUTPUT_BYTES = 64 * 1024**2
MAX_NODES = 200_000
COUNTERS = ('source_updates', 'restore_count', 'support_updates', 'gradient_updates',
            'target_inference_calls', 'query_count', 'model_constructions', 'measured_cells')
SAFETY = ('historical_custody_closed', 'historical_operation_released',
          'historical_retry_allowed', 'restart_qualified', 'scientific_admission',
          'candidate_tests_executed', 'successor_controls_executed')
PAYLOADS = {
 'checkpoint': 'state tick imports_digest native_sequence resources_digest guard_digest counters',
 'import_row': 'module phase origin kind loader_type namespace_paths retained_ref initializer_group',
 'native_event': 'event_sequence reason phase base image_size full_path native_observer_generation fault_flags',
 'native_join': 'event_sequence retained_ref system_role requester_choice snapshot_membership',
 'resource_row': 'resource_id phase caller retained_ref mode bytes_read mechanism outcome',
 'abi_row': 'module phase interpreter_identity extension_ref metadata_refs symbol_results safe_query_results loaded_image_refs scope unqualified_paths',
 'guard_row': 'guard_id phase defining_symbol blocker_identity aliases sentinel_result denial_sequence',
 'denial': 'ordinal phase mechanism operation target_role expected_sentinel_id before_effect tick',
 'collection_item': 'ordinal nodeid module original_function_name parameter_id source_ref item_type collection_sequence',
 'collection_end': 'pytest_exit_code collection_errors collection_skips deselected item_count function_counts ordered_roster_sha256 fixture_setup_calls runtest_protocol_calls phase_report_calls',
 'terminal': 'status first_failure completed_state observations_digest counters observer_shutdown safety',
}

def need(condition, message):
    if not condition:
        raise Refusal(message)

def integer(value, lower=0, upper=2**63-1):
    need(type(value) is int and lower <= value <= upper, 'bounded exact integer')
    return value

def string(value, maximum=4096, empty=False):
    need(type(value) is str, 'exact string')
    try:
        size = len(value.encode('utf-8', 'strict'))
    except UnicodeError as error:
        raise Refusal('invalid Unicode') from error
    need((empty or size > 0) and size <= maximum and '\0' not in value, 'bounded string')
    return value

def closed(value, keys):
    need(type(value) is dict and set(value) == set(keys.split() if type(keys) is str else keys),
         'closed object fields')
    return value

def digest(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'SHA256')
    return value

def canonical_uuid(value):
    string(value, 36)
    try:
        need(str(uuid.UUID(value)) == value, 'canonical UUID')
    except ValueError as error:
        raise Refusal('UUID') from error
    return value

def graph(value):
    count = 0
    def visit(item, depth):
        nonlocal count
        count += 1
        need(depth <= 32 and count <= MAX_NODES, 'JSON depth/nodes')
        if type(item) is dict:
            for key, child in item.items():
                string(key, FRAME_BYTES, empty=True)
                visit(child, depth+1)
        elif type(item) is list:
            for child in item:
                visit(child, depth+1)
        elif type(item) is str:
            string(item, FRAME_BYTES, empty=True)
        else:
            need(item is None or type(item) in (bool, int, float), 'JSON scalar')
            need(type(item) is not float or math.isfinite(item), 'finite JSON number')
    visit(value, 0)
    return value

def encode(value):
    graph(value)
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    need(len(raw) <= FRAME_BYTES, 'JSON byte bound')
    return raw

def decode(raw):
    need(type(raw) is bytes and 0 < len(raw) <= FRAME_BYTES, 'JSON bytes')
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def bad(value):
        raise Refusal('nonfinite JSON')
    try:
        value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=pairs, parse_constant=bad)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Refusal('invalid bounded JSON') from error
    return graph(value)

def zero_counters(value):
    closed(value, COUNTERS)
    for item in value.values():
        integer(item, 0, 0)
    return value

def safety(value):
    closed(value, SAFETY)
    for key in SAFETY[:5]:
        need(value[key] is False, 'historical/scientific scope')
    for key in SAFETY[5:]:
        integer(value[key], 0, 0)
    return value

def ref(value, retained=False):
    keys = 'path bytes sha256 role'
    closed(value, keys + (' native_identity owner sharing' if retained else ''))
    path = string(value['path'], 32768)
    need(re.match('^[A-Z]:/', path) is not None and '\\' not in path
         and all(p not in ('', '.', '..') for p in path[3:].split('/')), 'canonical absolute path')
    integer(value['bytes'], 0, 2*1024**3)
    digest(value['sha256']); string(value['role'], 128)
    if retained:
        closed(value['native_identity'], 'schema volume_serial file_id volume_kind filesystem')
        ident = value['native_identity']
        need(ident['schema'] == 'cho51_lv_native_identity_v1' and ident['volume_kind'] == 'local_fixed'
             and ident['filesystem'] == 'NTFS' and re.fullmatch('[0-9a-f]{16}', ident['volume_serial'])
             and re.fullmatch('[0-9a-f]{32}', ident['file_id']), 'retained identity')
        string(value['owner'], 128)
        closed(value['sharing'], 'read write delete')
        need(all(type(v) is bool for v in value['sharing'].values()), 'sharing exact booleans')
    return value

def roster_digest(nodeids):
    need(type(nodeids) is list, 'ordered roster array')
    for value in nodeids:
        string(value, 2048)
    need(len(set(nodeids)) == len(nodeids), 'duplicate node IDs')
    return hashlib.sha256(encode(nodeids)).hexdigest()

def validate_payload(kind,value):
    if 'phase' in value:need(value['phase'] in ('L1','L2','L3','L4','L5'),'payload phase')
    if kind=='checkpoint':
        for key in ('imports_digest','resources_digest','guard_digest'):digest(value[key])
        integer(value['native_sequence'],0,8192)
    if kind=='native_event':
        integer(value['event_sequence'],1,8192);integer(value['base'],1,2**64-1)
        integer(value['image_size'],1,2**32-1);integer(value['native_observer_generation'],1)
        integer(value['fault_flags'],0,0);string(value['full_path'],4096)
        need(value['reason'] in ('load','unload'),'native reason')
    if kind=='native_join':
        integer(value['event_sequence'],1,8192)
        need((value['retained_ref'] is None)!=(value['system_role'] is None),'one native join role')
        if value['retained_ref'] is not None:ref(value['retained_ref'],retained=True)
        else:string(value['system_role'],256)
        string(value['requester_choice'],1024);string(value['snapshot_membership'],256)
    if kind=='resource_row':
        ref(value['retained_ref'],retained=True);integer(value['bytes_read'],0,2*1024**3)
        need(value['mode']=='rb' and value['outcome'] in ('observed','denied'),'resource mode/outcome')
        for key in ('resource_id','caller','mechanism'):string(value[key],4096)
    if kind=='import_row':
        string(value['module'],2048);string(value['loader_type'],512);string(value['initializer_group'],256)
        need(value['kind'] in ('source','extension','builtin','frozen','namespace'),'import kind')
        need(type(value['namespace_paths']) is list,'namespace array')
        if value['kind'] in ('source','extension'):ref(value['retained_ref'],retained=True)
        else:need(value['retained_ref'] is None,'nonfile retained ref')
    if kind=='denial':
        integer(value['ordinal'],0,25000);need(value['before_effect'] is True,'denial before effect')
        for key in ('mechanism','operation','target_role'):string(value[key],4096)
        if value['expected_sentinel_id'] is not None:string(value['expected_sentinel_id'],256)
    if kind=='collection_item':
        integer(value['ordinal'],0,116);integer(value['collection_sequence'],0,116)
        string(value['nodeid'],2048);string(value['module'],2048);string(value['original_function_name'],512)
        if value['parameter_id'] is not None:string(value['parameter_id'],1024,empty=True)
        ref(value['source_ref'],retained=True);need(value['item_type']=='_pytest.python.Function','collection item type')
    if kind=='collection_end':
        for key in ('pytest_exit_code','collection_errors','collection_skips','deselected','fixture_setup_calls','runtest_protocol_calls','phase_report_calls'):integer(value[key],0,0)
        integer(value['item_count'],117,117);digest(value['ordered_roster_sha256'])
        need(type(value['function_counts']) is dict and len(value['function_counts'])==25,'function count map')
        for key,count in value['function_counts'].items():string(key,2048);integer(count,1,117)
    if kind=='abi_row':
        need(value['scope']=='observed initialization and required-symbol compatibility for the exact declared path','ABI scope')
        ref(value['extension_ref'],retained=True)
    if kind=='guard_row':
        need(value['sentinel_result'] is True,'guard sentinel incomplete')
        for key in ('guard_id','defining_symbol','blocker_identity'):string(value[key],1024)
        integer(value['denial_sequence'],0,25000)

class FailureLatch:
    def __init__(self):
        self.first = None
    def refuse(self, message):
        if self.first is None:
            self.first = string(message, 4096)
        raise Refusal(self.first)
    def check(self):
        need(self.first is None, self.first or 'sticky failure')

class PhaseMachine:
    def __init__(self, latch=None):
        self.state = 'L0'
        self.latch = latch or FailureLatch()
    def advance(self, target):
        self.latch.check()
        if target != 'L' + str(int(self.state[1])+1) or target not in tuple('L'+str(i) for i in range(1,7)):
            self.latch.refuse('phase skipped/reversed')
        self.state = target
    def require(self, *states):
        self.latch.check()
        if self.state not in states:
            self.latch.refuse('effect outside authorized phase')

class FrameValidator:
    def __init__(self, operation_id):
        self.operation_id = canonical_uuid(operation_id)
        self.next = 0
        self.terminal = False
        self.phase = 1
    def accept(self, value):
        closed(value, 'schema operation_id sequence phase kind payload')
        need(value['schema'] == 'cho51_l_frame_v1' and value['operation_id'] == self.operation_id, 'frame identity')
        integer(value['sequence'], self.next, self.next)
        need(not self.terminal and value['kind'] in PAYLOADS, 'after terminal/unknown kind')
        phase = value['phase']
        need(phase in ('L1','L2','L3','L4','L5'), 'child phase')
        index = int(phase[1])
        need(self.phase <= index <= self.phase+1, 'frame phase order')
        self.phase = index
        payload = closed(value['payload'], PAYLOADS[value['kind']])
        graph(payload)
        validate_payload(value['kind'],payload)
        if 'phase' in payload:
            need(payload['phase'] == phase, 'payload phase join')
        if value['kind'] == 'checkpoint':
            need(payload['state'] == phase, 'checkpoint state')
            zero_counters(payload['counters'])
        if value['kind'] == 'terminal':
            need(payload['status'] in ('provisional-complete','refused','unknown'), 'terminal status')
            need(payload['completed_state'] == phase, 'terminal phase')
            zero_counters(payload['counters']); safety(payload['safety'])
            need(type(payload['observer_shutdown']) is bool, 'observer shutdown boolean')
            if payload['status'] == 'provisional-complete':
                need(phase == 'L5' and payload['first_failure'] is None and payload['observer_shutdown'] is True,
                     'incomplete terminal success')
            self.terminal = True
        self.next += 1
        return value

class FrameReader:
    def __init__(self, read, operation_id, checkpoint):
        self.read, self.checkpoint = read, checkpoint
        self.validator = FrameValidator(operation_id)
        self.bytes = 0
    def _exact(self, size, eof=False):
        parts = bytearray()
        while len(parts) < size:
            need(self.checkpoint() is True, 'stream checkpoint')
            piece = self.read(size-len(parts))
            need(type(piece) is bytes and len(piece) <= size-len(parts), 'bounded pipe read')
            if not piece and eof and not parts:
                return None
            need(bool(piece), 'truncated frame')
            parts.extend(piece)
        return bytes(parts)
    def next_frame(self):
        header = self._exact(4, eof=True)
        if header is None:
            need(self.validator.terminal, 'EOF before terminal')
            return None
        size = struct.unpack('<I', header)[0]
        integer(size, 1, FRAME_BYTES)
        self.bytes += size+4
        need(self.bytes <= OUTPUT_BYTES, 'whole pipe bytes')
        return self.validator.accept(decode(self._exact(size)))

class FrameWriter:
    def __init__(self, write, operation_id, checkpoint):
        self.write, self.checkpoint = write, checkpoint
        self.validator = FrameValidator(operation_id)
        self.bytes = 0
    def emit(self, phase, kind, payload):
        value = dict(schema='cho51_l_frame_v1', operation_id=self.validator.operation_id,
                     sequence=self.validator.next, phase=phase, kind=kind, payload=payload)
        raw = encode(value)
        self.validator.accept(value)
        self.bytes += len(raw)+4
        need(self.bytes <= OUTPUT_BYTES, 'whole output bound')
        raw = struct.pack('<I', len(raw))+raw
        while raw:
            need(self.checkpoint() is True, 'write checkpoint')
            count = self.write(raw)
            integer(count, 1, len(raw))
            raw = raw[count:]
