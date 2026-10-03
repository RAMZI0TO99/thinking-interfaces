"""Small synthetic checks for prospective Cho target input publication."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

from adaptation.anchor_manifest import AnchorPrediction, EEGNetAnchorSettings
from adaptation.labram_manifest import LaBraMTuningSettings
from core.config import config_digest, load_toml
from core.provenance import SourceProvenance
from encoder.labram import LaBraMClassifier
from evaluation.phase2_pilot import (
    AnchorAdapter,
    CaseOutcome,
    LaBraMTunedAdapter,
    TargetCaseExecutor,
    _cho_target_input_attestation,
)
from evaluation.phase2_profile_binding import (
    CHO_CHANNELS,
    ChoProfileAssets60Hz,
    ChoProfileBinding60Hz,
)
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import (
    CasePlan,
    CaseRecorder,
    environment_digest,
    method_configuration,
)
from scripts.audit_phase2_protocol import file_digest, validate_protocol


class _OutcomeAdapter:
    def __init__(self, method: str, outcome: CaseOutcome) -> None:
        self.method = method
        self.outcome = outcome

    def predict_target(self, *args: object, **kwargs: object) -> CaseOutcome:
        return self.outcome


class ChoTargetAttestationTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "configs/phase2").mkdir(parents=True)
        (self.root / "configs/base.toml").write_text("[base]\nvalue=1\n", "utf-8")
        self.variant_path = self.root / "configs/phase2/cho_profile_b_60hz.toml"
        self.variant_path.write_text("[preprocessing]\nnotch_hz=60.0\n", "utf-8")
        b_dir = self.root / "data/processed/cho2017/profile_b_60hz_v1"
        b_dir.mkdir(parents=True)
        self.manifest_path = b_dir / "subject_01.manifest.json"
        self.manifest = {
            "source_file": "data/raw/moabb/cho2017/subject_01.gdf",
            "source_sha256": "8" * 64,
        }
        self.manifest_path.write_text(json.dumps(self.manifest), "utf-8")
        self.asset = ChoProfileAssets60Hz(
            "3" * 64, file_digest(self.manifest_path), file_digest(self.variant_path)
        )
        self.config = load_toml(
            Path(__file__).resolve().parents[1] / "configs/phase2/protocol.toml"
        )
        self.catalogs = tuple(
            TrialCatalog(
                "cho2017", f"subject_{number:02d}",
                tuple(f"subject_{number:02d}/trial_{index:02d}" for index in range(42)),
                ("left_hand", "right_hand") * 21,
                ("left_hand", "right_hand"),
                "1" * 64, "2" * 64,
            )
            for number in range(1, 53)
        )
        self.catalog = self.catalogs[0]
        self.selection = source_selection(self.catalogs, target="subject_01")
        self.selection_record = envelope("source_selection", asdict(self.selection))
        self.episode = nested_episode(
            self.catalog, shots=validate_protocol(self.config),
            protocol_sha256=config_digest(self.config),
        )
        self.episode_record = envelope("episode_manifest", self.episode.payload())
        partition = self.episode.partition(5)
        self.support_ids = tuple(self.catalog.trial_ids[i] for i in partition.support_indices)
        self.query_ids = tuple(self.catalog.trial_ids[i] for i in partition.query_indices)
        self.assertEqual(len(self.query_ids), 2)
        self.targets = torch.tensor(
            [self.catalog.classes.index(self.catalog.labels[i]) for i in partition.query_indices],
            dtype=torch.long,
        )
        self.logits = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        self.source = SourceProvenance("7" * 40, "5" * 64, False)

    def _method_config(self, method: str) -> dict[str, Any]:
        return {
            "method": method,
            "dataset": "cho2017",
            "input_profile": "cho_profile_a" if method == "eegnet" else "cho_profile_b_60hz_v1",
            "variant_config_sha256": (
                None if method == "eegnet" else self.asset.variant_config_sha256
            ),
            "candidates": [
                {"name": f"candidate_{index}",
                 "source": {
                     "steps_per_subject": 1,
                     "learning_rate": 0.01,
                     **({"seed": "$case_model_seed"} if method == "labram_lora" else {}),
                 },
                 "support": {"steps": 1, "learning_rate": 0.01}}
                for index in range(2)
            ],
            "source_seed_policy": "case_model_seed" if method == "labram_lora" else "none",
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order",
            "early_stopping": False,
        }

    def _plan_identity(self, method: str) -> tuple[CasePlan, CellIdentity, dict[str, Any]]:
        plan = CasePlan("cho2017", "subject_01", method, 5, 11, 1)
        method_config = self._method_config(method)
        identity = CellIdentity(
            "cho2017", "subject_01", method, 5, 11, None, None,
            config_digest(self.config), self.episode_record["sha256"],
            self.selection_record["sha256"], method_configuration(method_config),
            self.catalog.preprocessing_sha256, "f" * 64,
            self.source.source_sha256, environment_digest(),
            self.source.git_commit, False,
        )
        return plan, identity, method_config

    def _binding(self) -> ChoProfileBinding60Hz:
        preprocessing = load_toml(self.variant_path)["preprocessing"]
        if not isinstance(preprocessing, dict):
            raise AssertionError("synthetic variant preprocessing must be a mapping")
        return ChoProfileBinding60Hz(
            "cho2017", "subject_01", 5, self.catalog.classes, CHO_CHANNELS,
            config_digest(self.config), self.episode.sha256,
            self.catalog.artifact_sha256, self.asset.profile_b_artifact_sha256,
            self.asset.profile_b_manifest_sha256, self.catalog.preprocessing_sha256,
            config_digest(preprocessing),
            file_digest(self.root / "configs/base.toml"),
            self.support_ids, self.query_ids, tuple(range(len(self.support_ids))),
            tuple(range(len(self.support_ids), len(self.support_ids) + len(self.query_ids))),
            42, 0,
            variant_config_sha256=self.asset.variant_config_sha256,
            source_file=self.manifest["source_file"],
            source_sha256=self.manifest["source_sha256"],
        )

    def _anchor(self) -> AnchorPrediction:
        settings = EEGNetAnchorSettings(1, 0.01, 1000000.0)
        return AnchorPrediction(
            "eegnet", "subject_01", "outer_target", self.episode.sha256,
            self.selection.sha256, config_digest(asdict(settings)), settings,
            self.support_ids, self.query_ids, self.selection.source_subjects,
            {"subject_01": {
                "catalog_sha256": self.catalog.sha256,
                "artifact_sha256": self.catalog.artifact_sha256,
                "manifest_sha256": self.catalog.artifact_sha256,
                "base_config_sha256": file_digest(self.root / "configs/base.toml"),
            }},
            {}, "f" * 64, "e" * 64,
            self.logits.numpy().astype(np.float32),
            self.targets.numpy().astype(np.int64),
            classes=self.catalog.classes,
        )

    def _case_outcome(
        self, *, binding: ChoProfileBinding60Hz | None = None,
        anchor: AnchorPrediction | None = None,
    ) -> CaseOutcome:
        return CaseOutcome(
            self.logits, self.targets, self.support_ids, self.query_ids,
            self.episode_record["sha256"], "f" * 64, (0.0,),
            cho_profile_binding=binding, anchor_prediction=anchor,
        )

    def _attest(
        self, method: str, outcome: CaseOutcome,
        *, assets: dict[str, ChoProfileAssets60Hz] | None = None,
    ) -> dict[str, Any]:
        plan, identity, _ = self._plan_identity(method)
        current = assets if assets is not None else (
            {} if method == "eegnet" else {"subject_01": self.asset}
        )
        return _cho_target_input_attestation(
            root=self.root, plan=plan, identity=identity, outcome=outcome,
            target_catalog=self.catalog, episode_sha256=self.episode.sha256,
            selection_sha256=self.selection.sha256,
            expected_source_subjects=self.selection.source_subjects,
            expected_support_ids=self.support_ids, expected_query_ids=self.query_ids,
            assets=current,
            target_asset=current.get("subject_01"),
        )

    def test_labram_attestation_carries_full_observed_60hz_binding(self) -> None:
        binding = self._binding()
        for method in ("labram_linear", "labram_lora", "labram_full"):
            with self.subTest(method=method):
                evidence = self._attest(method, self._case_outcome(binding=binding))
                self.assertEqual(evidence["binding"], asdict(binding))
                self.assertEqual(evidence["binding_sha256"], binding.sha256)
                self.assertEqual(evidence["profile"], "cho_profile_b_60hz_v1")

    def test_labram_missing_or_swapped_observed_bytes_fail(self) -> None:
        binding = self._binding()
        cases = (
            (None, "missing"),
            (replace(binding, subject="subject_02"), "planned inputs"),
            (replace(binding, episode_sha256="0" * 64), "planned inputs"),
            (replace(binding, profile_b_artifact_sha256="0" * 64), "planned inputs"),
            (replace(binding, profile_b_manifest_sha256="0" * 64), "planned inputs"),
            (replace(binding, variant_config_sha256="0" * 64), "planned inputs"),
            (replace(binding, source_sha256="0" * 64), "planned inputs"),
            (replace(binding, profile_a_rejected_trials=1), "planned inputs"),
        )
        for observed, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ValueError, pattern):
                self._attest("labram_linear", self._case_outcome(binding=observed))

    def test_eegnet_attestation_is_exact_target_profile_a(self) -> None:
        anchor = self._anchor()
        evidence = self._attest("eegnet", self._case_outcome(anchor=anchor))
        self.assertEqual(evidence["profile"], "cho_profile_a")
        self.assertEqual(evidence["anchor"]["input_identities"], anchor.input_identities)
        self.assertNotIn("binding", evidence)
        self.assertNotIn(
            "profile_b_artifact_sha256",
            evidence["anchor"]["input_identities"]["subject_01"],
        )

    def test_eegnet_swapped_or_mixed_inputs_fail(self) -> None:
        anchor = self._anchor()
        wrong_a = replace(anchor, input_identities={
            "subject_01": {**anchor.input_identities["subject_01"], "artifact_sha256": "0" * 64}
        })
        wrong_subject = replace(anchor, subject="subject_02")
        mixed = replace(anchor, input_identities={
            "subject_01": {**anchor.input_identities["subject_01"],
                           "profile_b_artifact_sha256": "0" * 64}
        })
        for observed in (None, wrong_a, wrong_subject, mixed):
            with self.subTest(observed=observed), self.assertRaises(ValueError):
                self._attest("eegnet", self._case_outcome(anchor=observed))
        with self.assertRaisesRegex(ValueError, "Profile A observation"):
            self._attest("eegnet", self._case_outcome(anchor=anchor),
                         assets={"subject_01": self.asset})

    def test_adapters_carry_the_observed_runner_evidence(self) -> None:
        binding = self._binding()
        model = nn.Linear(2, 2)

        class FakeLaBraMRunner:
            def __init__(self, *args: object, **kwargs: object) -> None:
                self._source = model

            def predict_target(self, *args: object, **kwargs: object) -> SimpleNamespace:
                return SimpleNamespace(
                    logits=self_logits, targets=self_targets, binding=binding,
                )

        self_logits, self_targets = self.logits, self.targets
        with patch("evaluation.phase2_pilot.LaBraMTuningManifestRunner", FakeLaBraMRunner):
            plain = LaBraMTunedAdapter(
                "labram_linear", cast(LaBraMClassifier, model),
                LaBraMTuningSettings("linear", 1, 0.01),
            ).predict_target(
                self.root, self.config, self.catalogs, self.selection_record,
                {"subject_01": self.asset}, self.episode_record,
                outer_target="subject_01", shots_per_class=5,
            )
        self.assertIs(plain.cho_profile_binding, binding)

        anchor = self._anchor()

        class FakeAnchorRunner:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def predict_target(self, *args: object, **kwargs: object) -> AnchorPrediction:
                return anchor

        with patch("evaluation.phase2_pilot.BCIAnchorManifestRunner", FakeAnchorRunner):
            eegnet = AnchorAdapter(
                "eegnet", EEGNetAnchorSettings(1, 0.01, 1000000.0), model,
            ).predict_target(
                self.root, self.config, self.catalogs, self.selection_record,
                {}, self.episode_record,
                outer_target="subject_01", shots_per_class=5,
            )
        self.assertIs(eegnet.anchor_prediction, anchor)

    def test_executor_publishes_checked_binding_in_cell_metrics(self) -> None:
        plan, identity, method_config = self._plan_identity("labram_linear")
        recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/recorder")
        executor = TargetCaseExecutor(
            self.root, recorder,
            admission={"admitted": True, "operator_compute_admitted": True},
            worker="synthetic-attestation-test",
        )
        evidence_path = self.root / "runs/phase2/evidence.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("{}", "utf-8")
        binding = self._binding()
        manifest_sha256 = "d" * 64
        publication = SimpleNamespace(
            manifest_sha256=manifest_sha256,
            manifest_path=(
                self.root / "runs/phase2/selected_sources/manifests"
                / f"{manifest_sha256}.json"
            ),
        )
        with (
            patch("evaluation.phase2_pilot.capture_source", return_value=self.source),
            patch("evaluation.phase2_pilot.compute_admission", return_value={"admitted": True}),
            patch("evaluation.phase2_pilot.state_digest", return_value=identity.checkpoint_sha256),
            patch("evaluation.phase2_cho_execution_gate.verify_cho_case_preclaim"),
            patch(
                "evaluation.phase2_cho_publication_gate.publish_verified_cho_source",
                return_value=SimpleNamespace(
                    publication=publication,
                    witness=SimpleNamespace(verify_stable=lambda: None),
                ),
            ),
            patch("evaluation.phase2_cho_publication_gate._selected_model"),
            patch(
                "evaluation.phase2_cho_execution_gate._persisted_record",
                return_value={"sha256": "9" * 64},
            ),
            patch("evaluation.phase2_cho_execution_gate.verify_cho_adapter_posttarget"),
        ):
            result = executor.run_case(
                plan, adapter=_OutcomeAdapter("labram_linear", self._case_outcome(binding=binding)),
                identity=identity, method_config=method_config,
                selection_evidence_sha256="9" * 64,
                selection_evidence_path=evidence_path,
                protocol_config=self.config, catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.episode_record,
                assets={"subject_01": self.asset},
            )
        cell = json.loads(Path(result["cell"]).read_text("utf-8"))
        observed = cell["payload"]["metrics"]["target_input_attestation"]
        self.assertEqual(observed["schema"], "cho2017-target-input-v1")
        self.assertEqual(observed["binding_sha256"], binding.sha256)
        self.assertEqual(observed["binding"], json.loads(json.dumps(asdict(binding))))
        self.assertEqual(
            cell["payload"]["metrics"]["selected_source_manifest_sha256"],
            manifest_sha256,
        )
        self.assertEqual(
            cell["payload"]["metrics"]["selected_source_manifest_path"],
            f"runs/phase2/selected_sources/manifests/{manifest_sha256}.json",
        )
        self.assertEqual(recorder.completion([plan])["measured"], 1)

    def test_executor_records_failure_before_cell_for_missing_binding(self) -> None:
        plan, identity, method_config = self._plan_identity("labram_linear")
        recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/recorder")
        executor = TargetCaseExecutor(
            self.root, recorder,
            admission={"admitted": True, "operator_compute_admitted": True},
            worker="synthetic-attestation-test",
        )
        evidence_path = self.root / "runs/phase2/evidence.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("{}", "utf-8")
        manifest_sha256 = "d" * 64
        publication = SimpleNamespace(
            manifest_sha256=manifest_sha256,
            manifest_path=(
                self.root / "runs/phase2/selected_sources/manifests"
                / f"{manifest_sha256}.json"
            ),
        )
        with (
            patch("evaluation.phase2_pilot.capture_source", return_value=self.source),
            patch("evaluation.phase2_pilot.compute_admission", return_value={"admitted": True}),
            patch("evaluation.phase2_pilot.state_digest", return_value=identity.checkpoint_sha256),
            patch("evaluation.phase2_cho_execution_gate.verify_cho_case_preclaim"),
            patch(
                "evaluation.phase2_cho_publication_gate.publish_verified_cho_source",
                return_value=SimpleNamespace(
                    publication=publication,
                    witness=SimpleNamespace(verify_stable=lambda: None),
                ),
            ),
            patch("evaluation.phase2_cho_publication_gate._selected_model"),
            self.assertRaisesRegex(ValueError, "binding or asset pin is missing"),
        ):
            executor.run_case(
                plan, adapter=_OutcomeAdapter("labram_linear", self._case_outcome()),
                identity=identity, method_config=method_config,
                selection_evidence_sha256="9" * 64,
                selection_evidence_path=evidence_path,
                protocol_config=self.config, catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.episode_record,
                assets={"subject_01": self.asset},
            )
        self.assertEqual(recorder.completion([plan])["failed"], 1)
        self.assertEqual(recorder.completion([plan])["measured"], 0)


if __name__ == "__main__":
    unittest.main()
