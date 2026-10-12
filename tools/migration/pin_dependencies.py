"""Maintainer-only conversion of public pip resolutions into complete wheel hash locks."""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, write_json


def entries(relative):
    report = json.loads((ROOT / relative).read_bytes())
    rows = {}
    for entry in report["install"]:
        url = entry["download_info"]["url"]
        if not url.startswith(
            (
                "https://files.pythonhosted.org/",
                "https://download.pytorch.org/",
                "https://download-r2.pytorch.org/",
            )
        ) or not url.endswith(".whl"):
            raise ValueError("public wheel URL required")
        sha = entry["download_info"]["archive_info"].get("hashes", {}).get("sha256")
        if sha is None:
            # Three PyTorch mirror wheel metadata records omitted their hashes.
            # Fetch bounded wheel bytes; do not substitute a different mirror build.
            h = hashlib.sha256()
            count = 0
            with urllib.request.urlopen(url, timeout=45) as response:
                while block := response.read(1024**2):
                    count += len(block)
                    if count > 4 * 1024**2:
                        raise ValueError("unhashed wheel exceeds metadata export bound")
                    h.update(block)
            sha = h.hexdigest()
        metadata = entry["metadata"]
        rows[metadata["name"].lower().replace("_", "-")] = {
            "name": metadata["name"],
            "version": metadata["version"],
            "url": url,
            "sha256": sha,
        }
    return rows


def main():
    core = entries("runs/migration_core_resolve_001.json")
    full = entries("runs/migration_dependency_resolve_001.json")
    full["wheel"] = core["wheel"]
    for name, rows in (("core", core), ("full", full)):
        lock = ROOT / f"tools/migration/requirements-windows-{name}.lock"
        if lock.exists():
            raise ValueError("wheel lock already exists")
        lines = [
            "# Complete Windows x64 / CPython 3.12 wheel resolution, 2026-10-12.",
            "# Original requirements*.lock files retain their historical bytes.",
        ]
        lines += [
            f"{r['name']} @ {r['url']} --hash=sha256:{r['sha256']}" for _, r in sorted(rows.items())
        ]
        lock.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_json(
        ROOT / "tools/migration/dependency-resolution.json",
        {
            "schema": "windows_wheel_resolution_v1",
            "python": "3.12",
            "platform": "win_amd64",
            "resolved_utc_date": "2026-10-12",
            "core": list(core.values()),
            "full": list(full.values()),
            "limitation": (
                "Public resolver and wheel identities; fresh installation/import "
                "tests are separate evidence."
            ),
        },
    )
    print(json.dumps({"core_wheels": len(core), "full_wheels": len(full)}))


if __name__ == "__main__":
    main()
