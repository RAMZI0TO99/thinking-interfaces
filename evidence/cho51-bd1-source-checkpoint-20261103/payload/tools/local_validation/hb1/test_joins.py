"""Model parent/fixture accounting cases; no filesystem or provider fixtures."""
import unittest

from .common import Refusal, bounded_bytes, digest
from .joins import (HB_SCENARIO_PIN, PARTITIONS, ROLE_CAPS, parse_join, role_path,
                    root_path, verify_supplied_census)

PARENT = "11111111-1111-1111-1111-111111111111"
METADATA = "22222222-2222-2222-2222-222222222222"
FIXTURE = "33333333-3333-3333-3333-333333333333"


def yes():
    return True


def encoded(value):
    return bounded_bytes(value, 1_048_576, yes)


def ordinary(partition="caller", name="output.bin", size=100):
    return {"path": root_path(PARENT) + "/" + partition + "/" + name,
            "partition": partition, "reserved_bytes": size,
            "publisher_role": None, "transaction_id": PARENT}


def joined(native=False):
    rows = [{"path": role_path(PARENT, METADATA, role), "partition": "closeout",
             "reserved_bytes": size, "publisher_role": role, "transaction_id": METADATA}
            for role, size in ROLE_CAPS]
    value = {"schema": "cho51_hb1_parent_join_v1", "parent_operation_id": PARENT,
             "metadata_transaction_id": METADATA, "stage": "COMPONENT_MODEL",
             "authority_sha256": "a" * 64, "producer_domain_sha256": "b" * 64,
             "partitions": {n: {"files": f, "bytes": b} for n, f, b in PARTITIONS},
             "fixture_publication": None, "reservations": rows}
    if native:
        value["stage"] = "COMPONENT_NATIVE"
        roles = {role: {"path": role_path(PARENT, FIXTURE, role, fixture=True),
                        "reserved_bytes": size} for role, size in ROLE_CAPS}
        value["fixture_publication"] = {"transaction_id": FIXTURE,
                                         "scenario_id": "HB12", "roles": roles}
        rows.extend({"path": roles[role]["path"], "partition": "fixtures", "reserved_bytes": size,
                     "publisher_role": role, "transaction_id": FIXTURE} for role, size in ROLE_CAPS)
    return value


def census(value):
    raw = encoded(value)
    result = {"schema": "cho51_hb1_supplied_census_v1", "parent_operation_id": PARENT,
              "join_sha256": digest(raw, yes), "authority_sha256": "a" * 64,
              "producer_domain_sha256": "b" * 64,
              "barrier": {"kind": "SUPPLIED_ONLY", "sequence": 1,
                          "producers_closed": True, "lost_events": 0},
              "entries": [{"path": r["path"], "state": "RESERVED_ABSENT", "actual_bytes": 0,
                           "native_identity": None, "sha256": None, "links": None, "reparse": None}
                          for r in value["reservations"]]}
    return raw, result


def present(row, number=1):
    row.update(state="PARTIAL", actual_bytes=0,
               native_identity={"volume": "0" * 15 + "1", "file_id": format(number, "032x")},
               sha256="c" * 64, links=1, reparse=False)


