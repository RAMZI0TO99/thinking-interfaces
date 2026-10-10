"""One pinned real subject; original raw and cache files opened read-only."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common import ROOT, FIELDS, artifact_arrays, compare_arrays, configuration, finish, load_runtime, sha, start

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "reconstruct_001")
np, _, read_edf, pools, drop, Config, preprocess = load_runtime()
probe = json.loads((ROOT / plan["reviewed_probe"]["path"]).read_bytes())
for path, expected in probe["environment"]["imported_module_file_pins"].items():
    if sha(path) != expected:
        raise ValueError("reviewed scientific runtime changed: " + path)
if not probe["passed"] or len(probe["comparison_qualification"]) != 10:
    raise ValueError("actual qualified probe required")
config = configuration(Config)
runs, input_rows = [], []
for item in plan["raw_recordings"]:
    path = ROOT / item["path"]
    before = path.stat()
    if before.st_nlink != 1 or path.resolve(strict=True) != path or sha(path) != item["sha256"]:
        raise ValueError("raw recording alias/hash changed")
    raw = read_edf(path, preload=True, verbose=False)
    clean, dropped = drop(raw, baseline_s=config.baseline_duration_s, epoch_s=config.epoch_duration_s)
    runs.append(("0", path.stem[-2:], clean))
    input_rows.append({"path": item["path"], "sha256": item["sha256"], "bytes": before.st_size,
                       "sampling_rate_hz": float(raw.info["sfreq"]), "samples": raw.n_times, "channels": len(raw.ch_names),
                       "motor_annotations": int(np.count_nonzero(np.isin(raw.annotations.description, ["T1", "T2"]))),
                       "incomplete_motor_annotations_dropped": dropped})
artifact = preprocess(runs, event_id={"T1": 2, "T2": 3}, label_map={"T1": "left_fist", "T2": "right_fist"}, config=config)
rebuilt = artifact_arrays(artifact, np)
path = ROOT / plan["cache"]["path"]
with zipfile.ZipFile(path) as archive:
    entries = archive.infolist()
    if len(entries) != 6 or {row.filename for row in entries} != {name + ".npy" for name in FIELDS} or sum(row.file_size for row in entries) > 16 * 1024**2:
        raise ValueError("bounded nonduplicate six-member cache required")
with np.load(path, allow_pickle=False) as payload:
    cached = {name: payload[name] for name in FIELDS}
comparison = compare_arrays(cached, rebuilt, np)
if rebuilt["signals"].shape != (45, 64, 512):
    raise ValueError("pinned subject001 expected 45 epochs")
for item in plan["raw_recordings"] + [plan["cache"]]:
    if sha(ROOT / item["path"]) != item["sha256"]:
        raise ValueError("input changed after reconstruction")
record = finish(args.output, plan, boundary, {"passed": comparison["passed"], "stage": "reconstruct_001", "subject": "mmidb/001",
    "raw_recordings": input_rows, "cache": plan["cache"], "comparison": comparison, "input_bytes_unchanged": True,
    "rebuilt_epochs": 45, "rebuilt_class_counts": artifact.class_counts,
    "real_recordings_decoded": 3, "real_cache_decoded": True, "processed_artifact_written": False,
    "subject001_current_processing_reproduced": comparison["passed"], "other_subjects_reconstructed": 0}, pools)
raise SystemExit(0 if record["passed"] else 1)
