from __future__ import annotations

import json
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import test_labram_manifest as fixtures
import torch

from adaptation.anchor_manifest import EATangentAnchorSettings, EEGNetAnchorSettings
from adaptation.labram_manifest import LaBraMTuningSettings
from adaptation.labram_source import (
    BCILaBraMSourceSelector,
    LaBraMSourceCandidate,
    LaBraMSourceSettings,
)
from adaptation.source_selection import (
    BCIEEGNetSourceSelector,
    EEGNetCandidate,
    EEGNetSourceSettings,
)
from adaptation.tcpl_manifest import TCPLManifestRunner
from core.config import config_digest
from core.provenance import capture_source
from encoder.tcpl import TCPLClassifier
from evaluation.labram_parity import state_digest
from evaluation.phase2_pilot import (
    AnchorAdapter,
    CaseOutcome,
    LaBraMTunedAdapter,
    TargetCaseExecutor,
    TCPLAdapter,
    compute_admission,
    machine_snapshot,
)
from evaluation.phase2_profile_binding import BCI_CHANNELS
from evaluation.phase2_protocol import nested_episode
from evaluation.phase2_records import CellIdentity
from evaluation.phase2_runner import (
    CasePlan,
    CaseRecorder,
    environment_digest,
    method_configuration,
)

GIB = 1024**3


METHOD_CONFIG = {
    "optimizer": "sgd_no_momentum_eval_mode",
    "steps": 1,
    "fit_scope": "linear_probe",
    "preprocessing": "profile_b_800_200",
}


def identity(root: Path, config, records, selection_record, **overrides) -> CellIdentity:
    source = capture_source(root)
    catalog = records["subject_01"]["payload"]["catalog"]
    base = dict(
        dataset="bci_iv_2a",
        target_subject="subject_01",
        method="labram_linear",
        shots_per_class=1,
        model_seed=23,
        support_draw_seed=None,
        montage_seed=None,
        protocol_sha256=config_digest(config),
        episode_sha256=records["subject_01"]["sha256"],
        selection_sha256=selection_record["sha256"],
        method_config_sha256=method_configuration(METHOD_CONFIG),
        preprocessing_sha256=catalog["preprocessing_sha256"],
        checkpoint_sha256="f" * 64,
        source_sha256=source.source_sha256,
        environment_sha256=environment_digest(),
        git_commit=source.git_commit,
        git_dirty=source.git_dirty,
    )
    base.update(overrides)
    return CellIdentity(**base)


