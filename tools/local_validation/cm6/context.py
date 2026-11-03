"""Externally pinned, immutable expected cohort and census context."""
from dataclasses import dataclass
import re
from ..hb1 import common as c
from ..cm5 import registry as baseline

Q_PIN = (36161, 'e654b35a3c8a969d60d8f602f75f967bdf0711b4fb71491d0d0094673ac40dde')
Q_DIGEST = '321e076ba18c3bb413d5c7f70f34b03e3780bce1712e5ff4f03fd7f6e4b60a08'
CAP = 1048576
_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\Z')

def _check(): return True

def _pin(raw, pin, cap):
    c.require(type(pin) is tuple and len(pin) == 2, 'pin tuple')
    c.integer(pin[0], 1, cap)
    c.sha256_text(pin[1])
    c.require(type(raw) is bytes and len(raw) == pin[0] and c.digest(raw, _check) == pin[1], 'raw pin')

def _json(raw, cap):
    value = c.strict_json(raw, cap, _check)
    c.require(c.bounded_bytes(value, cap, _check) == raw, 'canonical bytes')
    return value

def _ids_digest(ids): return c.digest(('\n'.join(ids) + '\n').encode('ascii'), _check)

def _name(value, limit):
    c.require(type(value) is str and len(value) <= limit and _NAME.fullmatch(value) is not None, 'name')
    return value

def _identity(value):
    _name(value, 192)
    parts = value.rsplit('.', 2)
    c.require(len(parts) == 3 and parts[2].startswith('test_'), 'identity')
    _name(parts[0], 128)
    return parts[0]

@dataclass(frozen=True, slots=True)
class ContextFacts:
    operation: str
    context: str
    cohort_pin: tuple
    descriptor_pin: tuple
    cohort_digest: str
    census_digest: str
    ids: tuple
    modules: tuple
    cohort: tuple
    obligations: tuple
    source_set: str
    runtime_set: str
    producer_set: str
    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False

    @property
    def debt_discharged(self): return False

    @property
    def independent_adoption_required(self): return True

def parse_expected_context(raw_q, raw_d, expected_q_pin, expected_d_pin, operation):
    _pin(raw_q, expected_q_pin, 65536)
    _pin(raw_d, expected_d_pin, CAP)
    c.uuid_text(operation)
    c.require(expected_q_pin == Q_PIN, 'unsupported cohort pin')
    q = _json(raw_q, 65536)
    c.closed(q, ('schema', 'name', 'count', 'ids', 'ids_sha256'))
    c.require(q['schema'] == 'cho51_cm6_qualification_cohort_v1' and q['name'] == 'CM6-Q360-20261103', 'cohort profile')
    c.require(c.integer(q['count'], 1, 360) == 360 and type(q['ids']) is list, 'cohort count')
    selected = tuple(q['ids'])
    c.require(selected == baseline.selected_ids() and q['ids_sha256'] == Q_DIGEST and _ids_digest(selected) == Q_DIGEST, 'cohort identity')
    d = _json(raw_d, CAP)
    c.closed(d, ('schema', 'cohort', 'census', 'modules', 'tests', 'source_set', 'runtime_set', 'producer_set'))
    c.require(d['schema'] == 'cho51_cm6_expected_census_v1', 'descriptor schema')
    c.closed(d['cohort'], ('name', 'count', 'ids_sha256', 'bytes', 'sha256'))
    c.require(d['cohort'] == dict(name=q['name'], count=360, ids_sha256=Q_DIGEST, bytes=Q_PIN[0], sha256=Q_PIN[1]) and type(d['cohort']['count']) is int and type(d['cohort']['bytes']) is int, 'descriptor cohort')
    census = d['census']; c.closed(census, ('count', 'module_count', 'ids_sha256'))
    count = c.integer(census['count'], 876, 4096); module_count = c.integer(census['module_count'], 38, 256)
    c.sha256_text(census['ids_sha256'])
    c.require(type(d['modules']) is list and len(d['modules']) == module_count and type(d['tests']) is list and len(d['tests']) == count, 'census count')
    modules = []
    for row in d['modules']:
        c.closed(row, ('module', 'bytes', 'sha256'))
        modules.append((_name(row['module'], 128), c.integer(row['bytes'], 1), c.sha256_text(row['sha256'])))
    c.require(tuple(modules) == tuple(sorted(modules)) and len({m[0] for m in modules}) == module_count, 'module order')
    base_ids = frozenset(baseline.expected_ids()); base_modules = dict((n, (s, h)) for n, s, h in baseline.expected_modules())
    current_modules = dict((n, (s, h)) for n, s, h in modules)
    c.require(len(base_ids) == 876 and len(base_modules) == 38 and all(current_modules.get(n) == p for n, p in base_modules.items()), 'baseline modules')
    selected_set = frozenset(selected); ids = []; obligations = []; owners = set()
    for row in d['tests']:
        c.closed(row, ('id', 'schedule', 'obligation'))
        name = row['id']; owner = _identity(name); owners.add(owner); ids.append(name)
        if name in selected_set:
            c.require(row['schedule'] == 'COHORT' and row['obligation'] is None, 'cohort schedule')
            obligations.append((name, 'COHORT', None, None))
        else:
            c.require(row['schedule'] == 'HELD', 'held schedule')
            debt = row['obligation']; c.closed(debt, ('kind', 'id_sha256'))
            kind = 'BASELINE_HELD' if name in base_ids else 'NEW_TEST_UNQUALIFIED'
            c.require(debt['kind'] == kind and debt['id_sha256'] == c.digest(name.encode('ascii'), _check), 'held debt')
            if name not in base_ids: c.require(owner not in base_modules, 'new test module')
            obligations.append((name, 'HELD', kind, debt['id_sha256']))
    ids = tuple(ids)
    c.require(ids == tuple(sorted(set(ids))) and base_ids.issubset(ids) and selected_set.issubset(ids), 'census identities')
    c.require(owners == set(current_modules) and _ids_digest(ids) == census['ids_sha256'], 'census digest/owners')
    for key in ('source_set', 'runtime_set', 'producer_set'): c.sha256_text(d[key])
    k = dict(domain='cho51_cm6_context_v1', operation=operation, cohort=Q_DIGEST, census=census['ids_sha256'], descriptor=dict(bytes=expected_d_pin[0], sha256=expected_d_pin[1]))
    context = c.digest(c.bounded_bytes(k, CAP, _check), _check)
    return ContextFacts(operation, context, expected_q_pin, expected_d_pin, Q_DIGEST, census['ids_sha256'], ids, tuple(modules), selected, tuple(obligations), d['source_set'], d['runtime_set'], d['producer_set'])

def runtime_dispatch(*args, **kwargs):
    raise c.Refusal('runtime dispatch unavailable')

