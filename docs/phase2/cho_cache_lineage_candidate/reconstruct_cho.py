"""Compare a separately admitted Cho subject set without rewriting caches."""
import argparse
from collections import Counter
import gc
import json
from pathlib import Path
import sys
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import ROOT, FIELDS, artifact_arrays, compare_arrays, configuration, finish, sha, start, write_new
from cho_processing import build_artifact, load_runtime, local_raw

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
stage = json.loads(args.plan.read_bytes())["stage"]
if stage not in {"cho_subject001_001", "cho_remaining_001"}:
    raise ValueError("separately admitted Cho reconstruction stage required")
plan, boundary = start(args.output, args.plan, stage)
review_path = ROOT / plan["reviewed_cho_probe"]["path"]
if sha(review_path) != plan["reviewed_cho_probe"]["sha256"]:
    raise ValueError("reviewed Cho probe pin changed")
review = json.loads(review_path.read_bytes())
if not review["passed"] or not review["actual_cho_probe_qualified"] or not review["owned_job_freshly_absent"]:
    raise ValueError("complete qualified probe with physical release required")
np, _, pools, Config, preprocess, _, Dataset, Annotator = load_runtime()
for path, digest in review["measured_runtime_file_pins"].items():
    if sha(path, allow_empty=True) != digest:
        raise ValueError("measured Cho runtime changed")
expected = [1] if stage == "cho_subject001_001" else list(range(2, 53))
if [item["subject"] for item in plan["subjects"]] != expected:
    raise ValueError("exact admitted Cho subject set required")
if stage == "cho_remaining_001":
    first_path = ROOT / plan["reviewed_cho_subject001"]["path"]
    if sha(first_path) != plan["reviewed_cho_subject001"]["sha256"]:
        raise ValueError("reviewed Cho subject001 pin changed")
    first = json.loads(first_path.read_bytes())
    if not first["passed"] or not first["current_processing_reproduced"] or not first["owned_job_freshly_absent"] or first["subject_count"] != 1 or first["subjects"] != [1] or first["canonical_source_sha256"] != plan["canonical_source_sha256"]:
        raise ValueError("complete current-source subject001 comparison and release required")
    if first["measured_runtime_file_pins"] != review["measured_runtime_file_pins"]:
        raise ValueError("Cho subject001 and probe measured runtimes differ")
subjects_out = args.output / "subjects"
subjects_out.mkdir()
results, counts, total = [], Counter(), 0
for target in plan["subjects"]:
    clock = time.perf_counter()
    raw_item, cache_item = target["raw_recording"], target["cache"]
    for item in (raw_item, cache_item):
        path = ROOT / item["path"]
        point = path.stat()
        if point.st_nlink != 1 or path.resolve(strict=True) != path or sha(path) != item["sha256"] or point.st_size != item["bytes"] or point.st_mtime_ns != item["mtime_ns"]:
            raise ValueError("Cho pinned raw/cache bytes or identity changed")
    raw = local_raw(ROOT / raw_item["path"], target["subject"], Dataset, Annotator)
    rebuilt = artifact_arrays(build_artifact(raw, Config, configuration, preprocess), np)
    path = ROOT / cache_item["path"]
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) != 6 or {item.filename for item in entries} != {name + ".npy" for name in FIELDS} or sum(item.file_size for item in entries) > 64 * 1024**2:
            raise ValueError("bounded exact six-member Cho cache required")
    with np.load(path, allow_pickle=False) as payload:
        cached = {name: payload[name] for name in FIELDS}
    comparison = compare_arrays(cached, rebuilt, np)
    if rebuilt["signals"].shape != (target["expected_epochs"], 64, 512):
        raise ValueError("Cho subject epoch/channel/sample dimensions differ")
    class_counts = dict(Counter(str(label) for label in rebuilt["labels"]))
    for item in (raw_item, cache_item):
        point = (ROOT / item["path"]).stat()
        if point.st_nlink != 1 or sha(ROOT / item["path"]) != item["sha256"] or point.st_size != item["bytes"] or point.st_mtime_ns != item["mtime_ns"]:
            raise ValueError("Cho inputs changed after comparison")
    row = {"subject": target["subject"], "passed": comparison["passed"], "epochs": target["expected_epochs"],
        "raw_recording": raw_item, "cache": cache_item, "comparison": comparison, "class_counts": class_counts,
        "inputs_retained": True, "processed_artifact_written": False, "elapsed_seconds": time.perf_counter() - clock,
        "class_block_order_certifies_original_acquisition_chronology": False}
    receipt = subjects_out / f"subject_{target['subject']:02}.json"
    write_new(receipt, row)
    results.append({"subject": target["subject"], "path": receipt.relative_to(ROOT).as_posix(), "sha256": sha(receipt),
        "passed": row["passed"], "exact_signal_values": comparison["signals"]["exact_equal"]})
    total += target["expected_epochs"]
    counts.update(class_counts)
    with (args.output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"subject": target["subject"], "passed": row["passed"], "elapsed_seconds": row["elapsed_seconds"]}) + "\n")
        stream.flush()
    del raw, rebuilt, cached, payload
    gc.collect()
passed = all(row["passed"] for row in results)
finish(args.output, plan, boundary, {"passed": passed, "stage": stage, "subjects": results, "subject_count": len(results),
    "epoch_count": total, "class_counts": dict(counts), "raw_files_decoded": len(results), "caches_decoded": len(results),
    "current_processing_reproduced": passed, "processed_artifacts_written": False,
    "authenticated_historical_generation_scientific_eligibility_or_gate_a_acceptance": False,
    "class_block_order_certifies_original_acquisition_chronology": False}, pools)
raise SystemExit(0 if passed else 1)
