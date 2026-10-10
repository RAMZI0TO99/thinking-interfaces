"""Sequential read-only reconstruction of the remaining 108 MMIDB caches."""
import argparse
from collections import Counter
import gc
import json
import sys
from datetime import UTC, datetime
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import ROOT, FIELDS, artifact_arrays, compare_arrays, configuration, finish, load_runtime, sha, start, write_new

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "remaining_001")
np, _, read_edf, pools, drop, Config, preprocess = load_runtime()
probe = json.loads((ROOT / plan["reviewed_probe"]["path"]).read_bytes())
for path, expected in probe["environment"]["imported_module_file_pins"].items():
    if sha(path, allow_empty=True) != expected:
        raise ValueError("measured runtime changed")
if not probe["passed"] or len(probe["comparison_qualification"]) != 12:
    raise ValueError("qualified scientific runtime required")
single = json.loads((ROOT / plan["reused_subject001_result"]["path"]).read_bytes())
if not single["passed"] or not single["comparison"]["signals"]["exact_equal"]:
    raise ValueError("complete prior subject001 result required")
if [row["subject"] for row in plan["subjects"]] != list(range(2, 110)):
    raise ValueError("exact remaining108 subject order required; no eligibility exclusions")
config = configuration(Config)
subjects_out = args.output / "subjects"
subjects_out.mkdir()
receipts, failures, counts = [], [], Counter()
epoch_total = 0


def progress(event, **values):
    with (args.output / "progress.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"utc": datetime.now(UTC).isoformat(), "event": event, **values}, sort_keys=True) + "\n")
        stream.flush()


for target in plan["subjects"]:
    clock = time.perf_counter()
    subject = target["subject"]
    progress("subject_started", subject=subject)
    try:
        runs, raw_rows = [], []
        for item in target["raw_recordings"]:
            path = ROOT / item["path"]
            if path.stat().st_nlink != 1 or path.resolve(strict=True) != path or sha(path) != item["sha256"]:
                raise ValueError("raw recording alias/hash changed")
            raw = read_edf(path, preload=True, verbose=False)
            clean, dropped = drop(raw, baseline_s=config.baseline_duration_s, epoch_s=config.epoch_duration_s)
            runs.append(("0", path.stem[-2:], clean))
            raw_rows.append({"path": item["path"], "sha256": item["sha256"], "bytes": int(path.stat().st_size),
                "sampling_rate_hz": float(raw.info["sfreq"]), "samples": int(raw.n_times), "channels": len(raw.ch_names),
                "motor_annotations": int(np.count_nonzero(np.isin(raw.annotations.description, ["T1", "T2"]))),
                "incomplete_motor_annotations_dropped": int(dropped)})
        artifact = preprocess(runs, event_id={"T1": 2, "T2": 3}, label_map={"T1": "left_fist", "T2": "right_fist"}, config=config)
        rebuilt = artifact_arrays(artifact, np)
        path = ROOT / target["cache"]["path"]
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) != 6 or {row.filename for row in entries} != {name + ".npy" for name in FIELDS} or sum(row.file_size for row in entries) > 64 * 1024**2:
                raise ValueError("bounded exact six-member cache required")
        with np.load(path, allow_pickle=False) as payload:
            cached = {name: payload[name] for name in FIELDS}
        comparison = compare_arrays(cached, rebuilt, np)
        if rebuilt["signals"].shape != (target["expected_epochs"], 64, 512):
            raise ValueError("expected existing subject shape differs")
        for item in target["raw_recordings"] + [target["cache"]]:
            path = ROOT / item["path"]
            point = path.stat()
            if sha(path) != item["sha256"] or point.st_size != item["bytes"] or point.st_mtime_ns != item["mtime_ns"]:
                raise ValueError("raw/cache bytes/size/mtime changed")
        row = {"subject": subject, "passed": comparison["passed"], "epochs": target["expected_epochs"],
            "class_counts": artifact.class_counts, "raw_recordings": raw_rows, "cache": target["cache"],
            "comparison": comparison, "elapsed_seconds": time.perf_counter() - clock, "inputs_retained": True,
            "processed_artifact_written": False, "authenticated_historical_generation_or_scientific_eligibility": False}
        if not row["passed"]:
            failures.append({"subject": subject, "reason": "comparison mismatch"})
        counts.update(artifact.class_counts)
        epoch_total += target["expected_epochs"]
        del raw, clean, runs, artifact, rebuilt, cached, payload
        gc.collect()
    except Exception as error:
        # Preserve a structural/numerical finding, but never reinterpret a
        # resource, isolation, changing-input or unexpected implementation error.
        progress("subject_error", subject=subject, error_type=type(error).__name__, error=str(error)[:2000])
        raise
    receipt_path = subjects_out / f"subject_{subject:03}.json"
    write_new(receipt_path, row)
    receipts.append({"subject": subject, "path": receipt_path.relative_to(ROOT).as_posix(), "sha256": sha(receipt_path), "passed": row["passed"],
                     "epochs": row["epochs"], "signal_values_exact_equal": row["comparison"]["signals"]["exact_equal"]})
    progress("subject_completed", subject=subject, passed=row["passed"], epochs=row["epochs"], elapsed_seconds=row["elapsed_seconds"])
all_passed = not failures and len(receipts) == 108 and epoch_total + single["rebuilt_epochs"] == 4917
record = finish(args.output, plan, boundary, {"passed": all_passed, "stage": "remaining_001", "fresh_subjects": 108,
    "reused_subject001_result": plan["reused_subject001_result"], "all109_current_processing_reproduced": all_passed,
    "fresh_epoch_count": epoch_total, "combined_epoch_count": epoch_total + single["rebuilt_epochs"],
    "fresh_class_counts": dict(counts), "subjects": receipts, "mismatches": failures,
    "fresh_raw_recordings_decoded": 324, "fresh_caches_decoded": 108, "processed_artifacts_written": False,
    "single_subject_not_replayed": True, "scientific_eligibility_cohort_or_historical_generation_verified": False}, pools)
raise SystemExit(0 if record["passed"] else 1)
