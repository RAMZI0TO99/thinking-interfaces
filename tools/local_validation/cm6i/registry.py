"""CM6 integration source census; Q360 unchanged and every new test held."""
from ..cm6 import registry as prior
from ..hb1.common import digest, require

FULL_COUNT = 1016
MODULE_COUNT = 45
SELECTED_COUNT = 360
HELD_COUNT = 656
NEW_IDS = (
    'tools.local_validation.cm6i.test_events.EventTests.test_bad_collection_precedes_events',
    'tools.local_validation.cm6i.test_events.EventTests.test_bad_tables',
    'tools.local_validation.cm6i.test_events.EventTests.test_bool_sequence',
    'tools.local_validation.cm6i.test_events.EventTests.test_context',
    'tools.local_validation.cm6i.test_events.EventTests.test_dispatch_refusal',
    'tools.local_validation.cm6i.test_events.EventTests.test_empty_stream',
    'tools.local_validation.cm6i.test_events.EventTests.test_extra_field',
    'tools.local_validation.cm6i.test_events.EventTests.test_header_count',
    'tools.local_validation.cm6i.test_events.EventTests.test_header_kind',
    'tools.local_validation.cm6i.test_events.EventTests.test_header_owner',
    'tools.local_validation.cm6i.test_events.EventTests.test_mutable_stream',
    'tools.local_validation.cm6i.test_events.EventTests.test_negative_disposition',
    'tools.local_validation.cm6i.test_events.EventTests.test_negative_suffix',
    'tools.local_validation.cm6i.test_events.EventTests.test_noncanonical',
    'tools.local_validation.cm6i.test_events.EventTests.test_operation',
    'tools.local_validation.cm6i.test_events.EventTests.test_pass_count',
    'tools.local_validation.cm6i.test_events.EventTests.test_schema',
    'tools.local_validation.cm6i.test_events.EventTests.test_sequence',
    'tools.local_validation.cm6i.test_events.EventTests.test_truncated_footer',
    'tools.local_validation.cm6i.test_events.EventTests.test_whole_digest',
    'tools.local_validation.cm6i.test_join.JoinTests.test_cohort_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_collection_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_complete',
    'tools.local_validation.cm6i.test_join.JoinTests.test_context',
    'tools.local_validation.cm6i.test_join.JoinTests.test_descriptor_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_events_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_extra_field',
    'tools.local_validation.cm6i.test_join.JoinTests.test_held_debt',
    'tools.local_validation.cm6i.test_join.JoinTests.test_incomplete_event',
    'tools.local_validation.cm6i.test_join.JoinTests.test_negative',
    'tools.local_validation.cm6i.test_join.JoinTests.test_negative_suffix_distinct',
    'tools.local_validation.cm6i.test_join.JoinTests.test_noncanonical',
    'tools.local_validation.cm6i.test_join.JoinTests.test_operation',
    'tools.local_validation.cm6i.test_join.JoinTests.test_runtime_refusal',
    'tools.local_validation.cm6i.test_join.JoinTests.test_schema',
    'tools.local_validation.cm6i.test_join.JoinTests.test_table_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_table_substitution',
    'tools.local_validation.cm6i.test_join.JoinTests.test_terminal_pin',
    'tools.local_validation.cm6i.test_join.JoinTests.test_terminal_substitution',
    'tools.local_validation.cm6i.test_join.JoinTests.test_unauthenticated',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_begin_emits_two',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_cleanup_required',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_constructor_bad_collection',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_constructor_bad_tables',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_full_pass_count',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_invalid_trace_is_atomic',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_negative_lifecycle',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_nested_post_settled',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_nested_postfooter_accounted',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_nested_pre_settled',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_out_of_range_ordinal',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_partial_seal_has_no_terminal',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_post_refusal',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_pre_refusal',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_runtime_refuses',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_seal_is_stable',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_secondary_reject_helper_failure',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_secondary_settle_failure',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_subcase_interval',
    'tools.local_validation.cm6i.test_producer.ProducerTests.test_wrong_ordinal',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_attempt_overflow',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_bad_input_shape',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_bool_attempts',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_boundary',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_context',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_detached',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_events_pin',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_extra_field',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_first_refusal',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_inflight',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_inputs_pin',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_latch',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_late_without_refusal',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_noncanonical',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_operation',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_schema',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_terminal_complete',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_unauthenticated',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_unsettled',
    'tools.local_validation.cm6i.test_terminal.TerminalTests.test_wrong_event_pin_shape',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm6i.test_events', 5451, '993c3f72a85991eda5e5c1793140e4665c85d0d9e025d5afe1ae97b0090b4bea'),
    ('tools.local_validation.cm6i.test_join', 3520, 'd14d57aa676c039564a9ddb866951a3b092cde83d7e61e574ddf5726687fa9c1'),
    ('tools.local_validation.cm6i.test_producer', 4207, 'f43c116a7e9557e516b816ef62dcc8cd255530ae725ea8c0f26a4b9db9df6e2a'),
    ('tools.local_validation.cm6i.test_terminal', 2918, 'cac58b6e4149d317c6dea2c949dc522fb05ef5ef947a7415f333040b01514d1f'),
)
FULL_DIGEST = '34e9e6957665ac22836969dc25345e6c69e6167710a23e1171bdd6658f02f9e2'
SELECTION_DIGEST = '321e076ba18c3bb413d5c7f70f34b03e3780bce1712e5ff4f03fd7f6e4b60a08'

def expected_ids():
    return tuple(sorted(prior.expected_ids() + NEW_IDS))


def expected_modules():
    return tuple(sorted(prior.expected_modules() + NEW_MODULE_PINS))


def selected_ids():
    return prior.selected_ids()


def held_ids():
    selected = frozenset(selected_ids())
    return tuple(name for name in expected_ids() if name not in selected)


def selected_ordinals():
    """Full-C positions, not Q wire indices."""
    selected = frozenset(selected_ids())
    return tuple(i for i, name in enumerate(expected_ids()) if name in selected)


def roster_digest(check):
    value = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(value == FULL_DIGEST, "literal CM6 integration source roster")
    return value


def selection_digest(check):
    value = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(value == SELECTION_DIGEST, "unchanged CM6 Q360")
    return value
