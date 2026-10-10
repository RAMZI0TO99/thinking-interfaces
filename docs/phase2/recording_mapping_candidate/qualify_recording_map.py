"""Run boundary fixtures, then the read-only raw checksum and mapping scope."""
import argparse
import io
import json
from pathlib import Path
import sys
import unittest

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[3]
sys.path.insert(0, str(PKG))
import map_recordings as mapping


def subject(dataset="mmidb", number=1):
    return {"project_subject_number": number, "project_subject_id": f"{dataset}/subject_{number:03d}" if dataset == "mmidb" else f"{dataset}/subject_{number:02d}",
            "project_recording_groups": [{"session": "0", "run": run, "epoch_count": 15} for run in ("04", "08", "12")],
            "declared_raw_file_paths": []}


class BoundaryTests(unittest.TestCase):
    def test_mmidb_filename_relation(self):
        records = mapping.map_subject("mmidb", subject())
        self.assertEqual([Path(item["loader_defined_raw_file_path"]).name for item in records], ["S001R04.edf", "S001R08.edf", "S001R12.edf"])
        self.assertTrue(all(not item["cached_signal_processing_lineage_verified"] for item in records))

    def test_other_subject_identity_rejects(self):
        value = subject()
        value["project_subject_id"] = "mmidb/subject_002"
        with self.assertRaises(ValueError):
            mapping.map_subject("mmidb", value)

    def test_missing_extra_or_wrong_run_rejects(self):
        for run in ("4", "06", "../04"):
            value = subject()
            value["project_recording_groups"][0]["run"] = run
            with self.assertRaises(ValueError):
                mapping.map_subject("mmidb", value)

    def test_duplicate_group_rejects(self):
        value = subject()
        value["project_recording_groups"].append(value["project_recording_groups"][0])
        with self.assertRaises(ValueError):
            mapping.map_subject("mmidb", value)

    def test_wrong_bci_subject_source_rejects(self):
        value = subject("bci_iv_2a")
        value["declared_raw_file_paths"] = ["data/raw/moabb/MNE-bnci-data/A02T.mat", "data/raw/moabb/MNE-bnci-data/A02E.mat"]
        with self.assertRaises(ValueError):
            mapping.map_subject("bci_iv_2a", value)

    def test_empty_or_external_cho_source_rejects(self):
        value = subject("cho2017")
        for paths in ([], ["elsewhere/s01.mat"]):
            value["declared_raw_file_paths"] = paths
            with self.assertRaises(ValueError):
                mapping.map_subject("cho2017", value)

    def test_registry_formats_agree(self):
        sha = "a" * 64
        self.assertEqual(mapping.checksum_registry(f"{sha} S001/S001R04.edf\n".encode(), provider=True), mapping.checksum_registry(f"S001/S001R04.edf {sha}\n".encode(), provider=False))

    def test_duplicate_invalid_and_escape_checksums_reject(self):
        sha = "a" * 64
        for body in (f"{sha} S001/a\n{sha} S001/a\n", f"{sha} ../a\n", "bad S001/a\n", f"{sha} /absolute\n", f"{sha} S001\\a\n", ""):
            with self.assertRaises(ValueError):
                mapping.checksum_registry(body.encode(), provider=True)

    def test_checksum_metadata_bound(self):
        with self.assertRaises(ValueError):
            mapping.checksum_registry(b"x" * (1024**2 + 1), provider=True)


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
        raise ValueError("fresh exact output required")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests)
    names = [case.id().rsplit(".", 1)[-1] for case in suite]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    write_new(output / "tests.json", {"passed": result.wasSuccessful(), "tests_run": result.testsRun, "test_names": names,
                                      "failures": len(result.failures), "errors": len(result.errors), "log": stream.getvalue()})
    if not result.wasSuccessful():
        raise SystemExit(1)
    value = mapping.build_map(ROOT, output)
    if any(name in sys.modules for name in ("numpy", "mne", "moabb", "torch", "scipy")):
        raise ValueError("scientific package imported")
    write_new(output / "recording_map.json", value)
    summary = {key: item for key, item in value.items() if key not in ("recording_groups", "raw_files")}
    summary.update({"passed": True, "tests_passed": result.testsRun, "scientific_libraries_imported": False})
    write_new(output / "mapping_summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("passed", "tests_passed", "datasets", "fresh_raw_files_hashed", "fresh_raw_bytes_hashed", "mmidb_raw_files_matching_publisher_and_mne")}, sort_keys=True))


if __name__ == "__main__":
    main()