class ParentJoinTests(unittest.TestCase):
    def test_main_slots_full_charges_and_untrusted_result(self):
        result = parse_join(encoded(joined()), check=yes)
        self.assertEqual(dict((n, (f, b)) for n, f, b in result.charges)["closeout"], (16, 3293184))
        self.assertFalse(result.authenticated)
        self.assertEqual(result.evidence_kind, "UNAUTHENTICATED")

    def test_p_and_unknown_stage_refuse(self):
        for stage in ("P", "UNKNOWN"):
            value = joined(); value["stage"] = stage
            with self.subTest(stage=stage), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_uuid_alias_and_extra_fields_refuse(self):
        for change in ({"metadata_transaction_id": PARENT}, {"approval": True}):
            value = joined(); value.update(change)
            with self.subTest(change=change), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_partition_caps_are_not_caller_options(self):
        for key in ("files", "bytes"):
            value = joined(); value["partitions"]["caller"][key] += 1
            with self.subTest(key=key), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_missing_or_duplicate_role_refuses(self):
        for mutate in (lambda rows: rows.pop(), lambda rows: rows.append(dict(rows[0]))):
            value = joined(); mutate(value["reservations"])
            with self.subTest(mutate=mutate), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_main_role_cap_path_and_owner_exact(self):
        for field, replacement in (("reserved_bytes", 1), ("path", ordinary()["path"]),
                                    ("transaction_id", PARENT), ("publisher_role", None)):
            value = joined(); value["reservations"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_case_alias_and_ancestor_collision_refuse(self):
        for name in ("A.bin", "a.bin/child"):
            value = joined(); value["reservations"] += [ordinary(name="a.bin"), ordinary(name=name)]
            with self.subTest(name=name), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_path_escape_and_reserved_namespace_refuse(self):
        for name in ("../escape", "x:stream", "NUL", "publication_other/output"):
            value = joined(); value["reservations"].append(ordinary(name=name))
            with self.subTest(name=name), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_foreign_root_and_partition_refuse(self):
        for change in ({"partition": "fixtures"}, {"path": "D:/elsewhere/output"}):
            row = ordinary(); row.update(change)
            value = joined(); value["reservations"].append(row)
            with self.subTest(change=change), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_per_file_exact_integer_cap(self):
        for size in (True, 0, 8388609):
            value = joined(); value["reservations"].append(ordinary(size=size))
            with self.subTest(size=size), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_partition_file_and_byte_overflow_refuse(self):
        for rows in ([ordinary(name=str(n)) for n in range(41)],
                     [ordinary(name=str(n), size=8388608) for n in range(3)]):
            value = joined(); value["reservations"] += rows
            with self.subTest(count=len(rows)), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_typed_native_fixture_all_sixteen_roles(self):
        result = parse_join(encoded(joined(True)), check=yes)
        self.assertEqual(len(result.reservations), 32)
        self.assertEqual(result.fixture_transaction_id, FIXTURE)
        self.assertEqual(result.charges[0], ("fixtures", 16, 3293184))

    def test_inner_fixture_forbidden_in_model_and_q(self):
        for stage in ("COMPONENT_MODEL", "Q"):
            value = joined(True); value["stage"] = stage
            with self.subTest(stage=stage), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_inner_uuid_and_scenario_refuse(self):
        for field, replacement in (("transaction_id", METADATA), ("scenario_id", "HB01"),
                                    ("scenario_id", "O01")):
            value = joined(True); value["fixture_publication"][field] = replacement
            with self.subTest(field=field, replacement=replacement), self.assertRaises(Refusal):
                parse_join(encoded(value), check=yes)

    def test_inner_missing_role_and_mismatched_charge_refuse(self):
        value = joined(True); value["fixture_publication"]["roles"].pop("closeout")
        with self.assertRaises(Refusal):
            parse_join(encoded(value), check=yes)
        value = joined(True); value["reservations"][-1]["reserved_bytes"] -= 1
        with self.assertRaises(Refusal):
            parse_join(encoded(value), check=yes)

    def test_inner_auxiliary_boundary_and_overflow(self):
        value = joined(True)
        value["reservations"] += [ordinary("fixtures", str(n), 56320) for n in range(16)]
        result = parse_join(encoded(value), check=yes)
        self.assertEqual(result.charges[0], ("fixtures", 32, 4194304))
        value["reservations"][-1]["reserved_bytes"] += 1
        with self.assertRaises(Refusal):
            parse_join(encoded(value), check=yes)

    def test_inner_cross_ledger_role_refuses(self):
        value = joined(True); value["reservations"][-1]["partition"] = "closeout"
        with self.assertRaises(Refusal):
            parse_join(encoded(value), check=yes)

    def test_complete_parent_before_views_and_no_promotion(self):
        value = joined(True); value["reservations"].append(ordinary())
        raw, report = census(value)
        result = verify_supplied_census(raw, encoded(report), check=yes)
        self.assertEqual((len(result.metadata_paths), len(result.fixture_paths), len(result.other_paths)), (16, 16, 1))
        self.assertEqual(result.fixture_purpose, "NATIVE_FIXTURE")
        self.assertEqual(result.fixture_scenario_pin, HB_SCENARIO_PIN)
        self.assertEqual(result.evidence_kind, "MODEL_ONLY")
        self.assertFalse(result.authenticated)
        self.assertEqual(len(result.absent_paths), 33)

    def test_partial_failed_and_unused_still_charged(self):
        raw, report = census(joined())
        present(report["entries"][0]); report["entries"][1]["state"] = "FAILED_ABSENT"
        result = verify_supplied_census(raw, encoded(report), check=yes)
        self.assertEqual(len(result.present_paths), 1)
        self.assertEqual(result.charges[-1], ("closeout", 16, 3293184))

    def test_missing_extra_and_duplicate_census_paths_refuse(self):
        for action in ("missing", "extra", "duplicate", "copy"):
            raw, report = census(joined())
            if action == "missing": report["entries"].pop()
            if action == "extra": report["entries"].append(dict(report["entries"][0]))
            if action == "duplicate": report["entries"][-1] = dict(report["entries"][0])
            if action == "copy": report["entries"][-1]["path"] = ordinary()["path"]
            with self.subTest(action=action), self.assertRaises(Refusal):
                verify_supplied_census(raw, encoded(report), check=yes)

    def test_census_join_and_barrier_are_exact(self):
        for key in ("parent_operation_id", "join_sha256", "authority_sha256", "producer_domain_sha256"):
            raw, report = census(joined()); report[key] = "wrong"
            with self.subTest(key=key), self.assertRaises(Refusal):
                verify_supplied_census(raw, encoded(report), check=yes)
        for key, replacement in (("lost_events", 1), ("producers_closed", 1),
                                  ("kind", "AUTHENTICATED"), ("sequence", True)):
            raw, report = census(joined()); report["barrier"][key] = replacement
            with self.subTest(key=key), self.assertRaises(Refusal):
                verify_supplied_census(raw, encoded(report), check=yes)

    def test_physical_alias_reparse_and_overflow_refuse(self):
        for action in ("identity", "zero_volume", "zero_file", "links", "reparse", "bytes"):
            raw, report = census(joined()); first, second = report["entries"][:2]
            present(first); present(second, 2)
            if action == "identity": second["native_identity"] = first["native_identity"]
            if action == "zero_volume": first["native_identity"]["volume"] = "0" * 16
            if action == "zero_file": first["native_identity"]["file_id"] = "0" * 32
            if action == "links": first["links"] = 2
            if action == "reparse": first["reparse"] = True
            if action == "bytes": first["actual_bytes"] = 1048577
            with self.subTest(action=action), self.assertRaises(Refusal):
                verify_supplied_census(raw, encoded(report), check=yes)

    def test_absence_cannot_hide_created_bytes_or_identity(self):
        for field, replacement in (("actual_bytes", 1), ("native_identity", {}), ("sha256", "c" * 64)):
            raw, report = census(joined()); report["entries"][0][field] = replacement
            with self.subTest(field=field), self.assertRaises(Refusal):
                verify_supplied_census(raw, encoded(report), check=yes)

    def test_census_reparses_bytes_not_forged_map(self):
        value = joined(); raw, report = census(value)
        with self.assertRaises(Refusal):
            verify_supplied_census(parse_join(raw, check=yes), encoded(report), check=yes)

    def test_byte_caps_and_guard_refuse(self):
        with self.assertRaises(Refusal):
            parse_join(b" " * 65537, check=yes)
        raw, report = census(joined())
        with self.assertRaises(Refusal):
            verify_supplied_census(raw, b" " * 131073, check=yes)
        with self.assertRaises(Refusal):
            parse_join(raw, check=lambda: False)
