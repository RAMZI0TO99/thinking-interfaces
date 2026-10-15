"""Source-only byte and syntax inventory; never imports project code or runs tests.

The output is an authoring audit, not native runtime or canonical qualification.
Run from this checkout with Python -I -S -B and an unused output filename.
"""

import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
output = Path(sys.argv[1])
manifest = json.loads((ROOT / "tools/migration/source-files.json").read_bytes())
rows = []
for record in manifest["files"]:
    raw = (ROOT / record["path"]).read_bytes()
    rows.append({
        "path": record["path"],
        "observed_sha256": hashlib.sha256(raw).hexdigest(),
        "expected_sha256": record["sha256"],
        "exact_bytes_match": hashlib.sha256(raw).hexdigest() == record["sha256"],
        "lf_normalized_match": (
            hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == record["lf_sha256"]
        ),
    })
candidate = ROOT / "docs/phase2/cho51_recorder_collection_v1"
syntax = []
for path in sorted(candidate.glob("*.py")):
    raw = path.read_bytes()
    ast.parse(raw, filename=str(path))
    syntax.append({
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "syntax_parsed": True, "imported_or_executed": False,
    })
result = {
    "schema": "pro3_source_authoring_review_v1",
    "observed_utc": datetime.now(timezone.utc).isoformat(),
    "historical_manifest_source_sha256": manifest["source_sha256"],
    "manifest_files": len(rows),
    "exact_matches": sum(row["exact_bytes_match"] for row in rows),
    "lf_normalized_matches": sum(row["lf_normalized_match"] for row in rows),
    "changed_bytes": [row for row in rows if not row["exact_bytes_match"]],
    "config_files": [row for row in rows if row["path"].startswith("configs/")],
    "candidate_syntax": syntax,
    "canonical_files_rewritten": False,
    "project_code_imported_or_executed": False,
    "tests_or_native_jobs_started": False,
    "runtime_validation_passed": False,
}
with output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({key: result[key] for key in (
    "manifest_files", "exact_matches", "lf_normalized_matches",
    "canonical_files_rewritten", "tests_or_native_jobs_started",
)}))
