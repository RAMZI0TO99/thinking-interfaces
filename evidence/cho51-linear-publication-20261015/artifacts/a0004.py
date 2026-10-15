"""Fabricated contract-boundary cases; no I/O, models, fitting or proof authority.

The admitted publication child runs these once.  The dummy new-origin pin below
is syntax-only metadata and never authenticates an actual origin file.
"""

from __future__ import annotations

import copy
import json
import unittest

from docs.phase2.cho51_linear_publication_v1 import contract as C


def artifact(path, sha256, size):
    return {"path": path, "file_sha256": sha256, "size_bytes": size}


def valid_contract():
    root = r"D:\Aenv\pro3"
    run = root + r"\runs\coordination\cho51_linear_publication_20261015_v1"
    chain = root + r"\runs\coordination\cho51_linear_chain_20261015_v1"
    final = chain + r"\fragments\fragment_007"
    return {
        "schema": "cho51_linear_staged_publication_contract_v1",
        "architecture_root": root, "evidence_root": run + r"\publication_001\project",
        "origin_fixture_root": root + r"\runs\coordination\cho51_linear_lineage_20261015_v2\validation_001\fixture",
        "publication_output": run + r"\publication_001", "detached_output": run + r"\restoration_001",
        "origin_path": run + r"\origin-contract.json", "origin_file_sha256": "a" * 64,
        "source_artifacts": {
            "checkpoint": artifact(final + r"\selected-source.safetensors",
                "3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048", 23294624),
            "evidence": artifact(final + r"\selection-evidence.json",
                "e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3", 23087023),
            "state_schema": artifact(final + r"\selected-state-schema.json",
                "d9a276bb86322512fa87f90e06351c6f8552d63490b25f85968ebcbe1cbc68b4", 20594),
            "method_config": artifact(chain + r"\method-config.json",
                "37b07825274a45d0703bba56387aa75c42e612d84066996d4a3a8bf44cdd42af", 886),
            "final_review": artifact(chain + r"\final-review.json",
                "cc1917e786e81092443d6a90c2be9708ea5ef034deb3bcb43572b23e6a887b8a", 186353),
            "pins": artifact(chain + r"\pins.json",
                "1e3776fd84c22fdba9d36c97113ca1fb90ec5912018cfdcdd0c4cfcaa264be2e", 235853),
            "chain7": artifact(chain + r"\chains\chain_007.json",
                "20375fcf55818d9f2ec4f57a29f2ce6490dff35029896189e56ca251d306c1d7", 14616),
        },
        "case": {"dataset": "cho2017", "target_subject": "subject_02", "method": "labram_linear",
                 "shots_per_class": 5, "model_seed": 11, "repetition": 1},
        "selected_candidate": "lr_1e-3",
        "canonical_source_sha256": "3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529",
        "evidence_source_sha256": "9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299",
        "five_tomls": {
            "configs/base.toml": "02c8e3011abfcafe170f791ec688c791b2187d8e547dd3b2655bae2b5eedf2c4",
            "configs/benchmark.toml": "2dba370f37039cbee73726c407b7377ad9933385a1acab30f21cceca7bd369b5",
            "configs/phase2/cho_profile_b_60hz.toml": "6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3",
            "configs/phase2/protocol.toml": "d8b56cdb28c7cbf3999e9fc65f089535930bff23373ddf46b903695cf095fa95",
            "configs/phase2/selection_ceiling.toml": "a7db3ba233c71ff73c5599baa2f48ffb7616deb1c239b7bbfc41b6ac8e466548",
        },
        "historical_gradient_updates": 5253, "current_gradient_updates": 0, "complete_folds": 102,
        "source_policy": "two_root_staged_bridge", "public_single_root_factory_qualified": False,
        "publication_stage_qualified": False, "detached_stage_qualified": False,
        "scientific_admission": False, "original_case_attempts": 0,
        "limits": {"ordinary_json_bytes": 8388608, "complete_evidence_json_bytes": 33554432,
                   "checkpoint_bytes": 67108864},
    }


class StageContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = valid_contract()

    def reject(self):
        with self.assertRaises(ValueError):
            C.validate_stage_contract(self.contract)

    def test_valid_staging_keeps_roots_roles_and_authority_separate(self):
        self.assertIsNone(C.validate_stage_contract(self.contract))
        self.assertEqual(len({self.contract[k] for k in
            ("architecture_root", "evidence_root", "origin_fixture_root")}), 3)
        self.assertEqual((self.contract["historical_gradient_updates"], self.contract["current_gradient_updates"]),
                         (5253, 0))
        for key in ("public_single_root_factory_qualified", "publication_stage_qualified",
                    "detached_stage_qualified", "scientific_admission"):
            self.assertIs(self.contract[key], False)

    def test_validation_preserves_input_and_accepts_detached_json(self):
        before = copy.deepcopy(self.contract)
        C.validate_stage_contract(self.contract)
        C.validate_stage_contract(json.loads(json.dumps(self.contract)))
        self.assertEqual(self.contract, before)

    def test_missing_and_unknown_top_level_fields_refused(self):
        del self.contract["evidence_root"]
        self.reject()
        self.contract = valid_contract(); self.contract["high_level_restore_passed"] = True
        self.reject()

    def test_architecture_and_evidence_roots_cannot_be_swapped(self):
        self.contract["architecture_root"], self.contract["evidence_root"] = (
            self.contract["evidence_root"], self.contract["architecture_root"])
        self.reject()

    def test_original_fixture_cannot_become_the_writable_evidence_root(self):
        self.contract["evidence_root"] = self.contract["origin_fixture_root"]
        self.reject()

    def test_root_aliases_and_escaping_paths_refused(self):
        for key, value in (("architecture_root", "D:/Aenv/pro3"),
                           ("evidence_root", C.PUBLICATION_OUTPUT + r"\other\..\project"),
                           ("origin_fixture_root", C.ORIGIN_FIXTURE_ROOT + r"\..")):
            self.contract = valid_contract(); self.contract[key] = value
            self.reject()

    def test_stage_outputs_and_original_source_paths_cannot_be_repurposed(self):
        self.contract["detached_output"] = self.contract["publication_output"]
        self.reject()
        self.contract = valid_contract()
        self.contract["source_artifacts"]["checkpoint"]["path"] = C.PUBLICATION_OUTPUT + r"\selected-source.safetensors"
        self.reject()

    def test_evidence_and_checkpoint_source_roles_cannot_be_swapped(self):
        artifacts = self.contract["source_artifacts"]
        artifacts["checkpoint"], artifacts["evidence"] = artifacts["evidence"], artifacts["checkpoint"]
        self.reject()

    def test_substituted_external_historical_pins_refused(self):
        for name in self.contract["source_artifacts"]:
            self.contract = valid_contract()
            self.contract["source_artifacts"][name]["file_sha256"] = "f" * 64
            self.reject()

    def test_missing_extra_and_untyped_source_artifact_fields_refused(self):
        del self.contract["source_artifacts"]["final_review"]
        self.reject()
        self.contract = valid_contract(); self.contract["source_artifacts"]["caller_claim"] = {}
        self.reject()
        self.contract = valid_contract(); self.contract["source_artifacts"]["checkpoint"]["published"] = True
        self.reject()

    def test_artifact_size_and_boolean_integer_substitutions_refused(self):
        for name, value in (("checkpoint", 67108865), ("evidence", 33554433),
                            ("final_review", True), ("method_config", -1)):
            self.contract = valid_contract(); self.contract["source_artifacts"][name]["size_bytes"] = value
            self.reject()

    def test_wrong_case_method_target_seed_shot_or_repetition_refused(self):
        for key, value in (("dataset", "bci_iv_2a"), ("target_subject", "subject_01"),
                           ("method", "labram_lora"), ("shots_per_class", 10),
                           ("model_seed", 23), ("repetition", True)):
            self.contract = valid_contract(); self.contract["case"][key] = value
            self.reject()

    def test_a_new_or_uncomputed_winner_cannot_replace_the_accepted_winner(self):
        self.contract["selected_candidate"] = "lr_2e-3"
        self.reject()

    def test_refit_or_reclassified_historical_work_refused(self):
        for key, value in (("current_gradient_updates", 1), ("historical_gradient_updates", 0),
                           ("complete_folds", 100), ("current_gradient_updates", False)):
            self.contract = valid_contract(); self.contract[key] = value
            self.reject()

    def test_request_cannot_claim_public_high_level_or_stage_success(self):
        for key in ("public_single_root_factory_qualified", "publication_stage_qualified", "detached_stage_qualified"):
            self.contract = valid_contract(); self.contract[key] = True
            self.reject()

    def test_scientific_admission_or_original_case_retry_refused(self):
        self.contract["scientific_admission"] = True
        self.reject()
        self.contract = valid_contract(); self.contract["original_case_attempts"] = 1
        self.reject()

    def test_ordinary_evidence_and_checkpoint_ceilings_cannot_be_widened(self):
        for key in self.contract["limits"]:
            self.contract = valid_contract(); self.contract["limits"][key] *= 2
            self.reject()
        self.contract = valid_contract(); self.contract["limits"]["ordinary_json_bytes"] = True
        self.reject()

    def test_mirror_source_context_and_five_config_inventory_are_fixed(self):
        self.contract["evidence_source_sha256"] = self.contract["canonical_source_sha256"]
        self.reject()
        self.contract = valid_contract(); del self.contract["five_tomls"]["configs/base.toml"]
        self.reject()
        self.contract = valid_contract(); self.contract["five_tomls"]["configs/unused.toml"] = "a" * 64
        self.reject()
        self.contract = valid_contract(); self.contract["five_tomls"]["configs/base.toml"] = "b" * 64
        self.reject()

    def test_new_origin_pin_requires_exact_path_and_physical_digest_syntax(self):
        self.contract["origin_path"] = C.ORIGIN_FIXTURE_ROOT + r"\origin-contract.json"
        self.reject()
        for value in (True, "A" * 64, "a" * 32, None):
            self.contract = valid_contract(); self.contract["origin_file_sha256"] = value
            self.reject()

    def test_non_plain_or_nonfinite_json_inputs_refused(self):
        for value in (None, [], True):
            with self.assertRaises(ValueError):
                C.validate_stage_contract(value)
        self.contract["current_gradient_updates"] = float("nan")
        self.reject()
        self.contract = valid_contract(); self.contract["five_tomls"] = object()
        self.reject()


if __name__ == "__main__":
    unittest.main()
