"""Portable migration primitives. No scientific execution or pickle loading."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = "3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529"
GIB = 1024**3


def io_path(path: Path) -> Path:
    """Use Windows extended paths for history names exceeding MAX_PATH."""
    if os.name != "nt":
        return path
    value = str(path.absolute())
    if value.startswith("\\\\?\\"):
        return path
    if value.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + value[2:])
    return Path("\\\\?\\" + value)


def digest(path: Path) -> str:
    with io_path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(io_path(path).read_bytes())


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def safe_path(root: Path, relative: str) -> Path:
    """Reject Windows aliases, traversal, links and junctions, including ancestors."""
    parts = PurePosixPath(relative).parts
    if (
        not parts
        or relative != "/".join(parts)
        or any(p in {".", ".."} or p.endswith((".", " ")) for p in parts)
        or any(re.search(r'[<>:"\\|?*\x00-\x1f]', p) for p in parts)
        or any(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", p) for p in parts)
        or PurePosixPath(relative).is_absolute()
    ):
        raise ValueError("unsafe relative path")
    root = root.absolute()
    result = root.joinpath(*parts)
    for path in (root, *result.parents, result):
        physical = io_path(path)
        if physical.exists() or physical.is_symlink():
            info = physical.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
                raise ValueError("linked/reparse path refused")
    if result.resolve() != result or not result.is_relative_to(root):
        raise ValueError("path leaves root")
    return result


def source_check(root: Path, *, normalize: bool = False) -> str:
    """Only rewrite line endings when independently pinned normalized bytes match."""
    manifest = read_json(root / "tools/migration/source-files.json")
    checked = []
    for row in manifest["files"]:
        path = safe_path(root, row["path"])
        raw = path.read_bytes()
        if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != row["lf_sha256"]:
            raise ValueError("modified source refused: " + row["path"])
        expected = raw.replace(b"\r\n", b"\n")
        if row["eol"] in {"crlf", "mixed"}:
            crlf_lines = set(row["crlf_lines"])
            expected = b"".join(
                line[:-1] + b"\r\n" if i in crlf_lines and line.endswith(b"\n") else line
                for i, line in enumerate(expected.splitlines(keepends=True))
            )
        if hashlib.sha256(expected).hexdigest() != row["sha256"]:
            raise ValueError("invalid source manifest")
        if raw != expected and not normalize:
            raise ValueError("source line endings differ; run bootstrap: " + row["path"])
        checked.append((path, raw, expected, row))
    identity = hashlib.sha256(
        "\n".join(f"{row['path']}:{row['sha256']}" for _, _, _, row in checked).encode()
    ).hexdigest()
    if identity != manifest["source_sha256"] or identity != SOURCE_SHA:
        raise ValueError("canonical source manifest identity differs")
    # Also detect added canonical files; no model imports.
    paths = set()
    for directory in (
        "core",
        "encoder",
        "adaptation",
        "data",
        "realtime",
        "evaluation",
        "scripts",
        "tests",
        "configs",
    ):
        for path in (root / directory).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".toml", ".ps1"}:
                rel = path.relative_to(root).as_posix()
                if (
                    not rel.startswith(("data/raw/", "data/processed/", "data/interim/"))
                    and path.name != "local.toml"
                ):
                    paths.add(rel)
    paths.update(
        row["path"]
        for _, _, _, row in checked
        if not row["path"].startswith(
            (
                "core/",
                "encoder/",
                "adaptation/",
                "data/",
                "realtime/",
                "evaluation/",
                "scripts/",
                "tests/",
                "configs/",
            )
        )
    )
    paths.update(
        p.relative_to(root).as_posix() for p in (root / ".githooks").iterdir() if p.is_file()
    )
    if paths != {row["path"] for _, _, _, row in checked}:
        raise ValueError("canonical file set differs")
    # Complete file-set and byte preflight before touching any source file.
    for path, raw, expected, _row in checked:
        if normalize and raw != expected:
            if path.read_bytes() != raw:
                raise ValueError("source changed during normalization")
            path.write_bytes(expected)
    return identity


def npz_members(path: Path) -> dict:
    import zipfile

    members = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.filename in members or not info.filename.endswith(".npy"):
                raise ValueError("unexpected cache member")
            if info.file_size > 1024**3 or len(archive.infolist()) > 32:
                raise ValueError("cache exceeds bounded member limits")
            with archive.open(info) as stream:
                members[info.filename] = {
                    "bytes": info.file_size,
                    "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
                }
    return members


def replace_new(temp: Path, destination: Path) -> None:
    """Publish without overwriting a racing writer (Windows rename is exclusive)."""
    if os.name == "nt":
        os.rename(io_path(temp), io_path(destination))
    else:
        os.link(temp, destination)
        temp.unlink()
