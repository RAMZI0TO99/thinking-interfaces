"""Qualify staged reply tools in a fresh Windows checkout at a different path."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
DESTINATION = ROOT / "tmp/Provenance Windows checkout 001"
assert DESTINATION.resolve().is_relative_to((ROOT / "tmp").resolve())
assert not DESTINATION.exists()
DESTINATION.mkdir(parents=True, exist_ok=False)

tree = subprocess.run(
    ["git", "write-tree"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30
).stdout.strip()
subprocess.run(
    [
        "git", "-c", "core.autocrlf=true", "-c", "core.eol=crlf",
        "checkout-index", "--all", "--prefix=" + DESTINATION.as_posix() + "/",
    ],
    cwd=ROOT, capture_output=True, check=True, timeout=60,
)
normalize = (
    "import sys; from pathlib import Path; root=Path.cwd(); "
    "sys.path.insert(0,str(root/'tools/migration')); "
    "from common import source_check; print(source_check(root,normalize=True))"
)
result = subprocess.run(
    [sys.executable, "-I", "-S", "-B", "-c", normalize],
    cwd=DESTINATION, capture_output=True, text=True, check=True, timeout=30,
)
source = result.stdout.strip()
manifest = json.loads((ROOT / "tools/provenance/qualified/manifest.json").read_bytes())
identities = []
for row in manifest["files"]:
    raw = (DESTINATION / "tools/provenance/qualified" / row["path"]).read_bytes()
    assert len(raw) == row["bytes"]
    assert hashlib.sha256(raw).hexdigest() == row["sha256"]
    identities.append(row)
tests = subprocess.run(
    [sys.executable, "-I", "-S", "-B", "tools/provenance/test_reply.py"],
    cwd=DESTINATION, capture_output=True, text=True, timeout=120,
)
out = ROOT / "runs/coordination/provenance_reply_workflow_20261012_v1/checkout_001"
out.mkdir(exist_ok=False)
(out / "tests.log").write_text(tests.stdout + tests.stderr, encoding="utf-8")
assert tests.returncode == 0, tests.stderr[-1500:]
assert "Ran 33 tests" in tests.stderr and tests.stderr.rstrip().endswith("OK")
receipt = {
    "schema": "pro3_reply_workflow_windows_checkout_qualification_v1",
    "accepted": True,
    "checkout_path": DESTINATION.relative_to(ROOT).as_posix(),
    "candidate_index_tree": tree,
    "autocrlf": True,
    "core_eol": "crlf",
    "canonical_source_sha256": source,
    "byte_identical_qualified_dependencies": identities,
    "behavioral_tests_passed": 33,
    "public_api_or_network_used": False,
    "scientific_admission": False,
}
with (out / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(receipt, indent=2))
print(tests.stderr[-1000:])
