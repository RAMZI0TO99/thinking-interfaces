"""Read-only clone readiness checks; never treats historical receipts as admission."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, digest, npz_members, read_json, safe_path, source_check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-history", action="store_true")
    parser.add_argument("--verify-assets", action="store_true")
    parser.add_argument("--verify-caches", action="store_true")
    parser.add_argument("--imports", choices=("core", "full"))
    args = parser.parse_args()
    result = {"source_sha256": source_check(ROOT), "missing": {}, "verified": {},
              "scientific_admission": False, "original_case_attempts_remaining": 0}
    history = read_json(ROOT / "evidence/portable-20261012-v2/manifest.json")
    assets = read_json(ROOT / "tools/migration/assets.json")["assets"]
    caches = read_json(ROOT / "tools/migration/caches.json")["caches"]
    for name, rows, verify in (("history", history["files"], args.verify_history),
                               ("assets", assets, args.verify_assets),
                               ("caches", caches, args.verify_caches)):
        missing = verified = 0
        for row in rows:
            path = safe_path(ROOT, row["path"])
            if not path.is_file():
                missing += 1
            elif verify:
                if name == "caches":
                    if npz_members(path) != row["members"]:
                        raise ValueError("cache arrays differ: " + row["path"])
                elif path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
                    raise ValueError("file identity differs: " + row["path"])
                verified += 1
        result["missing"][name] = missing
        result["verified"][name] = verified
        if verify and missing:
            raise ValueError(f"{name}: {missing} required files missing")
    if args.imports:
        sys.path.insert(0, str(ROOT))
        from data.runtime import configure_scientific_runtime
        configure_scientific_runtime()
        names = ["numpy", "scipy", "pandas", "sklearn", "core", "evaluation"]
        if args.imports == "full":
            names += ["mne", "moabb", "torch", "torchaudio", "braindecode", "safetensors"]
        result["imports"] = {name: getattr(importlib.import_module(name), "__version__", "project")
                             for name in names}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
