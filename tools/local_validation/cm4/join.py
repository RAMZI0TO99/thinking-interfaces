"""Five original supplied byte inputs, reparsed; no runtime acceptance mode."""
from dataclasses import dataclass

from ..hb1 import common as c
from . import registry, collection, tables, events, terminal

UNAVAILABLE = ('actual_lifecycle_subcase_trace_population', 'original_exception_code_identity',
               'observer_cutoff_custody', 'future_activity_exclusion',
               'final_native_source_restoration_checks', 'capture_eof_tool_return',
               'complete_parent_census', 'owned_process_job_closure')


@dataclass(frozen=True, slots=True)
class JoinFacts:
    descriptor_sha256: str
    collection_sha256: str
    events_sha256: str
    tables_sha256: str
    terminal_sha256: str
    cm2_projection_sha256: str
    cm1_projection_sha256: str
    hb1_projection_sha256: str
    operation: str
    roster_sha256: str
    selection_sha256: str
    source_set: str
    runtime_set: str
    producer_set: str
    event_facts: object
    terminal_facts: object
    unavailable: tuple = UNAVAILABLE

    @property
    def disposition(self):
        return ('SUPPLIED_NEGATIVE_LIFECYCLE' if self.event_facts.negative or self.terminal_facts.refused
                else 'SUPPLIED_LIFECYCLE_CONSISTENT')

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def join_supplied(descriptor_raw, collection_raw, events_raw, tables_raw, terminal_raw, *, check):
    c.checkpoint(check)
    for raw, cap in ((descriptor_raw, 65536), (collection_raw, 1_048_576),
                     (events_raw, 2_097_152), (tables_raw, 1_048_576), (terminal_raw, 65536)):
        c.require(type(raw) is bytes and 0 < len(raw) <= cap, 'immutable input bounds')
    value = c.strict_json(descriptor_raw, 65536, check)
    c.closed(value, ('schema', 'operation', 'roster', 'selection', 'source_set',
                     'runtime_set', 'producer_set', 'collection', 'events', 'tables', 'terminal'))
    c.require(value['schema'] == 'cho51_cm4_supplied_evidence_join_v1', 'join schema')
    c.require(c.bounded_bytes(value, 65536, check) == descriptor_raw, 'canonical join')
    operation = c.uuid_text(value['operation'])
    for key in ('roster', 'selection', 'source_set', 'runtime_set', 'producer_set'):
        c.sha256_text(value[key])
    c.require(value['roster'] == registry.roster_digest(check)
              and value['selection'] == registry.selection_digest(check), 'current target digests')
    hashes = {}
    for name, raw in (('collection', collection_raw), ('events', events_raw),
                      ('tables', tables_raw), ('terminal', terminal_raw)):
        c.checkpoint(check)
        pin = value[name]
        c.closed(pin, ('bytes', 'sha256'))
        c.require(c.integer(pin['bytes'], 1, len(raw)) == len(raw), 'exact raw size')
        c.sha256_text(pin['sha256'])
        actual = events.hash_bytes(raw, check=check)
        c.require(actual == pin['sha256'], 'exact raw digest')
        hashes[name] = actual
    collected = collection.verify_collection(collection_raw, operation, check=check)
    c.require(collected.report_sha256 == hashes['collection'], 'collection join')
    refs = tables.parse_tables(tables_raw, operation, check=check)
    c.require(refs.whole_sha256 == hashes['tables'], 'table join')
    observed = events.verify_events(events_raw, operation, codes=refs.codes, fixtures=refs.fixtures, check=check)
    c.require(observed.whole_sha256 == hashes['events'], 'event join')
    final = terminal.parse_terminal(terminal_raw, operation, check=check)
    c.require(final.whole_sha256 == hashes['terminal'] and final.events_bytes == len(events_raw)
              and final.events_sha256 == hashes['events'], 'terminal whole event join')
    c.require(observed.negative or observed.started == observed.passed == observed.ended == registry.SELECTED_COUNT,
              'complete selected lifecycle')
    descriptor_hash = c.digest(descriptor_raw, check)
    c.checkpoint(check)
    return JoinFacts(descriptor_hash, hashes['collection'], hashes['events'], hashes['tables'],
                     hashes['terminal'], collected.cm2_projection_sha256,
                     collected.cm1_projection_sha256, collected.hb1_projection_sha256,
                     operation, value['roster'], value['selection'], value['source_set'],
                     value['runtime_set'], value['producer_set'], observed, final)


def dispatch(*args, **kwargs):
    raise c.Refusal('REFUSED_UNADMITTED')
