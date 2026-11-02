"""Closed Q4 admission and result contracts. No I/O and no operational grants."""
from datetime import datetime, timedelta, timezone
from pathlib import PureWindowsPath
import hashlib
import uuid
from ..v1 import records as r

STAGE = "Q"
PHASE = "runs/coordination/cho51_p3_dependency_prepare_20261029_q4"
CONTRACT = "docs/phase2/cho51_p3_local_validation_contract_20261029.md"
SUPPLEMENT = "docs/phase2/cho51_p3_p2r4_dependency_contract_20261029.md"
DESIGN_REVIEW = "runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json"
REQUIRED = (
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p3/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p3/root-disposition.json",
    "tools/local_validation/p2r4/test_performance.py",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/actual-review.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/root-disposition.json",
    "runs/coordination/cho51_p3_dependency_prepare_20261029_p2/static-path-diagnosis.json",
    "tools/local_validation/p2r4/native_reader.py",
    "tools/local_validation/p2r4/test_long_paths.py",
    "tools/local_validation/p2q4/native_reader.py",
    "tools/local_validation/p2q4/test_native_reader.py",
    "tools/local_validation/p2q4/job_adapter.py",
    "tools/local_validation/p2q4/protocol.py",
    "tools/local_validation/p2q4/test_protocol.py",
    "tools/local_validation/p2q4/child_entry.py",
    "tools/local_validation/p2q4/supervisor.py",
    "tools/local_validation/p2q4/invoke_q.ps1",
    "tools/local_validation/p2q4/caller_native.cs",
    "tools/local_validation/p2q4/README.md",
    "tools/local_validation/v1/records.py",
    "tools/local_validation/v1/preparation.py",
    "tools/local_validation/v1/test_foundation.py",
    "tools/local_validation/v1/README.md",
    "evaluation/phase2_supervision_primitives.py",
    "docs/PROJECT_EXECUTION_POLICY.md", CONTRACT, DESIGN_REVIEW, SUPPLEMENT,
    "runs/coordination/cho51_p3_q_qualification_20261029_q1/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q1/root-disposition.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/root-disposition.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q2/timestamp-metadata-analysis.json",
    "docs/phase2/cho51_p3_q2_bootstrap_contract_20261029.md",
    "runs/coordination/cho51_p3_q_qualification_20261029_q3/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q3/root-disposition.json",
    "docs/phase2/cho51_p3_q3_utc_contract_20261029.md",
    "docs/phase2/cho51_p3_q4_reader_contract_20261029.md",
    "tools/local_validation/q4/native_reader.py",
    "tools/local_validation/p1/preparation.py",
    "tools/local_validation/p1/test_preparation.py",
    "tools/local_validation/p1/README.md",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/source-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/actual-review.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/root-qualification.json",
    "runs/coordination/cho51_p3_q_qualification_20261029_q4/final-closeout.json",
    "tools/local_validation/p2r4/protocol.py",
    "tools/local_validation/p2r4/supervisor.py",
    "tools/local_validation/p2r4/invoke_p.ps1",
    "tools/local_validation/p2r4/caller_native.cs",
    "tools/local_validation/p2r4/manifest.py",
    "tools/local_validation/p2r4/pe.py",
    "tools/local_validation/p2r4/dependency_recipe.json",
    "tools/local_validation/p2r4/dependency_coverage.md",
    "tools/local_validation/p2r4/native_policy.json",
    "tools/local_validation/p2r4/README.md",
    "docs/phase2/cho51_p3_local_validation_v1/dependency-plan.json",
    "runs/coordination/cho51_p3_preparation_engine_20261029_p1q/root-qualification.json",
    "tools/local_validation/p2r4/build_native.ps1",
    "tools/local_validation/p2r4/test_manifest.py",
    "tools/local_validation/p2r4/test_pe.py",
    "tools/local_validation/p2r4/test_protocol.py",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/root-qualification.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/actual-review.json",
    "runs/coordination/cho51_p3_git_materialization_20261029_r1/seal_49b1f44d-46ef-446e-a8fd-85a3ddb7ce36.json",
    "docs/phase2/cho51_p3_p2_dependency_contract_20261029.md",
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
MODES = ("suite", "badframe", "stall")
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
                     "scientific_admission", "compiler"))
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
    r.require(type(value["expected_tests"]) is list and 1 <= len(value["expected_tests"]) <= 192,
              "bounded exact test roster")
    r.require(len(set(value["expected_tests"])) == len(value["expected_tests"]), "duplicate test id")
    for name in value["expected_tests"]:
        r.exact_string(name, 512)
        r.require(name.startswith(("tools.local_validation.v1.test_foundation.",
                                  "tools.local_validation.p2q4.test_native_reader.",
                                  "tools.local_validation.p2q4.test_protocol.",
                                  "tools.local_validation.p1.test_preparation.",
                                  "tools.local_validation.p2r4.test_manifest.",
                                  "tools.local_validation.p2r4.test_long_paths.",
                                  "tools.local_validation.p2r4.test_performance.",
                                  "tools.local_validation.p2r4.test_pe.",
                                  "tools.local_validation.p2r4.test_protocol.")), "unexpected test module")
    return value


def validate_chain(request, review, adoption):
    r.require(review["status"] == "ACCEPTED_SOURCE_P2Q" and review["sources"] == request["sources"]
              and review["reviewer"] not in review["authors"], "exact independent source review")
    r.closed(adoption, ("schema", "author", "status", "created_utc", "contract_sha256",
                       "source_review_sha256", "design_review_sha256", "supplement_sha256", *FALSES))
    r.require(adoption["schema"] == "cho51_q_contract_adoption_v2"
              and adoption["author"] == "project_root" and adoption["status"] == "ADOPTED_Q_ONLY",
              "Q-only contract adoption")
    r.require(adoption["contract_sha256"] == request["sources"][CONTRACT]["sha256"]
              and adoption["source_review_sha256"] == request["review"]["sha256"]
              and adoption["design_review_sha256"] == request["sources"][DESIGN_REVIEW]["sha256"]
              and adoption["supplement_sha256"] == request["sources"][SUPPLEMENT]["sha256"],
              "adoption source/review/design join")
    r.require(utc(adoption["created_utc"]) <= utc(request["created_utc"])
              and all(adoption[k] is False for k in FALSES), "adoption order/authority")


def validate_report(report, expected, operation):
    r.closed(report, ("schema", "operation_id", "tests", "tests_run", "failures", "errors",
                      "skipped", "expected_failures", "unexpected_successes", "successful",
                      "report", "fixture_files", "fixture_bytes", *FALSES))
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



