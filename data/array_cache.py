"""Atomic, content-verified float32 caches; incomplete arrays are never reused."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_float32_cache(
    path: Path,
    *,
    shape: tuple[int, ...],
    key: str,
    fill: Callable[[np.memmap[Any, Any]], None],
) -> NDArray[np.float32]:
    """Fill must not retain the writable mapping; Windows requires closing it before replace."""
    metadata_path = path.with_suffix(path.suffix + ".json")
    expected = {"cache_schema": 1, "key": key, "shape": list(shape), "dtype": "float32"}
    try:
        metadata = json.loads(metadata_path.read_text("utf-8"))
        if (
            all(metadata.get(name) == value for name, value in expected.items())
            and file_sha256(path) == metadata["file_sha256"]
        ):
            cached = np.load(path, mmap_mode="r", allow_pickle=False)
            if cached.shape == shape and cached.dtype == np.float32:
                return np.asarray(cached)
            cast(Any, cached)._mmap.close()
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    os.close(handle)
    temporary = Path(temporary_name)
    target = None
    metadata_temporary: Path | None = None
    try:
        target = np.lib.format.open_memmap(temporary, mode="w+", dtype=np.float32, shape=shape)
        fill(target)
        target.flush()
        cast(Any, target)._mmap.close()
        target = None
        metadata = {**expected, "file_sha256": file_sha256(temporary)}
        os.replace(temporary, path)
        handle, metadata_name = tempfile.mkstemp(
            dir=path.parent, prefix=metadata_path.name + ".", suffix=".tmp"
        )
        metadata_temporary = Path(metadata_name)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(metadata, stream, sort_keys=True)
            stream.write("\n")
        os.replace(metadata_temporary, metadata_path)
        return np.asarray(np.load(path, mmap_mode="r", allow_pickle=False))
    finally:
        if target is not None:
            cast(Any, target)._mmap.close()
        temporary.unlink(missing_ok=True)
        if metadata_temporary is not None:
            metadata_temporary.unlink(missing_ok=True)
