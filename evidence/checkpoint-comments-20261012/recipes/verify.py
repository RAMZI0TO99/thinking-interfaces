"""Offline identity verification for the portable public-provenance evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import source_check

OUT = ROOT / "evidence/checkpoint-comments-20261012"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    index = load(OUT / "index.json")
    assert source_check(ROOT) == index["canonical_source_sha256"]
    checked = set()
    for row in index["files"]:
        path = OUT / row["path"]
        assert path.resolve().is_relative_to(OUT.resolve())
        assert row["path"] not in checked
        checked.add(row["path"])
        raw = path.read_bytes()
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"], row["path"]
    issues = load(OUT / "acquisition/issues.json")
    summary = load(OUT / "acquisition/summary.json")
    assert len(issues) == 73
    assert sum("pull_request" in row for row in issues) == 6
    total = 0
    owners = 0
    for issue in issues:
        comments = load(OUT / f"acquisition/issue_{issue['number']:03d}_comments_1.json")
        assert len(comments) == issue["comments"]
        total += len(comments)
        owners += sum(comment["author_association"] == "OWNER" for comment in comments)
    assert total == index["comment_count"] == summary["comment_count"] == 222
    assert owners == index["owner_comment_count"] == 65
    assert all(not row["next_page"] for row in summary["captures"])
    authorized = load(OUT / "publication/authorized-request.json")
    verified = load(OUT / "publication/verified-response.json")
    receipt = load(OUT / "publication/verification.json")
    assert receipt == index["public_request"]
    assert (
        sha((OUT / "publication/authorized-request.json").read_bytes())
        == receipt["authorization_request_sha256"]
    )
    assert (
        sha((OUT / "publication/approved-draft-before-posting.md").read_bytes())
        == authorized["draft_sha256"]
    )
    assert verified["title"] == authorized["title"] == receipt["title"]
    assert verified["user"]["login"] == authorized["account"] == "RAMZI0TO99"
    assert authorized["body"] == verified["body"].replace("\r\n", "\n")
    assert sha(authorized["body"].encode("utf-8")) == receipt["body_sha256"]
    assert verified["html_url"] == receipt["url"] == "https://github.com/935963004/LaBraM/issues/75"
    assert authorized["attachments"] == receipt["attachments"] == []
    assert not index["scientific_admission"] and index["original_case_attempts_remaining"] == 0
    for path in (OUT / "guards").glob("*/receipt.json"):
        guard = load(path)
        assert guard["accepted"] and guard["job_absent"]
        assert not guard["scientific_admission"]
    print(
        json.dumps(
            {
                "offline_identity_check": "PASS",
                "files_verified": len(checked),
                "issues": 67,
                "pr_entries": 6,
                "comments": total,
                "owner_comments": owners,
                "exact_public_request_verified": True,
                "scientific_admission": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
