"""Finite synthetic report checks. No real score or model interface is called."""
import argparse
import contextlib
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import threading
import traceback
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parent
ROOT = Path("D:/Aenv/pro3")
OUT = None
C = None
CTX = None
REPORTS = {}


def ratio(value):
    return Fraction(value["numerator"], value["denominator"])


def reject(function, message):
    try:
        function()
    except C.ReportError as error:
        assert str(error) == message, (str(error), message)
    else:
        raise AssertionError("expected publication refusal missing")


def report(name):
    if name not in REPORTS:
        REPORTS[name] = C.build_report(ROOT, name, CTX)
    result = REPORTS[name]
    assert result["scope"] == "synthetic_engineering_only"
    assert result["authority"] == C.AUTHORITY
    assert result["synthetic_numeric_condition_diagnostic"]["scientific_superiority_claim"] is False
    return result


def zero():
    value = report("zero")["synthetic_primary_calculation"]
    assert ratio(value["mean_difference"]) == 0 and ratio(value["sample_variance"]) == 0
    assert value["wilcoxon_p_value_unrounded"] == 1.0
    assert value["paired_mean_ci_95"] == value["paired_mean_ci_90"] == [0.0, 0.0]
    assert value["zero_difference_count"] == 52
    assert value["nonzero_tied_subject_count"] == value["nonzero_absolute_tie_class_count"] == 0


def positive():
    value = report("positive")
    numbers = value["synthetic_primary_calculation"]
    assert ratio(numbers["mean_difference"]) == Fraction(1, 10) and ratio(numbers["sample_variance"]) == 0
    assert numbers["paired_mean_ci_95"] == numbers["paired_mean_ci_90"] == [0.1, 0.1]
    assert numbers["wilcoxon_p_value_unrounded"] < 0.05
    assert value["synthetic_numeric_condition_diagnostic"]["both_proposed_numeric_conditions_met"] is True


def negative():
    value = report("negative")
    numbers = value["synthetic_primary_calculation"]
    assert ratio(numbers["mean_difference"]) == Fraction(-1, 10) and ratio(numbers["sample_variance"]) == 0
    assert numbers["wilcoxon_p_value_unrounded"] > 0.95
    assert value["synthetic_numeric_condition_diagnostic"]["both_proposed_numeric_conditions_met"] is False


def ties():
    value = report("ties")
    numbers = value["synthetic_primary_calculation"]
    assert ratio(numbers["mean_difference"]) == Fraction(1, 20)
    assert ratio(numbers["sample_variance"]) == Fraction(13, 1020)
    assert numbers["zero_difference_count"] == 13 and numbers["nonzero_tied_subject_count"] == 39
    assert numbers["nonzero_absolute_tie_class_count"] == 2
    assert [row["signed_rank_level"] for row in value["subject_pairs"]] == [0, 1, -1, 2] * 13
    assert numbers["paired_mean_ci_95"][0] < numbers["paired_mean_ci_90"][0] < 0.05
    assert numbers["paired_mean_ci_95"][1] > numbers["paired_mean_ci_90"][1] > 0.05


def disagreement():
    value = report("rank_mean_disagree")
    numbers = value["synthetic_primary_calculation"]
    assert ratio(numbers["mean_difference"]) == Fraction(-449, 52000)
    diagnostic = value["synthetic_numeric_condition_diagnostic"]
    assert numbers["wilcoxon_p_value_unrounded"] < 0.05
    assert diagnostic["unrounded_p_less_than_proposed_alpha"] is True
    assert diagnostic["strictly_positive_exact_paired_mean"] is False
    assert diagnostic["both_proposed_numeric_conditions_met"] is False


def complete_roster():
    value = report("ties")
    roster = value["roster"]
    assert (roster["cell_count"], roster["subject_method_mean_count"], roster["inferential_unit_count"]) == (1040, 208, 52)
    cells = value["synthetic_cells"]
    keys = {(row["subject"], row["method"], row["seed"]) for row in cells}
    assert keys == {(subject, method, seed) for subject in C.SUBJECTS for method in C.METHODS for seed in C.SEEDS}
    assert len({row["synthetic_cell_sha256"] for row in cells}) == 1040
    assert all(row["shots"] == 5 and row["provenance"] == "fabricated_internal_fixture_only" for row in cells)
    assert roster["synthetic_cells_sha256"] == C.sha(C.encoded(cells)) and roster["real_cells_read"] == 0
    for item in value["subject_method_means"]:
        scores = [ratio(row["balanced_accuracy"]) for row in cells if row["subject"] == item["subject"] and row["method"] == item["method"]]
        assert len(scores) == item["contributing_seeds"] == 5
        assert sum(scores, Fraction()) / 5 == ratio(item["balanced_accuracy"])


