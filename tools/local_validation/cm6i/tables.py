"""Canonical Q-indexed supplied code and fixture tables."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.context import _check, _json
from ..cm6.collection import verify_collection

@dataclass(frozen=True, slots=True)
class TableFacts:
    codes: tuple
    fixtures: tuple
    raw_pin: tuple
    operation: str
    context: str
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False

def parse_tables(raw_t, raw_q, raw_d, raw_c, expected_q_pin, expected_d_pin, operation):
    collected = verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    v = _json(raw_t, 1048576)
    c.closed(v, ('schema', 'operation', 'context', 'codes', 'fixtures'))
    c.require(v['schema'] == 'cho51_cm6_supplied_tables_v1' and v['operation'] == operation and v['context'] == collected.context, 'table context')
    c.require(type(v['codes']) is list and len(v['codes']) <= 4096 and type(v['fixtures']) is list and len(v['fixtures']) <= 4096, 'table bound')
    codes = []
    for row in v['codes']:
        c.require(type(row) is list and len(row) == 2, 'code pair')
        pair = (c.integer(row[0], 0, 65535), c.integer(row[1], 1, 2147483647))
        c.require(not codes or codes[-1] < pair, 'code order'); codes.append(pair)
    fixtures = []; previous = -1
    for row in v['fixtures']:
        c.closed(row, ('slot', 'owner', 'phase', 'affected'))
        slot = c.integer(row['slot'], 0, 4095); c.require(slot > previous, 'slot order'); previous = slot
        owner = c.token(row['owner'])
        c.require(row['phase'] in ('setup', 'teardown', 'cleanup') and type(row['phase']) is str and type(row['affected']) is list, 'fixture')
        affected = tuple(row['affected'])
        for i in affected: c.integer(i, 0, 359)
        expected = tuple(i for i, name in enumerate(collected.cohort) if name.rsplit('.', 1)[0] == owner or name.rsplit('.', 2)[0] == owner)
        c.require(expected and affected == expected, 'fixture ownership')
        fixtures.append((slot, owner, row['phase'], affected))
    return TableFacts(tuple(codes), tuple(fixtures), (len(raw_t), c.digest(raw_t, _check)), operation, collected.context)

