from __future__ import annotations

import builtins
import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.config import load_toml
from scripts import probe_classical_runtime as script


class ProcessProbeCliTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.normal = load_toml(self.root / "configs/tangent_process_probe.toml")
        self.aligned = load_toml(self.root / "configs/ea_tangent_process_probe.toml")

    def test_alignment_configuration_only_changes_the_method(self):
        expected = copy.deepcopy(self.normal)
        expected["probe"]["method"] = "ea_tangent_lr"
        self.assertEqual(self.aligned, expected)

    def guarded_main(self, config, *, free_memory=9.99, dirty=False):
        original_import = builtins.__import__

        def checked_import(name, *args, **kwargs):
            if name in {"evaluation.baselines", "evaluation.benchmark"}:
                raise AssertionError("heavy EEG stack imported before qualification guards")
            return original_import(name, *args, **kwargs)

        with (
            patch("sys.argv", ["probe_classical_runtime.py"]),
            patch.object(script, "load_toml", side_effect=[{}, config]),
            patch.object(script, "capture_source", return_value=SimpleNamespace(git_dirty=dirty)),
            patch.object(script, "available_memory_gib", return_value=free_memory),
            patch("builtins.__import__", side_effect=checked_import),
        ):
            script.main()

    def test_both_variants_defer_below_unchanged_memory_guard_before_model_imports(self):
        for config in (self.normal, self.aligned):
            with (
                self.subTest(method=config["probe"]["method"]),
                self.assertRaisesRegex(SystemExit, "before model imports"),
            ):
                self.guarded_main(config)

    def test_dirty_source_fails_before_model_imports(self):
        with self.assertRaisesRegex(ValueError, "commit the process-probe source"):
            self.guarded_main(self.aligned, free_memory=16.0, dirty=True)

    def test_unqualified_method_or_changed_resource_settings_fail_closed(self):
        changes = (
            ("probe", "method", "ea_eegnet"),
            ("probe", "method", "fbcsp"),
            ("probe", "eigh_processes", 3),
            ("probe", "eigh_chunk_matrices", 128),
            ("probe", "blas_threads", 4),
            ("runtime", "minimum_free_memory_gib", 9.0),
            ("runtime", "stop_below_free_memory_gib", 3.0),
        )
        for section, key, value in changes:
            config = copy.deepcopy(self.aligned)
            config[section][key] = value
            with (
                self.subTest(section=section, key=key, value=value),
                self.assertRaisesRegex(ValueError, "bounded protocol"),
            ):
                self.guarded_main(config, free_memory=16.0)


if __name__ == "__main__":
    unittest.main()
