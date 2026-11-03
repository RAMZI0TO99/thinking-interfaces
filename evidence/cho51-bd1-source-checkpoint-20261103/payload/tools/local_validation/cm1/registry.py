"""Immutable CM1 source registry; no source reads or discovery. No self hash."""
from ..hb1.collection import expected_ids as original_ids, expected_modules as original_modules
from ..hb1.baseline import BASE_PARTITIONS, HB_IDS
from ..hb1.common import digest, require

CM_IDS = (
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_all_runner_cases_join_roster',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_class_method_alias_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_duplicate_identity_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_dynamic_load_tests_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_exact_full_roster_before_selection',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_exact_namespace_bijection',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_missing_extra_equal_count_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_mock_surface_restoration',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_module_pin_drift_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_partial_module_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_selection_never_discharges_cohorts',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_skip_xfail_deselection_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_source_package_preload_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_stdlib_shadow_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_unexpected_loader_refuse',
    'tools.local_validation.cm1.test_collection.CM1CollectionTests.test_unregistered_patch_refuse',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_bounded_record_grammar',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_capture_overflow_consumed',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_expected_failure_and_success_refuse',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_failure_without_formatting',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_final_verification_before_acceptance',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_guard_mock_isolation',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_header_and_operation_join',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_immutable_parent_reservations',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_ordinal_and_digest_join',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_original_deadline_cleanup_min',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_raw_stream_separation',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_start_complete_conservation',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_subtest_parent_accounting',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_suite_fixture_error_refuses',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_unavailable_host_never_authorizes',
    'tools.local_validation.cm1.test_protocol.CM1ProtocolTests.test_unknown_code_origin_refuses',
)
CM_MODULE_PINS = (
    ('tools.local_validation.cm1.test_collection', 8163, '8f53902e71470d786eaf99c80c1dfce9528b35383120ae1be13b103eeb2ad7eb'),
    ('tools.local_validation.cm1.test_protocol', 9755, '1ec01b98eebe98538d08658e21ce662c006ca15fd3ad51c75026ff0b9fbeb5d0'),
)
FULL_DIGEST = '4809c59806c616354c1cfb0fb2ac144ca07803532d314a8247ffacc8a8e985e6'
SELECTION_DIGEST = 'c331be73c669c83654a54401d0610fedbbf6f806650fae957fbbbf93281f160a'

def expected_ids():
    return tuple(sorted(original_ids() + CM_IDS))

def expected_modules():
    return tuple(sorted(original_modules() + CM_MODULE_PINS))

def selected_ids():
    parts = dict(BASE_PARTITIONS)
    return tuple(sorted(parts["qd10"] + parts["sc_hash_ram19"] + parts["sc_publisher35"] + HB_IDS + CM_IDS))

def selected_ordinals():
    positions = {name: i for i, name in enumerate(expected_ids())}
    return tuple(positions[name] for name in selected_ids())

def roster_digest(check):
    actual = digest(("\n".join(expected_ids()) + "\n").encode("ascii"), check)
    require(actual == FULL_DIGEST, "literal full roster digest")
    return actual

def selection_digest(check):
    actual = digest(("\n".join(selected_ids()) + "\n").encode("ascii"), check)
    require(actual == SELECTION_DIGEST, "literal selection digest")
    return actual
