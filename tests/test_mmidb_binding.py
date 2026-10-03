from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.config import config_digest, load_toml
from evaluation.phase2_profile_binding import (
    MMIDB_CHANNELS,
    MMIDB_CLASSES,
    load_mmidb_profile_b_episode,
)
from evaluation.phase2_protocol import nested_episode
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog

TRIALS_PER_CLASS = 24


class MMIDBBindingTests(unittest.TestCase):
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
            directory = self.root / f"data/processed/mmidb/profile_{profile}"
            directory.mkdir(parents=True)
            self.paths[profile] = directory / "subject_001.npz"
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
                labels=np.array(MMIDB_CLASSES * TRIALS_PER_CLASS),
                sessions=np.array(["0"] * total),
                runs=np.array(
                    ["04"] * (total // 3) + ["08"] * (total // 3) + ["12"] * (total // 3)
                ),
                trial_indices=np.arange(total),
                channel_names=np.array(MMIDB_CHANNELS),
            )
            if profile == "b":
                cfg = copy.deepcopy(base["profile_b"])
                manifest = dict(
                    artifact_schema_version=1,
                    artifact_kind="profile_b",
                    subject=1,
                    shape=[total, 64, samples],
                    channel_names=list(MMIDB_CHANNELS),
                    epoch_duration_s=4.0,
                    sampling_rate_hz=200.0,
                    config_sha256=config_digest(cfg),
                    reference="original",
                    amplitude_unit_mv=0.1,
                    patch_samples=200,
                    patches_per_epoch=4,
                )
                self.paths["bm"] = directory / "subject_001.manifest.json"
                self.paths["bm"].write_text(json.dumps(manifest))
        np.savez(self.paths["a"], **self.arrays["a"])
        np.savez(self.paths["b"], **self.arrays["b"])
        threshold = load_toml(self.root / "configs/benchmark.toml")["datasets"][
            "mmidb"
        ]["artifact_threshold_volts"]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(self.root / "configs/benchmark.toml"),
            "dataset": "mmidb",
            "threshold": threshold,
        })
        catalog, _ = read_catalog(
            self.paths["a"], dataset="mmidb", classes=MMIDB_CLASSES,
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
        return load_mmidb_profile_b_episode(**arguments)

    def test_all_shot_levels_bind_support_and_fixed_queries(self):
        for shots in (1, 5, 10, 20):
            with self.subTest(shots=shots):
                bound = self.episode(shots)
                self.assertEqual(bound.support_signals.shape, (2 * shots, 64, 800))
                self.assertEqual(bound.query_signals.shape, (7, 64, 800))
                self.assertTrue(np.isfinite(bound.query_signals).all())
                self.assertEqual(bound.binding.schema, "mmidb-a-to-b-episode-v1")
                self.assertEqual(bound.binding.classes, MMIDB_CLASSES)
                self.assertEqual(bound.binding.channel_names, MMIDB_CHANNELS)
                self.assertEqual(
                    bound.binding.profile_b_resample_policy,
                    "upsample_to_target_before_filter_documented",
                )
                self.assertEqual(
                    bound.binding.query_trial_ids,
                    tuple(self.catalog.trial_ids[i]
                          for i in self.manifest.partition(shots).query_indices),
                )

    def test_repeat_binding_is_exact_and_inputs_unchanged(self):
        first = self.episode()
        second = self.episode()
        self.assertEqual(first.binding.sha256, second.binding.sha256)
        np.testing.assert_array_equal(first.query_signals, second.query_signals)
        self.assertEqual(file_digest(self.paths["a"]), self.catalog.artifact_sha256)

    def test_wrong_pins_and_records_refuse(self):
        for overrides in (
            {"episode_record": {"sha256": "0" * 64}},
            {"profile_b_artifact_sha256": "0" * 64},
            {"profile_b_manifest_sha256": "1" * 64},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.episode(**overrides)

    def test_content_tampering_refuses_at_the_content_layer(self):
        relabeled = dict(self.arrays["b"])
        relabeled["labels"] = np.array(
            ["feet"] + list(self.arrays["b"]["labels"][1:])
        )
        np.savez(self.paths["b"], **relabeled)
        self.hashes["b"] = file_digest(self.paths["b"])
        with self.assertRaisesRegex(ValueError, "class"):
            self.episode()
        np.savez(self.paths["b"], **self.arrays["b"])
        self.hashes["b"] = file_digest(self.paths["b"])
        self.paths["bm"].write_text(
            self.paths["bm"].read_text().replace('"subject": 1', '"subject": 2')
        )
        self.hashes["bm"] = file_digest(self.paths["bm"])
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.episode()

    def test_ineligible_subjects_cannot_construct(self):
        from dataclasses import replace

        with self.assertRaisesRegex(ValueError, "audited episodes|eligible"):
            load_mmidb_profile_b_episode(
                root=self.root,
                protocol_config=self.config,
                catalog=replace(self.catalog, subject="subject_079"),
                episode_record=self.record,
                shots_per_class=1,
                profile_b_artifact_sha256=self.hashes["b"],
                profile_b_manifest_sha256=self.hashes["bm"],
            )


if __name__ == "__main__":
    unittest.main()
