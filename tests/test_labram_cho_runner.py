from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np
import torch
from braindecode.models import Labram

from adaptation.labram_manifest import LaBraMTuningManifestRunner, LaBraMTuningSettings
from adaptation.labram_prompt_trained import (
    PromptContinuationSettings,
    TrainedPromptManifestRunner,
)
from adaptation.labram_source import (
    BCILaBraMSourceSelector,
    LaBraMSourceCandidate,
    LaBraMSourceSettings,
)
from core.config import config_digest, load_toml
from evaluation.labram_parity import state_digest
from evaluation.phase2_profile_binding import CHO_CHANNELS as MONTAGE
from evaluation.phase2_profile_binding import (
    CHO_CLASSES,
    ChoProfileAssets,
    ChoProfileAssets60Hz,
    ChoProfileBinding60Hz,
)
from evaluation.phase2_protocol import nested_episode, source_selection
from evaluation.phase2_records import envelope
from scripts.audit_phase2_protocol import file_digest, read_catalog

CHO_CLASSES_TUPLE = CHO_CLASSES
TRIALS_PER_CLASS = 24
SUPPORT_SETTINGS = LaBraMTuningSettings("linear", 1, 0.01, None, 4)


class ChoRunnerTests(unittest.TestCase):
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
        self.config = load_toml("configs/phase2/protocol.toml")
        # A three-subject Cho cohort declared for this fixture world.
        self.config = json.loads(json.dumps(self.config))
        self.config["datasets"]["cho2017"]["expected_subjects"] = 3
        base = load_toml("configs/base.toml")["preprocessing"]
        self.catalogs, self.assets, self.records = [], {}, {}
        generator = np.random.default_rng(23)
        for subject in (1, 2, 3):
            name = f"subject_{subject:02d}"
            total = 2 * TRIALS_PER_CLASS
            for profile, samples in (("a", 512), ("b", 800)):
                directory = self.root / f"data/processed/cho2017/profile_{profile}"
                directory.mkdir(parents=True, exist_ok=True)
                signals = generator.normal(size=(total, 64, samples)).astype(np.float32)
                signals *= 1e-8 if profile == "a" else 0.1
                if profile == "a":
                    signals[0] = 1  # One threshold-rejected trial.
                np.savez(
                    directory / f"{name}.npz",
                    signals=signals,
                    labels=np.array(CHO_CLASSES_TUPLE * TRIALS_PER_CLASS),
                    sessions=np.array(["s"] * total),
                    runs=np.array(["r"] * total),
                    trial_indices=np.arange(total),
                    channel_names=np.array(MONTAGE),
                )
                if profile == "b":
                    cfg = copy.deepcopy(base["profile_b"])
                    (directory / f"{name}.manifest.json").write_text(json.dumps(dict(
                        artifact_schema_version=1, artifact_kind="profile_b", subject=subject,
                        shape=[total, 64, samples], channel_names=list(MONTAGE),
                        epoch_duration_s=4.0, sampling_rate_hz=200.0,
                        config_sha256=config_digest(cfg), reference="original",
                        amplitude_unit_mv=0.1, patch_samples=200, patches_per_epoch=4,
                    )))
        threshold = load_toml(self.root / "configs/benchmark.toml")["datasets"]["cho2017"][
            "artifact_threshold_volts"
        ]
        preprocessing = config_digest({
            "profile_identity": self.config["preparation"]["profile_identity"],
            "threshold_config_sha256": file_digest(self.root / "configs/benchmark.toml"),
            "dataset": "cho2017", "threshold": threshold,
        })
        for subject in (1, 2, 3):
            name = f"subject_{subject:02d}"
            a = self.root / f"data/processed/cho2017/profile_a/{name}.npz"
            b = self.root / f"data/processed/cho2017/profile_b/{name}.npz"
            catalog, _ = read_catalog(
                a, dataset="cho2017", classes=CHO_CLASSES_TUPLE, threshold=threshold,
                preprocessing_sha256=preprocessing,
            )
            self.catalogs.append(catalog)
            self.assets[name] = ChoProfileAssets(
                file_digest(b), file_digest(b.with_suffix(".manifest.json"))
            )
            self.records[name] = envelope(
                "episode_manifest",
                nested_episode(
                    catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
                ).payload(),
            )
        self.catalogs = tuple(self.catalogs)
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(23)
            self.model = Labram(
                n_times=800, n_chans=64, n_outputs=0, num_layers=2,
                drop_prob=0.2, attn_drop_prob=0.2,
            )
        from encoder.labram import LaBraMClassifier

        self.classifier = LaBraMClassifier(self.model, classes=2, channel_names=MONTAGE)
        self.classifier.eval()

    def tearDown(self):
        self.temp.cleanup()

    def test_tuning_runner_predicts_cho_two_class_target(self):
        runner = LaBraMTuningManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, self.classifier,
            self.assets, outer_target="subject_01",
        )
        result = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=SUPPORT_SETTINGS,
        )
        self.assertEqual(result.logits.shape, (7, 2))  # (23-20)+(24-20) fixed queries.
        self.assertTrue(torch.isfinite(result.logits).all())
        self.assertEqual(result.binding.classes, CHO_CLASSES_TUPLE)
        self.assertEqual(result.binding.channel_names, MONTAGE)
        inner = LaBraMTuningManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, self.classifier,
            self.assets, outer_target="subject_01", validation_subject="subject_02",
        )
        validation = inner.predict_validation(
            self.records["subject_02"], shots_per_class=5, settings=SUPPORT_SETTINGS,
        )
        self.assertEqual(validation.role, "inner_validation")
        self.assertEqual(validation.logits.shape, (7, 2))

    def test_selector_runs_cho_selection_with_class_balanced_prompt_candidate(self):
        candidate = LaBraMSourceCandidate(
            "cho_linear", LaBraMSourceSettings("linear", 1, 2, 0.01), SUPPORT_SETTINGS
        )
        selector = BCILaBraMSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, self.classifier,
            self.assets, outer_target="subject_01",
            template_state_sha256=state_digest(self.classifier),
            candidates=(candidate,), seed=23, shots_per_class=1, maximum_gradient_steps=32,
        )
        self.assertEqual(selector.contract["dataset"], "cho2017")
        result = selector.run_selection()
        payload = result.evidence.record["payload"]
        self.assertTrue(payload["complete"])
        # Two source subjects -> two inner folds for the single candidate.
        self.assertEqual(len(payload["folds"]), 2)
        final = payload["final_source_fit"]
        self.assertEqual(final["training_subjects"], ["subject_02", "subject_03"])
        self.assertEqual(len(final["steps"]), 2)
        for fold in payload["folds"]:
            matrix = fold["confusion_matrix"]
            self.assertEqual(len(matrix), 2)
            self.assertEqual(len(matrix[0]), 2)
        # Recompute from confusion counts: a copied BCI divisor must not pass
        # merely because candidate ranking is unchanged by common scaling.
        means = [
            sum(Fraction(row[i], sum(row)) for i, row in enumerate(f["confusion_matrix"]))
            / len(f["confusion_matrix"])
            for f in payload["folds"]
        ]
        self.assertEqual(
            Fraction(*payload["scores"][0]["mean_balanced_accuracy"]),
            sum(means, start=Fraction()) / len(means),
        )
        self.assertEqual(
            selector.contract["source_policy"],
            "all_non_target_subjects; inner_validation_also_excluded",
        )

    def test_trained_prompt_runner_continues_on_cho(self):
        from adaptation.labram_prompt_trained import PromptSourceCandidate, PromptSourceSettings

        source_settings = PromptSourceSettings(2, 8, 11, True, 1, 1, 1, 0.01)
        prompt_candidate = PromptSourceCandidate(
            "cho_prompt",
            source_settings,
            PromptContinuationSettings(True, 1, 0.01, 4),
        )
        prompt_selector = BCILaBraMSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, self.classifier,
            self.assets, outer_target="subject_01",
            template_state_sha256=state_digest(self.classifier),
            candidates=(prompt_candidate,), seed=23, shots_per_class=1, maximum_gradient_steps=32,
        )
        source, fit = prompt_selector._fit(prompt_candidate, "subject_02")
        runner = TrainedPromptManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, source, self.assets,
            source_settings=source_settings, source_state_sha256=fit["fitted_state_sha256"],
            outer_target="subject_01",
        )
        result = runner.predict_target(
            self.records["subject_01"], shots_per_class=1,
            settings=PromptContinuationSettings(True, 1, 0.01, 4),
        )
        self.assertEqual(result.logits.shape, (7, 2))
        self.assertTrue(torch.isfinite(result.logits).all())
        self.assertEqual(result.binding.classes, CHO_CLASSES_TUPLE)

    def test_mismatched_asset_inventory_refuses(self):
        from evaluation.phase2_profile_binding import BCIProfileAssets

        bci_assets = {
            name: BCIProfileAssets("0" * 64, "1" * 64, "2" * 64) for name in self.assets
        }
        with self.assertRaisesRegex(ValueError, "sidecar convention"):
            LaBraMTuningManifestRunner(
                self.root, self.config, self.catalogs, self.selection_record, self.classifier,
                bci_assets, outer_target="subject_01",
            )
        with self.assertRaises(ValueError):
            LaBraMTuningManifestRunner(
                self.root, self.config, self.catalogs[:-1], self.selection_record,
                self.classifier, self.assets, outer_target="subject_01",
            )

    def test_60hz_cohort_binds_and_mixed_inventory_refuses(self):
        config_file = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path("configs/phase2/cho_profile_b_60hz.toml"), config_file)
        variant_document = load_toml(config_file)
        directory = self.root / variant_document["variant"]["output_directory"]
        directory.mkdir(parents=True)
        variant_assets = {}
        for subject in (1, 2, 3):
            name = f"subject_{subject:02d}"
            historical = self.root / "data/processed/cho2017/profile_b"
            artifact = directory / f"{name}.npz"
            shutil.copyfile(historical / artifact.name, artifact)
            raw_file = self.root / f"data/raw/moabb/cho2017/{name}.mat"
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            raw_file.write_bytes(f"source {name}".encode())
            manifest = json.loads(
                (historical / f"{name}.manifest.json").read_text(encoding="utf-8")
            )
            manifest.update({
                "config_sha256": config_digest(variant_document["preprocessing"]),
                "variant": variant_document["variant"],
                "variant_config_sha256": file_digest(config_file),
                "source_file": raw_file.relative_to(self.root).as_posix(),
                "source_sha256": file_digest(raw_file),
            })
            manifest_file = directory / f"{name}.manifest.json"
            manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
            variant_assets[name] = ChoProfileAssets60Hz(
                file_digest(artifact), file_digest(manifest_file), file_digest(config_file)
            )
        mixed_assets = dict(variant_assets)
        mixed_assets["subject_02"] = self.assets["subject_02"]
        with self.assertRaisesRegex(ValueError, "mixes 50 Hz and 60 Hz"):
            LaBraMTuningManifestRunner(
                self.root, self.config, self.catalogs, self.selection_record, self.classifier,
                mixed_assets, outer_target="subject_01",
            )
        runner = LaBraMTuningManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, self.classifier,
            variant_assets, outer_target="subject_01",
        )
        result = runner.predict_target(
            self.records["subject_01"], shots_per_class=1, settings=SUPPORT_SETTINGS,
        )
        self.assertIsInstance(result.binding, ChoProfileBinding60Hz)


if __name__ == "__main__":
    unittest.main()
