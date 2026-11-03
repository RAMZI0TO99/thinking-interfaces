"""Independent parsing of a supplied terminal snapshot, never a live cutoff."""
from dataclasses import dataclass

from ..hb1 import common as c
from . import registry


@dataclass(frozen=True, slots=True)
class TerminalFacts:
    whole_sha256: str
    operation: str
    roster_sha256: str
    selection_sha256: str
    events_bytes: int
    events_sha256: str
    attempts: int
    settled: int
    post_footer_attempts: int
    first_refusal: object
    refused: bool

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def parse_terminal(raw, operation, *, check):
    c.uuid_text(operation)
    value = c.strict_json(raw, 65536, check)
    c.closed(value, ('schema', 'operation', 'roster', 'selection', 'events', 'boundary',
                     'attempts', 'settled', 'in_flight', 'post_footer_attempts',
                     'first_refusal', 'refused', 'producer_detached'))
    c.require(value['schema'] == 'cho51_cm4_supplied_terminal_v1'
              and value['operation'] == operation, 'terminal identity')
    c.require(c.bounded_bytes(value, 65536, check) == raw, 'canonical terminal')
    full, selected = registry.roster_digest(check), registry.selection_digest(check)
    c.require(value['roster'] == full and value['selection'] == selected, 'terminal context')
    c.closed(value['events'], ('bytes', 'sha256'))
    size = c.integer(value['events']['bytes'], 1, 2_097_152)
    digest = c.sha256_text(value['events']['sha256'])
    c.require(value['boundary'] == 'SUPPLIED_SEALED_CHANNEL_SNAPSHOT', 'supplied boundary')
    attempts = c.integer(value['attempts'], 1, 65535)
    settled = c.integer(value['settled'], 0, 65535)
    active = c.integer(value['in_flight'], 0, 65535)
    late = c.integer(value['post_footer_attempts'], 0, attempts)
    c.require(attempts == settled + active, 'attempt accounting')
    first = value['first_refusal']
    if first is not None:
        c.integer(first, 1, attempts)
    refused = value['refused']
    c.require(type(refused) is bool and refused == (first is not None), 'refusal latch')
    c.require(not late or refused, 'late callback refusal')
    c.require(active == 0 and settled == attempts and value['producer_detached'] is True,
              'complete supplied snapshot')
    whole = c.digest(raw, check)
    c.checkpoint(check)
    return TerminalFacts(whole, operation, full, selected, size, digest,
                         attempts, settled, late, first, refused)
