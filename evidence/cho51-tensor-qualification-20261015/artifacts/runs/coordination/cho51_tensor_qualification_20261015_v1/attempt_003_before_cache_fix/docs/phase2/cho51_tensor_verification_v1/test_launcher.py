"""Fabricated-file launcher boundaries; native proof and subprocess are mocked.

These tests do not execute a guard, restore tensors, inspect EEG arrays, or
qualify native supervision. The independent guarded integration owns that
evidence. Dummy project/runtime bytes make file and digest checks real here.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


@pytest.fixture
def case(tmp_path, monkeypatch):
    source = Path(__file__).with_name("launcher.py")
    spec = importlib.util.spec_from_file_location("_fabricated_tensor_launcher", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "p"
    root.mkdir()
    package = root / "docs/phase2/cho51_tensor_verification_v1"
    package.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "PACKAGE", package)
    migration = root / "tools/migration"
    migration.mkdir(parents=True)
    for name in ("guard.py", "common.py", "job_adapter.py", "task.py"):
        (migration / name).write_text("# fabricated source pin\n", encoding="utf-8")
    for name in ("launcher.py", "child.py", "contract.py"):
        (package / name).write_text("# fabricated candidate pin\n", encoding="utf-8")
    members = []
    for name in ("evaluation/member.py", "evaluation/phase2_supervision_primitives.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fabricated canonical pin\n", encoding="utf-8")
        members.append(dict(path=name, sha256=module.digest(path)))
    _json(migration / "source-files.json", dict(source_sha256=module.CANONICAL_SHA, files=members))
    files = {str(root / row["path"]): row["sha256"] for row in members}
    files.update({str(path): module.digest(path) for path in migration.iterdir()})
    files.update({str(path): module.digest(path) for path in package.iterdir()})
    for name in module.DEPENDENCIES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fabricated transitive dependency pin\n", encoding="utf-8")
        files[str(path)] = module.digest(path)
    runtime = {}
    for name in (".venv/Scripts/python.exe", "base/python.exe", "base/python312.dll", "base/python3.dll", "bin/git.exe"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fabricated runtime, never executed\n", encoding="utf-8")
        runtime[str(path)] = module.digest(path)
    request_root = root / "request-assets"
    request_root.mkdir()
    asset = request_root / "publication-bytes.txt"
    asset.write_text("fabricated bytes, never decoded\n", encoding="utf-8")
    workspace = root / "runs/coordination/tensor-one"
    workspace.mkdir(parents=True)
    pub = dict(case_id="a" * 64, manifest_sha256="b" * 64, evidence_sha256="c" * 64,
               selected_candidate="fabricated-candidate", model_recipe_sha256="d" * 64,
               model_state_sha256="e" * 64, weights_sha256=module.digest(asset), environment_sha256="f" * 64)
    payload = dict(schema="cho51_tensor_child_input_v1", project_root=str(request_root), publication=pub)
    _json(workspace / "input.json", payload)
    bundle = dict(schema="cho51_tensor_bundle_v1", source_root=str(root), workspace=str(workspace),
                  input_path=str(workspace / "input.json"), input_file_sha256=module.digest(workspace / "input.json"),
                  request_sha256=module._payload_sha(payload), witness_path=str(workspace / "witness.json"),
                  files=files, runtime=runtime, assets={str(asset): module.digest(asset)},
                  limits=dict(seconds=120, process_mib=2048, job_mib=3072),
                  canonical_source_sha256=module.CANONICAL_SHA, native_child_path=str(package / "child.py"),
                  request_root=str(request_root), git_executable=str(root / "bin/git.exe"))
    _json(workspace / "bundle.json", bundle)
    bundle_sha = module.digest(workspace / "bundle.json")
    native = root / "runs/migration/fabricated_native"
    native.mkdir(parents=True)
    command = [str(root / ".venv/Scripts/python.exe"), "-I", "-S", "-B", bundle["native_child_path"],
               "--bundle", str(workspace / "bundle.json"), "--expect-bundle", bundle_sha]
    samples = [dict(available_ram_bytes=11 * module.GIB, free_disk_bytes=21 * module.GIB),
               dict(available_ram_bytes=10 * module.GIB, free_disk_bytes=20 * module.GIB)]
    start = datetime.now(timezone.utc) - timedelta(seconds=2)
    admission = dict(schema="migration_admission_v1", command=command, source_sha256=module.CANONICAL_SHA,
                     operation_pins={str(Path(path).relative_to(root)).replace("\\", "/"): sha
                                     for path, sha in files.items()
                                     if Path(path).is_relative_to(migration)
                                     or Path(path) == root / "evaluation/phase2_supervision_primitives.py"},
                     selected_runtime_pins={path: sha for path, sha in runtime.items()
                                            if path == str(root / ".venv/Scripts/python.exe")
                                            or Path(path).suffix == ".dll"},
                     process_mib=2048, job_mib=3072, active_ram_gib=4, active_disk_gib=20,
                     native_threads=1, peer_pause_file=str(module.PAUSE),
                     started_utc=start.isoformat(), deadline_utc=(start + timedelta(seconds=120)).isoformat(),
                     startup_samples=samples)
    state = {name: True for name in (
        "limits_set", "limits_query_verified", "job_created", "created_suspended",
        "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned", "membership_verified",
        "resumed", "job_empty_before_close", "job_closed", "root_exit_after_job_close", "process_handle_closed",
        "thread_handle_closed", "assignment_step_seen")}
    state.update(owned_job_termination_called=False, peak_samples=2, job_named="pro3_migration_" + native.name,
                 process_limit_bytes=2048 * 1024**2, aggregate_limit_bytes=3072 * 1024**2,
                 peak_process_commit_bytes=123456, peak_job_commit_bytes=234567,
                 cleanup_errors=[], peak_sampling_errors=[])
    receipt = dict(schema="migration_guard_receipt_v1", accepted=True, job_absent=True,
                   scientific_admission=False, error=None, job_name="pro3_migration_" + native.name,
                   result=dict(reason="normal", exit_code=0, peak_process_memory_bytes=123456,
                               peak_job_memory_bytes=234567), native_state=state,
                   startup_samples=copy.deepcopy(samples), completed_utc=(start + timedelta(seconds=1)).isoformat())
    witness = dict(schema="cho51_tensor_child_witness_v1", request_sha256=bundle["request_sha256"],
                   training_performed=False, **{key: value for key, value in pub.items() if key != "environment_sha256"})
    scope = dict(schema="cho51_tensor_child_scope_v1", request_sha256=bundle["request_sha256"],
                 denied_operations=[], torch_threads=1, torch_interop_threads=1, gpu_hidden=True,
                 status="verified", error=None, actual_tensor_restoration_performed=True,
                 canonical_tensor_verifier_unchanged=True, no_fitting_hooks_installed=True,
                 environment_sha256=pub["environment_sha256"])
    for path, value in ((native / "admission.json", admission), (native / "receipt.json", receipt),
                        (workspace / "witness.json", witness), (workspace / "child-scope.json", scope)):
        _json(path, value)
    observed_jobs = []
    monkeypatch.setattr(module, "_job_absent", lambda name: observed_jobs.append(name))
    # No test may start a process, even if a negative boundary unexpectedly fails.
    def forbidden_run(*args, **kwargs):
        raise AssertionError("fabricated launcher tests must never execute subprocesses")
    monkeypatch.setattr(module.subprocess, "run", forbidden_run)
    return SimpleNamespace(module=module, root=root, workspace=workspace, bundle=bundle, bundle_sha=bundle_sha,
                           native=native, admission=admission, receipt=receipt, witness=witness, scope=scope,
                           payload=payload, asset=asset, observed_jobs=observed_jobs)


def _admit(case):
    return case.module.admit_native_receipt(case.bundle, case.bundle_sha, case.native)


def _edit(case, filename, section, key, value):
    record = copy.deepcopy(getattr(case, filename))
    target = record if section is None else record[section]
    target[key] = value
    directory = case.native if filename in {"admission", "receipt"} else case.workspace
    path = directory / ("child-scope.json" if filename == "scope" else filename + ".json")
    _json(path, record)


def test_fabricated_receipt_admits_only_one_case_metadata(case):
    result = _admit(case)
    assert result["native_supervision_verified"] is True
    assert result["one_case_tensor_digest_verified"] is True
    assert result["full_roster_verified"] is False
    assert result["full_selector_evidence_verified"] is False
    assert result["scientific_admission"] is False
    assert result["bundle_sha256"] == case.bundle_sha
    assert result["receipt_file_sha256"] == case.module.digest(case.native / "receipt.json")
    assert result["witness_file_sha256"] == case.module.digest(case.workspace / "witness.json")
    assert case.observed_jobs == [case.receipt["job_name"]]


@pytest.mark.parametrize("key,value", [
    ("schema", "wrong"), ("command", []), ("source_sha256", "0" * 64),
    ("process_mib", 2049), ("job_mib", 3073), ("active_ram_gib", 3), ("active_disk_gib", 19),
    ("native_threads", 2), ("peer_pause_file", None), ("operation_pins", {}), ("selected_runtime_pins", {}),
    ("process_mib", 2048.0), ("native_threads", True),
])
def test_refuses_wrong_native_admission(case, key, value):
    _edit(case, "admission", None, key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [
    ("schema", "wrong"), ("accepted", False), ("accepted", 1), ("job_absent", False),
    ("job_absent", 1), ("scientific_admission", True), ("scientific_admission", 0),
    ("error", "failure"), ("job_name", "pro3_migration_other"), ("startup_samples", []),
])
def test_refuses_wrong_native_receipt(case, key, value):
    _edit(case, "receipt", None, key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [("reason", "deadline"), ("exit_code", 1), ("exit_code", False), ("exit_code", 0.0)])
def test_refuses_non_normal_or_nonliteral_exit(case, key, value):
    _edit(case, "receipt", "result", key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("flag", [
    "limits_set", "limits_query_verified", "job_created", "created_suspended",
    "atomic_job_assignment_requested", "atomic_job_assignment_verified", "assigned", "membership_verified",
    "resumed", "job_empty_before_close", "job_closed", "root_exit_after_job_close", "process_handle_closed",
    "thread_handle_closed", "assignment_step_seen",
])
def test_refuses_any_unconfirmed_native_lifecycle(case, flag):
    _edit(case, "receipt", "native_state", flag, False)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [("cleanup_errors", ["error"]), ("peak_sampling_errors", ["error"]),
                                       ("peak_samples", 0), ("peak_samples", True), ("job_named", "other"),
                                       ("process_limit_bytes", 2048 * 1024**2 + 1),
                                       ("aggregate_limit_bytes", 3072 * 1024**2 + 1)])
def test_refuses_cleanup_or_peak_sampling_failure(case, key, value):
    _edit(case, "receipt", "native_state", key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [
    ("peak_process_commit_bytes", 0), ("peak_process_commit_bytes", -1),
    ("peak_process_commit_bytes", True), ("peak_process_commit_bytes", 2048 * 1024**2 + 1),
    ("peak_job_commit_bytes", 0), ("peak_job_commit_bytes", 3072 * 1024**2 + 1),
])
def test_refuses_unmeasured_or_over_cap_peaks(case, key, value):
    _edit(case, "receipt", "native_state", key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key", ["peak_process_memory_bytes", "peak_job_memory_bytes"])
def test_result_peaks_must_match_native_job_measurements(case, key):
    _edit(case, "receipt", "result", key, 1)
    with pytest.raises(ValueError, match="peak result"):
        _admit(case)


@pytest.mark.parametrize("samples", [
    [], [dict(available_ram_bytes=10 * 1024**3, free_disk_bytes=20 * 1024**3)],
    [dict(available_ram_bytes=10 * 1024**3 - 1, free_disk_bytes=20 * 1024**3)] * 2,
    [dict(available_ram_bytes=10 * 1024**3, free_disk_bytes=20 * 1024**3 - 1)] * 2,
    [dict(available_ram_bytes=float(10 * 1024**3), free_disk_bytes=20 * 1024**3)] * 2,
])
def test_refuses_missing_or_below_floor_startup_samples(case, samples):
    _edit(case, "admission", None, "startup_samples", samples)
    _edit(case, "receipt", None, "startup_samples", samples)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("which", ["short-bound", "naive-start", "naive-completed", "early-completed", "late-completed"])
def test_refuses_unbounded_or_unordered_native_times(case, which):
    start = datetime.fromisoformat(case.admission["started_utc"])
    if which == "short-bound":
        _edit(case, "admission", None, "deadline_utc", (start + timedelta(seconds=119)).isoformat())
    elif which == "naive-start":
        _edit(case, "admission", None, "started_utc", start.replace(tzinfo=None).isoformat())
    elif which == "naive-completed":
        _edit(case, "receipt", None, "completed_utc", start.replace(tzinfo=None).isoformat())
    else:
        delta = -1 if which == "early-completed" else 121
        _edit(case, "receipt", None, "completed_utc", (start + timedelta(seconds=delta)).isoformat())
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [
    ("schema", "cho_tensor_case_child_witness_v1"), ("request_sha256", "0" * 64),
    ("case_id", "0" * 64), ("training_performed", True), ("training_performed", 0),
    ("manifest_sha256", "0" * 64), ("evidence_sha256", "0" * 64),
    ("selected_candidate", "other"), ("model_recipe_sha256", "0" * 64),
    ("model_state_sha256", "0" * 64), ("weights_sha256", "0" * 64), ("extra", False),
])
def test_refuses_any_witness_field_mismatch(case, key, value):
    _edit(case, "witness", None, key, value)
    with pytest.raises(ValueError):
        _admit(case)


@pytest.mark.parametrize("key,value", [
    ("request_sha256", "0" * 64), ("denied_operations", ["denied"]),
    ("torch_threads", 2), ("torch_threads", True), ("torch_interop_threads", 2),
    ("torch_interop_threads", True), ("gpu_hidden", False), ("gpu_hidden", 1),
    ("schema", "wrong"), ("status", "failed"), ("error", "failure"),
    ("actual_tensor_restoration_performed", False), ("canonical_tensor_verifier_unchanged", False),
    ("no_fitting_hooks_installed", False), ("environment_sha256", "0" * 64),
])
def test_refuses_uncontrolled_child_scope(case, key, value):
    _edit(case, "scope", None, key, value)
    with pytest.raises(ValueError):
        _admit(case)


def test_current_asset_bytes_must_still_match_at_admission(case):
    case.asset.write_text("changed fabricated publication bytes\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pinned file changed"):
        _admit(case)


@pytest.mark.parametrize("group", ["runtime", "source", "asset"])
def test_only_installed_runtime_pins_allow_identical_hardlinked_bytes(case, group):
    path = {
        "runtime": case.root / ".venv/Scripts/python.exe",
        "source": case.root / "evaluation/member.py",
        "asset": case.asset,
    }[group]
    original_sha = case.module.digest(path)
    alias = case.workspace / ("hardlink-" + group)
    os.link(path, alias)
    assert path.stat().st_nlink == alias.stat().st_nlink == 2
    assert case.module.digest(path) == original_sha
    if group == "runtime":
        case.module.verify_bundle_pins(case.bundle)
    else:
        with pytest.raises(ValueError, match="pinned file changed"):
            case.module.verify_bundle_pins(case.bundle)


@pytest.mark.parametrize("group", ["asset", "runtime", "source"])
def test_pins_are_rechecked_after_native_job_absence_observation(case, monkeypatch, group):
    path = {
        "asset": case.asset,
        "runtime": case.root / ".venv/Scripts/python.exe",
        "source": case.root / "evaluation/member.py",
    }[group]
    def mutate_after_first_pin_check(name):
        case.observed_jobs.append(name)
        path.write_text("changed after initial pin verification\n", encoding="utf-8")
    monkeypatch.setattr(case.module, "_job_absent", mutate_after_first_pin_check)
    with pytest.raises(ValueError, match="pinned file changed"):
        _admit(case)
    assert case.observed_jobs == [case.receipt["job_name"]]


@pytest.mark.parametrize("proof", ["admission", "receipt", "witness", "scope"])
def test_same_byte_proof_replacement_after_parsing_is_refused(case, monkeypatch, proof):
    paths = {
        "admission": case.native / "admission.json",
        "receipt": case.native / "receipt.json",
        "witness": case.workspace / "witness.json",
        "scope": case.workspace / "child-scope.json",
    }
    path = paths[proof]
    original_read = case.module.read_json
    replacements = []
    def replace_after_parse(requested, *args, **kwargs):
        result = original_read(requested, *args, **kwargs)
        if requested == path and not replacements:
            replacement = path.with_name(path.name + ".replacement")
            replacement.write_bytes(path.read_bytes())
            os.replace(replacement, path)
            replacements.append(path)
        return result
    monkeypatch.setattr(case.module, "read_json", replace_after_parse)
    with pytest.raises(ValueError, match="proof changed during admission"):
        _admit(case)
    assert replacements == [path]


def test_fresh_native_job_absence_must_be_observed(case, monkeypatch):
    def present(_name):
        raise ValueError("fresh native Job absence unconfirmed")
    monkeypatch.setattr(case.module, "_job_absent", present)
    with pytest.raises(ValueError, match="Job absence"):
        _admit(case)


def test_native_receipt_cannot_escape_migration_root(case):
    with pytest.raises(ValueError, match="direct migration"):
        case.module.admit_native_receipt(case.bundle, case.bundle_sha, case.workspace)


def test_independently_expected_bundle_sha_must_match(case):
    with pytest.raises(ValueError, match="independent JSON byte SHA"):
        case.module.admit_native_receipt(case.bundle, "0" * 64, case.native)


def test_admission_cannot_use_a_changed_in_memory_bundle(case):
    changed = copy.deepcopy(case.bundle)
    changed["request_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        case.module.admit_native_receipt(changed, case.bundle_sha, case.native)


def test_load_bundle_checks_real_dummy_files(case):
    loaded = case.module.load_bundle(case.workspace / "bundle.json", case.bundle_sha)
    assert loaded == case.bundle
    case.module.verify_bundle_pins(loaded)


@pytest.mark.parametrize("key,value", [
    ("schema", "wrong"), ("canonical_source_sha256", "0" * 64), ("source_root", "elsewhere"),
    ("native_child_path", "elsewhere"), ("input_path", "elsewhere"), ("witness_path", "elsewhere"),
    ("request_sha256", "0" * 64), ("files", {}), ("runtime", {}), ("assets", {}), ("extra", True),
])
def test_load_bundle_refuses_incomplete_or_rebound_metadata(case, key, value):
    changed = copy.deepcopy(case.bundle)
    changed[key] = value
    _json(case.workspace / "bundle.json", changed)
    sha = case.module.digest(case.workspace / "bundle.json")
    with pytest.raises(ValueError):
        case.module.load_bundle(case.workspace / "bundle.json", sha)


@pytest.mark.parametrize("key,value", [("seconds", 9), ("seconds", 601), ("seconds", True),
                                       ("process_mib", 2049), ("job_mib", 3073), ("process_mib", 2048.0)])
def test_load_bundle_refuses_unreviewed_limits(case, key, value):
    changed = copy.deepcopy(case.bundle)
    changed["limits"][key] = value
    _json(case.workspace / "bundle.json", changed)
    with pytest.raises(ValueError, match="limits"):
        case.module.load_bundle(case.workspace / "bundle.json", case.module.digest(case.workspace / "bundle.json"))


def test_changed_input_cannot_reuse_the_pinned_request_digest(case):
    changed = copy.deepcopy(case.payload)
    changed["publication"]["selected_candidate"] = "changed"
    _json(case.workspace / "input.json", changed)
    with pytest.raises(ValueError, match="independent JSON byte SHA"):
        case.module.load_bundle(case.workspace / "bundle.json", case.bundle_sha)


def test_bundle_cannot_omit_current_guard_source_pins(case):
    changed = copy.deepcopy(case.bundle)
    del changed["files"][str(case.root / "tools/migration/guard.py")]
    _json(case.workspace / "bundle.json", changed)
    with pytest.raises(ValueError, match="pins required"):
        case.module.load_bundle(case.workspace / "bundle.json", case.module.digest(case.workspace / "bundle.json"))


def test_bundle_cannot_omit_transitive_publication_dependency(case):
    changed = copy.deepcopy(case.bundle)
    dependency = case.root / "docs/phase2/cho51_publication_collection_v1/collection.py"
    del changed["files"][str(dependency)]
    _json(case.workspace / "bundle.json", changed)
    with pytest.raises(ValueError, match="pins required"):
        case.module.load_bundle(case.workspace / "bundle.json", case.module.digest(case.workspace / "bundle.json"))


def test_launch_builds_exact_pinned_guard_command_and_reserves_once(case, monkeypatch):
    (case.workspace / "witness.json").unlink()
    commands = []
    def failed(command, **kwargs):
        commands.append((command, kwargs))
        return SimpleNamespace(returncode=1, stdout=str(case.native) + "\nFAIL\n", stderr="fixture refusal")
    monkeypatch.setattr(case.module.subprocess, "run", failed)
    with pytest.raises(ValueError, match="refused/failed"):
        case.module.launch_tensor_bundle(case.workspace / "bundle.json", case.bundle_sha)
    python = str(case.root / ".venv/Scripts/python.exe")
    expected = [python, "-I", "-S", "-B", str(case.root / "tools/migration/guard.py"),
                "--purpose", "one adopted51 selected tensor engineering verification; no fitting or science",
                "--seconds", "120", "--process-mib", "2048", "--job-mib", "3072", "--pause-file",
                str(case.module.PAUSE), "--", *case.admission["command"]]
    assert commands == [(expected, dict(cwd=case.root, capture_output=True, text=True, check=False))]
    assert (case.workspace / "launch-reservation.json").is_file()
    assert (case.workspace / "launch-result.json").is_file()
    assert not (case.workspace / "native-result.json").exists()
    with pytest.raises(FileExistsError):
        case.module.launch_tensor_bundle(case.workspace / "bundle.json", case.bundle_sha)
    assert len(commands) == 1


def test_failed_guard_cannot_admit_even_matching_fabricated_witness(case, monkeypatch):
    (case.workspace / "witness.json").unlink()
    def failed(*args, **kwargs):
        _json(case.workspace / "witness.json", case.witness)
        return SimpleNamespace(returncode=1, stdout=str(case.native) + "\n", stderr="")
    monkeypatch.setattr(case.module.subprocess, "run", failed)
    monkeypatch.setattr(case.module, "admit_native_receipt", lambda *args: pytest.fail("failed guard reached admission"))
    with pytest.raises(ValueError, match="refused/failed"):
        case.module.launch_tensor_bundle(case.workspace / "bundle.json", case.bundle_sha)
    assert not (case.workspace / "native-result.json").exists()


def test_matching_mocked_guard_result_writes_a_narrow_native_result(case, monkeypatch):
    (case.workspace / "witness.json").unlink()
    def completed(*args, **kwargs):
        _json(case.workspace / "witness.json", case.witness)
        return SimpleNamespace(returncode=0, stdout=str(case.native) + "\nPASS\n", stderr="")
    monkeypatch.setattr(case.module.subprocess, "run", completed)
    result = case.module.launch_tensor_bundle(case.workspace / "bundle.json", case.bundle_sha)
    assert result == case.module.read_json(case.workspace / "native-result.json")
    assert result["full_roster_verified"] is False
    assert result["scientific_admission"] is False


@pytest.mark.parametrize("raw", [
    '{"same":1,"same":2}', '{"outer":{"same":1,"same":2}}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}',
])
def test_json_refuses_ambiguous_or_nonfinite_input(case, raw):
    path = case.workspace / "ambiguous.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        case.module.read_json(path)


@pytest.mark.parametrize("raw,limit", [("", 10), ('{"large":"1234567890"}', 10)])
def test_json_requires_nonempty_bounded_bytes(case, raw, limit):
    path = case.workspace / "bounded.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError, match="bounded"):
        case.module.read_json(path, maximum_bytes=limit)


def test_json_refuses_relative_path(case):
    with pytest.raises(ValueError, match="direct absolute"):
        case.module.read_json(Path("relative.json"))


def test_json_refuses_lexical_parent_alias(case):
    nested = case.workspace / "nested"
    nested.mkdir()
    path = nested / ".." / "input.json"
    with pytest.raises(ValueError, match="direct absolute"):
        case.module.read_json(path)


def test_json_refuses_multiple_hardlinks(case):
    path = case.workspace / "input-alias.json"
    os.link(case.workspace / "input.json", path)
    with pytest.raises(ValueError, match="single-linked"):
        case.module.read_json(path)


@pytest.mark.parametrize("value", [None, True, "F" * 64, "a" * 63, "a" * 65, "g" * 64])
def test_independent_digest_requires_exact_lowercase_sha(case, value):
    with pytest.raises(ValueError, match="SHA256"):
        case.module.load_bundle(case.workspace / "bundle.json", value)
