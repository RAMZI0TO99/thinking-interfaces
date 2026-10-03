"""Focused metadata routing checks; no EEG arrays or model fits."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from evaluation.phase2_cho_case_inputs import (
    CHO_SUBJECTS,
    ChoCaseInputPins,
    prepare_cho_first_tranche,
)
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog
from evaluation.phase2_runner import CasePlan


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ChoCaseInputTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        source_root = Path(__file__).resolve().parents[1]
        for relative in ("configs/phase2/protocol.toml", "configs/benchmark.toml"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((source_root / relative).read_bytes())
        for subject in CHO_SUBJECTS:
            artifact = self.root / f"data/processed/cho2017/profile_a/{subject}.npz"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(subject.encode())
        self.variant_sha256 = "d" * 64
        self.pins = ChoCaseInputPins(
            protocol_config_sha256=digest(
                (self.root / "configs/phase2/protocol.toml").read_bytes()
            ),
            threshold_config_sha256=digest(
                (self.root / "configs/benchmark.toml").read_bytes()
            ),
            cohort_audit_sha256="e" * 64,
            variant_config_sha256=self.variant_sha256,
        )
        self.assets = {
            subject: ChoProfileAssets60Hz(
                profile_b_artifact_sha256=digest(f"b-{subject}".encode()),
                profile_b_manifest_sha256=digest(f"m-{subject}".encode()),
                variant_config_sha256=self.variant_sha256,
            )
            for subject in CHO_SUBJECTS
        }

    def catalog(self, path, *, dataset, classes, threshold, preprocessing_sha256):
        del threshold
        subject = path.stem
        return TrialCatalog(
            dataset=dataset,
            subject=subject,
            trial_ids=tuple(f"{subject}-{index:02d}" for index in range(42)),
            labels=("left_hand",) * 21 + ("right_hand",) * 21,
            classes=classes,
            artifact_sha256=digest(subject.encode()),
            preprocessing_sha256=preprocessing_sha256,
        ), {}

    def build(self, *, assets=None, catalog=None):
        with (
            patch(
                "evaluation.phase2_cho_case_inputs.read_catalog",
                side_effect=catalog or self.catalog,
            ),
            patch(
                "evaluation.phase2_cho_case_inputs.load_cho_60hz_assets",
                return_value=self.assets if assets is None else assets,
            ),
        ):
            return prepare_cho_first_tranche(self.root, pins=self.pins)

    def test_selected_route_has_fixed_cases_and_method_correct_profiles(self) -> None:
        route = self.build()
        self.assertEqual(len(route.catalogs), 52)
        self.assertEqual(len(route.labram_assets), 52)
        self.assertEqual(len(route.plans), 1040)
        self.assertEqual(Counter(plan.method for plan in route.plans), {
            "labram_linear": 260,
            "labram_lora": 260,
            "labram_full": 260,
            "eegnet": 260,
        })
        self.assertEqual({plan.shots_per_class for plan in route.plans}, {5})
        self.assertEqual({plan.model_seed for plan in route.plans}, {11, 23, 37, 53, 71})
        linear = route.inputs_for(route.plans[0])
        eegnet = route.inputs_for(next(p for p in route.plans if p.method == "eegnet"))
        self.assertEqual(linear.profile, "cho_profile_b_60hz_v1")
        self.assertEqual(len(linear.assets), 52)
        self.assertEqual(eegnet.profile, "cho_profile_a")
        self.assertEqual(len(eegnet.assets), 0)
        self.assertEqual(linear.selection_record["kind"], "source_selection")
        self.assertEqual(linear.episode_record["kind"], "episode_manifest")
        self.assertEqual(
            linear.episode_record["payload"]["catalog"]["subject"], "subject_01"
        )
        linear.selection_record["payload"]["dataset"] = "tampered"
        self.assertEqual(
            route.inputs_for(route.plans[0]).selection_record["payload"]["dataset"],
            "cho2017",
        )
        with self.assertRaisesRegex(ValueError, "outside the selected"):
            route.inputs_for(CasePlan("cho2017", "subject_01", "ea_tangent_lr", 5, 11, 1))

    def test_wrong_pins_or_incomplete_inventory_refuse(self) -> None:
        wrong = ChoCaseInputPins(
            "0" * 64,
            self.pins.threshold_config_sha256,
            self.pins.cohort_audit_sha256,
            self.pins.variant_config_sha256,
        )
        with self.assertRaisesRegex(ValueError, "protocol config.*pin"):
            prepare_cho_first_tranche(self.root, pins=wrong)
        with self.assertRaisesRegex(ValueError, "complete pinned"):
            self.build(assets={k: v for k, v in self.assets.items() if k != "subject_52"})

    def test_catalog_roster_mismatch_refuses(self) -> None:
        def duplicate_catalog(path, **kwargs):
            if path.stem == "subject_02":
                path = path.with_name("subject_01.npz")
            return self.catalog(path, **kwargs)

        with self.assertRaisesRegex(ValueError, "catalog roster"):
            self.build(catalog=duplicate_catalog)


if __name__ == "__main__":
    unittest.main()
