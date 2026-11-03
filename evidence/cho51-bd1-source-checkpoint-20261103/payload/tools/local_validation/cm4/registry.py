"""Explicit CM4 current roster; frozen predecessors keep their literal pins."""
from ..cm3 import registry as prior
from ..hb1.common import digest, require

FULL_COUNT = 836
MODULE_COUNT = 36
SELECTED_COUNT = 320
NEW_IDS = (
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_all_five_input_caps_and_missing_data',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_checkpoints_refuse_and_do_not_create_authority',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_closed_canonical_json_and_exact_input_types',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_code_pair_limits_and_table_aggregate_caps',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_collection_context_and_historical_roster_refuse',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_collection_module_pins_loader_and_code_owner',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_collection_omissions_duplicates_and_excluded_rows',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_current_fixture_owner_and_affected_conservation',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_current_roster_and_conditional_budget_successor',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_frozen_facts_reparse_and_dispatch_refusal',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_full_collection_and_distinct_projections',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_full_collection_precedes_event_semantics',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_join_descriptor_and_raw_substitution',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_negative_events_and_late_refusal_cannot_be_erased',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_raw_join_pins_and_distinct_projections',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_table_slot_phase_context_and_canonical_rules',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_terminal_complete_and_refused_snapshots',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_terminal_counter_algebra_and_latch_types',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_terminal_must_pin_exact_whole_event_bytes',
    'tools.local_validation.cm4.test_contracts.CM4ContractTests.test_terminal_schema_context_and_event_pin',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_chunked_hash_and_final_checkpoints',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_cleanup_duration_and_primary_order',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_closed_canonical_encoding',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_closed_subcase_triplets',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_complete_current_lifecycle',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_context_sequence_and_closed_schema',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_duration_required_and_integer_range',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_exact_primitive_types_and_null_fields',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_failed_subcase_exit_then_cleanup_failures',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_fixture_slots_phases_and_late_negation',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_full_4096_record_boundary_and_4097_refusal',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_immutable_provisional_facts_and_dispatch',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_skip_and_mixed_cleanup',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_sticky_negative_exact_suffix',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_subcase_missing_duplicate_nested_and_owner',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_suite_closure_and_final_claim_order',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_trace_128_positive_129_refused',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_trace_owner_location_and_null_rejection',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_whole_prefix_hash_and_footer_integrity',
    'tools.local_validation.cm4.test_events.CM4EventTests.test_xfail_xpass_and_exception_kinds',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm4.test_events', 13802, 'c5cc67ed5df83e8fa71edbb913b3d216efe49ebfb550d99481cad3c18d621dfa'),
    ('tools.local_validation.cm4.test_contracts', 18768, 'db5205965ce9f503c1c1abc2fe4ebea3f03617ce12e37e59d19dd18da9dc6dd2'),
)
FULL_DIGEST = '39572716ef171a65c2e4074c700f68e45d6384f61d0cffa886b34697054ed498'
SELECTION_DIGEST = '4df0f69faf6d83032c33eca43e82382269e125eb1a2436a94694cd7474d5af39'


def expected_ids():
    return tuple(sorted(prior.expected_ids() + NEW_IDS))


def expected_modules():
    return tuple(sorted(prior.expected_modules() + NEW_MODULE_PINS))


def selected_ids():
    return tuple(sorted(prior.selected_ids() + NEW_IDS))


def selected_ordinals():
    ids = expected_ids()
    selected = frozenset(selected_ids())
    return tuple(i for i, name in enumerate(ids) if name in selected)


def roster_digest(check):
    value = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(value == FULL_DIGEST, "literal current roster")
    return value


def selection_digest(check):
    value = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(value == SELECTION_DIGEST, "literal current selection")
    return value
