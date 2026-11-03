"""Exact CM2 supplied roster conservation before the frozen CM1 projection."""
from dataclasses import dataclass
from ..hb1 import common as c
from ..cm1 import collection as cm1, registry as prior
from . import registry


@dataclass(frozen=True, slots=True)
class CollectionFacts:
    report_sha256: str
    cm1_projection_sha256: str
    hb1_projection_sha256: str
    roster_sha256: str
    selection_sha256: str
    ids: tuple
    selection: tuple

    @property
    def authenticated(self): return False

    @property
    def execution_accepted(self): return False


def verify_collection(raw, *, check):
    value = c.strict_json(raw, 1_048_576, check)
    c.closed(value, ("schema", "complete", "modules", "tests"))
    c.require(value["schema"] == "cho51_cm2_supplied_collection_v1"
              and value["complete"] is True, "complete successor report")
    c.require(c.bounded_bytes(value, 1_048_576, check) == raw, "canonical collection")
    ids, modules = registry.expected_ids(), registry.expected_modules()
    c.require(len(ids) == len(set(ids)) == 764 and len(modules) == 32, "literal roster")
    c.require(type(value["modules"]) is list and len(value["modules"]) == 32, "module count")
    for row, (name, size, sha) in zip(value["modules"], modules):
        c.checkpoint(check)
        c.closed(row, ("module", "bytes", "sha256", "loader", "load_tests", "partial"))
        c.require(row["module"] == name and c.integer(row["bytes"], 1) == size
                  and row["sha256"] == sha, "exact module pin/order")
        c.require(row["loader"] == cm1.LOADER and row["load_tests"] is False
                  and row["partial"] is False, "loader/module contract")
    c.require(type(value["tests"]) is list and len(value["tests"]) == 764, "full case count")
    for row, name in zip(value["tests"], ids):
        c.checkpoint(check)
        c.closed(row, ("id", "module", "class_name", "method_name", "source_module",
                       "source_qualname", "skipped", "deselected", "expected_failure", "xfail"))
        module, cls, method = name.rsplit(".", 2)
        c.require(row["id"] == name and row["module"] == module and row["class_name"] == cls
                  and row["method_name"] == method and row["source_module"] == module
                  and row["source_qualname"] == cls + "." + method, "exact case/code owner")
        c.require(all(row[k] is False for k in ("skipped", "deselected", "expected_failure", "xfail")),
                  "eligibility flags")
    original = frozenset(prior.expected_ids())
    mod_names = frozenset(m[0] for m in prior.expected_modules())
    projection = dict(schema="cho51_cm1_supplied_collection_v1", complete=True,
                      modules=[r for r in value["modules"] if r["module"] in mod_names],
                      tests=[r for r in value["tests"] if r["id"] in original])
    projected = c.bounded_bytes(projection, 1_048_576, check)
    checked = cm1.verify_collection(projected, check=check)
    selected = registry.selected_ids()
    c.require(len(selected) == 248 and set(selected).issubset(ids), "exact successor selection")
    return CollectionFacts(c.digest(raw, check), checked.report_sha256,
                           checked.projection_sha256, registry.roster_digest(check),
                           registry.selection_digest(check), ids, selected)
