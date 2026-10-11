"""All nine BCI Profile A caches reconstructed sequentially from pinned local MATs."""
import argparse
from collections import Counter
import gc
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
import time
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import ROOT, FIELDS, compare_arrays, configuration, finish, sha, start, write_new
from bci_processing import build_arrays, load_bci_runtime, local_runs

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "reconstruct_001")
np, _, pools, Config, _, convert, Annotator, preprocess = load_bci_runtime()
review_path = ROOT / plan["reviewed_bci_probe"]["path"]
if sha(review_path) != plan["reviewed_bci_probe"]["sha256"]:
    raise ValueError("reviewed BCI probe pin changed")
probe = json.loads(review_path.read_bytes())
if not probe["passed"] or not probe["actual_bci_probe_qualified"] or not probe["owned_job_freshly_absent"] or probe["probe_checks_passed"] != 5 or probe["canonical_source_sha256"] != plan["canonical_source_sha256"]:
    raise ValueError("complete current-source qualified revised BCI probe and physical release required")
for path, expected in probe["measured_runtime_file_pins"].items():
    if sha(path, allow_empty=True) != expected:
        raise ValueError("measured BCI runtime changed")
config = configuration(Config)
subjects_out = args.output / "subjects"
subjects_out.mkdir()
results, counts = [], Counter()
total = 0
if [target["subject"] for target in plan["subjects"]] != list(range(1, 10)):
    raise ValueError("exact nine subjects required")
for target in plan["subjects"]:
    clock = time.perf_counter()
    sessions = []
    for index, item in enumerate(target["raw_recordings"]):
        path = ROOT / item["path"]
        if path.stat().st_nlink != 1 or path.resolve(strict=True) != path or sha(path) != item["sha256"]:
            raise ValueError("BCI raw alias/hash changed")
        raws = local_runs(path, target["subject"], convert, Annotator)
        if len(raws) != 6:
            raise ValueError("six event-bearing runs per BCI session required")
        sessions.append(("0train" if index == 0 else "1test", raws))
    rebuilt = build_arrays(sessions, config, np, preprocess)
    path = ROOT / target["cache"]["path"]
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) != 6 or {row.filename for row in entries} != {name + ".npy" for name in FIELDS} or sum(row.file_size for row in entries) > 64 * 1024**2:
            raise ValueError("bounded exact six-member BCI cache required")
    with np.load(path, allow_pickle=False) as payload:
        cached = {name: payload[name] for name in FIELDS}
    comparison = compare_arrays(cached, rebuilt, np)
    if rebuilt["signals"].shape != (576, 22, 512):
        raise ValueError("expected BCI576x22x512 shape differs")
    for item in target["raw_recordings"] + [target["cache"]]:
        path = ROOT / item["path"]
        point = path.stat()
        if sha(path) != item["sha256"] or point.st_size != item["bytes"] or point.st_mtime_ns != item["mtime_ns"]:
            raise ValueError("BCI raw/cache bytes or metadata changed")
    class_counts = dict(Counter(str(label) for label in rebuilt["labels"]))
    row = {"subject": target["subject"], "passed": comparison["passed"], "epochs": 576, "raw_recordings": target["raw_recordings"],
        "cache": target["cache"], "comparison": comparison, "class_counts": class_counts, "inputs_retained": True,
        "processed_artifact_written": False, "elapsed_seconds": time.perf_counter() - clock}
    receipt = subjects_out / f"subject_{target['subject']:02}.json"
    write_new(receipt, row)
    results.append({"subject": target["subject"], "path": receipt.relative_to(ROOT).as_posix(), "sha256": sha(receipt),
        "passed": row["passed"], "exact_signal_values": comparison["signals"]["exact_equal"]})
    total += 576
    counts.update(class_counts)
    with (args.output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"utc": datetime.now(UTC).isoformat(), "subject": target["subject"], "passed": row["passed"], "elapsed_seconds": row["elapsed_seconds"]}) + "\n")
        stream.flush()
    del sessions, raws, rebuilt, cached, payload
    gc.collect()
passed = all(row["passed"] for row in results) and total == 5184
finish(args.output, plan, boundary, {"passed": passed, "stage": "reconstruct_001", "subjects": results, "subject_count": 9,
    "epoch_count": total, "class_counts": dict(counts), "raw_files_decoded": 18, "caches_decoded": 9,
    "all9_current_processing_reproduced": passed, "processed_artifacts_written": False,
    "authenticated_historical_generation_scientific_eligibility_or_gate_a_acceptance": False}, pools)
raise SystemExit(0 if passed else 1)
