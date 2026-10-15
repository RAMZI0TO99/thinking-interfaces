"""Fabricated chain-planning cases, with no native execution or model evidence.

Run only inside the admitted guarded child.  Fake leaf digests in these cases
exercise metadata consistency; they never authenticate execution or fold reuse.
"""

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from docs.phase2.cho51_linear_chain_v1 import plan as P


PINS = hashlib.sha256(b"fabricated fixed reviewed bundle").hexdigest()
ORIGIN = hashlib.sha256(b"fabricated root origin file").hexdigest()


def sha(label):
    return hashlib.sha256(label.encode()).hexdigest()


def initial():
    return {
        "schema": "cho51_linear_chain_metadata_v1", "root_origin_sha256": ORIGIN,
        "pins_sha256": PINS, "chain_index": 0, "leaves": [],
        "accepted_pairs": [
            {"candidate": candidate, "validation_subject": f"subject_{number:02d}"}
            for candidate in ("lr_1e-3", "lr_2e-3") for number in (1, 3, 4, 5, 6)
        ],
        "head_sha256": ORIGIN, "complete": False,
    }


def request(chain):
    return P.next_request(chain, pins_sha256=PINS, root_origin_sha256=ORIGIN)


def descriptor(chain):
    planned = request(chain)
    encoded = (json.dumps(planned, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    return {
        "index": planned["index"],
        "path": "runs/coordination/cho51_linear_chain_20261015_v1"
                + f"/fragments/fragment_{planned['index']:03d}/leaf.json",
        "sha256": sha("fabricated immutable native leaf " + str(planned["index"])),
        "request_sha256": hashlib.sha256(encoded).hexdigest(),
        "parent_head_sha256": chain["head_sha256"], "mode": planned["mode"],
        "pairs": copy.deepcopy(planned["pairs"]),
        "accepted_folds_before": planned["prior_folds"],
        "accepted_folds_after": planned["prior_folds"] + len(planned["pairs"]),
    }


def progress(index):
    chain = initial()
    for _ in range(index):
        chain = P.advance_chain(chain, descriptor(chain))
    return chain


class ChainPlanTests(unittest.TestCase):
    def setUp(self):
        self.chain = initial()

    def validate(self, planned, chain=None):
        return P.validate_request(planned, self.chain if chain is None else chain,
                                  pins_sha256=PINS, root_origin_sha256=ORIGIN)

    def reject_descriptor(self, leaf):
        with self.assertRaises(ValueError):
            P.advance_chain(self.chain, leaf)

    def test_logical_json_encoding_and_key_order(self):
        self.assertEqual(P.logical({"b": 2, "a": 1}), hashlib.sha256(b'{"a":1,"b":2}').hexdigest())
        self.assertEqual(P.logical({"a": 1, "b": 2}), P.logical({"b": 2, "a": 1}))
        self.assertNotEqual(P.logical({"a": True}), P.logical({"a": 1}))

    def test_logical_rejects_nonfinite_or_non_json_values(self):
        for value in ({"x": float("nan")}, {"x": float("inf")}, {1: "non-string key"}, (1, 2), {"x": object()}):
            with self.assertRaises(ValueError):
                P.logical(value)

    def test_initial_chain_has_exact_ten_historical_pairs(self):
        P.validate_chain_metadata(self.chain)
        self.assertEqual(len(self.chain["accepted_pairs"]), 10)
        self.assertEqual(self.chain["head_sha256"], ORIGIN)
        self.assertEqual(len(P.FULL_ROSTER), 102)
        self.assertEqual(len(P.REMAINING_ROSTER), 92)
        self.assertNotIn("subject_02", [row["validation_subject"] for row in self.chain["accepted_pairs"]])

    def test_first_request_has_exact_next_sixteen(self):
        planned = request(self.chain)
        self.validate(planned)
        self.assertEqual(planned["index"], 1)
        self.assertEqual(planned["mode"], "folds")
        self.assertEqual(planned["pairs"], [
            {"candidate": "lr_1e-3", "validation_subject": f"subject_{i:02d}"} for i in range(7, 23)])
        self.assertEqual(planned["prior_folds"], 10)
        self.assertEqual(planned["chain_relative"], "chains/chain_000.json")
        self.assertEqual(planned["output_relative"], "fragments/fragment_001")
        self.assertEqual(planned["chain_sha256"], P.logical(self.chain))

    def test_fold_budget_is_exact_current_work(self):
        self.assertEqual(P.budget(request(self.chain)), {
            "source_updates": 800, "support_updates": 16, "gradient_updates": 816,
            "optimizer_init": 32, "safetensors_load": 2, "module_load_state_dict": 2, "safetensors_save": 0})

    def test_six_chunks_cover_remaining_roster_once(self):
        seen = []; sizes = []; updates = 0; prior = []
        for index in range(1, 7):
            planned = request(self.chain); self.validate(planned)
            prior.append(planned["prior_folds"]); sizes.append(len(planned["pairs"]))
            seen.extend((row["candidate"], row["validation_subject"]) for row in planned["pairs"])
            updates += P.budget(planned)["gradient_updates"]
            self.chain = P.advance_chain(self.chain, descriptor(self.chain))
            self.assertEqual(self.chain["chain_index"], index)
        self.assertEqual(sizes, [16, 16, 16, 16, 16, 12])
        self.assertEqual(prior, [10, 26, 42, 58, 74, 90])
        self.assertEqual(tuple(seen), P.REMAINING_ROSTER)
        self.assertEqual(len(set(seen)), 92)
        self.assertEqual(updates + 51 + 510, 5253)
        self.assertEqual(len(self.chain["accepted_pairs"]), 102)

    def test_final_request_only_follows_all_one_hundred_two_folds(self):
        chain = progress(6); planned = request(chain)
        self.validate(planned, chain)
        self.assertEqual((planned["index"], planned["mode"], planned["prior_folds"], planned["pairs"]), (7, "final", 102, []))
        self.assertEqual(P.budget(planned), {
            "source_updates": 51, "support_updates": 0, "gradient_updates": 51,
            "optimizer_init": 1, "safetensors_load": 3, "module_load_state_dict": 2, "safetensors_save": 1})
        self.assertIs(chain["complete"], False)

    def test_eighth_request_and_leaf_are_forbidden(self):
        chain = progress(7)
        with self.assertRaisesRegex(ValueError, "seven-request chain is exhausted"):
            request(chain)
        with self.assertRaisesRegex(ValueError, "seven-request chain is exhausted"):
            P.advance_chain(chain, chain["leaves"][-1])

    def test_return_values_have_no_mutable_input_aliases(self):
        planned = request(self.chain); planned["limits"]["seconds"] = 1
        self.assertEqual(request(self.chain)["limits"]["seconds"], 600)
        leaf = descriptor(self.chain); advanced = P.advance_chain(self.chain, leaf)
        advanced["leaves"][0]["path"] = "mutated output"
        self.assertTrue(leaf["path"].endswith("/leaf.json"))
        self.assertEqual(self.chain["leaves"], [])

    def test_boolean_chain_index_is_not_an_integer(self):
        self.chain["chain_index"] = False
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_negative_or_oversized_chain_index_refused(self):
        for index in (-1, 8, 0.0):
            self.chain["chain_index"] = index
            with self.assertRaises(ValueError):
                P.validate_chain_metadata(self.chain)

    def test_chain_missing_or_unknown_fields_refused(self):
        del self.chain["complete"]
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)
        self.chain = initial(); self.chain["winner"] = "lr_1e-3"
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_wrong_chain_schema_or_complete_claim_refused(self):
        self.chain["schema"] = "scientific_complete"
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)
        self.chain = initial(); self.chain["complete"] = True
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_invalid_chain_digest_fields_refused(self):
        for key in ("root_origin_sha256", "pins_sha256", "head_sha256"):
            for value in (True, "A" * 64, "a" * 32, None):
                mutated = initial(); mutated[key] = value
                with self.assertRaises(ValueError):
                    P.validate_chain_metadata(mutated)

    def test_chain_gap_or_leaf_count_mismatch_refused(self):
        self.chain["chain_index"] = 1
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)
        self.chain = progress(2); self.chain["leaves"].pop(0)
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_leaf_index_gap_or_boolean_refused(self):
        for value in (2, True):
            leaf = descriptor(self.chain); leaf["index"] = value
            self.reject_descriptor(leaf)

    def test_leaf_path_must_be_exact_root_relative_path(self):
        for path in ("../leaf.json", "D:/outside/leaf.json", "fragments/fragment_001/leaf.json",
                     P.RUN_RELATIVE + "/fragments/fragment_002/leaf.json"):
            leaf = descriptor(self.chain); leaf["path"] = path
            self.reject_descriptor(leaf)

    def test_leaf_parent_head_substitution_refused(self):
        leaf = descriptor(self.chain); leaf["parent_head_sha256"] = sha("different parent")
        self.reject_descriptor(leaf)

    def test_historical_request_physical_digest_checked(self):
        leaf = descriptor(self.chain); leaf["request_sha256"] = P.logical(request(self.chain))
        self.reject_descriptor(leaf)

    def test_leaf_digest_replay_or_root_reuse_refused(self):
        leaf = descriptor(self.chain); leaf["sha256"] = ORIGIN
        self.reject_descriptor(leaf)
        self.chain = progress(1); leaf = descriptor(self.chain)
        leaf["sha256"] = self.chain["leaves"][0]["sha256"]
        self.reject_descriptor(leaf)

    def test_chain_current_head_must_equal_last_leaf(self):
        chain = progress(1); chain["head_sha256"] = sha("wrong head")
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(chain)

    def test_duplicate_accepted_pair_refused(self):
        self.chain["accepted_pairs"].append(copy.deepcopy(self.chain["accepted_pairs"][0]))
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_accepted_pairs_must_be_in_canonical_order(self):
        chain = progress(1); chain["accepted_pairs"].reverse()
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(chain)

    def test_missing_or_premature_accepted_pair_refused(self):
        self.chain["accepted_pairs"].pop()
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)
        self.chain = initial(); self.chain["accepted_pairs"].append({"candidate": "lr_1e-3", "validation_subject": "subject_07"})
        with self.assertRaises(ValueError):
            P.validate_chain_metadata(self.chain)

    def test_request_duplicate_pair_refused(self):
        planned = request(self.chain); planned["pairs"][1] = copy.deepcopy(planned["pairs"][0])
        with self.assertRaises(ValueError):
            self.validate(planned)

    def test_request_current_pairs_cannot_be_reordered(self):
        planned = request(self.chain); planned["pairs"].reverse()
        with self.assertRaises(ValueError):
            self.validate(planned)

    def test_outer_target_or_wrong_candidate_pair_refused(self):
        for pair in ({"candidate": "lr_1e-3", "validation_subject": "subject_02"},
                     {"candidate": "lr_3e-3", "validation_subject": "subject_07"}):
            planned = request(self.chain); planned["pairs"][0] = pair
            with self.assertRaises(ValueError):
                self.validate(planned)

    def test_request_index_skip_or_boolean_refused(self):
        for index in (2, True, 0):
            planned = request(self.chain); planned["index"] = index
            with self.assertRaises(ValueError):
                self.validate(planned)

    def test_request_parent_context_and_digest_substitution_refused(self):
        for key in ("parent_head_sha256", "pins_sha256", "root_origin_sha256", "chain_sha256"):
            planned = request(self.chain); planned[key] = sha("substituted " + key)
            with self.assertRaises(ValueError):
                self.validate(planned)

    def test_external_pin_or_origin_mismatch_refused(self):
        with self.assertRaises(ValueError):
            P.next_request(self.chain, pins_sha256=sha("wrong external pins"), root_origin_sha256=ORIGIN)
        with self.assertRaises(ValueError):
            P.next_request(self.chain, pins_sha256=PINS, root_origin_sha256=sha("wrong external origin"))

    def test_premature_final_mode_refused_by_validation_and_budget(self):
        planned = request(self.chain); planned["mode"] = "final"; planned["pairs"] = []
        with self.assertRaises(ValueError):
            self.validate(planned)
        with self.assertRaises(ValueError):
            P.budget(planned)

    def test_mutated_limits_or_boolean_scoped_integer_refused(self):
        for key, value in (("seconds", 601), ("startup_ram_gib", 9), ("torch_threads", True), ("gpu_hidden", False)):
            planned = request(self.chain); planned["limits"][key] = value
            with self.assertRaises(ValueError):
                self.validate(planned)
            with self.assertRaises(ValueError):
                P.budget(planned)
        planned = request(self.chain); planned["original_case_attempts"] = False
        with self.assertRaises(ValueError):
            self.validate(planned)

    def test_request_output_and_parent_snapshot_paths_are_exact(self):
        for key, value in (("output_relative", "../escape"), ("output_relative", "fragments/fragment_002"),
                           ("chain_relative", "chains/chain_001.json"), ("chain_relative", "D:/escape.json")):
            planned = request(self.chain); planned[key] = value
            with self.assertRaises(ValueError):
                self.validate(planned)

    def test_request_unknown_or_missing_keys_refused(self):
        planned = request(self.chain); planned["winner"] = "lr_1e-3"
        with self.assertRaises(ValueError):
            self.validate(planned)
        planned = request(self.chain); del planned["chain_relative"]
        with self.assertRaises(ValueError):
            self.validate(planned)

    def test_used_request_cannot_replay_on_advanced_chain(self):
        planned = request(self.chain); advanced = P.advance_chain(self.chain, descriptor(self.chain))
        with self.assertRaises(ValueError):
            self.validate(planned, advanced)

    def test_descriptor_modes_pairs_counts_and_unknown_fields_refused(self):
        for key, value in (("mode", "final"), ("pairs", []), ("accepted_folds_before", 11),
                           ("accepted_folds_after", 27), ("accepted_folds_before", True)):
            leaf = descriptor(self.chain); leaf[key] = value
            self.reject_descriptor(leaf)
        leaf = descriptor(self.chain); leaf["unverified_execution"] = True
        self.reject_descriptor(leaf)


if __name__ == "__main__":
    unittest.main()
