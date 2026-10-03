from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from evaluation.phase2_records import CellIdentity, envelope, verify_envelope, write_once


class Phase2RecordTests(unittest.TestCase):
    def test_identity_binds_selection_preprocessing_checkpoint_and_seeds(self) -> None:
        identity = CellIdentity(
            "cho2017",
            "subject_01",
            "labram_lora",
            5,
            11,
            None,
            None,
            *("a" * 64 for _ in range(8)),
            "b" * 40,
            True,
        )
        for field in (
            "selection_sha256",
            "episode_sha256",
            "checkpoint_sha256",
            "preprocessing_sha256",
            "environment_sha256",
        ):
            self.assertNotEqual(identity.sha256, replace(identity, **{field: "c" * 64}).sha256)
        self.assertNotEqual(identity.sha256, replace(identity, model_seed=23).sha256)
        record = envelope("evaluation_cell", asdict(identity))
        self.assertTrue(
            verify_envelope(record, kind="evaluation_cell", expected_payload=asdict(identity))
        )
        changed = envelope("evaluation_cell", asdict(replace(identity, method="labram_full")))
        self.assertFalse(
            verify_envelope(changed, kind="evaluation_cell", expected_payload=asdict(identity))
        )
        for changes in (
            {"model_seed": True},
            {"git_commit": "unversioned-workspace"},
            {"shots_per_class": 0},
            {"checkpoint_sha256": "unknown"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(identity, **changes)

    def test_concurrent_publication_resume_and_conflict_preserve_first_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "cell.json"
            payload = envelope("protocol_audit", {"source": "original"})
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda _: write_once(path, payload, output_root=root), range(8)))
            self.assertEqual(json.loads(path.read_text()), payload)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_once(path, {"changed": True}, output_root=root)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(list(root.glob(".phase2-*")))

    def test_interrupted_publish_has_no_partial_record_and_path_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "cell.json"
            with (
                patch("evaluation.phase2_records.os.link", side_effect=OSError("interrupted")),
                self.assertRaises(OSError),
            ):
                write_once(path, {"finite": 1}, output_root=root)
            self.assertFalse(path.exists())
            self.assertFalse(list(root.glob(".phase2-*")))
            with self.assertRaises(ValueError):
                write_once(root / ".." / "escape.json", {}, output_root=root)
            with self.assertRaises(ValueError):
                write_once(path, {"metric": float("nan")}, output_root=root)
