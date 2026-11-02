"""Adversarial retained-reader test SOURCES, requiring separate run admission.

All filesystem writes stay in new, exclusive children of CUSTODY_TEST_ROOT.
There is no fallback to cwd/temp, no subprocess, no symlink privilege assumption,
and no platform skip. Unsupported Windows/filesystem/fixture setup fails closed.
Reparse refusals inject attributes at the native API boundary: real junction or
symlink creation is not claimed, because privilege-free creation is not assumed.
These tests exercise local bytes and namespace exclusion, never host identity,
historical custody, provider qualification or review authority.
"""

import ctypes
import hashlib
import importlib.util
import os
from pathlib import Path
import unittest
from unittest import mock


HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("custody_retained_reader_v2", HERE / "retained_reader.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def reference(path, data):
    return {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


class RetainedReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name != "nt":
            raise RuntimeError("retained-reader qualification requires native Windows")
        supplied = os.environ.get("CUSTODY_TEST_ROOT")
        if supplied is None:
            raise RuntimeError("CUSTODY_TEST_ROOT must identify admitted fresh fixture directory")
        reader._root_path(supplied)
        cls.fixture_root = Path(supplied)
        if not cls.fixture_root.is_dir() or any(cls.fixture_root.iterdir()):
            raise RuntimeError("test fixture root must exist and be empty")
        # Retain the fixture root/ancestors throughout the suite, so the admitted
        # output directory cannot be renamed or replaced between individual cases.
        cls.fixture_guard = reader.RetainedArtifactSet(supplied)

    @classmethod
    def tearDownClass(cls):
        cls.fixture_guard.close()

    def setUp(self):
        self.root = self.fixture_root / self._testMethodName
        self.root.mkdir()  # exclusive; no replay/cleanup of a previous identity

    def put(self, relative="Artifact.bin", data=b"local pinned bytes"):
        path = self.root.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)
        return path, reference(relative, data)

    def open_set(self):
        return reader.RetainedArtifactSet(str(self.root))

    def test_plain_read_pins_and_identity_from_handle(self):
        path, ref = self.put("Nested/Artifact.bin")
        with self.open_set() as retained:
            self.assertEqual(retained.read(ref), b"local pinned bytes")
            retained.verify()
            witness, = retained.witnesses
            self.assertEqual(witness["final_path"], str(path))
            self.assertEqual(witness["bytes"], ref["bytes"])
            self.assertEqual(witness["sha256"], ref["sha256"])
            self.assertEqual(witness["links"], 1)
            self.assertGreater(witness["file_index"], 0)
            self.assertEqual(witness["share_mode"], reader.FILE_SHARE_READ)
            self.assertEqual(witness["filesystem"], "NTFS")

    def test_witness_copies_cannot_mutate_retained_pins(self):
        _, ref = self.put()
        with self.open_set() as retained:
            retained.read(ref)
            retained.witnesses[0]["bytes"] = 999
            self.assertEqual(retained.witnesses[0]["bytes"], ref["bytes"])
            retained.verify()

    def test_repeat_exact_reference_reuses_handle(self):
        _, ref = self.put()
        with self.open_set() as retained:
            first = retained.read(ref)
            count = len(retained._handles)
            self.assertEqual(retained.read(dict(ref)), first)
            self.assertEqual(len(retained._handles), count)
            self.assertEqual(len(retained.witnesses), 1)

    def test_wrong_hash_closes_and_poisons_set(self):
        path, ref = self.put()
        retained = self.open_set()
        with self.assertRaises(reader.RetainedArtifactError):
            retained.read(dict(ref, sha256="0" * 64))
        self.assertEqual(retained._handles, [])
        with self.assertRaises(reader.RetainedArtifactError):
            retained.verify()
        path.write_bytes(b"released after refusal")

    def test_wrong_byte_count_is_refused(self):
        _, ref = self.put()
        with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
            retained.read(dict(ref, bytes=ref["bytes"] + 1))

    def test_reference_exact_types_and_fields(self):
        _, ref = self.put()
        bad = [None, [], dict(ref, bytes=True), dict(ref, bytes=1.0),
               dict(ref, bytes=-1), dict(ref, path=Path("Artifact.bin")),
               dict(ref, sha256="A" * 64), dict(ref, sha256=False),
               dict(ref, extra="ignored"), {"path": "Artifact.bin", "bytes": 1}]
        for sample in bad:
            with self.subTest(sample=sample), self.open_set() as retained:
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(sample)

    def test_outside_traversal_device_stream_and_short_alias_paths(self):
        _, ref = self.put()
        bad = ("../Artifact.bin", "/Artifact.bin", "a//b", "a/./b", "a/../b", "a/",
               "C:/Artifact.bin", "\\\\host\\share", "\\\\?\\D:\\Artifact.bin",
               "a\\b", "Artifact.bin:stream", "CON", "nul.txt", "COM1.txt", "a.",
               "a /b", "PROGRA~1/Artifact.bin", "a\x00b")
        for path in bad:
            with self.subTest(path=path), self.open_set() as retained:
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(dict(ref, path=path))

    def test_case_alias_file_and_directory_are_refused(self):
        _, ref = self.put("MixedCase/Artifact.bin")
        for path in ("mixedcase/Artifact.bin", "MixedCase/artifact.bin"):
            with self.subTest(path=path), self.open_set() as retained:
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(dict(ref, path=path))

    def test_root_alias_and_unsupported_namespace_inputs(self):
        bad = (str(self.root).replace("D:", "d:", 1) if str(self.root).startswith("D:")
               else str(self.root)[0].lower() + str(self.root)[1:],
               str(self.root) + "\\", str(self.root) + "\\..", "relative",
               "\\\\host\\share", "\\\\?\\" + str(self.root), str(self.root).replace("\\", "/"))
        for root in bad:
            with self.subTest(root=root), self.assertRaises(reader.RetainedArtifactError):
                reader.RetainedArtifactSet(root)
        # A well-formed root with incorrect directory case must also fail.
        altered = str(self.root.parent / self.root.name.upper())
        with self.assertRaises(reader.RetainedArtifactError):
            reader.RetainedArtifactSet(altered)

    def test_existing_writer_prevents_retention(self):
        path, ref = self.put()
        with path.open("r+b") as writer:
            writer.write(b"local")
            writer.flush()
            with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
                retained.read(ref)

    def test_ordinary_write_delete_and_rename_excluded_while_held(self):
        path, ref = self.put()
        with self.open_set() as retained:
            retained.read(ref)
            with self.assertRaises(OSError):
                with path.open("r+b"):
                    pass
            with self.assertRaises(OSError):
                path.unlink()
            with self.assertRaises(OSError):
                path.rename(self.root / "Renamed.bin")
            retained.verify()

    def test_directory_rename_excluded_while_chain_retained(self):
        _, ref = self.put("Nested/Artifact.bin")
        with self.open_set() as retained:
            retained.read(ref)
            with self.assertRaises(OSError):
                (self.root / "Nested").rename(self.root / "Moved")
            with self.assertRaises(OSError):
                self.root.rename(self.root.with_name(self.root.name + "-moved"))
            retained.verify()

    def test_release_restores_read_write_and_rename(self):
        path, ref = self.put()
        retained = self.open_set()
        retained.read(ref)
        retained.close()
        retained.close()
        self.assertEqual(path.read_bytes(), b"local pinned bytes")
        path.write_bytes(b"after release")
        moved = path.rename(self.root / "Moved.bin")
        self.assertEqual(moved.read_bytes(), b"after release")
        with self.assertRaises(reader.RetainedArtifactError):
            retained.read(ref)

    def test_context_exception_releases_all_handles(self):
        path, ref = self.put("Nested/Artifact.bin")
        with self.assertRaisesRegex(RuntimeError, "sentinel"):
            with self.open_set() as retained:
                retained.read(ref)
                raise RuntimeError("sentinel")
        self.assertEqual(retained._handles, [])
        path.write_bytes(b"released")

    def test_changed_source_before_open_is_refused(self):
        path, ref = self.put()
        path.write_bytes(b"X" * ref["bytes"])
        with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
            retained.read(ref)

    def test_empty_artifact_eof_and_digest(self):
        _, ref = self.put(data=b"")
        with self.open_set() as retained:
            self.assertEqual(retained.read(ref), b"")
            retained.verify()

    def test_directory_cannot_be_read_as_regular_file(self):
        (self.root / "Directory").mkdir()
        with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
            retained.read(reference("Directory", b""))

    def test_missing_file_refuses_and_closes_all_ancestors(self):
        (self.root / "Nested").mkdir()
        retained = self.open_set()
        with self.assertRaises(reader.RetainedArtifactError):
            retained.read(reference("Nested/missing.bin", b""))
        self.assertEqual(retained._handles, [])
        (self.root / "Nested").rename(self.root / "Moved")

    def test_real_ntfs_hardlink_is_refused(self):
        path, ref = self.put()
        os.link(path, self.root / "Alias.bin")
        for item in (ref, dict(ref, path="Alias.bin")):
            with self.subTest(path=item["path"]), self.open_set() as retained:
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(item)

    def test_file_larger_than_declared_or_maximum_is_refused(self):
        path, ref = self.put(data=b"")
        with path.open("r+b") as output:
            output.truncate(reader.MAX_ARTIFACT_BYTES + 1)
        with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
            retained.read(ref)
        with self.open_set() as retained, self.assertRaises(reader.RetainedArtifactError):
            retained.read(dict(ref, bytes=reader.MAX_ARTIFACT_BYTES + 1))

    def test_artifact_count_bound_including_zero_bytes(self):
        refs = [self.put("File" + str(i) + ".bin", b"")[1] for i in range(reader.MAX_ARTIFACTS + 1)]
        with self.open_set() as retained:
            for ref in refs[:-1]:
                self.assertEqual(retained.read(ref), b"")
            with self.assertRaises(reader.RetainedArtifactError):
                retained.read(refs[-1])

    def test_aggregate_and_exact_per_artifact_bounds(self):
        data = b"\x00" * reader.MAX_ARTIFACT_BYTES
        refs = [self.put("Large" + str(i) + ".bin", data)[1] for i in range(4)]
        _, extra = self.put("Extra.bin", b"x")
        with self.open_set() as retained:
            for ref in refs:
                self.assertEqual(retained.read(ref), data)
            self.assertEqual(retained._total, reader.MAX_TOTAL_ARTIFACT_BYTES)
            with self.assertRaises(reader.RetainedArtifactError):
                retained.read(extra)

    def test_conflicting_repeated_reference_closes_set(self):
        _, ref = self.put()
        with self.open_set() as retained:
            retained.read(ref)
            with self.assertRaises(reader.RetainedArtifactError):
                retained.read(dict(ref, bytes=0))
            self.assertEqual(retained._handles, [])

    def test_reparse_attribute_native_branch_is_refused(self):
        _, ref = self.put()
        with self.open_set() as retained:
            original = retained._native.dll.GetFileInformationByHandle

            def reparse(handle, output):
                result = original(handle, output)
                info = ctypes.cast(output, ctypes.POINTER(reader._FileInformation)).contents
                info.attributes |= reader.FILE_ATTRIBUTE_REPARSE_POINT
                return result

            with mock.patch.object(retained._native.dll, "GetFileInformationByHandle", side_effect=reparse):
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(ref)

    def test_changed_metadata_on_retained_handle_refuses(self):
        _, ref = self.put()
        with self.open_set() as retained:
            retained.read(ref)
            original = retained._native.snapshot

            def changed(handle, path, directory):
                pin = original(handle, path, directory)
                if not directory:
                    pin["change_100ns"] += 1
                return pin

            with mock.patch.object(retained._native, "snapshot", side_effect=changed):
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.verify()

    def test_verify_rehashes_retained_handle_without_reopen(self):
        _, ref = self.put()
        with self.open_set() as retained:
            retained.read(ref)
            with mock.patch.object(retained._native, "open", side_effect=AssertionError("reopen forbidden")):
                retained.verify()
                with mock.patch.object(retained._native, "chunks", return_value=iter([b"X" * ref["bytes"]])):
                    with self.assertRaises(reader.RetainedArtifactError):
                        retained.verify()

    def test_close_attempts_every_handle_and_retains_failure_for_retry(self):
        _, ref = self.put("Nested/Artifact.bin")
        retained = self.open_set()
        retained.read(ref)
        original, calls = retained._native.close, []
        failed_handle = retained._handles[-1]

        def one_failure(handle):
            calls.append(handle)
            if handle == failed_handle:
                raise reader.RetainedArtifactError("injected close refusal")
            return original(handle)

        count = len(retained._handles)
        try:
            with mock.patch.object(retained._native, "close", side_effect=one_failure):
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.close()
            self.assertEqual(len(calls), count)
            self.assertEqual(retained._handles, [failed_handle])
        finally:
            retained.close()

    def test_unsupported_volume_refuses_constructor(self):
        self._assert_constructor_cleanup("volume")

    def test_constructor_late_snapshot_failure_closes_all_owned_handles(self):
        self._assert_constructor_cleanup("snapshot")

    def _assert_constructor_cleanup(self, failure_point):
        # A directory rename also depends on the separately retained parent
        # fixture namespace. Observe only this constructor's real native opens
        # and successful real closes; do not release any containment guard.
        partial = reader.RetainedArtifactSet.__new__(reader.RetainedArtifactSet)
        opened, closed = [], []
        real_open, real_close = reader._Win32.open, reader._Win32.close
        real_snapshot = reader._Win32.snapshot

        def opening(native, path, directory):
            handle = real_open(native, path, directory)
            opened.append(handle)
            return handle

        def closing(native, handle):
            real_close(native, handle)
            closed.append(handle)

        def snapshot(native, handle, path, directory):
            result = real_snapshot(native, handle, path, directory)
            if path == str(self.root):
                raise reader.RetainedArtifactError("injected final-directory failure")
            return result

        failure = (mock.patch.object(reader._Win32, "volume", side_effect=
                   reader.RetainedArtifactError("unsupported filesystem"))
                   if failure_point == "volume" else
                   mock.patch.object(reader._Win32, "snapshot", new=snapshot))
        with mock.patch.object(reader._Win32, "open", new=opening), \
                mock.patch.object(reader._Win32, "close", new=closing), failure:
            with self.assertRaises(reader.RetainedArtifactError):
                partial.__init__(str(self.root))
        self.assertEqual(len(opened), 1 if failure_point == "volume"
                         else 1 + len(str(self.root)[3:].split("\\")))
        self.assertEqual(closed, list(reversed(opened)))
        self.assertTrue(partial._closed)
        self.assertEqual(partial._handles, [])

    def test_reparse_directory_native_branch_is_refused(self):
        _, ref = self.put("Nested/Artifact.bin")
        with self.open_set() as retained:
            original = retained._native.dll.GetFileInformationByHandle

            def reparse(handle, output):
                result = original(handle, output)
                info = ctypes.cast(output, ctypes.POINTER(reader._FileInformation)).contents
                info.attributes |= reader.FILE_ATTRIBUTE_REPARSE_POINT
                return result

            with mock.patch.object(retained._native.dll, "GetFileInformationByHandle", side_effect=reparse):
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(ref)
            self.assertEqual(retained._handles, [])

    def test_retained_directory_handle_bound(self):
        _, ref = self.put("Nested/Artifact.bin")
        with self.open_set() as retained:
            with mock.patch.object(reader, "MAX_HANDLES", len(retained._handles)):
                with self.assertRaises(reader.RetainedArtifactError):
                    retained.read(ref)
            self.assertEqual(retained._handles, [])


if __name__ == "__main__":
    unittest.main()
