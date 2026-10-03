"""Prepare versioned Cho2017 Profile B epochs with a 60 Hz line-noise notch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.config import config_digest
from data.cho2017 import configure_local_cache, download_subject
from data.profile_a import save_epoch_artifact
from data.profile_b import (
    ProfileBConfig,
    build_profile_b_summary,
    preprocess_profile_b_cho_subject,
)

ROOT = Path(__file__).resolve().parents[1]
VARIANT_CONFIG = Path("configs/phase2/cho_profile_b_60hz.toml")
VARIANT = {
    "schema_version": 1,
    "dataset": "cho2017",
    "name": "profile_b_60hz_v1",
    "output_directory": "data/processed/cho2017/profile_b_60hz_v1",
}
SUBJECT_RESERVE_BYTES = 2 * 1024**3
GB = 1024**3


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subjects", nargs="+", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def load_plan(root: Path) -> tuple[dict[str, Any], ProfileBConfig, Path, Path, float]:
    with (root / "configs/base.toml").open("rb") as stream:
        base = tomllib.load(stream)
    with (root / "configs/cho2017.toml").open("rb") as stream:
        dataset = tomllib.load(stream)["dataset"]
    with (root / VARIANT_CONFIG).open("rb") as stream:
        variant_document = tomllib.load(stream)

    if set(variant_document) != {"variant", "preprocessing"} or (
        variant_document.get("variant") != VARIANT
    ):
        raise ValueError("Cho 60 Hz variant identity or output namespace mismatch")
    if dataset.get("key") != "cho2017" or float(dataset["line_frequency_hz"]) != 60.0:
        raise ValueError("Cho2017 line-frequency metadata must declare 60 Hz")
    base_profile = base["preprocessing"]["profile_b"]
    expected = {**base_profile, "notch_hz": 60.0}
    profile = variant_document.get("preprocessing")
    if profile != expected:
        raise ValueError("Cho 60 Hz preprocessing must copy base Profile B except for the notch")
    config = ProfileBConfig(**profile)
    if config.notch_hz != 60.0 or config.notch_hz != float(dataset["line_frequency_hz"]):
        raise ValueError("Cho 60 Hz notch and dataset line frequency disagree")
    root = root.resolve()
    raw_root = root / str(dataset["raw_root"])
    expected_raw_root = root / "data/raw/moabb/cho2017"
    if raw_root != expected_raw_root or raw_root.resolve() != expected_raw_root:
        raise ValueError("Cho raw root changed from the pinned namespace")
    output_dir = root / str(VARIANT["output_directory"])
    expected_output_dir = root / "data/processed/cho2017/profile_b_60hz_v1"
    if output_dir != expected_output_dir or output_dir.resolve() != expected_output_dir:
        raise ValueError("Cho 60 Hz output aliases or escapes its versioned namespace")
    floor_gb = float(base["storage"]["minimum_free_gb"])
    if floor_gb != 20.0:
        raise ValueError("the pinned 20 GiB storage floor changed")
    return dataset, config, raw_root, output_dir, floor_gb


def check_space(path: Path, floor_gb: float, *, reserve_bytes: int = 0) -> None:
    free = shutil.disk_usage(path).free
    required = int(floor_gb * GB) + reserve_bytes
    if free < required:
        raise RuntimeError(
            f"insufficient disk space: {free / GB:.3f} GiB free; "
            f"need {required / GB:.3f} GiB including subject reserve"
        )


def _publish_one(staged: Path, destination: Path) -> str:
    if destination.exists():
        if file_digest(staged) != file_digest(destination):
            raise FileExistsError(f"existing Cho 60 Hz file differs: {destination}")
        return "reused"
    try:
        os.link(staged, destination)
    except FileExistsError:
        if file_digest(staged) != file_digest(destination):
            raise FileExistsError(f"concurrent Cho 60 Hz file differs: {destination}") from None
        return "reused"
    return "created"


def _publish_pair(
    staged_artifact: Path,
    staged_manifest: Path,
    artifact: Path,
    manifest: Path,
) -> str:
    if artifact.exists() != manifest.exists():
        raise FileExistsError("incomplete existing Cho 60 Hz subject pair requires inspection")
    if artifact.exists():
        if file_digest(staged_artifact) != file_digest(artifact):
            raise FileExistsError(f"existing Cho 60 Hz artifact differs: {artifact}")
        if file_digest(staged_manifest) != file_digest(manifest):
            raise FileExistsError(f"existing Cho 60 Hz manifest differs: {manifest}")
        return "reused"
    _publish_one(staged_artifact, artifact)
    _publish_one(staged_manifest, manifest)
    return "created"


def process_subject(
    subject: int,
    root: Path,
    config: ProfileBConfig,
    raw_root: Path,
    output_dir: Path,
    floor_gb: float,
) -> dict[str, object]:
    expected_raw_root = root.resolve() / "data/raw/moabb/cho2017"
    if raw_root != expected_raw_root or raw_root.resolve() != expected_raw_root:
        raise ValueError("Cho raw root aliases or escapes its pinned namespace")
    expected_output = root.resolve() / str(VARIANT["output_directory"])
    if output_dir != expected_output or output_dir.resolve() != expected_output:
        raise ValueError("Cho 60 Hz output aliases or escapes its versioned namespace")
    if config.notch_hz != 60.0:
        raise ValueError("Cho 60 Hz subject requires the versioned 60 Hz notch")
    variant_config_sha256 = file_digest(root / VARIANT_CONFIG)
    check_space(root, floor_gb, reserve_bytes=SUBJECT_RESERVE_BYTES)
    artifact = output_dir / f"subject_{subject:02d}.npz"
    manifest = output_dir / f"subject_{subject:02d}.manifest.json"
    if artifact.resolve() != artifact or manifest.resolve() != manifest:
        raise FileExistsError("Cho 60 Hz subject file aliases another namespace")
    if artifact.exists() != manifest.exists():
        raise FileExistsError("incomplete existing Cho 60 Hz subject pair requires inspection")

    configure_local_cache(root, raw_root)
    source = download_subject(subject, raw_root)
    source_resolved = source.resolve()
    if not source_resolved.is_file() or not source_resolved.is_relative_to(raw_root):
        raise ValueError("Cho source file is outside the configured raw root")
    source_relative = source_resolved.relative_to(root.resolve()).as_posix()
    source_sha256 = file_digest(source_resolved)
    check_space(root, floor_gb, reserve_bytes=SUBJECT_RESERVE_BYTES)

    signals, labels, sessions, runs, trial_indices, channels = (
        preprocess_profile_b_cho_subject(subject, root, raw_root, config)
    )
    check_space(root, floor_gb, reserve_bytes=SUBJECT_RESERVE_BYTES)
    summary = build_profile_b_summary(
        subject=subject, signals=signals, channel_names=channels, config=config
    )
    if (
        signals.ndim != 3
        or signals.shape[0] < 1
        or signals.shape[1:] != (64, 800)
        or len(channels) != 64
        or len(set(channels)) != 64
        or any(len(item) != signals.shape[0] for item in (labels, sessions, runs, trial_indices))
        or not set(labels.tolist()) <= {"left_hand", "right_hand"}
    ):
        raise ValueError("Cho Profile B signals or trial identities violate the variant contract")
    if summary.config_sha256 != config_digest(asdict(config)):
        raise ValueError("Profile B summary config digest mismatch")
    if file_digest(source_resolved) != source_sha256:
        raise ValueError("Cho source changed during preprocessing")
    if file_digest(root / VARIANT_CONFIG) != variant_config_sha256:
        raise ValueError("Cho 60 Hz variant config changed during preprocessing")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".subject_{subject:02d}.", dir=output_dir) as name:
        stage = Path(name)
        staged_artifact = save_epoch_artifact(
            stage / artifact.name,
            signals=signals,
            labels=labels,
            sessions=sessions,
            runs=runs,
            trial_indices=trial_indices,
            channel_names=channels,
        )
        manifest_payload: dict[str, object] = {
            **summary.as_dict(),
            "variant": VARIANT,
            "variant_config_sha256": variant_config_sha256,
            "source_file": source_relative,
            "source_sha256": source_sha256,
        }
        staged_manifest = stage / manifest.name
        staged_manifest.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        check_space(root, floor_gb)
        if output_dir.resolve() != output_dir:
            raise ValueError("Cho 60 Hz output aliases its versioned namespace during work")
        status = _publish_pair(staged_artifact, staged_manifest, artifact, manifest)
    check_space(root, floor_gb)
    return {
        "subject": subject,
        "status": status,
        "artifact": str(artifact),
        "artifact_sha256": file_digest(artifact),
        "manifest": str(manifest),
        "manifest_sha256": file_digest(manifest),
        "source_file": source_relative,
        "source_sha256": source_sha256,
        "variant_config_sha256": manifest_payload["variant_config_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = ROOT.resolve()
    dataset, config, raw_root, output_dir, floor_gb = load_plan(root)
    subjects = [int(subject) for subject in args.subjects]
    roster = set(dataset["subjects"])
    if len(subjects) != len(set(subjects)) or any(subject not in roster for subject in subjects):
        raise ValueError("subjects must be unique members of the configured Cho2017 roster")
    for subject in subjects:
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "subject": subject,
                        "dry_run": True,
                        "variant": VARIANT,
                        "artifact": str(output_dir / f"subject_{subject:02d}.npz"),
                        "manifest": str(output_dir / f"subject_{subject:02d}.manifest.json"),
                        "config_sha256": config_digest(asdict(config)),
                        "variant_config_sha256": file_digest(root / VARIANT_CONFIG),
                        "disk_floor_gib": floor_gb,
                        "subject_reserve_gib": SUBJECT_RESERVE_BYTES / GB,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        else:
            print(
                json.dumps(process_subject(subject, root, config, raw_root, output_dir, floor_gb)),
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
