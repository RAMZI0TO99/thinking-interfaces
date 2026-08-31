from __future__ import annotations

import math
import unittest

from core.config import config_digest, config_snapshot


class ConfigTests(unittest.TestCase):
    def test_digest_is_independent_of_mapping_order(self) -> None:
        first = {"model": {"name": "eegnet", "depth": 4}, "seed": 11}
        second = {"seed": 11, "model": {"depth": 4, "name": "eegnet"}}
        self.assertEqual(config_digest(first), config_digest(second))

    def test_snapshot_is_detached(self) -> None:
        original = {"model": {"name": "eegnet"}}
        snapshot = config_snapshot(original)
        original["model"]["name"] = "changed"
        self.assertEqual(snapshot["model"], {"name": "eegnet"})

    def test_non_finite_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            config_digest({"learning_rate": math.nan})


if __name__ == "__main__":
    unittest.main()

