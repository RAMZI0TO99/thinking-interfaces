"""Synthetic checks for the proposed no-future artifact writer."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from data.pre_cue_no_future import BCI_EVENT_ID, load_no_future_config
from scripts import preprocess_pre_cue_no_future_v1 as writer


def _small_artifact_arrays() -> dict[str, object]:
    return {
        "signals": np.zeros((2, 22, 128), dtype=np.float32),
        "labels": np.asarray(["feet", "tongue"]),
        "sessions": np.asarray(["0train", "0train"]),
        "runs": np.asarray(["0", "0"]),
        "trial_indices": np.asarray([0, 1], dtype=np.int64),
        "channel_names": tuple(load_no_future_config().channel_names),
    }


class NoFutureArtifactWriterTests(unittest.TestCase):
    def test_npz_orphan_exact_resume_and_conflict_preserve_first_bytes(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(writer, "guard_resources"),
        ):
            path = Path(temporary).resolve() / "proposed" / "subject_01.npz"
            arrays = _small_artifact_arrays()
            status, digest, size = writer._publish_npz(path, root=path.parent, **arrays)
            self.assertEqual(status, "created")
            original = path.read_bytes()
            self.assertEqual(digest, hashlib.sha256(original).hexdigest())
            self.assertEqual(size, len(original))
            with np.load(path, allow_pickle=False) as stored:
                np.testing.assert_array_equal(stored["signals"], arrays["signals"])
            status, retry_digest, retry_size = writer._publish_npz(
                path, root=path.parent, **arrays
            )
            self.assertEqual((status, retry_digest, retry_size), ("reused_orphan", digest, size))
            self.assertEqual(path.read_bytes(), original)
            changed = _small_artifact_arrays()
            changed["signals"][0, 0, 0] = 1.0
            with self.assertRaisesRegex(FileExistsError, "artifact differs"):
                writer._publish_npz(path, root=path.parent, **changed)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(sorted(item.name for item in path.parent.iterdir()), [path.name])

    def test_manifest_last_exact_resume_and_conflict(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(writer, "guard_resources"),
        ):
            directory = Path(temporary).resolve()
            artifact = directory / "subject_01.npz"
            manifest = directory / "subject_01.manifest.json"
            arrays = _small_artifact_arrays()
            writer._publish_npz(artifact, root=directory, **arrays)
            self.assertFalse(manifest.exists())
            payload = {"kind": "proposed", "artifact_sha256": writer.file_sha256(artifact)}
            self.assertEqual(writer._publish_manifest(manifest, payload, root=directory), "created")
            original = manifest.read_bytes()
            self.assertEqual(json.loads(original), payload)
            self.assertEqual(writer._publish_manifest(manifest, payload, root=directory), "reused")
            with self.assertRaisesRegex(FileExistsError, "manifest differs"):
                writer._publish_manifest(
                    manifest, {**payload, "kind": "changed"}, root=directory
                )
            self.assertEqual(manifest.read_bytes(), original)
            self.assertEqual(
                sorted(item.name for item in directory.iterdir()),
                sorted((artifact.name, manifest.name)),
            )

    def test_disk_and_ram_guards_fail_before_write(self) -> None:
        root = Path(".")
        for disk_gib, ram_gib, reserve_bytes, should_pass in (
            (20.0, 4.0, 0, True), (19.9, 8.0, 0, False),
            (30.0, 3.9, 0, False), (20.0, 4.0, 1, False),
        ):
            with (
                self.subTest(disk_gib=disk_gib, ram_gib=ram_gib),
                patch.object(writer.shutil, "disk_usage",
                             return_value=SimpleNamespace(free=int(disk_gib * writer.GIB))),
                patch.object(writer.psutil, "virtual_memory",
                             return_value=SimpleNamespace(available=int(ram_gib * writer.GIB))),
            ):
                if should_pass:
                    self.assertEqual(
                        writer.guard_resources(root, reserve_bytes=reserve_bytes)[
                            "available_ram_gib"
                        ], ram_gib
                    )
                else:
                    with self.assertRaisesRegex(RuntimeError, "resource guard failed"):
                        writer.guard_resources(root, reserve_bytes=reserve_bytes)

    def test_npz_reserve_and_post_temp_guard_prevent_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            path = root / "proposed" / "subject_01.npz"
            arrays = _small_artifact_arrays()
            with (
                patch.object(
                    writer, "guard_resources", side_effect=RuntimeError("resource guard failed")
                ) as guard,
                self.assertRaisesRegex(RuntimeError, "resource guard failed"),
            ):
                writer._publish_npz(path, root=root, **arrays)
            self.assertGreater(guard.call_args.kwargs["reserve_bytes"],
                               arrays["signals"].nbytes)
            self.assertFalse(path.parent.exists())

            calls = []

            def fail_after_temporary(_root: Path, *, reserve_bytes: int = 0) -> None:
                calls.append(reserve_bytes)
                if len(calls) == 3:
                    raise RuntimeError("resource guard failed after temporary")

            with (
                patch.object(writer, "guard_resources", side_effect=fail_after_temporary),
                self.assertRaisesRegex(RuntimeError, "after temporary"),
            ):
                writer._publish_npz(path, root=root, **arrays)
            self.assertEqual(len(calls), 3)
            self.assertGreater(calls[0], arrays["signals"].nbytes)
            self.assertEqual(calls[2], 4096)
            self.assertFalse(path.exists())
            self.assertEqual(list(path.parent.iterdir()), [])

    def test_parent_symlink_cannot_redirect_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            actual = root / "actual"
            actual.mkdir()
            alias = root / "alias"
            path = alias / "subject_01.npz"
            original_resolve = Path.resolve

            def resolve_parent_swap(candidate: Path, *args: object, **kwargs: object) -> Path:
                if candidate == path:
                    return actual / path.name
                return original_resolve(candidate, *args, **kwargs)

            with (
                patch.object(Path, "resolve", resolve_parent_swap),
                patch.object(writer, "guard_resources"),
                self.assertRaisesRegex(ValueError, "aliases another location"),
            ):
                self.assertFalse(writer._unaliased_file(path))
                writer._publish_npz(path, root=root, **_small_artifact_arrays())
            self.assertEqual(list(actual.iterdir()), [])

    def test_raw_pre_post_pin_and_changed_during_hash_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            raw_dir = root / "raw"
            raw_dir.mkdir()
            pins = {}
            for suffix, contents in (("T", b"training"), ("E", b"evaluation")):
                name = f"A01{suffix}.mat"
                (raw_dir / name).write_bytes(contents)
                pins[name] = {"sha256": hashlib.sha256(contents).hexdigest(),
                              "bytes": len(contents)}
            plan = writer.Plan(
                root=root, raw_dir=raw_dir, output_dir=root / "proposed",
                config=load_no_future_config(), observed={"raw_files": pins},
                source_sha256={}, expected_runs={},
            )
            self.assertEqual(writer.verify_raw_subject(plan, 1), pins)
            (raw_dir / "A01T.mat").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "differs from the all-nine-subject receipt"):
                writer.verify_raw_subject(plan, 1)

            (raw_dir / "A01T.mat").write_bytes(b"training")
            original_hash = writer.file_sha256

            def mutate_while_hashing(path: Path) -> str:
                result = original_hash(path)
                if path.name == "A01T.mat":
                    path.write_bytes(b"changed")
                return result

            with (
                patch.object(writer, "file_sha256", side_effect=mutate_while_hashing),
                self.assertRaisesRegex(ValueError, "changed while hashing"),
            ):
                writer.verify_raw_subject(plan, 1)

    def test_source_config_hash_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            config = root / "configs/pre_cue_no_future_v1.toml"
            config.parent.mkdir()
            config.write_bytes(b"pinned")
            writer_file = root / writer.WRITER_RELATIVE
            writer_file.parent.mkdir()
            writer_file.write_bytes(b"writer")
            pinned = {"configs/pre_cue_no_future_v1.toml": writer.file_sha256(config)}
            with patch.object(writer, "REQUIRED_AUDIT_PATHS", tuple(pinned)):
                hashes = writer._source_hashes(root, pinned)
                self.assertEqual(hashes[writer.WRITER_RELATIVE], writer.file_sha256(writer_file))
                config.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "source/config differs"):
                    writer._source_hashes(root, pinned)

    def test_moabb_loader_can_request_only_the_two_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            raw_dir = root / "raw"
            raw_dir.mkdir()
            plan = writer.Plan(
                root=root, raw_dir=raw_dir, output_dir=root / "proposed",
                config=load_no_future_config(), observed={},
                source_sha256={}, expected_runs={},
            )
            case = self

            class LocalDataset:
                event_id = dict(BCI_EVENT_ID)

                def get_data(self, *, subjects: list[int], n_jobs: int) -> dict[int, object]:
                    self_paths = [writer.bnci_2014.data_path(
                        f"https://example.invalid/A01{part}.mat", None, False, None
                    )[0] for part in ("T", "E")]
                    case.assertEqual(subjects, [1])
                    case.assertEqual(n_jobs, 1)
                    case.assertEqual(self_paths, [str(raw_dir / f"A01{part}.mat")
                                                  for part in ("T", "E")])
                    return {1: {"0train": {}, "1test": {}}}

            with patch.object(writer, "BNCI2014_001", return_value=LocalDataset()):
                data, event_id = writer._local_subject_data(plan, 1)
            self.assertEqual(set(data), set(writer.SESSIONS))
            self.assertEqual(event_id, BCI_EVENT_ID)

            class DownloadingDataset(LocalDataset):
                def get_data(self, *, subjects: list[int], n_jobs: int) -> dict[int, object]:
                    writer.bnci_2014.data_path(
                        "https://example.invalid/A02T.mat", None, False, None
                    )
                    return {1: {}}

            with (
                patch.object(writer, "BNCI2014_001", return_value=DownloadingDataset()),
                self.assertRaisesRegex(ValueError, "unpinned or downloadable"),
            ):
                writer._local_subject_data(plan, 1)

    def test_subject_shape_count_and_audited_label_order(self) -> None:
        expected_runs = {
            (session, run): tuple((500 + index * 10, tuple(BCI_EVENT_ID)[index % 4])
                                  for index in range(48))
            for session in writer.SESSIONS for run in writer.RUNS
        }
        rows = [(session, run, index, label)
                for session in writer.SESSIONS for run in writer.RUNS
                for index, (_, label) in enumerate(expected_runs[(session, run)])]
        arrays = {
            "subject": 1,
            "signals": np.zeros((576, 22, 128), dtype=np.float32),
            "labels": np.asarray([label for _, _, _, label in rows]),
            "sessions": np.asarray([session for session, _, _, _ in rows]),
            "runs": np.asarray([run for _, run, _, _ in rows]),
            "trial_indices": np.asarray([index for _, _, index, _ in rows], dtype=np.int64),
            "channel_names": tuple(load_no_future_config().channel_names),
            "config": load_no_future_config(),
            "expected_runs": expected_runs,
        }
        self.assertEqual(writer.validate_arrays(**arrays)["shape"], (576, 22, 128))
        changed = {**arrays, "labels": arrays["labels"].copy()}
        changed["labels"][0] = "tongue"
        with self.assertRaisesRegex(ValueError, "audited cue roster differs"):
            writer.validate_arrays(**changed)
        changed = {**arrays, "signals": arrays["signals"][:-1]}
        with self.assertRaisesRegex(ValueError, "signal shape"):
            writer.validate_arrays(**changed)

    def test_check_only_verifies_complete_pair_and_rejects_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = root / "proposed"
            expected_runs = {
                (session, run): tuple((500 + index * 10, tuple(BCI_EVENT_ID)[index % 4])
                                      for index in range(48))
                for session in writer.SESSIONS for run in writer.RUNS
            }
            rows = [(session, run, index, label)
                    for session in writer.SESSIONS for run in writer.RUNS
                    for index, (_, label) in enumerate(expected_runs[(session, run)])]
            config = load_no_future_config()
            arrays = {
                "signals": np.zeros((576, 22, 128), dtype=np.float32),
                "labels": np.asarray([label for _, _, _, label in rows]),
                "sessions": np.asarray([session for session, _, _, _ in rows]),
                "runs": np.asarray([run for _, run, _, _ in rows]),
                "trial_indices": np.asarray([index for _, _, index, _ in rows], dtype=np.int64),
                "channel_names": config.channel_names,
            }
            plan = writer.Plan(
                root=root, raw_dir=root / "raw", output_dir=output,
                config=config, observed={"source_sha256": {}},
                source_sha256={"writer": "a" * 64}, expected_runs={1: expected_runs},
            )
            artifact = output / "subject_01.npz"
            manifest = output / "subject_01.manifest.json"
            raw_files = {"A01T.mat": {"sha256": "b" * 64, "bytes": 1}}
            with (
                patch.object(writer, "guard_resources"),
                patch.object(writer, "_source_hashes", return_value=plan.source_sha256),
                patch.object(writer, "verify_raw_subject", return_value=raw_files),
            ):
                with self.assertRaisesRegex(FileNotFoundError, "completed no-future"):
                    writer.check_subject(plan, 1)
                _, digest, size = writer._publish_npz(artifact, root=root, **arrays)
                summary = writer.validate_arrays(
                    subject=1, **arrays, config=config, expected_runs=expected_runs
                )
                payload = writer._manifest(
                    plan, 1, summary, raw_files, artifact, digest, size
                )
                writer._publish_manifest(manifest, payload, root=root)
                matching = writer.SubjectComputation(**arrays, summary=summary)
                with patch.object(writer, "_compute_subject", return_value=matching):
                    self.assertEqual(writer.check_subject(plan, 1)["status"],
                                     "verified_existing")
                forged_raw_signals = arrays["signals"].copy()
                forged_raw_signals[0, 0, 0] = 1.0
                recomputed = writer.SubjectComputation(
                    **{**arrays, "signals": forged_raw_signals}, summary=summary
                )
                with patch.object(writer, "_compute_subject", return_value=recomputed):
                    with self.assertRaisesRegex(ValueError, "recomputed pinned raw windows"):
                        writer.check_subject(plan, 1)
                    with self.assertRaisesRegex(ValueError, "recomputed pinned raw windows"):
                        writer.process_subject(plan, 1)
                manifest.write_bytes(b'{"tampered":true}\n')
                with (
                    patch.object(writer, "_compute_subject", return_value=matching),
                    self.assertRaisesRegex(ValueError, "manifest differs"),
                ):
                    writer.check_subject(plan, 1)


if __name__ == "__main__":
    unittest.main()
