"""Maintainer export of portable identities and compact, inert historical evidence."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import stat
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SOURCE_SHA, digest, npz_members, write_json

EXCLUDED_COMPONENTS = {
    "site-packages",
    "__pycache__",
    ".venv",
    "venv",
    "Lib",
    "Scripts",
    "Include",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
    "migration",
    "migration_export",
}
SECRET = re.compile(
    rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|"
    rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}|AKIA[A-Z0-9]{16}|"
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def identities():
    spec = importlib.util.spec_from_file_location("_export_provenance", ROOT / "core/provenance.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    paths = module.source_files(ROOT)
    source = module.source_fingerprint(ROOT)
    if source != SOURCE_SHA or len(paths) != 432:
        raise ValueError("settled source differs")
    source_rows = []
    for path in paths:
        raw = path.read_bytes()
        normalized = raw.replace(b"\r\n", b"\n")
        eol = "crlf" if b"\r\n" in raw else "lf"
        if eol == "crlf" and normalized.replace(b"\n", b"\r\n") != raw:
            eol = "mixed"
        source_rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "lf_sha256": hashlib.sha256(normalized).hexdigest(),
                "eol": eol,
                "crlf_lines": [
                    i
                    for i, line in enumerate(raw.splitlines(keepends=True))
                    if line.endswith(b"\r\n")
                ],
            }
        )
    write_json(
        ROOT / "tools/migration/source-files.json",
        {"schema": "portable_source_v1", "source_sha256": source, "files": source_rows},
    )
    inventory = json.loads(
        (ROOT / "docs/phase2/evaluation_recording_provenance_package_20261011.json").read_bytes()
    )
    raw_paths = {}
    for path in (ROOT / "data/raw").rglob("*"):
        if path.suffix.lower() in {".edf", ".mat"}:
            if path.name in raw_paths:
                raise ValueError("ambiguous raw filename")
            raw_paths[path.name] = path
    assets = []
    for row in inventory["recordings"]:
        path = raw_paths[row["filename"]]
        dataset = row["dataset"]
        if dataset == "mmidb":
            url = "https://physionet.org/files/eegmmidb/1.0.0/" + row["publisher_recording_path"]
        elif dataset == "bci_iv_2a":
            url = "https://lampx.tugraz.at/~bci/database/001-2014/" + row["filename"]
        elif dataset == "cho2017":
            url = (
                "https://s3.ap-northeast-1.wasabisys.com/gigadb-datasets/live/pub/"
                "10.5524/100001_101000/100295/mat_data/" + row["filename"]
            )
        else:
            raise ValueError("unknown dataset")
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError("raw inventory differs")
        assets.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "dataset": dataset,
                "subject": row["subject_number"],
                "url": url,
            }
        )
    snapshot = "0563b6c626e7b40d9a36653b763715db94d945d7"
    hfbase = ".cache/huggingface/hub/models--braindecode--labram-pretrained/snapshots/" + snapshot
    weights = [
        (
            "checkpoints/labram-base.pth",
            "https://raw.githubusercontent.com/935963004/LaBraM/"
            "c431221e6cfd23dbfa9950e0180682fb322b0548/checkpoints/labram-base.pth",
        ),
        (
            hfbase + "/model.safetensors",
            "https://huggingface.co/braindecode/labram-pretrained/resolve/"
            + snapshot
            + "/model.safetensors",
        ),
        (
            hfbase + "/config.json",
            "https://huggingface.co/braindecode/labram-pretrained/resolve/"
            + snapshot
            + "/config.json",
        ),
    ]
    for relative, url in weights:
        path = ROOT / relative
        assets.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest(path),
                "dataset": "weights",
                "subject": None,
                "url": url,
            }
        )
    write_json(
        ROOT / "tools/migration/assets.json",
        {
            "schema": "verified_assets_v1",
            "hf_revision": snapshot,
            "assets": assets,
            "limitation": (
                "Content identity does not establish checkpoint training provenance "
                "or scientific approval."
            ),
        },
    )
    caches = []
    for path in sorted((ROOT / "data/processed").rglob("*.npz")):
        relative = path.relative_to(ROOT).as_posix()
        parts = relative.split("/")
        caches.append(
            {
                "path": relative,
                "dataset": parts[2],
                "profile": parts[3],
                "subject": int(path.stem.split("_")[1]),
                "bytes": path.stat().st_size,
                "container_sha256": digest(path),
                "members": npz_members(path),
            }
        )
    if len(caches) != 410:
        raise ValueError("cache roster differs")
    write_json(
        ROOT / "tools/migration/caches.json",
        {
            "schema": "verified_cache_arrays_v1",
            "caches": caches,
            "verification": (
                "Compare uncompressed .npy bytes; NPZ timestamps/compression can differ."
            ),
        },
    )
    print(
        json.dumps(
            {
                "source_files": len(paths),
                "raw_assets": len(assets) - 3,
                "weight_assets": 3,
                "cache_artifacts": len(caches),
            }
        ),
        flush=True,
    )


def selected_files():
    roots = [ROOT / "runs", ROOT / "checkpoints", ROOT / ".cache/phase2", ROOT / "data/processed"]
    for root in roots:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or set(relative.parts) & EXCLUDED_COMPONENTS:
                continue
            if root.name == "processed" and path.suffix != ".json":
                continue
            if path.name == "labram-base.pth" or path.suffix in {
                ".db",
                ".db-wal",
                ".db-shm",
                ".pyc",
            }:
                continue
            if path.name.startswith(".env") or path.name == "local.toml":
                raise ValueError("local configuration found in history export")
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
                raise ValueError("history links refused")
            yield path


def history():
    out = ROOT / "evidence/portable-20261012-v2"
    out.mkdir(parents=True, exist_ok=False)
    paths = list(selected_files())
    # Put similar large checkpoint files together for bounded long-range compression.
    paths.sort(key=lambda p: (p.suffix, p.relative_to(ROOT).as_posix()))
    rows = []
    total = 0
    start = time.monotonic()
    text_suffixes = {
        ".json",
        ".jsonl",
        ".txt",
        ".log",
        ".md",
        ".py",
        ".ps1",
        ".toml",
        ".csv",
        ".yml",
        ".yaml",
        ".patch",
        ".diff",
        ".sh",
    }
    # The first long-range compression attempt reached its finite deadline.
    # Use fast streaming compression in this fresh namespace, retaining all bytes.
    with (
        gzip.open(out / "history.tar.gz", "wb", compresslevel=1) as compressed,
        tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive,
    ):
        for number, path in enumerate(paths, 1):
            relative = path.relative_to(ROOT).as_posix()
            info = path.stat()
            if (
                path.suffix in text_suffixes
                and info.st_size < 64 * 1024**2
                and SECRET.search(path.read_bytes())
            ):
                raise ValueError("credential pattern found; path only: " + relative)
            sha = digest(path)
            tarinfo = tarfile.TarInfo(relative)
            tarinfo.size = info.st_size
            tarinfo.mtime = 0
            tarinfo.mode = 0o644
            with path.open("rb") as stream:
                archive.addfile(tarinfo, stream)
            after = path.stat()
            if (info.st_ino, info.st_size, info.st_mtime_ns) != (
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError("history file changed during export")
            rows.append({"path": relative, "bytes": info.st_size, "sha256": sha})
            total += info.st_size
            if number % 2000 == 0:
                print(
                    json.dumps(
                        {"files": number, "bytes": total, "seconds": time.monotonic() - start}
                    ),
                    flush=True,
                )
    archive = out / "history.tar.gz"
    archive_sha = digest(archive)
    parts = []
    with archive.open("rb") as stream:
        number = 0
        while block := stream.read(40 * 1024**2):
            number += 1
            path = out / f"history.tar.gz.{number:03d}"
            path.write_bytes(block)
            parts.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "bytes": len(block),
                    "sha256": hashlib.sha256(block).hexdigest(),
                }
            )
    write_json(
        out / "manifest.json",
        {
            "schema": "inert_history_v1",
            "source_sha256": SOURCE_SHA,
            "created_utc_date": "2026-10-12",
            "historical_workspace": "D:/Aenv/pro3",
            "archive_sha256": archive_sha,
            "archive_bytes": archive.stat().st_size,
            "uncompressed_bytes": total,
            "files": rows,
            "parts": parts,
            "excluded": [
                "Copied virtual environments and disposable tool caches",
                "Raw recordings and processed NPZs (verified downloads/rebuilds)",
                "Public original LaBraM weights (verified downloads)",
            ],
            "authority": (
                "Dated, inert evidence only. Old absolute paths, deadlines, leases "
                "and execution helpers are not portable admission."
            ),
        },
    )
    # Keep original compressed bytes private; only bounded parts enter Git.
    private = ROOT / "runs/migration_export"
    private.mkdir(exist_ok=True)
    archive.rename(private / "history-20261012-v2.tar.gz")
    print(
        json.dumps(
            {
                "files": len(rows),
                "uncompressed_bytes": total,
                "archive_bytes": sum(p["bytes"] for p in parts),
                "parts": len(parts),
                "seconds": time.monotonic() - start,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("identities", "history"))
    args = parser.parse_args()
    identities() if args.mode == "identities" else history()
