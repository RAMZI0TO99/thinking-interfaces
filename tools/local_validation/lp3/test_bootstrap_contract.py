"""Adversarial bootstrap authority joins; fixtures confer no execution authority."""
from copy import deepcopy
import unittest

from . import bootstrap_contract as b
from ..v1.records import Refusal


def request(stage="Q"):
    pin = {"bytes": 17, "sha256": "a" * 64}
    value = {"stage": stage, "bootstrap_qualification": {"path": b.QUALIFICATION, **pin},
             "sources": {b.QUALIFICATION: deepcopy(pin)}}
    if stage == "Q":
        value["bootstrap_controls"] = list(b.CONTROLS)
    return value


class BootstrapContractTests(unittest.TestCase):
    def test_q_request_requires_both_controls(self):
        value = request()
        original = deepcopy(value)
        self.assertTrue(b.validate_request(value))
        self.assertEqual(value, original)

    def test_p_request_cannot_choose_a_control(self):
        value = request("P")
        self.assertTrue(b.validate_request(value))
        value["bootstrap_controls"] = list(b.CONTROLS)
        with self.assertRaises(Refusal):
            b.validate_request(value)

    def test_unknown_stage_refuses(self):
        for stage in ("L", "Q ", True, None):
            value = request()
            value["stage"] = stage
            with self.subTest(stage=stage), self.assertRaises(Refusal):
                b.validate_request(value)

    def test_reference_has_closed_fields(self):
        for field in ("path", "bytes", "sha256"):
            value = request()
            del value["bootstrap_qualification"][field]
            with self.subTest(field=field), self.assertRaises(Refusal):
                b.validate_request(value)
        value = request()
        value["bootstrap_qualification"]["trusted"] = True
        with self.assertRaises(Refusal):
            b.validate_request(value)

    def test_reference_rejects_wrong_or_absolute_path(self):
        for path in ("other/root-qualification.json", "D:/Aenv/pro3/" + b.QUALIFICATION,
                     b.QUALIFICATION.upper()):
            value = request()
            value["bootstrap_qualification"]["path"] = path
            with self.subTest(path=path), self.assertRaises(Refusal):
                b.validate_request(value)

    def test_reference_rejects_invalid_size_and_digest(self):
        for key, bad in (("bytes", True), ("bytes", 0), ("bytes", 1024**2 + 1),
                         ("sha256", "A" * 64), ("sha256", "a" * 63), ("sha256", False)):
            value = request()
            value["bootstrap_qualification"][key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(Refusal):
                b.validate_request(value)

    def test_reference_must_be_in_source_map(self):
        value = request()
        value["sources"].clear()
        with self.assertRaises(Refusal):
            b.validate_request(value)

    def test_reference_pin_must_equal_source_pin(self):
        for key, bad in (("bytes", 18), ("sha256", "b" * 64)):
            value = request()
            value["sources"][b.QUALIFICATION][key] = bad
            with self.subTest(key=key), self.assertRaises(Refusal):
                b.validate_request(value)
        value = request()
        value["bootstrap_qualification"]["bytes"] = 1
        value["sources"][b.QUALIFICATION]["bytes"] = True
        with self.assertRaises(Refusal):
            b.validate_request(value)

    def test_controls_reject_omission_order_duplicates_and_types(self):
        for bad in (None, "accepted,bad_identity", [], ["accepted"],
                    ["bad_identity", "accepted"], ["accepted", "accepted"],
                    ["accepted", True], ["accepted", "bad_identity", "extra"]):
            value = request()
            value["bootstrap_controls"] = bad
            with self.subTest(bad=bad), self.assertRaises(Refusal):
                b.validate_request(value)

    def test_adoption_requires_exact_bootstrap_pin(self):
        value = request()
        self.assertTrue(b.validate_adoption(value, {"bootstrap_qualification_sha256": "a" * 64}))
        for record in ({}, {"bootstrap_qualification_sha256": "b" * 64},
                       {"bootstrap_qualification_sha256": True}):
            with self.subTest(record=record), self.assertRaises(Refusal):
                b.validate_adoption(value, record)

    def test_root_qualification_requires_complete_controls(self):
        actual = {"bootstrap_controls": list(b.CONTROLS)}
        self.assertTrue(b.validate_qualification(deepcopy(actual), actual))
        for record in ({}, {"bootstrap_controls": ["accepted"]},
                       {"bootstrap_controls": ["bad_identity", "accepted"]}):
            with self.subTest(record=record), self.assertRaises(Refusal):
                b.validate_qualification(record, actual)

    def test_actual_review_cannot_omit_or_change_controls(self):
        qualified = {"bootstrap_controls": list(b.CONTROLS)}
        for record in ({}, {"bootstrap_controls": ["accepted"]},
                       {"bootstrap_controls": ["accepted", "other"]}):
            with self.subTest(record=record), self.assertRaises(Refusal):
                b.validate_qualification(qualified, record)
