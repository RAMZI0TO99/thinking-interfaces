"""Verify the full supplied current census before constructing either view."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm1.collection import LOADER
from ..cm4 import collection as cm4, registry as historical
from .context import CAP, _check, _json, parse_expected_context

@dataclass(frozen=True, slots=True)
class CollectionFacts:
    operation: str
    context: str
    collection_pin: tuple
    q_view_pin: tuple
    h_pin: tuple
    cm2_sha256: str
    cm1_sha256: str
    hb1_sha256: str
    ids: tuple
    cohort: tuple
    held: tuple
    q_to_c: tuple
    modules: tuple
    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False

    @property
    def debt_discharged(self): return False

    @property
    def independent_adoption_required(self): return True

def _raw(value): return c.bounded_bytes(value, CAP, _check)
def _rawpin(raw): return (len(raw), c.digest(raw, _check))

def verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation):
    context = parse_expected_context(raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
    value = _json(raw_c, CAP)
    c.closed(value, ('schema', 'operation', 'context', 'complete', 'modules', 'tests'))
    c.require(value['schema'] == 'cho51_cm6_supplied_collection_v1' and value['operation'] == operation and value['context'] == context.context and value['complete'] is True, 'collection identity')
    c.require(type(value['modules']) is list and len(value['modules']) == len(context.modules) and type(value['tests']) is list and len(value['tests']) == len(context.ids), 'full collection size')
    for row, (name, size, sha) in zip(value['modules'], context.modules):
        c.closed(row, ('module', 'bytes', 'sha256', 'loader', 'load_tests', 'partial'))
        c.require(row['module'] == name and c.integer(row['bytes'], 1) == size and row['sha256'] == sha and row['loader'] == LOADER and row['load_tests'] is False and row['partial'] is False, 'module report')
    for row, name in zip(value['tests'], context.ids):
        c.closed(row, ('id', 'module', 'class_name', 'method_name', 'source_module', 'source_qualname', 'skipped', 'deselected', 'expected_failure', 'xfail'))
        module, cls, method = name.rsplit('.', 2)
        c.require(row['id'] == name and row['module'] == module and row['class_name'] == cls and row['method_name'] == method and row['source_module'] == module and row['source_qualname'] == cls + '.' + method and all(row[k] is False for k in ('skipped', 'deselected', 'expected_failure', 'xfail')), 'test report')
    by_id = {row['id']: row for row in value['tests']}; by_module = {row['module']: row for row in value['modules']}
    q_modules = sorted({name.rsplit('.', 2)[0] for name in context.cohort})
    q_view = dict(schema='cho51_cm6_cohort_view_v1', operation=operation, context=context.context, cohort=context.cohort_digest, modules=[by_module[n] for n in q_modules], tests=[by_id[n] for n in context.cohort])
    q_raw = _raw(q_view)
    h_ids = historical.expected_ids(); h_modules = historical.expected_modules()
    h_view = dict(schema='cho51_cm4_supplied_collection_v1', operation=operation, roster=historical.roster_digest(_check), selection=historical.selection_digest(_check), complete=True, modules=[by_module[n] for n, _, _ in h_modules], tests=[by_id[n] for n in h_ids])
    h_raw = _raw(h_view)
    h = cm4.verify_collection(h_raw, operation, check=_check)
    positions = {name: i for i, name in enumerate(context.ids)}
    return CollectionFacts(operation, context.context, _rawpin(raw_c), _rawpin(q_raw), _rawpin(h_raw), h.cm2_projection_sha256, h.cm1_projection_sha256, h.hb1_projection_sha256, context.ids, context.cohort, tuple(row for row in context.obligations if row[1] == 'HELD'), tuple(positions[n] for n in context.cohort), context.modules)

