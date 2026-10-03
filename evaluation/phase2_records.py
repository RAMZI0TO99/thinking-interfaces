"""Append-only Phase II envelopes with trusted-context verification and no Phase I writes."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.config import canonical_config_json, config_digest
from evaluation.phase2_protocol import require_digest


@dataclass(frozen=True, slots=True)
class CellIdentity:
    dataset: str
    target_subject: str
    method: str
    shots_per_class: int
    model_seed: int
    support_draw_seed: int | None
    montage_seed: int | None
    protocol_sha256: str
    episode_sha256: str
    selection_sha256: str
    method_config_sha256: str
    preprocessing_sha256: str
    checkpoint_sha256: str
    source_sha256: str
    environment_sha256: str
    git_commit: str
    git_dirty: bool

    def __post_init__(self) -> None:
        for name in ("dataset", "target_subject", "method"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if type(self.shots_per_class) is not int or self.shots_per_class < 1:
            raise ValueError("shots_per_class must be a positive integer")
        for name in ("model_seed", "support_draw_seed", "montage_seed"):
            value = getattr(self, name)
            if value is None and name != "model_seed":
                continue
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer or applicable null")
        for name in asdict(self):
            if name.endswith("sha256"):
                require_digest(getattr(self, name), name)
        if (
            not isinstance(self.git_commit, str)
            or len(self.git_commit) not in (40, 64)
            or any(c not in "0123456789abcdef" for c in self.git_commit)
            or type(self.git_dirty) is not bool
        ):
            raise ValueError("a real Git commit and explicit dirty-state flag are required")

    @property
    def sha256(self) -> str:
        return config_digest(asdict(self))


def envelope(kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if kind not in {
        "episode_manifest",
        "source_selection",
        "evaluation_cell",
        "protocol_audit",
        "engineering_smoke",
    }:
        raise ValueError("unknown Phase II envelope kind")
    snapshot = json.loads(canonical_config_json(payload))
    content = {"schema_version": 1, "phase": 2, "kind": kind, "payload": snapshot}
    return {**content, "sha256": config_digest(content)}


def verify_envelope(
    record: Mapping[str, Any], *, kind: str, expected_payload: Mapping[str, Any]
) -> bool:
    """Compare with reconstructed expected content, not just the record's own digest."""
    try:
        expected = envelope(kind, expected_payload)
        return canonical_config_json(record) == canonical_config_json(expected)
    except (TypeError, ValueError):
        return False


def write_once(path: Path, payload: Mapping[str, Any], *, output_root: Path) -> Path:
    """Publish complete bytes with atomic no-clobber hard linking on the same volume.

    Same-byte resume is a no-op. Different content and paths outside the caller's
    admitted output root fail without replacing an existing record.
    """
    root = output_root.resolve()
    destination = path.resolve()
    if destination == root or not destination.is_relative_to(root):
        raise ValueError("record path must remain inside its admitted output root")
    encoded = (canonical_config_json(payload) + "\n").encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != encoded:
            raise FileExistsError(f"conflicting immutable record: {destination}")
        return destination
    descriptor, temporary = tempfile.mkstemp(prefix=".phase2-", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.read_bytes() != encoded:
                raise FileExistsError(f"conflicting immutable record: {destination}") from None
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)
    return destination
