"""Import and metadata inspection only; no selector, model factory or recorder."""

import hashlib
import importlib
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

ROOT = Path.cwd()
TASK = ROOT / "runs/coordination/phase2_readiness_20261012_v1"
OUT = TASK / "worker_probe_003"
sys.path[:0] = [str(ROOT), str(ROOT / "tools/migration"), str(ROOT / ".venv/Lib/site-packages")]
from common import digest, source_check, write_json

pins = json.loads((TASK / "worker_probe_pins_003.json").read_bytes())
source_before = source_check(ROOT)
for name, expected in pins.items():
    assert digest(ROOT / name) == expected, name
OUT.mkdir(exist_ok=False)
(OUT / "temp").mkdir()
for name, relative in {
    "MPLCONFIGDIR": "matplotlib",
    "_MNE_FAKE_HOME_DIR": "mne-home",
    "HF_HOME": "huggingface",
    "TMP": "temp",
    "TEMP": "temp",
    "TMPDIR": "temp",
}.items():
    folder = OUT / relative
    folder.mkdir(exist_ok=True)
    os.environ[name] = str(folder)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"

denied = []
observed_local_hostname_queries = 0
owned = OUT.resolve()
raw_roots = [(ROOT / name).resolve() for name in ("data/raw", "data/processed", "weights")]


def deny(event, detail):
    frames = []
    frame = sys._getframe(1)
    for _ in range(8):
        if frame is None: break
        frames.append({"file": frame.f_code.co_filename, "function": frame.f_code.co_name, "line": frame.f_lineno})
        frame = frame.f_back
    denied.append({"event": event, "detail": str(detail)[:240], "call_stack": frames, "bind_address": list(detail) if event == "socket.bind" and isinstance(detail, tuple) else None})
    raise PermissionError("environment probe excludes " + event)


def path_value(value):
    if isinstance(value, (str, bytes, os.PathLike)):
        return Path(os.fsdecode(value)).resolve()
    return None


def owned_write(event, value):
    path = path_value(value)
    if path is not None and not path.is_relative_to(owned):
        deny(event, path)


def audit(event, args):
    global observed_local_hostname_queries
    if event == "socket.gethostname":
        observed_local_hostname_queries += 1
    elif event == "socket.bind":
        deny(event, args[1])
    elif event in {"socket.connect", "socket.bind", "socket.getaddrinfo", "socket.sendto", "subprocess.Popen", "os.system"} or event.startswith(("os.exec", "os.spawn")):
        deny(event, "network/DNS/subprocess outside this import-only scope")
    elif event == "open":
        path = path_value(args[0])
        if path is None:
            return
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        )
        if writing:
            owned_write(event, path)
        elif path.suffix.lower() in {".pth", ".pt", ".ckpt", ".safetensors", ".npz", ".mat", ".edf", ".gdf"} or any(path.is_relative_to(root) for root in raw_roots):
            deny(event, path)
    elif event == "os.mkdir":
        path = path_value(args[0])
        if path is not None and not path.is_relative_to(owned) and not path.is_dir():
            deny(event, path)
    elif event in {"os.remove", "os.rmdir"}:
        owned_write(event, args[0])
    elif event == "os.rename":
        owned_write(event, args[0])
        owned_write(event, args[1])


sys.addaudithook(audit)
started = time.monotonic()
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
callback_root = ROOT / "docs/phase2/cho_b_disk_cache"
sys.path.insert(0, str(callback_root))
requested_imports = (
    "encoder.labram",
    "adaptation.labram_source",
    "adaptation.labram_lora_support",
    "evaluation.phase2_cho_execution",
    "evaluation.phase2_cho_sweep",
    "evaluation.phase2_cho_case_inputs",
    "pro3_inference_candidate.selection_callback",
    "pro3_inference_candidate.source_selection_cache_scope_inference",
)
for name in requested_imports:
    importlib.import_module(name)

