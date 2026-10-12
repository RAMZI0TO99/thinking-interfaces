"""Hash-checked historical restore, source normalization and public asset fetch."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, digest, read_json, replace_new, safe_path, source_check

HISTORY_MANIFEST = "evidence/portable-20261012-v2/manifest.json"


def normalize(root: Path):
    source_check(root, normalize=True)
    if not (root / ".git").is_dir():
        raise ValueError("bootstrap requires an ordinary Git clone")
    # This local overlay does not alter the frozen root .gitattributes or Git blobs.
    attributes = safe_path(root, ".git/info/attributes")
    attributes.parent.mkdir(parents=True, exist_ok=True)
    begin = "# BEGIN thinking-interfaces portable source\n"
    end = "# END thinking-interfaces portable source\n"
    previous = attributes.read_text() if attributes.exists() else ""
    if begin in previous:
        start = previous.index(begin)
        stop = previous.index(end, start) + len(end)
        previous = previous[:start] + previous[stop:]
    rows = read_json(root / "tools/migration/source-files.json")["files"]
    block = begin + "".join('"/' + row["path"] + '" text eol=lf\n' for row in rows) + end
    attributes.write_text(previous.rstrip("\n") + "\n" + block, encoding="utf-8", newline="\n")
    import subprocess
    subprocess.run(["git", "config", "--local", "core.autocrlf", "false"], cwd=root, check=True)
    print("Exact source bytes restored: " + source_check(root))


def history_preflight(root: Path, manifest: dict):
    rows = {}
    seen = set()
    for row in manifest["files"]:
        relative = row["path"]
        if not relative.startswith(("runs/", "checkpoints/", "data/processed/", ".cache/phase2/")):
            raise ValueError("history target is outside allowlisted roots")
        if relative.casefold() in seen:
            raise ValueError("duplicate/aliased history target")
        seen.add(relative.casefold())
        path = safe_path(root, relative)
        if path.exists() and (not path.is_file() or path.stat().st_size != row["bytes"]
                              or digest(path) != row["sha256"]):
            raise ValueError("conflicting historical file refused: " + relative)
        rows[relative] = row
    if sum(row["bytes"] for row in rows.values()) != manifest["uncompressed_bytes"]:
        raise ValueError("history size ledger differs")
    return rows


def restore_history(root: Path):
    manifest = read_json(root / HISTORY_MANIFEST)
    rows = history_preflight(root, manifest)
    work = safe_path(root, ".cache/migration")
    work.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < manifest["uncompressed_bytes"] + 20 * 1024**3:
        raise ValueError("history restore requires archive space plus a 20 GiB free disk floor")
    archive = work / ("history-" + uuid.uuid4().hex + ".tar.xz")
    try:
        total = 0
        with archive.open("xb") as target:
            for row in manifest["parts"]:
                path = safe_path(root, row["path"])
                if not path.exists() and "github_asset" in row:
                    from github import download_asset
                    download_asset(root, row)
                if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
                    raise ValueError("history archive part differs")
                with path.open("rb") as stream:
                    shutil.copyfileobj(stream, target, length=1024**2)
                total += row["bytes"]
        if total != manifest["archive_bytes"] or digest(archive) != manifest["archive_sha256"]:
            raise ValueError("complete archive differs")
        consumed = set()
        restored = 0
        with tarfile.open(archive, mode="r|*") as source:
            for info in source:
                if not info.isfile() or info.name not in rows or info.name in consumed:
                    raise ValueError("unexpected, duplicated or linked archive member")
                row = rows[info.name]
                if info.size != row["bytes"]:
                    raise ValueError("history member size differs")
                destination = safe_path(root, info.name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                stream = source.extractfile(info)
                h = hashlib.sha256()
                # Even skipped members are checked against their independent ledger.
                temp = destination.with_name(destination.name + ".restore-" + uuid.uuid4().hex)
                try:
                    with temp.open("xb") as target:
                        while block := stream.read(1024**2):
                            target.write(block)
                            h.update(block)
                    if h.hexdigest() != row["sha256"] or temp.stat().st_size != row["bytes"]:
                        raise ValueError("history member digest differs")
                    if destination.exists():
                        if digest(destination) != row["sha256"]:
                            raise ValueError("historical destination changed during restore")
                    else:
                        replace_new(temp, destination)
                        restored += 1
                finally:
                    if temp.exists():
                        temp.unlink()
                consumed.add(info.name)
        if consumed != set(rows):
            raise ValueError("archive is incomplete")
        print(f"Verified {len(rows)} historical files; restored {restored}. Old admissions remain expired.")
    finally:
        if archive.exists():
            archive.unlink()


def fetch_one(root: Path, row: dict):
    destination = safe_path(root, row["path"])
    if destination.exists():
        if destination.stat().st_size != row["bytes"] or digest(destination) != row["sha256"]:
            raise ValueError("existing asset differs; preserved: " + row["path"])
        return "verified"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < row["bytes"] + 20 * 1024**3:
        raise ValueError("download requires asset size plus 20 GiB free disk")
    temp = destination.with_name(destination.name + ".download-" + uuid.uuid4().hex)
    count = 0
    h = hashlib.sha256()
    if not row["url"].startswith("https://"):
        raise ValueError("HTTPS download required")
    request = urllib.request.Request(row["url"], headers={"User-Agent": "thinking-interfaces-migration/1"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response, temp.open("xb") as target:
            if not response.url.startswith("https://"):
                raise ValueError("insecure redirect refused")
            while block := response.read(1024**2):
                count += len(block)
                if count > row["bytes"]:
                    raise ValueError("download exceeds expected size")
                target.write(block)
                h.update(block)
        if count != row["bytes"] or h.hexdigest() != row["sha256"]:
            raise ValueError("download digest/size differs: " + row["path"])
        replace_new(temp, destination)
    finally:
        if temp.exists():
            temp.unlink()
    return "downloaded"


def fetch(root: Path, dataset: str, subjects=None):
    manifest = read_json(root / "tools/migration/assets.json")
    rows = [row for row in manifest["assets"] if row["dataset"] == dataset
            and (subjects is None or row["subject"] in subjects)]
    if not rows:
        raise ValueError("no assets selected")
    for row in rows:
        print(fetch_one(root, row) + ": " + row["path"], flush=True)
    if dataset == "weights":
        refs = safe_path(root, ".cache/huggingface/hub/models--braindecode--labram-pretrained/refs/main")
        refs.parent.mkdir(parents=True, exist_ok=True)
        revision = manifest["hf_revision"]
        if refs.exists() and refs.read_text().strip() != revision:
            raise ValueError("HF main reference differs; existing reference preserved")
        if not refs.exists():
            refs.write_text(revision, encoding="ascii")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("normalize", "history", "fetch"))
    parser.add_argument("--dataset", choices=("bci_iv_2a", "cho2017", "mmidb", "weights"))
    parser.add_argument("--subjects", nargs="+", type=int)
    args = parser.parse_args()
    if args.mode == "normalize":
        normalize(ROOT)
    elif args.mode == "history":
        restore_history(ROOT)
    else:
        if args.dataset is None:
            parser.error("fetch requires --dataset")
        fetch(ROOT, args.dataset, args.subjects)


if __name__ == "__main__":
    main()
