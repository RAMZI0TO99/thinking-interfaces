from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from evaluation.leakage_ci import run_leakage_ci


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = run_leakage_ci(project_root)
    payload = {**asdict(report), "passed": report.passed}
    output = project_root / "runs" / "leakage_ci_status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not report.passed:
        print("Current-source leakage evidence is missing, stale or failed. "
              "Inspect with python -m scripts.refresh_source_bound_controls --check-only; "
              "run without --check-only to refresh the full 45-fit controls safely.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
