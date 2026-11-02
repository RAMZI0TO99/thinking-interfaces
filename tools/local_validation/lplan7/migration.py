"""Pure byte comparison of an explicitly pinned candidate migration."""
import json
import re
from .compiler import Refusal, closed, need, digest

OLD = 'docs/phase2/cho51_p3_adapter_v1/'
NEW = 'docs/phase2/cho51_p3_adapter_v2/'
FILES = ('contracts.py', 'mapping.py', 'telemetry.py', 'test_mapping.py', 'test_telemetry.py', 'README.md')

def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result

def refcheck(ref, raw):
    closed(ref, ('path', 'bytes', 'sha256'))
    need(type(ref['path']) is str and 0 < len(ref['path']) <= 1024, 'ref path')
    need(type(raw) is bytes and type(ref['bytes']) is int and 0 <= ref['bytes'] <= 8 * 1024**2 and
         len(raw) == ref['bytes'] and type(ref['sha256']) is str and digest(raw) == ref['sha256'], 'ref bytes')

def validate_migration(record, old_bytes_by_path, new_bytes_by_path, roster_bytes, control_roster_bytes):
    closed(record, ('schema', 'original_roster_ref', 'original_source_refs', 'successor_source_refs',
                    'allowed_edits', 'function_map', 'control_roster_ref', 'independent_review', 'safety'))
    need(record['schema'] == 'cho51_candidate_migration_v1', 'migration schema')
    need(record['independent_review'] == {'required': True, 'binding': 'external_source_review_and_root_adoption'} and
         type(record['independent_review'].get('required')) is bool, 'review requirement')
    need(record['safety'] == {'launch_authorized': False, 'scientific_admission': False,
                              'original_executed': False, 'successor_executed': False} and
         all(type(v) is bool for v in record['safety'].values()), 'safety')
    refcheck(record['original_roster_ref'], roster_bytes)
    refcheck(record['control_roster_ref'], control_roster_bytes)
    need(type(old_bytes_by_path) is dict and type(new_bytes_by_path) is dict, 'source maps')
    for key, prefix, data in (('original_source_refs', OLD, old_bytes_by_path),
                              ('successor_source_refs', NEW, new_bytes_by_path)):
        refs = record[key]
        need(type(refs) is list and len(refs) == 6 and type(data) is dict and set(data) == {prefix + name for name in FILES}, 'source set')
        need(all(type(ref) is dict and 'path' in ref for ref in refs), 'source refs')
        need({ref['path'] for ref in refs} == set(data) and len({ref['path'] for ref in refs}) == 6, 'source paths')
        for ref in refs: refcheck(ref, data[ref['path']])
    try:
        roster = json.loads(roster_bytes.decode('utf-8-sig'), object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError):
        raise Refusal('invalid roster') from None
    need(type(roster) is dict and type(roster.get('functions')) is list and len(roster['functions']) == 25, 'roster functions')
    need(roster.get('executed') is False and roster.get('function_count') == 25 and roster.get('expected_total') == 117, 'roster status')
    pins = roster.get('candidate_source_pins')
    need(type(pins) is dict, 'roster source pins')
    for name in FILES:
        raw = old_bytes_by_path[OLD + name]
        need(pins.get(OLD + name) == {'bytes': len(raw), 'sha256': digest(raw)}, 'roster source pin')
    for name in FILES[:3]:
        need(old_bytes_by_path[OLD + name] == new_bytes_by_path[NEW + name], 'production bytes')
    edits = record['allowed_edits']
    need(type(edits) is list and len(edits) == 4, 'edit count')
    grouped = {'test_mapping.py': [], 'test_telemetry.py': []}
    for edit in edits:
        closed(edit, ('original_path', 'successor_path', 'original_offset', 'successor_offset', 'removed_hex', 'inserted_hex'))
        name = edit['original_path'][len(OLD):] if type(edit['original_path']) is str and edit['original_path'].startswith(OLD) else ''
        need(name in grouped and edit['successor_path'] == NEW + name, 'edit path')
        need(type(edit['original_offset']) is int and type(edit['successor_offset']) is int and edit['original_offset'] >= 0 and edit['successor_offset'] >= 0, 'edit offset')
        for key in ('removed_hex', 'inserted_hex'):
            need(type(edit[key]) is str and re.fullmatch(r'(?:[0-9a-f]{2})*', edit[key]) is not None and len(edit[key]) <= 256, 'edit bytes')
        grouped[name].append(edit)
    for name, group in grouped.items():
        need(len(group) == 2, 'edit class count')
        raw = old_bytes_by_path[OLD + name]; out = bytearray(); pos = 0
        for edit in sorted(group, key=lambda e: e['original_offset']):
            at = edit['original_offset']; removed = bytes.fromhex(edit['removed_hex']); inserted = bytes.fromhex(edit['inserted_hex'])
            need(at >= pos and at + len(removed) <= len(raw) and raw[at:at+len(removed)] == removed, 'edit original')
            out.extend(raw[pos:at]); need(len(out) == edit['successor_offset'], 'edit successor offset')
            if name == 'test_mapping.py':
                need(removed == b'docs.phase2.cho51_p3_adapter_v1' and inserted == b'docs.phase2.cho51_p3_adapter_v2', 'mapping change')
                need(raw[max(0,at-5):at] == b'from ' and re.match(rb' import (contracts as Contracts|mapping as Mapping)(?:\r?\n)', raw[at+len(removed):]) is not None, 'mapping import context')
            else:
                need(removed == b':' and inserted == b'' and raw[max(0,at-2):at] == b'])', 'decorator edit')
                need(re.match(rb'\r?\ndef test_(segment_rejects_malformed_contract|join_rejects_cross_domain_and_order_errors)\(', raw[at+1:]) is not None, 'decorator context')
            out.extend(inserted); pos = at + len(removed)
        out.extend(raw[pos:])
        need(bytes(out) == new_bytes_by_path[NEW + name], 'undeclared source change')
    maps = record['function_map']; expected = {}
    for row in roster['functions']:
        need(type(row) is dict and set(row) == {'module', 'node_prefix', 'expected_cases'}, 'roster row')
        module, prefix, count = row['module'], row['node_prefix'], row['expected_cases']
        need(module in (OLD + 'test_mapping.py', OLD + 'test_telemetry.py') and type(prefix) is str and
             re.fullmatch(re.escape(module) + r'::test_[A-Za-z0-9_]+', prefix) is not None and type(count) is int and count > 0, 'roster identity')
        need(prefix not in expected, 'duplicate roster identity'); expected[prefix] = (module, count)
    need(type(maps) is list and len(maps) == 25, 'map count')
    seen, totals = set(), {OLD + 'test_mapping.py': 0, OLD + 'test_telemetry.py': 0}
    for row in maps:
        closed(row, ('original_module', 'original_node_prefix', 'successor_module', 'successor_node_prefix', 'expected_cases'))
        prefix = row['original_node_prefix']; need(type(prefix) is str and prefix in expected and prefix not in seen, 'map identity')
        module, count = expected[prefix]
        need(row['original_module'] == module and row['successor_module'] == NEW + module[len(OLD):] and
             row['successor_node_prefix'] == NEW + prefix[len(OLD):] and type(row['expected_cases']) is int and row['expected_cases'] == count, 'map mismatch')
        seen.add(prefix); totals[module] += count
    need(totals[OLD + 'test_mapping.py'] == 39 and totals[OLD + 'test_telemetry.py'] == 78, 'case totals')
    return {'status': 'COMPARISON_ONLY_REQUIRES_INDEPENDENT_REVIEW', 'launch_authorized': False}

