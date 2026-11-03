"""Bounded supplied-event model; no runtime authority or producer."""
import hashlib
from dataclasses import dataclass
from ..hb1 import common as c
from . import registry

FIELDS = ('schema','seq','op','roster','event','case','sub','fixture','kind','code','line','count','prefix')
NEG = ('FAIL','ERROR','SKIP','XFAIL','XPASS','SUBFAIL','FIXTURE_ERROR')
EXC = ('ASSERT','EXCEPTION','SYSTEM_EXIT','KEYBOARD_INTERRUPT')

@dataclass(frozen=True, slots=True)
class Facts:
    records: int
    started: int
    passed: int
    ended: int
    negative: bool
    not_started: tuple
    whole_sha256: str
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def supplied_success(self):
        return self.started == self.passed == self.ended == 216 and not self.negative and not self.not_started
    @property
    def scope(self):
        return 'UNAUTHENTICATED_SUPPLIED_SUCCESS' if self.supplied_success else 'UNAUTHENTICATED_INCOMPLETE_OR_NEGATIVE'


def verify_events(data, operation, *, check, codes=(), fixtures=()):
    """Validate canonical transcript and finite supplied references, never authenticate."""
    c.uuid_text(operation)
    c.checkpoint(check)
    c.require(type(data) is bytes and 0 < len(data) <= 2097152 and data.endswith(b'\n'), 'stream')
    c.require(type(codes) is tuple and len(codes) <= 4096 and type(fixtures) is tuple and len(fixtures) <= 4096, 'tables')
    for row in codes:
        c.checkpoint(check)
        c.require(type(row) is tuple and len(row) == 2 and type(row[0]) is int and 0 <= row[0] <= 65535 and type(row[1]) is int and 1 <= row[1] <= 2147483647, 'code row')
    for row in fixtures:
        c.checkpoint(check)
        c.require(type(row) is tuple and len(row) == 4 and type(row[0]) is int and 0 <= row[0] <= 4095 and type(row[1]) is str and 0 < len(row[1]) <= 128 and row[1].isascii() and type(row[2]) is str and row[2] in ('setup','teardown','cleanup') and type(row[3]) is tuple and len(row[3]) <= 216 and all(type(i) is int and 0 <= i < 732 for i in row[3]) and len(set(row[3])) == len(row[3]), 'fixture row')
    c.require(len(set(codes)) == len(codes) and len({r[0] for r in fixtures}) == len(fixtures), 'duplicate table row')
    lines = []
    offset = 0
    while offset < len(data):
        c.checkpoint(check)
        c.require(len(lines) < 4096, 'record count')
        end = data.find(b'\n', offset, min(len(data), offset + 512))
        c.require(end >= 0, 'line cap or missing LF')
        lines.append(data[offset:end + 1])
        offset = end + 1
    c.require(2 <= len(lines) <= 4096, 'record count')
    expected, selection = registry.expected_ids(), registry.selected_ids()
    c.require(len(expected) == 732 and len(selection) == 216 and len(set(expected)) == 732 and len(set(selection)) == 216, 'registry')
    positions = {name: i for i, name in enumerate(expected)}
    c.require(all(name in positions for name in selection), 'selection')
    order = tuple(positions[name] for name in selection)
    for _, owner, _, affected in fixtures:
        c.checkpoint(check)
        matches = tuple(i for i in order if expected[i].startswith(owner + '.'))
        c.require(matches and affected == matches and all(expected[i].rsplit('.', 1)[0] == owner or expected[i].rsplit('.', 2)[0] == owner for i in matches), 'fixture owner and selection')
    digest = registry.roster_digest(check)
    c.sha256_text(digest)
    active = None
    started = passed = ended = subs = 0
    primary = badcase = sticky = special = False
    group = None
    prefix = hashlib.sha256()
    whole = hashlib.sha256()
    for offset in range(0, len(data), 65536):
        c.checkpoint(check)
        whole.update(data[offset:offset + 65536])
    for index, line in enumerate(lines):
        c.checkpoint(check)
        c.require(len(line) <= 512 and line.endswith(b'\n') and all(32 <= x <= 126 for x in line[:-1]), 'line')
        o = c.strict_json(line, 512, check)
        c.closed(o, FIELDS)
        c.require(c.bounded_bytes(o, 512, check) == line and o['schema'] == 'cho51_cm1_event_v1' and type(o['seq']) is int and o['seq'] == index + 1 and o['op'] == operation and o['roster'] == digest, 'canonical join')
        e, case, sub, fixture, kind, code, loc, count, pre = (o[k] for k in ('event','case','sub','fixture','kind','code','line','count','prefix'))
        c.require(type(e) is str and type(kind) is str, 'event type')
        c.require(index != 0 or e == 'HEADER', 'header first')
        if group is not None:
            owner, k, remaining, ordinal = group
            c.require(all((v is None if prior is None else type(v) is int)
                          for v, prior in zip((case, sub, fixture), owner)), 'exact trace owner types')
            c.require(e == 'TRACE' and (case,sub,fixture) == owner and kind == k and type(count) is int and count == ordinal and type(code) is int and type(loc) is int and (code,loc) in codes and pre is None, 'trace group')
            group = None if remaining == 1 else (owner,k,remaining-1,ordinal+1)
        else:
            c.require(e != 'TRACE' and code is None and loc is None, 'unexpected trace')
            if e == 'HEADER':
                c.require(index == 0 and case is None and sub is None and fixture is None and kind == 'NONE' and type(count) is int and count == 216 and pre is None, 'header')
            elif e == 'FOOTER':
                c.require(index == len(lines)-1 and active is None and case is None and sub is None and fixture is None and kind == 'NONE' and type(count) is int and count == index and pre == prefix.hexdigest(), 'footer')
            else:
                c.require(0 < index < len(lines)-1 and pre is None, 'position')
                if e == 'CASE_START':
                    c.require(active is None and not sticky and started < 216 and type(case) is int and case == order[started] and sub is None and fixture is None and kind == 'NONE' and count is None, 'start')
                    active, started, subs, primary, badcase, special = case, started+1, 0, False, False, False
                elif e == 'CASE_END':
                    c.require(active is not None and type(case) is int and case == active and sub is None and fixture is None and kind == 'NONE' and type(count) is int and count == subs and primary != badcase, 'end')
                    active, ended = None, ended+1
                elif e in ('SUBPASS','SUBFAIL'):
                    c.require(active is not None and not primary and not sticky and type(case) is int and case == active and type(sub) is int and sub == subs+1 and sub <= 4096 and fixture is None, 'subcase')
                    subs += 1
                    if e == 'SUBPASS':
                        c.require(kind == 'NONE' and count is None, 'subpass')
                elif e == 'PASS':
                    c.require(active is not None and type(case) is int and case == active and sub is None and fixture is None and kind == 'NONE' and count is None and not primary and not badcase and not sticky, 'pass')
                    primary, passed = True, passed+1
                elif e == 'FIXTURE_ERROR':
                    c.require(active is None and case is None and sub is None and type(fixture) is int and any(r[0] == fixture for r in fixtures), 'fixture')
                elif e in ('FAIL','ERROR','SKIP','XFAIL','XPASS'):
                    c.require(active is not None and type(case) is int and case == active and sub is None and fixture is None and not primary and (e in ('FAIL','ERROR') or not special), 'negative')
                    if e in ('SKIP','XFAIL','XPASS'):
                        special = True
                else:
                    raise c.Refusal('unknown event')
                if e in NEG:
                    c.require(type(count) is int and 0 <= count <= 128, 'trace count')
                    if e in ('SKIP','XPASS') or (e == 'FIXTURE_ERROR' and kind == 'NONE'):
                        c.require(kind == 'NONE' and count == 0, 'zero-frame outcome')
                    elif kind == 'UNSUPPORTED':
                        c.require(count == 0, 'unsupported callback')
                    else:
                        c.require(kind in EXC and count >= 1, 'trace required')
                    if count:
                        group = ((case,sub,fixture),kind,count,1)
                    sticky = True
                    if active is not None:
                        badcase = True
        if e != 'FOOTER':
            prefix.update(line)
    c.require(group is None and o['event'] == 'FOOTER', 'incomplete')
    c.checkpoint(check)
    return Facts(len(lines), started, passed, ended, sticky, order[started:], whole.hexdigest())

