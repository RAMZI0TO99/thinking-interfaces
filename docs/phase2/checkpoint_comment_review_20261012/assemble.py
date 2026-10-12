"""Preserve the completed metadata review with portable byte-identical evidence."""

from __future__ import annotations

import ctypes
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
from common import digest, source_check, write_json

OUT = ROOT / "evidence/checkpoint-comments-20261012"
BASE = ROOT / "runs/coordination/checkpoint_comments_20261012_v1"
JOBS = (
    "20261012T110220Z_70bf55b493",
    "20261012T110733Z_2d5e27de8c",
    "20261012T112320Z_e80ca451ee",
)
QUALITY_SHA = "4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357"
OWNER_SHA = "2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400"


def main():
    source = source_check(ROOT)
    assert digest(ROOT / "runs/quality_status.json") == QUALITY_SHA
    assert digest(ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json") == OWNER_SHA
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / ".gitattributes").write_bytes(b"* -text\n")
    copied = []
    secret_pattern = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{40,})")

    def capture(path, target):
        raw = path.read_bytes()
        assert not secret_pattern.search(raw), "credential-shaped value; preserve privately"
        dest = OUT / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(raw)
        assert digest(path) == digest(dest)
        copied.append(
            {
                "original_path": path.relative_to(ROOT).as_posix(),
                "path": dest.relative_to(OUT).as_posix(),
                "bytes": len(raw),
                "sha256": digest(dest),
            }
        )

    summary = json.loads((BASE / "acquisition_001/summary.json").read_text(encoding="utf-8"))
    for row in summary["captures"]:
        path = ROOT / row["path"]
        assert digest(path) == row["sha256"] and path.stat().st_size == row["bytes"]
        capture(path, "acquisition/" + path.name)
    capture(BASE / "acquisition_001/summary.json", "acquisition/summary.json")
    for name in (
        "authorized-request.json",
        "created-response.json",
        "verified-response.json",
        "verification.json",
        "dedup_page_1.json",
    ):
        capture(BASE / "publication_001" / name, "publication/" + name)
    capture(
        ROOT / "docs/phase2/checkpoint_provenance_public_issue_ready_20261011.md",
        "publication/approved-draft-before-posting.md",
    )
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenJobObjectW.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenJobObjectW.restype = ctypes.c_void_p
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    absence = []
    for job in JOBS:
        folder = ROOT / "runs/migration" / job
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        assert receipt["accepted"] and receipt["job_absent"]
        ctypes.set_last_error(0)
        handle = api.OpenJobObjectW(0x0004, False, receipt["job_name"])
        error = ctypes.get_last_error()
        if handle:
            api.CloseHandle(handle)
            raise ValueError("completed owned Job still exists")
        assert error == 2
        absence.append({"run": job, "job_name": receipt["job_name"], "freshly_absent": True})
        for name in (
            "admission.json",
            "command-result.json",
            "command.log",
            "deadline.json",
            "receipt.json",
        ):
            capture(folder / name, "guards/" + job + "/" + name)
    issues = json.loads((BASE / "acquisition_001/issues.json").read_text(encoding="utf-8"))
    comments = [
        comment
        for row in summary["rows"]
        for comment in json.loads(
            (BASE / f"acquisition_001/issue_{row['number']:03d}_comments_1.json").read_text(
                encoding="utf-8"
            )
        )
    ]
    assert len(issues) == 73 and len(comments) == 222
    corpus = issues + comments
    terms = (
        "7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c",
        "c431221e6cfd23dbfa9950e0180682fb322b0548",
        "MMIDB",
        "Cho2017",
        "IV-2a",
        "manifest",
        "PhysioNet",
        "motor imagery",
    )
    term_hits = {
        term: [
            entry["html_url"]
            for entry in corpus
            if term.casefold() in (entry.get("body") or "").casefold()
        ]
        for term in terms
    }
    verification = json.loads(
        (BASE / "publication_001/verification.json").read_text(encoding="utf-8")
    )
    index = {
        "schema": "portable_checkpoint_comment_review_v1",
        "assembled_utc": datetime.now(UTC).isoformat(),
        "acquisition_observed_utc": summary["observed_utc"],
        "canonical_source_sha256": source,
        "historical_quality_sha256": QUALITY_SHA,
        "owner_decision_packet_sha256": OWNER_SHA,
        "issue_count": sum("pull_request" not in row for row in issues),
        "pull_request_entry_count": sum("pull_request" in row for row in issues),
        "comment_count": len(comments),
        "owner_comment_count": sum(row["author_association"] == "OWNER" for row in comments),
        "listed_issue_comment_pages_complete": summary["all_listed_issue_comment_pages_complete"],
        "literal_body_term_hits_before_our_issue": term_hits,
        "limitations": [
            "PR inline review comments",
            "Discussions",
            "images and attachments",
            "deleted historical entries",
            "external archives and repositories",
            "future comments",
        ],
        "public_request": verification,
        "maintainer_response_reviewed": False,
        "checkpoint_recording_coverage": "unknown",
        "evaluation_overlap": "unknown",
        "scientific_admission": False,
        "gate_a_signed": False,
        "experiment_freeze_signed": False,
        "owner_decisions_signed": False,
        "original_case_attempts_remaining": 0,
        "fresh_owned_job_absence": absence,
        "credential_pattern_scan": "no GitHub credential-shaped values found in copied bytes",
        "files": copied,
    }
    assert source_check(ROOT) == source
    assert digest(ROOT / "runs/quality_status.json") == QUALITY_SHA
    assert digest(ROOT / "docs/phase2/cho_owner_decision_packet_20261010.json") == OWNER_SHA
    write_json(OUT / "index.json", index)
    print(
        json.dumps(
            {
                "files": len(copied),
                "bytes": sum(r["bytes"] for r in copied),
                "issue_url": verification["url"],
                "all_owned_jobs_freshly_absent": True,
                "literal_term_hit_counts": {k: len(v) for k, v in term_hits.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
