"""Adversarial stdlib-only foundation cases. Source only until separate admission."""

import copy
import hashlib
import io
import unittest

from . import preparation as p
from . import records as r


def identity(number):
    return {"schema": r.IDENTITY_SCHEMA, "volume_serial": "0000000000000001",
            "file_id": format(number, "032x"), "volume_kind": "local_fixed", "filesystem": "NTFS"}


def directory(path, number):
    return {"schema": r.DIRECTORY_SCHEMA, "path": path, "native_identity": identity(number),
            "file_type": "directory", "reparse_point": False}


def file_record(path="C:/source/a.py", number=10, size=3):
    return {"schema": r.FILE_SCHEMA, "path": path, "native_identity": identity(number),
            "file_type": "regular", "reparse_point": False, "link_count": 1,
            "bytes": size, "sha256": hashlib.sha256(b"abc").hexdigest()}


def snapshot(role="source", number=10):
    return {"schema": r.SNAPSHOT_SCHEMA, "label": role, "role": role,
            "root": "C:/" + role, "complete_enumeration": True,
            "directories": [directory("C:/", 1), directory("C:/" + role, number + 1)],
            "files": [file_record("C:/" + role + "/a.py", number)]}


def proposal_inputs():
    snapshots = [snapshot(role, 10 + 10 * index) for index, role in enumerate(sorted(r.ROLES))]
    pins = [{key: item["files"][0][key] for key in ("path", "bytes", "sha256")} | {"role": item["role"]}
            for item in snapshots]
    return snapshots, pins


def node_ids():
    return [module + "::" + name + ("[case" + str(index) + "]" if count > 1 else "")
            for module, name, count in p.EXPECTED_FUNCTIONS for index in range(count)]


