"""Pre-claim Cho selector, adapter and static method-configuration binding."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import torch
from torch import nn

from adaptation.anchor_manifest import EEGNetAnchorSettings
from adaptation.labram_lora_trained import LoRAContinuationSettings, LoRASourceSettings
from adaptation.labram_manifest import LaBraMTuningSettings
from core.config import canonical_config_json, config_digest, load_toml
from core.provenance import SourceProvenance
from evaluation.labram_parity import state_digest
from evaluation.phase2_cho_execution_gate import (
    _persisted_record,
    verify_cho_adapter_posttarget,
    verify_cho_case_preclaim,
)
from evaluation.phase2_factored_evidence import pack_factored_selection
from evaluation.phase2_pilot import (
    AnchorAdapter,
    LaBraMTunedAdapter,
    TargetCaseExecutor,
    TrainedLaBraMAdapter,
)
from evaluation.phase2_profile_binding import ChoProfileAssets60Hz
from evaluation.phase2_protocol import TrialCatalog, nested_episode, source_selection
from evaluation.phase2_records import CellIdentity, envelope
from evaluation.phase2_runner import (
    CasePlan,
    CaseRecorder,
    environment_digest,
    method_configuration,
)
from evaluation.phase2_selection_evidence_binding import VerifiedChoSelection
from scripts.audit_phase2_protocol import validate_protocol


class ChoExecutionGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.model = nn.Linear(2, 2)
        self.checkpoint = state_digest(self.model)

    def setup_case(self, method: str):
        plan = CasePlan("cho2017", "subject_01", method, 5, 11, 1)
        if method in {"labram_linear", "labram_full"}:
            short = method.removeprefix("labram_")
            support = LaBraMTuningSettings(short, 1, 0.001)
            adapter = LaBraMTunedAdapter(method, self.model, support)
            source_settings = {
                "method": short, "steps_per_subject": 1, "batch_size": 2,
                "learning_rate": 0.001, "partial_depth": None,
            }
            assets = {
                f"subject_{number:02d}": ChoProfileAssets60Hz("3" * 64, "4" * 64, "5" * 64)
                for number in range(1, 53)
            }
        elif method == "labram_lora":
            source = LoRASourceSettings(
                ("backbone.blocks.0.attn.qkv",), 4, 1.0, 11, True, 1, 2, 0.001
            )
            support = LoRAContinuationSettings(True, 1, 0.001)
            adapter = TrainedLaBraMAdapter(method, self.model, source, support)
            source_settings = asdict(source)
            assets = {
                f"subject_{number:02d}": ChoProfileAssets60Hz("3" * 64, "4" * 64, "5" * 64)
                for number in range(1, 53)
            }
        else:
            support = EEGNetAnchorSettings(1, 0.001, 1000000.0)
            adapter = AnchorAdapter("eegnet", support, self.model)
            source_settings = {
                "steps_per_subject": 1, "batch_size": 4,
                "learning_rate": 0.001, "input_scale": 1000000.0,
            }
            assets = {}
        candidate = {"name": "candidate_0", "source": source_settings, "support": asdict(support)}
        second = copy.deepcopy(candidate)
        second["name"] = "candidate_1"
        second["source"]["learning_rate"] = 0.002
        second["support"]["learning_rate"] = 0.002
        record = envelope("engineering_smoke", {
            "contract": {"candidates": [candidate, second]},
            "selected_candidate": "candidate_0",
        })
        path = self.root / "runs/phase2/selection/record.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((canonical_config_json(record) + "\n").encode("utf-8"))
        roster = copy.deepcopy([candidate, second])
        if method == "labram_lora":
            for row in roster:
                row["source"]["seed"] = "$case_model_seed"
        method_config = {
            "method": method, "dataset": "cho2017",
            "input_profile": "cho_profile_a" if method == "eegnet" else "cho_profile_b_60hz_v1",
            "variant_config_sha256": None if method == "eegnet" else "5" * 64,
            "candidates": roster,
            "source_seed_policy": "case_model_seed" if method == "labram_lora" else "none",
            "source_policy": "all_non_target_subjects; inner_validation_also_excluded",
            "score": "mean_subject_balanced_accuracy_exact_rational",
            "tie_break": "first_in_declared_candidate_order", "early_stopping": False,
        }
        identity = CellIdentity(
            "cho2017", "subject_01", method, 5, 11, None, None,
            "1" * 64, "2" * 64, "3" * 64, config_digest(method_config),
            "4" * 64, self.checkpoint, "5" * 64, "6" * 64, "7" * 40, True,
        )
        arguments = {
            "root": self.root, "plan": plan, "adapter": adapter, "identity": identity,
            "method_config": method_config, "evidence_path": path,
            "evidence_sha256": record["sha256"], "protocol_config": {}, "catalogs": (),
            "selection_record": {}, "assets": assets,
        }
        return arguments, record

    def test_four_methods_bind_persisted_record_and_static_roster(self) -> None:
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            with self.subTest(method=method):
                arguments, _ = self.setup_case(method)
                with (
                    patch("evaluation.phase2_cho_execution_gate.validate_trained_lora"),
                    patch(
                        "evaluation.phase2_cho_execution_gate.verify_cho_selection_evidence",
                        return_value=VerifiedChoSelection(
                            "candidate_0", arguments["evidence_sha256"]
                        ),
                    ) as verifier,
                ):
                    result = verify_cho_case_preclaim(**arguments)
                self.assertEqual(result.selected_candidate, "candidate_0")
                self.assertEqual(
                    verifier.call_args.kwargs["adapter_model_state_sha256"], self.checkpoint
                )

    def test_missing_or_noncanonical_evidence_refuses_before_verifier(self) -> None:
        arguments, record = self.setup_case("eegnet")
        path = arguments["evidence_path"]
        path.write_bytes(canonical_config_json(record).encode("utf-8"))
        with patch(
            "evaluation.phase2_cho_execution_gate.verify_cho_selection_evidence"
        ) as verifier:
            with self.assertRaisesRegex(ValueError, "canonical"):
                verify_cho_case_preclaim(**arguments)
            verifier.assert_not_called()
        path.unlink()
        with self.assertRaisesRegex(ValueError, "persisted file"):
            verify_cho_case_preclaim(**arguments)

    def test_canonical_evidence_byte_limit_is_checked_before_parse(self) -> None:
        arguments, _ = self.setup_case("eegnet")
        path = arguments["evidence_path"]
        with (
            patch(
                "evaluation.phase2_cho_execution_gate.MAXIMUM_LOGICAL_BYTES",
                path.stat().st_size - 1,
            ),
            self.assertRaisesRegex(ValueError, "record size or link count"),
        ):
            _persisted_record(self.root, path, arguments["evidence_sha256"])

    def test_canonical_evidence_hardlink_is_refused(self) -> None:
        arguments, _ = self.setup_case("eegnet")
        path = arguments["evidence_path"]
        alias = path.with_name("selection-evidence-alias.json")
        try:
            os.link(path, alias)
        except OSError as error:
            self.skipTest(f"hard links unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "record size or link count"):
            _persisted_record(self.root, path, arguments["evidence_sha256"])

    def test_factored_store_evidence_path_reconstructs_exact_logical_record(self) -> None:
        project = Path(__file__).resolve().parents[1]
        historical = (
            project / "runs/phase2/source_selection_checks/20260908_step20/"
            "engineering_selection.json"
        )
        if not historical.is_file():
            self.skipTest("bounded selection example is unavailable")
        record = json.loads(historical.read_bytes())
        packed = pack_factored_selection(record)
        physical_sha = hashlib.sha256(packed).hexdigest()
        directory = self.root / "runs/phase2/selected_sources/evidence"
        directory.mkdir(parents=True)
        (directory.parent / "weights").mkdir()
        (directory.parent / "manifests").mkdir()
        path = directory / f"{physical_sha}.factored.json"
        path.write_bytes(packed)
        self.assertEqual(
            _persisted_record(self.root, path, record["sha256"]), record,
        )
        arguments, _ = self.setup_case("eegnet")
        selected = next(
            row for row in record["payload"]["contract"]["candidates"]
            if row["name"] == record["payload"]["selected_candidate"]
        )
        arguments.update({
            "adapter": AnchorAdapter(
                "eegnet", EEGNetAnchorSettings(**selected["support"]), self.model,
            ),
            "evidence_path": path,
            "evidence_sha256": record["sha256"],
        })
        with patch("evaluation.phase2_cho_execution_gate._method_config"), patch(
            "evaluation.phase2_cho_execution_gate.verify_cho_selection_evidence",
            return_value=VerifiedChoSelection(
                selected["name"], record["sha256"],
            ),
        ) as verifier:
            verify_cho_case_preclaim(**arguments)
        self.assertEqual(verifier.call_args.kwargs["record"], record)
        with self.assertRaisesRegex(ValueError, "external envelope pin"):
            _persisted_record(self.root, path, "0" * 64)
        path.write_bytes(packed + b" ")
        with self.assertRaisesRegex(ValueError, "file hash differs"):
            _persisted_record(self.root, path, record["sha256"])

    def test_canonical_evidence_with_stale_envelope_digest_refuses(self) -> None:
        arguments, record = self.setup_case("eegnet")
        record["payload"]["selected_candidate"] = "candidate_1"
        arguments["evidence_path"].write_bytes(
            (canonical_config_json(record) + "\n").encode("utf-8")
        )
        with patch(
            "evaluation.phase2_cho_execution_gate.verify_cho_selection_evidence"
        ) as verifier:
            with self.assertRaisesRegex(ValueError, "envelope"):
                verify_cho_case_preclaim(**arguments)
            verifier.assert_not_called()

    def test_posttarget_live_model_and_settings_must_still_match(self) -> None:
        arguments, record = self.setup_case("eegnet")
        post = {
            "plan": arguments["plan"], "adapter": arguments["adapter"],
            "identity": arguments["identity"], "evidence_record": record,
        }
        verify_cho_adapter_posttarget(**post)
        with torch.no_grad():
            self.model.weight.add_(1)
        with self.assertRaisesRegex(ValueError, "model changed"):
            verify_cho_adapter_posttarget(**post)
        self.model = nn.Linear(2, 2)
        self.checkpoint = state_digest(self.model)
        arguments, record = self.setup_case("eegnet")
        arguments["adapter"]._settings = EEGNetAnchorSettings(2, 0.001, 1000000.0)
        with self.assertRaisesRegex(ValueError, "settings changed"):
            verify_cho_adapter_posttarget(
                plan=arguments["plan"], adapter=arguments["adapter"],
                identity=arguments["identity"], evidence_record=record,
            )

    def test_model_roster_and_adapter_mismatch_refuse(self) -> None:
        arguments, _ = self.setup_case("labram_lora")
        lora_validation = patch("evaluation.phase2_cho_execution_gate.validate_trained_lora")
        lora_validation.start()
        self.addCleanup(lora_validation.stop)
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            verify_cho_case_preclaim(**{
                **arguments, "identity": CellIdentity(
                    "cho2017", "subject_01", "labram_lora", 5, 11, None, None,
                    "1" * 64, "2" * 64, "3" * 64,
                    config_digest(arguments["method_config"]), "4" * 64,
                    "0" * 64, "5" * 64, "6" * 64, "7" * 40, True,
                ),
            })
        changed = dict(arguments["method_config"])
        changed["source_seed_policy"] = "none"
        with self.assertRaisesRegex(ValueError, "method configuration"):
            verify_cho_case_preclaim(**{**arguments, "method_config": changed})
        other, _ = self.setup_case("eegnet")
        arguments, _ = self.setup_case("labram_lora")
        with self.assertRaisesRegex(ValueError, "LoRA adapter"):
            verify_cho_case_preclaim(**{**arguments, "adapter": other["adapter"]})

    def test_static_cho_method_config_refuses_missing_roster_and_seed_policy(self) -> None:
        for method in ("labram_linear", "labram_lora", "labram_full", "eegnet"):
            with self.subTest(method=method):
                arguments, _ = self.setup_case(method)
                good = arguments["method_config"]
                self.assertEqual(method_configuration(good), config_digest(good))
                short = {**good, "candidates": good["candidates"][:1]}
                with self.assertRaisesRegex(ValueError, "two ordered candidates"):
                    method_configuration(short)
                extra = {**good, "selected_candidate": "candidate_0"}
                with self.assertRaisesRegex(ValueError, "static schema"):
                    method_configuration(extra)
                if method == "labram_lora":
                    numeric = copy.deepcopy(good)
                    numeric["candidates"][0]["source"]["seed"] = 11
                    with self.assertRaisesRegex(ValueError, "static case template"):
                        method_configuration(numeric)

    def test_executor_refuses_missing_cho_evidence_before_claim(self) -> None:
        arguments, _ = self.setup_case("eegnet")
        config = load_toml("configs/phase2/protocol.toml")
        catalogs = tuple(
            TrialCatalog(
                "cho2017", f"subject_{number:02d}",
                tuple(f"subject_{number:02d}/trial_{index:02d}" for index in range(42)),
                ("left_hand", "right_hand") * 21,
                ("left_hand", "right_hand"), "1" * 64, "2" * 64,
            )
            for number in range(1, 53)
        )
        selection_record = envelope(
            "source_selection", asdict(source_selection(catalogs, target="subject_01"))
        )
        episode = nested_episode(
            catalogs[0], shots=validate_protocol(config), protocol_sha256=config_digest(config)
        )
        episode_record = envelope("episode_manifest", episode.payload())
        source = SourceProvenance("7" * 40, "5" * 64, False)
        identity = CellIdentity(
            "cho2017", "subject_01", "eegnet", 5, 11, None, None,
            config_digest(config), episode_record["sha256"], selection_record["sha256"],
            config_digest(arguments["method_config"]), catalogs[0].preprocessing_sha256,
            self.checkpoint, source.source_sha256, environment_digest(),
            source.git_commit, False,
        )
        recorder = CaseRecorder(self.root, output_root=self.root / "runs/phase2/recorder")
        executor = TargetCaseExecutor(
            self.root, recorder,
            admission={"admitted": True, "operator_compute_admitted": True},
            worker="gate-test",
        )
        with (
            patch("evaluation.phase2_pilot.capture_source", return_value=source),
            self.assertRaisesRegex(ValueError, "persisted Cho selection evidence"),
        ):
            executor.run_case(
                arguments["plan"], adapter=arguments["adapter"], identity=identity,
                method_config=arguments["method_config"],
                selection_evidence_sha256=arguments["evidence_sha256"],
                protocol_config=config, catalogs=catalogs,
                selection_record=selection_record, episode_record=episode_record,
                assets={},
            )
        self.assertEqual(list((self.root / "runs/phase2/recorder/claims").glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
