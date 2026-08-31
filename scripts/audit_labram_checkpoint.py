"""Byte correspondence of pinned original and safe LaBraM weights; no unpickling."""

from __future__ import annotations

import hashlib
import json
import math
import tomllib
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.provenance import capture_source
from evaluation.static_checkpoint import Descriptor, float_tensor_slice, inspect_metadata

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def original_key(safe_key: str) -> str:
    """Explicit name-only conversion; no tensor reshaping or value transforms."""
    key = {"position_embedding": "pos_embed", "temporal_embedding": "time_embed"}.get(
        safe_key, safe_key
    )
    key = key.replace("patch_embed.temporal_conv.", "patch_embed.")
    key = key.replace(".mlp.0.", ".mlp.fc1.").replace(".mlp.2.", ".mlp.fc2.")
    return "student." + key


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate safe-header JSON key")
        result[key] = value
    return result


def safe_tensor_bytes(payload: bytes) -> dict[str, tuple[tuple[int, ...], bytes]]:
    """Validate an F32-only safetensors header and return exact serialized slices."""
    if len(payload) < 8:
        raise ValueError("truncated safe header")
    length = int.from_bytes(payload[:8], "little")
    if not 2 <= length <= 4 * 1024 * 1024 or 8 + length > len(payload):
        raise ValueError("invalid safe header length")
    header = json.loads(payload[8 : 8 + length], object_pairs_hook=unique_json_object)
    if not isinstance(header, dict):
        raise ValueError("safe header must be an object")
    data = payload[8 + length :]
    tensors = {}
    intervals = []
    for key, entry in header.items():
        if key == "__metadata__":
            if not isinstance(entry, dict) or any(not isinstance(v, str) for v in entry.values()):
                raise ValueError("invalid safe metadata")
            continue
        if not isinstance(entry, dict) or set(entry) != {"dtype", "shape", "data_offsets"}:
            raise ValueError("invalid safe tensor entry")
        shape, offsets = entry["shape"], entry["data_offsets"]
        if (
            entry["dtype"] != "F32"
            or not isinstance(shape, list)
            or any(type(value) is not int or value < 1 for value in shape)
            or not isinstance(offsets, list)
            or len(offsets) != 2
            or any(type(value) is not int for value in offsets)
        ):
            raise ValueError("unsupported safe tensor metadata")
        start, end = offsets
        if not 0 <= start < end <= len(data) or end - start != math.prod(shape) * 4:
            raise ValueError("invalid safe tensor byte range")
        intervals.append((start, end))
        tensors[key] = (tuple(shape), data[start:end])
    cursor = 0
    for start, end in sorted(intervals):
        if start != cursor:
            raise ValueError("safe tensor overlap or uncovered data")
        cursor = end
    if cursor != len(data) or not tensors:
        raise ValueError("trailing data or empty safe checkpoint")
    return tensors


