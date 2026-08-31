"""Deterministic loading, validation, and hashing of experiment configuration."""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def _json_snapshot(value: Mapping[str, Any]) -> dict[str, JsonValue]:
    """Return a detached JSON-compatible configuration snapshot."""

    try:
        encoded = json.dumps(value, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise ValueError("configuration must contain only finite JSON-compatible values") from error
    decoded: object = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise ValueError("configuration root must be a mapping")
    return deepcopy(decoded)


def load_toml(path: str | Path) -> dict[str, JsonValue]:
    """Load one committed TOML file into a detached configuration snapshot."""

    source = Path(path)
    with source.open("rb") as stream:
        raw = tomllib.load(stream)
    return _json_snapshot(raw)


def canonical_config_json(config: Mapping[str, Any]) -> str:
    """Serialize config identically across runs and machines."""

    snapshot = _json_snapshot(config)
    return json.dumps(snapshot, allow_nan=False, separators=(",", ":"), sort_keys=True)


def config_digest(config: Mapping[str, Any]) -> str:
    """Return a SHA-256 digest that uniquely identifies the full configuration."""

    payload = canonical_config_json(config).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def config_snapshot(config: Mapping[str, Any]) -> dict[str, JsonValue]:
    """Public copy helper used when creating immutable run records."""

    return _json_snapshot(config)

