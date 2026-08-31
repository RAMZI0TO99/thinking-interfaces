"""Check the native LSL demonstrator's saved evidence, without rerunning a model."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from core.config import config_digest, load_toml


def verify_live_demo(root: Path) -> bool:
    try:
        directory = root / "runs" / "live_demo"
        latest = json.loads((directory / "latest.json").read_text("utf-8"))
        result_path = (root / latest["result"]).resolve()
        if not result_path.is_relative_to(directory.resolve()):
            return False
        if hashlib.sha256(result_path.read_bytes()).hexdigest() != latest["sha256"]:
            return False
        report = json.loads(result_path.read_text("utf-8"))
        config = load_toml(root / "configs" / "live_demo.toml")
        if report["config"] != config or report["config_sha256"] != config_digest(config):
            return False
        benchmark = load_toml(root / "configs" / "benchmark.toml")
        if report["benchmark_config_sha256"] != config_digest(benchmark):
            return False
        if not (
            report["passed"] is True
            and report["source_query_disjoint"] is True
            and report["support_trials"] == 0
            and report["held_out_subject"] not in report["source_subjects"]
            and report["source_trials"] > 0
            and len(report["source_subjects"]) == 8
        ):
            return False
        stream = report["stream"]
        expected_frames = len(report["query_indices"])
        protocol = report["config"]
        dataset_config = report["config"]["data"]
        sampling_rate = (
            report["expected_samples"] / (expected_frames * protocol["stream"]["window_seconds"])
            if expected_frames
            else 0
        )
        classes = {"feet", "left_hand", "right_hand", "tongue"}
        sequences = list(range(expected_frames))
        if not (
            expected_frames > 0
            and report["held_out_subject"] == dataset_config["held_out_subject"]
            and set(report["query_class_counts"]) == classes
            and all(
                count == dataset_config["query_trials_per_class"]
                for count in report["query_class_counts"].values()
            )
            and math.isclose(sampling_rate, 128.0)
            and math.isclose(
                report["expected_wall_seconds"], (report["expected_samples"] - 1) / 128.0
            )
            and len(set(report["query_indices"])) == expected_frames
            and stream["received_samples"] == report["expected_samples"]
            and stream["received_sample_sha256"] == report["sample_sha256"]
            and len(stream["frames"]) == expected_frames
            and sum(report["query_class_counts"].values()) == expected_frames
            and report["interface_all_frames_rendered"] is True
            and stream["processing_latency"]["count"] == expected_frames
            and math.isfinite(report["wall_drift_seconds"])
            and abs(report["wall_drift_seconds"])
            <= report["config"]["stream"]["maximum_wall_drift_seconds"]
            and math.isclose(
                report["wall_drift_seconds"],
                stream["wall_seconds"] - report["expected_wall_seconds"],
                abs_tol=1e-8,
            )
        ):
            return False
        receipt_path = result_path.parent / "interface_receipt.json"
        if (
            hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            != report["interface_receipt_sha256"]
        ):
            return False
        receipt = json.loads(receipt_path.read_text("utf-8-sig"))
        if not (
            receipt["completed"] is True
            and not receipt["error"]
            and receipt["hidden_preview"] is False
            and receipt["sequences"] == sequences
            and [row["sequence"] for row in receipt["updates"]] == sequences
            and [row["state"] for row in receipt["updates"]]
            == [frame["decision_state"] for frame in stream["frames"]]
        ):
            return False
        rendered = report["rendered_frames"]
        if len(rendered) != expected_frames or any(
            shown["target"] not in report["query_class_counts"]
            or any(
                shown[key] != frame[key]
                for key in ("decision_state", "confidence", "emitted_command", "latency_ms")
            )
            for shown, frame in zip(rendered, stream["frames"], strict=True)
        ):
            return False
        hashes = report["preview_sha256"]
        return bool(
            set(hashes) == {"initial.png", "final.png"}
            and all(
                hashlib.sha256((result_path.parent / name).read_bytes()).hexdigest() == digest
                for name, digest in hashes.items()
            )
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ZeroDivisionError):
        return False
