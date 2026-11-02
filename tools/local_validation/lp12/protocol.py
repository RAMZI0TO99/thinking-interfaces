"""Closed file-only P stage records; source and coverage are separate gates."""
from datetime import datetime, timedelta
import hashlib
import re
import uuid
from ..v1 import records as r
from . import api_mapping as am
from . import bootstrap_contract as bc

PHASE = 'runs/coordination/cho51_p3_lossless_20261101_p1'
Q_PHASE = 'runs/coordination/cho51_p3_lossless_20261101_q1'
CONTRACT = 'docs/phase2/cho51_p3_local_validation_contract_20261029.md'
SUPPLEMENT = 'docs/phase2/cho51_p3_lossless_codec_contract_20261101.md'
DESIGN_REVIEW = 'runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json'
REQUIRED = (
    "docs/phase2/cho51_p3_adapter_v2/contracts.py",
    "docs/phase2/cho51_p3_adapter_v2/mapping.py",
    "docs/phase2/cho51_p3_adapter_v2/README.md",
    "docs/phase2/cho51_p3_adapter_v2/telemetry.py",
    "docs/phase2/cho51_p3_adapter_v2/test_mapping.py",
    "docs/phase2/cho51_p3_adapter_v2/test_telemetry.py",
    "docs/phase2/cho51_p3_candidate_inventory_contract_20261031.md",
    "docs/phase2/cho51_p3_lossless_codec_contract_20261101.md",
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
    "runs/coordination/cho51_p3_lossless_20261101_q1/candidate-migration.json",
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
    "tools/local_validation/lp12/api_mapping.py",
    "tools/local_validation/lp12/api_query_plan.json",
    "tools/local_validation/lp12/bootstrap_contract.py",
    "tools/local_validation/lp12/bootstrap_loader.ps1",
    "tools/local_validation/lp12/build_native.ps1",
    "tools/local_validation/lp12/caller_native.cs",
    "tools/local_validation/lp12/dependency_coverage.md",
    "tools/local_validation/lp12/dependency_recipe.json",
    "tools/local_validation/lp12/invoke_p.ps1",
    "tools/local_validation/lp12/manifest.py",
    "tools/local_validation/lp12/native_bootstrap.ps1",
    "tools/local_validation/lp12/native_policy.json",
    "tools/local_validation/lp12/native_reader.py",
    "tools/local_validation/lp12/pe.py",
    "tools/local_validation/lp12/protocol.py",
    "tools/local_validation/lp12/README.md",
    "tools/local_validation/lp12/supervisor.py",
    "tools/local_validation/lp12/test_bootstrap_contract.py",
    "tools/local_validation/lp12/test_long_paths.py",
    "tools/local_validation/lp12/test_manifest.py",
    "tools/local_validation/lp12/test_pe.py",
    "tools/local_validation/lp12/test_performance.py",
    "tools/local_validation/lp12/test_protocol.py",
    "tools/local_validation/lplan1/__init__.py",
    "tools/local_validation/lplan1/compiler.py",
    "tools/local_validation/lplan1/pytest.ini",
    "tools/local_validation/lplan1/README.md",
    "tools/local_validation/lplan1/seed-spec.json",
    "tools/local_validation/lplan1/test_compiler.py",
    "tools/local_validation/lplan9/__init__.py",
    "tools/local_validation/lplan9/compiler.py",
    "tools/local_validation/lplan9/migration.py",
    "tools/local_validation/lplan9/README.md",
    "tools/local_validation/lplan9/test_compiler.py",
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
    "tools/local_validation/lq12/bootstrap_controls.ps1",
    "tools/local_validation/lq12/bootstrap_probe.ps1",
    "tools/local_validation/lq12/build_l_native.ps1",
    "tools/local_validation/lq12/caller_native.cs",
    "tools/local_validation/lq12/child_entry.py",
    "tools/local_validation/lq12/invoke_q.ps1",
    "tools/local_validation/lq12/job_adapter.py",
    "tools/local_validation/lq12/l_native.py",
    "tools/local_validation/lq12/native_reader.py",
    "tools/local_validation/lq12/protocol.py",
    "tools/local_validation/lq12/README.md",
    "tools/local_validation/lq12/supervisor.py",
    "tools/local_validation/lq12/test_l_native.py",
    "tools/local_validation/lq12/test_native_reader.py",
    "tools/local_validation/lq12/test_protocol.py",
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
LIMITS = {'whole_seconds':300, 'work_seconds':240, 'cleanup_seconds':5,
          'process_mib':4096, 'job_mib':5120, 'parent_mib':4096,
          'startup_ram_gib':4, 'active_ram_gib':4, 'disk_gib':20,
          'stream_bytes':1048576, 'threads':1, 'gpu_visible':False}
FALSES = {'historical_custody_closed':False, 'historical_operation_released':False,
          'historical_retry_allowed':False, 'restart_qualified':False, 'boundary_qualified':False,
          'complete_dependency_closure':False, 'launch_authorized':False, 'scientific_admission':False}
FORBIDDEN = ['candidate_imports','third_party_imports','execution_or_bytecode_compilation_of_dependency_sources',
             'native_source_compilation','numerical_work','data_or_weights','network','git',
             'unowned_processes','historical_launcher_replay']
EXPECTED_Q_TESTS = 384
BUILDER_TRUE_KEYS = ('emitted_pe_verified','original_output_identity_retained',
    'loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed',
    'l_two_process_limits_query_verified','l_empty_job_closed','l_invalid_process_count_refused')


def pin(value, cap=8*1024**2):
    r.closed(value, ('bytes','sha256'))
    r.exact_int(value['bytes'], upper=cap)
    r.require(type(value['sha256']) is str and r.HEX64.fullmatch(value['sha256']), 'pin digest')
    return value


def utc(text):
    r.exact_string(text,64)
    value=datetime.fromisoformat(text.replace('Z','+00:00'))
    r.require(value.utcoffset()==timedelta(0),'explicit UTC')
    return value


def validate(value, root, origin):
    value=r.defensive_copy(value)
    r.closed(value, ('schema','stage','operation_id','created_utc','expires_utc','root',
        'python','runtime','caller_runtime','sources','review','adoption','qualification',
        'native_helper','map_index','coverage_review','extra_paths','limits','forbidden','scientific_admission','api_mapping','native_diagnostic','l_native_bundle','plan_spec','bootstrap_qualification','qualification_aggregate'))
    r.require(value['schema']=='cho51_resolver_p_admission_v1' and value['stage']=='P','P-only admission')
    r.require(value['operation_id']==str(uuid.UUID(value['operation_id'])),'canonical UUID')
    r.require(value['root']==root,'exact project root')
    start,end,origin=map(utc,(value['created_utc'],value['expires_utc'],origin))
    r.require(start<=origin and origin+timedelta(seconds=300)<=end and
              300<=(end-start).total_seconds()<=900,'original complete P window')
    r.require(r.canonical_bytes(value['limits'])==r.canonical_bytes(LIMITS),'P exact limits')
    r.require(value['forbidden']==FORBIDDEN and value['scientific_admission'] is False,'P effects')
    r.require(type(value['sources']) is dict and set(value['sources'])==set(REQUIRED),'exact P sources')
    for item in value['sources'].values(): pin(item)
    bc.validate_request(value)
    r.closed(value['caller_runtime'],('path','bytes','sha256','version'))
    r.windows_path(value['caller_runtime']['path'],absolute=True)
    pin({k:value['caller_runtime'][k] for k in ('bytes','sha256')})
    r.require(value['caller_runtime']['version'].startswith('7.'),'PowerShell7 caller')
    runtime=value['runtime']
    r.closed(runtime,('root','files','recipe','platform_trust'))
    r.windows_path(runtime['root'],absolute=True)
    r.require(runtime['recipe']=='python.exe+root-dll+Lib-py-without-site-packages-or-pycache+DLLs-pyd-dll'
        and runtime['platform_trust']=='reviewed-local-Windows-and-PowerShell-host-no-loaded-code-attestation',
        'bootstrap runtime recipe/trust')
    r.require(value['python']==runtime['root']+'/python.exe' and value['python'] in runtime['files'], 'Python path')
    r.require(type(runtime['files']) is dict and 1<=len(runtime['files'])<=2000,'bootstrap runtime count')
    total=0;seen=set()
    for path,item in runtime['files'].items():
        r.windows_path(path,absolute=True)
        r.require(path.startswith(runtime['root']+'/') and path.lower() not in seen,'runtime scope/alias')
        seen.add(path.lower())
        pin(item,64*1024**2);total+=item['bytes']
    r.require(total<=64*1024**2,'bootstrap runtime bytes')
    expected={'review':PHASE+'/source-review.json','adoption':PHASE+'/contract-adoption.json',
        'qualification':Q_PHASE+'/root-qualification.json','qualification_aggregate':Q_PHASE+'/qualification-aggregate.json','map_index':PHASE+'/pin-index.json',
        'coverage_review':PHASE+'/coverage-review.json','plan_spec':PHASE+'/plan-spec.json'}
    for key in (*expected,'native_helper'):
        ref=value[key];r.closed(ref,('path','bytes','sha256'));r.windows_path(ref['path'])
        if key in expected:r.require(ref['path']==expected[key],'exact control reference')
        else:r.require(ref['path'].startswith(Q_PHASE+'/native-helper_') and ref['path'].endswith('.dll'),'qualified native artifact')
        pin({k:ref[k] for k in ('bytes','sha256')})
    r.require(type(value['extra_paths']) is list and len(value['extra_paths'])<=256,'extra input count')
    for path in value['extra_paths']:r.windows_path(path,absolute=True)
    r.require(len({p.lower() for p in value['extra_paths']})==len(value['extra_paths']),'duplicate/case-alias extra input')
    ref=value['api_mapping'];r.closed(ref,('path','bytes','sha256'))
    r.windows_path(ref['path'])
    r.require(re.fullmatch(re.escape(Q_PHASE)+r'/api-mapping_[0-9a-f-]{36}\.json',ref['path']), 'Q mapping reference')
    pin({k:ref[k] for k in ('bytes','sha256')})
    ref=value['native_diagnostic'];r.closed(ref,('path','bytes','sha256'));r.windows_path(ref['path'])
    r.require(re.fullmatch(re.escape(Q_PHASE)+r'/native-diagnostic_[0-9a-f-]{36}\.json',ref['path']), 'Q diagnostic reference')
    pin({k:ref[k] for k in ('bytes','sha256')})
    ref=value['l_native_bundle'];r.closed(ref,('path','bytes','sha256'));r.windows_path(ref['path'])
    r.require(re.fullmatch(re.escape(Q_PHASE)+r'/l-bundle_[0-9a-f-]{36}\.json',ref['path']), 'L native bundle reference')
    pin({k:ref[k] for k in ('bytes','sha256')})
    return value


def _accepted_review(value, status):
    """Validate core fields of a separately versioned full evidence record."""
    value=r.defensive_copy(value)
    r.require(type(value) is dict and all(k in value for k in
        ('schema','status','reviewer','authors','created_utc','findings','checks','limitations')),
        'accepted review core fields')
    r.require(type(value['schema']) is str and value['schema'].endswith('_v1')
        and value['status']==status,'versioned accepted review')
    authors=value['authors']
    r.require(type(authors) is list and 1<=len(authors)<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in authors) and len(set(authors))==len(authors),
        'review author identities')
    r.require(type(value['reviewer']) is str and 0<len(value['reviewer'])<=128
        and value['reviewer'] not in authors,'independent review identity')
    r.require(type(value['findings']) is list and value['findings']==[],'no unresolved review findings')
    for field in ('checks','limitations'):
        r.require(type(value[field]) is list and len(value[field])<=256 and
            all(type(s) is str and 0<len(s)<=4096 for s in value[field]),'typed review statements')
    utc(value['created_utc'])
    return value


