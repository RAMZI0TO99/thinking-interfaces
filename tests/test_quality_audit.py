from __future__ import annotations

import hashlib
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from core.provenance import source_fingerprint
from evaluation.quality_audit import QUALITY_COMMANDS, verify_quality_bundle


class QualityAuditTests(unittest.TestCase):
    def test_exact_source_and_logs_pass_but_stale_or_incomplete_bundle_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            logs = root / "runs" / "quality"
            logs.mkdir(parents=True)
            payload = {
                "passed": True,
                "source_sha256_before": source_fingerprint(root),
                "source_sha256_after": source_fingerprint(root),
                "checks": {},
            }
            for name, command in QUALITY_COMMANDS.items():
                log = logs / f"{name}.txt"
                log.write_text("passed")
                payload["checks"][name] = {
                    "arguments": list(command),
                    "exit_code": 0,
                    "log": log.relative_to(root).as_posix(),
                    "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                }
            self.assertTrue(verify_quality_bundle(root, payload))
            for field, value in (("exit_code", 1), ("arguments", []), ("log", "outside.txt")):
                with self.subTest(field=field):
                    damaged = deepcopy(payload)
                    damaged["checks"]["tests"][field] = value
                    self.assertFalse(verify_quality_bundle(root, damaged))
            missing = deepcopy(payload)
            del missing["checks"]["types"]
            self.assertFalse(verify_quality_bundle(root, missing))
            (logs / "tests.txt").write_text("changed")
            self.assertFalse(verify_quality_bundle(root, payload))
            (logs / "tests.txt").write_text("passed")
            (root / "core").mkdir()
            (root / "core" / "changed.py").write_text("changed = True")
            self.assertFalse(verify_quality_bundle(root, payload))
