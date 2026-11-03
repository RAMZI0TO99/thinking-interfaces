"""Independent supplied CM6 lifecycle parser; no producer or runtime capability."""
import hashlib
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.collection import verify_collection
from .tables import parse_tables


MAX_BYTES = 2_097_152
MAX_RECORDS = 4096
EXCEPTIONS = ('ASSERT', 'EXCEPTION', 'SYSTEM_EXIT', 'KEYBOARD_INTERRUPT')
FIELDS = ('schema', 'seq', 'op', 'context', 'event', 'case', 'sub', 'fixture',
          'kind', 'code', 'line', 'count', 'prefix')
UNAVAILABLE = ('actual_lifecycle_completion', 'actual_subcase_population',
               'actual_trace_completeness_and_order', 'original_exception_code_identity',
               'observer_cutoff_custody', 'future_activity_exclusion',
               'final_native_source_restoration_checks', 'capture_eof_tool_return',
               'complete_parent_census', 'owned_process_job_closure',
               'final_producer_refusal_latch', 'native_guard_effectiveness')

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
    declared_suite_closed: bool
    declared_restored: bool
    declared_inputs_verified: bool
    unavailable: tuple = UNAVAILABLE

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False

    @property
    def debt_discharged(self): return False


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


def verify_events(raw, raw_t, raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation):
    from ..cm6.context import _check
    check = _check
    collected = verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    tables = parse_tables(raw_t, raw_q, raw_d, raw_c, expected_q_pin, expected_d_pin, operation)
    codes, fixtures = tables.codes, tables.fixtures
    order = tuple(range(360))
    whole = hash_bytes(raw, check=check)
    locations, fixture_map = frozenset(codes), {row[0]: row for row in fixtures}
    lines, start = [], 0
    while start < len(raw):
        c.checkpoint(check)
        end = raw.find(b'\n', start, min(len(raw), start + 512))
        c.require(end >= 0 and len(lines) < MAX_RECORDS, 'line bound')
        lines.append(raw[start:end + 1])
        start = end + 1
    c.require(2 <= len(lines) <= MAX_RECORDS, 'record count')
    prefix = hashlib.sha256()
    prefix_size = 0
    stage = 'HEADER'
    active = opened_sub = pending = None
    sub_state = None
    started = passed = ended = total_subs = subs = 0
    primary = 'NONE'
    negative = badcase = cleanup = duration = False
    seen = set()
    for index, line in enumerate(lines):
        c.checkpoint(check)
        c.require(all(b < 128 and b != 13 for b in line), 'ASCII LF')
        row = c.strict_json(line, 512, check)
        c.closed(row, FIELDS)
        c.require(c.bounded_bytes(row, 512, check) == line, 'canonical event')
        c.require(row['schema'] == 'cho51_cm6_event_v1' and row['op'] == operation
                  and row['context'] == collected.context, 'event identity')
        c.integer(row['seq'], 1, MAX_RECORDS)
        c.require(row['seq'] == index + 1, 'sequence')
        ev, kind = row['event'], row['kind']
        c.require(type(ev) is str and type(kind) is str, 'event types')
        case, sub, fixture, code, loc, count, digest = (row[k] for k in
            ('case', 'sub', 'fixture', 'code', 'line', 'count', 'prefix'))
        if case is not None: c.integer(case, 0, 359)
        if sub is not None: c.integer(sub, 1, 4096)
        if fixture is not None: c.integer(fixture, 0, 4095)
        if code is not None: c.integer(code, 0, 65535)
        if loc is not None: c.integer(loc, 1, 2147483647)
        if count is not None: c.integer(count, 0, 2**63 - 1 if ev == 'DURATION' else MAX_RECORDS)
        if pending is not None:
            owner, trace_kind, remaining, position = pending
            c.require(ev == 'TRACE' and (case, sub, fixture) == owner and kind == trace_kind
                      and code is not None and loc is not None and (code, loc) in locations
                      and count == position and digest is None, 'trace group')
            pending = None if remaining == 1 else (owner, trace_kind, remaining - 1, position + 1)
        else:
            c.require(ev != 'TRACE' and code is None and loc is None, 'unexpected trace')
            if opened_sub is not None:
                c.require(ev in ('SUBPASS', 'SUBFAIL') if sub_state == 'OUTCOME'
                          else ev == 'SUB_EXIT', 'closed subcase interval')
            if stage == 'HEADER':
                c.require(ev == 'HEADER' and index == 0 and (case, sub, fixture, digest) == (None,)*4
                          and kind == 'NONE' and count == 360, 'header')
                stage = 'OPEN'
            elif stage in ('OPEN', 'RESTORE', 'VERIFY'):
                required = {'OPEN': 'SUITE_OPEN', 'RESTORE': 'RESTORED', 'VERIFY': 'INPUTS_VERIFIED'}[stage]
                c.require(ev == required and (case, sub, fixture, code, loc, count, digest) == (None,)*7
                          and kind == 'NONE', 'suite lifecycle order')
                stage = {'OPEN': 'BODY', 'RESTORE': 'VERIFY', 'VERIFY': 'FOOTER'}[stage]
            elif stage == 'FOOTER':
                c.require(ev == 'FOOTER' and index == len(lines)-1 and (case, sub, fixture) == (None,)*3
                          and kind == 'NONE' and count == index and digest == prefix.hexdigest(), 'footer')
                stage = 'DONE'
            else:
                c.require(stage == 'BODY' and index < len(lines)-1 and digest is None, 'event placement')
                if ev == 'SUITE_CLOSE':
                    c.require(active is None and opened_sub is None and ended == started
                              and (negative or ended == 360)
                              and (case, sub, fixture, count) == (None,)*4 and kind == 'NONE', 'suite close')
                    stage = 'RESTORE'
                elif ev == 'CASE_START':
                    c.require(active is None and not negative and started < len(order) and case == order[started]
                              and (sub, fixture, count) == (None,)*3 and kind == 'NONE', 'start')
                    active, started, primary, badcase, subs = case, started + 1, 'NONE', False, 0
                    cleanup = duration = False
                elif ev == 'FIXTURE_ERROR':
                    c.require(active is None and case is None and sub is None and fixture in fixture_map
                              and fixture not in seen, 'fixture')
                    _, _, phase, affected = fixture_map[fixture]
                    begun = frozenset(order[:started])
                    c.require(not any(i in begun for i in affected) if phase == 'setup'
                              else all(i in begun for i in affected) or negative, 'fixture phase')
                    seen.add(fixture)
                    negative = True
                else:
                    c.require(active is not None and case == active and fixture is None, 'case owner')
                    if ev in ('SUB_ENTER', 'SUBPASS', 'SUBFAIL', 'SUB_EXIT'):
                        if ev == 'SUB_ENTER':
                            c.require(opened_sub is None and not cleanup and primary == 'NONE' and not negative
                                      and sub == subs + 1 and kind == 'NONE' and count is None, 'sub enter')
                            opened_sub, sub_state = sub, 'OUTCOME'
                        else:
                            c.require(sub == opened_sub and opened_sub is not None, 'sub owner')
                            if ev == 'SUB_EXIT':
                                c.require(sub_state == 'EXIT' and kind == 'NONE' and count is None, 'sub exit')
                                opened_sub = sub_state = None
                                subs += 1
                                total_subs += 1
                            else:
                                c.require(sub_state == 'OUTCOME', 'sub outcome')
                                sub_state = 'EXIT'
                                if ev == 'SUBFAIL': negative = badcase = True
                    else:
                        c.require(sub is None, 'unexpected sub')
                        if ev == 'CLEANUP_DONE':
                            c.require(not cleanup and kind == 'NONE' and count is None, 'cleanup')
                            cleanup = True
                        elif ev == 'DURATION':
                            c.require(cleanup and not duration and kind == 'NONE' and type(count) is int, 'duration')
                            duration = True
                        elif ev == 'CASE_END':
                            c.require(cleanup and duration and count == subs and kind == 'NONE'
                                      and (primary != 'NONE' or badcase), 'end')
                            active, ended = None, ended + 1
                        elif ev == 'PASS':
                            c.require(cleanup and duration and primary == 'NONE' and not negative and not badcase
                                      and kind == 'NONE' and count is None, 'pass')
                            primary, passed = 'PASS', passed + 1
                        elif ev in ('FAIL', 'ERROR'):
                            c.require(not cleanup and primary in ('NONE', 'SKIP'), 'failure')
                            negative = badcase = True
                        elif ev in ('SKIP', 'XFAIL', 'XPASS'):
                            c.require(primary == 'NONE' and not badcase and
                                      ((not cleanup) if ev == 'SKIP' else (cleanup and duration)), 'special outcome')
                            primary = ev
                            negative = badcase = True
                        else: raise c.Refusal('unknown event')
                if ev == 'SUBPASS': c.require(kind == 'NONE' and count is None, 'subpass')
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
    c.require(stage == 'DONE' and pending is None and opened_sub is None, 'complete footer')
    c.require(negative or started == passed == ended == 360, 'complete passing selection')
    c.checkpoint(check)
    return EventFacts(whole, prefix.hexdigest(), len(lines), started, passed, ended, total_subs,
                      negative, order[started:], 'SUPPLIED_NEGATIVE_LIFECYCLE' if negative else
                      'SUPPLIED_LIFECYCLE_CONSISTENT', True, True, True)


def dispatch():
    raise c.Refusal('REFUSED_UNADMITTED')



