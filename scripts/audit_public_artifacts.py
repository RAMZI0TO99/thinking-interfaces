from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import load_toml
from evaluation.artifact_audit import audit_epoch_artifact, write_audit


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "artifact_rejection.toml")
    )
    datasets = cast(Mapping[str, Any], config["datasets"])
    summary: dict[str, dict[str, int | bool]] = {}
    all_passed = True
    for dataset, raw_settings in datasets.items():
        settings = cast(Mapping[str, Any], raw_settings)
        directory = root / str(settings["artifact_directory"])
        paths = tuple(sorted(directory.glob("subject_*.npz")))
        expected = int(settings["expected_subjects"])
        if len(paths) != expected:
            raise SystemExit(f"{dataset} has {len(paths)} artifacts; expected {expected}")
        passed = 0
        for path in paths:
            audit = audit_epoch_artifact(path)
            write_audit(root / "runs" / "artifact_audits" / dataset / f"{path.stem}.json", audit)
            passed += int(audit.passed)
        dataset_passed = passed == expected
        all_passed = all_passed and dataset_passed
        summary[dataset] = {
            "subjects": len(paths),
            "passed": passed,
            "failed": len(paths) - passed,
            "complete": dataset_passed,
        }
    report = {"passed": all_passed, "datasets": summary}
    output = root / "runs" / "artifact_audit_status.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
