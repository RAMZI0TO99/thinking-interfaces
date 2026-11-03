"""Independent verifier for the observable frozen CM2 event transcript."""
import hashlib
from dataclasses import dataclass

from ..hb1 import common as c
from ..cm2 import registry
from .tables import validate_tables

MAX_BYTES = 2_097_152
MAX_RECORDS = 4096
EXCEPTIONS = ('ASSERT', 'EXCEPTION', 'SYSTEM_EXIT', 'KEYBOARD_INTERRUPT')
UNAVAILABLE = ('method_cleanup_completion', 'duration_ordering', 'suite_closure',
               'final_producer_refusal_latch', 'native_guard_effectiveness',
               'original_trace_type_identity', 'original_source_transport_custody',
               'actual_subcase_population', 'actual_trace_completeness_and_order')
FIELDS = ('schema', 'seq', 'op', 'roster', 'event', 'case', 'sub', 'fixture',
          'kind', 'code', 'line', 'count', 'prefix')

@dataclass(frozen=True, slots=True)
class EventFacts:
    whole_sha256: str
    prefix_sha256: str
    records: int
    started: int
    passed: int
    ended: int
    subcases: int
    negative: bool
    not_started: tuple
    disposition: str
    unavailable: tuple = UNAVAILABLE

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def hash_bytes(raw, *, check):
    c.require(type(raw) is bytes and 1 <= len(raw) <= MAX_BYTES, 'bounded bytes')
    c.checkpoint(check)
    result = hashlib.sha256()
    for offset in range(0, len(raw), 65536):
        c.checkpoint(check)
        result.update(raw[offset:offset + 65536])
        c.checkpoint(check)
    c.checkpoint(check)
    return result.hexdigest()


