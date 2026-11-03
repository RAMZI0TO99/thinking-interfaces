"""Exact supplied collection and isolation models. No importing or discovery."""
from dataclasses import dataclass

from ..hb1 import collection as hb
from ..hb1.common import bounded_bytes, checkpoint, closed, digest, integer, require, strict_json
from . import registry

CAP = 1_048_576
LOADER = hb.LOADER
PATCH_SURFACES = (
    "ctypes.create_string_buffer", "ctypes.get_last_error", "ctypes.WinDLL",
    "shutil.disk_usage", "os.lstat", "tools.local_validation.lq19.supervisor.absent",
    "tools.local_validation.lq19.supervisor._MemoryStatus",
    "tools.local_validation.sc1.native_backend.RetainedReader",
)


@dataclass(frozen=True, slots=True)
class CollectionFacts:
    report_sha256: str
    projection_sha256: str
    ordered_ids_sha256: str
    selection_sha256: str
    ids: tuple
    selection: tuple

    @property
    def authenticated(self):
        return False

    @property
    def execution_accepted(self):
        return False

    @property
    def evidence_kind(self):
        return "UNAUTHENTICATED_SUPPLIED_COLLECTION"


def verify_collection(raw, *, check):
    """Full exact successor conservation precedes any projection or selection."""
    checkpoint(check)
    value = strict_json(raw, CAP, check)
    closed(value, ("schema", "complete", "modules", "tests"))
    require(value["schema"] == "cho51_cm1_supplied_collection_v1"
            and value["complete"] is True, "complete CM1 report")
    require(bounded_bytes(value, CAP, check) == raw, "canonical original collection bytes")
    ids, modules = registry.expected_ids(), registry.expected_modules()
    require(len(ids) == 732 and len(set(ids)) == 732 and len(modules) == 30,
            "frozen successor cardinality")
    require(type(value["modules"]) is list and len(value["modules"]) == 30, "module count")
    for row, (name, size, sha) in zip(value["modules"], modules):
        checkpoint(check)
        closed(row, ("module", "bytes", "sha256", "loader", "load_tests", "partial"))
        require(row["module"] == name and integer(row["bytes"], 1) == size
                and row["sha256"] == sha, "module pin/order")
        require(row["loader"] == LOADER and row["load_tests"] is False
                and row["partial"] is False, "loader/full module/no hook")
    require(type(value["tests"]) is list and len(value["tests"]) == 732, "full test count")
    for row, name in zip(value["tests"], ids):
        checkpoint(check)
        closed(row, ("id", "module", "class_name", "method_name", "source_module",
                     "source_qualname", "skipped", "deselected", "expected_failure", "xfail"))
        module, cls, method = name.rsplit(".", 2)
        require(row["id"] == name and row["module"] == module and row["class_name"] == cls
                and row["method_name"] == method and row["source_module"] == module
                and row["source_qualname"] == cls + "." + method, "exact identity/code owner")
        require(all(row[key] is False for key in
                    ("skipped", "deselected", "expected_failure", "xfail")), "no omitted outcome")
    # Never filter before every successor module and test row has been checked.
    original_ids = frozenset(hb.expected_ids())
    original_modules = frozenset(m[0] for m in hb.expected_modules())
    projection = {"schema": "cho51_hb1_supplied_collection_v1", "complete": True,
                  "modules": [r for r in value["modules"] if r["module"] in original_modules],
                  "tests": [r for r in value["tests"] if r["id"] in original_ids]}
    projected_raw = bounded_bytes(projection, CAP, check)
    baseline = hb.verify_collection(projected_raw, check=check)
    require(baseline.ids == hb.expected_ids(), "unchanged baseline projection")
    selected = registry.selected_ids()
    require(len(selected) == 216 and set(selected).issubset(ids), "exact selection")
    return CollectionFacts(digest(raw, check), baseline.report_sha256,
                           registry.roster_digest(check), registry.selection_digest(check), ids, selected)


def verify_namespace(raw, *, check):
    """Only the approved identity bijection; arbitrary renaming needs a successor."""
    value = strict_json(raw, CAP, check)
    closed(value, ("schema", "bindings"))
    require(value["schema"] == "cho51_cm1_namespace_model_v1", "namespace model")
    rows = value["bindings"]
    require(type(rows) is list and len(rows) == 732, "full namespace")
    for row, name in zip(rows, registry.expected_ids()):
        checkpoint(check)
        closed(row, ("source", "target"))
        require(row["source"] == row["target"] == name, "exact identity bijection")
    return ("SUPPLIED_MODEL_ONLY", False)


def verify_bootstrap(raw, *, check):
    """Negative-list schema, not an attestation of actual loaded Python objects."""
    value = strict_json(raw, 65_536, check)
    closed(value, ("schema", "stdlib_shadows", "source_packages_preloaded", "unknown_imports"))
    require(value["schema"] == "cho51_cm1_bootstrap_model_v1", "bootstrap model")
    for key in ("stdlib_shadows", "source_packages_preloaded", "unknown_imports"):
        require(type(value[key]) is list and len(value[key]) == 0, "unreconciled bootstrap entry")
    return ("SUPPLIED_MODEL_ONLY", False)


def _snapshot(raw, check):
    value = strict_json(raw, 65_536, check)
    closed(value, ("schema", "surfaces", "namespace", "importer"))
    require(value["schema"] == "cho51_cm1_restoration_model_v1", "restoration model")
    from ..hb1.common import sha256_text
    namespace, importer = sha256_text(value["namespace"]), sha256_text(value["importer"])
    rows = value["surfaces"]
    require(type(rows) is list and len(rows) == len(PATCH_SURFACES), "exact surfaces")
    frozen = []
    for row, surface in zip(rows, PATCH_SURFACES):
        checkpoint(check)
        closed(row, ("surface", "present", "identity"))
        require(row["surface"] == surface and type(row["present"]) is bool, "surface identity")
        if row["present"]:
            identity = sha256_text(row["identity"])
        else:
            require(row["identity"] is None, "absent object identity")
            identity = None
        if surface.endswith(".absent"):
            require(row["present"] is False, "create=True original absence")
        frozen.append((surface, row["present"], identity))
    return tuple(frozen), namespace, importer


def verify_restoration(before, after, *, check):
    """Compare supplied tokens, including absent attributes; never repair live state."""
    initial, final = _snapshot(before, check), _snapshot(after, check)
    require(initial == final, "restoration mismatch")
    checkpoint(check)
    return ("SUPPLIED_MODEL_ONLY", False)