class JsonCases(unittest.TestCase):
    def test_finite_round_trip_and_defensive_copy(self):
        source = {"a": [None, True, -1, 1.25, "x"]}
        result = r.defensive_copy(source)
        self.assertEqual(source, result)
        source["a"].append("later")
        self.assertEqual(len(result["a"]), 5)

    def test_duplicate_keys_including_escaped_equivalence(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}', b'{"x":{"a":1,"a":2}}'):
            with self.subTest(raw=raw), self.assertRaises(r.Refusal):
                r.strict_loads(raw)

    def test_nonfinite_and_float_overflow(self):
        for raw in (b"NaN", b"Infinity", b"-Infinity", b"1e400"):
            with self.subTest(raw=raw), self.assertRaises(r.Refusal):
                r.strict_loads(raw)

    def test_signed_integer_boundaries_and_overflow(self):
        self.assertEqual(r.strict_loads(b"9223372036854775807"), r.MAX_INT)
        self.assertEqual(r.strict_loads(b"-9223372036854775808"), -r.MAX_INT - 1)
        for raw in (b"9223372036854775808", b"-9223372036854775809", b"1" * 10_000):
            with self.subTest(length=len(raw)), self.assertRaises(r.Refusal):
                r.strict_loads(raw)

    def test_predecode_depth_and_node_bounds(self):
        self.assertIsInstance(r.strict_loads(b"[" * 32 + b"0" + b"]" * 32), list)
        for raw in (b"[" * 33 + b"0" + b"]" * 33,
                    b"[" + b"0," * r.MAX_NODES + b"0]"):
            with self.subTest(length=len(raw)), self.assertRaises(r.Refusal):
                r.strict_loads(raw)

    def test_strings_bytes_encoding_and_syntax(self):
        for raw in ("{}", bytearray(b"{}"), b"\xff", b"\xef\xbb\xbf{}", b'{"x":}',
                    b'"\\ud800"', b'"' + b"x" * (r.MAX_STRING + 1) + b'"',
                    b" " * (r.MAX_JSON_BYTES + 1)):
            with self.subTest(kind=type(raw)), self.assertRaises(r.Refusal):
                r.strict_loads(raw)

    def test_exact_graph_types_cycles_and_nonfinite(self):
        class Integer(int):
            pass
        cycle = []
        cycle.append(cycle)
        for value in ((1, 2), {1: "x"}, {"x": Integer(1)}, float("inf"), cycle, {"x": object()}):
            with self.subTest(kind=type(value)), self.assertRaises(r.Refusal):
                r.canonical_bytes(value)

    def test_encoded_graph_limit(self):
        # Many individually bounded strings exceed only the aggregate bound.
        with self.assertRaises(r.Refusal):
            r.canonical_bytes(["x" * r.MAX_STRING] * 257)

    def test_child_scheduling_is_bounded_before_queue_growth(self):
        for value in ([0] * r.MAX_NODES, {str(i): 0 for i in range(r.MAX_NODES // 2)}):
            with self.subTest(kind=type(value)), self.assertRaises(r.Refusal):
                r.canonical_bytes(value)


class PathAndSnapshotCases(unittest.TestCase):
    def test_canonical_relative_absolute_and_drive_root(self):
        self.assertEqual(r.windows_path("core/a.py"), "core/a.py")
        self.assertEqual(r.windows_path("C:/", absolute=True), "C:/")
        self.assertEqual(r.windows_path("D:/Aenv/pro3/a.py", absolute=True), "D:/Aenv/pro3/a.py")

    def test_ambiguous_windows_spellings(self):
        for path in ("c:/x", "C:x", "C:\\x", "//server/x", "//?/C:/x", "/x", "C:/a//b",
                     "C:/a/../b", "C:/./b", "C:/a.", "C:/a ", "C:/a:stream", "C:/PROGRA~1/x",
                     "C:/NUL.txt", "C:/CON .txt", "C:/com1 .log", "C:/com1", "C:/LPT9.log", "C:/a*", "C:/é", "C:/a\x00b",
                     "C:/" + "x" * 256, "C:/" + "/".join(["a"] * 33)):
            with self.subTest(path=path), self.assertRaises(r.Refusal):
                r.windows_path(path, absolute=True)
        for path in ("", "C:/x", "../x", "a\\b", "/a"):
            with self.subTest(path=path), self.assertRaises(r.Refusal):
                r.windows_path(path)

    def test_closed_file_descriptor_and_exact_types(self):
        baseline = file_record()
        self.assertEqual(r.validate_file_descriptor(baseline), baseline)
        mutations = (("bytes", True), ("bytes", -1), ("bytes", r.MAX_FILE_BYTES + 1),
                     ("sha256", "A" * 64), ("sha256", 1), ("link_count", True),
                     ("link_count", 2), ("reparse_point", 0), ("reparse_point", True),
                     ("file_type", "symlink"), ("path", "C:/"), ("schema", "future"))
        for key, value in mutations:
            item = copy.deepcopy(baseline)
            item[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(r.Refusal):
                r.validate_file_descriptor(item)
        for item in ({**baseline, "authority": True}, {key: value for key, value in baseline.items() if key != "sha256"}):
            with self.assertRaises(r.Refusal):
                r.validate_file_descriptor(item)

    def test_native_identity_closed_and_supported(self):
        for key, value in (("volume_kind", "network"), ("filesystem", "FAT32"),
                           ("file_id", "0" * 31), ("file_id", "0" * 32),
                           ("volume_serial", "0" * 16), ("volume_serial", 1), ("extra", True)):
            item = file_record()
            item["native_identity"][key] = value
            with self.subTest(key=key), self.assertRaises(r.Refusal):
                r.validate_file_descriptor(item)

    def test_snapshot_requires_complete_ordinary_ancestry(self):
        self.assertEqual(r.validate_snapshot(snapshot()), snapshot())
        for change in ("missing_root", "missing_drive", "reparse_ancestor", "partial", "outside", "unknown_field"):
            item = snapshot()
            if change == "missing_root":
                item["directories"].pop()
            elif change == "missing_drive":
                item["directories"].pop(0)
            elif change == "reparse_ancestor":
                item["directories"][0]["reparse_point"] = True
            elif change == "partial":
                item["complete_enumeration"] = False
            elif change == "outside":
                item["files"][0]["path"] = "C:/other/a.py"
            else:
                item["complete_manifest"] = True
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                r.validate_snapshot(item)

    def test_snapshot_case_native_alias_and_volume_drift(self):
        for change in ("case", "identity", "volume", "filesystem"):
            item = snapshot()
            extra = file_record("C:/source/b.py", 20)
            if change == "case":
                extra["path"] = "C:/source/A.py"
            elif change == "identity":
                extra["native_identity"] = item["files"][0]["native_identity"]
            elif change == "volume":
                extra["native_identity"]["volume_serial"] = "2" * 16
            else:
                extra["native_identity"]["filesystem"] = "ReFS"
            item["files"].append(extra)
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                r.validate_snapshot(item)

    def test_snapshot_total_file_and_depth_limits(self):
        item = snapshot()
        item["files"] = [file_record("C:/source/" + str(i), 100 + i, r.MAX_FILE_BYTES) for i in range(3)]
        with self.assertRaises(r.Refusal):
            r.validate_snapshot(item)
        item["files"] = [file_record()] * (r.MAX_FILES + 1)
        with self.assertRaises(r.Refusal):
            r.validate_snapshot(item)


class CensusAndProposalCases(unittest.TestCase):
    def test_equal_census_order_is_not_membership(self):
        initial = snapshot()
        initial["files"].append(file_record("C:/source/b.py", 20))
        final = copy.deepcopy(initial)
        final["files"].reverse()
        report = p.compare_census(initial, final)
        self.assertTrue(report["supplied_censuses_equal"])
        self.assertFalse(report["complete_manifest"])

    def test_census_added_missing_content_identity_and_directory_drift(self):
        for change in ("added", "missing", "content", "identity", "directory", "context"):
            initial = snapshot()
            final = copy.deepcopy(initial)
            if change == "added":
                final["files"].append(file_record("C:/source/b.py", 20))
            elif change == "missing":
                final["files"].clear()
            elif change == "content":
                final["files"][0]["sha256"] = "1" * 64
            elif change == "identity":
                final["files"][0]["native_identity"] = identity(99)
            elif change == "directory":
                final["directories"][1]["native_identity"] = identity(99)
            else:
                final["label"] = "another"
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.compare_census(initial, final)

    def test_proposal_has_no_positive_authority_and_is_defensive(self):
        snapshots, pins = proposal_inputs()
        report = p.assemble_proposal(snapshots, copy.deepcopy(snapshots), pins)
        self.assertEqual(report["file_count"], 4)
        self.assertEqual(report["total_bytes"], 12)
        for flag in ("complete_manifest", "runtime_qualified", "launch_authorized", "scientific_admission"):
            self.assertIs(report[flag], False)
        report["launch_authorized"] = True
        snapshots[0]["files"][0]["sha256"] = "1" * 64
        self.assertNotEqual(report["files"][0]["descriptor"]["sha256"], "1" * 64)
        snapshots, pins = proposal_inputs()
        self.assertIs(p.assemble_proposal(snapshots, snapshots, pins)["launch_authorized"], False)

    def test_proposal_refuses_missing_roles_snapshots_and_empty_roles(self):
        for change in ("missing_role", "missing_final", "duplicate_label", "empty_role"):
            snapshots, pins = proposal_inputs()
            final = copy.deepcopy(snapshots)
            if change == "missing_role":
                snapshots.pop()
                final.pop()
            elif change == "missing_final":
                final.pop()
            elif change == "duplicate_label":
                snapshots.append(copy.deepcopy(snapshots[0]))
            else:
                snapshots[0]["files"] = []
                final[0]["files"] = []
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.assemble_proposal(snapshots, final, pins)

    def test_required_inputs_missing_changed_duplicate_extra_and_bool(self):
        for change in ("missing", "hash", "role", "duplicate", "extra", "bool"):
            snapshots, pins = proposal_inputs()
            if change == "missing":
                pins[0]["path"] = "C:/source/missing.py"
            elif change == "hash":
                pins[0]["sha256"] = "1" * 64
            elif change == "role":
                pins[0]["role"] = "runtime"
            elif change == "duplicate":
                pins.append(copy.deepcopy(pins[0]))
            elif change == "extra":
                pins[0]["complete_manifest"] = True
            else:
                pins[0]["bytes"] = True
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.assemble_proposal(snapshots, snapshots, pins)

    def test_cross_snapshot_aliases_and_aggregate_limits(self):
        for change in ("file_alias", "directory_alias", "directory_fact", "total"):
            snapshots, pins = proposal_inputs()
            if change == "file_alias":
                snapshots[1]["files"][0]["native_identity"] = identity(10)
            elif change == "directory_alias":
                snapshots[1]["directories"][1]["native_identity"] = identity(11)
            elif change == "directory_fact":
                snapshots[1]["directories"][0]["native_identity"] = identity(99)
            else:
                for item in snapshots:
                    item["files"][0]["bytes"] = r.MAX_FILE_BYTES
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.assemble_proposal(snapshots, snapshots, pins)


class StreamCases(unittest.TestCase):
    def test_chunked_digest_and_eof_probe(self):
        data = b"abc" * 50_000
        class Stream:
            def __init__(self):
                self.source, self.requests = io.BytesIO(data), []
            def read(self, amount):
                self.requests.append(amount)
                return self.source.read(amount)
        stream = Stream()
        checkpoints = []
        result = p.hash_supplied_stream(stream, len(data), lambda: checkpoints.append(True) or True)
        self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())
        self.assertLessEqual(max(stream.requests), 65_536)
        self.assertEqual(stream.requests[-1], 1)
        self.assertEqual(len(checkpoints), 2 * len(stream.requests))

    def test_empty_short_long_and_exact_streams(self):
        self.assertEqual(p.hash_supplied_stream(io.BytesIO(b""), 0, lambda: True)["bytes"], 0)
        self.assertEqual(p.hash_supplied_stream(io.BytesIO(b"a"), 1, lambda: True)["bytes"], 1)
        for data, expected in ((b"a", 2), (b"ab", 1), (b"x", 0)):
            with self.subTest(data=data), self.assertRaises(r.Refusal):
                p.hash_supplied_stream(io.BytesIO(data), expected, lambda: True)

    def test_checkpoint_before_and_after_read_and_exact_true(self):
        class Stream:
            calls = 0
            def read(self, amount):
                self.calls += 1
                return b""
        stream = Stream()
        with self.assertRaises(r.Refusal):
            p.hash_supplied_stream(stream, 0, lambda: 1)
        self.assertEqual(stream.calls, 0)
        checks = iter((True, False))
        with self.assertRaises(r.Refusal):
            p.hash_supplied_stream(stream, 0, lambda: next(checks))
        self.assertEqual(stream.calls, 1)

    def test_stream_contract_types_and_oversized_reads(self):
        class Stream:
            def __init__(self, value):
                self.value = value
            def read(self, amount):
                return self.value
        for value in (bytearray(b"a"), "a", None, b"ab"):
            with self.subTest(kind=type(value)), self.assertRaises(r.Refusal):
                p.hash_supplied_stream(Stream(value), 0, lambda: True)
        for length in (True, -1, r.MAX_FILE_BYTES + 1):
            with self.subTest(length=length), self.assertRaises(r.Refusal):
                p.hash_supplied_stream(io.BytesIO(b""), length, lambda: True)


class RosterCases(unittest.TestCase):
    def test_exact_function_module_tallies_and_order_digest(self):
        nodes = node_ids()
        result = p.verify_collection_tallies(nodes, nodes)
        self.assertEqual((result["case_count"], result["mapping_count"], result["telemetry_count"]), (117, 39, 78))
        self.assertFalse(result["execution_established"])
        self.assertFalse(result["launch_authorized"])
        self.assertEqual(result["ordered_sha256"], hashlib.sha256(r.canonical_bytes(nodes)).hexdigest())

    def test_roster_duplicate_missing_extra_prefix_and_count_only_swap(self):
        for change in ("duplicate", "missing", "extra", "prefix", "swap", "malformed"):
            nodes = node_ids()
            if change == "duplicate":
                nodes[1] = nodes[0]
            elif change == "missing":
                nodes.pop()
            elif change == "extra":
                nodes.append("extra")
            elif change == "prefix":
                nodes[0] += "other"
            elif change == "swap":
                nodes[0] = p.EXPECTED_FUNCTIONS[-1][0] + "::" + p.EXPECTED_FUNCTIONS[-1][1] + "[extra]"
            else:
                nodes[0] = nodes[0][:-1]
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.verify_collection_tallies(nodes)

    def test_order_and_parameter_identity_drift_against_baseline(self):
        baseline = node_ids()
        for change in ("order", "parameter"):
            nodes = baseline.copy()
            if change == "order":
                nodes.reverse()
            else:
                nodes[0] = nodes[0].replace("case0", "changed")
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.verify_collection_tallies(nodes, baseline)

    def test_exact_34_control_values_do_not_prove_execution(self):
        report = p.verify_control_values(dict.fromkeys(p.EXPECTED_CONTROLS, True))
        self.assertEqual(report["control_count"], 34)
        self.assertFalse(report["execution_established"])
        self.assertFalse(report["complete_manifest"])

    def test_control_missing_extra_false_bool_equivalent_and_old_names(self):
        for change in ("missing", "extra", "false", "integer", "old_window"):
            values = dict.fromkeys(p.EXPECTED_CONTROLS, True)
            if change == "missing":
                values.pop("finite_json")
            elif change == "extra":
                values["extra"] = True
            elif change == "false":
                values["finite_json"] = False
            elif change == "integer":
                values["finite_json"] = 1
            else:
                values["full_window"] = values.pop("local_full_window")
            with self.subTest(change=change), self.assertRaises(r.Refusal):
                p.verify_control_values(values)
