"""Explicit CM5 source census only; producer retains frozen CM4 target."""
from ..cm4 import registry as prior
from ..hb1.common import digest, require

FULL_COUNT = 876
MODULE_COUNT = 38
SELECTED_COUNT = 360
NEW_IDS = (
    'tools.local_validation.cm5.test_producer.ProducerTests.test_duration_requires_cleanup',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_end_requires_outcome',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_failfast_rejects_new_case',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_failfast_rejects_new_subcase',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_fixture_duplicate_refused',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_fixture_setup_negative',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_interval_rejects_parent_failure',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_invalid_trace_rejected_without_output',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_negative_failure_and_trace',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_normal_all_selected_and_independent_parsers',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_skip_then_cleanup_failures',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_skip_zero_trace',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_subfail_no_fabricated_primary',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_subpass_closed_interval',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_trace_128_complete_group',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_trace_129_rejected',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_wrong_selection_rejected',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_xfail_forbids_later_failure',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_xfail_trace_after_cleanup',
    'tools.local_validation.cm5.test_producer.ProducerTests.test_xpass_after_cleanup',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_65535th_representable',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_65536th_invalidates_accounting',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_detached_entry_does_not_mutate_snapshot',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_empty_and_partial_have_no_terminal',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_encoder_exception_settles_without_commit',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_footer_4096_boundary',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_group_reserves_footer_record',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_hash_exception_settles_without_commit',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_invalid_command_settled',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_invalid_fault_settled',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_post_finish_refusal_has_valid_terminal',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_post_footer_entry_counted',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_post_refusal_preserves_complete_group',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_pre_refusal_preserves_prefix',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_reentry_post_retains_output',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_reentry_pre_first_observed_two',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_runtime_dispatch_and_constructor_refuse',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_seal_active_latches',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_seal_is_immutable_and_repeated',
    'tools.local_validation.cm5.test_refusal.RefusalTests.test_sticky_refusal_counts_later_attempt',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm5.test_producer', 7790, 'af4d8555ad691c8900d7ea19c7a299e969830d5a1a43bfaec3e0ac29667a570a'),
    ('tools.local_validation.cm5.test_refusal', 8749, '60ba08f9457b8f47157bffd7fdc1baaa2c2a1215d582c6fc41ca54cc88dbd262'),
)
FULL_DIGEST = 'f6a3081e3becb650c5485cd70121a644ebdcebde278499fe85a385764b317739'
SELECTION_DIGEST = '321e076ba18c3bb413d5c7f70f34b03e3780bce1712e5ff4f03fd7f6e4b60a08'

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
    require(value == FULL_DIGEST, "literal CM5 source roster")
    return value


def selection_digest(check):
    value = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(value == SELECTION_DIGEST, "literal CM5 source selection")
    return value
