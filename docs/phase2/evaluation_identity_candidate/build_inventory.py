"""Inventory project identities; this does not establish a checkpoint cohort."""
import hashlib
import json
from pathlib import Path
import re
import tomllib

import metadata_reader as reader

DATASETS = {
    "bci_iv_2a": (9, 2, "profile_a"),
    "cho2017": (52, 2, "profile_b_60hz_v1"),
    "mmidb": (109, 3, "profile_b"),
}
RAW_AUDIT = "runs/coordination/source_prerequisites_20261010_v1/raw_environment_002/raw52/receipt.json"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON sidecar key")
        result[key] = value
    return result


def read_json(root, path):
    data = reader.read_small(root, path)
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                       parse_constant=lambda token: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    return value, {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(data).hexdigest()}


def declared_raw_path(root, value):
    if type(value) is not str or not value or ".." in value.replace("\\", "/").split("/"):
        raise ValueError("invalid declared raw path")
    path = Path(value)
    path = path if path.is_absolute() else root / path
    path = path.absolute()
    if not path.is_relative_to(root / "data/raw"):
        raise ValueError("declared raw path outside workspace raw namespace")
    return path.relative_to(root).as_posix()


def build_inventory(root):
    root = Path(root).absolute()
    pins, configs = {}, {}
    for name in ("configs/dataset_inventory.toml", "configs/phase2/protocol.toml"):
        data = reader.read_small(root, root / name)
        configs[name] = tomllib.loads(data.decode("utf-8"))
        pins[name] = hashlib.sha256(data).hexdigest()
    history, history_pin = read_json(root, root / RAW_AUDIT)
    pins[RAW_AUDIT] = history_pin["sha256"]
    datasets = {}
    for dataset, (expected, digits, sidecar_profile) in DATASETS.items():
        directory_name = f"data/processed/{dataset}/profile_a"
        inventory_config = configs["configs/dataset_inventory.toml"]["datasets"][dataset]
        protocol_config = configs["configs/phase2/protocol.toml"]["datasets"][dataset]
        if inventory_config["processed_directory"] != directory_name or protocol_config["artifact_directory"] != directory_name or inventory_config["expected_subjects"] != expected or protocol_config["expected_subjects"] != expected:
            raise ValueError("fixed evaluation directories/counts differ from pinned configs")
        directory = root / directory_name
        expected_files = {f"subject_{subject:0{digits}d}.npz" for subject in range(1, expected + 1)}
        actual_files = {path.name for path in directory.glob("*.npz")}
        if expected_files != actual_files:
            raise ValueError("fixed subject inventory differs")
        subjects = []
        for subject in range(1, expected + 1):
            code = f"subject_{subject:0{digits}d}"
            record = reader.inspect_archive(root, directory / (code + ".npz"))
            sidecar_path = root / f"data/processed/{dataset}/{sidecar_profile}/{code}.manifest.json"
            sidecar, sidecar_pin = read_json(root, sidecar_path)
            if type(sidecar.get("subject")) is not int or sidecar["subject"] != subject:
                raise ValueError("sidecar subject disagrees with file identity")
            source_values = sidecar.get("source_files", [sidecar["source_file"]] if "source_file" in sidecar else [])
            if type(source_values) is not list or any(type(value) is not str for value in source_values):
                raise ValueError("source-file declaration type")
            raw_paths = [declared_raw_path(root, value) for value in source_values]
            if len(raw_paths) != len(set(raw_paths)):
                raise ValueError("duplicate declared source path")
            historical = None
            if dataset == "cho2017":
                old = history["raw_sources"][code]
                old_path = declared_raw_path(root, old["path"])
                if raw_paths != [old_path] or sidecar.get("source_sha256") != old["sha256"] or not re.fullmatch(r"[0-9a-f]{64}", old["sha256"]):
                    raise ValueError("Cho sidecar differs from historical verified raw audit")
                historical = {"raw_file_path": old_path, "raw_file_bytes": old["bytes"], "historical_verified_raw_sha256": old["sha256"], "audit_receipt": history_pin, "raw_file_rehashed_in_this_scope": False}
            record.update({"project_subject_id": f"{dataset}/{code}", "project_subject_number": subject,
                           "sidecar": sidecar_pin, "sidecar_profile": sidecar_profile, "declared_raw_file_paths": raw_paths,
                           "raw_file_declarations_status": "declared_in_sidecar" if raw_paths else "unknown_no_sidecar_mapping",
                           "group_to_raw_file_mapping": "unverified", "historical_raw_audit": historical,
                           "publisher_subject_or_recording_namespace_mapping": "unknown"})
            subjects.append(record)
        datasets[dataset] = {"subject_count": len(subjects), "epoch_count": sum(item["epoch_count"] for item in subjects),
            "project_recording_group_count": sum(len(item["project_recording_groups"]) for item in subjects),
            "subjects_with_raw_path_declarations": sum(bool(item["declared_raw_file_paths"]) for item in subjects),
            "subjects_with_historical_raw_hash_match": sum(item["historical_raw_audit"] is not None for item in subjects),
            "subjects": subjects}
    return {"schema": "pro3_read_only_evaluation_identity_inventory_v1", "input_pins": pins, "datasets": datasets,
            "total_subjects": sum(item["subject_count"] for item in datasets.values()),
            "total_epochs": sum(item["epoch_count"] for item in datasets.values()),
            "identity_namespace": "project Profile A artifact basenames and stored session/run/trial values",
            "artifact_hashes_freshly_measured": True, "raw_signal_files_opened_or_rehashed": False,
            "signal_or_label_arrays_decoded": False, "scientific_libraries_or_models_imported": False,
            "provider_identity_mapping_verified": False, "checkpoint_cohort_or_overlap_verified": False,
            "scientifically_eligible_subject_roster_or_query_freeze": False, "scientific_gate_or_freeze_signed": False,
            "real_training_or_original_case_admission": False, "original_case_attempts_remaining": 0}
