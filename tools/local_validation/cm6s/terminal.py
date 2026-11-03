"""Independent supplied terminal parser; never a native cutoff witness."""
from dataclasses import dataclass
from .context import parse_expected_context_s
from ..hb1 import common as c
from ..cm6.context import _check, _json

@dataclass(frozen=True, slots=True)
class TerminalFacts:
    raw_pin: tuple
    operation: str
    context: str
    inputs: tuple
    events: tuple
    attempts: int
    settled: int
    post_footer_attempts: int
    first_refusal: object
    refused: bool
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False

def _pin(row, cap):
    c.closed(row, ('bytes', 'sha256'))
    return (c.integer(row['bytes'], 1, cap), c.sha256_text(row['sha256']))

def parse_terminal(raw_terminal, raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation):
    expected = parse_expected_context_s(raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    v = _json(raw_terminal, 65536)
    c.closed(v, ('schema', 'operation', 'context', 'inputs', 'events', 'boundary', 'attempts', 'settled', 'in_flight', 'post_footer_attempts', 'first_refusal', 'refused', 'producer_detached'))
    c.require(v['schema'] == 'cho51_cm6s_supplied_terminal_v1' and v['operation'] == operation and v['context'] == expected.context, 'terminal context')
    c.closed(v['inputs'], ('anchor', 'supplement', 'descriptor', 'expected', 'collection', 'tables'))
    inputs = tuple(_pin(v['inputs'][n], cap) for n, cap in (('anchor',65536), ('supplement',65536), ('descriptor',1048576), ('expected',65536), ('collection',1048576), ('tables',1048576)))
    c.require(inputs[:4] == (expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin), 'terminal expected inputs')
    event_pin = _pin(v['events'],2097152)
    c.require(v['boundary'] == 'SUPPLIED_SEALED_CHANNEL_SNAPSHOT', 'boundary')
    attempts = c.integer(v['attempts'], 1, 65535); settled = c.integer(v['settled'], 0, 65535)
    active = c.integer(v['in_flight'], 0, 65535); late = c.integer(v['post_footer_attempts'], 0, attempts)
    first = v['first_refusal']
    if first is not None: c.integer(first, 1, attempts)
    refused = v['refused']
    c.require(type(refused) is bool and refused == (first is not None) and (not late or refused), 'latch')
    c.require(attempts == settled + active and active == 0 and v['producer_detached'] is True, 'accounting')
    return TerminalFacts((len(raw_terminal), c.digest(raw_terminal, _check)), operation, expected.context, inputs, event_pin, attempts, settled, late, first, refused)

