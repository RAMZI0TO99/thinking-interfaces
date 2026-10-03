"""Focused Cho selected-source publication and preclaim ordering checks."""

from __future__ import annotations

import json
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast
from unittest.mock import patch

import test_phase2_cho_target_attestation as attestation_fixture
from torch import nn

from adaptation.anchor_manifest import EEGNetAnchorSettings
from adaptation.labram_lora_trained import LoRAContinuationSettings, LoRASourceSettings
from adaptation.labram_manifest import LaBraMTuningSettings
from core.config import config_digest
from core.provenance import SourceProvenance
from encoder.labram import LaBraMClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_publication_gate import (
    _require_selected_model_class,
    publish_verified_cho_source,
)
from evaluation.phase2_pilot import (
    AnchorAdapter,
    LaBraMTunedAdapter,
    TargetCaseExecutor,
    TrainedLaBraMAdapter,
)
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_runner import CasePlan, CaseRecorder
from evaluation.phase2_selected_source_store import SelectedSourcePublication
from evaluation.phase2_selection_evidence_binding import VerifiedChoSelection


def _identity(method: str, model_sha: str) -> CellIdentity:
    return CellIdentity(
        "cho2017", "subject_01", method, 5, 11, None, None,
        config_digest({"protocol": 1}), "2" * 64, "3" * 64, "4" * 64,
        "5" * 64, model_sha, "6" * 64, "7" * 64, "8" * 40, False,
    )


def _publication(root: Path, model_sha: str, evidence_sha: str, candidate: str,
                 evidence_format: str) -> SelectedSourcePublication:
    root = root.resolve()
    return SelectedSourcePublication(
        "a" * 64, evidence_sha, candidate, model_sha, "b" * 64,
        root / "runs/phase2/selected_sources/manifests" / f"{'a' * 64}.json",
        root / "runs/phase2/selected_sources/evidence" / f"{evidence_sha}.json",
        root / "runs/phase2/selected_sources/weights" / f"{'b' * 64}.safetensors",
        False, "full_v1", cast(Any, evidence_format),
    )


class ChoPublicationGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = attestation_fixture.ChoTargetAttestationTests(
            "test_labram_attestation_carries_full_observed_60hz_binding"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.model = nn.Linear(2, 2)
        self.model_sha = state_digest(self.model)
        self.evidence_sha = "9" * 64
        self.selection = VerifiedChoSelection("candidate_0", self.evidence_sha)
        self.source = SourceProvenance("8" * 40, "6" * 64, False)

    def _record(self, winner: str = "candidate_0") -> dict[str, Any]:
        contract = {"source": asdict(self.source)}
        return {"sha256": self.evidence_sha, "payload": {
            "selected_candidate": winner,
            "contract": contract,
            "contract_sha256": config_digest(contract),
        }}

    @staticmethod
    def _witness(publication: SelectedSourcePublication) -> SimpleNamespace:
        return SimpleNamespace(
            weights_path=publication.weights_path,
            weights_sha256=publication.weights_sha256,
            evidence_path=publication.evidence_path,
            verify_stable=lambda: None,
        )

    def _adapter(self, method: str) -> Any:
        if method in {"labram_linear", "labram_full"}:
            tuning: Literal["linear", "full"] = (
                "linear" if method == "labram_linear" else "full"
            )
            return LaBraMTunedAdapter(
                method, cast(LaBraMClassifier, self.model),
                LaBraMTuningSettings(tuning, 1, 0.01),
            )
        if method == "labram_lora":
            return TrainedLaBraMAdapter(
                method, cast(LaBraMClassifier, self.model),
                LoRASourceSettings(
                    ("backbone.blocks.11.attn.qkv",), 1, 1.0, 11, True, 1, 2, 0.01,
                ),
                LoRAContinuationSettings(True, 1, 0.01),
            )
        return AnchorAdapter("eegnet", EEGNetAnchorSettings(1, 0.01, 1.0), self.model)

    def test_all_four_methods_publish_live_model_with_independent_recipe(self) -> None:
        record = self._record()
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            with self.subTest(method=method):
                plan = CasePlan("cho2017", "subject_01", method, 5, 11, 1)
                identity = _identity(method, self.model_sha)
                evidence_path = self.root / (
                    "runs/phase2/source/evidence/packed.factored.json"
                    if method == "eegnet" else "runs/phase2/evidence.json"
                )
                expected_format = (
                    "factored_json_v1" if method == "eegnet" else "canonical_json_v1"
                )
                publication = _publication(
                    self.root, self.model_sha, self.evidence_sha,
                    "candidate_0", expected_format,
                )
                config = {"method": method, "dataset": "cho2017"}
                with (
                    patch(
                        "evaluation.phase2_cho_publication_gate.prepare_cho_source_restore",
                        return_value=SimpleNamespace(model_recipe={"architecture": method}),
                    ) as prepare,
                    patch("evaluation.phase2_cho_publication_gate.capture_source",
                          return_value=self.source),
                    patch("evaluation.phase2_cho_publication_gate._require_selected_model_class"),
                    patch(
                        "evaluation.phase2_cho_publication_gate._persisted_record",
                        return_value=record,
                    ) as read_record,
                    patch(
                        "evaluation.phase2_cho_publication_gate.SelectedSourceStore.publish",
                        return_value=publication,
                    ) as publish,
                    patch(
                        "evaluation.phase2_cho_publication_gate.verify_cho_selected_manifest_files",
                        return_value=self._witness(publication),
                    ) as verify_files,
                ):
                    observed = publish_verified_cho_source(
                        root=self.root, plan=plan, adapter=self._adapter(method),
                        identity=identity, method_config=config,
                        protocol_config={"protocol": 1}, evidence_path=evidence_path,
                        selection=self.selection,
                    )
                self.assertIs(observed.publication, publication)
                self.assertEqual(verify_files.call_args.kwargs["expected_source"], self.source)
                self.assertEqual(
                    verify_files.call_args.kwargs["model_recipe_sha256"],
                    config_digest({"architecture": method}),
                )
                self.assertEqual(
                    verify_files.call_args.kwargs["selection_contract_sha256"],
                    record["payload"]["contract_sha256"],
                )
                self.assertEqual(prepare.call_args.kwargs["selected_candidate"], "candidate_0")
                self.assertEqual(
                    prepare.call_args.kwargs["expected_method_config_sha256"],
                    identity.method_config_sha256,
                )
                self.assertEqual(read_record.call_count, 1)
                self.assertIs(publish.call_args.args[0], self.model)
                self.assertIs(publish.call_args.args[1], record)
                self.assertEqual(publish.call_args.kwargs["evidence_format"], expected_format)
                self.assertEqual(publish.call_args.kwargs["model_recipe"], {
                    "architecture": method,
                })
                self.assertNotIn("weights_format", publish.call_args.kwargs)

    def test_changed_winner_or_model_refuses_before_store_publish(self) -> None:
        plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        identity = _identity("eegnet", self.model_sha)
        with (
            patch(
                "evaluation.phase2_cho_publication_gate.prepare_cho_source_restore",
                return_value=SimpleNamespace(model_recipe={"architecture": "eegnet"}),
            ),
            patch("evaluation.phase2_cho_publication_gate.capture_source",
                  return_value=self.source),
            patch("evaluation.phase2_cho_publication_gate._require_selected_model_class"),
            patch(
                "evaluation.phase2_cho_publication_gate._persisted_record",
                return_value=self._record("other"),
            ),
            patch("evaluation.phase2_cho_publication_gate.SelectedSourceStore.publish") as publish,
            self.assertRaisesRegex(ValueError, "changed after preclaim"),
        ):
            publish_verified_cho_source(
                root=self.root, plan=plan, adapter=self._adapter("eegnet"),
                identity=identity, method_config={}, protocol_config={"protocol": 1},
                evidence_path=self.root / "runs/phase2/evidence.json",
                selection=self.selection,
            )
        publish.assert_not_called()
        wrong = _identity("eegnet", "0" * 64)
        with (
            patch("evaluation.phase2_cho_publication_gate._persisted_record") as read_record,
            self.assertRaisesRegex(ValueError, "state differs"),
        ):
            publish_verified_cho_source(
                root=self.root, plan=plan, adapter=self._adapter("eegnet"),
                identity=wrong, method_config={}, protocol_config={"protocol": 1},
                evidence_path=self.root / "runs/phase2/evidence.json",
                selection=self.selection,
            )
        read_record.assert_not_called()

    def test_publication_manifest_path_must_match_returned_digest(self) -> None:
        plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        publication = replace(
            _publication(
                self.root, self.model_sha, self.evidence_sha,
                "candidate_0", "canonical_json_v1",
            ),
            manifest_path=self.root / "runs/phase2/selected_sources/manifests/wrong.json",
        )
        with (
            patch(
                "evaluation.phase2_cho_publication_gate.prepare_cho_source_restore",
                return_value=SimpleNamespace(model_recipe={"architecture": "eegnet"}),
            ),
            patch("evaluation.phase2_cho_publication_gate.capture_source",
                  return_value=self.source),
            patch("evaluation.phase2_cho_publication_gate._require_selected_model_class"),
            patch(
                "evaluation.phase2_cho_publication_gate._persisted_record",
                return_value=self._record(),
            ),
            patch(
                "evaluation.phase2_cho_publication_gate.SelectedSourceStore.publish",
                return_value=publication,
            ),
            self.assertRaisesRegex(ValueError, "published source differs"),
        ):
            publish_verified_cho_source(
                root=self.root, plan=plan, adapter=self._adapter("eegnet"),
                identity=_identity("eegnet", self.model_sha),
                method_config={}, protocol_config={"protocol": 1},
                evidence_path=self.root / "runs/phase2/evidence.json",
                selection=self.selection,
            )

    def test_live_model_class_must_match_restore_recipe(self) -> None:
        with self.assertRaisesRegex(ValueError, "LaBraM fitted source model class"):
            _require_selected_model_class(
                self.model, "labram_linear",
                {"architecture": {"channel_names": [], "classes": 2}},
            )
        with self.assertRaisesRegex(ValueError, "EEGNet fitted source model class"):
            _require_selected_model_class(
                self.model, "eegnet",
                {"architecture": {
                    "n_chans": 22, "n_outputs": 2, "n_times": 512, "sfreq": 128,
                    "final_layer_with_constraint": True,
                }},
            )

    def test_wrong_live_model_class_refuses_before_store_publish(self) -> None:
        plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        with (
            patch("evaluation.phase2_cho_publication_gate.capture_source",
                  return_value=self.source),
            patch(
                "evaluation.phase2_cho_publication_gate.prepare_cho_source_restore",
                return_value=SimpleNamespace(model_recipe={"architecture": {
                    "n_chans": 22, "n_outputs": 2, "n_times": 512, "sfreq": 128,
                    "final_layer_with_constraint": True,
                }}),
            ),
            patch("evaluation.phase2_cho_publication_gate._persisted_record") as evidence,
            patch("evaluation.phase2_cho_publication_gate.SelectedSourceStore.publish") as publish,
            self.assertRaisesRegex(ValueError, "EEGNet fitted source model class"),
        ):
            publish_verified_cho_source(
                root=self.root, plan=plan, adapter=self._adapter("eegnet"),
                identity=_identity("eegnet", self.model_sha), method_config={},
                protocol_config={"protocol": 1},
                evidence_path=self.root / "runs/phase2/evidence.json",
                selection=self.selection,
            )
        evidence.assert_not_called()
        publish.assert_not_called()

    def test_physical_file_verifier_refusal_prevents_release(self) -> None:
        plan = CasePlan("cho2017", "subject_01", "eegnet", 5, 11, 1)
        publication = _publication(
            self.root, self.model_sha, self.evidence_sha,
            "candidate_0", "canonical_json_v1",
        )
        with (
            patch("evaluation.phase2_cho_publication_gate.capture_source",
                  return_value=self.source),
            patch("evaluation.phase2_cho_publication_gate._require_selected_model_class"),
            patch(
                "evaluation.phase2_cho_publication_gate.prepare_cho_source_restore",
                return_value=SimpleNamespace(model_recipe={"architecture": "eegnet"}),
            ),
            patch("evaluation.phase2_cho_publication_gate._persisted_record",
                  return_value=self._record()),
            patch("evaluation.phase2_cho_publication_gate.SelectedSourceStore.publish",
                  return_value=publication) as publish,
            patch(
                "evaluation.phase2_cho_publication_gate.verify_cho_selected_manifest_files",
                side_effect=ValueError("selected weights bytes differ from manifest hash"),
            ) as verify_files,
            self.assertRaisesRegex(ValueError, "selected weights bytes differ"),
        ):
            publish_verified_cho_source(
                root=self.root, plan=plan, adapter=self._adapter("eegnet"),
                identity=_identity("eegnet", self.model_sha), method_config={},
                protocol_config={"protocol": 1},
                evidence_path=self.root / "runs/phase2/evidence.json",
                selection=self.selection,
            )
        publish.assert_called_once()
        verify_files.assert_called_once()

    def test_eegnet_live_head_must_have_recipe_constraint(self) -> None:
        from braindecode.models import EEGNet  # type: ignore[import-untyped]

        recipe = {"architecture": {
            "n_chans": 22, "n_outputs": 2, "n_times": 512, "sfreq": 128,
            "final_layer_with_constraint": True,
        }}
        constrained = EEGNet(
            n_chans=22, n_outputs=2, n_times=512, sfreq=128,
            final_layer_with_constraint=True,
        )
        _require_selected_model_class(constrained, "eegnet", recipe)
        unconstrained = EEGNet(
            n_chans=22, n_outputs=2, n_times=512, sfreq=128,
            final_layer_with_constraint=False,
        )
        with self.assertRaisesRegex(ValueError, "EEGNet fitted source model class"):
            _require_selected_model_class(unconstrained, "eegnet", recipe)

    def _run_case(
        self, *, publication_failure: bool, deny_after_publication: bool = False,
        mutate_after_target: bool = False, mutate_environment: bool = False,
    ) -> tuple[CaseRecorder, dict[str, Any] | None]:
        fixture = self.fixture
        plan, identity, method_config = fixture._plan_identity("labram_linear")
        recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/recorder")
        executor = TargetCaseExecutor(
            self.root, recorder,
            admission={"admitted": True, "operator_compute_admitted": True},
            worker="synthetic-publication-test",
        )
        evidence_path = self.root / "runs/phase2/evidence.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("{}", "utf-8")
        events: list[str] = []
        weights_path = self.root / "runs/phase2/selected_sources/weights/synthetic.safetensors"
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        weights_path.write_bytes(b"synthetic-source-weights")
        adapter = attestation_fixture._OutcomeAdapter(
            "labram_linear", fixture._case_outcome(binding=fixture._binding())
        )
        original_predict = adapter.predict_target

        def predict(*args: object, **kwargs: object) -> Any:
            events.append("predict")
            if mutate_after_target:
                weights_path.write_bytes(b"changed-source-weights")
            return original_predict(*args, **kwargs)

        def verify_stable() -> None:
            events.append("stable")
            if weights_path.read_bytes() != b"synthetic-source-weights":
                raise ValueError("selected weights changed after verification")

        def publish(*args: object, **kwargs: object) -> SimpleNamespace:
            events.append("publish")
            if publication_failure:
                raise ValueError("snapshot refused")
            events.append("verify")
            publication = SimpleNamespace(
                manifest_sha256="a" * 64,
                manifest_path=self.root / "runs/phase2/selected_sources/manifests"
                / f"{'a' * 64}.json",
            )
            return SimpleNamespace(
                publication=publication,
                witness=SimpleNamespace(verify_stable=verify_stable),
            )

        original_claim = recorder.claim

        def claim(*args: Any, **kwargs: Any) -> Any:
            events.append("claim")
            return original_claim(*args, **kwargs)

        with (
            patch("evaluation.phase2_pilot.capture_source", return_value=fixture.source),
            patch(
                "evaluation.phase2_pilot.environment_digest",
                side_effect=(
                    [identity.environment_sha256, identity.environment_sha256, "0" * 64]
                    if mutate_environment else None
                ),
                return_value=identity.environment_sha256,
            ),
            patch(
                "evaluation.phase2_pilot.compute_admission",
                side_effect=[
                    {"admitted": True},
                    {"admitted": not deny_after_publication},
                    {"admitted": True},
                ],
            ),
            patch("evaluation.phase2_pilot.state_digest", return_value="f" * 64),
            patch(
                "evaluation.phase2_cho_execution_gate.verify_cho_case_preclaim",
                return_value=self.selection,
            ),
            patch(
                "evaluation.phase2_cho_execution_gate._persisted_record",
                return_value={"sha256": self.evidence_sha},
            ),
            patch("evaluation.phase2_cho_execution_gate.verify_cho_adapter_posttarget"),
            patch(
                "evaluation.phase2_cho_publication_gate.publish_verified_cho_source",
                side_effect=publish,
            ),
            patch(
                "evaluation.phase2_cho_publication_gate._selected_model",
                return_value=self.model,
            ),
            patch.object(adapter, "predict_target", side_effect=predict),
            patch.object(recorder, "claim", side_effect=claim),
        ):
            if (
                publication_failure or deny_after_publication
                or mutate_after_target or mutate_environment
            ):
                pattern = (
                    "snapshot refused" if publication_failure
                    else "admission failed after source publication"
                    if deny_after_publication else "selected weights changed"
                    if mutate_after_target else "source or environment changed"
                )
                with self.assertRaisesRegex(ValueError, pattern):
                    executor.run_case(
                        plan, adapter=adapter, identity=identity,
                        method_config=method_config,
                        selection_evidence_sha256=self.evidence_sha,
                        selection_evidence_path=evidence_path,
                        protocol_config=fixture.config, catalogs=fixture.catalogs,
                        selection_record=fixture.selection_record,
                        episode_record=fixture.episode_record,
                        assets={"subject_01": fixture.asset},
                    )
                self.assertEqual(
                    events,
                    (["publish"] if publication_failure else ["publish", "verify"]
                     if deny_after_publication else
                     ["publish", "verify", "claim", "predict"]
                     if mutate_environment else
                     ["publish", "verify", "claim", "predict", "stable"]),
                )
                self.assertEqual(recorder.completion([plan])["measured"], 0)
                return recorder, None
            result = executor.run_case(
                plan, adapter=adapter, identity=identity,
                method_config=method_config,
                selection_evidence_sha256=self.evidence_sha,
                selection_evidence_path=evidence_path,
                protocol_config=fixture.config, catalogs=fixture.catalogs,
                selection_record=fixture.selection_record,
                episode_record=fixture.episode_record,
                assets={"subject_01": fixture.asset},
            )
        self.assertEqual(events, ["publish", "verify", "claim", "predict", "stable"])
        return recorder, result

    def test_publication_failure_has_no_claim_or_target_prediction(self) -> None:
        self._run_case(publication_failure=True)

    def test_postpublication_admission_failure_has_no_claim_or_prediction(self) -> None:
        self._run_case(publication_failure=False, deny_after_publication=True)

    def test_posttarget_selected_weights_mutation_records_failure_without_cell(self) -> None:
        self._run_case(publication_failure=False, mutate_after_target=True)

    def test_posttarget_environment_change_records_failure_without_cell(self) -> None:
        self._run_case(publication_failure=False, mutate_environment=True)

    def test_manifest_pin_reaches_cell_after_publication_before_claim(self) -> None:
        recorder, result = self._run_case(publication_failure=False)
        assert result is not None
        cell = json.loads(Path(result["cell"]).read_text("utf-8"))
        metrics = cell["payload"]["metrics"]
        self.assertEqual(metrics["selected_source_manifest_sha256"], "a" * 64)
        self.assertEqual(
            metrics["selected_source_manifest_path"],
            f"runs/phase2/selected_sources/manifests/{'a' * 64}.json",
        )
        self.assertEqual(recorder.completion([self.fixture._plan_identity("labram_linear")[0]])[
            "measured"
        ], 1)


if __name__ == "__main__":
    unittest.main()
