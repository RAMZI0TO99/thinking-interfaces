"""Run the structural leakage and quality audit for configured Profile A artifacts."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from evaluation.artifact_audit import audit_epoch_artifact, write_audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]
    failures = 0
    for subject_value in dataset["subjects"]:
        subject = int(subject_value)
        directory = ROOT / "data" / "processed" / "bci_iv_2a" / "profile_a"
        artifact = directory / f"subject_{subject:02d}.npz"
        audit = audit_epoch_artifact(artifact)
        output = write_audit(directory / f"subject_{subject:02d}.audit.json", audit)
        print(json.dumps({"audit": str(output), "result": audit.as_dict()}, indent=2))
        failures += int(not audit.passed)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

