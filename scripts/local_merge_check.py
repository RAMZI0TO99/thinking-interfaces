"""Fail-closed local commit/merge checks; not remote branch protection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from core.provenance import source_files


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = [path.relative_to(root).as_posix() for path in source_files(root)]
    subprocess.run(["git", "diff", "--exit-code", "--", *sources], cwd=root, check=True)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *sources],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    if untracked.stdout.strip():
        raise SystemExit("Stage all intended source changes before the checked commit.")
    for script in ("scripts/verify_phase1_quality.py", "scripts/ci_phase1.py"):
        subprocess.run([sys.executable, script], cwd=root, check=True)
    print("Local source quality and three Phase I leakage checks passed.", flush=True)


if __name__ == "__main__":
    main()
