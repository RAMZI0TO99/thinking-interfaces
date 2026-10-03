"""Byte-exact factoring checks for completed source-selection envelopes."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from core.config import canonical_config_json, config_digest
from evaluation.phase2_factored_evidence import (
    MAXIMUM_LOGICAL_BYTES,
    pack_factored_selection,
    unpack_factored_selection,
)
from evaluation.phase2_records import envelope


def _canonical(value: dict[str, Any]) -> bytes:
    return (canonical_config_json(value) + "\n").encode()


def _record(*, bindings: bool = True, tcpl: bool = False) -> dict[str, Any]:
    subjects = ["subject_01", "subject_02", "subject_03"]
    names = ["first", "second"]
    identities = {
        subject: {"catalog_sha256": hashlib.sha256(subject.encode()).hexdigest(),
                  "trial_ids": [f"{subject}-trial-{index:03d}" for index in range(80)]}
        for subject in subjects
    }
    contract = {
        "selection": {"target_subject": "subject_04", "source_subjects": subjects},
        "candidates": [{"name": name} for name in names],
    }

    def fit(candidate: str, validation: str | None) -> dict[str, Any]:
        members = [subject for subject in subjects if subject != validation]
        row = {
            "validation_subject": validation,
            "training_subjects": members,
            "input_identities": {subject: copy.deepcopy(identities[subject])
                                 for subject in members},
        }
        if not tcpl:
            row["candidate"] = candidate
        return row

    folds = []
    for candidate in names:
        for subject in subjects:
            fold: dict[str, Any] = {
                "candidate": candidate,
                "validation_subject": subject,
                "source_fit": fit(candidate, subject),
            }
            if bindings:
                fold["binding"] = {
                    "subject": subject,
                    "episode_sha256": hashlib.sha256(f"episode-{subject}".encode()).hexdigest(),
                    "support_trial_ids": [f"{subject}-support-{index:03d}"
                                          for index in range(30)],
                }
            else:
                fold["input_identities"] = {subject: copy.deepcopy(identities[subject])}
            folds.append(fold)
    payload = {
        "purpose": (
            "bounded_tcpl_source_selection" if tcpl else
            "bounded_labram_source_selection" if bindings
            else "bounded_eegnet_source_selection"
        ),
        "complete": True,
        "outer_target_predictions_performed": False,
        "contract": contract,
        "contract_sha256": config_digest(contract),
        "selected_candidate": "first",
        "folds": folds,
        "final_source_fit": fit("first", None),
    }
    return envelope("engineering_smoke", payload)


class FactoredSelectionEvidenceTests(unittest.TestCase):
    def test_exact_round_trip_with_shared_bindings(self) -> None:
        original = _record()
        packed = pack_factored_selection(original)
        restored = unpack_factored_selection(
            packed, expected_evidence_sha256=original["sha256"],
        )
        self.assertEqual(_canonical(restored), _canonical(original))
        self.assertLess(len(packed), len(_canonical(original)))

    def test_eegnet_without_validation_binding_round_trips(self) -> None:
        original = _record(bindings=False)
        packed = pack_factored_selection(original)
        restored = unpack_factored_selection(
            packed, expected_evidence_sha256=original["sha256"],
        )
        self.assertEqual(_canonical(restored), _canonical(original))

    def test_tcpl_fit_without_candidate_round_trips_but_wrong_candidate_fails(self) -> None:
        original = _record(bindings=False, tcpl=True)
        packed = pack_factored_selection(original)
        restored = unpack_factored_selection(
            packed, expected_evidence_sha256=original["sha256"],
        )
        self.assertEqual(_canonical(restored), _canonical(original))
        payload = copy.deepcopy(original["payload"])
        payload["folds"][0]["source_fit"]["candidate"] = "wrong"
        with self.assertRaisesRegex(ValueError, "source fit differs"):
            pack_factored_selection(envelope("engineering_smoke", payload))

    def test_disagreeing_fold_source_identity_refused(self) -> None:
        original = _record()
        payload = copy.deepcopy(original["payload"])
        payload["folds"][0]["source_fit"]["input_identities"]["subject_02"][
            "trial_ids"
        ][0] = "forged-trial"
        changed = envelope("engineering_smoke", payload)
        with self.assertRaisesRegex(ValueError, "fold source identities"):
            pack_factored_selection(changed)

    def test_disagreeing_validation_binding_refused(self) -> None:
        original = _record()
        payload = copy.deepcopy(original["payload"])
        payload["folds"][3]["binding"]["support_trial_ids"][0] = "forged-support"
        changed = envelope("engineering_smoke", payload)
        with self.assertRaisesRegex(ValueError, "validation binding"):
            pack_factored_selection(changed)

    def test_corrupted_table_and_wrong_external_pin_refused(self) -> None:
        original = _record()
        packed = json.loads(pack_factored_selection(original))
        packed["source_identities_by_subject"]["subject_01"]["trial_ids"][0] = "forged"
        corrupted = _canonical(packed)
        with self.assertRaisesRegex(ValueError, "envelope|canonical"):
            unpack_factored_selection(
                corrupted, expected_evidence_sha256=original["sha256"],
            )
        with self.assertRaisesRegex(ValueError, "external envelope pin"):
            unpack_factored_selection(
                pack_factored_selection(original), expected_evidence_sha256="0" * 64,
            )

    def test_declared_expansion_cap_refused(self) -> None:
        original = _record()
        packed = json.loads(pack_factored_selection(original))
        packed["logical_file_bytes"] = MAXIMUM_LOGICAL_BYTES + 1
        with self.assertRaisesRegex(ValueError, "byte limit"):
            unpack_factored_selection(
                _canonical(packed), expected_evidence_sha256=original["sha256"],
            )

    def test_falsely_small_expansion_claim_refused_before_copy(self) -> None:
        original = _record()
        packed = json.loads(pack_factored_selection(original))
        packed["logical_file_bytes"] = 4096
        with (
            patch("evaluation.phase2_factored_evidence.MAXIMUM_LOGICAL_BYTES", 8192),
            self.assertRaisesRegex(ValueError, "expansion exceeds"),
        ):
            unpack_factored_selection(
                _canonical(packed), expected_evidence_sha256=original["sha256"],
            )

    def test_existing_bounded_records_round_trip_when_present(self) -> None:
        root = Path(__file__).resolve().parents[1]
        relatives = (
            "runs/phase2/adapter_source_checks/20260909_step23/engineering_selection.json",
            "runs/phase2/source_selection_checks/20260908_step20/engineering_selection.json",
            "runs/phase2/tcpl_source_checks/20260916_step26/engineering_selection.json",
        )
        if any(not (root / relative).is_file() for relative in relatives):
            self.skipTest("historical bounded BCI evidence is unavailable")
        for relative in relatives:
            with self.subTest(record=relative):
                raw = (root / relative).read_bytes()
                record = json.loads(raw)
                packed = pack_factored_selection(record)
                restored = unpack_factored_selection(
                    packed, expected_evidence_sha256=record["sha256"],
                )
                self.assertEqual(_canonical(restored), raw)

    def test_existing_complete_tcpl_record_rejects_changed_tables(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "runs/phase2/tcpl_source_checks/20260916_step26/engineering_selection.json"
        if not path.is_file():
            self.skipTest("historical complete TCPL evidence is unavailable")
        raw = path.read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "9894db15395292be731b79b87698de7048d54c2c75d41341dd7f9414f58d0a92",
        )
        original = json.loads(raw)
        packed_bytes = pack_factored_selection(original)
        restored = unpack_factored_selection(
            packed_bytes, expected_evidence_sha256=original["sha256"],
        )
        self.assertEqual(_canonical(restored), raw)
        self.assertEqual(path.read_bytes(), raw)

        packed = json.loads(packed_bytes)
        subject = "subject_02"
        digest = packed["source_identities_by_subject"][subject]["catalog_sha256"]
        packed["source_identities_by_subject"][subject]["catalog_sha256"] = (
            ("0" if digest[0] != "0" else "1") + digest[1:]
        )
        with self.assertRaisesRegex(ValueError, "envelope|canonical"):
            unpack_factored_selection(
                _canonical(packed), expected_evidence_sha256=original["sha256"],
            )

        changed_payload = copy.deepcopy(original["payload"])
        changed_payload["folds"][0]["source_fit"]["input_identities"][
            "subject_03"
        ]["catalog_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fold source identities"):
            pack_factored_selection(envelope("engineering_smoke", changed_payload))


if __name__ == "__main__":
    unittest.main()
