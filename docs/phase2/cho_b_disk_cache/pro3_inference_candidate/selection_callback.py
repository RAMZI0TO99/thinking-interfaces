"""Explicit one-use callback for the optional production LaBraM selection hook.

Import and construction use only the standard library. Invoking the callback
imports the tested scope and performs selection; real inputs require a separately
admitted worker and guard. Paths retain the cleanup module's ownership boundary.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .owned_cache_cleanup import owned_output


def make_source_selection_callback(
    *,
    owner_directory: Path,
    worker_sha256: str,
    event_sink: Callable[[dict[str, Any]], None],
) -> Callable[[Any], Any]:
    """Bind one selector invocation to an existing package-owned output directory."""
    if not isinstance(worker_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", worker_sha256):
        raise ValueError("selection callback requires actual worker bytes")
    if not callable(event_sink):
        raise ValueError("selection callback requires an explicit progress sink")
    output = owned_output(owner_directory)
    registry = output / "cache_registry.json"
    if registry.exists() or registry.is_symlink():
        raise ValueError("selection callback requires an unused cache owner directory")
    used = False

    def select(selector: Any) -> Any:
        nonlocal used
        if used:
            raise ValueError("selection callback is one-use")
        used = True
        # Delay scientific imports until an actual admitted selector invocation.
        from .source_selection_cache_scope_inference import SourceSelectionCacheScope

        scope = SourceSelectionCacheScope(
            selector,
            owner_directory=output,
            worker_sha256=worker_sha256,
            event_sink=event_sink,
        )
        return scope.run_selection()

    return select
