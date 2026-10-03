"""Small synthetic checks for the complete Cho 60 Hz asset inventory."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from core.config import config_digest, load_toml
from evaluation.phase2_cho_60hz_inventory import load_cho_60hz_assets
from evaluation.phase2_protocol import TrialCatalog


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Cho60HzInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "data/processed/cho2017/profile_b_60hz_v1"
        self.output.mkdir(parents=True)
        self.config_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        self.config_file.parent.mkdir(parents=True)
        self.config_file.write_text(
            "[variant]\n"
            "schema_version = 1\n"
            'dataset = "cho2017"\n'
            'name = "profile_b_60hz_v1"\n'
            'output_directory = "data/processed/cho2017/profile_b_60hz_v1"\n'
            "[preprocessing]\nnotch_hz = 60.0\nresample_hz = 200.0\n",
            encoding="utf-8",
        )
        self.config_sha = sha(self.config_file.read_bytes())
        variant = load_toml(self.config_file)["variant"]
        preprocessing_sha = config_digest(load_toml(self.config_file)["preprocessing"])
        self.catalogs = []
        rows = []
        for index in range(1, 53):
            subject = f"subject_{index:02d}"
            a_sha = sha(f"profile-a-{subject}".encode())
            self.catalogs.append(TrialCatalog(
                dataset="cho2017", subject=subject,
                trial_ids=(f"{subject}-1", f"{subject}-2"),
                labels=("left_hand", "right_hand"),
                classes=("left_hand", "right_hand"),
                artifact_sha256=a_sha, preprocessing_sha256="a" * 64,
            ))
            artifact = self.output / f"{subject}.npz"
            artifact.write_bytes(f"synthetic-60hz-{subject}".encode())
            raw_sha = sha(f"raw-{subject}".encode())
            manifest_file = self.output / f"{subject}.manifest.json"
            manifest_file.write_text(json.dumps({
                "variant": variant,
                "variant_config_sha256": self.config_sha,
                "config_sha256": preprocessing_sha,
                "source_sha256": raw_sha,
            }), encoding="utf-8")
            rows.append({
                "subject": subject,
                "profile_a_sha256": a_sha,
                "variant_artifact_sha256": sha(artifact.read_bytes()),
                "variant_manifest_sha256": sha(manifest_file.read_bytes()),
                "raw_source_sha256": raw_sha,
                "binding_sha256": sha(f"binding-{subject}".encode()),
            })
        self.audit = {
            "schema_version": 1,
            "passed": True,
            "subject_count": 52,
            "scientific_cells_admitted": 0,
            "five_shot_episode_bindings_verified": 52,
            "all_52_versioned_pairs_pinned": True,
            "all_52_legacy_artifact_hashes_preserved": True,
            "all_52_profile_a_variant_trial_joins_verified": True,
            "all_52_raw_sources_verified_by_binding": True,
            "rows": rows,
        }
        self.audit_file = self.root / (
            "runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json"
        )
        self.audit_file.parent.mkdir(parents=True)
        self.save_audit()

    def save_audit(self) -> None:
        self.audit_file.write_text(json.dumps(self.audit), encoding="utf-8")
        self.audit_sha = sha(self.audit_file.read_bytes())

    def load(self):
        return load_cho_60hz_assets(
            self.root, self.catalogs,
            cohort_audit_sha256=self.audit_sha,
            variant_config_sha256=self.config_sha,
        )

    def test_complete_inventory_is_immutable(self) -> None:
        assets = self.load()
        self.assertEqual(len(assets), 52)
        self.assertEqual(assets["subject_01"].variant_config_sha256, self.config_sha)
        with self.assertRaises(TypeError):
            assets["subject_01"] = assets["subject_02"]  # type: ignore[index]

    def test_changed_or_missing_artifact_refuses(self) -> None:
        artifact = self.output / "subject_01.npz"
        artifact.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.load()
        artifact.unlink()
        with self.assertRaisesRegex(ValueError, "missing or unexpected"):
            self.load()

    def test_mixed_variant_refuses_even_with_updated_hash_pins(self) -> None:
        manifest_file = self.output / "subject_01.manifest.json"
        manifest = json.loads(manifest_file.read_text("utf-8"))
        manifest["variant"]["name"] = "historical_50hz"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        self.audit["rows"][0]["variant_manifest_sha256"] = sha(manifest_file.read_bytes())
        self.save_audit()
        with self.assertRaisesRegex(ValueError, "manifest provenance"):
            self.load()

    def test_wrong_catalog_and_receipt_pins_refuse(self) -> None:
        self.catalogs[0] = replace(self.catalogs[0], artifact_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "Profile A catalog"):
            self.load()
        self.catalogs[0] = replace(
            self.catalogs[0], artifact_sha256=self.audit["rows"][0]["profile_a_sha256"]
        )
        with self.assertRaisesRegex(ValueError, "audit bytes"):
            load_cho_60hz_assets(
                self.root, self.catalogs,
                cohort_audit_sha256="0" * 64,
                variant_config_sha256=self.config_sha,
            )


if __name__ == "__main__":
    unittest.main()
