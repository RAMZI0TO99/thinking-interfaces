"""Literal CM2 successor; no source reads or live discovery, no self hash."""
from ..cm1 import registry as prior
from ..hb1.common import digest, require

NEW_IDS = (
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_duration_never_formats',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_end_requires_outcome',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_event_caps_and_prefix',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_failfast_and_cleanup_errors',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_fixture_failure_after_passes',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_frozen_facts_and_raw_digest',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_full_selected_lifecycle',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_operational_dispatch_refuses',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_pass_requires_cleanup',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_skip_xfail_xpass_refuse_success',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_start_order_and_duplicates',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_sticky_reentrant_refusal',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_subtest_parent_and_count',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_suite_and_final_gates',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_trace_bounds_and_exact_types',
    'tools.local_validation.cm2.test_callbacks.CM2CallbackTests.test_trace_owner_and_location',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_before_after_drift_refuse',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_changed_bytes_refuse',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_checkpoints_and_no_live_authority',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_closed_manifest_and_bounds',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_code_graph_depth_and_cycles',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_code_owner_and_location_join',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_complete_roster_before_projection',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_duplicate_code_and_locations',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_exact_supplied_bytes_and_pin',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_loaded_token_reconciliation',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_module_kinds_and_phases',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_names_parents_dependencies',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_new_methods_and_frozen_baseline',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_package_paths_no_fallback',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_size_hash_and_exact_types',
    'tools.local_validation.cm2.test_retained.CM2RetainedTests.test_unavailable_runtime_refuses',
)
NEW_MODULE_PINS = (
    ('tools.local_validation.cm2.test_retained', 10184, '68c67e22f67a5564f8111b8ce8b8da9014ad9476f390f63701b5f121c4a52815'),
    ('tools.local_validation.cm2.test_callbacks', 11225, '59c7fb51a6f1b8600dfceef6918a66c66880149e869236c5554303bcd8a81393'),
)
FULL_DIGEST = 'ef626570e8ba7c74e42d8229edafba76c2b27ba8fe9955cdca7e58e5f5f22a11'
SELECTION_DIGEST = 'd9789f9cbe7c6b19252917987b56982ae49a5d964aeb24719fd7161bfca21a6c'

def expected_ids():
    return tuple(sorted(prior.expected_ids() + NEW_IDS))

def expected_modules():
    return tuple(sorted(prior.expected_modules() + NEW_MODULE_PINS))

def selected_ids():
    return tuple(sorted(prior.selected_ids() + NEW_IDS))

def selected_ordinals():
    positions = {name: i for i, name in enumerate(expected_ids())}
    return tuple(positions[name] for name in selected_ids())

def roster_digest(check):
    actual = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(actual == FULL_DIGEST, "literal successor roster")
    return actual

def selection_digest(check):
    actual = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(actual == SELECTION_DIGEST, "literal successor selection")
    return actual
