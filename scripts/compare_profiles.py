from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np

from core.config import load_toml
from encoder.eegnet_baseline import train_eegnet


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = cast(
        Mapping[str, Any], load_toml(project_root / "configs" / "profile_comparison.toml")
    )
    shared = cast(Mapping[str, Any], config["comparison"])
    results: dict[str, object] = {}
    for profile in ("profile_a", "profile_b"):
        settings = cast(Mapping[str, Any], config[profile])
        with np.load(project_root / str(settings["artifact"])) as artifact:
            result, _ = train_eegnet(
                signals=np.asarray(artifact["signals"], dtype=np.float32),
                labels=np.asarray(artifact["labels"], dtype=np.str_),
                sessions=np.asarray(artifact["sessions"], dtype=np.str_),
                train_session=str(shared["train_session"]),
                test_session=str(shared["test_session"]),
                sampling_rate_hz=float(settings["sampling_rate_hz"]),
                epochs=int(shared["epochs"]),
                batch_size=int(shared["batch_size"]),
                learning_rate=float(shared["learning_rate"]),
                weight_decay=float(shared["weight_decay"]),
                validation_fraction=float(shared["validation_fraction"]),
                early_stopping_patience=int(shared["early_stopping_patience"]),
                input_scale=float(settings["input_scale"]),
                seed=int(shared["seed"]),
            )
            results[profile] = {
                "balanced_accuracy": result.report.balanced_accuracy,
                "cohen_kappa": result.report.cohen_kappa,
                "best_epoch": result.best_epoch,
                "signal_shape": list(artifact["signals"].shape),
                "signal_standard_deviation": float(artifact["signals"].std()),
            }
    profile_a = cast(Mapping[str, Any], results["profile_a"])
    profile_b = cast(Mapping[str, Any], results["profile_b"])
    results["profile_b_minus_a_balanced_accuracy"] = float(
        profile_b["balanced_accuracy"]
    ) - float(profile_a["balanced_accuracy"])
    output = project_root / "runs" / "profile_comparison.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
