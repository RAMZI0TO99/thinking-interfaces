"""Reconstruct verified cache arrays in isolated staging trees, one subject per Job."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, digest, npz_members, read_json, replace_new, safe_path, source_check, write_json


def run_guard(python: Path, purpose: str, command: list[str]):
    result = subprocess.run([str(python), "-I", "-S", "-B", str(ROOT / "tools/migration/guard.py"),
                             "--purpose", purpose, "--", *command], cwd=ROOT, check=False)
    if result.returncode:
        raise ValueError("guarded rebuild operation failed; see runs/migration receipts")


def rebuild_one(python: Path, row: dict, assets: list[dict]):
    destination = safe_path(ROOT, row["path"])
    if destination.exists():
        if npz_members(destination) != row["members"]:
            raise ValueError("existing cache differs; preserved: " + row["path"])
        print("verified cache: " + row["path"], flush=True)
        return
    relative_stage = "tmp/migration_rebuild/" + uuid.uuid4().hex
    stage = safe_path(ROOT, relative_stage)
    stage.mkdir(parents=True, exist_ok=False)
    canonical = read_json(ROOT / "tools/migration/source-files.json")["files"]
    for entry in canonical:
        target = safe_path(stage, entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / entry["path"], target)
    selected = [a for a in assets if a["dataset"] == row["dataset"] and a["subject"] == row["subject"]]
    for entry in selected:
        raw = safe_path(ROOT, entry["path"])
        if not raw.exists() or raw.stat().st_size != entry["bytes"] or digest(raw) != entry["sha256"]:
            raise ValueError("raw bytes not verified: " + entry["path"])
        target = safe_path(stage, entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raw, target)
    if row["profile"] == "pre_cue_no_future_v1":
        relative = ("runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/"
                    "real_pre_cue_no_future_all9_posthash.json")
        receipt = safe_path(ROOT, relative)
        if digest(receipt) != "14accc31cb041b17cda1a670bbaae635a1fee53500d3ebbce95608a12ae69be5":
            raise ValueError("restore the frozen no-future audit receipt before reconstruction")
        target = safe_path(stage, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(receipt, target)
    venv = ROOT / ".venv/Scripts/python.exe"
    if not venv.is_file():
        raise ValueError("bootstrap the full environment first")
    run_guard(python, f"data-only rebuild {row['dataset']}/{row['profile']}/{row['subject']}", [
        str(venv), "-I", "-B", str(ROOT / "tools/migration/rebuild_worker.py"), str(stage),
        row["dataset"], row["profile"], str(row["subject"])])
    output = safe_path(stage, row["path"])
    if npz_members(output) != row["members"]:
        raise ValueError("rebuilt array bytes differ; staging retained: " + str(stage))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".publish-" + uuid.uuid4().hex)
    try:
        shutil.copyfile(output, temp)
        if npz_members(temp) != row["members"]:
            raise ValueError("publication copy differs")
        replace_new(temp, destination)
    finally:
        if temp.exists():
            temp.unlink()
    write_json(ROOT / "runs/migration" / ("rebuild_" + stage.name + ".json"), {
        "schema": "verified_data_rebuild_v1", "source_sha256": source_check(ROOT),
        "cache": row["path"], "verified_members": row["members"],
        "container_sha256": digest(destination), "raw_assets": selected,
        "scientific_admission": False, "original_case_attempts_remaining": 0,
        "historical_sidecars_preserved": True,
    })
    # Delete only this newly owned generated staging tree, after proving containment
    # and absence of links/junctions. Never clean raw data or historical runs.
    if stage.resolve() != stage or not stage.is_relative_to(ROOT / "tmp/migration_rebuild"):
        raise ValueError("staging cleanup scope differs")
    for path in stage.rglob("*"):
        safe_path(stage, path.relative_to(stage).as_posix())
    shutil.rmtree(stage)
    print("rebuilt and verified: " + row["path"], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=("all", "bci_iv_2a", "cho2017", "mmidb"))
    parser.add_argument("--subjects", nargs="+", type=int)
    parser.add_argument("--profile")
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    source_check(ROOT)
    if args.subjects is not None and (len(set(args.subjects)) != len(args.subjects) or min(args.subjects) < 1):
        parser.error("subjects must be unique positive integers")
    caches = read_json(ROOT / "tools/migration/caches.json")["caches"]
    selected = [r for r in caches if (args.dataset == "all" or r["dataset"] == args.dataset)
                and (args.subjects is None or r["subject"] in args.subjects)
                and (args.profile is None or r["profile"] == args.profile)]
    if not selected:
        parser.error("no known caches selected")
    if args.subjects is not None and set(args.subjects) != {r["subject"] for r in selected}:
        parser.error("requested subject outside the selected roster")
    if not args.skip_download:
        for dataset, subject in sorted({(r["dataset"], r["subject"]) for r in selected}):
            run_guard(args.python, f"verified raw download {dataset}/{subject}", [str(args.python),
                "-I", "-S", "-B", str(ROOT / "tools/migration/restore.py"), "fetch",
                "--dataset", dataset, "--subjects", str(subject)])
    assets = read_json(ROOT / "tools/migration/assets.json")["assets"]
    for row in selected:
        rebuild_one(args.python, row, assets)


if __name__ == "__main__":
    main()