from evaluation.phase2_cho_case_inputs import CHO_SUBJECTS, SELECTED_METHODS, SELECTED_SEEDS, SELECTED_SHOTS
from evaluation.phase2_protocol import selection_gradient_ceiling
from evaluation.phase2_runner import CasePlan, environment_digest, method_configuration

decision = json.loads((ROOT / "docs/phase2/gate_a_acceptance_20261012.json").read_bytes())
previous = json.loads((ROOT / "docs/phase2/cho_design_decisions_20261012.json").read_bytes())
design = previous["adopted_design"]
assert decision["scientific_gate_a_signed"] and not decision["experiment_freeze_signed"]
assert not decision["scientific_execution_budget_admitted"]
assert len(CHO_SUBJECTS) == design["scope"]["subjects"] == 52
assert list(SELECTED_METHODS) == design["scope"]["methods"]
assert list(SELECTED_SEEDS) == design["scope"]["model_seeds"]
assert SELECTED_SHOTS == design["scope"]["shots_per_class"] == 5
method_pins = {m["method"]: method_configuration(m) for m in design["candidate_template"]["methods"]}
plans = tuple(CasePlan("cho2017", subject, method, SELECTED_SHOTS, seed, 1)
    for subject in CHO_SUBJECTS for method in SELECTED_METHODS for seed in SELECTED_SEEDS)
assert len(plans) == len({plan.case_id for plan in plans}) == 1040
rows = [{**asdict(plan), "case_id": plan.case_id, "method_config_sha256": method_pins[plan.method]} for plan in plans]
original = decision["original_case"]
recorder_review = ROOT / original["recorder_decision"]["path"]
assert digest(recorder_review) == original["recorder_decision"]["sha256"]
review = json.loads(recorder_review.read_bytes())
for name, expected in review["input_pins"].items():
    assert digest(ROOT / name) == expected, name
claims = sorted((ROOT / "runs/phase2/recorder/claims").glob(original["id"] + ".attempt*.claim.json"))
failures = sorted((ROOT / "runs/phase2/recorder/attempts").glob(original["id"] + ".attempt*.failure.json"))
assert len(claims) == len(failures) == 2
assert not list((ROOT / "runs/phase2/recorder/publication_intents").glob(original["id"] + "*"))
assert not list((ROOT / "runs/phase2/recorder/engineering_intents").glob(original["id"] + "*"))
conflicts = [row for row in rows if row["case_id"] == original["id"]]
assert len(conflicts) == 1
assert conflicts[0]["method"] == "labram_linear" and conflicts[0]["target_subject"] == "subject_01" and conflicts[0]["model_seed"] == 11
ceiling = selection_gradient_ceiling(ROOT)
selection_steps = 2 * 51 * (50 + 1) + 51
assert ceiling == selection_steps == 5253
assert design["primary_analysis"]["complete_verified_cells_required"] == 1040
assert design["primary_analysis"]["imputation_allowed"] is False
loaded_files = {}
for module in tuple(sys.modules.values()):
    file = getattr(module, "__file__", None)
    if isinstance(file, str):
        path = Path(file)
        if path.is_file() and path.suffix.lower() in {".py", ".pyd", ".dll"}:
            loaded_files[str(path.resolve())] = digest(path)
for name, expected in pins.items():
    assert digest(ROOT / name) == expected, name
