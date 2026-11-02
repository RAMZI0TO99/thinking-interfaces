"""Exact supplied collection checks. Does not import, discover or run tests."""

from dataclasses import dataclass

from .baseline import BASE_MODULE_PINS, BASE_ORDERED_DIGEST, BASE_PARTITIONS, HB_IDS, HB_MODULE_PINS
from .common import checkpoint, closed, digest, integer, require, strict_json

LOADER = "unittest.TestLoader.loadTestsFromModule"


def expected_ids():
    return tuple(sorted(tuple(i for _, ids in BASE_PARTITIONS for i in ids) + HB_IDS))


def expected_modules():
    return tuple(sorted(BASE_MODULE_PINS + HB_MODULE_PINS))


@dataclass(frozen=True)
class CheckedCollection:
    report_sha256: str
    ordered_ids_sha256: str
    ids: tuple
    partitions: tuple

    @property
    def evidence_kind(self):
        return "UNAUTHENTICATED"

    @property
    def authenticated(self):
        return False

    @property
    def execution_accepted(self):
        return False

    @property
    def verifier_selection(self):
        parts = dict(self.partitions)
        return tuple(sorted(parts["qd10"] + parts["sc_hash_ram19"]
                            + parts["sc_publisher35"] + parts["hb_new"]))


def verify_collection(raw, *, check):
    """Check complete report against immutable literal IDs/pins, not a caller roster."""
    checkpoint(check)
    original = tuple(sorted(i for _, ids in BASE_PARTITIONS for i in ids))
    require(len(original) == 580 and len(set(original)) == 580, "closed existing 580 roster")
    require(digest(("\n".join(original) + "\n").encode("utf-8"), check) == BASE_ORDERED_DIGEST,
            "original roster digest")
    ids = expected_ids()
    modules = expected_modules()
    require(HB_IDS and len(ids) == len(set(ids)) and len(modules) == len({m[0] for m in modules}),
            "nonempty unique implementation roster")
    require({i.rsplit(".", 2)[0] for i in ids} == {m[0] for m in modules}, "complete module closure")
    value = strict_json(raw, 1_048_576, check)
    closed(value, ("schema", "complete", "modules", "tests"))
    require(value["schema"] == "cho51_hb1_supplied_collection_v1" and value["complete"] is True,
            "complete supplied report required")
    reported_modules = value["modules"]
    require(type(reported_modules) is list and len(reported_modules) == len(modules), "module count")
    for row, (name, size, sha) in zip(reported_modules, modules):
        checkpoint(check)
        closed(row, ("module", "bytes", "sha256", "loader", "load_tests", "partial"))
        require(row["module"] == name and integer(row["bytes"], 1) == size
                and row["sha256"] == sha, "exact source module pin/order")
        require(row["loader"] == LOADER and row["load_tests"] is False
                and row["partial"] is False, "standard loader/no hook/full module")
    reported = value["tests"]
    require(type(reported) is list and len(reported) == len(ids), "complete exact ID count")
    for row, test_id in zip(reported, ids):
        checkpoint(check)
        closed(row, ("id", "module", "class_name", "method_name", "source_module",
                     "source_qualname", "skipped", "deselected", "expected_failure", "xfail"))
        module, class_name, method_name = test_id.rsplit(".", 2)
        require(row["id"] == test_id and row["module"] == module
                and row["class_name"] == class_name and row["method_name"] == method_name
                and row["source_module"] == module
                and row["source_qualname"] == class_name + "." + method_name,
                "exact ID/class/method/source identity; no alias")
        require(all(row[key] is False for key in ("skipped", "deselected", "expected_failure", "xfail")),
                "no skipped/deselected/expected-failure/xfail cases")
    checkpoint(check)
    return CheckedCollection(digest(raw, check),
                             digest(("\n".join(ids) + "\n").encode("utf-8"), check), ids,
                             BASE_PARTITIONS + (("hb_new", HB_IDS),))
