"""Static held PC1 extension of the frozen CM6S census."""
from ..cm6s import registry as prior
from ..hb1.common import digest, require

FULL_COUNT = 1121
MODULE_COUNT = 51
SELECTED_COUNT = 360
HELD_COUNT = 761
FULL_DIGEST = '8444740f2a60ac96f1b834db1b0ed0b1d5a39787cd181679a57bf31ca466720e'
NEW_IDS = (
    'tools.local_validation.pc1.test_join.JoinTests.test_algebra',
    'tools.local_validation.pc1.test_join.JoinTests.test_bound_activity',
    'tools.local_validation.pc1.test_join.JoinTests.test_bound_events',
    'tools.local_validation.pc1.test_join.JoinTests.test_bound_fault_allowed',
    'tools.local_validation.pc1.test_join.JoinTests.test_capture_alternate_binding',
    'tools.local_validation.pc1.test_join.JoinTests.test_capture_counter_bool',
    'tools.local_validation.pc1.test_join.JoinTests.test_capture_operation',
    'tools.local_validation.pc1.test_join.JoinTests.test_complete_missing_eof',
    'tools.local_validation.pc1.test_join.JoinTests.test_cutoff_independent',
    'tools.local_validation.pc1.test_join.JoinTests.test_dispatch_refused',
    'tools.local_validation.pc1.test_join.JoinTests.test_drained_pending',
    'tools.local_validation.pc1.test_join.JoinTests.test_empty_events_digest',
    'tools.local_validation.pc1.test_join.JoinTests.test_empty_stream_digest',
    'tools.local_validation.pc1.test_join.JoinTests.test_eof_wrong_type',
    'tools.local_validation.pc1.test_join.JoinTests.test_expected_binding',
    'tools.local_validation.pc1.test_join.JoinTests.test_expected_noncanonical',
    'tools.local_validation.pc1.test_join.JoinTests.test_expected_operation',
    'tools.local_validation.pc1.test_join.JoinTests.test_ingress_alternate_binding',
    'tools.local_validation.pc1.test_join.JoinTests.test_ingress_operation',
    'tools.local_validation.pc1.test_join.JoinTests.test_join_flags',
    'tools.local_validation.pc1.test_join.JoinTests.test_pin_without_lf',
    'tools.local_validation.pc1.test_join.JoinTests.test_precutoff_late',
    'tools.local_validation.pc1.test_join.JoinTests.test_refusal_classification',
    'tools.local_validation.pc1.test_join.JoinTests.test_refused_flags',
    'tools.local_validation.pc1.test_join.JoinTests.test_refused_needs_fault',
    'tools.local_validation.pc1.test_join.JoinTests.test_result_constructor_rejects_flags',
    'tools.local_validation.pc1.test_join.JoinTests.test_result_frozen',
    'tools.local_validation.pc1.test_join.JoinTests.test_revoked_zero_cutoff',
    'tools.local_validation.pc1.test_join.JoinTests.test_unexpected_interrupt_propagates',
    'tools.local_validation.pc1.test_join.JoinTests.test_unexpected_propagates',
    'tools.local_validation.pc1.test_join.JoinTests.test_unexpected_value_error_propagates',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_ascii',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_boolean_ordinal',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_bounded_integer_token',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_bytes_exact_type',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_bytes_subclass_no_callbacks',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_cap',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_depth',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_digest_case',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_duplicate',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_extra_field',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_extra_lf',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_float',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_immutable_nested',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_input_pin_zero',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_missing_field',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_missing_lf',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_nan',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_noncanonical_spaces',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_ordinal_overflow',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_unexpected_json_interrupt',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_unexpected_json_value_error',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_uuid_case',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_valid_binding',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_valid_capture',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_valid_ingress',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_witness_cap',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_wrong_schema',
    'tools.local_validation.pc1.test_projections.ProjectionTests.test_zero_uuid',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.pc1.test_join', 5395, '09713609d95feb5fc1f0cb783780cb76a3b33fbb937b60d1ead4127818c56325'),
    ('tools.local_validation.pc1.test_projections', 4021, 'c98d2a722815e498b3db681936f802be0f5a0c4d87927e58bcb25b6c0b8bb9b1'),
)

def expected_ids(): return tuple(sorted(prior.expected_ids() + NEW_IDS))
def expected_modules(): return tuple(sorted(prior.expected_modules() + NEW_MODULE_PINS))
def selected_ids(): return prior.selected_ids()
def supplement_ids(): return prior.supplement_ids()
def held_ids():
    selected = frozenset(selected_ids())
    return tuple(name for name in expected_ids() if name not in selected)
def roster_digest(check):
    value = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(value == FULL_DIGEST, "PC1 source roster")
    return value
def selection_digest(check): return prior.selection_digest(check)
