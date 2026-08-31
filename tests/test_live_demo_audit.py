from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from core.config import config_digest, load_toml
from evaluation.live_demo_audit import verify_live_demo


class LiveDemoAuditTests(unittest.TestCase):
    def test_complete_receipt_passes_and_tampering_or_hidden_only_is_rejected(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "configs").mkdir()
            for name in ("live_demo.toml", "benchmark.toml"):
                shutil.copyfile(project / "configs" / name, root / "configs" / name)
            output = root / "runs" / "live_demo" / "test"
            output.mkdir(parents=True)
            receipt = {
                "completed": True,
                "error": None,
                "hidden_preview": False,
                "sequences": list(range(12)),
                "updates": [{"sequence": index, "state": "neutral"} for index in range(12)],
            }
            receipt_path = output / "interface_receipt.json"
            receipt_path.write_text(json.dumps(receipt))
            for name in ("initial.png", "final.png"):
                (output / name).write_bytes(b"test preview")
            frame = {
                "target": "left_hand",
                "decision_state": "neutral",
                "confidence": 0.25,
                "emitted_command": None,
                "latency_ms": 3.0,
            }
            config = load_toml(root / "configs" / "live_demo.toml")
            report = {
                "passed": True,
                "config": config,
                "config_sha256": config_digest(config),
                "benchmark_config_sha256": config_digest(
                    load_toml(root / "configs" / "benchmark.toml")
                ),
                "held_out_subject": "subject_09",
                "source_subjects": [f"subject_{i:02d}" for i in range(1, 9)],
                "source_trials": 100,
                "support_trials": 0,
                "source_query_disjoint": True,
                "query_indices": list(range(100, 112)),
                "query_class_counts": {
                    name: 3 for name in ("feet", "left_hand", "right_hand", "tongue")
                },
                "expected_samples": 6144,
                "sample_sha256": "a" * 64,
                "expected_wall_seconds": 6143 / 128,
                "wall_drift_seconds": 0.25,
                "stream": {
                    "received_samples": 6144,
                    "received_sample_sha256": "a" * 64,
                    "frames": [frame] * 12,
                    "processing_latency": {"count": 12},
                    "wall_seconds": 6143 / 128 + 0.25,
                },
                "interface_all_frames_rendered": True,
                "rendered_frames": [frame] * 12,
                "interface_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                "preview_sha256": {
                    name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                    for name in ("initial.png", "final.png")
                },
            }

            def save():
                result_path = output / "result.json"
                result_path.write_text(json.dumps(report))
                (output.parent / "latest.json").write_text(
                    json.dumps(
                        {
                            "result": result_path.relative_to(root).as_posix(),
                            "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                        }
                    )
                )

            save()
            self.assertTrue(verify_live_demo(root))
            report["stream"]["received_samples"] = 511
            save()
            self.assertFalse(verify_live_demo(root))
            report["stream"]["received_samples"] = 6144
            receipt["hidden_preview"] = True
            receipt_path.write_text(json.dumps(receipt))
            report["interface_receipt_sha256"] = hashlib.sha256(
                receipt_path.read_bytes()
            ).hexdigest()
            save()
            self.assertFalse(verify_live_demo(root))
            receipt["hidden_preview"] = False
            receipt_path.write_text(json.dumps(receipt))
            report["interface_receipt_sha256"] = hashlib.sha256(
                receipt_path.read_bytes()
            ).hexdigest()
            save()
            (output / "final.png").write_bytes(b"changed")
            self.assertFalse(verify_live_demo(root))
