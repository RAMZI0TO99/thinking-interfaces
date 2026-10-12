"""Publish only the exact, explicitly authorized checkpoint provenance request."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
import github
from common import digest, source_check, write_json

OUT = ROOT / "runs/coordination/checkpoint_comments_20261012_v1/publication_001"
REQUEST = OUT / "authorized-request.json"
EXPECTED_DRAFT = "5563ed7a099de9a9d031a04773e491cf42d78503ebcb2fb4c29492835d53f52c"
EXPECTED_BODY = "e8db8f6c1e690df9b1ceb763797dea21ae51acdac8233c29b3128881c272eed5"
API = "https://api.github.com/repos/935963004/LaBraM"


def body_hash(body):
    return hashlib.sha256(body.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def read_response(response, name):
    raw = response.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("metadata response exceeds the bound")
    with (OUT / name).open("xb") as stream:
        stream.write(raw)
    return json.loads(raw)


def main():
    source = source_check(ROOT)
    authorized = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert authorized["repository"] == "935963004/LaBraM"
    assert authorized["account"] == "RAMZI0TO99"
    assert authorized["attachments"] == []
    assert digest(ROOT / authorized["draft_path"]) == EXPECTED_DRAFT
    assert authorized["draft_sha256"] == EXPECTED_DRAFT
    assert body_hash(authorized["body"]) == EXPECTED_BODY
    assert authorized["body_sha256"] == EXPECTED_BODY
    assert authorized["original_case_attempts_remaining"] == 0
    assert authorized["scientific_admission"] is False
    assert not (OUT / "verification.json").exists(), "preserve the existing receipt"

    credential = github.token()
    with github.request("https://api.github.com/user", credential) as response:
        account = read_response(response, "account.json")
    assert account["login"] == authorized["account"]
    with github.request(API, credential) as response:
        repository = read_response(response, "repository.json")
    assert repository["full_name"] == authorized["repository"]
    assert repository["has_issues"] and not repository["archived"]

    candidates = []
    for page in (1, 2):
        url = API + "/issues?state=all&per_page=100&page=" + str(page)
        with github.request(url, credential) as response:
            rows = read_response(response, f"dedup_page_{page}.json")
            next_page = 'rel="next"' in response.headers.get("Link", "")
        candidates.extend(
            row
            for row in rows
            if row["title"] == authorized["title"]
            and row["user"]["login"] == authorized["account"]
            and "pull_request" not in row
        )
        if not next_page:
            break
    else:
        raise ValueError("deduplication listing exceeded two pages; no POST")
    if len(candidates) > 1:
        raise ValueError("multiple matching requests; no POST")
    reused = bool(candidates)
    if reused:
        issue = candidates[0]
        assert body_hash(issue["body"]) == EXPECTED_BODY, "existing title/body conflict"
        status = None
    else:
        payload = json.dumps(
            {"title": authorized["title"], "body": authorized["body"]},
            ensure_ascii=False,
        ).encode("utf-8")
        # Single POST only. On transport failure, keep the evidence and discover
        # the server result with a read-only GET before any operator retry.
        with github.request(
            API + "/issues",
            credential,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        ) as response:
            status = response.status
            issue = read_response(response, "created-response.json")
        assert status == 201
    number = issue["number"]
    with github.request(API + "/issues/" + str(number), credential) as response:
        verified = read_response(response, "verified-response.json")
        get_status = response.status
    assert verified["id"] == issue["id"]
    assert verified["user"]["login"] == authorized["account"]
    assert verified["title"] == authorized["title"]
    assert body_hash(verified["body"]) == EXPECTED_BODY
    assert verified["html_url"] == f"https://github.com/935963004/LaBraM/issues/{number}"
    assert source_check(ROOT) == source
    receipt = {
        "schema": "verified_authorized_provenance_issue_v1",
        "observed_utc": datetime.now(UTC).isoformat(),
        "authorization_request_sha256": digest(REQUEST),
        "repository": authorized["repository"],
        "account": verified["user"]["login"],
        "title": verified["title"],
        "body_sha256": body_hash(verified["body"]),
        "attachments": [],
        "issue_number": number,
        "issue_id": verified["id"],
        "url": verified["html_url"],
        "created_utc": verified["created_at"],
        "post_http_status": status,
        "verification_get_http_status": get_status,
        "reused_existing_exact_issue": reused,
        "exact_title_account_repository_body_verified": True,
        "canonical_source_sha256": source,
        "original_case_attempts_remaining": 0,
        "scientific_admission": False,
    }
    write_json(OUT / "verification.json", receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
