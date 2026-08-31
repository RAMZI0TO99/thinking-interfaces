"""Run outstanding compute sequentially, resuming atomic records after interruption."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    jobs: list[list[str]] = [
        ["scripts/run_support_adaptation.py"],
        ["scripts/audit_support_adaptation.py"],
        ["scripts/audit_subject_falsification.py"],
    ]
    for dataset in ("cho2017", "mmidb"):
        for methods in (
            ("eegnet", "shallow", "deep", "ea_eegnet"),
            ("fbcsp", "tangent_lr", "ea_tangent_lr"),
        ):
            args = ["scripts/run_benchmark.py", "--dataset", dataset]
            for method in methods:
                args.extend(("--method", method))
            jobs.append(args)
    jobs.append(["scripts/audit_benchmark.py"])
    for job in jobs:
        print("Starting: " + " ".join(job), flush=True)
        subprocess.run([sys.executable, *job], cwd=root, check=True)
    print(
        "Compute and record-integrity audit complete; scientific review still required.", flush=True
    )


if __name__ == "__main__":
    main()
