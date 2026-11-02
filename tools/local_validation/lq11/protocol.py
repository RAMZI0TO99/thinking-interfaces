"""Closed Q4 admission and result contracts. No I/O and no operational grants."""
from datetime import datetime, timedelta, timezone
from pathlib import PureWindowsPath
import hashlib
import uuid
from ..v1 import records as r
from ..lp11 import bootstrap_contract as bc

STAGE = "Q"
PHASE = "runs/coordination/cho51_p3_frontier_20261031_q1"
CONTRACT = "docs/phase2/cho51_p3_local_validation_contract_20261029.md"
SUPPLEMENT = "docs/phase2/cho51_p3_frontier_kernel_contract_20261031.md"
DESIGN_REVIEW = "runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json"
INVENTORY_PACKAGE = 'tools.local_validation.lplan8'


def qualification_cohort(expected):
    """Two finite cohorts; the inherited roster is never replaced or truncated."""
    r.require(type(expected) is list and all(type(name) is str for name in expected), 'cohort roster')
    r.require(len(set(expected)) == len(expected), 'duplicate cohort ID')
    prefixes = tuple(INVENTORY_PACKAGE + '.test_compiler.' + group + '.'
                     for group in ('ResolverTests', 'FrontierTests'))
    counts = [sum(name.startswith(prefix) for name in expected) for prefix in prefixes]
    if len(expected) == 72 and counts == [40, 32]:
        return 'continuation'
    r.require(len(expected) == 384 and counts == [0, 0],
              'exact inherited384 or resolver40 plus frontier32 cohort')
    return 'inherited'


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
    "docs/phase2/cho51_p3_frontier_kernel_contract_20261031.md",
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
    "runs/coordination/cho51_p3_frontier_20261031_q1/candidate-migration.json",
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
    "tools/local_validation/lp11/api_mapping.py",
    "tools/local_validation/lp11/api_query_plan.json",
    "tools/local_validation/lp11/bootstrap_contract.py",
    "tools/local_validation/lp11/bootstrap_loader.ps1",
    "tools/local_validation/lp11/build_native.ps1",
    "tools/local_validation/lp11/caller_native.cs",
    "tools/local_validation/lp11/dependency_coverage.md",
    "tools/local_validation/lp11/dependency_recipe.json",
    "tools/local_validation/lp11/invoke_p.ps1",
    "tools/local_validation/lp11/manifest.py",
    "tools/local_validation/lp11/native_bootstrap.ps1",
    "tools/local_validation/lp11/native_policy.json",
    "tools/local_validation/lp11/native_reader.py",
    "tools/local_validation/lp11/pe.py",
    "tools/local_validation/lp11/protocol.py",
    "tools/local_validation/lp11/README.md",
    "tools/local_validation/lp11/supervisor.py",
    "tools/local_validation/lp11/test_bootstrap_contract.py",
    "tools/local_validation/lp11/test_long_paths.py",
    "tools/local_validation/lp11/test_manifest.py",
    "tools/local_validation/lp11/test_pe.py",
    "tools/local_validation/lp11/test_performance.py",
    "tools/local_validation/lp11/test_protocol.py",
    "tools/local_validation/lplan1/__init__.py",
    "tools/local_validation/lplan1/compiler.py",
    "tools/local_validation/lplan1/pytest.ini",
    "tools/local_validation/lplan1/README.md",
    "tools/local_validation/lplan1/seed-spec.json",
    "tools/local_validation/lplan1/test_compiler.py",
    "tools/local_validation/lplan8/__init__.py",
    "tools/local_validation/lplan8/compiler.py",
    "tools/local_validation/lplan8/migration.py",
    "tools/local_validation/lplan8/README.md",
    "tools/local_validation/lplan8/test_compiler.py",
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
    "tools/local_validation/lq11/bootstrap_controls.ps1",
    "tools/local_validation/lq11/bootstrap_probe.ps1",
    "tools/local_validation/lq11/build_l_native.ps1",
    "tools/local_validation/lq11/caller_native.cs",
    "tools/local_validation/lq11/child_entry.py",
    "tools/local_validation/lq11/invoke_q.ps1",
    "tools/local_validation/lq11/job_adapter.py",
    "tools/local_validation/lq11/l_native.py",
    "tools/local_validation/lq11/native_reader.py",
    "tools/local_validation/lq11/protocol.py",
    "tools/local_validation/lq11/README.md",
    "tools/local_validation/lq11/supervisor.py",
    "tools/local_validation/lq11/test_l_native.py",
    "tools/local_validation/lq11/test_native_reader.py",
    "tools/local_validation/lq11/test_protocol.py",
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
                     "scientific_admission", "compiler", "native_compiler", "bootstrap_qualification", "bootstrap_controls"))
    r.require(value["schema"] == "cho51_q_admission_v1" and value["stage"] == STAGE, "Q-only schema")
    r.require(value["operation_id"] == str(uuid.UUID(value["operation_id"])), "canonical UUID")
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
    qualification_cohort(value['expected_tests'])
    r.require(len(set(value["expected_tests"])) == len(value["expected_tests"]), "duplicate test id")
    for name in value["expected_tests"]:
        r.exact_string(name, 512)
        r.require(name.startswith(("tools.local_validation.v1.test_foundation.",
                                  "tools.local_validation.lq11.test_native_reader.",
                                  "tools.local_validation.lq11.test_protocol.",
                                  "tools.local_validation.p1.test_preparation.",
                                  "tools.local_validation.lp11.test_manifest.",
                                  "tools.local_validation.lp11.test_bootstrap_contract.",
                                  "tools.local_validation.lp11.test_long_paths.",
                                  "tools.local_validation.lp11.test_performance.",
                                  "tools.local_validation.lp11.test_pe.",
                                  "tools.local_validation.lp11.test_protocol.",
                                  "tools.local_validation.lq11.test_l_native.",
                                  "tools.local_validation.l1.test_",
                                  "tools.local_validation.lhost1.test_",
                                  "tools.local_validation.lplan1.test_",
                                  INVENTORY_PACKAGE+".test_compiler.")), "unexpected test module")
    return value


