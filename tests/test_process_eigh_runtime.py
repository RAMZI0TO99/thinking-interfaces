from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation import process_eigh_runtime as runtime


class ProcessEighRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.backend = {"num_threads": 24, "version": "qualified-test-backend"}
        rows = []
        for subject in ("subject_01", "subject_02"):
            name = f"runs/benchmark/cho2017/ea_tangent_lr/seed_11/{subject}.json"
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(subject.encode())
            rows.append({
                "subject": subject,
                "reference_record": name,
                "reference_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "exact_non_timing_metrics_equal": True,
                "differences": {},
                "isolated_process_eigh": {"verified_backend": self.backend},
            })
        report = {
            "passed": True,
            "benchmark_config_sha256": "benchmark",
            "source": {"git_dirty": False},
            "probe_config": {"probe": {"method": "ea_tangent_lr"}},
            "rows": rows,
        }
        self.receipt = self.root / runtime.QUALIFICATION_PATH
        self.receipt.parent.mkdir(parents=True)
        self.receipt.write_text(json.dumps(report))
        self.digest = hashlib.sha256(self.receipt.read_bytes()).hexdigest()

    def ready(self, *, free=10.0, backend=None, **changes):
        with (
            patch.object(runtime, "QUALIFICATION_SHA256", self.digest),
            patch.object(runtime, "available_memory_gib", return_value=free),
            patch.object(runtime, "numpy_backend", return_value=backend or self.backend),
        ):
            return runtime.process_eigh_startup_ready(self.root, **{
                "enabled": True,
                "dataset": "cho2017",
                "methods": ("ea_tangent_lr",),
                "benchmark_sha256": "benchmark",
                **changes,
            })

    def test_unchanged_memory_guard_and_backend_identity(self):
        self.assertTrue(self.ready(free=10.0))
        self.assertFalse(self.ready(free=9.999))
        self.assertFalse(self.ready(backend={"num_threads": 4}))

    def test_other_datasets_methods_and_disabled_setting_do_not_load_the_receipt(self):
        self.receipt.unlink()
        for changes in (
            {"enabled": False}, {"dataset": "mmidb"}, {"methods": ("tangent_lr",)},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(self.ready(**changes))

    def test_receipt_or_reference_tampering_fails_closed(self):
        self.receipt.write_text(self.receipt.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            self.ready()
        self.receipt.write_text(self.receipt.read_text()[:-1])
        reference = self.root / "runs/benchmark/cho2017/ea_tangent_lr/seed_11/subject_02.json"
        reference.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "reference or exact-parity"):
            self.ready()

    def test_benchmark_binding_and_explicit_boolean_are_required(self):
        with self.assertRaisesRegex(ValueError, "two-fold benchmark protocol"):
            self.ready(benchmark_sha256="other")
        with self.assertRaisesRegex(ValueError, "explicit boolean"):
            self.ready(enabled="true")
        for settings in ({"enabled": "true"}, {"enabled": True, "workers": 4}, []):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                runtime.process_eigh_enabled({"tangent_process": settings})
        self.assertFalse(runtime.process_eigh_enabled({}))
        self.assertTrue(runtime.process_eigh_enabled({"tangent_process": {"enabled": True}}))