class Phase2PilotTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.LaBraMManifestTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.LaBraMManifestTests.tearDownClass.__func__)

    def setUp(self):
        fixtures.LaBraMManifestTests.setUp(self)
        self.recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/recorder")
        self.plan = CasePlan("bci_iv_2a", "subject_01", "labram_linear", 1, 23, 1)
        self.manifests = {n: a.profile_a_manifest_sha256 for n, a in self.assets.items()}
        self.admission = compute_admission(
            self.root, operator_admitted=True, disk_free_bytes=100 * GIB,
            gpu_memory_mib=12288, free_host_ram_gib=16.0,
        )
        self.executor = TargetCaseExecutor(
            self.root, self.recorder, admission=self.admission, worker="pilot-tests"
        )

    tearDown = fixtures.LaBraMManifestTests.tearDown

    def fitted_linear_model(self):
        candidate = LaBraMSourceCandidate(
            "linear_a",
            LaBraMSourceSettings("linear", 1, 2, 0.01),
            LaBraMTuningSettings("linear", 1, 0.01),
        )
        selector = BCILaBraMSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, self.model,
            self.assets, outer_target="subject_01",
            template_state_sha256=state_digest(self.model),
            candidates=(candidate,), seed=23, shots_per_class=1, maximum_gradient_steps=64,
        )
        model, fit = selector._fit(candidate, None)
        return model, fit, candidate

    def test_machine_and_compute_admission_fail_closed(self):
        good = machine_snapshot(
            self.root, disk_free_bytes=100 * GIB, gpu_memory_mib=12288,
            free_host_ram_gib=16.0,
        )
        self.assertTrue(good["machine_ok"])
        for overrides in (
            {"disk_free_bytes": 10 * GIB},
            {"gpu_memory_mib": 4096},
        ):
            snapshot = machine_snapshot(self.root, free_host_ram_gib=16.0, **overrides)
            self.assertFalse(snapshot["machine_ok"], overrides)
        self.assertFalse(
            compute_admission(
                self.root, operator_admitted=False, disk_free_bytes=100 * GIB,
                gpu_memory_mib=12288, free_host_ram_gib=16.0,
            )["admitted"]
        )
        self.assertFalse(
            compute_admission(
                self.root, operator_admitted=True, disk_free_bytes=10 * GIB,
                gpu_memory_mib=12288, free_host_ram_gib=16.0,
            )["admitted"]
        )
        self.assertTrue(self.admission["admitted"])
        self.assertEqual(self.admission["probe_cap_minutes"], 10.0)
        self.assertEqual(self.admission["session_cap_minutes"], 120.0)

    def test_plain_labram_case_records_a_verified_cell(self):
        model, fit, candidate = self.fitted_linear_model()
        adapter = LaBraMTunedAdapter("labram_linear", model, candidate.support)
        cell_identity = identity(
            self.root, self.config, self.records, self.selection_record,
            checkpoint_sha256=state_digest(model),
        )
        result = self.executor.run_case(
            self.plan,
            adapter=adapter,
            identity=cell_identity,
            method_config=METHOD_CONFIG,
            selection_evidence_sha256="9" * 64,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            episode_record=self.records["subject_01"],
            assets=self.assets,
        )
        cell_path = Path(result["cell"])
        self.assertEqual(cell_path.name, f"{cell_identity.sha256}.json")
        record = json.loads(cell_path.read_text("utf-8"))
        confusion = record["payload"]["metrics"]["confusion_matrix"]
        rational = (
            sum((Fraction(row[i], sum(row)) for i, row in enumerate(confusion)), start=Fraction())
            / len(confusion)
        )
        self.assertEqual(
            record["payload"]["metrics"]["balanced_accuracy"],
            [rational.numerator, rational.denominator],
        )
        self.assertEqual(record["payload"]["metrics"]["query_count"], 4)
        self.assertEqual(len(record["payload"]["metrics"]["stage_timings_s"]), 3)
        self.assertIn(self.plan.identity_key, self.recorder.measured_identities())
        completion = self.recorder.completion([self.plan])
        self.assertEqual(completion["measured"], 1)
        self.assertEqual(result["confusion_matrix"], confusion)

    def test_refusals_happen_before_any_claim(self):
        model, _, candidate = self.fitted_linear_model()
        adapter = LaBraMTunedAdapter("labram_linear", model, candidate.support)
        good = identity(self.root, self.config, self.records, self.selection_record)
        method_config = {
            "optimizer": "sgd_no_momentum_eval_mode",
            "steps": 1,
            "fit_scope": "linear_probe",
            "preprocessing": "profile_b_800_200",
        }
        arguments = dict(
            adapter=adapter,
            identity=good,
            method_config=method_config,
            selection_evidence_sha256="9" * 64,
            protocol_config=self.config,
            catalogs=self.catalogs,
            selection_record=self.selection_record,
            episode_record=self.records["subject_01"],
            assets=self.assets,
        )
        refused = TargetCaseExecutor(
            self.root, self.recorder,
            admission=compute_admission(
                self.root, operator_admitted=False, disk_free_bytes=100 * GIB,
                gpu_memory_mib=12288, free_host_ram_gib=16.0,
            ),
            worker="pilot-tests",
        )
        with self.assertRaisesRegex(ValueError, "compute admission"):
            refused.run_case(self.plan, **arguments)
        for overrides, pattern in (
            ({"dataset": "cho2017"}, "planned dataset"),
            ({"method": "labram_full"}, "planned method"),
            ({"target_subject": "subject_02"}, "target subject"),
            ({"shots_per_class": 5}, "shot level"),
            ({"model_seed": 71}, "model seed"),
            ({"protocol_sha256": "0" * 64}, "protocol configuration"),
            ({"selection_sha256": "0" * 64}, "source selection"),
            ({"preprocessing_sha256": "0" * 64}, "catalog preprocessing"),
            ({"episode_sha256": "0" * 64}, "episode differs"),
            ({"environment_sha256": "1" * 64}, "live source or environment"),
        ):
            with self.subTest(overrides=overrides), self.assertRaisesRegex(ValueError, pattern):
                self.executor.run_case(
                    self.plan, **{**arguments, "identity": identity(
                        self.root, self.config, self.records,
                        self.selection_record, **overrides,
                    )}
                )
        with self.assertRaisesRegex(ValueError, "method configuration"):
            self.executor.run_case(
                self.plan, **{**arguments, "method_config": {**method_config, "steps": 2}}
            )
        with self.assertRaisesRegex(ValueError, "trial catalog dataset"):
            self.executor.run_case(
                self.plan, **{**arguments, "catalogs": (
                    replace(self.catalogs[0], dataset="cho2017"), *self.catalogs[1:]
                )}
            )
        with self.assertRaisesRegex(ValueError, "source selection"):
            self.executor.run_case(
                self.plan, **{**arguments, "selection_record": {
                    **self.selection_record, "sha256": "0" * 64,
                }}
            )
        with self.assertRaisesRegex(ValueError, "target episode"):
            self.executor.run_case(
                self.plan, **{**arguments, "episode_record": {
                    **self.records["subject_01"], "sha256": "0" * 64,
                }}
            )
        claims = list((self.root / "runs/phase2/recorder/claims").glob("*.json"))
        self.assertEqual(claims, [])

    def test_checkpoint_mismatch_records_failure_without_cell(self):
        class WrongCheckpointAdapter:
            method = "labram_linear"

            def predict_target(self, *args, **kwargs):
                return CaseOutcome(
                    torch.empty((0, 4)), torch.empty(0, dtype=torch.long),
                    (), (), self_episode_sha, "e" * 64, (0.0,),
                )

        self_episode_sha = self.records["subject_01"]["sha256"]
        with self.assertRaisesRegex(ValueError, "predicted checkpoint"):
            self.executor.run_case(
                self.plan,
                adapter=WrongCheckpointAdapter(),
                identity=identity(self.root, self.config, self.records, self.selection_record),
                method_config=METHOD_CONFIG,
                selection_evidence_sha256="9" * 64,
                protocol_config=self.config,
                catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.records["subject_01"],
                assets=self.assets,
            )
        completion = self.recorder.completion([self.plan])
        self.assertEqual(completion["failed"], 1)
        self.assertEqual(completion["measured"], 0)

    def test_mismatched_prediction_partition_never_publishes_cell(self):
        catalog = next(c for c in self.catalogs if c.subject == "subject_01")
        episode = nested_episode(
            catalog, shots=(1, 5, 10, 20), protocol_sha256=config_digest(self.config)
        )
        partition = episode.partition(1)
        support = tuple(catalog.trial_ids[index] for index in partition.support_indices)
        query = tuple(catalog.trial_ids[index] for index in partition.query_indices)
        targets = tuple(
            catalog.classes.index(catalog.labels[index]) for index in partition.query_indices
        )

        class OutcomeAdapter:
            method = "labram_linear"

            def __init__(self, outcome):
                self.outcome = outcome

            def predict_target(self, *args, **kwargs):
                return self.outcome

        cases = (
            ((), query, targets, "support identities"),
            (support, tuple(reversed(query)), targets, "query identities"),
            (support, query, ((targets[0] + 1) % len(catalog.classes), *targets[1:]),
             "target rows"),
        )
        for repetition, (support_ids, query_ids, target_values, pattern) in enumerate(
            cases, start=1
        ):
            plan = replace(self.plan, repetition=repetition)
            outcome = CaseOutcome(
                torch.zeros((len(query), len(catalog.classes))),
                torch.tensor(target_values, dtype=torch.long),
                support_ids, query_ids, self.records["subject_01"]["sha256"],
                "f" * 64, (0.0,),
            )
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ValueError, pattern):
                self.executor.run_case(
                    plan,
                    adapter=OutcomeAdapter(outcome),
                    identity=identity(
                        self.root, self.config, self.records, self.selection_record
                    ),
                    method_config=METHOD_CONFIG,
                    selection_evidence_sha256="9" * 64,
                    protocol_config=self.config,
                    catalogs=self.catalogs,
                    selection_record=self.selection_record,
                    episode_record=self.records["subject_01"],
                    assets=self.assets,
                )
            self.assertEqual(self.recorder.completion([plan])["measured"], 0)

    def test_case_failures_are_recorded_and_capped(self):
        model, _, candidate = self.fitted_linear_model()

        with (
            patch("evaluation.phase2_pilot._metrics", side_effect=RuntimeError("adapter exploded")),
            self.assertRaises(RuntimeError),
        ):
            self.executor.run_case(
                self.plan,
                adapter=LaBraMTunedAdapter("labram_linear", model, candidate.support),
                identity=identity(
                    self.root, self.config, self.records, self.selection_record,
                    checkpoint_sha256=state_digest(model),
                ),
                method_config=METHOD_CONFIG,
                selection_evidence_sha256="9" * 64,
                protocol_config=self.config,
                catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.records["subject_01"],
                assets=self.assets,
            )
        completion = self.recorder.completion([self.plan])
        self.assertEqual(completion["failed"], 1)
        self.assertEqual(completion["measured"], 0)
        tiny = dict(self.admission, probe_cap_minutes=1e-9, admitted=True)
        capped = TargetCaseExecutor(self.root, self.recorder, admission=tiny, worker="pilot-tests")
        adapter = LaBraMTunedAdapter("labram_linear", model, candidate.support)
        probe_plan = CasePlan("bci_iv_2a", "subject_01", "labram_linear", 1, 23, 2)
        with self.assertRaisesRegex(ValueError, "probe cap"):
            capped.run_case(
                probe_plan,
                adapter=adapter,
                identity=identity(
                    self.root, self.config, self.records, self.selection_record,
                    checkpoint_sha256=state_digest(model),
                ),
                method_config=METHOD_CONFIG,
                selection_evidence_sha256="9" * 64,
                protocol_config=self.config,
                catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.records["subject_01"],
                assets=self.assets,
            )
        expired = dict(self.admission, session_cap_minutes=1e-9, admitted=True)
        session_capped = TargetCaseExecutor(
            self.root, self.recorder, admission=expired, worker="pilot-tests"
        )
        session_plan = CasePlan("bci_iv_2a", "subject_01", "labram_linear", 1, 23, 3)
        with self.assertRaisesRegex(ValueError, "session cap"):
            session_capped.run_case(
                session_plan,
                adapter=adapter,
                identity=identity(self.root, self.config, self.records, self.selection_record),
                method_config=METHOD_CONFIG,
                selection_evidence_sha256="9" * 64,
                protocol_config=self.config,
                catalogs=self.catalogs,
                selection_record=self.selection_record,
                episode_record=self.records["subject_01"],
                assets=self.assets,
            )

    def test_ea_and_eegnet_anchor_adapters_predict_the_outer_target(self):
        for method, settings, model in (
            ("ea_tangent_lr", EATangentAnchorSettings(1e-6, 1.0, 1000, 2), None),
            (
                "eegnet",
                EEGNetAnchorSettings(1, 0.001, 1e6, 2),
                self.fitted_eegnet(),
            ),
        ):
            with self.subTest(method=method):
                adapter = AnchorAdapter(method, settings, model)
                outcome = adapter.predict_target(
                    self.root,
                    self.config,
                    self.catalogs,
                    self.selection_record,
                    self.manifests,
                    self.records["subject_01"],
                    outer_target="subject_01",
                    shots_per_class=1,
                )
                self.assertEqual(outcome.logits.shape, (4, 4))
                self.assertTrue(torch.isfinite(outcome.logits).all())
                self.assertEqual(outcome.query_trial_ids, tuple(self.episode_query_ids()))
                self.assertEqual(len(outcome.episode_sha256), 64)

    def fitted_eegnet(self):
        candidate = EEGNetCandidate(
            "eegnet_a",
            EEGNetSourceSettings(1, 4, 0.001, 1e6),
            EEGNetAnchorSettings(1, 0.001, 1e6, 2),
        )
        selector = BCIEEGNetSourceSelector(
            self.root, self.config, self.catalogs, self.selection_record, self.manifests,
            outer_target="subject_01", candidates=(candidate,), seed=23,
            shots_per_class=1, maximum_gradient_steps=64,
        )
        model, _ = selector._fit(candidate, None)
        return model

    def episode_query_ids(self):
        from evaluation.phase2_protocol import nested_episode

        catalog = next(c for c in self.catalogs if c.subject == "subject_01")
        manifest = nested_episode(
            catalog, shots=(1, 5, 10, 20),
            protocol_sha256=config_digest(self.config),
        )
        return [catalog.trial_ids[i] for i in manifest.partition(1).query_indices]

    def test_tcpl_adapter_requires_a_final_outer_role_runner(self):
        template = TCPLClassifier(len(BCI_CHANNELS), 4)
        inner = TCPLManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, template,
            outer_target="subject_01", channel_names=BCI_CHANNELS,
            validation_subject="subject_02",
        )
        with self.assertRaisesRegex(ValueError, "final outer-role"):
            TCPLAdapter(inner)
        final = TCPLManifestRunner(
            self.root, self.config, self.catalogs, self.selection_record, template,
            outer_target="subject_01", channel_names=BCI_CHANNELS,
        )
        adapter = TCPLAdapter(final, query_batch_size=2)
        outcome = adapter.predict_target(
            self.root, self.config, self.catalogs, self.selection_record, {},
            self.records["subject_01"],
            outer_target="subject_01", shots_per_class=1,
        )
        self.assertEqual(outcome.logits.shape, (4, 4))
        self.assertEqual(len(outcome.checkpoint_sha256), 64)


if __name__ == "__main__":
    unittest.main()
