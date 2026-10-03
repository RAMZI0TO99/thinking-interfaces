"""Confirm the present pre-cue control can be affected by later samples."""

from __future__ import annotations

import unittest

from scripts.diagnose_pre_cue_post_cue_leakage import diagnose


class PreCuePostCueLeakageDiagnosticTests(unittest.TestCase):
    def test_post_cue_pulse_changes_filtered_and_final_pre_cue_windows(self) -> None:
        result = diagnose()

        self.assertEqual(result["raw_pre_cue_max_abs_delta_uv"], 0.0)
        filtered_delta = result["filtered_pre_cue_max_abs_delta_uv"]
        final_delta = result["final_pre_cue_max_abs_delta_uv"]
        assert isinstance(filtered_delta, float)
        assert isinstance(final_delta, float)
        self.assertGreater(filtered_delta, 0.01)
        self.assertGreater(final_delta, 0.01)
        self.assertEqual(result["final_epoch_shape"], [1, 2, 128])


if __name__ == "__main__":
    unittest.main()
