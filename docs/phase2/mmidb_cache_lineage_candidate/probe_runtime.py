"""Actual imports and synthetic preprocessing/comparison; no real data read."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common import artifact_arrays, compare_arrays, configuration, finish, load_runtime, start

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "probe_001")
np, mne, _, pools, drop, Config, preprocess = load_runtime()
config = configuration(Config)
raw = mne.io.RawArray(np.zeros((2, 1920)), mne.create_info(["C3", "C4"], 160, "eeg"), verbose=False)
raw.set_annotations(mne.Annotations([2, 7], [4, 4], ["T1", "T2"]))
clean, dropped = drop(raw, baseline_s=config.baseline_duration_s, epoch_s=config.epoch_duration_s)
artifact = preprocess([("0", "04", clean)], event_id={"T1": 2, "T2": 3}, label_map={"T1": "left_fist", "T2": "right_fist"}, config=config)
arrays = artifact_arrays(artifact, np)
if arrays["signals"].shape != (2, 2, 512) or dropped:
    raise ValueError("synthetic frozen preprocessing shape differs")
checks = []
checks.append({"case": "exact", "passed": compare_arrays(arrays, arrays, np)["passed"]})
for case, field, transform in (
    ("within_absolute_tolerance", "signals", lambda x: x + np.float32(5e-13)),
    ("outside_tolerance", "signals", lambda x: x + np.float32(1e-8)),
    ("label_order", "labels", lambda x: x[::-1].copy()),
    ("run_identity", "runs", lambda x: np.asarray(["08", "08"])),
    ("trial_identity", "trial_indices", lambda x: x[::-1].copy()),
    ("channel_order", "channel_names", lambda x: x[::-1].copy()),
    ("shape", "signals", lambda x: x[:, :, :-1]),
    ("dtype", "signals", lambda x: x.astype(np.float64)),
    ("nonfinite", "signals", lambda x: np.full_like(x, np.nan)),
):
    other = dict(arrays)
    other[field] = transform(arrays[field])
    accepted = compare_arrays(arrays, other, np)["passed"]
    expected = case == "within_absolute_tolerance"
    checks.append({"case": case, "expected_match": expected, "actual_match": accepted, "passed": accepted == expected})
if not all(row["passed"] for row in checks):
    raise ValueError("comparison qualification failed")
finish(args.output, plan, boundary, {"passed": True, "stage": "probe_001", "synthetic_processing_shape": [2, 2, 512],
       "comparison_qualification": checks, "real_recordings_decoded": 0, "real_cache_decoded": False}, pools)