def compare_checkpoints(original: Path, safe: Path, inspection: dict[str, Any]) -> dict[str, Any]:
    tensors = safe_tensor_bytes(safe.read_bytes())
    if len(tensors) != inspection["expected_safe_tensors"]:
        raise ValueError("unexpected converted tensor count")
    with zipfile.ZipFile(original) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith("/data.pkl")]
        if len(names) != len(set(names)) or len(metadata_names) != 1:
            raise ValueError("ambiguous original ZIP members")
        name = metadata_names[0]
        if archive.getinfo(name).file_size > 8 * 1024 * 1024:
            raise ValueError("original metadata exceeds size limit")
        root = inspect_metadata(archive.read(name))
        if not isinstance(root, dict) or not isinstance(root.get("model"), Descriptor):
            raise ValueError("missing inert model dictionary")
        model = root["model"].items
        slices = {key: float_tensor_slice(value) for key, value in model.items()}
        mapping = {key: original_key(key) for key in tensors}
        if len(set(mapping.values())) != len(mapping) or not set(mapping.values()) <= set(slices):
            raise ValueError("tensor mapping is not one-to-one and complete")
        omitted = set(slices) - set(mapping.values())
        if {key for key in omitted if key.startswith("student.")} != set(
            inspection["omitted_student_keys"]
        ):
            raise ValueError("unexpected omitted student tensors")
        rows = []
        for safe_key, (shape, safe_bytes) in sorted(tensors.items()):
            source = slices[mapping[safe_key]]
            member = name.removesuffix("data.pkl") + "data/" + source.storage_key
            if archive.getinfo(member).file_size != source.storage_elements * 4:
                raise ValueError("original storage byte size mismatch")
            if source.storage_elements * 4 > 32 * 1024 * 1024:
                raise ValueError("original storage exceeds inspection limit")
            raw = archive.read(member)
            original_bytes = raw[source.offset * 4 : (source.offset + source.elements) * 4]
            rows.append(
                {
                    "safe_key": safe_key,
                    "original_key": mapping[safe_key],
                    "safe_shape": shape,
                    "original_shape": source.shape,
                    "elements": source.elements,
                    "original_sha256": hashlib.sha256(original_bytes).hexdigest(),
                    "safe_sha256": hashlib.sha256(safe_bytes).hexdigest(),
                    "shape_matches": shape == source.shape,
                    "bytes_identical": safe_bytes == original_bytes,
                }
            )
        elements = sum(math.prod(shape) for shape, _ in tensors.values())
        if elements != inspection["expected_safe_elements"]:
            raise ValueError("unexpected safe element count")
        return {
            "scope": "Exact shapes and serialized F32 bytes under explicit name-only mapping.",
            "pickle_executed": False,
            "training_performed": False,
            "inference_parity_established": False,
            "scientific_signoff": False,
            "original_root_keys": sorted(root),
            "original_model_tensors": len(slices),
            "original_model_state_elements": sum(value.elements for value in slices.values()),
            "original_student_state_elements": sum(
                value.elements for key, value in slices.items() if key.startswith("student.")
            ),
            "safe_tensors": len(tensors),
            "safe_elements": elements,
            "all_retained_weights_identical": all(
                row["shape_matches"] and row["bytes_identical"] for row in rows
            ),
            "expected_plan_parameters": inspection["expected_plan_parameters"],
            "parameter_count_matches_plan": elements == inspection["expected_plan_parameters"],
            "omitted_original_model_tensors": {
                key: {"shape": slices[key].shape, "elements": slices[key].elements}
                for key in sorted(omitted)
            },
            "comparisons": rows,
            "limitations": [
                "State-dictionary element counts are not a reconstruction of the original model.",
                "Optimizer/training metadata is inspected inertly, never loaded for execution.",
                "Byte identity does not establish model implementation or inference parity.",
                "No explanation for the plan's exact parameter count is inferred.",
                "Original archive has no byteorder marker; no original floats were decoded.",
            ],
        }


def main() -> int:
    config_path = ROOT / "configs/labram_checkpoint_audit.toml"
    config = tomllib.loads(config_path.read_text("utf-8"))
    source = capture_source(ROOT)
    if source.git_dirty is not False:
        raise ValueError("commit audit source before recording checkpoint evidence")
    paths = {
        name: (ROOT / config[name]["path"]).resolve() for name in ("original", "safe_conversion")
    }
    before = {}
    for name, path in paths.items():
        if not path.is_relative_to(ROOT):
            raise ValueError("checkpoint path escaped the workspace")
        before[name] = sha256_file(path)
        if before[name] != config[name]["sha256"]:
            raise ValueError(f"{name} checkpoint does not match its pinned hash")
    report = compare_checkpoints(paths["original"], paths["safe_conversion"], config["inspection"])
    if before != {name: sha256_file(path) for name, path in paths.items()}:
        raise RuntimeError("checkpoint changed during inspection")
    if capture_source(ROOT).source_sha256 != source.source_sha256:
        raise RuntimeError("audit source changed during inspection")
    report.update(
        {
            "source": asdict(source),
            "config": config,
            "checkpoint_sha256": before,
            "config_sha256": sha256_file(config_path),
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
    )
    directory = ROOT / "runs/checkpoint_audit"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    with target.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "report": str(target),
                **{
                    key: report[key]
                    for key in (
                        "safe_tensors",
                        "safe_elements",
                        "all_retained_weights_identical",
                        "parameter_count_matches_plan",
                    )
                },
            }
        )
    )
    return 0 if report["all_retained_weights_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
