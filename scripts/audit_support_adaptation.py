from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from core.config import config_digest, load_toml
from evaluation.support_adaptation_audit import audit_support_adaptation


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    settings = cast(
        Mapping[str, Any], load_toml(root / "configs" / "eegnet_support_adaptation.toml")
    )
    benchmark = cast(Mapping[str, Any], load_toml(root / "configs" / "benchmark.toml"))
    dataset = str(settings["episode"]["dataset"])
    directory = root / benchmark["datasets"][dataset]["artifact_directory"]
    report = audit_support_adaptation(
        root / "runs" / "support_adaptation" / dataset,
        settings=settings,
        subjects=tuple(path.stem for path in sorted(directory.glob("subject_*.npz"))),
        benchmark_sha256=config_digest(benchmark),
    )
    output = root / "runs" / "support_adaptation_status.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
