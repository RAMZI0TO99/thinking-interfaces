"""Independent raw-input join; no native or scientific acceptance."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.context import _check, _json
from .context import parse_expected_context_s
from .collection import verify_collection_s
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
        return 'SUPPLIED_NEGATIVE_SUPPLEMENT' if self.events.negative or self.terminal.refused else 'SUPPLIED_SUPPLEMENT_CONSISTENT'
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False
    @property
    def independent_adoption_required(self): return True

def join_supplied(raw_join, raw_q, raw_s, raw_d, raw_e, raw_c, raw_t, raw_events, raw_terminal, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation):
    context = parse_expected_context_s(raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    collected = verify_collection_s(raw_c, raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    table = parse_tables(raw_t, raw_q, raw_s, raw_d, raw_e, raw_c, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    observed = verify_events(raw_events, raw_t, raw_c, raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    terminal = parse_terminal(raw_terminal, raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    v = _json(raw_join, 65536)
    c.closed(v, ('schema', 'operation', 'context', 'anchor', 'supplement', 'descriptor', 'expected', 'collection', 'tables', 'events', 'terminal'))
    c.require(v['schema'] == 'cho51_cm6s_supplied_join_v1' and v['operation'] == operation and v['context'] == context.context, 'join context')
    items = (('anchor',raw_q,65536), ('supplement',raw_s,65536), ('descriptor',raw_d,1048576), ('expected',raw_e,65536), ('collection',raw_c,1048576), ('tables',raw_t,1048576), ('events',raw_events,2097152), ('terminal',raw_terminal,65536))
    pins = []
    for name, raw, cap in items:
        expected = _pin(v[name], cap)
        c.require(type(raw) is bytes and 0 < len(raw) <= cap and expected == (len(raw), hash_bytes(raw, check=_check)), 'join raw pin')
        pins.append(expected)
    c.require(tuple(pins[:6]) == terminal.inputs and pins[6] == terminal.events, 'terminal input join')
    return JoinFacts(operation, context.context, tuple(pins), collected, observed, terminal)

def dispatch(*args, **kwargs): raise c.Refusal('REFUSED_UNADMITTED')

