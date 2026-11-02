"""Closed Q4 admission and result contracts. No I/O and no operational grants."""
from datetime import datetime, timedelta, timezone
from pathlib import PureWindowsPath
import hashlib
import uuid
from ..v1 import records as r
from ..lp18 import bootstrap_contract as bc

STAGE = "QD"
TIMING_HASHES = ('948eb50a0bc4176f9f07adc70e033304131ab3311f59487b9d84ce78425a7d68',
                 '4c46130c2d52395e6fd17a01ba8d8fa7c0e7a025dd10cc89cff4fa9161dcfd76',
                 'ac449ef41d3c3537a4ebd3265262199d093be2f40454618525c9050651e38c38')
PHASE = "runs/coordination/cho51_p3_startup_timing_20261101_qd1"
CONTRACT = "docs/phase2/cho51_p3_local_validation_contract_20261029.md"
SUPPLEMENT = "docs/phase2/cho51_p3_qd_contract_20261101.md"
DESIGN_REVIEW = "runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json"
INVENTORY_PACKAGE = 'tools.local_validation.lplan15'
PROBE_EXPECTED_REPORT_SHA256 = '97da15bcc6181ab015bab6dcc171f45fa19acb2f4a5e7d4d23f1b691c4b668cf'
PROBE_TEST_NAMES = ('fixed_supplied_case','closed_schema_and_types','fixed_selection','raw_pin_before_parse',
    'historical_descriptor','full_page_and_index','strict_json','origin_is_not_custody','full_field_traversal',
    'parent_identity','bom_crlf_null_spans','extra_node_changes_count','comparison_has_six_fields',
    'distinct_observation_identities','semantics_stay_unresolved','conservation','forbidden_products',
    'report_schema_is_not_state','safe_parser_refusal','source_and_node_bounds','encoder_bound',
    'report_is_bounded','raw_assets_counted','guard_refusal','deterministic_immutable',
    'self_certified_pin_refused','refusal_has_no_report','no_custody_grant','no_progress_state',
    'exact_probe_roster','original_kernel_limit','all_authority_false')
PROBE_TESTS = tuple(INVENTORY_PACKAGE + '.test_compiler.SourceProbeTests.test_rs%02d_' % (i+1) + name
                    for i, name in enumerate(PROBE_TEST_NAMES))
PROBE_ASSETS = (
    ('source', 494, '6e758cdd0028b2cad74c739b9adc9c9f06f054932306280b878bfe59d39219b5'),
    ('index', 39086, 'e7d9c90fe2b1542dfefb130932e8d0be2d53b8add318897615acf843ae10c5d1'),
    ('page', 160029, '2699ca2b0e056186af4e6c007bcdf4831b9e7c622204be42436735faa9b80a2e'))


def qualification_cohort(expected):
    """Three finite cohorts; no inherited identity is replaced or truncated."""
    r.require(type(expected) is list and all(type(name) is str for name in expected), 'cohort roster')
    r.require(len(set(expected)) == len(expected), 'duplicate cohort ID')
    prefixes = tuple(INVENTORY_PACKAGE + '.test_compiler.' + group + '.'
                     for group in ('ResolverTests', 'FrontierTests', 'LosslessTests', 'SourceProbeTests'))
    counts = [sum(name.startswith(prefix) for name in expected) for prefix in prefixes]
    if len(expected) == 32 and counts == [0, 0, 0, 32]:
        return 'probe'
    if len(expected) == 100 and counts == [40, 32, 28, 0]:
        return 'lossless'
    r.require(len(expected) == 384 and counts == [0, 0, 0, 0],
              'exact inherited384, combined100 or fixed probe32 cohort')
    return 'inherited'


# Reserved partitions of one shared 256-file/64-MiB operation allocation.
# These add stricter stage bounds; no original resource/state guard is replaced.
ALLOCATION = {'fixtures': (160, 32 * 1024**2), 'supervisor': (40, 8 * 1024**2),
              'caller': (40, 20 * 1024**2), 'closeout': (16, 4 * 1024**2)}


def validate_allocation(bucket, files, byte_count, largest):
    r.require(type(bucket) is str and bucket in ALLOCATION, 'allocation bucket')
    cap_files, cap_bytes = ALLOCATION[bucket]
    r.exact_int(files, upper=cap_files)
    r.exact_int(byte_count, upper=cap_bytes)
    r.exact_int(largest, upper=8 * 1024**2)
    r.require(largest <= byte_count and (files != 0 or byte_count == 0), 'allocation totals')
    return {'files': files, 'bytes': byte_count, 'largest': largest}


def validate_probe_observation(value, cohort):
    r.require(cohort in ('inherited', 'lossless', 'probe'), 'probe cohort')
    if cohort != 'probe':
        r.require(value is None, 'probe observation outside fixed cohort')
        return
    r.closed(value, ('schema', 'outcome', 'reason', 'checks_completed', 'report'))
    r.require(value['schema'] == 'cho51_source_probe_result_v1'
              and value['outcome'] == 'OBSERVED_SELECTED_SOURCE' and value['reason'] is None
              and value['checks_completed'] == ['request_and_pins', 'historical_membership',
                   'syntax_observation', 'selected_comparison', 'final_guard'], 'complete fixed observation')
    report = value['report']
    r.closed(report, ('schema', 'case_id', 'source_pin', 'index_pin', 'page_pin',
                     'selected_ordinals', 'observations', 'comparisons', 'origin_pin_equal',
                     'selected_syntax_equal', 'global_scope', 'authority'))
    r.require(report['schema'] == 'cho51_source_probe_report_v1'
              and report['case_id'] == 'packaging_source_v1'
              and report['origin_pin_equal'] is True and report['selected_syntax_equal'] is True,
              'fixed syntax observation equality')
    r.require(type(report['observations']) is list and len(report['observations']) == 37
              and type(report['comparisons']) is list and len(report['comparisons']) == 37,
              'complete selected syntax census')
    r.require(report['global_scope'] == {'resolver_rows':18793,'inventory_rows':13406,
              'selected_rows':38,'unselected_resolver_rows':18755,'obligations_discharged':0,
              'global_ledger_mutated':False}, 'all global obligations retained')
    r.closed(report['authority'], ('resumable', 'exhaustive_reconciliation', 'complete_dependency_closure',
              'g2_complete', 'launch_authorized', 'capabilities_accepted', 'scientific_admission',
              'historical_custody_closed', 'current_p_custody_refreshed'))
    r.require(all(v is False for v in report['authority'].values()), 'probe cannot grant authority')
    # Exact expected report pin is generated from the complete historical selected
    # syntax fields, not by executing the new observer or trusting its own digest.
    r.require(hashlib.sha256(r.canonical_bytes(report)).hexdigest() == PROBE_EXPECTED_REPORT_SHA256,
              'independently pinned complete fixed report')


