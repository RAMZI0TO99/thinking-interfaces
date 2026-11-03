"""Full current supplied collection before separately pinned historical views."""
from dataclasses import dataclass

from ..hb1 import common as c
from ..cm1.collection import LOADER
from ..cm2 import collection as historical, registry as old
from . import registry


@dataclass(frozen=True, slots=True)
class CollectionFacts:
    report_sha256: str
    cm2_projection_sha256: str
    cm1_projection_sha256: str
    hb1_projection_sha256: str
    operation: str
    roster_sha256: str
    selection_sha256: str
    ids: tuple
    selection: tuple

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def verify_collection(raw, operation, *, check):
    c.uuid_text(operation)
    value = c.strict_json(raw, 1_048_576, check)
    c.closed(value, ('schema', 'operation', 'roster', 'selection', 'complete', 'modules', 'tests'))
    c.require(value['schema'] == 'cho51_cm4_supplied_collection_v1'
              and value['operation'] == operation and value['complete'] is True, 'collection identity')
    c.require(c.bounded_bytes(value, 1_048_576, check) == raw, 'canonical collection')
    full, selected = registry.roster_digest(check), registry.selection_digest(check)
    c.require(value['roster'] == full and value['selection'] == selected, 'current digests')
    ids, modules = registry.expected_ids(), registry.expected_modules()
    c.require(len(ids) == len(set(ids)) == registry.FULL_COUNT
              and len(modules) == registry.MODULE_COUNT, 'literal current roster')
    c.require(type(value['modules']) is list and len(value['modules']) == len(modules), 'module count')
    for row, (name, size, sha) in zip(value['modules'], modules):
        c.checkpoint(check)
        c.closed(row, ('module', 'bytes', 'sha256', 'loader', 'load_tests', 'partial'))
        c.require(row['module'] == name and c.integer(row['bytes'], 1) == size
                  and row['sha256'] == sha, 'exact module pin/order')
        c.require(row['loader'] == LOADER and row['load_tests'] is False
                  and row['partial'] is False, 'loader contract')
    c.require(type(value['tests']) is list and len(value['tests']) == len(ids), 'full case count')
    for row, name in zip(value['tests'], ids):
        c.checkpoint(check)
        c.closed(row, ('id', 'module', 'class_name', 'method_name', 'source_module',
                       'source_qualname', 'skipped', 'deselected', 'expected_failure', 'xfail'))
        module, cls, method = name.rsplit('.', 2)
        c.require(row['id'] == name and row['module'] == module and row['class_name'] == cls
                  and row['method_name'] == method and row['source_module'] == module
                  and row['source_qualname'] == cls + '.' + method, 'exact case/code owner')
        c.require(all(row[k] is False for k in ('skipped', 'deselected', 'expected_failure', 'xfail')),
                  'eligibility flags')
    # Projection is deliberately last: even an unselected new row must pass.
    old_ids = frozenset(old.expected_ids())
    old_modules = frozenset(row[0] for row in old.expected_modules())
    projection = dict(schema='cho51_cm2_supplied_collection_v1', complete=True,
                      modules=[r for r in value['modules'] if r['module'] in old_modules],
                      tests=[r for r in value['tests'] if r['id'] in old_ids])
    checked = historical.verify_collection(c.bounded_bytes(projection, 1_048_576, check), check=check)
    selection = registry.selected_ids()
    c.require(len(selection) == registry.SELECTED_COUNT and set(selection).issubset(ids), 'selection')
    whole = c.digest(raw, check)
    c.checkpoint(check)
    return CollectionFacts(whole, checked.report_sha256, checked.cm1_projection_sha256,
                           checked.hb1_projection_sha256, operation, full, selected, ids, selection)
