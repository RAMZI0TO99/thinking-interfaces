"""Raw-input stability checks for the nine-subject signal audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.audit_real_pre_cue_no_future_all9 import (
    _raw_file_identity,
    _require_raw_files_unchanged,
)


class RawAuditIntegrityTests(unittest.TestCase):
    def test_postprocessing_check_refuses_same_size_mutation_of_last_raw_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_files = {
                f"A{subject:02d}{session}.mat": root / f"A{subject:02d}{session}.mat"
                for subject in range(1, 10)
                for session in ("T", "E")
            }
            for name, path in raw_files.items():
                path.write_bytes(f"raw input {name}".encode())
            initial_hashes = {
                name: _raw_file_identity(path) for name, path in raw_files.items()
            }
            _require_raw_files_unchanged(raw_files, initial_hashes)

            last = raw_files["A09E.mat"]
            changed = bytearray(last.read_bytes())
            changed[-1] ^= 1
            last.write_bytes(changed)
            self.assertEqual(last.stat().st_size, initial_hashes["A09E.mat"]["bytes"])
            with self.assertRaisesRegex(ValueError, "A09E.mat"):
                _require_raw_files_unchanged(raw_files, initial_hashes)


if __name__ == "__main__":
    unittest.main()