def validate_probe_assets(value, cohort, checkpoint=None):
    r.require(cohort in ('inherited', 'lossless', 'probe'), 'probe asset cohort')
    if cohort != 'probe':
        r.require(value is None, 'probe assets outside fixed cohort')
        return None
    r.require(callable(checkpoint), 'trusted probe transport checkpoint required')
    def guard():
        if checkpoint() is not True:
            raise RuntimeError('probe transport checkpoint refused')
    guard()
    r.closed(value, ('source', 'index', 'page'))
    decoded = {}
    for name, size, sha in PROBE_ASSETS:
        guard()
        parts = value[name]
        r.require(type(parts) is list and len(parts) == (size * 2 + 4095) // 4096,
                  'exact asset transport parts')
        chunks, digest = [], hashlib.sha256()
        for i, part in enumerate(parts):
            if i % 8 == 0:
                guard()  # At most 32 KiB hex / 16 KiB raw between samples.
            length = min(4096, size * 2 - i * 4096)
            r.require(type(part) is str and len(part) == length
                      and r.re.fullmatch('[0-9a-f]+', part) is not None, 'bounded exact hex part')
            chunk = bytes.fromhex(part)
            chunks.append(chunk)
            digest.update(chunk)
        guard()
        raw = b''.join(chunks)  # One bounded final copy; sample both sides.
        guard()
        r.require(len(raw) == size and digest.hexdigest() == sha, 'complete raw asset pin')
        decoded[name] = raw
    guard()
    return decoded


def inventory_modules(sources, namespaces):
    """One declared inventory package binds preloads, namespace and source pins."""
    r.require(INVENTORY_PACKAGE in namespaces, 'inventory namespace missing')
    result = tuple((INVENTORY_PACKAGE+'.'+leaf,
                    INVENTORY_PACKAGE.replace('.','/')+'/'+leaf+'.py')
                   for leaf in ('compiler','migration'))
    r.require(all(path in sources for _,path in result), 'inventory preload missing source pin')
    r.require(INVENTORY_PACKAGE.replace('.','/')+'/test_compiler.py' in sources,
              'inventory suite missing source pin')
    return result


