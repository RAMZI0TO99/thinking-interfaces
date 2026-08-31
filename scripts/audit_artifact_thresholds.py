from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import load_toml
from evaluation.artifact_thresholds import audit_threshold_directory


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "artifact_rejection.toml")
    )
    policy = cast(Mapping[str, Any], config["policy"])
    thresholds = cast(Mapping[str, Any], config["thresholds_volts"])
    datasets = cast(Mapping[str, Any], config["datasets"])
    audits = []
    for name, raw_settings in datasets.items():
        settings = cast(Mapping[str, Any], raw_settings)
        audits.append(
            audit_threshold_directory(
                root / str(settings["artifact_directory"]),
                dataset=name,
                threshold_volts=float(thresholds[name]),
                expected_subjects=int(settings["expected_subjects"]),
            ).as_dict()
        )
    report = {
        "frozen": bool(policy["frozen"]),
        "freeze_date": str(policy["freeze_date"]),
        "selection_rule": str(policy["selection_rule"]),
        "datasets": audits,
    }
    output = root / "runs" / "artifact_threshold_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
