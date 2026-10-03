"""Small, disk-only checks for persisted Cho target input declarations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import tomllib
import unittest
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import cast
from unittest.mock import patch

from core.config import config_digest
from evaluation import phase2_cho_persisted_target as target_module
from evaluation.phase2_cho_case_inputs import CHO_SUBJECTS, ChoFirstTrancheRoute
from evaluation.phase2_cho_persisted_target import (
    ChoPersistedTargetDeclarations,
    verify_cho_persisted_target_declarations,
)
from evaluation.phase2_profile_binding import CHO_CLASSES, ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class PersistedTargetDeclarationTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        project = Path(__file__).resolve().parents[1]
        for relative in ("configs/base.toml", "configs/phase2/cho_profile_b_60hz.toml"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project / relative, destination)
        self.base_sha256 = _digest((self.root / "configs/base.toml").read_bytes())
        variant_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        self.variant_sha256 = _digest(variant_file.read_bytes())
        variant = tomllib.loads(variant_file.read_text("utf-8"))
        self.variant_identity = variant["variant"]
        self.preprocessing_sha256 = config_digest(variant["preprocessing"])
        self.sources = {
            subject: (
                f"data/raw/moabb/cho2017/subject_{index:02d}.mat",
                _digest(subject.encode("utf-8")),
            )
            for index, subject in enumerate(CHO_SUBJECTS, 1)
        }
        assets: dict[str, ChoProfileAssets60Hz] = {}
        catalogs: list[TrialCatalog] = []
        for index, subject in enumerate(CHO_SUBJECTS, 1):
            source_file, source_sha256 = self.sources[subject]
            manifest = {
                "subject": index,
                "variant": self.variant_identity,
                "variant_config_sha256": self.variant_sha256,
                "config_sha256": self.preprocessing_sha256,
                "source_file": source_file,
                "source_sha256": source_sha256,
            }
            path = self._manifest_path(subject)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            assets[subject] = ChoProfileAssets60Hz(
                _digest(f"artifact-{subject}".encode()),
                _digest(path.read_bytes()),
                self.variant_sha256,
            )
            catalogs.append(TrialCatalog(
                "cho2017", subject, ("left", "right"), CHO_CLASSES,
                CHO_CLASSES, _digest(f"catalog-{subject}".encode()),
                _digest(b"preprocessing"),
            ))
        self.route = ChoFirstTrancheRoute(
            (), tuple(catalogs), MappingProxyType(assets), "{}",
            MappingProxyType({}), MappingProxyType({}),
        )

    def _manifest_path(self, subject: str) -> Path:
        return self.root / (
            f"data/processed/cho2017/profile_b_60hz_v1/{subject}.manifest.json"
        )

    def _repin_manifest(self, name: str, **changes: object) -> None:
        path = self._manifest_path(name)
        manifest = json.loads(path.read_text("utf-8"))
        manifest.update(changes)
        path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        assets = dict(self.route.labram_assets)
        assets[name] = replace(
            assets[name], profile_b_manifest_sha256=_digest(path.read_bytes()),
        )
        self.route = replace(self.route, labram_assets=MappingProxyType(assets))

    def _verify(self) -> ChoPersistedTargetDeclarations:
        return verify_cho_persisted_target_declarations(
            self.root, self.route, base_config_sha256=self.base_sha256,
        )

    def test_exact_pinned_buffers_return_immutable_52_subject_declarations(self) -> None:
        result = self._verify()
        self.assertEqual(result.base_config_sha256, self.base_sha256)
        self.assertEqual(result.profile_b_config_sha256, self.preprocessing_sha256)
        self.assertEqual(dict(result.source_by_subject), self.sources)
        with self.assertRaises(TypeError):
            cast(dict[str, tuple[str, str]], result.source_by_subject)["subject_01"] = (
                "changed", "0" * 64,
            )

    def test_wrong_base_pin_and_changed_variant_refuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "base config.*pin"):
            verify_cho_persisted_target_declarations(
                self.root, self.route, base_config_sha256="0" * 64,
            )
        variant_path = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        variant_path.write_text(
            variant_path.read_text("utf-8").replace("notch_hz = 60.0", "notch_hz = 50.0"),
            encoding="utf-8",
        )
        variant_sha256 = _digest(variant_path.read_bytes())
        assets = {
            subject: replace(asset, variant_config_sha256=variant_sha256)
            for subject, asset in self.route.labram_assets.items()
        }
        self.route = replace(self.route, labram_assets=MappingProxyType(assets))
        with self.assertRaisesRegex(ValueError, "60 Hz variant identity or preprocessing"):
            self._verify()

    def test_manifest_pin_subject_and_source_namespace_refuse(self) -> None:
        subject = "subject_01"
        path = self._manifest_path(subject)
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "manifest subject_01.*pin"):
            self._verify()
        self._repin_manifest(subject, subject=2)
        with self.assertRaisesRegex(ValueError, "manifest variant or config"):
            self._verify()
        self._repin_manifest(subject, subject=1, source_file="data/raw/moabb/cho2017/../other.mat")
        with self.assertRaisesRegex(ValueError, "source path escapes"):
            self._verify()
        self._repin_manifest(subject, source_file=self.sources[subject][0], source_sha256="bad")
        with self.assertRaisesRegex(ValueError, "digest"):
            self._verify()

    def test_manifest_alias_refuses_when_symlink_available(self) -> None:
        subject = "subject_01"
        path = self._manifest_path(subject)
        backing = path.with_name("subject_01.backing.json")
        path.rename(backing)
        try:
            os.symlink(backing, path)
        except OSError as error:
            self.skipTest(f"symlink unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "aliases"):
            self._verify()

    def test_manifest_changed_after_first_read_refuses(self) -> None:
        original = target_module._pinned_bytes
        first = self._manifest_path("subject_01")

        def change_during_read(path: Path, digest: str, limit: int, name: str) -> bytes:
            raw = original(path, digest, limit, name)
            if name == "Cho B manifest subject_52":
                first.write_bytes(first.read_bytes() + b" ")
            return raw

        with (
            patch.object(target_module, "_pinned_bytes", side_effect=change_during_read),
            self.assertRaisesRegex(ValueError, "manifest subject_01.*pin"),
        ):
            self._verify()


if __name__ == "__main__":
    unittest.main()