REQUIRED = (
    "docs/phase2/cho51_p3_adapter_v2/contracts.py",
    "docs/phase2/cho51_p3_adapter_v2/mapping.py",
    "docs/phase2/cho51_p3_adapter_v2/README.md",
    "docs/phase2/cho51_p3_adapter_v2/telemetry.py",
    "docs/phase2/cho51_p3_adapter_v2/test_mapping.py",
    "docs/phase2/cho51_p3_adapter_v2/test_telemetry.py",
    "docs/phase2/cho51_p3_candidate_inventory_contract_20261031.md",
    "docs/phase2/cho51_p3_qd_contract_20261101.md",
    "docs/phase2/cho51_p3_l_implementation_contract_20261029.md",
    "docs/phase2/cho51_p3_loader_design_20261029.md",
    "docs/phase2/cho51_p3_loader_design_v1/acceptance-cases.json",
    "docs/phase2/cho51_p3_loader_design_v1/README.md",
    "docs/phase2/cho51_p3_loader_design_v1/record-contract.md",
    "docs/phase2/cho51_p3_loader_design_v1/source-trace.md",
    "docs/phase2/cho51_p3_local_validation_contract_20261029.md",
    "docs/phase2/cho51_p3_local_validation_v1/control-roster.json",
    "docs/phase2/cho51_p3_local_validation_v1/dependency-plan.json",
    "docs/phase2/cho51_p3_local_validation_v1/test-roster.json",
    "docs/phase2/cho51_p3_lq2_array_contract_20261031.md",
    "docs/phase2/cho51_p3_native_memory_bootstrap_contract_20261031.md",
    "docs/phase2/cho51_p3_p2_dependency_contract_20261029.md",
    "docs/phase2/cho51_p3_q2_bootstrap_contract_20261029.md",
    "docs/phase2/cho51_p3_q3_utc_contract_20261029.md",
    "docs/phase2/cho51_p3_q4_reader_contract_20261029.md",
    "docs/phase2/cho51_p3_startup_cache_successor_contract_20261031.md",
    "docs/phase2/cho51_p3_startup_implementation_contract_20261031.md",
    "docs/phase2/cho51_p3_startup_scalar_successor_contract_20261031.md",
    "docs/PROJECT_EXECUTION_POLICY.md",
    "evaluation/phase2_supervision_primitives.py",
    "runs/coordination/cho51_p3_candidate_inventory_20261031_p3/failure_b8a63867-4de2-42a0-9176-d13c9b60d37a/actual-review.json",
    "runs/coordination/cho51_p3_candidate_inventory_20261031_p3/failure_b8a63867-4de2-42a0-9176-d13c9b60d37a/root-disposition.json",
    "runs/coordination/cho51_p3_startup_timing_20261101_qd1/candidate-migration.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/static-path-diagnosis.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p3/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p3/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p4/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p4/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p4/static-api-host-diagnosis.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p5/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p5/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p5/static-pe-descriptor-diagnosis.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p6/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p6/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p6/static-api-query-scope.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p6/static-missing-native.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p9/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p9/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_q7/failure_6451d9c4-0c30-42fc-8a47-caa520b2043d/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_q7/failure_6451d9c4-0c30-42fc-8a47-caa520b2043d/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_q8/failure_7c2de01e-6143-4421-a750-b686b69dc2d4/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_q8/failure_7c2de01e-6143-4421-a750-b686b69dc2d4/root-disposition.json",
    "runs/coordination/cho51_p3_finite_l_design_20261031_v1/design-candidate-revision1.json",
    "runs/coordination/cho51_p3_finite_l_design_20261031_v1/design-review-revision1.json",
    "runs/coordination/cho51_p3_finite_l_design_20261031_v1/root-design-acceptance.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/actual-review.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/root-qualification.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/seal_49b1f44d-46ef-446e-a8fd-85a3ddb7ce36.json",
    "runs/coordination/cho51_p3_loader_design_20261029_v1/design-review-revision1.json",
    "runs/coordination/cho51_p3_loader_design_20261029_v1/root-design-acceptance.json",
    "runs/coordination/cho51_p3_loader_implementation_20261029_p1/root-held-disposition.json",
    "runs/coordination/cho51_p3_loader_implementation_20261029_q1/actual-review.json",
    "runs/coordination/cho51_p3_loader_implementation_20261029_q1/root-disposition.json",
    "runs/coordination/cho51_p3_loader_implementation_20261029_q1/static-array-diagnosis.json",
    "runs/coordination/cho51_p3_loader_implementation_20261031_q2/actual-review.json",
    "runs/coordination/cho51_p3_loader_implementation_20261031_q2/root-qualification.json",
    "runs/coordination/cho51_p3_loader_implementation_20261031_q2/source-review.json",
    "runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json",
    "runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/actual-review.json",
    "runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/root-disposition.json",
    "runs/coordination/cho51_p3_native_bootstrap_20261031_q1/failure_1a07add9-5fac-40b2-8ff2-18d55e70c385/static-import-review.json",
    "runs/coordination/cho51_p3_preparation_engine_20261029_p1q/root-qualification.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q1/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q1/root-disposition.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/root-disposition.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/timestamp-metadata-analysis.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q3/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q3/root-disposition.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/final-closeout.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/source-review.json",
    "runs/coordination/cho51_p3_startup_diagnostic_20261031_d2/source-review.json",
    "runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/actual-review.json",
    "runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/root-qualification.json",
    "runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/source-review.json",
    "tools/local_validation/l1/__init__.py",
    "tools/local_validation/l1/child_entry.py",
    "tools/local_validation/l1/collection.py",
    "tools/local_validation/l1/guards.py",
    "tools/local_validation/l1/imports.py",
    "tools/local_validation/l1/native_bridge.py",
    "tools/local_validation/l1/native_cases.py",
    "tools/local_validation/l1/native_fixture.c",
    "tools/local_validation/l1/native_observer.c",
    "tools/local_validation/l1/native_observer.h",
    "tools/local_validation/l1/observation.py",
    "tools/local_validation/l1/plan.py",
    "tools/local_validation/l1/protocol.py",
    "tools/local_validation/l1/qualification-map.json",
    "tools/local_validation/l1/README.md",
    "tools/local_validation/l1/test_collection.py",
    "tools/local_validation/l1/test_guards.py",
    "tools/local_validation/l1/test_imports.py",
    "tools/local_validation/l1/test_native.py",
    "tools/local_validation/l1/test_observation.py",
    "tools/local_validation/l1/test_protocol.py",
    "tools/local_validation/l1/test_support.py",
    "tools/local_validation/lhost1/__init__.py",
    "tools/local_validation/lhost1/abi.py",
    "tools/local_validation/lhost1/authority.py",
    "tools/local_validation/lhost1/bootstrap.py",
    "tools/local_validation/lhost1/caller_native.cs",
    "tools/local_validation/lhost1/invoke_l.ps1",
    "tools/local_validation/lhost1/job_adapter.py",
    "tools/local_validation/lhost1/README.md",
    "tools/local_validation/lhost1/runtime.py",
    "tools/local_validation/lhost1/supervisor.py",
    "tools/local_validation/lhost1/test_authority.py",
    "tools/local_validation/lhost1/test_transport.py",
    "tools/local_validation/lhost1/transport.py",
    "tools/local_validation/lp1/api_mapping.py",
    "tools/local_validation/lp1/api_query_plan.json",
    "tools/local_validation/lp1/build_native.ps1",
    "tools/local_validation/lp1/caller_native.cs",
    "tools/local_validation/lp1/dependency_coverage.md",
    "tools/local_validation/lp1/dependency_recipe.json",
    "tools/local_validation/lp1/invoke_p.ps1",
    "tools/local_validation/lp1/manifest.py",
    "tools/local_validation/lp1/native_policy.json",
    "tools/local_validation/lp1/native_reader.py",
    "tools/local_validation/lp1/pe.py",
    "tools/local_validation/lp1/protocol.py",
    "tools/local_validation/lp1/README.md",
    "tools/local_validation/lp1/supervisor.py",
    "tools/local_validation/lp1/test_long_paths.py",
    "tools/local_validation/lp1/test_manifest.py",
    "tools/local_validation/lp1/test_pe.py",
    "tools/local_validation/lp1/test_performance.py",
    "tools/local_validation/lp1/test_protocol.py",
    "tools/local_validation/lp2/api_mapping.py",
    "tools/local_validation/lp2/api_query_plan.json",
    "tools/local_validation/lp2/build_native.ps1",
    "tools/local_validation/lp2/caller_native.cs",
    "tools/local_validation/lp2/dependency_coverage.md",
    "tools/local_validation/lp2/dependency_recipe.json",
    "tools/local_validation/lp2/invoke_p.ps1",
    "tools/local_validation/lp2/manifest.py",
    "tools/local_validation/lp2/native_policy.json",
    "tools/local_validation/lp2/native_reader.py",
    "tools/local_validation/lp2/pe.py",
    "tools/local_validation/lp2/protocol.py",
    "tools/local_validation/lp2/README.md",
    "tools/local_validation/lp2/supervisor.py",
    "tools/local_validation/lp2/test_long_paths.py",
    "tools/local_validation/lp2/test_manifest.py",
    "tools/local_validation/lp2/test_pe.py",
    "tools/local_validation/lp2/test_performance.py",
    "tools/local_validation/lp2/test_protocol.py",
    "tools/local_validation/lp18/api_mapping.py",
    "tools/local_validation/lp18/api_query_plan.json",
    "tools/local_validation/lp18/bootstrap_contract.py",
    "tools/local_validation/lp18/bootstrap_loader.ps1",
    "tools/local_validation/lp18/build_native.ps1",
    "tools/local_validation/lp18/caller_native.cs",
    "tools/local_validation/lp18/dependency_coverage.md",
    "tools/local_validation/lp18/dependency_recipe.json",
    "tools/local_validation/lp18/invoke_p.ps1",
    "tools/local_validation/lp18/manifest.py",
    "tools/local_validation/lp18/native_bootstrap.ps1",
    "tools/local_validation/lp18/native_policy.json",
    "tools/local_validation/lp18/native_reader.py",
    "tools/local_validation/lp18/pe.py",
    "tools/local_validation/lp18/protocol.py",
    "tools/local_validation/lp18/README.md",
    "tools/local_validation/lp18/supervisor.py",
    "tools/local_validation/lp18/test_bootstrap_contract.py",
    "tools/local_validation/lp18/test_long_paths.py",
    "tools/local_validation/lp18/test_manifest.py",
    "tools/local_validation/lp18/test_pe.py",
    "tools/local_validation/lp18/test_performance.py",
    "tools/local_validation/lp18/test_protocol.py",
    "tools/local_validation/lplan1/__init__.py",
    "tools/local_validation/lplan1/compiler.py",
    "tools/local_validation/lplan1/pytest.ini",
    "tools/local_validation/lplan1/README.md",
    "tools/local_validation/lplan1/seed-spec.json",
    "tools/local_validation/lplan1/test_compiler.py",
    "tools/local_validation/lplan15/__init__.py",
    "tools/local_validation/lplan15/compiler.py",
    "tools/local_validation/lplan15/migration.py",
    "tools/local_validation/lplan15/README.md",
    "tools/local_validation/lplan15/test_compiler.py",
    "tools/local_validation/lq1/build_l_native.ps1",
    "tools/local_validation/lq1/caller_native.cs",
    "tools/local_validation/lq1/child_entry.py",
    "tools/local_validation/lq1/invoke_q.ps1",
    "tools/local_validation/lq1/job_adapter.py",
    "tools/local_validation/lq1/l_native.py",
    "tools/local_validation/lq1/native_reader.py",
    "tools/local_validation/lq1/protocol.py",
    "tools/local_validation/lq1/README.md",
    "tools/local_validation/lq1/supervisor.py",
    "tools/local_validation/lq1/test_l_native.py",
    "tools/local_validation/lq1/test_native_reader.py",
    "tools/local_validation/lq1/test_protocol.py",
    "tools/local_validation/lq2/build_l_native.ps1",
    "tools/local_validation/lq2/caller_native.cs",
    "tools/local_validation/lq2/child_entry.py",
    "tools/local_validation/lq2/invoke_q.ps1",
    "tools/local_validation/lq2/job_adapter.py",
    "tools/local_validation/lq2/l_native.py",
    "tools/local_validation/lq2/native_reader.py",
    "tools/local_validation/lq2/protocol.py",
    "tools/local_validation/lq2/README.md",
    "tools/local_validation/lq2/supervisor.py",
    "tools/local_validation/lq2/test_l_native.py",
    "tools/local_validation/lq2/test_native_reader.py",
    "tools/local_validation/lq2/test_protocol.py",
    "tools/local_validation/lq18/bootstrap_controls.ps1",
    "tools/local_validation/lq18/bootstrap_probe.ps1",
    "tools/local_validation/lq18/build_l_native.ps1",
    "tools/local_validation/lq18/caller_native.cs",
    "tools/local_validation/lq18/child_entry.py",
    "tools/local_validation/lq18/invoke_q.ps1",
    "tools/local_validation/lq18/job_adapter.py",
    "tools/local_validation/lq18/l_native.py",
    "tools/local_validation/lq18/native_reader.py",
    "tools/local_validation/lq18/protocol.py",
    "tools/local_validation/lq18/README.md",
    "tools/local_validation/lq18/supervisor.py",
    "tools/local_validation/lq18/test_l_native.py",
    "tools/local_validation/lq18/test_native_reader.py",
    "tools/local_validation/lq18/test_protocol.py",
    "tools/local_validation/p1/preparation.py",
    "tools/local_validation/p1/README.md",
    "tools/local_validation/p1/test_preparation.py",
    "tools/local_validation/q4/native_reader.py",
    "tools/local_validation/startup2/__init__.py",
    "tools/local_validation/startup2/contract.py",
    "tools/local_validation/startup2/diagnostic.ps1",
    "tools/local_validation/startup2/empty_probe.ps1",
    "tools/local_validation/startup2/fast_probe.ps1",
    "tools/local_validation/startup2/malformed_probe.ps1",
    "tools/local_validation/startup2/partial_probe.ps1",
    "tools/local_validation/startup2/pdh_probe.ps1",
    "tools/local_validation/startup2/README.md",
    "tools/local_validation/startup2/reordered_probe.ps1",
    "tools/local_validation/startup2/stall_probe.ps1",
    "tools/local_validation/startup2/test_diagnostic.py",
    "tools/local_validation/v1/preparation.py",
    "tools/local_validation/v1/README.md",
    "tools/local_validation/v1/records.py",
    "tools/local_validation/v1/test_foundation.py",
)
LIMITS = {"whole_seconds": 90, "work_seconds": 60, "cleanup_seconds": 5,
          "process_mib": 512, "job_mib": 768, "parent_mib": 512,
          "startup_ram_gib": 4, "active_ram_gib": 4, "disk_gib": 20,
          "frame_bytes": 1048576, "stream_bytes": 1048576,
          "threads": 1, "gpu_visible": False}
