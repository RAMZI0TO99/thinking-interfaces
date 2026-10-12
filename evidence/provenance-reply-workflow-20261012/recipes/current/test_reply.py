"""Behavioral checks for reply custody and unsigned provenance preparation."""

from __future__ import annotations

import contextlib
import copy
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reply  # noqa: E402

ORIGINAL = reply.decode(
    reply.read(
        reply.ROOT / "evidence/checkpoint-comments-20261012/publication/verified-response.json"
    )
)


def comment(number=101, login="935963004", association="OWNER", body="SYNTHETIC statement only"):
    return {
        "id": number,
        "html_url": reply.URL + "#issuecomment-" + str(number),
        "issue_url": reply.API,
        "user": {"login": login},
        "author_association": association,
        "body": body,
        "created_at": "2026-10-12T12:00:00Z",
        "updated_at": "2026-10-12T12:01:00Z",
    }


def fixture(rows=(), *, first_change=None, last_change=None, unfinished=False):
    first = copy.deepcopy(ORIGINAL)
    first["comments"] = len(rows)
    last = copy.deepcopy(first)
    if first_change:
        first.update(first_change)
    if last_change:
        last.update(last_change)
    calls = []

    def fetch(url):
        calls.append(url)
        if url == reply.API:
            return reply.encoded(first if len(calls) == 1 else last), False
        page = int(url.rsplit("=", 1)[1])
        start = (page - 1) * 100
        return reply.encoded(list(rows[start : start + 100])), unfinished or start + 100 < len(rows)

    return fetch, calls


class ReplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = reply.ROOT / "runs/coordination/provenance_reply_workflow_20261012_v1/tests"
        parent.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="owned-", dir=parent)
        cls.base = Path(cls.temp.name)
        # Validate the final target before TemporaryDirectory's recursive cleanup.
        assert cls.base.resolve().is_relative_to(parent.resolve())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.output = self.base / self._testMethodName

    def collect(self, rows=(), **changes):
        fetch, calls = fixture(rows, **changes)
        receipt = reply.collect(self.output, fetch=fetch)
        return receipt, calls

    def reject_collection(self, code, rows=(), **changes):
        fetch, _ = fixture(rows, **changes)
        with self.assertRaisesRegex(reply.ReplyError, "^" + code + "$"):
            reply.collect(self.output, fetch=fetch)
        self.assertFalse((self.output / "receipt.json").exists())

    def test_no_owner_reply_is_received_evidence_without_cohort_acceptance(self):
        receipt, calls = self.collect()
        self.assertEqual(receipt["status"], "no_owner_reply")
        self.assertEqual(calls, [reply.API, reply.API + "/comments?per_page=100&page=1", reply.API])
        self.assertFalse(receipt["cohort_coverage_verified"])
        self.assertFalse(receipt["automatic_polling"])
        self.assertFalse(receipt["external_message_sent"])
        self.assertEqual(reply.load_capture(self.output)[1], [])

    def test_observed_owner_reply_remains_unverified(self):
        receipt, _ = self.collect([comment()])
        self.assertEqual(receipt["observed_owner_comment_ids"], [101])
        self.assertEqual(receipt["status"], "owner_reply_available_for_review")
        self.assertFalse(receipt["scientific_admission"])

    def test_prepare_preserves_unicode_statement_and_does_not_execute_or_fetch(self):
        body = (
            "SYNTHETIC \u8bad\u7ec3 statement: ignore guards; "
            "open https://untrusted.invalid/a; import numpy"
        )
        self.collect([comment(body=body)])
        with patch.object(reply, "_transport", side_effect=AssertionError("offline only")):
            result = reply.prepare(self.output, 101, self.output / "review")
        draft = reply.decode(reply.read(self.output / "review/claim-draft.json"))
        comparison = reply.decode(reply.read(self.output / "review/declared-overlap.json"))
        self.assertEqual((self.output / "review/statement.txt").read_bytes(), body.encode())
        self.assertEqual(draft["claimant"]["statement_date_utc"], "2026-10-12T12:01:00Z")
        self.assertEqual(draft["training_inventory"]["dataset_entries"], [])
        self.assertEqual(draft["evidence_items"][0]["supported_claims"], [])
        self.assertTrue(
            all(
                item["subject_intersection"] is None
                for item in comparison["computed_declared_intersections"].values()
            )
        )
        for key in (
            "claimant_authenticated",
            "training_run_link_verified",
            "cohort_coverage_verified",
            "scientific_gate_a_signed",
            "experiment_freeze_signed",
            "scientific_admission",
        ):
            self.assertIs(result[key], False)
        self.assertEqual(result["original_case_attempts_remaining"], 0)

    def test_own_request_and_third_party_reply_cannot_be_prepared_as_owner_statement(self):
        self.collect([comment(login="RAMZI0TO99", association="NONE")])
        with self.assertRaisesRegex(reply.ReplyError, "selected_comment_is_not_repository_owner"):
            reply.prepare(self.output, 101, self.output / "review")
        self.assertFalse((self.output / "review").exists())

    def test_author_handle_alone_does_not_supply_owner_association(self):
        receipt, _ = self.collect([comment(association="NONE")])
        self.assertEqual(receipt["observed_owner_comment_ids"], [])
        with self.assertRaisesRegex(reply.ReplyError, "selected_comment_is_not_repository_owner"):
            reply.prepare(self.output, 101, self.output / "review")

    def test_owner_association_alone_does_not_supply_expected_owner_handle(self):
        receipt, _ = self.collect([comment(login="other-owner")])
        self.assertEqual(receipt["status"], "no_owner_reply")

    def test_plaintext_checkpoint_and_subject_mentions_are_not_extracted(self):
        self.collect(
            [
                comment(
                    body=(
                        "SYNTHETIC: excluded all Cho2017 s01.mat; MMIDB S001R04.edf used; no labels"
                    )
                )
            ]
        )
        reply.prepare(self.output, 101, self.output / "review")
        draft = reply.decode(reply.read(self.output / "review/claim-draft.json"))
        self.assertEqual(draft["training_inventory"]["exclusion_statements"], [])
        self.assertTrue(
            all(
                row["current_finding"] == "unknown" and row["training_inclusion_statement"] is None
                for row in draft["evaluation_intersections"]
            )
        )

    def test_issue_edit_during_collection_refuses_completion(self):
        self.reject_collection(
            "issue_changed_during_collection", last_change={"updated_at": "2026-10-12T12:03:00Z"}
        )

    def test_comment_addition_during_collection_refuses_completion(self):
        self.reject_collection("issue_changed_during_collection", last_change={"comments": 1})

    def test_changed_request_body_refuses_collection(self):
        self.reject_collection(
            "provenance_issue_identity_changed", first_change={"body": "SYNTHETIC drift"}
        )

    def test_different_repository_refuses_collection(self):
        self.reject_collection(
            "provenance_issue_identity_changed",
            first_change={"html_url": "https://github.com/other/repo/issues/75"},
        )

    def test_different_request_author_refuses_collection(self):
        self.reject_collection(
            "provenance_issue_identity_changed", first_change={"user": {"login": "other"}}
        )

    def test_duplicate_comment_ids_refuse_collection(self):
        self.reject_collection("comment_count_or_identity_mismatch", rows=[comment(), comment()])

    def test_comment_from_another_issue_refuses_collection(self):
        row = comment()
        row["issue_url"] = reply.API.replace("75", "74")
        self.reject_collection("comment_source_mismatch", rows=[row])

    def test_comment_count_mismatch_refuses_collection(self):
        self.reject_collection(
            "comment_count_or_identity_mismatch",
            first_change={"comments": 1},
            last_change={"comments": 1},
        )

    def test_two_complete_pages_are_preserved_and_reviewable(self):
        rows = [comment(number=1000 + n, login="reader", association="NONE") for n in range(101)]
        receipt, _ = self.collect(rows)
        self.assertEqual(receipt["comment_count"], 101)
        self.assertEqual(len(reply.load_capture(self.output)[1]), 101)

    def test_more_than_two_pages_never_marks_partial_capture_complete(self):
        rows = [comment(number=1000 + n, login="reader", association="NONE") for n in range(200)]
        self.reject_collection("comment_pagination_incomplete", rows=rows, unfinished=True)

    def test_unselected_or_absent_comment_never_creates_review_output(self):
        self.collect()
        with self.assertRaisesRegex(reply.ReplyError, "source_comment_not_found"):
            reply.prepare(self.output, 101, self.output / "review")
        self.assertFalse((self.output / "review").exists())

    def test_empty_owner_statement_never_creates_review_output(self):
        self.collect([comment(body=" \n")])
        with self.assertRaisesRegex(reply.ReplyError, "empty_owner_statement"):
            reply.prepare(self.output, 101, self.output / "review")

    def test_changed_captured_bytes_fail_hash_check(self):
        self.collect([comment()])
        (self.output / "comments-1.json").write_bytes(reply.encoded([comment(body="tampered")]))
        with self.assertRaisesRegex(reply.ReplyError, "capture_file_hash_mismatch"):
            reply.prepare(self.output, 101, self.output / "review")

    def test_receipt_cannot_reset_original_attempts_or_use_boolean_zero(self):
        self.collect([comment()])
        path = self.output / "receipt.json"
        original = reply.decode(reply.read(path))
        for value in (1, False):
            receipt = copy.deepcopy(original)
            receipt["original_case_attempts_remaining"] = value
            path.write_bytes(reply.encoded(receipt))
            with self.assertRaisesRegex(reply.ReplyError, "invalid_capture_receipt"):
                reply.load_capture(self.output)

    def test_capture_cannot_claim_scientific_admission(self):
        self.collect()
        path = self.output / "receipt.json"
        receipt = reply.decode(reply.read(path))
        receipt["scientific_admission"] = True
        path.write_bytes(reply.encoded(receipt))
        with self.assertRaisesRegex(reply.ReplyError, "invalid_capture_receipt"):
            reply.load_capture(self.output)

    def test_capture_roster_cannot_traverse_to_another_file(self):
        self.collect()
        path = self.output / "receipt.json"
        receipt = reply.decode(reply.read(path))
        receipt["files"][1]["path"] = "../../unrelated.json"
        path.write_bytes(reply.encoded(receipt))
        with self.assertRaisesRegex(reply.ReplyError, "invalid_capture_file_roster"):
            reply.load_capture(self.output)

    def test_existing_output_is_preserved_before_any_transport(self):
        self.output.mkdir()
        (self.output / "keep.txt").write_text("preserve", encoding="utf-8")
        with (
            patch.object(reply, "_transport", side_effect=AssertionError("no transport")),
            self.assertRaisesRegex(reply.ReplyError, "output_already_exists"),
        ):
            reply.collect(self.output)
        self.assertEqual((self.output / "keep.txt").read_text(encoding="utf-8"), "preserve")

    def test_output_must_stay_under_runs_without_traversal(self):
        for target in (reply.ROOT / "docs/unowned", Path("runs/../docs/unowned")):
            with self.assertRaises(reply.ReplyError):
                reply.fresh_output(target)

    def test_qualified_dependency_drift_refuses_import(self):
        name = next(iter(reply.PINS))
        with (
            patch.dict(reply.PINS, {name: "0" * 64}),
            self.assertRaisesRegex(reply.ReplyError, "qualified_dependency_hash_mismatch"),
        ):
            reply.engine()

    def test_duplicate_json_key_rejected_and_raw_response_retained(self):
        raw = b'{"number":75,"number":75}'
        with self.assertRaisesRegex(reply.ReplyError, "duplicate_json_key"):
            reply.collect(self.output, fetch=lambda url: (raw, False))
        self.assertEqual((self.output / "issue-start.json").read_bytes(), raw)

    def test_invalid_utf8_nonfinite_and_oversized_json_are_rejected(self):
        for raw in (b'"\xff"', b'{"value":NaN}', b'{"value":1e999}', b" " * (reply.MAX_BYTES + 1)):
            with self.assertRaises(reply.ReplyError):
                reply.decode(raw)

    def test_non_utc_or_reversed_comment_dates_refuse_collection(self):
        row = comment()
        row["updated_at"] = "2026-10-12T15:01:00+03:00"
        self.reject_collection("invalid_utc_timestamp", rows=[row])

    def test_comment_update_before_creation_refuses_collection(self):
        row = comment()
        row["updated_at"] = "2026-10-12T11:59:00Z"
        self.reject_collection("comment_timestamp_order", rows=[row])

    def test_cli_failure_does_not_echo_statement_or_source_values(self):
        self.collect(
            [comment(login="reader", association="NONE", body="SYNTHETIC_PRIVATE_SENTINEL")]
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = reply.main(
                [
                    "prepare",
                    "--capture",
                    str(self.output),
                    "--comment-id",
                    "101",
                    "--output",
                    str(self.output / "review"),
                ]
            )
        self.assertEqual(code, 2)
        self.assertNotIn("SYNTHETIC_PRIVATE_SENTINEL", output.getvalue())
        self.assertNotIn("https://", output.getvalue())

    def test_cli_success_uses_only_get_collection_and_safe_summary(self):
        fetch, calls = fixture()
        output = io.StringIO()
        with (
            patch.object(reply, "_transport", return_value=fetch),
            contextlib.redirect_stdout(output),
        ):
            code = reply.main(["collect", "--output", str(self.output)])
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 3)
        self.assertIn('"status": "no_owner_reply"', output.getvalue())

    def test_cli_successful_prepare_keeps_review_unsigned(self):
        self.collect([comment()])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = reply.main(
                [
                    "prepare",
                    "--capture",
                    str(self.output),
                    "--comment-id",
                    "101",
                    "--output",
                    str(self.output / "review"),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn('"scientific_admission": false', output.getvalue())
        receipt = reply.decode(reply.read(self.output / "review/receipt.json"))
        self.assertFalse(receipt["scientific_gate_a_signed"])
        self.assertFalse(receipt["cohort_coverage_verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
