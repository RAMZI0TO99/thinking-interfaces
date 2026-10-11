"""Write-once reports for internal synthetic fixtures; no real input interface."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

MAX_BYTES = 1024**2
SOURCE = "3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529"
QUALITY = "4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357"
OWNER = "2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400"
MODULE_PINS = {
    "evaluation/phase2_inference.py": "ceb4369da7e277dd0a3a6a8050c3f1002eaa800b05026183c1d920116f9c0189",
    "evaluation/phase2_subject_aggregation.py": "8f32ebc19bf7977c777a92114c324e7b73b0be97a169063b874df5dd59fd9a34",
    "evaluation/phase2_protocol.py": "4547de8f2606aa40f5c901a0c06db473c8eead0a27ac2930581485e4a86eab9f",
    "core/config.py": "1b55c368098a138396f9cd9bfbf1d9d196c2b1e74c718b74d569778c69e52e79",
    "evaluation/__init__.py": "c63f07e2fee073e5fc641df4a1d04c595285be01abc85282b077b3277234bfdf",
    "core/__init__.py": "84f9835e5a02662d99556a21aa014a352ae9abb307a22c4add4ba425ed3203ca",
}
FIXTURES = ("zero", "positive", "negative", "ties", "rank_mean_disagree")
METHODS = ("labram_linear", "labram_lora", "labram_full", "eegnet")
SEEDS = (11, 23, 37, 53, 71)
SUBJECTS = tuple(f"subject_{i:02d}" for i in range(1, 53))
AUTHORITY = {
    "scientific_cells_admitted": False,
    "scientific_gate_a_signed": False,
    "experiment_freeze_signed": False,
    "checkpoint_training_coverage_verified": False,
    "actual_checkpoint_target_overlap_verified": False,
    "scientific_claim_issued": False,
    "real_training_or_case_admitted": False,
    "original_case_attempts_remaining": 0,
}


class ReportError(ValueError):
    """A report or publication boundary was refused."""


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _regular(path, *, directory=False):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
        raise ReportError("reparse_or_symbolic_link_refused")
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ReportError("regular_directory_or_file_required")
    if not directory and info.st_nlink != 1:
        raise ReportError("multiply_linked_file_refused")
    return info


def _directory_chain(path):
    path = Path(os.path.abspath(path))
    for item in (*reversed(path.parents), path):
        _regular(item, directory=True)
    return path


def read_small(path):
    path = Path(os.path.abspath(path))
    _directory_chain(path.parent)
    before = _regular(path)
    if not 0 < before.st_size <= MAX_BYTES:
        raise ReportError("bounded_metadata_file_required")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(MAX_BYTES + 1)
        after_handle = os.fstat(stream.fileno())
    after = _regular(path)
    for item in (opened, after_handle, after):
        if not os.path.samestat(before, item) or item.st_size != before.st_size or item.st_mtime_ns != before.st_mtime_ns:
            raise ReportError("metadata_file_changed_during_read")
    if len(data) != before.st_size:
        raise ReportError("metadata_file_changed_during_read")
    return data


def decoded(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ReportError("duplicate_json_key")
            result[key] = value
        return result

    def constant(value):
        raise ReportError("nonfinite_json")

    if type(data) is not bytes or not 0 < len(data) <= MAX_BYTES:
        raise ReportError("bounded_metadata_bytes_required")
    try:
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ReportError("invalid_json") from error
    if type(value) is not dict:
        raise ReportError("json_object_required")
    return value


def validate_context(value):
    keys = {"execution_git_commit", "canonical_source_sha256", "canonical_files", "quality_pointer_sha256", "owner_packet_sha256"}
    if type(value) is not dict or set(value) != keys:
        raise ReportError("exact_context_fields_required")
    git = value["execution_git_commit"]
    if type(git) is not str or re.fullmatch(r"[0-9a-f]{40}", git) is None:
        raise ReportError("execution_git_digest_required")
    if value["canonical_source_sha256"] != SOURCE or type(value["canonical_files"]) is not int or value["canonical_files"] != 432:
        raise ReportError("canonical_source_context_changed")
    if value["quality_pointer_sha256"] != QUALITY or value["owner_packet_sha256"] != OWNER:
        raise ReportError("quality_or_unsigned_owner_context_changed")
    return dict(value)


def rational(value):
    if type(value) is not Fraction:
        raise ReportError("exact_fraction_required")
    return {"numerator": value.numerator, "denominator": value.denominator}


def _difference(fixture, index):
    if fixture == "zero":
        return Fraction()
    if fixture == "positive":
        return Fraction(1, 10)
    if fixture == "negative":
        return Fraction(-1, 10)
    if fixture == "ties":
        return (Fraction(), Fraction(1, 10), Fraction(-1, 10), Fraction(1, 5))[index % 4]
    if fixture == "rank_mean_disagree":
        return Fraction(1, 1000) if index < 51 else Fraction(-1, 2)
    raise ReportError("unknown_internal_fixture")


def _load_calculators(root):
    root = _directory_chain(root)
    pins = {**MODULE_PINS, "docs/phase2/cho_owner_decision_packet_20261010.json": OWNER}
    buffers = {}
    for relative, digest in pins.items():
        data = read_small(root / relative)
        if sha(data) != digest:
            raise ReportError("project_calculator_or_owner_pin_changed")
        buffers[relative] = data
    owner = decoded(buffers["docs/phase2/cho_owner_decision_packet_20261010.json"])
    modules = dict((name, relative) for name, relative in (
        ("evaluation", "evaluation/__init__.py"), ("core", "core/__init__.py"),
        ("core.config", "core/config.py"), ("evaluation.phase2_protocol", "evaluation/phase2_protocol.py"),
        ("evaluation.phase2_subject_aggregation", "evaluation/phase2_subject_aggregation.py"),
        ("evaluation.phase2_inference", "evaluation/phase2_inference.py"),
    ))
    class PinnedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            relative = modules[fullname]
            current = read_small(root / relative)
            if current != buffers[relative]:
                raise ReportError("calculator_bytes_changed_before_compile")
            return compile(current, str(root / relative), "exec", dont_inherit=True)

    class PinnedFinder:
        def find_spec(self, fullname, path=None, target=None):
            if fullname in modules:
                filename = str(root / modules[fullname])
                return importlib.util.spec_from_file_location(fullname, filename, loader=PinnedLoader(fullname, filename))
            return None

    finder = PinnedFinder()
    sys.meta_path.insert(0, finder)
    try:
        from evaluation import phase2_subject_aggregation as aggregation
        from evaluation import phase2_inference as inference
    finally:
        sys.meta_path.remove(finder)
    for name, relative in modules.items():
        if Path(sys.modules[name].__file__).resolve() != root / relative or read_small(root / relative) != buffers[relative]:
            raise ReportError("loaded_calculator_origin_or_bytes_changed")
    return aggregation, inference, owner


def build_report(project_root, fixture, context):
    context = validate_context(context)
    if type(fixture) is not str or fixture not in FIXTURES:
        raise ReportError("unknown_internal_fixture")
    aggregation, inference, owner = _load_calculators(project_root)
    rows, serialized = [], []
    for index, subject in enumerate(SUBJECTS):
        for method in METHODS:
            for seed_index, seed in enumerate(SEEDS):
                value = {"labram_linear": Fraction(1, 2), "labram_lora": Fraction(1, 2) + _difference(fixture, index),
                         "labram_full": Fraction(9, 20), "eegnet": Fraction(11, 20)}[method]
                # The zero LoRA score in the disagreement fixture remains in [0, 1].
                offset = Fraction(seed_index - 2, 1000) if 0 < value < 1 else Fraction()
                score = value + offset
                cell = {"dataset": "cho2017", "subject": subject, "method": method, "shots": 5, "seed": seed,
                        "balanced_accuracy": rational(score), "provenance": "fabricated_internal_fixture_only"}
                digest = sha(encoded(cell))
                serialized.append({**cell, "synthetic_cell_sha256": digest})
                key = aggregation.ExpectedCell("cho2017", subject, method, 5, seed)
                rows.append(aggregation.ScoreRow(key, score.numerator, score.denominator, digest))
    # A digest authenticates only these invented fixture bytes, never a real cell.
    aggregated = aggregation.aggregate_subject_methods(tuple(row.key for row in rows), rows)
    means = {(item.subject, item.method): Fraction(item.numerator, item.denominator) for item in aggregated.means}
    pairs = tuple((subject, means[(subject, "labram_lora")] - means[(subject, "labram_linear")]) for subject in SUBJECTS)
    result = inference.calculate_cho_paired_inference(pairs, expected_subjects=SUBJECTS)
    import numpy
    import scipy
    numeric = {
        "mean_difference": rational(result.mean_difference), "sample_variance": rational(result.sample_variance),
        "wilcoxon_statistic": result.wilcoxon_statistic, "wilcoxon_p_value_unrounded": result.wilcoxon_p_value,
        "zero_difference_count": result.zero_difference_count, "nonzero_tied_subject_count": result.nonzero_tied_subject_count,
        "nonzero_absolute_tie_class_count": result.nonzero_absolute_tie_class_count,
        "paired_mean_ci_95": list(result.paired_mean_ci_95), "paired_mean_ci_90": list(result.paired_mean_ci_90),
    }
    if not all(math.isfinite(value) for value in (result.wilcoxon_p_value, result.wilcoxon_statistic, *result.paired_mean_ci_95, *result.paired_mean_ci_90)):
        raise ReportError("nonfinite_calculation_refused")
    primary = dict(owner["proposed_primary_analysis"])
    secondary = dict(owner["proposed_secondary_analysis"])
    margin = dict(owner["proposed_margin_display"])
    levels = dict(result.signed_rank_levels)
    report = {
        "schema": "pro3_cho_internal_synthetic_primary_report_v1", "scope": "synthetic_engineering_only", "fixture": fixture,
        "authority": dict(AUTHORITY), "execution_context_declaration": context,
        "execution_context_independently_authenticated_by_candidate": False,
        "implementation_pins": MODULE_PINS, "candidate_sha256": sha(read_small(Path(__file__))),
        "runtime": {"python": sys.version, "numpy": numpy.__version__, "scipy": scipy.__version__},
        "proposed_primary_analysis": primary, "proposed_secondary_analysis": secondary, "proposed_margin_display": margin,
        "roster": {"dataset": "cho2017", "subjects": list(SUBJECTS), "methods": list(METHODS), "shots": 5, "seeds": list(SEEDS),
                   "cell_count": len(rows), "subject_method_mean_count": len(aggregated.means), "inferential_unit_count": len(pairs),
                   "synthetic_cells_sha256": sha(encoded(serialized)), "real_cells_read": 0},
        "synthetic_cells": serialized,
        "subject_method_means": [{"subject": item.subject, "method": item.method, "contributing_seeds": item.contributing_cells,
                                  "balanced_accuracy": rational(Fraction(item.numerator, item.denominator))} for item in aggregated.means],
        "subject_pairs": [{"subject": subject, "lora_minus_linear": rational(value), "signed_rank_level": levels[subject]} for subject, value in pairs],
        "synthetic_primary_calculation": numeric,
        "synthetic_numeric_condition_diagnostic": {
            "unrounded_p_less_than_proposed_alpha": result.wilcoxon_p_value < primary["alpha"],
            "strictly_positive_exact_paired_mean": result.mean_difference > 0,
            "both_proposed_numeric_conditions_met": result.wilcoxon_p_value < primary["alpha"] and result.mean_difference > 0,
            "scientific_superiority_claim": False,
        },
        "secondary_superiority_p_values": [], "formal_tost_or_equivalence_decision": None,
    }
    if len(encoded(report)) > MAX_BYTES:
        raise ReportError("report_exceeds_metadata_bound")
    return report


def preview(report):
    calculation = report["synthetic_primary_calculation"]
    mean = calculation["mean_difference"]
    lines = ["# Synthetic engineering report preview", "", "Invented values only. No decoding result or scientific claim.", "",
             f"Fixture: `{report['fixture']}`. 1,040 fabricated cells; 208 five-seed means; 52 subject units.", "",
             f"Exact paired mean: {mean['numerator']}/{mean['denominator']}.",
             f"Unrounded proposed Pratt p-value: {calculation['wilcoxon_p_value_unrounded']!r}.",
             f"Separate 95% paired-mean interval: {calculation['paired_mean_ci_95']!r}.",
             f"Separate exploratory 90% paired-mean interval: {calculation['paired_mean_ci_90']!r}.", "",
             "These intervals are not inversions of the signed-rank test. The exact JSON contains all cells, means, ties and unsigned rules.", "",
             "| Subject | Exact LoRA minus linear | Signed integer level |", "| --- | --- | --- |"]
    for row in report["subject_pairs"]:
        value = row["lora_minus_linear"]
        lines.append(f"| {row['subject']} | {value['numerator']}/{value['denominator']} | {row['signed_rank_level']} |")
    lines += ["", "Gate A and the experiment freeze remain unsigned. No real cells were read. Original case attempts remain zero.", ""]
    return "\n".join(lines).encode("utf-8")


def _write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _receipt(report, outputs):
    return {"schema": "pro3_cho_synthetic_write_once_publication_v1", "scope": "synthetic_engineering_only",
            "complete": True, "fixture": report["fixture"], "authority": dict(AUTHORITY),
            "execution_context_declaration": report["execution_context_declaration"],
            "candidate_sha256": report["candidate_sha256"],
            "outputs": {name: {"sha256": sha(data), "bytes": len(data)} for name, data in outputs.items()}}


def publish_fixture(project_root, fixture, context, destination):
    destination = Path(os.path.abspath(destination))
    _directory_chain(destination.parent)
    if os.path.lexists(destination):
        raise ReportError("new_publication_directory_required")
    report = build_report(project_root, fixture, context)
    outputs = {"report.json": encoded(report), "preview.md": preview(report)}
    # mkdir and exclusive file creation also refuse an intervening competing writer.
    destination.mkdir(exist_ok=False)
    _regular(destination, directory=True)
    for name, data in outputs.items():
        _write_new(destination / name, data)
    _write_new(destination / "receipt.json", encoded(_receipt(report, outputs)))
    return {"publication_complete": True, "scope": "synthetic_engineering_only", "authority": dict(AUTHORITY),
            "receipt_sha256": sha(read_small(destination / "receipt.json"))}


def verify_publication(project_root, destination):
    destination = _directory_chain(destination)
    if {item.name for item in destination.iterdir()} != {"report.json", "preview.md", "receipt.json"}:
        raise ReportError("exact_complete_publication_inventory_required")
    receipt_bytes = read_small(destination / "receipt.json")
    receipt = decoded(receipt_bytes)
    if receipt.get("authority") != AUTHORITY or receipt.get("complete") is not True or receipt.get("scope") != "synthetic_engineering_only":
        raise ReportError("synthetic_publication_authority_or_scope_changed")
    report = build_report(project_root, receipt.get("fixture"), receipt.get("execution_context_declaration"))
    outputs = {name: read_small(destination / name) for name in ("report.json", "preview.md")}
    expected = {"report.json": encoded(report), "preview.md": preview(report)}
    if outputs != expected or receipt_bytes != encoded(_receipt(report, expected)):
        raise ReportError("publication_bytes_or_internal_fixture_changed")
    return {"publication_complete": True, "scope": "synthetic_engineering_only", "authority": dict(AUTHORITY),
            "receipt_sha256": sha(read_small(destination / "receipt.json"))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--context-file", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--fixture", choices=FIXTURES, required=True)
    parser.add_argument("--mode", choices=("synthetic",), default="synthetic")
    args = parser.parse_args(argv)
    try:
        context = validate_context(decoded(read_small(args.context_file)))
        result = publish_fixture(args.project_root, args.fixture, context, args.output_directory)
    except (ReportError, OSError) as error:
        print(json.dumps({"publication_complete": False, "error": str(error), "scope": "synthetic_engineering_only", "authority": AUTHORITY}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
