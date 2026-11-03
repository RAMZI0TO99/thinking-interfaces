"""Explicit current source roster; frozen CM2 evidence remains a separate target."""
from ..cm2 import registry as prior
from ..hb1.common import digest, require

NEW_IDS = (
    'tools.local_validation.cm3.test_events.CM3EventTests.test_canonical_json_and_encoding',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_exact_types_and_nullability',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_fixture_ownership_phase_and_reuse',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_hash_above_one_mib_and_checkpoints',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_header_operation_and_roster',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_hidden_lifecycle_and_no_authority',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_minimal_passing_transcript',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_negative_suffix_and_failfast',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_prefix_and_whole_hashes',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_record_line_and_stream_caps',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_skip_then_mixed_cleanup',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_special_outcomes_and_primary_order',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_start_pass_end_and_footer_order',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_subcase_counts_and_ownership',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_trace_128_129_and_unknown_kind',
    'tools.local_validation.cm3.test_events.CM3EventTests.test_trace_groups_and_locations',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_code_pair_bounds_and_duplicates',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_collection_before_event_semantics',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_collection_omission_and_substitution',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_current_roster_is_separate_target',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_descriptor_closed_canonical_and_pins',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_fixture_exact_owner_and_affected_set',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_fixture_slots_phases_and_duplicates',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_frozen_results_and_refusal',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_full_raw_join_and_separate_projections',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_input_bounds_and_immutability',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_negative_join_preserved',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_operation_and_context_types',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_raw_table_schema_and_canonical_order',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_reparse_not_caller_facts',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_table_aggregate_limits',
    'tools.local_validation.cm3.test_join.CM3JoinTests.test_tables_bound_to_events',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm3.test_events', 12914, '894197e79a4bb7ecb053f0c8b05ce515f20008d0b823609d28fba2a1d52155d9'),
    ('tools.local_validation.cm3.test_join', 12308, '74f86379a9e04d097121e3d6bd3148127b8d116a31d197293c1c8c68e1c7e8fe'),
)
FULL_DIGEST = '11b76c3173fdaf6de6ef3e9b4ce71814b423930d7ac75d5c9f0768fa5a6edd56'
SELECTION_DIGEST = '33f075f498b160748883fc3f53f3bed18258db0d706f66d41dd0c4b25024c092'

def expected_ids():
    return tuple(sorted(prior.expected_ids() + NEW_IDS))

def expected_modules():
    return tuple(sorted(prior.expected_modules() + NEW_MODULE_PINS))

def selected_ids():
    return tuple(sorted(prior.selected_ids() + NEW_IDS))

def roster_digest(check):
    value = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(value == FULL_DIGEST, "literal current roster")
    return value

def selection_digest(check):
    value = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(value == SELECTION_DIGEST, "literal current selection")
    return value
