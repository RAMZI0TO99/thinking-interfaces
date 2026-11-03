"""Current source inventory; new CM6 tests are held outside fixed Q360."""
from ..cm5 import registry as prior
from ..hb1.common import digest, require

FULL_COUNT = 936
MODULE_COUNT = 41
SELECTED_COUNT = 360
HELD_COUNT = 576
NEW_IDS = (
    'tools.local_validation.cm6.test_collection.CollectionTests.test_auth_flags',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_baseline_full',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_baseline_held',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_complete_exact',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_equal_count_swap',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_facts_frozen',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_h_target_unchanged',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_held_flag_before_projection',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_load_tests',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_loader',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_mapping',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_missing_module',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_missing_test',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_module_pin',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_new_held',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_owner_substitution',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_partial',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_q_count',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_wrong_context',
    'tools.local_validation.cm6.test_collection.CollectionTests.test_wrong_operation',
    'tools.local_validation.cm6.test_context.ContextTests.test_bad_external_d_pin',
    'tools.local_validation.cm6.test_context.ContextTests.test_bad_external_q_pin',
    'tools.local_validation.cm6.test_context.ContextTests.test_bad_set_hash',
    'tools.local_validation.cm6.test_context.ContextTests.test_baseline_counts',
    'tools.local_validation.cm6.test_context.ContextTests.test_baseline_module_pin',
    'tools.local_validation.cm6.test_context.ContextTests.test_bool_count',
    'tools.local_validation.cm6.test_context.ContextTests.test_canonical_anchor_pin',
    'tools.local_validation.cm6.test_context.ContextTests.test_cohort_obligation',
    'tools.local_validation.cm6.test_context.ContextTests.test_count_bound',
    'tools.local_validation.cm6.test_context.ContextTests.test_current_registry_census',
    'tools.local_validation.cm6.test_context.ContextTests.test_dispatch_refuses',
    'tools.local_validation.cm6.test_context.ContextTests.test_held_baseline',
    'tools.local_validation.cm6.test_context.ContextTests.test_held_digest',
    'tools.local_validation.cm6.test_context.ContextTests.test_held_schedule',
    'tools.local_validation.cm6.test_context.ContextTests.test_immutable_facts',
    'tools.local_validation.cm6.test_context.ContextTests.test_missing_baseline',
    'tools.local_validation.cm6.test_context.ContextTests.test_new_held',
    'tools.local_validation.cm6.test_context.ContextTests.test_noncanonical',
    'tools.local_validation.cm6.test_context.ContextTests.test_operation_binding',
    'tools.local_validation.cm6.test_context.ContextTests.test_unknown_field',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_added_debt_held',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_contexts_separate',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_current_collection_pin',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_current_held_count',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_current_report_incomplete',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_descriptor_pins',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_drop_prior_addition',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_execution_unaccepted',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_immutable',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_new_module_addition',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_noop_no_additions',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_noop_preserves_all',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_preserved_held_count',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_collection_pin',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_debt_mutation',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_pin_change',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_promotion',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_rename',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_prior_report_incomplete',
    'tools.local_validation.cm6.test_reconciliation.ReconciliationTests.test_unauthenticated',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm6.test_collection', 3443, '5161b387e08e72ae40fd1366285f427f7538caba4890ac425da56a245a2a2aab'),
    ('tools.local_validation.cm6.test_context', 6858, '86008983805bf8149cea03fac33f3047eefae40ec7998bc3c2cd35ce5b27d70d'),
    ('tools.local_validation.cm6.test_reconciliation', 4359, '717fa6fe42fe90d51653ab58e4fa1dbf8af2cd01e197fa1dfd0c69507c35c0c3'),
)
FULL_DIGEST = '65e9157ccaff54f6f059478bfbce0c94f4cea4c70ab2501621c317a790009f68'
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
    """Positions in full C; these are not Q wire ordinals."""
    selected = frozenset(selected_ids())
    return tuple(i for i, name in enumerate(expected_ids()) if name in selected)


def roster_digest(check):
    value = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(value == FULL_DIGEST, "literal CM6 current source roster")
    return value


def selection_digest(check):
    value = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(value == SELECTION_DIGEST, "literal unchanged CM6 Q360 cohort")
    return value
