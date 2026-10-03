from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from adaptation.anchor_manifest import (
    BCIAnchorManifestRunner,
    EATangentAnchorSettings,
    EEGNetAnchorSettings,
)
from adaptation.ea_selection import BCIEATangentSelector, EATangentCandidate
from adaptation.source_selection import (
    BCIEEGNetSourceSelector,
    EEGNetCandidate,
    EEGNetSourceSettings,
)
from core.config import config_digest, load_toml
from evaluation.phase2_cho_profile_a import load_cho_profile_a_subject
from evaluation.phase2_profile_binding import CHO_CHANNELS, CHO_CLASSES
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog

TRIALS_PER_CLASS = 24


class AnchorChoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd() / "tmp")
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        ceiling = self.root / "configs/phase2"
        ceiling.mkdir(parents=True, exist_ok=True)
        (ceiling / "selection_ceiling.toml").write_bytes(
            Path("configs/phase2/selection_ceiling.toml").read_bytes()
        )
        for name in ("base.toml", "benchmark.toml"):
            (self.root / "configs" / name).write_bytes((Path("configs") / name).read_bytes())
        self.config = json.loads(json.dumps(load_toml("configs/phase2/protocol.toml")))
        self.config["datasets"]["cho2017"]["expected_subjects"] = 3
        generator = np.random.default_rng(23)
        self.catalogs = []
        for subject in (1, 2, 3):
            name = f"subject_{subject:02d}"
            directory = self.root / "data/processed/cho2017/profile_a"
            directory.mkdir(parents=True, exist_ok=True)
            total = 2 * TRIALS_PER_CLASS
            signals = generator.normal(size=(total, 64, 512)).astype(np.float32) * 1e-8
            signals[0] = 1  # One threshold-rejected trial.
            np.savez(
                directory / f"{name}.npz",
                signals=signals,
                labels=np.array(CHO_CLASSES * TRIALS_PER_CLASS),
                sessions=np.array(["s"] * total),
                runs=np.array(["r"] * total),
                trial_indices=np.arange(total),
                channel_names=np.array(CHO_CHANNELS),
            )
        threshold = load_toml(self.root / "configs/benchmark.toml")["datasets"]["cho2017"][
            "artifact_threshold_volts"
        ]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(self.root / "configs/benchmark.toml"),
            "dataset": "cho2017", "threshold": threshold,
        })
        self.records = {}
        for subject in (1, 2, 3):
            name = f"subject_{subject:02d}"
            path = self.root / f"data/processed/cho2017/profile_a/{name}.npz"
            catalog, _ = read_catalog(
                path, dataset="cho2017", classes=CHO_CLASSES, threshold=threshold,
                preprocessing_sha256=preprocessing,
            )
            self.catalogs.append(catalog)
            self.records[name] = envelope(
                "episode_manifest",
                nested_episode(
                    catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
                ).payload(),
            )
        self.catalogs = tuple(self.catalogs)
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))

    def tearDown(self):
        self.temp.cleanup()

    def test_cho_profile_a_hashes_the_buffer_it_parses(self):
        target = self.root / "data/processed/cho2017/profile_a/subject_01.npz"
        original_read_bytes = Path.read_bytes

        def substituted_read_bytes(path):
            if path == target:
                return b"different Profile A bytes while the pinned file is unchanged"
            return original_read_bytes(path)

        with (
            patch.object(Path, "read_bytes", substituted_read_bytes),
            self.assertRaisesRegex(ValueError, "Profile A parse buffer differs"),
        ):
            load_cho_profile_a_subject(self.root, self.config, self.catalogs[0])

    def test_ea_tangent_anchor_predicts_cho_two_class_target(self):
        runner = BCIAnchorManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, {},
            outer_target="subject_01",
        )
        result = runner.predict_target(
            self.records["subject_01"], shots_per_class=1,
            settings=EATangentAnchorSettings(1e-6, 1.0, 1000, 2),
        )
        self.assertEqual(result.probabilities.shape, (7, 2))
        self.assertTrue(np.isfinite(result.probabilities).all())
        self.assertEqual(result.source_subjects, ("subject_02", "subject_03"))
        self.assertEqual(result.classes, CHO_CLASSES)

    def test_eegnet_anchor_predicts_with_a_sixty_four_channel_model(self):
        from braindecode.models import EEGNet

        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            model = EEGNet(
                n_chans=64, n_outputs=2, n_times=512, sfreq=128,
                final_layer_with_constraint=True,
            ).eval()
        runner = BCIAnchorManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, {},
            outer_target="subject_01", eegnet_source=model,
            validation_subject="subject_02",
        )
        result = runner.predict_validation(
            self.records["subject_02"], shots_per_class=1,
            settings=EEGNetAnchorSettings(1, 0.001, 1e6, 2),
        )
        self.assertEqual(result.role, "inner_validation")
        self.assertEqual(result.probabilities.shape, (7, 2))

    def test_selectors_run_single_cho_folds(self):
        eegnet = BCIEEGNetSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, {},
            outer_target="subject_01",
            candidates=(EEGNetCandidate(
                "eegnet_cho", EEGNetSourceSettings(1, 4, 0.001, 1e6),
                EEGNetAnchorSettings(1, 0.001, 1e6, 2)),),
            seed=23, shots_per_class=1, maximum_gradient_steps=64,
        )
        evidence = eegnet.run_fold(candidate_name="eegnet_cho", validation_subject="subject_02")
        fold = evidence.record["payload"]["folds"][0]
        self.assertEqual(len(fold["source_fit"]["steps"]), 1)  # Validation excluded.
        self.assertEqual(len(fold["query_trial_ids"]), 7)
        ea = BCIEATangentSelector(
            self.root, self.config, self.catalogs, self.selection_record, {},
            outer_target="subject_01",
            candidates=(EATangentCandidate("ea_cho", EATangentAnchorSettings(1e-6, 1.0, 1000, 2)),),
            shots_per_class=1, maximum_classical_fits=8,
        )
        ea_evidence = ea.run_fold(candidate_name="ea_cho", validation_subject="subject_02")
        ea_fold = ea_evidence.record["payload"]["folds"][0]
        matrix = ea_fold["confusion_matrix"]
        self.assertEqual(len(matrix), 2)
        self.assertEqual(ea_fold["anchor_fit"]["covariance"], "oas")
        with self.assertRaisesRegex(ValueError, "sidecar manifests"):
            BCIEEGNetSourceSelector(
                self.root, self.config, self.catalogs, self.selection_record,
                {"subject_01": "0" * 64},
                outer_target="subject_01",
                candidates=(EEGNetCandidate(
                    "eegnet_cho", EEGNetSourceSettings(1, 4, 0.001, 1e6),
                    EEGNetAnchorSettings(1, 0.001, 1e6, 2)),),
                seed=23, shots_per_class=1, maximum_gradient_steps=64,
            )


if __name__ == "__main__":
    unittest.main()