def verify_events(raw, operation, *, codes=(), fixtures=(), check):
    c.require(type(raw) is bytes and 1 <= len(raw) <= MAX_BYTES, 'event bytes')
    c.uuid_text(operation)
    codes, fixtures = validate_tables(codes, fixtures, check=check)
    expected, selected, order = registry.expected_ids(), registry.selected_ids(), registry.selected_ordinals()
    c.require(type(expected) is tuple and len(expected) == 764 and type(selected) is tuple
              and len(selected) == 248 and type(order) is tuple and len(order) == 248
              and tuple(expected[i] for i in order) == selected, 'frozen registry')
    c.require(registry.roster_digest(check) == registry.FULL_DIGEST and
              registry.selection_digest(check) == registry.SELECTION_DIGEST, 'registry pin')
    whole = hash_bytes(raw, check=check)
    locations, fixture_map = frozenset(codes), {row[0]: row for row in fixtures}
    lines = []
    start = 0
    while start < len(raw):
        c.checkpoint(check)
        end = raw.find(b'\n', start, min(len(raw), start + 512))
        c.require(end >= 0 and len(lines) < MAX_RECORDS, 'line bound')
        lines.append(raw[start:end + 1])
        start = end + 1
    c.require(2 <= len(lines) <= MAX_RECORDS, 'record count')
    prefix = hashlib.sha256()
    active = None
    started = passed = ended = subs = total_subs = 0
    primary = 'NONE'
    negative = badcase = False
    seen = set()
    pending = None
    prefix_size = 0
    for index, line in enumerate(lines):
        c.checkpoint(check)
        c.require(all(b < 128 and b != 13 for b in line), 'ASCII LF')
        row = c.strict_json(line, 512, check)
        c.closed(row, FIELDS)
        c.require(c.bounded_bytes(row, 512, check) == line, 'canonical event')
        c.require(row['schema'] == 'cho51_cm2_event_v1' and row['op'] == operation
                  and row['roster'] == registry.FULL_DIGEST, 'event identity')
        c.integer(row['seq'], 1, MAX_RECORDS)
        c.require(row['seq'] == index + 1, 'sequence')
        ev = row['event']
        c.require(type(ev) is str and type(row['kind']) is str, 'event types')
        case, sub, fixture = row['case'], row['sub'], row['fixture']
        kind, code, loc, count, digest = (row[k] for k in ('kind','code','line','count','prefix'))
        if case is not None: c.integer(case, 0, 763)
        if sub is not None: c.integer(sub, 1, 4096)
        if fixture is not None: c.integer(fixture, 0, 4095)
        if count is not None: c.integer(count, 0, MAX_RECORDS)
        if code is not None: c.integer(code, 0, 65535)
        if loc is not None: c.integer(loc, 1, 2147483647)
        if pending is not None:
            owner, trace_kind, remaining, position = pending
            c.require(ev == 'TRACE' and (case, sub, fixture) == owner and kind == trace_kind
                      and (code, loc) in locations and count == position and digest is None,
                      'trace group')
            pending = None if remaining == 1 else (owner, trace_kind, remaining - 1, position + 1)
        else:
            c.require(ev != 'TRACE' and code is None and loc is None, 'unexpected trace')
            if ev == 'HEADER':
                c.require(index == 0 and (case, sub, fixture, digest) == (None,)*4
                          and kind == 'NONE' and count == 248, 'header')
            elif ev == 'FOOTER':
                c.require(index == len(lines)-1 and active is None and ended == started
                          and (negative or ended == 248) and (case, sub, fixture) == (None,)*3
                          and kind == 'NONE' and count == index and digest == prefix.hexdigest(), 'footer')
            else:
                c.require(index > 0 and index < len(lines)-1 and digest is None, 'event placement')
                if ev == 'CASE_START':
                    c.require(active is None and not negative and started < 248 and case == order[started]
                              and sub is None and fixture is None and kind == 'NONE' and count is None, 'start')
                    active, started, primary, badcase, subs = case, started + 1, 'NONE', False, 0
                elif ev == 'CASE_END':
                    c.require(active is not None and case == active and sub is None and fixture is None
                              and kind == 'NONE' and count == subs and (primary != 'NONE' or badcase), 'end')
                    active, ended = None, ended + 1
                elif ev == 'FIXTURE_ERROR':
                    c.require(active is None and case is None and sub is None and fixture in fixture_map
                              and fixture not in seen, 'fixture')
                    _, _, phase, affected = fixture_map[fixture]
                    begun = frozenset(order[:started])
                    c.require((not any(i in begun for i in affected)) if phase == 'setup'
                              else (all(i in begun for i in affected) or negative), 'fixture phase')
                    seen.add(fixture)
                    negative = True
                else:
                    c.require(active is not None and case == active and fixture is None, 'case owner')
                    if ev in ('SUBPASS','SUBFAIL'):
                        c.require(primary == 'NONE' and not negative and sub == subs + 1, 'subtest')
                        subs += 1
                        total_subs += 1
                        if ev == 'SUBFAIL': negative = badcase = True
                    else:
                        c.require(sub is None, 'unexpected sub')
                        if ev == 'PASS':
                            c.require(primary == 'NONE' and not negative and not badcase
                                      and kind == 'NONE' and count is None, 'pass')
                            primary, passed = 'PASS', passed + 1
                        elif ev in ('FAIL','ERROR'):
                            c.require(primary in ('NONE','SKIP'), 'failure')
                            negative = badcase = True
                        elif ev in ('SKIP','XFAIL','XPASS'):
                            c.require(primary == 'NONE' and not badcase, 'special outcome')
                            primary = ev
                            negative = badcase = True
                        else:
                            raise c.Refusal('unknown event')
                if ev == 'SUBPASS':
                    c.require(kind == 'NONE' and count is None, 'subpass')
                if ev in ('FAIL','ERROR','SUBFAIL','XFAIL','FIXTURE_ERROR','SKIP','XPASS'):
                    if ev in ('SKIP','XPASS') or (ev == 'FIXTURE_ERROR' and kind == 'NONE'):
                        c.require(kind == 'NONE' and count == 0, 'zero trace')
                    else:
                        c.require(kind in EXCEPTIONS and type(count) is int and 1 <= count <= 128, 'exception trace')
                        pending = ((case, sub, fixture), kind, count, 1)
        if ev != 'FOOTER':
            prefix_size += len(line)
            c.require(index < 4095 and prefix_size <= MAX_BYTES - 512, 'footer reservation')
            prefix.update(line)
    c.require(lines and row['event'] == 'FOOTER' and pending is None, 'complete footer')
    disposition = 'SUPPLIED_NEGATIVE_TRANSCRIPT' if negative else 'SUPPLIED_TRANSCRIPT_CONSISTENT'
    c.require(negative or started == passed == ended == 248, 'complete passing selection')
    c.checkpoint(check)
    return EventFacts(whole, prefix.hexdigest(), len(lines), started, passed, ended,
                      total_subs, negative, order[started:], disposition)


def dispatch():
    raise c.Refusal('REFUSED_UNADMITTED')

