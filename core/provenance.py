"""Read-only source fingerprints and Git identity, without retroactive attribution."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


def source_files(root: Path) -> tuple[Path, ...]:
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
        for extension in ("*.py", "*.toml", "*.ps1"):
            for path in (root / directory).rglob(extension):
                relative = path.relative_to(root).parts
                if (
                    len(relative) > 1
                    and relative[0] == "data"
                    and relative[1] in {"raw", "processed", "interim"}
                ):
                    continue
                if path.name != "local.toml":
                    paths.add(path)
    for name in (
        "pyproject.toml",
        "requirements.lock",
        "requirements-core.lock",
        "requirements-data.lock",
        "requirements-ml.lock",
        ".python-version",
    ):
        if (root / name).is_file():
            paths.add(root / name)
    return tuple(sorted(paths))


def source_fingerprint(root: Path) -> str:
    rows = [
        f"{path.relative_to(root).as_posix()}:{hashlib.sha256(path.read_bytes()).hexdigest()}"
        for path in source_files(root)
    ]
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    git_commit: str
    source_sha256: str
    git_dirty: bool | None


def capture_source(root: Path) -> SourceProvenance:
    fingerprint = source_fingerprint(root)
    executable = shutil.which("git")
    if executable is None:
        return SourceProvenance("unversioned-workspace", fingerprint, None)
    try:
        revision = subprocess.run(
            [executable, "--no-optional-locks", "rev-parse", "--verify", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        commit = revision.stdout.strip()
        if (
            revision.returncode
            or len(commit) not in (40, 64)
            or any(character not in "0123456789abcdef" for character in commit)
        ):
            return SourceProvenance("unversioned-workspace", fingerprint, None)
        status = subprocess.run(
            [executable, "--no-optional-locks", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        tracked_source = {path.relative_to(root).as_posix() for path in source_files(root)}
        dirty = (
            any(
                not line.startswith("?? ") or line[3:] in tracked_source
                for line in status.stdout.splitlines()
            )
            if status.returncode == 0
            else None
        )
        return SourceProvenance(commit, fingerprint, dirty)
    except (OSError, subprocess.TimeoutExpired):
        return SourceProvenance("unversioned-workspace", fingerprint, None)
