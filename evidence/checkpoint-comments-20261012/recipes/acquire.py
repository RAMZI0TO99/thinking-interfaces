"""Bounded read-only GitHub issue/comment acquisition; no model or posting."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools/migration"))
import github
from common import source_check, write_json

API_ROOT = "https://api.github.com/repos/935963004/LaBraM"
OUT = ROOT / "runs/coordination/checkpoint_comments_20261012_v1/acquisition_001"


def main():
    source = source_check(ROOT)
    OUT.mkdir(parents=True, exist_ok=False)
    credential = github.token()
    captures = []

    def get(suffix: str, name: str):
        with github.request(API_ROOT + suffix, credential, method="GET") as response:
            raw = response.read(2 * 1024**2 + 1)
            if len(raw) > 2 * 1024**2:
                raise ValueError("response exceeds reviewed metadata bound")
            link = response.headers.get("Link", "")
            remaining = response.headers.get("X-RateLimit-Remaining")
        path = OUT / name
        with path.open("xb") as stream:
            stream.write(raw)
        captures.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "url": API_ROOT + suffix,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "next_page": 'rel="next"' in link,
                "rate_remaining": remaining,
            }
        )
        return json.loads(raw), 'rel="next"' in link

    issues, next_page = get(
        "/issues?state=all&per_page=100&sort=created&direction=asc", "issues.json"
    )
    if next_page or not isinstance(issues, list) or len(issues) > 100:
        raise ValueError("issue list exceeds the reviewed single-page scope")
    rows = []
    for issue in issues:
        number = issue["number"]
        comments = []
        for page in (1, 2):
            values, more = get(
                f"/issues/{number}/comments?per_page=100&page={page}",
                f"issue_{number:03d}_comments_{page}.json",
            )
            if not isinstance(values, list):
                raise ValueError("comment response is not a list")
            comments.extend(values)
            if not more:
                break
        if more or len(comments) != issue["comments"]:
            raise ValueError(f"comments changed or exceed bounded pages for issue {number}")
        rows.append(
            {
                "number": number,
                "title": issue["title"],
                "url": issue["html_url"],
                "is_pull_request": "pull_request" in issue,
                "comments": len(comments),
                "owner_comments": sum(c["author_association"] == "OWNER" for c in comments),
            }
        )
        print(f"Read #{number}: {len(comments)} public comments", flush=True)
    summary = {
        "schema": "labram_public_comment_acquisition_v1",
        "observed_utc": datetime.now(UTC).isoformat(),
        "canonical_source_sha256": source,
        "repository": "935963004/LaBraM",
        "issue_or_pr_count": len(rows),
        "comment_count": sum(r["comments"] for r in rows),
        "all_listed_issue_comment_pages_complete": True,
        "rows": rows,
        "captures": captures,
        "posting_performed": False,
        "checkpoint_cohort_authenticated": False,
        "scientific_admission": False,
        "original_case_attempts_remaining": 0,
    }
    write_json(OUT / "summary.json", summary)
    print(
        json.dumps({k: v for k, v in summary.items() if k not in {"rows", "captures"}}), flush=True
    )


if __name__ == "__main__":
    main()
