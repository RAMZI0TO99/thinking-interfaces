"""Execute independent binary fixtures, then the fixed local metadata inventory."""
import argparse
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import warnings
import zipfile

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[3]
sys.path.insert(0, str(PKG))
import metadata_reader as reader
import build_inventory as inventory


def fixture(descriptor="<U2", shape=(2,), payload=None, version=(1, 0), header=None, fortran=False):
    if payload is None:
        payload = "0\x001\x00".encode("utf-32-le")
    text = header if header is not None else repr({"descr": descriptor, "fortran_order": fortran, "shape": shape})
    size_bytes = 2 if version == (1, 0) else 4
    prefix_size = 8 + size_bytes
    padding = (-(prefix_size + len(text.encode("utf-8")) + 1)) % 64
    data = (text + " " * padding + "\n").encode("utf-8")
    return b"\x93NUMPY" + bytes(version) + len(data).to_bytes(size_bytes, "little") + data + payload


def archive_fixture(path, *, extras=(), missing=(), trials=(0, 1), sessions=None, runs=None):
    members = {
        "sessions.npy": sessions if sessions is not None else fixture(),
        "runs.npy": runs if runs is not None else fixture(),
        "trial_indices.npy": fixture("<i8", (len(trials),), b"".join(struct.pack("<q", trial) for trial in trials)),
        # Deliberately invalid NPY: opening/decoding unused members would fail.
        "signals.npy": b"unopened-signal-fixture",
        "labels.npy": b"unopened-label-fixture",
        "channel_names.npy": b"unopened-channel-fixture",
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in members.items():
                if name not in missing:
                    archive.writestr(name, data)
            for name, data in extras:
                archive.writestr(name, data)


class MetadataTests(unittest.TestCase):
    def reject(self, data, kind="unicode"):
        with self.assertRaises((ValueError, SyntaxError, TypeError, UnicodeError)):
            reader.decode_npy(data, kind)

    def test_little_endian_unicode(self):
        self.assertEqual(reader.decode_npy(fixture(), "unicode")[0], ["0", "1"])

    def test_big_endian_unicode(self):
        self.assertEqual(reader.decode_npy(fixture(">U2", payload="a\x00b\x00".encode("utf-32-be")), "unicode")[0], ["a", "b"])

    def test_signed_integer_endianness_and_widths(self):
        for descriptor, pack in (("<i8", "<q"), (">i4", ">i"), ("|i1", "b")):
            values = [-1, 12]
            self.assertEqual(reader.decode_npy(fixture(descriptor, payload=b"".join(struct.pack(pack, v) for v in values)), "integer")[0], values)

    def test_versions_two_and_three(self):
        for version in ((2, 0), (3, 0)):
            self.assertEqual(reader.decode_npy(fixture(version=version), "unicode")[0], ["0", "1"])

    def test_fortran_one_dimension(self):
        self.assertEqual(reader.decode_npy(fixture(fortran=True), "unicode")[0], ["0", "1"])

    def test_magic_and_truncated_prefix(self):
        self.reject(b"bad")
        self.reject(b"BADMAG" + fixture()[6:])

    def test_unsupported_version(self):
        self.reject(fixture(version=(4, 0)))

    def test_header_and_member_bounds(self):
        self.reject(b"\x93NUMPY\x01\x00" + (reader.MAX_HEADER + 1).to_bytes(2, "little") + b" " * 5000)
        self.reject(b"x" * (reader.MAX_MEMBER + 1))

    def test_alignment_and_newline(self):
        data = bytearray(fixture())
        data[8:10] = (int.from_bytes(data[8:10], "little") - 1).to_bytes(2, "little")
        self.reject(bytes(data))
        data = bytearray(fixture())
        data[127] = 32
        self.reject(bytes(data))

    def test_duplicate_header_key(self):
        self.reject(fixture(header="{'descr': '<U2', 'descr': '<U2', 'fortran_order': False, 'shape': (2,)}"))

    def test_header_expression_cannot_execute(self):
        self.reject(fixture(header="{'descr': __import__('os').getcwd(), 'fortran_order': False, 'shape': (2,)}"))

    def test_unexpected_header_keys(self):
        self.reject(fixture(header="{'descr': '<U2', 'fortran_order': False, 'shape': (2,), 'extra': 1}"))

    def test_object_and_structured_arrays_reject(self):
        self.reject(fixture("|O"))
        self.reject(fixture(header="{'descr': [('id', '<U2')], 'fortran_order': False, 'shape': (2,)}"))

    def test_dimension_boolean_negative_and_large_counts(self):
        for shape in ((1, 2), (True,), (-1,), (10001,)):
            self.reject(fixture(shape=shape))
        self.reject(fixture(header="{'descr': '<U2', 'fortran_order': 0, 'shape': (2,)}"))

    def test_dtype_kind_and_width(self):
        for descriptor in ("<U129", "<f8", "=U2", "|U2"):
            self.reject(fixture(descriptor))
        self.reject(fixture("|i8"), "integer")
        self.reject(fixture("<i8"))

    def test_payload_length_and_trailing_data(self):
        self.reject(fixture()[:-1])
        self.reject(fixture() + b"x")

    def test_invalid_unicode_and_control_identifiers(self):
        self.reject(fixture(payload=b"\xff" * 16))
        self.reject(fixture(payload="\x00\x00b\x00".encode("utf-32-le")))
        self.reject(fixture(payload="a\nb\x00".encode("utf-32-le")))

    def test_unique_epoch_identity_and_run_scoping(self):
        groups = reader.recording_groups(["0", "0", "1"], ["r", "s", "r"], [1, 1, 1])
        self.assertEqual(len(groups), 3)
        with self.assertRaises(ValueError):
            reader.recording_groups(["0", "0"], ["r", "r"], [1, 1])

    def test_lengths_empty_and_negative_trials(self):
        for args in (([], [], []), (["0"], [], [1]), (["0"], ["r"], [-1])):
            with self.assertRaises(ValueError):
                reader.recording_groups(*args)

    def test_only_three_members_opened(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = root / "subject.npz"
            archive_fixture(path)
            result = reader.inspect_archive(root, path)
            self.assertEqual(result["opened_members"], list(reader.IDENTITY_MEMBERS))
            self.assertEqual(result["epoch_count"], 2)
            self.assertFalse(result["signal_or_label_arrays_decoded"])

    def test_missing_duplicate_and_unexpected_zip_members(self):
        for extra, missing in (((), ("sessions.npy",)), ((('runs.npy', fixture()),), ()), ((('../escape.npy', b'x'),), ())):
            with tempfile.TemporaryDirectory() as name:
                root = Path(name)
                path = root / "subject.npz"
                archive_fixture(path, extras=extra, missing=missing)
                with self.assertRaises(ValueError):
                    reader.inspect_archive(root, path)

    def test_oversized_zip_metadata(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            path = root / "subject.npz"
            archive_fixture(path, sessions=b"x" * (reader.MAX_MEMBER + 1))
            with self.assertRaises(ValueError):
                reader.inspect_archive(root, path)

    def test_workspace_and_raw_path_boundaries(self):
        root = ROOT
        self.assertEqual(inventory.declared_raw_path(root, "data/raw/example.mat"), "data/raw/example.mat")
        for value in ("../escape", "data/raw/../secret", str(root.parent / "other.mat")):
            with self.assertRaises(ValueError):
                inventory.declared_raw_path(root, value)
        with self.assertRaises(ValueError):
            reader.local_file(root, root / "data/../../outside")

    def test_duplicate_sidecar_json_key(self):
        with self.assertRaises(ValueError):
            json.loads('{"subject": 1, "subject": 2}', object_pairs_hook=inventory.unique_object)


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output != PKG / "attempt_001" or not output.is_dir():
        raise ValueError("fresh pinned attempt output required")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MetadataTests)
    test_names = [test.id().rsplit(".", 1)[-1] for test in suite]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {"passed": result.wasSuccessful(), "tests_run": result.testsRun, "test_names": test_names,
              "failures": len(result.failures), "errors": len(result.errors), "log": stream.getvalue(),
              "scientific_libraries_imported": any(name in sys.modules for name in ("numpy", "torch", "scipy"))}
    write_new(output / "tests.json", report)
    if not result.wasSuccessful() or report["scientific_libraries_imported"]:
        raise SystemExit(1)
    value = inventory.build_inventory(ROOT)
    write_new(output / "inventory.json", value)
    summary = {"passed": True, "tests_passed": result.testsRun, "subjects": value["total_subjects"],
               "epochs": value["total_epochs"], "datasets": {key: {name: item for name, item in dataset.items() if name != "subjects"} for key, dataset in value["datasets"].items()},
               "provider_or_checkpoint_overlap_verified": False, "scientific_or_case_admission": False}
    write_new(output / "inventory_summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
