"""Report remaining work using matching observed durations and honest unknowns."""

from __future__ import annotations

import json
from pathlib import Path

from core.config import load_toml
from evaluation.compute_estimate import benchmark_work_report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report = benchmark_work_report(root, load_toml(root / "configs" / "benchmark.toml"))
    output = root / "runs" / "benchmark_work_estimate.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
