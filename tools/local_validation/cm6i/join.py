"""Independent raw-input join; no native or scientific acceptance."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.context import _check, _json, parse_expected_context
from ..cm6.collection import verify_collection
from .tables import parse_tables
from .events import verify_events, hash_bytes
from .terminal import parse_terminal, _pin

@dataclass(frozen=True, slots=True)
class JoinFacts:
    operation: str
    context: str
    raw_pins: tuple
    collection: object
    events: object
    terminal: object
    @property
    def disposition(self):
        return 'SUPPLIED_NEGATIVE_COHORT' if self.events.negative or self.terminal.refused else 'SUPPLIED_COHORT_CONSISTENT'
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False
    @property
    def independent_adoption_required(self): return True

def join_supplied(raw_join, raw_q, raw_d, raw_c, raw_t, raw_events, raw_terminal, expected_q_pin, expected_d_pin, operation):
    context = parse_expected_context(raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    collected = verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    table = parse_tables(raw_t, raw_q, raw_d, raw_c, expected_q_pin, expected_d_pin, operation)
    observed = verify_events(raw_events, raw_t, raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    terminal = parse_terminal(raw_terminal, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    v = _json(raw_join, 65536)
    c.closed(v, ('schema', 'operation', 'context', 'cohort', 'descriptor', 'collection', 'tables', 'events', 'terminal'))
    c.require(v['schema'] == 'cho51_cm6_supplied_join_v1' and v['operation'] == operation and v['context'] == context.context, 'join context')
    items = (('cohort',raw_q,65536), ('descriptor',raw_d,1048576), ('collection',raw_c,1048576), ('tables',raw_t,1048576), ('events',raw_events,2097152), ('terminal',raw_terminal,65536))
    pins = []
    for name, raw, cap in items:
        expected = _pin(v[name], cap)
        c.require(type(raw) is bytes and 0 < len(raw) <= cap and expected == (len(raw), hash_bytes(raw, check=_check)), 'join raw pin')
        pins.append(expected)
    c.require(tuple(pins[:4]) == terminal.inputs and pins[4] == terminal.events, 'terminal input join')
    return JoinFacts(operation, context.context, tuple(pins), collected, observed, terminal)

def dispatch(*args, **kwargs): raise c.Refusal('REFUSED_UNADMITTED')
