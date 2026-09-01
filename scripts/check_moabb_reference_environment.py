"""Verify the isolated reference installation without importing TensorFlow or MOABB."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import sys
import sysconfig
import tomllib
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from core.provenance import capture_source
from evaluation.reference_environment import resource_gate, startup_runtime, verify_reference_files

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/moabb_reference_environment.toml"
    )
    parser.add_argument(
        "--startup-minimum-free-memory-gib",
        type=float,
        help="Operational admission threshold; scientific/environment configuration is unchanged",
    )
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    environment = config["environment"]
    expected_prefix = (ROOT / environment["directory"]).resolve()
    if Path(sys.prefix).resolve() != expected_prefix:
        raise ValueError("run this checker with the isolated reference environment's Python")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if python_version != environment["python_version"]:
        raise ValueError("reference Python version mismatch")
    installed = {
        distribution.metadata["Name"]: distribution.version
        for distribution in importlib.metadata.distributions()
    }
    for requirement in environment["requirements"]:
        if "==" in requirement:
            name, version = requirement.split("==", 1)
            if importlib.metadata.version(name) != version:
                raise ValueError(f"reference dependency version mismatch: {name}")
    distribution = importlib.metadata.distribution("moabb")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    expected_url = (
        "https://codeload.github.com/NeuroTechX/moabb/zip/"
        + environment["source_revision"]
    )
    if direct.get("url") != expected_url:
        raise ValueError("MOABB was not installed from the pinned reference archive")
    archive_hash = direct.get("archive_info", {}).get("hashes", {}).get("sha256")
    if archive_hash != environment["source_archive_sha256"]:
        raise ValueError("MOABB reference archive hash mismatch")
    install_path = ROOT / "runs/moabb_reference/environment_install.json"
    install = json.loads(install_path.read_text(encoding="utf-8"))
    for item in install["install"]:
        metadata = item["metadata"]
        if importlib.metadata.version(metadata["name"]) != metadata["version"]:
            raise ValueError(f"resolved dependency changed: {metadata['name']}")
    hashes = verify_reference_files(Path(sysconfig.get_path("purelib")), config["source_files"])
    free_memory_gib = (
        importlib.import_module("psutil").virtual_memory().available / 1024**3
    )
    operational_runtime = startup_runtime(
        config["runtime"], args.startup_minimum_free_memory_gib
    )
    resources = resource_gate(
        operational_runtime, free_memory_gib=free_memory_gib,
        free_disk_gib=shutil.disk_usage(ROOT).free / 1024**3,
    )
    operating_mode = {
        "version": 1,
        "scope": "startup admission only; scientific and numerical configuration unchanged",
        "configured_minimum_free_memory_gib": float(
            config["runtime"]["minimum_free_memory_gib"]
        ),
        "startup_minimum_free_memory_gib": float(
            operational_runtime["minimum_free_memory_gib"]
        ),
        "startup_override_applied": (
            operational_runtime["minimum_free_memory_gib"]
            != config["runtime"]["minimum_free_memory_gib"]
        ),
        "stop_below_free_memory_gib": float(
            config["runtime"]["stop_below_free_memory_gib"]
        ),
        "minimum_free_disk_gib": float(config["runtime"]["minimum_free_disk_gib"]),
    }
    report = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "source": asdict(capture_source(ROOT)),
        "config": config,
        "config_file_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "installed_versions": installed,
        "installation_report_sha256": hashlib.sha256(install_path.read_bytes()).hexdigest(),
        "moabb_archive": direct,
        "verified_source_files": hashes,
        "environment_verified": True,
        "training_ready": resources["ready"],
        "resources": resources,
        "operating_mode": operating_mode,
        "model_imported": False,
        "training_performed": False,
        "reference_reproduction_passed": False,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "runs/moabb_reference" / f"environment_check_{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "environment_verified": True,
                      "training_ready": resources["ready"], "resources": resources}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