def validate_chain(request, review, adoption):
    r.require(review["status"] == "ACCEPTED_SOURCE_LQ1" and review["sources"] == request["sources"]
              and review["reviewer"] not in review["authors"], "exact independent source review")
    r.closed(adoption, ("schema", "author", "status", "created_utc", "contract_sha256",
                       "source_review_sha256", "design_review_sha256", "supplement_sha256", "query_plan_sha256", "bootstrap_qualification_sha256", *FALSES))
    bc.validate_adoption(request, adoption)
    r.require(adoption["schema"] == "cho51_q_contract_adoption_v2"
              and adoption["author"] == "project_root" and adoption["status"] == "ADOPTED_Q_ONLY",
              "Q-only contract adoption")
    r.require(adoption["contract_sha256"] == request["sources"][CONTRACT]["sha256"]
              and adoption["source_review_sha256"] == request["review"]["sha256"]
              and adoption["design_review_sha256"] == request["sources"][DESIGN_REVIEW]["sha256"]
              and adoption["supplement_sha256"] == request["sources"][SUPPLEMENT]["sha256"],
              "adoption source/review/design join")
    r.require(adoption['query_plan_sha256']==request['sources']['tools/local_validation/lp11/api_query_plan.json']['sha256'], 'Q query plan adoption')
    r.require(utc(adoption["created_utc"]) <= utc(request["created_utc"])
              and all(adoption[k] is False for k in FALSES), "adoption order/authority")


def validate_report(report, expected, operation):
    r.closed(report, ("schema", "operation_id", "tests", "tests_run", "failures", "errors",
                      "skipped", "expected_failures", "unexpected_successes", "successful",
                      "report", "fixture_files", "fixture_bytes", "api_mapping", "api_mapping_native_identity", "native_diagnostic", "native_diagnostic_native_identity", "caller_artifact_capabilities", "sharing_controls", "sharing_test_ids", "sharing_separate", *FALSES))
    ref(report['api_mapping'],PHASE+'/api-mapping_'+operation+'.json')
    r.require(type(report['api_mapping_native_identity']) is str and r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',report['api_mapping_native_identity']), 'mapping original identity')
    ref(report['native_diagnostic'],PHASE+'/native-diagnostic_'+operation+'.json')
    r.require(type(report['native_diagnostic_native_identity']) is str and r.re.fullmatch(r'[0-9a-f]{16}:[0-9a-f]{32}',report['native_diagnostic_native_identity']), 'diagnostic original identity')
    caps=report['caller_artifact_capabilities']
    r.closed(report['sharing_controls'],('cooperative_read_protected','ordinary_reader_strict','capability_authentication'))
    r.require(all(v is True for v in report['sharing_controls'].values()),'actual native sharing controls')
    ids=sorted('tools.local_validation.lq11.test_native_reader.HandoffSharingTests.'+name for name in (
        'test_cooperative_read_preserves_unrelated_writer_delete_and_rename_denial',
        'test_ordinary_readers_remain_incompatible_with_live_writer',
        'test_capability_rejects_path_role_hash_and_native_identity_mismatch'))
    r.require(report['sharing_test_ids']==ids and report['sharing_separate'] is
              (qualification_cohort(expected)=='continuation'),'fresh exact sharing control execution')
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
    r.require(all(report[k] is False for k in FALSES), "test report authority")


def verify_bytes(raw, expected):
    pin(expected)
    r.require(type(raw) is bytes and len(raw) == expected["bytes"]
              and hashlib.sha256(raw).hexdigest() == expected["sha256"], "pinned byte mismatch")
    return raw