AGGREGATE_REFS = ('source_review', 'primary_qualification', 'primary_admission',
                  'primary_actual', 'secondary_qualification', 'secondary_admission',
                  'secondary_actual')


def aggregate_references(value):
    """Closed, finite content references, validated before any retained read."""
    r.closed(value, ('schema','status','author','created_utc',*AGGREGATE_REFS,
                     'expected_counts','launch_authorized','scientific_admission'))
    r.require(value['schema']=='cho51_resolver_q_aggregate_v1' and
              value['status']=='ACCEPTED_BOTH_Q_COHORTS' and value['author']=='project_root',
              'Q aggregate schema/status')
    r.require(value['launch_authorized'] is False and value['scientific_admission'] is False,
              'Q aggregate no execution grant')
    r.require(r.canonical_bytes(value['expected_counts'])==r.canonical_bytes({'inherited':384,'resolver':40}),
              'complete384+40 aggregate counts')
    fixed={'source_review':'source-review.json','primary_qualification':'root-qualification.json',
           'primary_actual':'actual-review.json','secondary_qualification':'resolver-qualification.json',
           'secondary_actual':'resolver-actual-review.json'}
    for key in AGGREGATE_REFS:
        item=value[key];r.closed(item,('path','bytes','sha256'));r.windows_path(item['path'])
        pin({k:item[k] for k in ('bytes','sha256')})
        if key in fixed:
            r.require(item['path']==Q_PHASE+'/'+fixed[key], 'fixed aggregate reference')
        else:
            r.require(re.fullmatch(re.escape(Q_PHASE)+r'/admission_[0-9a-f-]{36}\.json',item['path']) is not None,
                      'finite cohort admission reference')
    utc(value['created_utc'])
    return {key:value[key] for key in AGGREGATE_REFS}


