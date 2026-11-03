"""Supplied S140 context; external pins do not authenticate their contents."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.context import _check, _pin, _json, _ids_digest, parse_expected_context
from . import registry

@dataclass(frozen=True, slots=True)
class ContextFacts:
    baseline: object
    context: str
    supplement: tuple
    expected_pin: tuple
    @property
    def operation(self): return self.baseline.operation
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False
    @property
    def independent_adoption_required(self): return True

def parse_expected_context_s(raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation):
    base = parse_expected_context(raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    _pin(raw_s, expected_s_pin, 65536)
    _pin(raw_e, expected_e_pin, 65536)
    c.require(expected_s_pin == registry.S_PIN, 'unsupported supplement pin')
    s = _json(raw_s, 65536)
    c.closed(s, ('schema', 'name', 'count', 'ids', 'ids_sha256'))
    ids = registry.supplement_ids()
    c.require(s['schema'] == 'cho51_cm6s_cohort_v1' and s['name'] == 'CM6-S140-20261103' and type(s['count']) is int and s['count'] == 140 and type(s['ids']) is list and tuple(s['ids']) == ids and s['ids_sha256'] == registry.SUPPLEMENT_DIGEST and _ids_digest(ids) == registry.SUPPLEMENT_DIGEST, 'supplement identity')
    c.require(not set(ids).intersection(base.cohort) and set(ids).issubset(base.ids), 'supplement membership')
    # The complete successor registry is an independently maintained floor, not
    # merely the 876-row floor of the frozen CM6 parser.
    c.require(set(registry.expected_ids()).issubset(base.ids), 'successor identities')
    modules = {n: (size, sha) for n, size, sha in base.modules}
    c.require(all(modules.get(n) == (size, sha) for n, size, sha in registry.expected_modules()), 'successor module pins')
    e = _json(raw_e, 65536)
    c.closed(e, ('schema', 'profile', 'anchor', 'supplement', 'descriptor', 'source_set', 'runtime_set', 'producer_set'))
    c.require(e['schema'] == 'cho51_cm6s_expected_v1' and e['profile'] == 'CM6-S140-20261103', 'expected profile')
    for key, pin in (('anchor', expected_q_pin), ('supplement', expected_s_pin), ('descriptor', expected_d_pin)):
        c.closed(e[key], ('bytes', 'sha256'))
        c.require(type(e[key]['bytes']) is int and e[key] == dict(bytes=pin[0], sha256=pin[1]), 'expected pin join')
    c.require((e['source_set'], e['runtime_set'], e['producer_set']) == (base.source_set, base.runtime_set, base.producer_set), 'expected manifest references')
    k = dict(domain='cho51_cm6s_context_v1', operation=operation, anchor=base.cohort_digest, supplement=registry.SUPPLEMENT_DIGEST, census=base.census_digest, expected=dict(bytes=expected_e_pin[0], sha256=expected_e_pin[1]))
    context = c.digest(c.bounded_bytes(k, 1048576, _check), _check)
    return ContextFacts(base, context, ids, expected_e_pin)

def dispatch(*args, **kwargs): raise c.Refusal('REFUSED_UNADMITTED')
