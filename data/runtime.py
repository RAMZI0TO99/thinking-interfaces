"""Process-local cache routing for scientific libraries."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def configure_scientific_runtime(project_root: Path = PROJECT_ROOT) -> None:
    """Prevent MNE, MOABB, and Matplotlib from writing outside the project."""

    mne_home = project_root / ".cache" / "mne-home"
    matplotlib_cache = project_root / ".cache" / "matplotlib"
    (mne_home / ".mne").mkdir(parents=True, exist_ok=True)
    matplotlib_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("_MNE_FAKE_HOME_DIR", str(mne_home))
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))
    os.environ.setdefault("MOABB_DOWNLOAD_PROVIDER", "upstream")