FALSES = {"historical_custody_closed": False, "historical_operation_released": False,
          "historical_retry_allowed": False, "restart_qualified": False, "boundary_qualified": False,
          "complete_dependency_closure": False, "launch_authorized": False,
          "scientific_admission": False}
MODES = ("suite", "native-transient", "native-overflow", "native-badreason", "native-badutf16", "native-pathbound", "badframe", "stall")
FORBIDDEN = ["candidate_imports", "third_party_imports", "numerical_work",
             "data_or_weights", "network", "git", "unowned_processes", "historical_launcher_replay"]


def timing_decimal(value, *, positive=False, upper=2**63-1):
    """Checked decimal strings preserve native 64-bit clock identity."""
    r.require(type(value) is str and r.re.fullmatch(r'0|[1-9][0-9]*', value) is not None,
              'canonical decimal string')
    number = int(value)
    r.require((not positive or number > 0) and number <= upper, 'decimal bounds')
    return number


def datetime_utc_ticks(value):
    """Convert an aware UTC datetime to .NET ticks without floating arithmetic.

    Python datetime carries microseconds, so the low decimal tick is zero. A
    native 100-ns reading must be kept as its original integer instead.
    """
    r.require(type(value) is datetime and value.utcoffset() == timedelta(0), 'UTC datetime required')
    delta = value - datetime(1, 1, 1, tzinfo=timezone.utc)
    ticks = (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10
    r.require(0 < ticks <= 2**63-1, 'UTC tick bounds')
    return ticks


def encode_timing_event(value):
    raw = r.canonical_bytes(value) + b'\n'
    r.require(len(raw) <= 512 and all(byte < 128 for byte in raw), 'event encoding bound')
    return raw


class TimingEvents:
    """Pure incremental validator for either role; it grants no custody claim."""
    _codes = frozenset(('ok', 'prefix_stop', 'input', 'authority', 'clock', 'resource',
                        'stop', 'capacity', 'io', 'identity', 'custody', 'deadline', 'unknown'))

    def __init__(self, role, operation, admission_sha256, origin_qpc, frequency, origin_ticks, producer_pid):
        r.require(role in ('C', 'S') and operation == str(uuid.UUID(operation)), 'timing identity')
        r.require(type(admission_sha256) is str and r.HEX64.fullmatch(admission_sha256), 'admission hash')
        self.role, self.operation, self.admission = role, operation, admission_sha256
        self.oq = timing_decimal(origin_qpc, positive=True)
        self.fq = timing_decimal(frequency, positive=True)
        self.ou = timing_decimal(origin_ticks, positive=True)
        self.pid = timing_decimal(producer_pid, positive=True, upper=2**32-1)
        self.count = self.bytes = self.normal = self.final = 0
        self.last_q, self.last_u = self.oq, self.ou
        self.stack, self.completed = [], set()
        self.authority, self.failed, self.secondary, self.ready, self.terminal = 'pending', False, False, False, False
        self.counter_start = {}
        self.poisoned = False
        if role == 'S':
            self.expected = [(f'S{i:02d}', e) for i in range(1, 16) for e in ('begin', 'end')]
            self.expected += [('S16', 'mark')]
            self.expected += [(f'S{i:02d}', e) for i in range(17, 21) for e in ('begin', 'end')]
        else:
            self.expected = [(f'C{i:02d}', e) for i in range(1, 12) for e in ('begin', 'end')]
            self.expected += [('C12', 'begin')]
            self.expected += [(f'C{i:02d}', e) for i in range(13, 22) for e in ('begin', 'end')]
            self.expected += [('C12', 'end')]
            self.expected += [(f'C{i:02d}', e) for i in range(22, 29) for e in ('begin', 'end')]
        self.position = 0

    def accept(self, raw):
        r.require(not self.poisoned, 'journal validator already refused')
        try:
            return self._accept(raw)
        except BaseException:
            self.poisoned = True
            raise

    def _accept(self, raw):
        r.require(type(raw) is bytes and 1 <= len(raw) <= 512 and raw.endswith(b'\n')
                  and raw.count(b'\n') == 1 and b'\r' not in raw
                  and not raw.startswith(b'\xef\xbb\xbf') and all(b < 128 for b in raw), 'ASCII line bound')
        r.require(not self.terminal and self.count < 128 and self.bytes + len(raw) <= 65536, 'journal bounds')
        value = r.strict_loads(raw)
        r.require(type(value) is dict and type(value.get('v')) is int and value['v'] == 1, 'event version')
        kind = value.get('k')
        if self.count == 0:
            r.closed(value, ('v','k','op','r','n','oq','fq','ou','pp','ah'))
            r.require(kind == 'H' and value['op'] == self.operation and value['r'] == self.role
                      and value['n'] == '0' and value['ah'] == self.admission
                      and timing_decimal(value['oq'], positive=True) == self.oq
                      and timing_decimal(value['fq'], positive=True) == self.fq
                      and timing_decimal(value['ou'], positive=True) == self.ou
                      and timing_decimal(value['pp'], positive=True, upper=2**32-1) == self.pid, 'header identity')
            is_final = False
        else:
            r.require(kind in ('E', 'T') and timing_decimal(value.get('n')) == self.count, 'contiguous sequence')
            q, u = timing_decimal(value.get('q'), positive=True), timing_decimal(value.get('u'), positive=True)
            r.require(q >= self.last_q and u >= self.last_u, 'clock moved backwards')
            self.last_q, self.last_u = q, u
            if kind == 'T':
                r.closed(value, ('v','k','n','q','u','c','lv'))
                r.require(value['c'] in ('ready_for_original_close','incomplete','journal_fault')
                          and value['lv'] in ('complete','incomplete','unknown'), 'terminal tokens')
                r.require(not (value['c'] == 'ready_for_original_close' and
                               (not self.ready or self.failed or self.stack or value['lv'] != 'complete')),
                          'complete terminal requires ready and verification')
                r.require(value['c'] == 'ready_for_original_close' or self.failed,
                          'incomplete terminal requires failure tail')
                self.terminal = True
                is_final = True
            else:
                r.closed(value, ('v','k','n','s','e','q','u','a','c','nf','nb','gs'))
                stage, edge, code = value['s'], value['e'], value['c']
                max_stage = 29 if self.role == 'C' else 21
                r.require(type(stage) is str and stage in {self.role + str(i).zfill(2) for i in range(1,max_stage+1)}
                          and edge in ('begin','end','fail','mark') and code in self._codes, 'stage tokens')
                r.require(value['a'] in ('pending','verified'), 'authority token')
                for name in ('nf','nb','gs'):
                    if value[name] is not None:
                        timing_decimal(value[name])
                is_ready = stage == self.role + str(max_stage) and edge == 'mark'
                is_final = edge == 'fail' or is_ready
                if self.failed:
                    r.require(is_final and not self.ready and (is_ready or (edge == 'fail' and code == 'io' and not self.secondary)), 'failure tail')
                    if edge == 'fail': self.secondary = True
                    if is_ready: self.ready = True
                elif edge == 'fail':
                    r.require(code not in ('ok','prefix_stop'), 'failure code')
                    self.failed = True
                elif is_ready:
                    r.require(not self.ready and not self.stack and code == 'ok'
                              and self.position == len(self.expected), 'ready mark')
                    self.ready = True
                elif edge == 'mark':
                    r.require(self.role == 'S' and stage == 'S16' and code == 'prefix_stop'
                              and not self.stack and stage not in self.completed, 'prefix stop mark')
                    self.completed.add(stage)
                elif edge == 'begin':
                    r.require(code == 'ok' and stage not in self.completed and stage not in self.stack, 'stage begin')
                    r.require(not self.stack or (self.role == 'C' and self.stack == ['C12']
                              and stage in {'C%02d' % i for i in range(13,22)}), 'stage nesting')
                    self.stack.append(stage)
                    self.counter_start[stage] = tuple(value[k] for k in ('nf','nb','gs'))
                elif edge == 'end':
                    r.require(code == 'ok' and self.stack and self.stack[-1] == stage, 'stage end')
                    for start, end in zip(self.counter_start[stage], (value[k] for k in ('nf','nb','gs'))):
                        r.require(start is None or end is None or int(end) >= int(start), 'stage counter regression')
                    self.stack.pop(); self.completed.add(stage)
                expected_authority = 'verified' if self.authority == 'verified' or (edge == 'end' and stage == self.role + ('05' if self.role == 'C' else '08')) else 'pending'
                r.require(value['a'] == expected_authority, 'authority transition')
                self.authority = expected_authority
                if not is_final:
                    r.require(self.position < len(self.expected) and self.expected[self.position] == (stage, edge),
                              'fixed stage order')
                    self.position += 1
        if is_final:
            self.final += 1
            r.require(self.final <= 6, 'final capacity')
        else:
            r.require(self.final == 0, 'normal after final')
            self.normal += 1
            r.require(self.normal <= 122, 'normal capacity')
        self.count += 1; self.bytes += len(raw)
        return value


def pin(value):
    r.closed(value, ("bytes", "sha256"))
    r.exact_int(value["bytes"], upper=64 * 1024**2)
    r.require(type(value["sha256"]) is str and r.HEX64.fullmatch(value["sha256"]) is not None, "pin digest")
    return value


def utc(text):
    r.exact_string(text, 64)
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    r.require(value.utcoffset() == timedelta(0), "explicit UTC required")
    return value


def window(start, expiry, origin):
    start, expiry, origin = utc(start), utc(expiry), utc(origin)
    r.require(start <= origin and origin + timedelta(seconds=90) <= expiry
              and 90 <= (expiry-start).total_seconds() <= 900, "complete original caller window")
    return origin + timedelta(seconds=90)


def ref(value, expected_path):
    r.closed(value, ("path", "bytes", "sha256"))
    r.require(value["path"] == expected_path, "reference path")
    pin({k: value[k] for k in ("bytes", "sha256")})


def validate_admission(value, root, origin_utc):
    value = r.defensive_copy(value)
    r.closed(value, ("schema", "stage", "operation_id", "created_utc", "expires_utc",
                     "root", "python", "runtime", "caller_runtime", "sources", "review", "adoption",
                     "predecessor", "limits", "modes", "expected_tests", "forbidden",
                     "scientific_admission", "compiler", "native_compiler", "bootstrap_qualification", "bootstrap_controls",
                     "purpose", "stop_point", "timing"))
    r.require(value["schema"] == "cho51_startup_timing_admission_v1" and value["stage"] == STAGE
              and value['purpose'] == 'QD_STARTUP_PREFIX_ONLY' and value['stop_point'] == 'BEFORE_MODE_LOOP', 'QD-only schema')
    r.require(value["operation_id"] == str(uuid.UUID(value["operation_id"])), "canonical UUID")
    timing = value['timing']
    r.closed(timing, ('design_sha256', 'format_sha256', 'stages_sha256', 'caller_name', 'supervisor_name',
                      'records', 'record_bytes', 'journal_bytes', 'prefix_seconds', 'verification_seconds', 'publication_seconds'))
    expected_timing = dict(zip(('design_sha256', 'format_sha256', 'stages_sha256'), TIMING_HASHES))
    expected_timing.update(caller_name='timing-caller_' + value['operation_id'] + '.jsonl',
                           supervisor_name='timing-supervisor_' + value['operation_id'] + '.jsonl',
                           records=128, record_bytes=512, journal_bytes=65536,
                           prefix_seconds=45, verification_seconds=53, publication_seconds=55)
    r.require(r.canonical_bytes(timing) == r.canonical_bytes(expected_timing), 'exact timing contract')
    r.require(value["root"] == root, "exact project root")
    r.windows_path(root, absolute=True)
    r.closed(value["caller_runtime"], ("path", "bytes", "sha256", "version"))
    r.windows_path(value["caller_runtime"]["path"], absolute=True)
    pin({k: value["caller_runtime"][k] for k in ("bytes", "sha256")})
    r.require(type(value["caller_runtime"]["version"]) is str and value["caller_runtime"]["version"].startswith("7."),
              "declared PowerShell7 host")
    window(value["created_utc"], value["expires_utc"], origin_utc)
    r.require(value["limits"] == LIMITS and r.canonical_bytes(value["limits"]) == r.canonical_bytes(LIMITS),
              "exact limits and scalar types")
    r.require(value["modes"] == list(MODES) and value["forbidden"] == FORBIDDEN
              and value["scientific_admission"] is False, "effects/stages/authority")
    r.require(type(value["sources"]) is dict and set(value["sources"]) == set(REQUIRED), "exact source set")
    for item in value["sources"].values():
        pin(item)
    bc.validate_request(value)
    runtime = value["runtime"]
    r.closed(runtime, ("root", "files", "recipe", "platform_trust"))
    r.windows_path(runtime["root"], absolute=True)
    r.require(runtime["recipe"] == "python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll",
              "runtime recipe")
    r.require(runtime["platform_trust"] == "reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation",
              "platform trust")
    r.require(type(runtime["files"]) is dict and 1 <= len(runtime["files"]) <= 2000, "runtime count")
    r.require(value["python"] == runtime["root"] + "/python.exe" and value["python"] in runtime["files"],
              "runtime executable")
    total = 0
    seen = set()
    for name, item in runtime["files"].items():
        r.windows_path(name, absolute=True)
        r.require(name.startswith(runtime["root"] + "/") and name.lower() not in seen, "runtime scope/alias")
        seen.add(name.lower())
        pin(item)
        total += item["bytes"]
    r.require(total <= 64 * 1024**2, "Q bootstrap runtime byte bound")
    ref(value["review"], "source-review.json")
    ref(value["adoption"], "contract-adoption.json")
    ref(value["predecessor"], "runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json")
    compiler=value['compiler']
    r.closed(compiler,('root','files'))
    r.windows_path(compiler['root'],absolute=True)
    r.require(type(compiler['files']) is dict and 3<=len(compiler['files'])<=258,'compiler closure count')
    total=0
    for path,item in compiler['files'].items():
        r.windows_path(path,absolute=True)
        r.require(path.startswith(compiler['root']+'/ref/') or path in
            (compiler['root']+'/Microsoft.CodeAnalysis.dll',compiler['root']+'/Microsoft.CodeAnalysis.CSharp.dll'),
            'compiler closure scope')
        pin(item);total+=item['bytes']
    r.require(total<=64*1024**2,'compiler bytes')
    native=value['native_compiler']
    r.closed(native,('root','files','import_library','recipe'))
    r.require(native['recipe']=='clang-cc1-closed-header-lld-stdout-v1','closed native compiler recipe')
    r.windows_path(native['root'],absolute=True);r.windows_path(native['import_library'],absolute=True)
    r.require(type(native['files']) is dict and 4<=len(native['files'])<=128,'native compiler closure count')
    required={native['root']+'/'+leaf for leaf in ('clang.exe','lld-link.exe','llvm-objdump.exe')}|{native['import_library']}
    r.require(required<=set(native['files']),'native toolchain required tools/import library')
    total=0
    for path,item in native['files'].items():
        r.windows_path(path,absolute=True);r.closed(item,('bytes','sha256'))
        r.require(path in required or (path.rpartition('/')[0]==native['root'] and path.endswith('.dll')),'native tool scope')
        r.exact_int(item['bytes'],1,256*1024**2)
        r.require(type(item['sha256']) is str and r.HEX64.fullmatch(item['sha256']) is not None,'native tool digest')
        total+=item['bytes']
    r.require(total<=2*1024**3,'native tool aggregate cap')
    r.require(type(value["expected_tests"]) is list and 1 <= len(value["expected_tests"]) <= 384,
              "bounded exact test roster")
    r.require(qualification_cohort(value['expected_tests']) == 'probe'
              and value['expected_tests'] == list(PROBE_TESTS), 'exact held probe32 roster')
    r.require(len(set(value["expected_tests"])) == len(value["expected_tests"]), "duplicate test id")
    for name in value["expected_tests"]:
        r.exact_string(name, 512)
        r.require(name.startswith(("tools.local_validation.v1.test_foundation.",
                                  "tools.local_validation.lq18.test_native_reader.",
                                  "tools.local_validation.lq18.test_protocol.",
                                  "tools.local_validation.p1.test_preparation.",
                                  "tools.local_validation.lp18.test_manifest.",
                                  "tools.local_validation.lp18.test_bootstrap_contract.",
                                  "tools.local_validation.lp18.test_long_paths.",
                                  "tools.local_validation.lp18.test_performance.",
                                  "tools.local_validation.lp18.test_pe.",
                                  "tools.local_validation.lp18.test_protocol.",
                                  "tools.local_validation.lq18.test_l_native.",
                                  "tools.local_validation.l1.test_",
                                  "tools.local_validation.lhost1.test_",
                                  "tools.local_validation.lplan1.test_",
                                  INVENTORY_PACKAGE+".test_compiler.")), "unexpected test module")
    return value


def validate_chain(request, review, adoption):
    r.require(review["status"] == "ACCEPTED_SOURCE_QD1" and review["sources"] == request["sources"]
              and review["reviewer"] not in review["authors"], "exact independent source review")
    r.closed(adoption, ("schema", "author", "status", "created_utc", "contract_sha256",
                       "source_review_sha256", "design_review_sha256", "supplement_sha256", "query_plan_sha256", "bootstrap_qualification_sha256", *FALSES))
    bc.validate_adoption(request, adoption)
    r.require(adoption["schema"] == "cho51_q_contract_adoption_v2"
              and adoption["author"] == "project_root" and adoption["status"] == "ADOPTED_QD_ONLY",
              "Q-only contract adoption")
    r.require(adoption["contract_sha256"] == request["sources"][CONTRACT]["sha256"]
              and adoption["source_review_sha256"] == request["review"]["sha256"]
              and adoption["design_review_sha256"] == request["sources"][DESIGN_REVIEW]["sha256"]
              and adoption["supplement_sha256"] == request["sources"][SUPPLEMENT]["sha256"],
              "adoption source/review/design join")
    r.require(adoption['query_plan_sha256']==request['sources']['tools/local_validation/lp18/api_query_plan.json']['sha256'], 'Q query plan adoption')
    r.require(utc(adoption["created_utc"]) <= utc(request["created_utc"])
              and all(adoption[k] is False for k in FALSES), "adoption order/authority")


def validate_report(report, expected, operation, checkpoint=None):
    r.closed(report, ("schema", "operation_id", "tests", "tests_run", "failures", "errors",
                      "skipped", "expected_failures", "unexpected_successes", "successful",
                      "report", "fixture_files", "fixture_bytes", "fixture_largest", "probe_observation", "probe_assets", "api_mapping", "api_mapping_native_identity", "native_diagnostic", "native_diagnostic_native_identity", "caller_artifact_capabilities", "sharing_controls", "sharing_test_ids", "sharing_separate", *FALSES))
    cohort = qualification_cohort(expected)
    validate_probe_observation(report['probe_observation'], cohort)
    validate_probe_assets(report['probe_assets'], cohort, checkpoint)
    ref(report['api_mapping'],PHASE+'/api-mapping_'+operation+'.json')
    r.require(type(report['api_mapping_native_identity']) is str and r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',report['api_mapping_native_identity']), 'mapping original identity')
    ref(report['native_diagnostic'],PHASE+'/native-diagnostic_'+operation+'.json')
    r.require(type(report['native_diagnostic_native_identity']) is str and r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',report['native_diagnostic_native_identity']), 'diagnostic original identity')
    caps=report['caller_artifact_capabilities']
    r.closed(report['sharing_controls'],('cooperative_read_protected','ordinary_reader_strict','capability_authentication'))
    r.require(all(v is True for v in report['sharing_controls'].values()),'actual native sharing controls')
    ids=sorted('tools.local_validation.lq18.test_native_reader.HandoffSharingTests.'+name for name in (
        'test_cooperative_read_preserves_unrelated_writer_delete_and_rename_denial',
        'test_ordinary_readers_remain_incompatible_with_live_writer',
        'test_capability_rejects_path_role_hash_and_native_identity_mismatch'))
    r.require(report['sharing_test_ids']==ids and report['sharing_separate'] is
              (cohort!='inherited'),'fresh exact sharing control execution')
    r.require(type(caps) is list and len(caps)==3 and {c['role'] for c in caps}=={'mapping','diagnostic','helper'},'three exact caller capabilities')
    for item in caps:
        r.closed(item,('role','path','bytes','sha256','native_identity','read_share'))
        r.windows_path(item['path'],absolute=True);pin({k:item[k] for k in ('bytes','sha256')})
        r.require(type(item['read_share']) is int and item['read_share']==3 and type(item['native_identity']) is str and r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',item['native_identity']),'scoped handoff sharing/identity')
    r.require(report["schema"] == "cho51_q_test_report_v1" and report["operation_id"] == operation,
              "test report identity")
    r.require(report["tests"] == expected and report["tests_run"] == len(expected)
              and type(report["tests_run"]) is int and report["successful"] is True, "complete exact test roster")
    for key in ("failures", "errors", "skipped", "expected_failures", "unexpected_successes"):
        r.require(type(report[key]) is int and report[key] == 0, "test failure or omission")
    r.exact_string(report["report"], 32768)
    r.exact_int(report["fixture_files"], upper=240)
    r.exact_int(report["fixture_bytes"], upper=48 * 1024**2)
    validate_allocation('fixtures', report['fixture_files'], report['fixture_bytes'], report['fixture_largest'])
    r.require(all(report[k] is False for k in FALSES), "test report authority")


def verify_bytes(raw, expected):
    pin(expected)
    r.require(type(raw) is bytes and len(raw) == expected["bytes"]
              and hashlib.sha256(raw).hexdigest() == expected["sha256"], "pinned byte mismatch")
    return raw










