"""Audit every BCI IV 2a Profile B artifact and manifest."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from evaluation.artifact_audit import audit_epoch_artifact, write_audit

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "configs" / "bci_iv_2a.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]
    directory = ROOT / "data" / "processed" / "bci_iv_2a" / "profile_b"
    failures = 0
    for subject_value in dataset["subjects"]:
        subject = int(subject_value)
        artifact = directory / f"subject_{subject:02d}.npz"
        manifest_path = directory / f"subject_{subject:02d}.manifest.json"
        audit = audit_epoch_artifact(artifact)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        structural_passed = bool(
            audit.finite
            and audit.provenance_unique
            and audit.exact_duplicate_groups == 0
            and audit.cross_session_duplicate_groups == 0
            and audit.zero_variance_trials == 0
            and audit.shape == (576, 22, 800)
            and audit.class_counts
            == {"left_hand": 144, "right_hand": 144, "feet": 144, "tongue": 144}
            and audit.session_counts == {"0train": 288, "1test": 288}
            and manifest["patch_samples"] == 200
            and manifest["patches_per_epoch"] == 4
            and manifest["fraction_within_unit_interval"] >= 0.95
        )
        output = write_audit(directory / f"subject_{subject:02d}.audit.json", audit)
        print(
            json.dumps(
                {
                    "subject": subject,
                    "audit": str(output),
                    "fraction_within_unit_interval": manifest[
                        "fraction_within_unit_interval"
                    ],
                    "passed": structural_passed,
                }
            ),
            flush=True,
        )
        failures += int(not structural_passed)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