def unchanged_proposal():
    value = report("ties")
    owner = C.decoded(C.read_small(ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json"))
    for key in ("proposed_primary_analysis", "proposed_secondary_analysis", "proposed_margin_display"):
        assert value[key] == owner[key] and value[key]["ratified"] is False
    assert value["secondary_superiority_p_values"] == []
    assert value["formal_tost_or_equivalence_decision"] is None
    assert value["execution_context_independently_authenticated_by_candidate"] is False


def deterministic():
    assert C.encoded(report("ties")) == C.encoded(C.build_report(ROOT, "ties", CTX))
    assert C.preview(report("ties")).count(b"| subject_") == 52


def publish():
    destination = OUT / "preview_bundle"
    first = C.publish_fixture(ROOT, "ties", CTX, destination)
    assert first == C.verify_publication(ROOT, destination) and first["publication_complete"] is True
    assert set(p.name for p in destination.iterdir()) == {"report.json", "preview.md", "receipt.json"}


def replay():
    destination = OUT / "preview_bundle"
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    reject(lambda: C.publish_fixture(ROOT, "positive", CTX, destination), "new_publication_directory_required")
    assert before == {p.name: p.read_bytes() for p in destination.iterdir()}


def interrupted():
    destination = OUT / "interrupted_bundle"
    original = C._write_new
    def fail_preview(path, data):
        if path.name == "preview.md":
            raise OSError("owned synthetic interruption")
        original(path, data)
    with patch.object(C, "_write_new", fail_preview):
        try:
            C.publish_fixture(ROOT, "zero", CTX, destination)
        except OSError as error:
            assert str(error) == "owned synthetic interruption"
        else:
            raise AssertionError("interruption missing")
    assert {p.name for p in destination.iterdir()} == {"report.json"}
    reject(lambda: C.verify_publication(ROOT, destination), "exact_complete_publication_inventory_required")
    reject(lambda: C.publish_fixture(ROOT, "zero", CTX, destination), "new_publication_directory_required")


def changed_bundle(name, change):
    destination = OUT / name
    C.publish_fixture(ROOT, "zero", CTX, destination)
    change(destination)
    return destination


def extra_entry():
    destination = changed_bundle("extra_entry", lambda p: (p / "unexpected.txt").write_bytes(b"synthetic"))
    reject(lambda: C.verify_publication(ROOT, destination), "exact_complete_publication_inventory_required")


def tamper():
    destination = changed_bundle("tampered", lambda p: (p / "preview.md").write_bytes(b"fabricated replacement"))
    reject(lambda: C.verify_publication(ROOT, destination), "publication_bytes_or_internal_fixture_changed")


def authority_tamper():
    def change(path):
        receipt = C.decoded((path / "receipt.json").read_bytes())
        receipt["authority"]["scientific_gate_a_signed"] = True
        (path / "receipt.json").write_bytes(C.encoded(receipt))
    destination = changed_bundle("authority_tampered", change)
    reject(lambda: C.verify_publication(ROOT, destination), "synthetic_publication_authority_or_scope_changed")


def self_consistent_tamper():
    def change(path):
        value = C.decoded((path / "report.json").read_bytes())
        value["synthetic_primary_calculation"]["mean_difference"] = {"numerator": 1, "denominator": 1}
        data = C.encoded(value)
        (path / "report.json").write_bytes(data)
        receipt = C.decoded((path / "receipt.json").read_bytes())
        receipt["outputs"]["report.json"] = {"sha256": C.sha(data), "bytes": len(data)}
        (path / "receipt.json").write_bytes(C.encoded(receipt))
    destination = changed_bundle("self_consistent_tampered", change)
    reject(lambda: C.verify_publication(ROOT, destination), "publication_bytes_or_internal_fixture_changed")


def bool_integer_tamper():
    def change(path):
        receipt = C.decoded((path / "receipt.json").read_bytes())
        receipt["authority"]["scientific_gate_a_signed"] = 0
        (path / "receipt.json").write_bytes(C.encoded(receipt))
    destination = changed_bundle("bool_integer_tampered", change)
    reject(lambda: C.verify_publication(ROOT, destination), "publication_bytes_or_internal_fixture_changed")


def linked_file():
    destination = changed_bundle("linked", lambda p: os.link(p / "report.json", OUT / "linked_report.json"))
    reject(lambda: C.verify_publication(ROOT, destination), "multiply_linked_file_refused")


def context_change(key, value, error):
    changed = dict(CTX)
    changed[key] = value
    reject(lambda: C.build_report(ROOT, "zero", changed), error)


def pin_change():
    original = C.read_small
    def drift(path):
        data = original(path)
        return data + b" " if Path(path).name == "phase2_inference.py" else data
    with patch.object(C, "read_small", drift):
        reject(lambda: C.build_report(ROOT, "zero", CTX), "project_calculator_or_owner_pin_changed")


def cli():
    path = OUT / "synthetic_cli_context.json"
    path.write_bytes(C.encoded(CTX))
    args = ["--project-root", str(ROOT), "--context-file", str(path), "--output-directory", str(OUT / "cli_bundle"), "--fixture", "positive"]
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert C.main(args) == 0
    assert json.loads(output.getvalue())["publication_complete"] is True
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        assert C.main(args) == 2
    assert json.loads(output.getvalue())["error"] == "new_publication_directory_required"
    for extra in (["--mode", "scientific"], ["--real-cells", "never-open-this"]):
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                C.main(args + extra)
            except SystemExit as error:
                assert error.code == 2
            else:
                raise AssertionError("scientific/real-input CLI unexpectedly accepted")


CASES = [
    ("all_zero_point_intervals", zero), ("positive_constant_no_scientific_claim", positive),
    ("negative_constant_direction", negative), ("exact_absolute_ties_and_pratt_zeros", ties),
    ("small_rank_p_negative_exact_mean", disagreement), ("1040_cells_208_means_52_subject_units", complete_roster),
    ("unchanged_unsigned_owner_proposal", unchanged_proposal), ("deterministic_json_and_subject_preview", deterministic),
    ("complete_write_once_publication", publish), ("replay_refused_bytes_preserved", replay),
    ("interrupted_no_commit_receipt", interrupted), ("extra_publication_entry_refused", extra_entry),
    ("output_tamper_refused", tamper), ("authority_tamper_refused", authority_tamper),
    ("self_consistent_score_hash_tamper_refused", self_consistent_tamper), ("boolean_integer_authority_refused", bool_integer_tamper),
    ("multiply_linked_output_refused", linked_file),
    ("source_context_drift", lambda: context_change("canonical_source_sha256", "f"*64, "canonical_source_context_changed")),
    ("owner_context_drift", lambda: context_change("owner_packet_sha256", "f"*64, "quality_or_unsigned_owner_context_changed")),
    ("boolean_canonical_count_refused", lambda: context_change("canonical_files", True, "canonical_source_context_changed")),
    ("context_authority_injection_refused", lambda: context_change("scientific_gate_a_signed", True, "exact_context_fields_required")),
    ("unknown_fixture_refused", lambda: reject(lambda: C.build_report(ROOT, "real", CTX), "unknown_internal_fixture")),
    ("calculator_byte_drift_refused", pin_change),
    ("duplicate_json_key_refused", lambda: reject(lambda: C.decoded(b'{"x":1,"x":2}'), "duplicate_json_key")),
    ("nonfinite_json_refused", lambda: reject(lambda: C.decoded(b'{"x":NaN}'), "nonfinite_json")),
    ("oversized_metadata_refused", lambda: reject(lambda: C.decoded(b" "*(C.MAX_BYTES+1)), "bounded_metadata_bytes_required")),
    ("cli_publish_replay_scientific_real_input_refusals", cli),
]


def main():
    global OUT, C, CTX
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    OUT = args.output.resolve(strict=True)
    assert OUT.parent == P and OUT.name == "attempt_001" and not (OUT / "tests.json").exists()
    log = (OUT / "worker.log").open("x", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log
    def failure(kind, value, trace):
        traceback.print_exception(kind, value, trace, file=log)
        (OUT / "worker_failure.json").write_text(json.dumps({"error": str(value), "type": kind.__name__}), encoding="utf-8")
    sys.excepthook = failure
    plan = json.loads((P / "launch_plan_001.json").read_bytes())
    CTX = json.loads((P / "report_context_001.json").read_bytes())
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        assert os.environ.get(key) == "1", key
    denied = {"network": 0, "subprocess": 0, "outside_write": 0, "protected_project_read": 0, "forbidden_import": 0}
    local_socket_probes = []
    unexpected_socket_events = []
    allowed_project = {ROOT / relative for relative in plan["calculator_pins"]} | {ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json"}
    site = ROOT / ".venv/Lib/site-packages"
    def audit(event, values):
        if event.startswith("socket."):
            record = {"event": event, "callsite": [{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                                                   for frame in traceback.extract_stack(limit=16)], "denied": True}
            if event in {"socket.gethostname", "socket.__new__"}:
                local_socket_probes.append(record)
            else:
                denied["network"] += 1
                unexpected_socket_events.append(record)
            raise PermissionError("synthetic_all_socket_operations_denied")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.spawn"}:
            denied["subprocess"] += 1
            raise PermissionError("synthetic_child_process_denied")
        if event == "import" and values[0].split(".")[0] in {"torch", "mne", "moabb", "models", "data", "safetensors"}:
            denied["forbidden_import"] += 1
            raise PermissionError("model_dataset_import_denied")
        if event == "open" and not isinstance(values[0], int):
            path = Path(os.fsdecode(values[0])).resolve()
            mode, flags = values[1], values[2]
            write = (isinstance(mode, str) and any(char in mode for char in "wax+")) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
            if write and not path.is_relative_to(OUT):
                denied["outside_write"] += 1
                raise PermissionError("synthetic_outside_write_denied")
            if not write and path.is_relative_to(ROOT) and not (path.is_relative_to(site) or path.is_relative_to(P) or path in allowed_project):
                denied["protected_project_read"] += 1
                raise PermissionError("raw_checkpoint_recorder_or_unlisted_project_read_denied")
        elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime", "os.truncate"}:
            if not Path(values[0]).resolve().is_relative_to(OUT):
                denied["outside_write"] += 1
                raise PermissionError("synthetic_outside_mutation_denied")
        elif event in {"os.rename", "os.link", "os.symlink"}:
            if any(not Path(value).resolve().is_relative_to(OUT) for value in values[:2]):
                denied["outside_write"] += 1
                raise PermissionError("synthetic_outside_mutation_denied")
    sys.addaudithook(audit)
    sys.path.insert(0, str(site))
    spec = importlib.util.spec_from_file_location("_pro3_synthetic_report", P / "synthetic_report.py")
    C = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = C
    spec.loader.exec_module(C)
    suite = unittest.TestSuite(unittest.FunctionTestCase(fn, description=name) for name, fn in CASES)
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
    assert pools and all(pool["num_threads"] == 1 for pool in pools)
    expected = json.loads((P / "numerical_runtime_manifest_001.json").read_bytes())
    actual_runtime = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if not name:
            continue
        path = Path(name).resolve()
        if path.is_relative_to(site):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert expected[str(path)]["sha256"] == digest, str(path)
            actual_runtime[str(path)] = {"sha256": digest, "bytes": path.stat().st_size}
    for pool in pools:
        path = Path(pool["filepath"]).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected[str(path)]["sha256"] == digest
        actual_runtime[str(path)] = {"sha256": digest, "bytes": path.stat().st_size}
    forbidden = sorted(name for name in sys.modules if name.split(".")[0] in {"torch", "mne", "moabb", "models", "data", "safetensors"})
    probes_expected = all(probe["event"] in {"socket.gethostname", "socket.__new__"} and probe["denied"] is True
                          and any(Path(frame["file"]).resolve().is_relative_to(site)
                                  or Path(frame["file"]).resolve().is_relative_to(Path(sys.base_prefix))
                                  for frame in probe["callsite"])
                          for probe in local_socket_probes)
    passed = result.wasSuccessful() and not forbidden and not any(denied.values()) and threading.active_count() == 1 and probes_expected
    artifact = OUT / "preview_bundle"
    record = {"schema": "pro3_cho_synthetic_report_qualification_v1", "passed": passed, "tests_run": result.testsRun,
              "test_names": [name for name, _ in CASES], "failures": len(result.failures), "errors": len(result.errors),
              "boundary_denials": denied, "denied_local_socket_probes": local_socket_probes,
              "unexpected_denied_socket_events": unexpected_socket_events, "probes_expected": probes_expected, "active_python_threads": threading.active_count(), "actual_native_threadpools": pools,
              "loaded_numerical_runtime_files": actual_runtime, "forbidden_modules_loaded": forbidden,
              "cli_entry_paths_executed": 4, "fixture_variants_calculated": list(REPORTS),
              "preview_bundle": {name: {"sha256": C.sha((artifact/name).read_bytes()), "bytes": (artifact/name).stat().st_size}
                                 for name in ("report.json", "preview.md", "receipt.json")},
              "authority": C.AUTHORITY, "real_cell_model_checkpoint_raw_or_recorder_accessed": False}
    C._write_new(OUT / "tests.json", C.encoded(record))
    print(json.dumps({"passed": passed, "tests_run": result.testsRun, "cli_entry_paths": 4, "numerical_runtime_files": len(actual_runtime)}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
