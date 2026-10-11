"""Owned synthetic60Hz loader/filter/scaling/comparison runtime qualification."""
import argparse
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker_common_004 import finish, start, write_new
from cho_processing import local_raw
from processing import EVENTS, build_arrays, compare_scaled, configuration, load_runtime

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--plan", type=Path, required=True)
args = parser.parse_args()
plan, boundary = start(args.output, args.plan, "probe60_001")
np, mne, pools, Config, collect, scale, savemat, Dataset, Annotator = load_runtime()
config = configuration(Config)
samples = np.arange(16384) / 512
amplitudes = np.arange(1, 69)
left = np.outer(amplitudes, np.sin(2 * np.pi * 12 * samples) + 0.35 * np.sin(2 * np.pi * 60 * samples))
right = np.outer(amplitudes, np.cos(2 * np.pi * 13 * samples) + 0.35 * np.sin(2 * np.pi * 60 * samples))
stim = np.zeros((1, 16384))
stim[0, [4096, 8192]] = 1
fixture = args.output / "synthetic_cho60.mat"
savemat(fixture, {"eeg": {"imagery_left": left, "imagery_right": right, "imagery_event": stim, "srate": 512}})
raw = local_raw(fixture, 1, Dataset, Annotator)
arrays = build_arrays(raw, config, collect, np)
legacy = build_arrays(raw, Config(**{**asdict(config), "notch_hz": 50.0}), collect, np)
frequencies = np.fft.rfftfreq(800, 1 / 200)
line = int(np.flatnonzero(frequencies == 60.0)[0])
window = np.hanning(800)
new_power = np.abs(np.fft.rfft(arrays["signals"].astype(np.float64) * window, axis=-1)) ** 2
old_power = np.abs(np.fft.rfft(legacy["signals"].astype(np.float64) * window, axis=-1)) ** 2
attenuation_db = float(10 * np.log10(float(np.median(old_power[..., line])) / float(np.median(new_power[..., line]))))
native_events, _ = mne.events_from_annotations(raw, event_id=EVENTS, regexp=None, verbose=False)
equal = compare_scaled(arrays, arrays, config, np)
zero = {name: np.zeros((1, 1, 1), dtype=np.float32) if name == "signals" else values[:1].copy() for name, values in arrays.items()}
below, above = dict(zero), dict(zero)
below["signals"] = np.full((1, 1, 1), 1e-9, dtype=np.float32)
above["signals"] = np.full((1, 1, 1), 1e-7, dtype=np.float32)
small = compare_scaled(zero, below, config, np)
large = compare_scaled(zero, above, config, np)
changed = dict(arrays)
changed["labels"] = arrays["labels"].copy()
changed["labels"][0] = "right_hand"
checks = [
    {"case": "frozen60Hz200Hz4second_original_reference_config", "passed": config.notch_hz == 60.0 and config.resample_hz == 200.0 and config.epoch_duration_s == 4.0 and config.reference == "original" and config.amplitude_unit_mv == 0.1},
    {"case": "local_cues_epoch_shape_and_channel_trial_schema", "passed": bool(np.array_equal(native_events[:, 0], [4096, 8192, 20980, 25076])) and arrays["signals"].shape == (4, 64, 800) and arrays["labels"].tolist() == ["left_hand", "left_hand", "right_hand", "right_hand"] and arrays["sessions"].tolist() == ["0"] * 4 and arrays["runs"].tolist() == ["0"] * 4 and arrays["trial_indices"].tolist() == [0, 1, 2, 3] and arrays["channel_names"][0] == "Fp1"},
    {"case": "frozen_amplitude_scaling_0point1mV", "passed": bool(np.array_equal(scale(np.asarray([1e-4, -1e-4]), amplitude_unit_mv=0.1), np.asarray([1, -1], dtype=np.float32)))},
    {"case": "stored_float32_exact_self_comparison", "passed": equal["passed"] and equal["signals"]["exact_equal"] and equal["signals"]["maximum_absolute_error_volts"] == equal["signals"]["maximum_absolute_error_amplitude_units"] == 0.0},
    {"case": "physical_volt_tolerance_and_identity_rejection", "passed": small["passed"] and not small["signals"]["exact_equal"] and not large["passed"] and bool(np.isclose(large["signals"]["maximum_absolute_error_volts"], 1e-11, rtol=1e-6, atol=1e-20)) and not compare_scaled(arrays, changed, config, np)["passed"]},
    {"case": "60Hz_notch_vs_synthetic_legacy50Hz_at_least6dB", "passed": bool(np.isfinite(attenuation_db)) and attenuation_db >= 6.0},
]
write_new(args.output / "probe_checks.json", {"checks": checks, "synthetic60Hz_attenuation_db": attenuation_db,
    "native_event_samples": native_events[:, 0].tolist(), "configuration": asdict(config), "synthetic_only": True})
if not all(row["passed"] for row in checks):
    raise ValueError("Cho60 synthetic filter/scaling/comparison qualification failed")
finish(args.output, plan, boundary, {"passed": True, "stage": "probe60_001", "probe_checks": checks,
    "synthetic_signal_shape": [4, 64, 800], "synthetic60Hz_attenuation_db": attenuation_db, "real_raw_files_decoded": 0,
    "real_cache_decoded": False, "signal_unit_volts": config.amplitude_unit_mv * 1e-3}, pools)
