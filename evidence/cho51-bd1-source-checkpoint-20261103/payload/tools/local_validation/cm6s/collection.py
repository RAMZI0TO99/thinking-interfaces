"""Full observed collection verification before S projection."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm6.context import _check, _json
from ..cm6.collection import verify_collection
from .context import parse_expected_context_s
from . import registry

@dataclass(frozen=True, slots=True)
class CollectionFacts:
    baseline: object
    context: str
    supplement: tuple
    s_to_c: tuple
    s_view_pin: tuple
    @property
    def authenticated(self): return False
    @property
    def execution_accepted(self): return False
    @property
    def debt_discharged(self): return False
    @property
    def independent_adoption_required(self): return True

def verify_collection_s(raw_c, raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation):
    expected = parse_expected_context_s(raw_q, raw_s, raw_d, raw_e, expected_q_pin, expected_s_pin, expected_d_pin, expected_e_pin, operation)
    baseline = verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    v = _json(raw_c, 1048576)
    tests = {row['id']: row for row in v['tests']}
    modules = {row['module']: row for row in v['modules']}
    owners = sorted({name.rsplit('.', 2)[0] for name in expected.supplement})
    view = dict(schema='cho51_cm6s_collection_view_v1', operation=operation, context=expected.context, baseline_context=expected.baseline.context, supplement=registry.SUPPLEMENT_DIGEST, modules=[modules[n] for n in owners], tests=[tests[n] for n in expected.supplement])
    raw = c.bounded_bytes(view, 1048576, _check)
    positions = {name: i for i, name in enumerate(baseline.ids)}
    return CollectionFacts(baseline, expected.context, expected.supplement, tuple(positions[n] for n in expected.supplement), (len(raw), c.digest(raw, _check)))