assert source_check(ROOT) == source_before
write_json(OUT / "denied_operations.json", {"denied_operations": denied})
connection_path = ROOT / ".venv/Lib/site-packages/urllib3/util/connection.py"
assert digest(connection_path) == pins[connection_path.relative_to(ROOT).as_posix()]
expected_import_denials = [event for event in denied if event["event"] == "socket.bind" and event["bind_address"] == ["::1", 0] and any(frame["function"] == "_has_ipv6" and Path(frame["file"]).resolve() == connection_path.resolve() for frame in event["call_stack"])]
unexpected_denials = [event for event in denied if event not in expected_import_denials]
assert len(expected_import_denials) <= 1 and not unexpected_denials
assert torch.get_num_threads() == torch.get_num_interop_threads() == 1
observed = datetime.now(UTC).isoformat()
environment = {
    "schema": "pro3_actual_worker_module_import_environment_measurement_v1",
    "observed_utc": observed,
    "import_probe_passed": True,
    "canonical_source_sha256": source_before,
    "project_and_worker_input_pins": pins,
    "requested_imports": list(requested_imports),
    "python": sys.version,
    "python_executable": sys.executable,
    "python_executable_sha256": digest(Path(sys.executable)),
    "installed_distribution_versions": {name: version(name) for name in ("torch", "numpy", "scipy", "scikit-learn", "mne", "braindecode", "safetensors", "einops")},
    "torch_version": str(torch.__version__),
    "torch_threads": torch.get_num_threads(),
    "torch_interop_threads": torch.get_num_interop_threads(),
    "deterministic_algorithms_enabled": torch.are_deterministic_algorithms_enabled(),
    "phase2_environment_digest": environment_digest(),
    "device_scope": "CPU imports and metadata only; GPUs hidden; no tensor forward/fit",
    "elapsed_seconds": time.monotonic() - started,
    "loaded_module_file_count": len(loaded_files),
    "loaded_module_file_hashes": loaded_files,
    "loaded_file_hash_note": "Paths and file bytes measured after imports, then rechecked before exit; not a reconstruction of historical loaded binaries",
    "forbidden_operation_attempts": denied,
    "expected_denied_import_capability_probe_count": len(expected_import_denials),
    "expected_denial_note": "Pinned urllib3 _has_ipv6 loopback bind attempt denied; bind stays blocked and no network permission added",
    "unexpected_denied_operation_count": len(unexpected_denials),
    "unrestricted_worker_behavior_qualified": False,
    "local_hostname_metadata_queries": observed_local_hostname_queries,
    "raw_or_processed_array_or_checkpoint_opened": False,
    "model_factory_selector_or_recorder_invoked": False,
    "worker_numerical_execution_qualified": False,
    "complete_cached_real_selection_completed": False,
    "scientific_admission": False,
    "original_case_attempts_remaining": 0,
}
roster = {
    "schema": "pro3_current_cho_case_identity_and_budget_readiness_v1",
    "observed_utc": observed,
    "canonical_source_sha256": source_before,
    "planned_cases": len(rows),
    "subjects": len(CHO_SUBJECTS), "methods": list(SELECTED_METHODS),
    "model_seeds": list(SELECTED_SEEDS), "shots_per_class": SELECTED_SHOTS,
    "live_selection_gradient_ceiling": ceiling,
    "declared_selection_steps_per_case": selection_steps,
    "declared_target_support_steps_per_case": 1,
    "selection_ceiling_matches_declared_complete_plan": True,
    "planned_selection_steps_total": selection_steps * len(rows),
    "original_exhausted_case_conflicts": conflicts,
    "original_case_claims": len(claims), "original_case_failures": len(failures),
    "original_case_success_intent_present": False,
    "original_case_attempts_remaining": 0,
    "complete_roster_feasible_under_unchanged_case_rules": False,
    "complete_analysis_requires_all_cells_and_forbids_imputation": True,
    "scientific_gate_a_signed_under_retrospective_amendment": True,
    "actual_checkpoint_cohort_and_overlap": "unknown",
    "experiment_freeze_signed": False,
    "scientific_execution_budget_admitted": False,
    "runnable_scientific_cases_admitted": 0,
    "recorder_instantiated_locked_claimed_recovered_or_reset": False,
    "identity_substitution_or_case_rename_performed": False,
    "cases": rows,
}
write_json(OUT / "environment.json", environment)
write_json(OUT / "roster.json", roster)
for name, expected in loaded_files.items():
    assert digest(Path(name)) == expected, name
assert source_check(ROOT) == source_before
print(json.dumps({"import_probe_passed": True, "loaded_module_files": len(loaded_files), "planned_cases": len(rows), "live_ceiling": ceiling, "exhausted_case_conflicts": len(conflicts), "complete_roster_feasible": False, "scientific_admission": False}))
