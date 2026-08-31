"""Read-only machine and project preflight checks."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[1]
VALID_DATASET_STATUSES = {
    "not_downloaded",
    "partially_downloaded",
    "downloaded",
    "agreement_not_confirmed",
    "agreement_confirmed",
}


class DatasetStatus(TypedDict):
    datasets: list[dict[str, object]]
    enabled_access_blockers: list[str]
    pending_agreements: list[str]


def gpu_status() -> dict[str, object]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"available": False, "name": None, "memory_mib": None}
    command = [
        executable,
        "--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    name, memory = (part.strip() for part in result.stdout.strip().split(",", 1))
    return {"available": True, "name": name, "memory_mib": int(memory)}


def dataset_status(path: Path) -> DatasetStatus:
    """Validate the dataset registry and expose access blockers."""

    with path.open("rb") as stream:
        registry = tomllib.load(stream)["datasets"]

    datasets: list[dict[str, object]] = []
    blockers: list[str] = []
    pending_agreements: list[str] = []
    for key, raw in registry.items():
        status = raw["status"]
        if status not in VALID_DATASET_STATUSES:
            raise ValueError(f"invalid status for {key}: {status}")
        enabled = bool(raw["enabled"])
        access = str(raw["access"])
        display_name = str(raw["display_name"])
        if access == "agreement_required" and status != "agreement_confirmed":
            pending_agreements.append(display_name)
            if enabled:
                blockers.append(display_name)
        datasets.append(
            {
                "key": key,
                "display_name": display_name,
                "enabled": enabled,
                "access": access,
                "status": status,
                "needed_by_week": int(raw["needed_by_week"]),
            }
        )
    return {
        "datasets": datasets,
        "enabled_access_blockers": blockers,
        "pending_agreements": pending_agreements,
    }


def main() -> int:
    with (ROOT / "configs" / "base.toml").open("rb") as stream:
        config = tomllib.load(stream)

    data_root = ROOT / config["storage"]["data_root"]
    free_gb = shutil.disk_usage(ROOT).free / 1024**3
    gpu = gpu_status()
    gpu_memory = gpu["memory_mib"]
    minimum_gpu_memory = int(config["hardware"]["minimum_gpu_vram_mib"])
    gpu_ok = isinstance(gpu_memory, int) and gpu_memory >= minimum_gpu_memory
    datasets = dataset_status(ROOT / "configs" / "datasets.toml")
    required_modules = ("numpy", "pandas", "scipy", "sklearn")
    optional_modules = ("torch", "mne", "moabb", "braindecode", "pyriemann", "pylsl")
    report = {
        "python": sys.version.split()[0],
        "project_root": str(ROOT),
        "data_root": str(data_root),
        "data_root_writable": os.access(data_root, os.W_OK),
        "free_gb": round(free_gb, 1),
        "minimum_free_gb": config["storage"]["minimum_free_gb"],
        "storage_ok": free_gb >= config["storage"]["minimum_free_gb"],
        "gpu": gpu,
        "minimum_gpu_vram_mib": minimum_gpu_memory,
        "gpu_ok": gpu_ok,
        "dataset_access": datasets,
        "required_modules": {
            name: importlib.util.find_spec(name) is not None for name in required_modules
        },
        "optional_modules": {
            name: importlib.util.find_spec(name) is not None for name in optional_modules
        },
    }
    report["phase1_start_ready"] = bool(
        report["storage_ok"]
        and report["data_root_writable"]
        and report["gpu_ok"]
        and not datasets["enabled_access_blockers"]
    )
    print(json.dumps(report, indent=2))
    return 0 if report["phase1_start_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
