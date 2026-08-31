from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.smoke_moabb_reference import main


class MoabbReferenceSmokeGuardTests(unittest.TestCase):
    def test_low_memory_defers_without_loading_or_training_model(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "environment.json"
            receipt.write_text(json.dumps({"training_ready": False,
                                          "resources": {"ready": False}}), encoding="utf-8")
            completed = subprocess.CompletedProcess(
                [], 0, stdout=json.dumps({"report": str(receipt)})
            )
            output = StringIO()
            with (
                patch("sys.argv", ["smoke_moabb_reference.py"]),
                patch("scripts.smoke_moabb_reference.subprocess.run", return_value=completed),
                patch("scripts.smoke_moabb_reference.run_smoke") as trainer,
                redirect_stdout(output),
            ):
                self.assertEqual(main(), 2)
                trainer.assert_not_called()
            result = json.loads(output.getvalue())
            self.assertTrue(result["deferred"])
            self.assertFalse(result["training_performed"])

    def test_failed_preflight_never_reaches_training(self):
        with (
            patch("sys.argv", ["smoke_moabb_reference.py"]),
            patch("scripts.smoke_moabb_reference.subprocess.run",
                  side_effect=subprocess.CalledProcessError(1, ["checker"])),
            patch("scripts.smoke_moabb_reference.run_smoke") as trainer,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            main()
        trainer.assert_not_called()

    def test_smoke_cannot_expand_into_a_full_experiment(self):
        valid = {"subject": 1, "epochs": 2, "fold_count": 5, "fold_index": 0}
        for changed in ({"epochs": 300}, {"epochs": 2.0}, {"subject": True},
                        {"subject": 10}, {"fold_index": -1}, {"fold_index": 5},
                        {"fold_count": 5.0}, {"fold_count": 10}):
            with (
                self.subTest(changed=changed),
                patch("sys.argv", ["smoke_moabb_reference.py"]),
                patch("scripts.smoke_moabb_reference.tomllib.loads",
                      return_value={"smoke": {**valid, **changed}}),
                patch("scripts.smoke_moabb_reference.subprocess.run") as preflight,
                self.assertRaises(ValueError),
            ):
                main()
            preflight.assert_not_called()


if __name__ == "__main__":
    unittest.main()
