from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from core.config import config_digest, load_toml
from evaluation.phase2_profile_binding import (
    BCI_CLASSES,
    CHO_CHANNELS,
    CHO_CLASSES,
    ChoProfileBinding60Hz,
    load_cho_profile_b_episode,
)
from evaluation.phase2_protocol import nested_episode
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog

TRIALS_PER_CLASS = 24


class ChoBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        for name in ("base.toml", "benchmark.toml"):
            (self.root / "configs" / name).write_bytes((Path("configs") / name).read_bytes())
        self.config = load_toml("configs/phase2/protocol.toml")
        self.paths = {}
        self.arrays = {}
        base = load_toml("configs/base.toml")["preprocessing"]
        total = 2 * TRIALS_PER_CLASS
        for profile, samples in (("a", 512), ("b", 800)):
            directory = self.root / f"data/processed/cho2017/profile_{profile}"
            directory.mkdir(parents=True)
            self.paths[profile] = directory / "subject_01.npz"
            signals = np.broadcast_to(
                np.arange(total, dtype=np.float32)[:, None, None], (total, 64, samples)
            ).copy()
            if profile == "a":
                signals *= 1e-8
                signals[0] = 1  # Reject one original trial before constructing the catalog.
            else:
                signals = signals / 100 + 1
            self.arrays[profile] = dict(
                signals=signals,
                labels=np.array(CHO_CLASSES * TRIALS_PER_CLASS),
                sessions=np.array(["session"] * total),
                runs=np.array(["run"] * total),
                trial_indices=np.arange(total),
                channel_names=np.array(CHO_CHANNELS),
            )
            if profile == "b":
                cfg = copy.deepcopy(base["profile_b"])
                manifest = dict(
                    artifact_schema_version=1,
                    artifact_kind="profile_b",
                    subject=1,
                    shape=[total, 64, samples],
                    channel_names=list(CHO_CHANNELS),
                    epoch_duration_s=4.0,
                    sampling_rate_hz=200.0,
                    config_sha256=config_digest(cfg),
                    reference="original",
                    amplitude_unit_mv=0.1,
                    patch_samples=200,
                    patches_per_epoch=4,
                )
                self.paths["bm"] = directory / "subject_01.manifest.json"
                self.paths["bm"].write_text(json.dumps(manifest))
        np.savez(self.paths["a"], **self.arrays["a"])
        np.savez(self.paths["b"], **self.arrays["b"])
        threshold = load_toml(self.root / "configs/benchmark.toml")["datasets"][
            "cho2017"
        ]["artifact_threshold_volts"]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(self.root / "configs/benchmark.toml"),
            "dataset": "cho2017",
            "threshold": threshold,
        })
        catalog, _ = read_catalog(
            self.paths["a"], dataset="cho2017", classes=CHO_CLASSES,
            threshold=threshold, preprocessing_sha256=preprocessing,
        )
        self.catalog = catalog
        self.manifest = nested_episode(
            catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
        )
        self.record = envelope("episode_manifest", self.manifest.payload())
        self.hashes = {
            "b": file_digest(self.paths["b"]),
            "bm": file_digest(self.paths["bm"]),
        }

    def tearDown(self):
        self.temp.cleanup()

    def episode(self, shots=1, **overrides):
        arguments = dict(
            root=self.root,
            protocol_config=self.config,
            catalog=self.catalog,
            episode_record=self.record,
            shots_per_class=shots,
            profile_b_artifact_sha256=self.hashes["b"],
            profile_b_manifest_sha256=self.hashes["bm"],
        )
        arguments.update(overrides)
        return load_cho_profile_b_episode(**arguments)

    def make_60hz_variant(self):
        config_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        config_file.parent.mkdir(parents=True)
        shutil.copyfile(Path("configs/phase2/cho_profile_b_60hz.toml"), config_file)
        variant = load_toml(config_file)
        directory = self.root / variant["variant"]["output_directory"]
        directory.mkdir(parents=True)
        artifact = directory / "subject_01.npz"
        np.savez(artifact, **self.arrays["b"])
        raw_file = self.root / "data/raw/moabb/cho2017/synthetic_subject_01.mat"
        raw_file.parent.mkdir(parents=True)
        raw_file.write_bytes(b"synthetic Cho source")
        manifest = json.loads(self.paths["bm"].read_text(encoding="utf-8"))
        manifest.update({
            "config_sha256": config_digest(variant["preprocessing"]),
            "variant": variant["variant"],
            "variant_config_sha256": file_digest(config_file),
            "source_file": raw_file.relative_to(self.root).as_posix(),
            "source_sha256": file_digest(raw_file),
        })
        manifest_file = directory / "subject_01.manifest.json"
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        return config_file, artifact, manifest_file

    def test_all_shot_levels_bind_support_and_fixed_queries(self):
        for shots in (1, 5, 10, 20):
            with self.subTest(shots=shots):
                bound = self.episode(shots)
                self.assertEqual(bound.support_signals.shape, (2 * shots, 64, 800))
                self.assertEqual(bound.support_labels.shape, (2 * shots,))
                self.assertEqual(bound.query_signals.shape, (7, 64, 800))
                self.assertTrue(np.isfinite(bound.query_signals).all())
                self.assertEqual(bound.binding.schema, "cho-a-to-b-episode-v1")
                self.assertEqual(bound.binding.classes, CHO_CLASSES)
                self.assertEqual(bound.binding.channel_names, CHO_CHANNELS)
                self.assertEqual(
                    bound.binding.profile_a_sidecar_manifests,
                    "absent_cho_identity_is_the_audited_catalog_hash",
                )
                self.assertEqual(
                    bound.binding.query_trial_ids,
                    tuple(self.catalog.trial_ids[i]
                          for i in self.manifest.partition(shots).query_indices),
                )
                self.assertEqual(
                    bound.binding.profile_b_artifact_sha256, self.hashes["b"]
                )
                self.assertTrue(set(bound.query_labels.tolist()) <= {0, 1})

    def test_repeat_binding_is_exact_and_inputs_unchanged(self):
        first = self.episode()
        second = self.episode()
        self.assertEqual(first.binding.sha256, second.binding.sha256)
        np.testing.assert_array_equal(first.query_signals, second.query_signals)
        np.testing.assert_array_equal(first.support_signals, second.support_signals)
        self.assertEqual(file_digest(self.paths["a"]), self.catalog.artifact_sha256)
        self.assertEqual(file_digest(self.paths["b"]), self.hashes["b"])

    def test_60hz_binding_is_versioned_and_legacy_binding_stays_stable(self):
        legacy = self.episode()
        config_file, artifact, manifest_file = self.make_60hz_variant()
        bound = self.episode(
            profile_b_artifact_sha256=file_digest(artifact),
            profile_b_manifest_sha256=file_digest(manifest_file),
            variant_config_sha256=file_digest(config_file),
        )
        self.assertIsInstance(bound.binding, ChoProfileBinding60Hz)
        self.assertEqual(bound.binding.schema, "cho-a-to-b-episode-60hz-v1")
        self.assertEqual(
            bound.binding.profile_b_config_sha256,
            config_digest(load_toml(config_file)["preprocessing"]),
        )
        self.assertEqual(bound.binding.variant_config_sha256, file_digest(config_file))
        self.assertEqual(bound.binding.source_file,
                         "data/raw/moabb/cho2017/synthetic_subject_01.mat")
        self.assertNotEqual(bound.binding.sha256, legacy.binding.sha256)
        self.assertEqual(self.episode().binding.sha256, legacy.binding.sha256)
        np.testing.assert_array_equal(bound.support_signals, legacy.support_signals)

    def test_60hz_binding_refuses_legacy_manifest_and_wrong_variant(self):
        config_file, artifact, manifest_file = self.make_60hz_variant()
        arguments = dict(
            profile_b_artifact_sha256=file_digest(artifact),
            variant_config_sha256=file_digest(config_file),
        )
        original = manifest_file.read_bytes()
        manifest_file.write_bytes(self.paths["bm"].read_bytes())
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.episode(profile_b_manifest_sha256=file_digest(manifest_file), **arguments)
        manifest_file.write_bytes(original)
        tampered = json.loads(original)
        tampered["variant"]["name"] = "profile_b_50hz"
        manifest_file.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "variant"):
            self.episode(profile_b_manifest_sha256=file_digest(manifest_file), **arguments)
        manifest_file.write_bytes(original)
        tampered = json.loads(original)
        tampered["source_file"] = "data/raw/moabb/cho2017/../../outside.mat"
        manifest_file.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source file"):
            self.episode(profile_b_manifest_sha256=file_digest(manifest_file), **arguments)
        manifest_file.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "pinned variant bytes"):
            self.episode(profile_b_manifest_sha256=file_digest(manifest_file),
                         variant_config_sha256="0" * 64,
                         profile_b_artifact_sha256=file_digest(artifact))

    def test_60hz_binding_refuses_changed_raw_source(self):
        config_file, artifact, manifest_file = self.make_60hz_variant()
        raw_file = self.root / json.loads(manifest_file.read_text())["source_file"]
        raw_file.write_bytes(b"raw source changed after artifact generation")
        with self.assertRaisesRegex(ValueError, "raw source bytes changed"):
            self.episode(
                profile_b_artifact_sha256=file_digest(artifact),
                profile_b_manifest_sha256=file_digest(manifest_file),
                variant_config_sha256=file_digest(config_file),
            )

    def test_60hz_binding_hashes_the_buffers_it_parses(self):
        config_file, artifact, manifest_file = self.make_60hz_variant()
        arguments = dict(
            profile_b_artifact_sha256=file_digest(artifact),
            profile_b_manifest_sha256=file_digest(manifest_file),
            variant_config_sha256=file_digest(config_file),
        )
        original_read_bytes = Path.read_bytes
        for target, expected_name in ((artifact, "artifact"), (manifest_file, "bm")):
            with self.subTest(target=target):
                def substituted_read_bytes(path, target_path=target):
                    if path == target_path:
                        return b"different bytes while the pinned path is unchanged"
                    return original_read_bytes(path)

                with (
                    patch.object(Path, "read_bytes", substituted_read_bytes),
                    self.assertRaisesRegex(
                        ValueError, f"pinned {expected_name} bytes changed during load",
                    ),
                ):
                    self.episode(**arguments)

    def test_60hz_binding_refuses_link_to_legacy_directory(self):
        config_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        config_file.parent.mkdir(parents=True)
        shutil.copyfile(Path("configs/phase2/cho_profile_b_60hz.toml"), config_file)
        legacy = self.root / "data/processed/cho2017/profile_b"
        variant = legacy.parent / "profile_b_60hz_v1"
        try:
            variant.symlink_to(legacy, target_is_directory=True)
        except OSError as error:
            if os.name != "nt":
                self.skipTest(f"directory links unavailable: {error}")
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(variant), str(legacy)],
                capture_output=True, check=False,
            )
            if result.returncode:
                self.skipTest(f"directory links unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "output aliases"):
            self.episode(variant_config_sha256=file_digest(config_file))

    def test_wrong_catalogs_and_records_refuse_before_reading(self):
        for overrides in (
            {"episode_record": {"sha256": "0" * 64}},
            {"profile_b_artifact_sha256": "0" * 64},
            {"profile_b_manifest_sha256": "1" * 64},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.episode(**overrides)
        from dataclasses import replace

        with self.assertRaises(ValueError):
            load_cho_profile_b_episode(
                root=self.root,
                protocol_config=self.config,
                catalog=replace(self.catalog, dataset="bci_iv_2a"),
                episode_record=self.record,
                shots_per_class=1,
                profile_b_artifact_sha256=self.hashes["b"],
                profile_b_manifest_sha256=self.hashes["bm"],
            )

    def test_identity_label_or_manifest_tampering_refuses(self):
        relabeled = dict(self.arrays["b"])
        relabeled["labels"] = np.array(
            [BCI_CLASSES[0]] + list(self.arrays["b"]["labels"][1:])
        )
        np.savez(self.paths["b"], **relabeled)
        # Refresh the pinned digest so the content validation, not the hash
        # guard, is the refusing layer under test.
        self.hashes["b"] = file_digest(self.paths["b"])
        with self.assertRaisesRegex(ValueError, "class"):
            self.episode()
        np.savez(self.paths["b"], **self.arrays["b"])
        shifted = dict(self.arrays["b"])
        shifted["trial_indices"] = np.roll(shifted["trial_indices"], 1)
        np.savez(self.paths["b"], **shifted)
        self.hashes["b"] = file_digest(self.paths["b"])
        with self.assertRaises(ValueError):
            self.episode()
        np.savez(self.paths["b"], **self.arrays["b"])
        self.hashes["b"] = file_digest(self.paths["b"])
        self.paths["bm"].write_text(
            self.paths["bm"].read_text().replace('"subject": 1', '"subject": 2')
        )
        self.hashes["bm"] = file_digest(self.paths["bm"])
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.episode()


if __name__ == "__main__":
    unittest.main()
