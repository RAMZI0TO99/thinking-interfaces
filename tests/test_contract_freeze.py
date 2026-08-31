from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.contract_freeze import verify_contract_freeze


class ContractFreezeTests(unittest.TestCase):
    def test_current_local_contract_matches_its_recorded_freeze(self):
        self.assertTrue(verify_contract_freeze(Path(__file__).resolve().parents[1]))

    def test_missing_or_changed_contract_fails(self):
        original = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(verify_contract_freeze(root))
            for name in ("configs/contract_freeze.toml", "core/contracts.py", "core/run_record.py"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((original / name).read_text("utf-8"), "utf-8")
            self.assertTrue(verify_contract_freeze(root))
            path = root / "core/contracts.py"
            path.write_text(path.read_text("utf-8") + "\n# unreviewed change\n", "utf-8")
            self.assertFalse(verify_contract_freeze(root))
