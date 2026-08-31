from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import evaluate_gate_b as gate_cli


class GateBCLIEvidenceTests(unittest.TestCase):
    def prepare(self, root: Path):
        configs = root / "configs"
        configs.mkdir()
        (configs / "gate_b.toml").write_text(
            '[gate_b]\nrequired_datasets = ["cho2017"]\n'
            'required_methods = ["eegnet"]\nseeds = [11]\n'
            'margin_source_dataset = "cho2017"\nmargin_source_method = "eegnet"\n'
            "target_power = 0.8\nalpha = 0.05\nupstream_gate_a_signed = false\n"
            "[subjects]\ncho2017 = 1\n"
        )
        (configs / "benchmark.toml").write_text(
            '[datasets.cho2017]\nartifact_directory = "artifacts"\n'
        )
        (configs / "artifact_rejection.toml").write_text(
            '[policy]\nfrozen = true\nfreeze_date = "test"\n'
        )
        (root / "artifacts").mkdir()
        (root / "artifacts" / "subject_01.npz").touch()
        (root / "runs").mkdir()
        (root / "runs" / "artifact_audit_status.json").write_text('{"passed": true}')
        (root / "runs" / "replay_demo_subject_09_cuda.json").write_text(
            json.dumps({"frames": [{"command": "left"}], "query_trials": 1})
        )

    def run_cli(self, root: Path):
        incomplete = SimpleNamespace(passed=False, as_dict=lambda: {"passed": False})
        with (
            patch.object(gate_cli, "__file__", str(root / "scripts" / "evaluate_gate_b.py")),
            patch.object(gate_cli, "evaluate_gate_b", return_value=incomplete) as evaluator,
            patch("builtins.print"),
            self.assertRaises(SystemExit) as stopped,
        ):
            gate_cli.main()
        self.assertEqual(stopped.exception.code, 1)
        return evaluator.call_args.kwargs

    def test_legacy_array_frames_do_not_pass_demonstrator_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            arguments = self.run_cli(root)
        self.assertFalse(arguments["demonstrator_passed"])

    def test_native_verifier_result_is_used_without_changing_upstream_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.prepare(root)
            with patch.object(gate_cli, "verify_live_demo", return_value=True) as verifier:
                arguments = self.run_cli(root)
            verifier.assert_called_once_with(root.resolve())
        self.assertTrue(arguments["demonstrator_passed"])
        self.assertFalse(arguments["upstream_gate_a_signed"])


if __name__ == "__main__":
    unittest.main()
