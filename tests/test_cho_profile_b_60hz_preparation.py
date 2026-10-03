from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import preprocess_cho_profile_b_60hz as prepare

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Cho60HzPreparationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in (
            "configs/base.toml",
            "configs/cho2017.toml",
            "configs/phase2/cho_profile_b_60hz.toml",
        ):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT_ROOT / relative, target)
        self.raw_root = self.root / "data/raw/moabb/cho2017"
        self.raw_root.mkdir(parents=True)
        self.raw = self.raw_root / "subject_01.mat"
        self.raw.write_bytes(b"synthetic raw source")
        self.output = self.root / "data/processed/cho2017/profile_b_60hz_v1"

    def synthetic(self) -> tuple[object, ...]:
        return (
            np.zeros((2, 64, 800), dtype=np.float32),
            np.asarray(["left_hand", "right_hand"]),
            np.asarray(["0", "0"]),
            np.asarray(["0", "0"]),
            np.asarray([0, 1], dtype=np.int64),
            tuple(f"C{index:02d}" for index in range(64)),
        )

    def test_dry_run_never_loads_raw_or_writes_output(self) -> None:
        stream = io.StringIO()
        with (
            patch.object(prepare, "ROOT", self.root),
            patch.object(prepare, "preprocess_profile_b_cho_subject") as preprocess,
            patch.object(prepare, "download_subject") as download,
            redirect_stdout(stream),
        ):
            self.assertEqual(prepare.main(["--subjects", "1", "52", "--dry-run"]), 0)
        self.assertEqual(preprocess.call_count, 0)
        self.assertEqual(download.call_count, 0)
        self.assertFalse(self.output.exists())
        rows = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual([row["subject"] for row in rows], [1, 52])
        self.assertTrue(
            all(Path(row["artifact"]).parent == self.output.resolve() for row in rows)
        )

    def test_refuses_historical_path_and_config_mismatch(self) -> None:
        variant_path = self.root / prepare.VARIANT_CONFIG
        original = variant_path.read_text(encoding="utf-8")
        variant_path.write_text(
            original.replace("profile_b_60hz_v1", "profile_b"), encoding="utf-8"
        )
        with (
            patch.object(prepare, "ROOT", self.root),
            self.assertRaisesRegex(ValueError, "variant identity"),
        ):
            prepare.main(["--subjects", "1", "--dry-run"])
        variant_path.write_text(original.replace("notch_hz = 60.0", "notch_hz = 50.0"))
        with (
            patch.object(prepare, "ROOT", self.root),
            self.assertRaisesRegex(ValueError, "copy base Profile B"),
        ):
            prepare.main(["--subjects", "1", "--dry-run"])

    def test_rejects_bad_roster_before_raw_access(self) -> None:
        with (
            patch.object(prepare, "ROOT", self.root),
            patch.object(prepare, "download_subject") as download,
        ):
            with self.assertRaisesRegex(ValueError, "unique members"):
                prepare.main(["--subjects", "1", "1"])
            with self.assertRaisesRegex(ValueError, "unique members"):
                prepare.main(["--subjects", "53"])
        download.assert_not_called()

    def test_pair_is_write_once_and_same_byte_resume_only(self) -> None:
        dataset, config, raw_root, output, floor = prepare.load_plan(self.root)
        self.assertEqual(dataset["key"], "cho2017")
        with (
            patch.object(prepare, "check_space"),
            patch.object(prepare, "configure_local_cache"),
            patch.object(prepare, "download_subject", return_value=self.raw),
            patch.object(
                prepare, "preprocess_profile_b_cho_subject", return_value=self.synthetic()
            ),
        ):
            first = prepare.process_subject(1, self.root, config, raw_root, output, floor)
            self.assertEqual(first["status"], "created")
            self.assertEqual(first["source_file"], "data/raw/moabb/cho2017/subject_01.mat")
            artifact = output / "subject_01.npz"
            manifest = output / "subject_01.manifest.json"
            initial_bytes = artifact.read_bytes()
            initial_manifest = manifest.read_bytes()
            record = json.loads(initial_manifest)
            self.assertEqual(record["variant"], prepare.VARIANT)
            self.assertEqual(record["source_sha256"], prepare.file_digest(self.raw))
            self.assertEqual(record["variant_config_sha256"], first["variant_config_sha256"])
            resumed = prepare.process_subject(1, self.root, config, raw_root, output, floor)
            self.assertEqual(resumed["status"], "reused")
            self.assertEqual(artifact.read_bytes(), initial_bytes)
            self.assertEqual(manifest.read_bytes(), initial_manifest)
            manifest.write_bytes(initial_manifest + b" ")
            with self.assertRaisesRegex(FileExistsError, "manifest differs"):
                prepare.process_subject(1, self.root, config, raw_root, output, floor)
            self.assertEqual(artifact.read_bytes(), initial_bytes)
            self.assertEqual(manifest.read_bytes(), initial_manifest + b" ")

    def test_incomplete_pair_refuses_without_processing(self) -> None:
        _dataset, config, raw_root, output, floor = prepare.load_plan(self.root)
        output.mkdir(parents=True)
        (output / "subject_01.npz").write_bytes(b"partial")
        with (
            patch.object(prepare, "check_space"),
            patch.object(prepare, "preprocess_profile_b_cho_subject") as preprocess,
            self.assertRaisesRegex(FileExistsError, "incomplete existing"),
        ):
            prepare.process_subject(1, self.root, config, raw_root, output, floor)
        preprocess.assert_not_called()

    def test_direct_subject_call_refuses_historical_path(self) -> None:
        _dataset, config, raw_root, _output, floor = prepare.load_plan(self.root)
        historical = self.root / "data/processed/cho2017/profile_b"
        with (
            patch.object(prepare, "preprocess_profile_b_cho_subject") as preprocess,
            self.assertRaisesRegex(ValueError, "versioned namespace"),
        ):
            prepare.process_subject(1, self.root, config, raw_root, historical, floor)
        preprocess.assert_not_called()
        self.assertFalse(historical.exists())

    def test_disk_floor_and_reserve_block_subject_before_raw_access(self) -> None:
        _dataset, config, raw_root, output, floor = prepare.load_plan(self.root)
        with (
            patch("shutil.disk_usage", return_value=shutil._ntuple_diskusage(0, 0, 0)),
            patch.object(prepare, "download_subject") as download,
            self.assertRaisesRegex(RuntimeError, "insufficient disk space"),
        ):
            prepare.process_subject(1, self.root, config, raw_root, output, floor)
        download.assert_not_called()

    def test_linked_output_directory_cannot_alias_historical_cohort(self) -> None:
        _dataset, config, raw_root, _output, floor = prepare.load_plan(self.root)
        legacy = self.root / "data/processed/cho2017/profile_b"
        legacy.mkdir(parents=True)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.output.symlink_to(legacy, target_is_directory=True)
        except OSError as error:
            if os.name != "nt":
                self.skipTest(f"directory links unavailable: {error}")
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(self.output), str(legacy)],
                capture_output=True, check=False,
            )
            if result.returncode:
                self.skipTest(f"directory links unavailable: {error}")
        with self.assertRaisesRegex(ValueError, "aliases or escapes"):
            prepare.load_plan(self.root)
        with (
            patch.object(prepare, "download_subject") as download,
            self.assertRaisesRegex(ValueError, "aliases or escapes"),
        ):
            prepare.process_subject(1, self.root, config, raw_root, self.output, floor)
        download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
