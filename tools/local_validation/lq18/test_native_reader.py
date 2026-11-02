"""Q4 qualification source; native fixtures live only below injected FIXTURE_ROOT.

Real NTFS cases and explicitly instrumented fault cases are named separately.
Reparse refusal is injected native-attribute coverage, not an OS-reparse fixture.
No skip substitutes for an unavailable actual hardlink qualification fixture.
"""

import hashlib
import os
from pathlib import Path
import unittest

from ..lp18 import native_reader as nr
from . import native_reader as control_nr

FIXTURE_ROOT = None  # child injects a fresh attempt-owned ordinary directory


class HandoffSharingTests(unittest.TestCase):
    def setUp(self):
        self.directory=FIXTURE_ROOT/('handoff_'+hashlib.sha256(self._testMethodName.encode()).hexdigest()[:8])
        self.directory.mkdir()
        self.operation='11111111-1111-4111-8111-111111111111'
        self.owner=nr.RetainedReader(lambda:True);self.addCleanup(self.owner.close)
        self.writer=nr.RetainedOutputs(self.owner,self.directory);self.addCleanup(self.writer.close)
        self.consumer=control_nr.RetainedReader(lambda:True);self.addCleanup(self.consumer.close)
        self.raw=b'{"handoff_fixture":true}'
        self.descriptor=self.writer.write('api-mapping_'+self.operation+'.json',self.raw)
        self.path=Path(self.descriptor['path'])
        self.pin={key:self.descriptor[key] for key in ('bytes','sha256')}
        native=self.descriptor['native_identity'];self.identity=native['volume_serial']+':'+native['file_id']

    def test_cooperative_read_preserves_unrelated_writer_delete_and_rename_denial(self):
        path=self.consumer.authorize_handoff(self.directory.as_posix(),self.operation,'mapping',self.pin,self.identity)
        self.assertEqual(self.consumer.read_small(path),self.raw)
        with self.assertRaises(OSError):
            with self.path.open('r+b'):pass
        with self.assertRaises(OSError):self.path.unlink()
        with self.assertRaises(OSError):self.path.rename(self.directory/'other.json')
        self.consumer.verify();self.writer.verify()
        self.assertEqual(self.consumer.handoff_capabilities()[0]['read_share'],3)

    def test_ordinary_readers_remain_incompatible_with_live_writer(self):
        with control_nr.RetainedReader(lambda:True) as ordinary:
            with self.assertRaises(OSError):ordinary.read_small(self.path)
        with nr.RetainedReader(lambda:True) as production:
            with self.assertRaises(OSError):production.read_small(self.path)
        self.writer.verify()

    def test_capability_rejects_path_role_hash_and_native_identity_mismatch(self):
        with self.assertRaises(nr.Refusal):
            self.consumer.authorize_handoff(self.directory.as_posix()+'/../outside',self.operation,'mapping',self.pin,self.identity)
        with self.assertRaises(nr.Refusal):
            self.consumer.authorize_handoff(self.directory.as_posix(),self.operation,'other',self.pin,self.identity)
        for change in ('hash','identity'):
            with self.subTest(change=change),control_nr.RetainedReader(lambda:True) as reader:
                pin=dict(self.pin);identity=self.identity
                if change=='hash':pin['sha256']='0'*64
                else:identity='f'*16+':'+'e'*32
                path=reader.authorize_handoff(self.directory.as_posix(),self.operation,'mapping',pin,identity)
                with self.assertRaises(nr.Refusal):reader.read_small(path)
        self.writer.verify()


class NativeReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not isinstance(FIXTURE_ROOT, Path) or not FIXTURE_ROOT.is_absolute():
            raise AssertionError("fresh FIXTURE_ROOT must be injected by admitted child")
        # This retained check also rejects a missing, reparse or aliased root.
        with nr.RetainedReader(lambda: True) as reader:
            reader.retain_directory(FIXTURE_ROOT)

    def setUp(self):
        self.directory = FIXTURE_ROOT / self._testMethodName
        # create-new semantics: stale tests cannot reuse a previous fixture.
        self.directory.mkdir()
        self.reader = nr.RetainedReader(lambda: True)
        self.addCleanup(lambda: self.reader.close())

    def fixture(self, name="input.json", raw=b'{"fixture":true}'):
        path = self.directory / name
        with path.open("xb") as stream:
            self.assertEqual(stream.write(raw), len(raw))
        return path

    @staticmethod
    def pin(raw):
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def test_real_retained_read_identity_and_defensive_descriptors(self):
        raw = b'{"value":1}'
        path = self.fixture(raw=raw)
        descriptor = self.reader.retain(path, self.pin(raw))
        self.assertEqual(descriptor["native_identity"]["filesystem"], "NTFS")
        self.assertEqual(len(descriptor["native_identity"]["file_id"]), 32)
        descriptor["native_identity"]["file_id"] = "0" * 32
        self.assertNotEqual(self.reader.verify()[0]["native_identity"]["file_id"], "0" * 32)
        self.assertEqual(self.reader.read_small(path, self.pin(raw)), raw)

    def test_real_retained_input_blocks_writer_delete_and_rename(self):
        path = self.fixture()
        self.reader.retain(path)
        with self.assertRaises(OSError):
            with path.open("r+b"):
                self.fail("incompatible writer opened")
        with self.assertRaises(OSError):
            path.unlink()
        with self.assertRaises(OSError):
            path.rename(self.directory / "renamed.json")
        self.reader.verify()

    def test_real_existing_writer_refuses_retention(self):
        path = self.fixture()
        with path.open("r+b"):
            with self.assertRaises(OSError):
                self.reader.retain(path)
        self.reader.retain(path)

    def test_real_retained_ancestor_blocks_rename(self):
        path = self.fixture()
        self.reader.retain(path)
        with self.assertRaises(OSError):
            self.directory.rename(FIXTURE_ROOT / (self._testMethodName + "_renamed"))
        self.reader.verify()

    def test_real_same_path_duplicate_pin_conflict(self):
        raw = b"{}"
        path = self.fixture(raw=raw)
        first = self.reader.retain(path, self.pin(raw))
        self.assertEqual(first, self.reader.retain(path, self.pin(raw)))
        self.assertEqual(len(self.reader.verify()), 1)
        with self.assertRaises(nr.Refusal):
            self.reader.retain(path, self.pin(b"[]"))

    def test_real_wrong_pin_closes_failed_file_handle(self):
        path = self.fixture()
        with self.assertRaises(nr.Refusal):
            self.reader.retain(path, self.pin(b"wrong"))
        with path.open("r+b") as stream:
            stream.write(b"{}")
        self.assertEqual(self.reader.verify(), [])

    def test_real_hardlink_refusal_with_proved_fixture(self):
        path = self.fixture()
        alias = self.directory / "hardlink.json"
        try:
            os.link(path, alias)
        except OSError as exc:
            self.fail("hardlink fixture could not be qualified: " + str(exc))
        self.assertEqual(path.stat().st_ino, alias.stat().st_ino)
        self.assertGreaterEqual(path.stat().st_nlink, 2)
        for target in (path, alias):
            with self.assertRaises(nr.Refusal):
                self.reader.retain(target)

    def test_real_tree_hardlink_refusal_outside_selected_suffix(self):
        path = self.fixture()
        alias = self.directory / "unselected-link.json"
        os.link(path, alias)
        self.assertEqual(path.stat().st_ino, alias.stat().st_ino)
        self.assertGreaterEqual(os.stat(path, follow_symlinks=False).st_nlink, 2)
        with self.assertRaisesRegex(nr.Refusal, "enumerated hardlink refused"):
            self.reader.observe_tree(self.directory, "fixture", "metadata", suffixes=(".meta",))

    def test_instrumented_native_reparse_file_and_directory_refusal(self):
        path = self.fixture()
        nested = self.directory / "nested"
        nested.mkdir()
        self.reader.retain_directory(self.directory)
        original_info = self.reader.api.GetFileInformationByHandle

        def information_then_inject_reparse(handle, information):
            result = original_info(handle, information)
            if result:
                information._obj.attributes |= 0x400
            return result

        self.reader.api.GetFileInformationByHandle = information_then_inject_reparse
        try:
            with self.assertRaises(nr.Refusal):
                self.reader.retain(path)
            with self.assertRaises(nr.Refusal):
                self.reader.retain_directory(nested)
        finally:
            self.reader.api.GetFileInformationByHandle = original_info
        with path.open("r+b"):
            pass
        self.assertEqual(self.reader.verify(), [])

    def test_real_path_case_alias_refused(self):
        path = self.fixture(name="MixedCase.json")
        with self.assertRaises(nr.Refusal):
            self.reader.retain(path.with_name("mixedcase.json"))

    def test_real_lexical_aliases_and_depth_refused_before_effect(self):
        root = nr.checked_path(self.directory)
        for tail in ("../input.json", "./input.json", "INPUT~1.JSON", "input.json.",
                     "input.json ", "input.json:stream", "NUL.json", "CONIN$.json"):
            with self.subTest(tail=tail), self.assertRaises(nr.Refusal):
                self.reader.retain(root + "/" + tail)
        with self.assertRaises(nr.Refusal):
            self.reader.retain(root + "/" + "/".join(["d"] * 33) + "/input.json")

    def test_real_missing_file_is_actual_open_error(self):
        with self.assertRaises(FileNotFoundError):
            self.reader.retain(self.directory / "absent.json")
        self.assertEqual(self.reader.verify(), [])

    def test_real_file_and_aggregate_caps_before_reads(self):
        self.reader.close()
        self.reader = nr.RetainedReader(lambda: True, max_file_bytes=3, max_total_bytes=4)
        first = self.fixture("one.json", b"{}")
        second = self.fixture("two.json", b"[] ")
        third = self.fixture("three.json", b"null")
        self.reader.retain(first)
        with self.assertRaises(nr.Refusal):
            self.reader.retain(second)
        with self.assertRaises(nr.Refusal):
            self.reader.retain(third)
        self.assertEqual(len(self.reader.verify()), 1)
        self.reader.close()

    def test_real_file_count_cap_and_small_read_cap(self):
        self.reader.close()
        self.reader = nr.RetainedReader(lambda: True, max_files=1)
        first = self.fixture("one.json", b"{}")
        second = self.fixture("two.json", b"null")
        with self.assertRaises(nr.Refusal):
            self.reader.read_small(second, max_bytes=3)
        self.assertEqual(self.reader.verify(), [])
        self.reader.retain(first)
        with self.assertRaises(nr.Refusal):
            self.reader.retain(second)
        self.reader.close()

    def test_real_bounded_tree_snapshot_and_added_file_refusal(self):
        subdirectory = self.directory / "nested"
        subdirectory.mkdir()
        with (subdirectory / "nested.json").open("xb") as stream:
            stream.write(b"[]")
        self.fixture()
        snapshot = self.reader.observe_tree(self.directory, "fixture", "metadata")
        self.assertEqual(len(snapshot["files"]), 2)
        self.assertTrue(snapshot["complete_enumeration"])
        self.reader.verify()
        self.fixture("added.json", b"{}")
        with self.assertRaises(nr.Refusal):
            self.reader.verify()

    def test_real_tree_missing_excluded_directory_refusal(self):
        omitted = self.directory / "omitted"
        omitted.mkdir()
        self.fixture()
        self.reader.observe_tree(self.directory, "fixture", "metadata", excluded_dirs=("omitted",))
        omitted.rmdir()
        with self.assertRaises(nr.Refusal):
            self.reader.verify()

    def test_real_tree_added_empty_directory_refusal(self):
        self.fixture()
        self.reader.observe_tree(self.directory, "fixture", "metadata")
        (self.directory / "added").mkdir()
        with self.assertRaises(nr.Refusal):
            self.reader.verify()

    def test_instrumented_enumeration_limits_and_recipe_validation(self):
        self.fixture()
        previous = nr.MAX_ENTRIES
        nr.MAX_ENTRIES = 0
        try:
            with self.assertRaises(nr.Refusal):
                self.reader.observe_tree(self.directory, "fixture", "metadata")
        finally:
            nr.MAX_ENTRIES = previous
        with self.assertRaises(nr.Refusal):
            self.reader.observe_tree(self.directory, "fixture", "metadata", suffixes=("*",))
        with self.assertRaises(nr.Refusal):
            self.reader.observe_tree(self.directory, "fixture", "metadata", excluded_dirs=("../escape",))

    def test_instrumented_identity_alias_registration_refused(self):
        descriptor = self.reader.retain(self.fixture())
        with self.assertRaises(nr.Refusal):
            self.reader._register(nr.checked_path(self.directory / "alias.json"), descriptor["native_identity"])

    def test_instrumented_directory_handle_bound_refuses(self):
        previous = nr.MAX_DIRECTORIES
        nr.MAX_DIRECTORIES = 1
        try:
            with self.assertRaises(nr.Refusal):
                self.reader.retain_directory(self.directory)
        finally:
            nr.MAX_DIRECTORIES = previous

    def test_real_output_create_new_readback_and_exclusion(self):
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        raw = b'{"result":true}'
        descriptor = output.write("result.json", raw)
        self.assertEqual({k: descriptor[k] for k in ("bytes", "sha256")}, self.pin(raw))
        self.assertEqual(output.verify(), [descriptor])
        with self.assertRaises(nr.Refusal):
            output.write("result.json", raw)
        path = self.directory / "result.json"
        with self.assertRaises(OSError):
            with path.open("r+b"):
                self.fail("output writer opened")
        with self.assertRaises(OSError):
            path.rename(self.directory / "moved.json")
        output.close()
        self.assertEqual(path.read_bytes(), raw)

    def test_real_output_existing_collision_unchanged(self):
        raw = b'{"existing":true}'
        path = self.fixture("result.json", raw)
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        with self.assertRaises(OSError):
            output.write("result.json", b"{}")
        self.assertEqual(path.read_bytes(), raw)

    def test_instrumented_output_caps_and_bad_names(self):
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        for name in ("../escape.json", "sub/escape.json", "NUL.json", ""):
            with self.subTest(name=name), self.assertRaises(nr.Refusal):
                output.write(name, b"{}")
        with self.assertRaises(nr.Refusal):
            output.write("notbytes.json", bytearray(b"{}"))
        previous = (nr.MAX_OUTPUT_FILE_BYTES, nr.MAX_OUTPUT_BYTES, nr.MAX_OUTPUT_FILES)
        try:
            nr.MAX_OUTPUT_FILE_BYTES, nr.MAX_OUTPUT_BYTES, nr.MAX_OUTPUT_FILES = 3, 4, 2
            output.write("first.json", b"{}")
            with self.assertRaises(nr.Refusal):
                output.write("large.json", b"null")
            with self.assertRaises(nr.Refusal):
                output.write("total.json", b"[] ")
            output.write("second.json", b"[]")
            with self.assertRaises(nr.Refusal):
                output.write("count.json", b"")
        finally:
            nr.MAX_OUTPUT_FILE_BYTES, nr.MAX_OUTPUT_BYTES, nr.MAX_OUTPUT_FILES = previous
        # Actual successor writer reserves failed writes as well as successes.
        with control_nr.RetainedReader(lambda: True) as bounded_reader:
            bounded = control_nr.RetainedOutputs(bounded_reader, self.directory,
                max_files=2, max_total_bytes=3, max_file_bytes=2)
            try:
                bounded.write('control-first.json', b'0')
                with self.assertRaises(control_nr.Refusal):
                    bounded.write('control-too-large.json', b'000')
                original_flush = bounded_reader.api.FlushFileBuffers
                def failed_flush(handle):
                    original_flush(handle)
                    return 0
                bounded_reader.api.FlushFileBuffers = failed_flush
                try:
                    with self.assertRaises(OSError): bounded.write('control-failed.json', b'{}')
                finally:
                    bounded_reader.api.FlushFileBuffers = original_flush
                self.assertEqual((len(bounded._reserved), bounded._reserved_bytes), (2, 3))
                with self.assertRaises(control_nr.Refusal): bounded.write('control-third.json', b'')
                self.assertEqual(len(bounded.verify()), 1)
            finally:
                bounded.close()

    def test_instrumented_tiny_chunks_use_real_native_reads_and_writes(self):
        raw = b'{"payload":"' + b"x" * 100 + b'"}'
        path = self.fixture(raw=raw)
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        previous = nr.CHUNK_BYTES
        nr.CHUNK_BYTES = 7
        try:
            self.assertEqual(self.reader.read_small(path), raw)
            descriptor = output.write("result.json", raw)
            self.assertEqual(output.verify(), [descriptor])
            self.reader.verify()
        finally:
            nr.CHUNK_BYTES = previous

    def test_instrumented_stop_after_native_read_closes_original_file(self):
        path = self.fixture()
        original_read = self.reader.api.ReadFile
        stopped = [False]

        def read_then_stop(*args):
            result = original_read(*args)
            stopped[0] = True
            return result

        self.reader.api.ReadFile = read_then_stop
        self.reader.checkpoint = lambda: not stopped[0]
        try:
            with self.assertRaises(nr.Refusal):
                self.reader.retain(path)
        finally:
            self.reader.api.ReadFile = original_read
            self.reader.checkpoint = lambda: True
        with path.open("r+b"):
            pass
        self.assertEqual(self.reader.verify(), [])

    def test_instrumented_hash_drift_refuses_original_output(self):
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        output.write("result.json", b'{"result":true}')
        original_read = self.reader.api.ReadFile

        def corrupted_read(handle, buffer, amount, read, overlapped):
            result = original_read(handle, buffer, amount, read, overlapped)
            if result and read._obj.value:
                buffer[0] = b"X"
            return result

        self.reader.api.ReadFile = corrupted_read
        try:
            with self.assertRaises(nr.Refusal):
                output.verify()
        finally:
            self.reader.api.ReadFile = original_read
        self.assertEqual(len(output.verify()), 1)

    def test_instrumented_flush_failure_closes_original_output(self):
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        original_flush = self.reader.api.FlushFileBuffers

        def flush_then_report_failure(handle):
            original_flush(handle)
            return 0

        self.reader.api.FlushFileBuffers = flush_then_report_failure
        try:
            with self.assertRaises(OSError):
                output.write("failed.json", b"{}")
        finally:
            self.reader.api.FlushFileBuffers = original_flush
        with (self.directory / "failed.json").open("r+b"):
            pass
        self.assertEqual(output.verify(), [])

    def test_instrumented_checkpoint_exact_true_and_before_create(self):
        output = nr.RetainedOutputs(self.reader, self.directory)
        self.addCleanup(output.close)
        self.reader.checkpoint = lambda: 1
        with self.assertRaises(nr.Refusal):
            output.write("must-not-exist.json", b"{}")
        self.reader.checkpoint = lambda: True
        with self.assertRaises(FileNotFoundError):
            (self.directory / "must-not-exist.json").stat()

    def test_instrumented_close_failure_attempts_every_original_handle(self):
        self.reader.retain(self.fixture())
        original_close = self.reader.api.CloseHandle
        calls = []
        count = len(self.reader._files) + len(self.reader._directories)

        def close_then_report_first_failure(handle):
            calls.append(handle)
            result = original_close(handle)
            return 0 if len(calls) == 1 else result

        self.reader.api.CloseHandle = close_then_report_first_failure
        try:
            with self.assertRaises(nr.Refusal):
                self.reader.close()
            self.assertEqual(len(calls), count)
            self.assertEqual(len(self.reader.cleanup_errors), 1)
        finally:
            self.reader.api.CloseHandle = original_close
            # Explicitly retire the injected diagnostic so unittest cleanup can
            # succeed; the failing close assertion above already records it.
            self.reader.cleanup_errors.clear()

    def test_real_close_releases_input_and_repeated_close_is_safe(self):
        path = self.fixture()
        self.reader.retain(path)
        self.reader.close()
        self.reader.close()
        with path.open("r+b"):
            pass
        with self.assertRaises(nr.Refusal):
            self.reader.retain(path)










