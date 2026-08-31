"""Audit every pre-cue negative-control artifact."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from evaluation.artifact_audit import audit_epoch_artifact, write_audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]
    directory = ROOT / "data" / "processed" / "bci_iv_2a" / "pre_cue_control"
    failures = 0
    for subject_value in dataset["subjects"]:
        subject = int(subject_value)
        artifact = directory / f"subject_{subject:02d}.npz"
        audit = audit_epoch_artifact(artifact)
        expected = (
            audit.shape == (576, 22, 128)
            and audit.class_counts
            == {"left_hand": 144, "right_hand": 144, "feet": 144, "tongue": 144}
            and audit.session_counts == {"0train": 288, "1test": 288}
        )
        passed = audit.passed and expected
        output = write_audit(directory / f"subject_{subject:02d}.audit.json", audit)
        print(
            json.dumps(
                {"subject": subject, "audit": str(output), "passed": passed},
            ),
            flush=True,
        )
        failures += int(not passed)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
