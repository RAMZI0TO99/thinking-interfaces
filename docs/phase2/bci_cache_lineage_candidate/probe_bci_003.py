"""Synthetic BCI runtime probe includes the installed converter's metadata."""
import argparse
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import configuration, finish, start, write_new
from bci_processing import CHANNELS, EVENTS, build_arrays, load_bci_runtime, local_runs

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "probe_003")
np, mne, pools, Config, savemat, convert, Annotator, preprocess = load_bci_runtime()
signal = np.outer(np.sin(2 * np.pi * 12 * np.arange(10000) / 250), np.arange(1, 26))
fixture = args.output / "synthetic_bci.mat"
savemat(fixture, {"data": {"X": signal, "fs": 250, "trial": np.asarray([251, 2251, 4251, 6251]),
    "y": np.asarray([1, 2, 3, 4]), "classes": np.asarray(["left hand", "right hand", "both feet", "tongue"], dtype=object),
    "age": 25, "gender": "female", "artifacts": np.zeros(4, dtype=np.int64)}})
raws = local_runs(fixture, 1, convert, Annotator)
native_events, _ = mne.events_from_annotations(raws[0], event_id=EVENTS, regexp=None, verbose=False)
arrays = build_arrays([("0train", raws)], configuration(Config), np, preprocess)
demographics = raws[0].info["subject_info"]
checks = [
    {"case": "MAT_converter_one_run_and_volt_units", "passed": len(raws) == 1 and bool(np.allclose(raws[0].get_data()[:25], signal.T * 1e-6, atol=1e-15, rtol=1e-12))},
    {"case": "cue_offset_500_native_samples", "passed": bool(np.array_equal(native_events[:, 0], [750, 2750, 4750, 6750]))},
    {"case": "four_classes_and_epoch_shape", "passed": arrays["signals"].shape == (4, 22, 512) and arrays["labels"].tolist() == list(EVENTS)},
    {"case": "original_channel_names_and_trial_schema", "passed": arrays["channel_names"].tolist() == CHANNELS[:22] and arrays["sessions"].tolist() == ["0train"] * 4 and arrays["runs"].tolist() == ["0"] * 4 and arrays["trial_indices"].tolist() == [0, 1, 2, 3]},
    {"case": "installed_BNCI_demographics_and_artifact_fields", "passed": demographics["birthday"] == date(1983, 1, 1) and demographics["sex"] == 2 and demographics["hand"] == 1 and demographics["his_id"] == "sub-01" and raws[0].info["line_freq"] == 50.0},
]
write_new(args.output / "probe_checks.json", {"checks": checks, "native_event_samples": native_events[:, 0].tolist(),
    "signal_shape": list(arrays["signals"].shape), "labels": arrays["labels"].tolist(),
    "channel_names": arrays["channel_names"].tolist(), "synthetic_birthday": str(demographics["birthday"]),
    "recording_year": raws[0].info["meas_date"].year, "synthetic_demographics_only": True})
if not all(row["passed"] for row in checks):
    raise ValueError("BCI synthetic loader/annotation/provenance qualification failed")
finish(args.output, plan, boundary, {"passed": True, "stage": "probe_003", "probe_checks": checks,
    "synthetic_signal_shape": [4, 22, 512], "real_raw_files_decoded": 0, "real_cache_decoded": False}, pools)
