from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from evaluation.moabb_reference_plan import ReferenceUnit
from scripts.audit_moabb_reference_inputs import compare_input_proof, guard_memory


class MoabbReferenceInputTests(unittest.TestCase):
    def setUp(self):
        self.unit = ReferenceUnit(42, 1, "0train", 0)
        self.proof = {
            "session_targets": [0, 1],
            "channel_names": ["Fz"],
            "native_epoch_shape": [2, 1, 1001],
            "raw_file_sha256": "a" * 64,
            "folds": {
                "0": {
                    "query_indices": [0],
                    "transformed_query_shape": [1, 1, 513],
                    "transformed_query_sha256": "b" * 64,
                }
            },
        }
        self.result = {
            key: self.proof[key]
            for key in ("session_targets", "channel_names", "native_epoch_shape")
        }
        self.result.update(self.proof["folds"]["0"])
        self.result["raw_file_sha256"] = {"A01T.mat": "a" * 64}

    def test_exact_reconstruction_matches(self):
        compare_input_proof(self.result, self.proof, self.unit)

    def test_every_input_identity_mismatch_is_rejected(self):
        for key, value in (
            ("session_targets", [1, 0]),
            ("channel_names", ["Cz"]),
            ("native_epoch_shape", [2, 1, 1000]),
            ("query_indices", [1]),
            ("transformed_query_shape", [1, 1, 512]),
            ("transformed_query_sha256", "c" * 64),
            ("raw_file_sha256", {"A01T.mat": "d" * 64}),
        ):
            result = copy.deepcopy(self.result)
            result[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                compare_input_proof(result, self.proof, self.unit)

    def test_memory_refusal(self):
        fake = SimpleNamespace(virtual_memory=lambda: SimpleNamespace(available=3 * 1024**3))
        with (
            patch(
                "scripts.audit_moabb_reference_inputs.importlib.import_module", return_value=fake
            ),
            self.assertRaisesRegex(RuntimeError, "low-memory"),
        ):
            guard_memory(4.0)


if __name__ == "__main__":
    unittest.main()
