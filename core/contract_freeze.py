"""Verify the explicit, non-retroactive local interface freeze."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from core.config import load_toml


def verify_contract_freeze(root: Path) -> bool:
    try:
        config = cast(Mapping[str, Any], load_toml(root / "configs" / "contract_freeze.toml"))
        freeze = config["freeze"]
        files = config["files"]
        return bool(
            freeze["version"] == 1
            and datetime.fromisoformat(freeze["recorded_at_utc"]).utcoffset() is not None
            and set(files) == {"core/contracts.py", "core/run_record.py"}
            and all(
                hashlib.sha256((root / name).read_text("utf-8").encode("utf-8")).hexdigest()
                == digest
                for name, digest in files.items()
            )
        )
    except (OSError, ValueError, TypeError, KeyError):
        return False
