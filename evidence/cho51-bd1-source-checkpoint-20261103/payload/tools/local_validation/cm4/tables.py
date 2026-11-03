"""Closed current CM4 supplied tables; no original code or fixture witness."""
from dataclasses import dataclass

from ..hb1 import common as c
from . import registry


@dataclass(frozen=True, slots=True)
class TableFacts:
    codes: tuple
    fixtures: tuple
    whole_sha256: str
    operation: str
    roster_sha256: str
    selection_sha256: str

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def validate_tables(codes, fixtures, *, check):
    c.checkpoint(check)
    c.require(type(codes) is tuple and len(codes) <= 4096
              and type(fixtures) is tuple and len(fixtures) <= 4096, 'table bounds')
    previous = None
    for pair in codes:
        c.checkpoint(check)
        c.require(type(pair) is tuple and len(pair) == 2, 'exact code pair')
        c.integer(pair[0], 0, 65535)
        c.integer(pair[1], 1, 2147483647)
        c.require(previous is None or previous < pair, 'sorted unique code pairs')
        previous = pair
    ids, selected, order = registry.expected_ids(), registry.selected_ids(), registry.selected_ordinals()
    c.require(type(ids) is tuple and len(ids) == len(set(ids)) == registry.FULL_COUNT
              and type(selected) is tuple and len(selected) == len(set(selected)) == registry.SELECTED_COUNT
              and type(order) is tuple and len(order) == registry.SELECTED_COUNT
              and tuple(ids[i] for i in order) == selected, 'current target roster')
    registry.roster_digest(check)
    registry.selection_digest(check)
    previous_slot = -1
    for row in fixtures:
        c.checkpoint(check)
        c.require(type(row) is tuple and len(row) == 4, 'exact fixture row')
        slot, owner, phase, affected = row
        c.integer(slot, 0, 4095)
        c.require(slot > previous_slot, 'sorted unique fixture slots')
        c.token(owner)
        c.require(type(phase) is str and phase in ('setup', 'teardown', 'cleanup')
                  and type(affected) is tuple and 0 < len(affected) <= registry.SELECTED_COUNT,
                  'fixture phase and affected set')
        for ordinal in affected:
            c.checkpoint(check)
            c.integer(ordinal, 0, registry.FULL_COUNT - 1)
        matches = tuple(i for i in order if ids[i].rsplit('.', 1)[0] == owner
                        or ids[i].rsplit('.', 2)[0] == owner)
        c.require(affected == matches, 'exact fixture owner and selection')
        previous_slot = slot
    c.checkpoint(check)
    return codes, fixtures


def parse_tables(raw, operation, *, check):
    c.uuid_text(operation)
    value = c.strict_json(raw, 1_048_576, check)
    c.closed(value, ('schema', 'operation', 'roster', 'selection', 'codes', 'fixtures'))
    c.require(value['schema'] == 'cho51_cm4_supplied_tables_v1'
              and value['operation'] == operation, 'table identity')
    full, selected = registry.roster_digest(check), registry.selection_digest(check)
    c.require(value['roster'] == full and value['selection'] == selected, 'table context')
    c.require(c.bounded_bytes(value, 1_048_576, check) == raw, 'canonical tables')
    c.require(type(value['codes']) is list and len(value['codes']) <= 4096
              and type(value['fixtures']) is list and len(value['fixtures']) <= 4096, 'table rows')
    codes, fixtures = [], []
    for pair in value['codes']:
        c.checkpoint(check)
        c.require(type(pair) is list and len(pair) == 2, 'raw code pair')
        codes.append(tuple(pair))
    for row in value['fixtures']:
        c.checkpoint(check)
        c.closed(row, ('slot', 'owner', 'phase', 'affected'))
        c.require(type(row['affected']) is list and 0 < len(row['affected']) <= registry.SELECTED_COUNT,
                  'raw affected set')
        fixtures.append((row['slot'], row['owner'], row['phase'], tuple(row['affected'])))
    codes, fixtures = validate_tables(tuple(codes), tuple(fixtures), check=check)
    whole = c.digest(raw, check)
    c.checkpoint(check)
    return TableFacts(codes, fixtures, whole, operation, full, selected)
