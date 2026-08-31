from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.provenance import capture_source, source_fingerprint


class ProvenanceTests(unittest.TestCase):
    def test_source_changes_but_data_and_outputs_do_not_change_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "core").mkdir()
            code = root / "core" / "model.py"
            code.write_text("version = 1")
            original = source_fingerprint(root)
            (root / "runs").mkdir()
            (root / "runs" / "result.json").write_text("{}")
            (root / "data" / "raw").mkdir(parents=True)
            (root / "data" / "raw" / "not_source.py").write_text("raw")
            self.assertEqual(source_fingerprint(root), original)
            code.write_text("version = 2")
            self.assertNotEqual(source_fingerprint(root), original)

    def test_absent_git_is_honestly_labelled(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("core.provenance.shutil.which", return_value=None),
        ):
            result = capture_source(Path(directory))
        self.assertEqual(result.git_commit, "unversioned-workspace")
        self.assertIsNone(result.git_dirty)
        self.assertEqual(len(result.source_sha256), 64)

    def test_dirty_source_is_not_reported_as_clean_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "core").mkdir()
            (root / "core" / "new.py").write_text("new = True")
            replies = [
                subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                subprocess.CompletedProcess([], 0, "?? core/new.py\n?? plan.docx\n", ""),
            ]
            with (
                patch("core.provenance.shutil.which", return_value="git"),
                patch("core.provenance.subprocess.run", side_effect=replies),
            ):
                result = capture_source(root)
        self.assertEqual(result.git_commit, "a" * 40)
        self.assertTrue(result.git_dirty)

    def test_untracked_reference_document_does_not_dirty_source(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("core.provenance.shutil.which", return_value="git"),
            patch(
                "core.provenance.subprocess.run",
                side_effect=[
                    subprocess.CompletedProcess([], 0, "a" * 40 + "\n", ""),
                    subprocess.CompletedProcess([], 0, "?? plan.docx\n", ""),
                ],
            ),
        ):
            result = capture_source(Path(directory))
        self.assertFalse(result.git_dirty)