def validate_aggregate(request, aggregate, material, primary_qualification):
    """Require both actual cohorts on identical current source/runtime identities.

    P still consumes only the primary cohort's native artifacts. The second
    cohort's accepted test and lifecycle evidence is an additional prerequisite.
    """
    refs=aggregate_references(aggregate)
    r.closed(material, AGGREGATE_REFS)
    r.require(refs['primary_qualification']==request['qualification'] and
              material['primary_qualification']==primary_qualification, 'primary aggregate join')
    source=_accepted_review(material['source_review'],'ACCEPTED_SOURCE_LQ1')
    r.require(source['sources']==request['sources'], 'aggregate exact current source set')
    operations=[];identities=[]
    resolver_prefix='tools.local_validation.lplan9.test_compiler.ResolverTests.'
    for role,count in (('primary',384),('secondary',40)):
        qualification=material[role+'_qualification'];actual=material[role+'_actual']
        admission=material[role+'_admission']
        r.closed(admission, ('schema','stage','operation_id','created_utc','expires_utc','root','python',
            'runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests',
            'forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls'))
        r.require(type(qualification) is dict and set(qualification)==set(primary_qualification),
                  'same closed cohort qualification schema')
        operation=qualification['operation_id']
        r.require(type(operation) is str and operation==str(uuid.UUID(operation)), 'cohort UUID')
        operations.append(operation)
        r.require(qualification['schema']=='cho51_p2q_root_qualification_v1' and
                  qualification['status']=='QUALIFIED_LQ1_MECHANISMS_ONLY' and qualification['author']=='project_root'
                  and all(qualification[k] is False for k in FALSES), 'cohort qualification authority')
        r.require(qualification['source_review']==refs['source_review'] and
                  qualification['actual_review']==refs[role+'_actual'], 'cohort exact review refs')
        _accepted_review(actual,'ACCEPTED_LQ1_TESTED_SCOPE')
        r.require(actual['reviewer']!=source['reviewer'] and actual['reviewer'] not in source['authors']
                  and source['reviewer'] not in actual['authors'], 'cohort independent reviewers')
        r.require(actual.get('admission')==refs[role+'_admission'] and actual.get('operation_id')==operation
                  and actual.get('source_review_sha256')==refs['source_review']['sha256'], 'actual cohort admission join')
        r.require(type(admission) is dict and admission.get('schema')=='cho51_q_admission_v1'
                  and admission.get('stage')=='Q' and admission.get('operation_id')==operation
                  and refs[role+'_admission']['path']==Q_PHASE+'/admission_'+operation+'.json', 'cohort admission identity')
        r.require(admission['review']==dict(path='source-review.json',**{k:refs['source_review'][k] for k in ('bytes','sha256')}),
                  'admitted source review identity')
        expected=admission['expected_tests']
        r.require(type(expected) is list and len(expected)==count
                  and all(type(name) is str and name.startswith('tools.local_validation.') for name in expected),
                  'exact cohort roster')
        r.require(len(set(expected))==count, 'unique cohort IDs')
        r.require(all(name.startswith(resolver_prefix)==(role=='secondary') for name in expected), 'cohort partition')
        r.require(actual.get('test_roster_sha256')==hashlib.sha256(r.canonical_bytes(expected)).hexdigest(),
                  'actual accepted test IDs match admission')
        for field,expected_value in (('test_count',count),('timestamp_controls',8),('native_fault_controls',2)):
            r.require(type(qualification[field]) is int and qualification[field]==expected_value, 'cohort qualification counts')
        for field,expected_value in (('tests_run',count),('timestamp_controls_passed',8),('native_fault_controls_passed',2),('actual_tool_exit_code',0)):
            r.require(type(actual.get(field)) is int and actual[field]==expected_value, 'cohort actual counts/exit')
        r.require(actual.get('new_operation_owned_lifecycle_closed') is True and
                  actual.get('final_input_verification') is True, 'cohort final verification and cleanup')
        r.require(all(actual.get(key) is False for key in FALSES), 'actual cohort no authority expansion')
        _builder(qualification['native_builder_controls']);_builder(actual.get('native_builder_controls'))
        bc.validate_qualification(qualification,actual)
        for key in ('native_helper','native_builder_controls','api_mapping','api_mapping_native_identity',
                    'native_diagnostic','native_diagnostic_native_identity','artifact_handoff',
                    'sharing_controls','l_native_bundle','l_native_bundle_identity','l_native_cases'):
            r.require(qualification[key]==actual.get(key), 'cohort native/control join')
        r.require(qualification['l_native_cases']==['transient','overflow','badreason','badutf16','pathbound'],
                  'all native observer cases')
        r.closed(qualification['sharing_controls'],('cooperative_read_protected','ordinary_reader_strict','capability_authentication'))
        r.require(all(v is True for v in qualification['sharing_controls'].values()), 'all sharing controls')
        handoff=qualification['artifact_handoff']
        r.closed(handoff,('consumers_reaped','final_original_recheck','original_writers_held_through_consumers','artifacts'))
        r.require(all(handoff[k] is True for k in ('consumers_reaped','final_original_recheck','original_writers_held_through_consumers')),
                  'cohort original artifact custody')
        for key in ('sources','runtime','caller_runtime','python','root'):
            r.require(r.canonical_bytes(admission[key])==r.canonical_bytes(request[key]), 'cohort current '+key)
        identities.append(r.canonical_bytes({key:admission[key] for key in
                         ('sources','runtime','caller_runtime','compiler','native_compiler','python','root')}))
        r.require(utc(source['created_utc'])<=utc(admission['created_utc'])<=utc(actual['created_utc'])
                  <=utc(qualification['created_utc'])<=utc(aggregate['created_utc'])<=utc(request['created_utc']),
                  'cohort review/admission/acceptance order')
    r.require(operations[0]!=operations[1] and identities[0]==identities[1], 'distinct operations, identical source/runtime roles')
    return {'schema':'cho51_resolver_q_aggregate_observation_v1','cohorts':['inherited','resolver'],
            'counts':[384,40],'operation_ids':operations,'launch_authorized':False,'scientific_admission':False}


