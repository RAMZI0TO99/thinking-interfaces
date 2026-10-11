"""Frozen60Hz ProfileB collection and unit-aware comparison; no eager imports."""
EVENTS = {"left_hand": 1, "right_hand": 2}


def load_runtime():
    from cho_processing import load_runtime as qualified_cho_runtime
    np, mne, pools, _, _, savemat, Dataset, Annotator = qualified_cho_runtime()
    from data.profile_b import ProfileBConfig, collect_profile_b_runs, scale_to_amplitude_unit
    return np, mne, pools, ProfileBConfig, collect_profile_b_runs, scale_to_amplitude_unit, savemat, Dataset, Annotator


def configuration(Config):
    import tomllib
    from worker_common_004 import ROOT
    base = tomllib.loads((ROOT / "configs/base.toml").read_text(encoding="utf-8"))["preprocessing"]["profile_b"]
    document = tomllib.loads((ROOT / "configs/phase2/cho_profile_b_60hz.toml").read_text(encoding="utf-8"))
    expected = {"schema_version": 1, "dataset": "cho2017", "name": "profile_b_60hz_v1", "output_directory": "data/processed/cho2017/profile_b_60hz_v1"}
    if document["variant"] != expected or document["preprocessing"] != {**base, "notch_hz": 60.0}:
        raise ValueError("frozen60Hz variant differs from base ProfileB except notch")
    return Config(**document["preprocessing"])


def build_arrays(raw, config, collect, np):
    values = collect({"0": {"0": raw}}, EVENTS, config)
    from worker_common_004 import FIELDS
    return {name: np.asarray(value) if name == "channel_names" else value for name, value in zip(FIELDS, values, strict=True)}


def compare_scaled(cached, rebuilt, config, np):
    from worker_common_004 import compare_arrays
    result = compare_arrays(cached, rebuilt, np)
    signal = result["signals"]
    unit_volts = config.amplitude_unit_mv * 1e-3
    signal.update(stored_signal_unit="amplitude_unit", amplitude_unit_mv=config.amplitude_unit_mv, unit_volts=unit_volts,
        maximum_absolute_error_amplitude_units=signal["maximum_absolute_error_volts"],
        root_mean_square_error_amplitude_units=signal["root_mean_square_error_volts"])
    usable = signal["shape_equal"] and signal["finite_both"] and signal["float32_both"]
    if usable:
        left = cached["signals"].astype(np.float64)
        delta_volts = np.abs(left - rebuilt["signals"].astype(np.float64)) * unit_volts
        outside = int(np.count_nonzero(delta_volts > 1e-12 + 1e-6 * np.abs(left) * unit_volts))
        signal.update(maximum_absolute_error_volts=float(delta_volts.max()), root_mean_square_error_volts=float(np.sqrt(np.mean(delta_volts**2))),
            values_outside_tolerance=outside, within_tolerance=outside == 0)
    result["passed"] = signal["within_tolerance"] and all(all(row.values()) for row in result["identities"].values())
    return result
