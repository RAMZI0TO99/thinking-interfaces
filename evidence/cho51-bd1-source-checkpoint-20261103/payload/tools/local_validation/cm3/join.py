"""Reparse and join supplied original bytes; never authenticate a runtime."""
from dataclasses import dataclass

from ..hb1 import common as c
from ..cm2 import collection, registry as target
from . import events, tables

UNAVAILABLE = ('method_cleanup', 'duration_order', 'suite_closure',
               'final_producer_refusal', 'actual_subcase_population',
               'actual_exception_type_and_trace', 'native_guard',
               'source_runtime_transport_custody', 'original_same_operation_collection')


@dataclass(frozen=True, slots=True)
class JoinFacts:
    descriptor_sha256: str
    collection_sha256: str
    events_sha256: str
    tables_sha256: str
    cm1_projection_sha256: str
    hb1_projection_sha256: str
    operation: str
    roster_sha256: str
    selection_sha256: str
    source_set: str
    runtime_set: str
    producer_set: str
    event_facts: object
    unavailable: tuple = UNAVAILABLE

    @property
    def disposition(self): return self.event_facts.disposition

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def join_supplied(descriptor_raw, collection_raw, events_raw, tables_raw, *, check):
    """Fixed historical CM2 764/248 target, not a current-checkout collector."""
    c.checkpoint(check)
    for raw, cap in ((descriptor_raw, 65536), (collection_raw, 1_048_576),
                     (events_raw, 2_097_152), (tables_raw, 1_048_576)):
        c.require(type(raw) is bytes and 0 < len(raw) <= cap, 'immutable input bounds')
    value = c.strict_json(descriptor_raw, 65536, check)
    c.closed(value, ('schema', 'operation', 'roster', 'selection', 'source_set',
                     'runtime_set', 'producer_set', 'collection', 'events', 'tables'))
    c.require(value['schema'] == 'cho51_cm3_supplied_evidence_join_v1', 'join schema')
    c.require(c.bounded_bytes(value, 65536, check) == descriptor_raw, 'canonical join')
    operation = c.uuid_text(value['operation'])
    for key in ('roster', 'selection', 'source_set', 'runtime_set', 'producer_set'):
        c.sha256_text(value[key])
    c.require(value['roster'] == target.roster_digest(check)
              and value['selection'] == target.selection_digest(check), 'frozen target digests')
    raw_hashes = {}
    for name, raw in (('collection', collection_raw), ('events', events_raw),
                      ('tables', tables_raw)):
        c.checkpoint(check)
        pin = value[name]
        c.closed(pin, ('bytes', 'sha256'))
        c.require(c.integer(pin['bytes'], 1, len(raw)) == len(raw), 'exact raw size')
        c.sha256_text(pin['sha256'])
        actual = events.hash_bytes(raw, check=check)
        c.require(actual == pin['sha256'], 'exact raw digest')
        raw_hashes[name] = actual
    # Full raw collection must pass before table/event views. The frozen parser
    # performs full 764 rows before its separate 732 and 700 projections.
    collected = collection.verify_collection(collection_raw, check=check)
    c.require(collected.report_sha256 == raw_hashes['collection']
              and collected.roster_sha256 == value['roster']
              and collected.selection_sha256 == value['selection'], 'collection join')
    references = tables.parse_tables(tables_raw, check=check)
    c.require(references.whole_sha256 == raw_hashes['tables'], 'table join')
    observed = events.verify_events(events_raw, operation, codes=references.codes,
                                    fixtures=references.fixtures, check=check)
    c.require(observed.whole_sha256 == raw_hashes['events'], 'event join')
    c.checkpoint(check)
    return JoinFacts(c.digest(descriptor_raw, check), raw_hashes['collection'],
                     raw_hashes['events'], raw_hashes['tables'],
                     collected.cm1_projection_sha256, collected.hb1_projection_sha256,
                     operation, value['roster'], value['selection'], value['source_set'],
                     value['runtime_set'], value['producer_set'], observed)


def dispatch(*args, **kwargs):
    raise c.Refusal('REFUSED_UNADMITTED')
