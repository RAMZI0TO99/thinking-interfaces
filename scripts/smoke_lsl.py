from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np

from core.config import load_toml
from realtime.lsl import run_lsl_loopback


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(Mapping[str, Any], load_toml(root / "configs" / "lsl.toml"))
    loopback = cast(Mapping[str, Any], config["loopback"])
    seconds = float(loopback["seconds"])
    sampling_rate = float(loopback["sampling_rate_hz"])
    channels = tuple(cast(list[str], loopback["channels"]))
    frequencies = tuple(float(value) for value in cast(list[float], loopback["frequencies_hz"]))
    if len(channels) != len(frequencies):
        raise ValueError("loopback channels and frequencies must have the same length")
    samples = round(seconds * sampling_rate)
    positions = np.arange(samples) / sampling_rate
    signal = np.vstack(
        [np.sin(positions * 2 * np.pi * frequency) for frequency in frequencies]
    ).astype(np.float32)
    result = run_lsl_loopback(
        signal,
        channels,
        sampling_rate,
        timeout_s=float(loopback["timeout_seconds"]),
    )
    payload = asdict(result)
    payload["maximum_allowed_drift_s"] = float(
        loopback["maximum_startup_inclusive_drift_seconds"]
    )
    payload["passed"] = abs(result.drift_s) <= payload["maximum_allowed_drift_s"]
    output = root / "runs" / "lsl_loopback_60s.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
