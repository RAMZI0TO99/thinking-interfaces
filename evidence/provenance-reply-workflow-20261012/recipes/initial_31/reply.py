"""Collect the provenance issue once and prepare unsigned, local review drafts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import stat
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import safe_path, source_check, write_json  # noqa: E402

API = "https://api.github.com/repos/935963004/LaBraM/issues/75"
URL = "https://github.com/935963004/LaBraM/issues/75"
TITLE = "Recording-level pretraining provenance for the released LaBraM base checkpoint"
REQUEST_SHA = "e8db8f6c1e690df9b1ceb763797dea21ae51acdac8233c29b3128881c272eed5"
MAX_BYTES = 1024**2
MAX_PAGES = 2
PINS = {
    "docs/phase2/cohort_overlap_candidate/declared_overlap.py": (
        "96cfe17e9e4a6c865d85399f784a5fedbff28136bd91b02f112bed25b7ea5189"
    ),
    "docs/phase2/provenance_intake_candidate/inspect_cohort.py": (
        "9221d82a8035b851e56e76dcd50124846050dded5727755f2f939bfa0f04ba3b"
    ),
    "docs/phase2/provenance_intake_candidate/reference_template.json": (
        "d62cb5450578fa8ea0e90856cb314eb183db93f401a64e1aae5d28f4f536ceab"
    ),
    "docs/phase2/evaluation_recording_provenance_package_20261011.json": (
        "b9ea3dfefed137a2264313bed1b7b3c392a1be799fbd767583500f44024bfc69"
    ),
}


class ReplyError(ValueError):
    """Stable error codes never echo untrusted text, URLs or credentials."""


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ReplyError("duplicate_json_key")
        result[key] = value
    return result


def _nonfinite(value):
    raise ReplyError("nonfinite_json_number")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ReplyError("nonfinite_json_number")
    return result


def decode(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ReplyError("metadata_size_or_type")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
            parse_float=_float,
        )
    except ReplyError:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise ReplyError("invalid_json_or_utf8") from None


def read(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
        raise ReplyError("nonregular_metadata_file")
    if not 0 < info.st_size <= MAX_BYTES:
        raise ReplyError("metadata_size_or_type")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    after = path.lstat()
    if (info.st_size, info.st_mtime_ns, info.st_ino) != (
        after.st_size,
        after.st_mtime_ns,
        after.st_ino,
    ):
        raise ReplyError("metadata_changed_during_read")
    if len(raw) != info.st_size:
        raise ReplyError("metadata_changed_during_read")
    return raw


def local_path(path):
    path = Path(path)
    try:
        relative = path.relative_to(ROOT) if path.is_absolute() else path
        return safe_path(ROOT, relative.as_posix())
    except ValueError:
        raise ReplyError("workspace_path_required") from None


def fresh_output(path):
    path = local_path(path)
    if not path.is_relative_to(ROOT / "runs") or path == ROOT / "runs":
        raise ReplyError("fresh_runs_directory_required")
    if path.exists():
        raise ReplyError("output_already_exists")
    return path


def utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() != timedelta(0):
            raise ValueError
        return parsed
    except (AttributeError, TypeError, ValueError):
        raise ReplyError("invalid_utc_timestamp") from None


def check_issue(value):
    if (
        type(value) is not dict
        or type(value.get("number")) is not int
        or value.get("number") != 75
        or value.get("html_url") != URL
        or value.get("url") != API
        or value.get("title") != TITLE
        or value.get("user", {}).get("login") != "RAMZI0TO99"
        or type(value.get("comments")) is not int
        or not 0 <= value["comments"] <= 100 * MAX_PAGES
        or type(value.get("body")) is not str
        or sha(value["body"].replace("\r\n", "\n").encode()) != REQUEST_SHA
        or "pull_request" in value
    ):
        raise ReplyError("provenance_issue_identity_changed")
    utc(value.get("updated_at"))


def check_comment(value):
    if type(value) is not dict or type(value.get("id")) is not int or value["id"] <= 0:
        raise ReplyError("invalid_comment_identity")
    if (
        value.get("html_url") != URL + "#issuecomment-" + str(value["id"])
        or value.get("issue_url") != API
    ):
        raise ReplyError("comment_source_mismatch")
    login = value.get("user", {}).get("login")
    if type(login) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", login) is None:
        raise ReplyError("invalid_comment_author")
    if type(value.get("body")) is not str or type(value.get("author_association")) is not str:
        raise ReplyError("invalid_comment_content")
    if utc(value.get("updated_at")) < utc(value.get("created_at")):
        raise ReplyError("comment_timestamp_order")


def owner_comment(value):
    return value["user"]["login"] == "935963004" and value["author_association"] == "OWNER"


def _transport():
    import github

    credential = github.token()

    def get(url):
        with github.request(url, credential, method="GET") as response:
            raw = response.read(MAX_BYTES + 1)
            more = 'rel="next"' in response.headers.get("Link", "")
            if response.status != 200:
                raise ReplyError("metadata_http_status")
        if len(raw) > MAX_BYTES:
            raise ReplyError("metadata_size_or_type")
        return raw, more

    return get


def collect(output, *, fetch=None):
    """One bounded GET sequence; no posting, polling loop or reference downloads."""
    source = source_check(ROOT)
    output = fresh_output(output)
    output.mkdir(parents=True, exist_ok=False)
    fetch = _transport() if fetch is None else fetch
    files = []

    def get(url, name):
        raw, more = fetch(url)
        if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES or type(more) is not bool:
            raise ReplyError("metadata_size_or_type")
        with (output / name).open("xb") as stream:
            stream.write(raw)
        files.append(
            {"path": name, "url": url, "bytes": len(raw), "sha256": sha(raw), "next_page": more}
        )
        return decode(raw), more

    first, more = get(API, "issue-start.json")
    check_issue(first)
    if more:
        raise ReplyError("unexpected_issue_pagination")
    comments = []
    for page in range(1, MAX_PAGES + 1):
        rows, more = get(API + f"/comments?per_page=100&page={page}", f"comments-{page}.json")
        if type(rows) is not list or len(rows) > 100:
            raise ReplyError("comment_page_bound")
        for row in rows:
            check_comment(row)
        comments.extend(rows)
        if not more:
            break
    else:
        raise ReplyError("comment_pagination_incomplete")
    last, more = get(API, "issue-end.json")
    check_issue(last)
    if more or first["updated_at"] != last["updated_at"] or first["comments"] != last["comments"]:
        raise ReplyError("issue_changed_during_collection")
    if len(comments) != last["comments"] or len({row["id"] for row in comments}) != len(comments):
        raise ReplyError("comment_count_or_identity_mismatch")
    if source_check(ROOT) != source:
        raise ReplyError("canonical_source_changed")
    receipt = {
        "schema": "pro3_provenance_reply_capture_v1",
        "observed_utc": datetime.now(UTC).isoformat(),
        "issue_url": URL,
        "request_body_sha256": REQUEST_SHA,
        "canonical_source_sha256": source,
        "workflow_sha256": sha(Path(__file__).read_bytes()),
        "complete": True,
        "comment_count": len(comments),
        "observed_owner_comment_ids": [row["id"] for row in comments if owner_comment(row)],
        "status": "owner_reply_available_for_review"
        if any(owner_comment(row) for row in comments)
        else "no_owner_reply",
        "files": files,
        "automatic_polling": False,
        "external_message_sent": False,
        "referenced_artifacts_fetched": False,
        "cohort_coverage_verified": False,
        "scientific_admission": False,
        "original_case_attempts_remaining": 0,
    }
    write_json(output / "receipt.json", receipt)
    return receipt


def load_capture(folder):
    folder = local_path(folder)
    receipt = decode(read(folder / "receipt.json"))
    if (
        receipt.get("schema") != "pro3_provenance_reply_capture_v1"
        or receipt.get("complete") is not True
        or receipt.get("issue_url") != URL
        or receipt.get("request_body_sha256") != REQUEST_SHA
        or receipt.get("scientific_admission") is not False
        or type(receipt.get("original_case_attempts_remaining")) is not int
        or receipt["original_case_attempts_remaining"] != 0
    ):
        raise ReplyError("invalid_capture_receipt")
    files = receipt.get("files")
    if type(files) is not list or not 3 <= len(files) <= MAX_PAGES + 2:
        raise ReplyError("invalid_capture_file_roster")
    names = [row.get("path") for row in files]
    pages = len(files) - 2
    expected = (
        ["issue-start.json"]
        + [f"comments-{page}.json" for page in range(1, pages + 1)]
        + ["issue-end.json"]
    )
    if names != expected:
        raise ReplyError("invalid_capture_file_roster")
    values = []
    for index, row in enumerate(files):
        url = API if index in (0, len(files) - 1) else API + f"/comments?per_page=100&page={index}"
        if row.get("url") != url or row.get("next_page") is not (0 < index < len(files) - 2):
            raise ReplyError("invalid_capture_page_binding")
        raw = read(folder / row["path"])
        if len(raw) != row.get("bytes") or sha(raw) != row.get("sha256"):
            raise ReplyError("capture_file_hash_mismatch")
        values.append(decode(raw))
    check_issue(values[0])
    check_issue(values[-1])
    if (
        values[0]["updated_at"] != values[-1]["updated_at"]
        or values[0]["comments"] != values[-1]["comments"]
    ):
        raise ReplyError("issue_changed_during_collection")
    comments = []
    for page in values[1:-1]:
        if type(page) is not list or len(page) > 100:
            raise ReplyError("comment_page_bound")
        for comment in page:
            check_comment(comment)
        comments.extend(page)
    if (
        len(comments) != values[-1]["comments"]
        or len(comments) != receipt.get("comment_count")
        or len({row["id"] for row in comments}) != len(comments)
    ):
        raise ReplyError("comment_count_or_identity_mismatch")
    owners = [row["id"] for row in comments if owner_comment(row)]
    if owners != receipt.get("observed_owner_comment_ids"):
        raise ReplyError("owner_comment_roster_mismatch")
    return receipt, comments


def engine():
    for name, expected in PINS.items():
        if sha(read(ROOT / name)) != expected:
            raise ReplyError("qualified_dependency_hash_mismatch")
    path = ROOT / "docs/phase2/cohort_overlap_candidate/declared_overlap.py"
    spec = importlib.util.spec_from_file_location("_pro3_reply_qualified_overlap", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prepare(capture, comment_id, output):
    """Copy a selected owner statement; never infer its training identifiers."""
    source = source_check(ROOT)
    output = fresh_output(output)
    receipt, comments = load_capture(capture)
    selected = [row for row in comments if row["id"] == comment_id]
    if len(selected) != 1:
        raise ReplyError("source_comment_not_found")
    comment = selected[0]
    if not owner_comment(comment):
        raise ReplyError("selected_comment_is_not_repository_owner")
    if not comment["body"].strip():
        raise ReplyError("empty_owner_statement")
    candidate = engine()
    template = decode(read(candidate.intake.TEMPLATE_PATH))
    statement = comment["body"].encode("utf-8")
    template["claimant"] = {
        "identity_or_public_handle": comment["user"]["login"],
        "role": "GitHub OWNER association observed; training-run role unverified",
        "source_or_channel_reference": comment["html_url"],
        "statement_date_utc": comment["updated_at"],
    }
    template["evidence_items"] = [
        {
            "reference": comment["html_url"],
            "description": (
                "Captured UTF-8 comment body in statement.txt; claims require separate review"
            ),
            "source_date_utc": comment["updated_at"],
            "sha256": sha(statement),
            "supported_claims": [],
        }
    ]
    draft = encoded(template)
    report = candidate.compare_bytes(
        draft, read(ROOT / "docs/phase2/evaluation_recording_provenance_package_20261011.json")
    )
    if source_check(ROOT) != source:
        raise ReplyError("canonical_source_changed")
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for name, raw in (
        ("statement.txt", statement),
        ("selected-comment.json", encoded(comment)),
        ("claim-draft.json", draft),
        ("declared-overlap.json", encoded(report)),
    ):
        with (output / name).open("xb") as stream:
            stream.write(raw)
        files.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
    result = {
        "schema": "pro3_unsigned_owner_reply_review_draft_v1",
        "prepared_utc": datetime.now(UTC).isoformat(),
        "capture_receipt_sha256": sha(read(local_path(capture) / "receipt.json")),
        "capture_observed_utc": receipt["observed_utc"],
        "source_comment_id": comment_id,
        "source_url": comment["html_url"],
        "source_created_utc": comment["created_at"],
        "source_updated_utc": comment["updated_at"],
        "canonical_source_sha256": source,
        "workflow_sha256": sha(Path(__file__).read_bytes()),
        "qualified_dependency_pins": PINS,
        "draft_role": "local_review_draft; not an author-supplied manifest",
        "complete": True,
        "files": files,
        "training_identifiers_extracted_automatically": False,
        "claimant_authenticated": False,
        "training_run_link_verified": False,
        "cohort_coverage_verified": False,
        "scientific_gate_a_signed": False,
        "experiment_freeze_signed": False,
        "scientific_admission": False,
        "original_case_attempts_remaining": 0,
    }
    write_json(output / "receipt.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    get = commands.add_parser("collect", help="One read-only issue/comment capture")
    get.add_argument("--output", type=Path, required=True)
    draft = commands.add_parser("prepare", help="Offline unsigned owner-comment review draft")
    draft.add_argument("--capture", type=Path, required=True)
    draft.add_argument("--comment-id", type=int, required=True)
    draft.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (
            collect(args.output)
            if args.command == "collect"
            else prepare(args.capture, args.comment_id, args.output)
        )
    except ReplyError as exc:
        print(
            json.dumps({"complete": False, "error_code": str(exc), "scientific_admission": False})
        )
        return 2
    except Exception:
        print(
            json.dumps(
                {
                    "complete": False,
                    "error_code": "metadata_operation_failed",
                    "scientific_admission": False,
                }
            )
        )
        return 2
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "schema",
                    "complete",
                    "scientific_admission",
                    "original_case_attempts_remaining",
                )
            },
            sort_keys=True,
        )
    )
    if args.command == "collect":
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in ("status", "comment_count", "observed_owner_comment_ids")
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