def _builder(value):
    r.closed(value,(*BUILDER_TRUE_KEYS,'helper_identity'))
    r.require(all(value[k] is True for k in BUILDER_TRUE_KEYS) and
        type(value['helper_identity']) is str and
        re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',value['helper_identity']) is not None,
        'qualified native builder controls/identity')


def validate_chain(request, review, adoption, qualification, coverage,
                   q_source_review, q_actual_review, api_receipt, query_plan):
    r.closed(review,('schema','status','reviewer','authors','created_utc','sources','findings','checks','limitations'))
    r.require(review['schema']=='cho51_p2_source_review_v1' and
        type(review['authors']) is list and 1<=len(review['authors'])<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in review['authors']) and
        type(review['reviewer']) is str and 0<len(review['reviewer'])<=128 and
        review['findings']==[],'closed independent source review identity')
    r.require(review['status']=='ACCEPTED_SOURCE_LP1' and review['sources']==request['sources']
        and review['reviewer'] not in review['authors'],'P independent source review')
    r.closed(adoption,('schema','author','status','created_utc','contract_sha256','source_review_sha256',
        'design_review_sha256','supplement_sha256','bootstrap_qualification_sha256','qualification_sha256','qualification_aggregate_sha256','coverage_review_sha256','api_mapping_sha256','native_diagnostic_sha256','l_native_bundle_sha256','plan_spec_sha256',*FALSES))
    r.require(adoption['schema']=='cho51_p_contract_adoption_v1' and adoption['status']=='ADOPTED_P_ONLY'
        and adoption['author']=='project_root','P adoption')
    bc.validate_adoption(request, adoption)
    joins={'contract_sha256':request['sources'][CONTRACT]['sha256'],
        'source_review_sha256':request['review']['sha256'],
        'design_review_sha256':request['sources'][DESIGN_REVIEW]['sha256'],
        'supplement_sha256':request['sources'][SUPPLEMENT]['sha256'],
        'qualification_sha256':request['qualification']['sha256'],
        'qualification_aggregate_sha256':request['qualification_aggregate']['sha256'],
        'coverage_review_sha256':request['coverage_review']['sha256'], 'api_mapping_sha256':request['api_mapping']['sha256'],
        'native_diagnostic_sha256':request['native_diagnostic']['sha256'],
        'l_native_bundle_sha256':request['l_native_bundle']['sha256'],'plan_spec_sha256':request['plan_spec']['sha256']}
    r.require(all(adoption[k]==v for k,v in joins.items()) and all(adoption[k] is False for k in FALSES), 'adoption joins/flags')
    r.require(utc(adoption['created_utc'])<=utc(request['created_utc']),'adoption order')
    r.closed(qualification,('schema','status','author','created_utc','operation_id','source_review',
        'actual_review','native_helper','test_count','timestamp_controls','native_fault_controls',
        'native_builder_controls','api_mapping','api_mapping_native_identity','native_diagnostic','native_diagnostic_native_identity','artifact_handoff','sharing_controls','l_native_bundle','l_native_bundle_identity','l_native_cases','bootstrap_controls',*FALSES))
    r.require(qualification['schema']=='cho51_p2q_root_qualification_v1' and
        qualification['author']=='project_root' and
        all(qualification[k] is False for k in FALSES),'Q qualification schema/authority')
    r.require(qualification['status']=='QUALIFIED_LQ1_MECHANISMS_ONLY'
        and qualification['native_helper']==request['native_helper'],'qualified binary join')
    operation=qualification['operation_id']
    r.require(type(operation) is str and operation==str(uuid.UUID(operation)),'canonical Q operation UUID')
    for key,name in (('source_review','source-review.json'),('actual_review','actual-review.json')):
        ref=qualification[key]
        r.closed(ref,('path','bytes','sha256'))
        r.require(ref['path']==Q_PHASE+'/'+name,'exact Q review reference')
        pin({k:ref[k] for k in ('bytes','sha256')})
    r.require(operation in qualification['native_helper']['path'].rsplit('/',1)[-1],
        'native helper bound to Q operation')
    for field,expected in (('test_count',EXPECTED_Q_TESTS),('timestamp_controls',8),('native_fault_controls',2)):
        r.require(type(qualification[field]) is int and qualification[field]==expected,'qualified exact Q counts')
    _builder(qualification['native_builder_controls'])
    source=_accepted_review(q_source_review,'ACCEPTED_SOURCE_LQ1')
    actual=_accepted_review(q_actual_review,'ACCEPTED_LQ1_TESTED_SCOPE')
    bc.validate_qualification(qualification, actual)
    r.require(type(source.get('sources')) is dict and 1<=len(source['sources'])<=256,
        'Q reviewed source pins')
    for path,item in source['sources'].items():
        r.windows_path(path)
        pin(item)
    r.require(all(source['sources'].get(path)==item for path,item in request['sources'].items()),
        'Q source review covers exact P sources')
    r.require(actual['reviewer']!=source['reviewer'] and actual['reviewer'] not in source['authors']
        and source['reviewer'] not in actual['authors'],'different Q source/actual reviewers')
    r.require(actual.get('operation_id')==operation and
        actual.get('source_review_sha256')==qualification['source_review']['sha256'],
        'Q actual operation/source-review join')
    for field,expected in (('tests_run',EXPECTED_Q_TESTS),('timestamp_controls_passed',8),
                           ('native_fault_controls_passed',2),('actual_tool_exit_code',0)):
        r.require(type(actual.get(field)) is int and actual[field]==expected,'actual exact Q counts/exit')
    r.require(actual.get('new_operation_owned_lifecycle_closed') is True and
        actual.get('native_helper')==qualification['native_helper'],'actual Q lifecycle/native artifact')
    _builder(actual.get('native_builder_controls'))
    r.require(qualification['l_native_bundle']==request['l_native_bundle']==actual.get('l_native_bundle')
        and qualification['l_native_bundle_identity']==actual.get('l_native_bundle_identity')
        and qualification['l_native_cases']==actual.get('l_native_cases')==['transient','overflow','badreason','badutf16','pathbound'],
        'fresh qualified L native build/cases join')
    r.require(re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',qualification['l_native_bundle_identity']) is not None,'L native bundle original identity')
    r.require(actual['native_builder_controls']==qualification['native_builder_controls'],
        'native builder control join')
    r.require(qualification['api_mapping']==request['api_mapping'] and
        actual.get('api_mapping')==qualification['api_mapping'] and
        actual.get('api_mapping_native_identity')==qualification['api_mapping_native_identity'] and
        request['api_mapping']['path']==Q_PHASE+'/api-mapping_'+operation+'.json', 'accepted Q mapping receipt join')
    am.validate_receipt(api_receipt,query_plan,operation,qualification['native_helper'],
        qualification['api_mapping_native_identity'],request['sources'][am.PLAN]['sha256'])
    r.require(api_receipt['native_helper_native_identity']==qualification['native_builder_controls']['helper_identity'], 'emitted helper original native identity join')
    r.require(qualification['native_diagnostic']==request['native_diagnostic']==actual.get('native_diagnostic')==api_receipt['native_diagnostic']
        and qualification['native_diagnostic_native_identity']==actual.get('native_diagnostic_native_identity')==api_receipt['native_diagnostic_native_identity'], 'accepted diagnostic reference/identity join')
    handoff=qualification['artifact_handoff']
    r.closed(qualification['sharing_controls'],('cooperative_read_protected','ordinary_reader_strict','capability_authentication'))
    r.require(qualification['sharing_controls']==actual.get('sharing_controls') and all(v is True for v in qualification['sharing_controls'].values()),'accepted actual sharing controls')
    r.closed(handoff,('consumers_reaped','final_original_recheck','original_writers_held_through_consumers','artifacts'))
    r.require(handoff==actual.get('artifact_handoff') and all(handoff[k] is True for k in
        ('consumers_reaped','final_original_recheck','original_writers_held_through_consumers')),'accepted original-writer custody/return')
    expected_artifacts={'mapping':(request['api_mapping'],qualification['api_mapping_native_identity']),
        'diagnostic':(request['native_diagnostic'],qualification['native_diagnostic_native_identity']),
        'helper':(request['native_helper'],qualification['native_builder_controls']['helper_identity'])}
    items=handoff['artifacts']
    r.require(type(items) is list and len(items)==3 and {i['role'] for i in items}==set(expected_artifacts),'three qualified handoff artifacts')
    for item in items:
        r.closed(item,('role','reference','native_identity','writer_share'))
        ref,identity=expected_artifacts[item['role']]
        r.require(item['reference']==ref and item['native_identity']==identity and type(item['writer_share']) is int and item['writer_share']==1,'exact qualified original writer')
    r.require(utc(source['created_utc'])<=utc(actual['created_utc'])<=utc(qualification['created_utc'])
        <=utc(adoption['created_utc'])<=utc(request['created_utc']),'Q review/qualification/adoption order')
    r.closed(coverage,('schema','status','reviewer','authors','created_utc','recipe_sha256',
        'pin_index','findings','checks','limitations','launch_authorized','scientific_admission'))
    r.require(coverage['schema']=='cho51_p2_coverage_review_v1' and
        type(coverage['authors']) is list and 1<=len(coverage['authors'])<=8 and
        all(type(a) is str and 0<len(a)<=128 for a in coverage['authors']) and
        type(coverage['reviewer']) is str and coverage['reviewer'] not in coverage['authors']
        and coverage['findings']==[],'coverage independent identity')
    r.require(coverage['status']=='ACCEPTED_PROPOSED_P2_PHYSICAL_COVERAGE'
        and coverage['pin_index']==request['map_index'] and
        coverage['recipe_sha256']==request['sources']['tools/local_validation/lp12/dependency_recipe.json']['sha256'],
        'coverage recipe/map join')
    r.require(coverage['launch_authorized'] is False and coverage['scientific_admission'] is False,'coverage no grant')










