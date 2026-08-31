from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from core.config import load_toml


def directory_inventory(path: Path) -> dict[str, int | float | str | None]:
    files = tuple(item for item in path.rglob("*") if item.is_file())
    timestamps = tuple(item.stat().st_mtime for item in files)
    return {
        "directory": str(path.resolve()),
        "files": len(files),
        "bytes": sum(item.stat().st_size for item in files),
        "gibibytes": sum(item.stat().st_size for item in files) / (1024**3),
        "first_modified_utc": (
            datetime.fromtimestamp(min(timestamps), UTC).isoformat() if timestamps else None
        ),
        "last_modified_utc": (
            datetime.fromtimestamp(max(timestamps), UTC).isoformat() if timestamps else None
        ),
        "observed_acquisition_span_seconds": (
            max(timestamps) - min(timestamps) if timestamps else 0.0
        ),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    config = cast(
        Mapping[str, Any], load_toml(root / "configs" / "dataset_inventory.toml")
    )
    datasets = cast(Mapping[str, Any], config["datasets"])
    report: dict[str, object] = {}
    complete = True
    for dataset, raw_settings in datasets.items():
        settings = cast(Mapping[str, Any], raw_settings)
        processed = root / str(settings["processed_directory"])
        subjects = len(tuple(processed.glob("subject_*.npz")))
        expected = int(settings["expected_subjects"])
        dataset_complete = subjects == expected
        complete = complete and dataset_complete
        report[dataset] = {
            "subjects": subjects,
            "expected_subjects": expected,
            "complete": dataset_complete,
            "raw": directory_inventory(root / str(settings["raw_directory"])),
            "processed": directory_inventory(processed),
        }
    payload = {"complete": complete, "datasets": report}
    output = root / "runs" / "dataset_inventory.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
