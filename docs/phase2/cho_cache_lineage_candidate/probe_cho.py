"""Measure the installed Cho conversion and frozen Profile A on owned data."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import artifact_arrays, configuration, finish, start
from cho_processing import EVENTS, build_artifact, load_runtime, local_raw, synthetic_fixture

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "cho_probe_001")
np, mne, pools, Config, preprocess, savemat, Dataset, Annotator = load_runtime()
fixture = args.output / "synthetic_cho.mat"
left, right, stim = synthetic_fixture(fixture, np, savemat)
raw = local_raw(fixture, 1, Dataset, Annotator)
signals = raw.get_data()
left_volts = (left - left.mean(axis=1, keepdims=True)) * 1e-6
right_volts = (right - right.mean(axis=1, keepdims=True)) * 1e-6
events, _ = mne.events_from_annotations(raw, event_id=EVENTS, regexp=None, verbose=False)
arrays = artifact_arrays(build_artifact(raw, Config, configuration, preprocess), np)
checks = [
    {"case": "inherited_local_loader_units_demeaning_and_class_stack", "passed": signals.shape == (69, 16884) and bool(np.allclose(signals[:68, :8192], left_volts, atol=1e-15, rtol=1e-12)) and bool(np.allclose(signals[:68, 8692:], right_volts, atol=1e-15, rtol=1e-12))},
    {"case": "500_sample_zero_buffer_and_stim_codes", "passed": bool(np.array_equal(signals[:, 8192:8692], np.zeros((69, 500)))) and bool(np.array_equal(signals[68, :8192], stim[0])) and bool(np.array_equal(signals[68, 8692:], stim[0] * 2))},
    {"case": "default_annotations_have_zero_offset", "passed": bool(np.array_equal(events[:, 0], [1024, 4096, 9716, 12788])) and bool(np.array_equal(events[:, 2], [1, 1, 2, 2]))},
    {"case": "EEG_EMG_stim_and_sampling_contract", "passed": raw.get_channel_types().count("eeg") == 64 and raw.get_channel_types().count("emg") == 4 and raw.get_channel_types().count("stim") == 1 and float(raw.info["sfreq"]) == 512.0},
    {"case": "canonical_ProfileA_shape_channel_and_trial_schema", "passed": arrays["signals"].shape == (4, 64, 512) and arrays["signals"].dtype == np.dtype("float32") and bool(np.isfinite(arrays["signals"]).all()) and len(set(arrays["channel_names"].tolist())) == 64 and arrays["channel_names"][0] == "Fp1" and arrays["labels"].tolist() == ["left_hand", "left_hand", "right_hand", "right_hand"] and arrays["sessions"].tolist() == ["0"] * 4 and arrays["runs"].tolist() == ["0"] * 4 and arrays["trial_indices"].tolist() == [0, 1, 2, 3]},
]
if not all(row["passed"] for row in checks):
    raise ValueError("Cho local-loader/annotation/ProfileA probe failed")
finish(args.output, plan, boundary, {"passed": True, "stage": "cho_probe_001", "probe_checks": checks,
    "synthetic_signal_shape": [4, 64, 512], "real_raw_files_decoded": 0, "real_cache_decoded": False,
    "class_block_order_certifies_original_acquisition_chronology": False}, pools)
