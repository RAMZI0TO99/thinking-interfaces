"""File-only selector expansion and bounded P2 publication; no CLI or admission."""

import hashlib
import os
import stat

from . import native_reader as nr
from ..v1.records import (canonical_bytes, defensive_copy, exact_int, exact_string,
                          require, strict_loads, windows_path)

SCHEMA = "cho51_p3_dependency_recipe_v2"
PAGE_SIZE = 2048
LIMITS = {"files": 25000, "total_bytes": 4294967296,
          "file_bytes": 2147483648, "depth": 32, "hash_chunk_bytes": 65536}
ROOT_KEYS = {"project_root", "site_root", "runtime_root", "git_root",
             "git_user_root", "git_programdata_root", "runtime_library_root",
             "runtime_bin_root", "user_library_root", "nvtools_root", "cuda_root"}
TOP_KEYS = ROOT_KEYS | {"schema", "status", "limits", "selection_semantics",
    "selectors", "required_supplements", "exclusions", "assertions",
    "controlled_environment", "git_static_findings", "required_absent_project_paths"}
SELECTOR_KEYS = {"id", "root", "role", "tree", "trees", "exact", "optional_exact",
    "exact_optional", "optional_root", "recursive_extensions", "recursive_basenames",
    "exclude_trees", "exclude_components", "exclude_basename", "recursive_all_files",
    "recursive_all_files_trees", "optional_nonrecursive_trees", "exact_lists_from",
    "immediate_directory_suffix"}
PATH_LISTS = {"trees", "exact", "optional_exact", "exact_optional", "exclude_trees",
              "recursive_all_files_trees", "optional_nonrecursive_trees"}
TEXT_LISTS = {"recursive_extensions", "recursive_basenames", "exclude_components",
              "exclude_basename", "exact_lists_from"}


def _join(root, relative):
    return windows_path(root.rstrip("/") + "/" + windows_path(relative), absolute=True)


def _list(value):
    require(type(value) is list and len(value) <= 256, "bounded selector list")
    require(all(type(x) is str and 0 < len(x) <= 4096 for x in value), "selector strings")
    require(len({x.lower() for x in value}) == len(value), "selector list aliases")


def validate_recipe(value):
    value = defensive_copy(value)
    require(type(value) is dict and set(value) <= TOP_KEYS, "closed recipe fields")
    require(value.get("schema") == SCHEMA and value.get("limits") == LIMITS,
            "recipe schema and fixed limits")
    require(type(value.get("status")) is str and 0 < len(value["status"]) <= 256,
            "recipe status annotation")
    require(type(value["limits"]) is dict and all(type(v) is int for v in value["limits"].values()),
            "exact limit integers")
    for key in ROOT_KEYS & set(value):
        root = windows_path(value[key], absolute=True)
        require(len(root) > 3, "drive root scope refused")
    assertions = value.get("assertions")
    require(type(assertions) is dict and set(assertions) == {"historical_custody_repaired",
        "loader_abi_qualified", "launch_authorized", "physical_closure_established",
        "scientific_admission"} and all(v is False for v in assertions.values()), "false authorities")
    for field in ("required_supplements", "exclusions", "required_absent_project_paths"):
        if field in value:
            _list(value[field])
    for field in ("selection_semantics", "controlled_environment", "git_static_findings"):
        if field in value:
            require(type(value[field]) is dict and len(value[field]) <= 64
                    and all(type(k) is str and type(v) is str for k, v in value[field].items()),
                    "bounded annotation map")
    for path in value.get("required_absent_project_paths", []):
        windows_path(path)
    selectors = value.get("selectors")
    require(type(selectors) is list and 1 <= len(selectors) <= 256, "selector count")
    ids = set()
    for s in selectors:
        require(type(s) is dict and set(s) <= SELECTOR_KEYS and {"id", "root", "role"} <= set(s),
                "closed selector")
        label = exact_string(s["id"], 128)
        require(label and label not in ids, "unique selector id")
        ids.add(label)
        require(type(s["root"]) is str and s["root"] in ROOT_KEYS and s["root"] in value,
                "known selector root")
        require(exact_string(s["role"], 4096), "selector role")
        require(not ({"optional_exact", "exact_optional"} <= set(s)), "one optional spelling")
        for key in PATH_LISTS | TEXT_LISTS:
            if key in s:
                _list(s[key])
                for item in s[key]:
                    if key in PATH_LISTS:
                        windows_path(item)
                    elif key in {"exclude_components", "exclude_basename", "recursive_basenames"}:
                        windows_path(item)
                        require("/" not in item, "one component")
                    elif key == "recursive_extensions":
                        require(item.startswith(".") and len(item) <= 32 and
                                all(c.isalnum() or c in "._-" for c in item), "literal extension")
                    else:
                        require(item.count(":") == 1, "exact list reference")
                        path, name = item.split(":")
                        windows_path(path)
                        require(name in {"project_seed_paths", "metadata_asset_paths"}, "known exact array")
        if "tree" in s:
            windows_path(s["tree"])
        for key in ("optional_root", "recursive_all_files"):
            if key in s:
                require(type(s[key]) is bool, "exact selector Boolean")
        if "immediate_directory_suffix" in s:
            require(s["immediate_directory_suffix"] == ".dist-info" and
                    s.get("recursive_all_files") is True, "metadata directory selector")
        require(any(k in s for k in ("tree", "trees", "exact", "optional_exact", "exact_optional",
            "recursive_extensions", "recursive_basenames", "recursive_all_files_trees",
            "optional_nonrecursive_trees", "exact_lists_from", "immediate_directory_suffix")), "empty selector")
    return value


def _metadata(path):
    info = os.stat(nr.transport(path), follow_symlinks=False)
    attrs = info.st_file_attributes
    require(not attrs & 0x440 and not stat.S_ISLNK(info.st_mode), "reparse/device refused")
    directory = bool(attrs & 0x10)
    require(directory or (stat.S_ISREG(info.st_mode) and info.st_nlink == 1),
            "regular single-link entry: " + path[:512] + " links=" + str(info.st_nlink))
    return directory


def _absence(reader, path):
    """Retain existing ancestors; only actual FileNotFoundError means absent."""
    chain = nr._ancestors(path, include=True)
    missing = False
    for item in chain:
        reader._check()
        if missing:
            break
        try:
            directory = _metadata(item)
        except FileNotFoundError:
            missing = True
            break
        require(item == path or directory, "non-directory optional ancestor")
        if directory:
            reader.retain_directory(item)
    return missing


def _forbidden(path):
    parts = path.lower().split("/")
    require(not any(parts[i:i+2] in (["data", "raw"], ["data", "processed"],
                ["data", "interim"]) for i in range(len(parts)-1)), "protected data path")
    require(not path.lower().endswith((".pyc", ".pth", ".pt", ".ckpt", ".safetensors",
                ".npy", ".npz", ".edf", ".gdf", ".set", ".h5", ".hdf5", ".bin")),
            "bytecode/startup/weight path")
    require(not path.lower().endswith(".fif") or path.endswith(
        "/mne/data/fsaverage/fsaverage-fiducials.fif"), "only exact fiducial resource")


class Selection:
    def __init__(self, recipe, reader, extras):
        self.recipe, self.reader, self.extras = recipe, reader, extras
        self.files, self.censuses, self.absences = {}, [], []

    def add(self, path, s):
        path = windows_path(path, absolute=True)
        _forbidden(path)
        key = path.lower()
        require(key not in self.files or self.files[key]["path"] == path, "selected case alias")
        row = self.files.setdefault(key, {"path": path, "selectors": [], "roles": []})
        for field, item in (("selectors", s["id"]), ("roles", s["role"])):
            if item not in row[field]:
                row[field].append(item)
                row[field].sort()
        require(len(self.files) <= LIMITS["files"], "selected file cap")

    def exact(self, path, s, optional=False):
        path = windows_path(path, absolute=True)
        _forbidden(path)
        self.reader._check()
        if optional and _absence(self.reader, path):
            self.reader._check()
            self.absences.append(path)
            return
        self.reader._check()
        directory = _metadata(path)
        self.reader._check()
        require(not directory, "exact file required")
        self.add(path, s)

    def tree(self, root, s, all_files=False, recursive=True):
        reader = self.reader
        root = windows_path(root, absolute=True)
        pending, rows, seen, count = [root], [], set(), 0
        base = self.recipe[s["root"]]
        while pending:
            reader._check()
            directory = pending.pop()
            reader.retain_directory(directory)
            require(len(seen) < nr.MAX_DIRECTORIES, "tree directory cap")
            seen.add(directory)
            with os.scandir(nr.transport(directory)) as entries:
                for entry in entries:
                    reader._check()
                    count += 1
                    require(count <= nr.MAX_ENTRIES, "tree entry cap")
                    path = _join(directory, entry.name)
                    directory_entry = _metadata(path)
                    rows.append((path, directory_entry))
                    relative = path[len(base.rstrip("/"))+1:]
                    components = relative.lower().split("/")
                    excluded = (entry.name.lower() in [x.lower() for x in s.get("exclude_basename", [])] or
                        any(c in [x.lower() for x in s.get("exclude_components", [])] for c in components) or
                        any(relative.lower() == t.lower() or relative.lower().startswith(t.lower() + "/")
                            for t in s.get("exclude_trees", [])))
                    if excluded:
                        continue
                    if directory_entry:
                        if recursive:
                            require(len(seen) + len(pending) < nr.MAX_DIRECTORIES, "pending directory cap")
                            pending.append(path)
                    elif all_files or entry.name.lower() in [x.lower() for x in s.get("recursive_basenames", [])] or any(
                            entry.name.lower().endswith(x.lower()) for x in s.get("recursive_extensions", [])):
                        self.add(path, s)
        require(len({p.lower() for p, _ in rows}) == len(rows), "tree case alias")
        require(sum(len(c[2]) for c in self.censuses)+len(rows)<=200000,
                "whole observation census row bound")
        self.censuses.append((s["id"], root, tuple(sorted(rows))))

    def verify(self):
        self.reader.verify()
        other = expand(self.recipe, self.reader, self.extras)
        require(self.files == other.files and self.censuses == other.censuses and
                self.absences == other.absences, "initial/final complete census mismatch")
        return True


def expand(recipe, reader, extra_paths=()):
    require(type(reader) is nr.RetainedReader, "exact retained reader required")
    recipe = validate_recipe(recipe)
    require(type(extra_paths) in (tuple, list) and len(extra_paths) <= LIMITS["files"], "extra path bound")
    selection = Selection(recipe, reader, tuple(extra_paths))
    for s in recipe["selectors"]:
        reader._check()
        root = recipe[s["root"]]
        if s.get("optional_root") and _absence(reader, root):
            selection.absences.append(root)
            continue
        reader.retain_directory(root)
        for key in ("exact", "optional_exact", "exact_optional"):
            for relative in s.get(key, []):
                selection.exact(_join(root, relative), s, key != "exact")
        for ref in s.get("exact_lists_from", []):
            relative, field = ref.split(":")
            path = _join(root, relative)
            selection.exact(path, s)
            reader._check()
            document = strict_loads(reader.read_small(path))
            require(type(document) is dict and field in document, "exact list document")
            values = document[field]
            _list(values)
            for relative in values:
                selection.exact(_join(root, relative), s)
        if "immediate_directory_suffix" in s:
            # First retain full immediate membership (including nonmatches).
            before = len(selection.censuses)
            selection.tree(root, {**s, "recursive_all_files": False}, recursive=False)
            members = selection.censuses[before][2]
            for path, directory in members:
                if directory and path.lower().endswith(s["immediate_directory_suffix"].lower()):
                    selection.tree(path, s, all_files=True)
        else:
            trees = s.get("trees", []) + ([s["tree"]] if "tree" in s else [])
            if not trees and any(k in s for k in ("recursive_extensions", "recursive_basenames")):
                selection.tree(root, s, all_files=s.get("recursive_all_files", False))
            for relative in trees:
                selection.tree(_join(root, relative), s, all_files=s.get("recursive_all_files", False))
        for relative in s.get("recursive_all_files_trees", []):
            selection.tree(_join(root, relative), s, all_files=True)
        for relative in s.get("optional_nonrecursive_trees", []):
            path = _join(root, relative)
            if _absence(reader, path):
                selection.absences.append(path)
            else:
                selection.tree(path, s, all_files=True, recursive=False)
    for relative in recipe.get("required_absent_project_paths", []):
        path = _join(recipe["project_root"], relative)
        require(_absence(reader, path), "required absent path exists")
        selection.absences.append(path)
    for path in extra_paths:
        selection.exact(path, {"id": "supervisor-extra", "role": "reviewed observer/admission/native supplement"})
    selection.files = {row["path"]: row for row in sorted(selection.files.values(), key=lambda x: x["path"])}
    selection.absences = tuple(sorted(set(selection.absences)))
    selection.censuses = tuple(selection.censuses)
    return selection


def validate_pins(pins):
    require(type(pins) is dict and 1 <= len(pins) <= LIMITS["files"], "pin map bound")
    total, keys = 0, set()
    for path, pin in pins.items():
        windows_path(path, absolute=True)
        require(path.lower() not in keys, "pin alias")
        keys.add(path.lower())
        require(type(pin) is dict and set(pin) == {"bytes", "sha256"}, "closed pin")
        total += exact_int(pin["bytes"], upper=LIMITS["file_bytes"])
        require(type(pin["sha256"]) is str and len(pin["sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in pin["sha256"]), "pin digest")
        require(total <= LIMITS["total_bytes"], "pin byte cap")
    return total


def paginate(rows, page_size=PAGE_SIZE):
    """Bound page fanout before slicing; never serialize a combined record."""
    require(type(rows) in (list, tuple) and len(rows) <= nr.MAX_ENTRIES,
            "bounded exact row sequence")
    exact_int(page_size, lower=1, upper=PAGE_SIZE)
    for offset in range(0, len(rows), page_size):
        yield rows[offset:offset + page_size]


class Prepared:
    def __init__(self, selection, outputs):
        self.selection, self.outputs, self.pages, self.index = selection, outputs, [], None

    def verify(self):
        self.selection.verify()
        self.outputs.verify()
        return True


def prepare(reader, recipe, expected_pins, outputs, extra_paths=()):
    require(type(outputs) is nr.RetainedOutputs and outputs.reader is reader, "original retained outputs")
    total = validate_pins(expected_pins)
    selection = expand(recipe, reader, extra_paths)
    require(set(selection.files) == set(expected_pins), "exact selected/pinned union")
    prepared = Prepared(selection, outputs)
    refs = []

    def publish(kind, rows):
        name = "physical-" + kind + "-" + str(len(refs)).zfill(3) + ".json"
        descriptor = outputs.write(name, canonical_bytes({"schema": "cho51_p2_" + kind + "_page_v1", "rows": rows}))
        refs.append({"kind": kind, "path": descriptor["path"], "bytes": descriptor["bytes"],
                     "sha256": descriptor["sha256"], "rows": len(rows)})
        prepared.pages.append(descriptor)

    for paths in paginate(list(selection.files)):
        batch = []
        for path in paths:
            row = selection.files[path]
            descriptor = reader.retain(path, expected_pins[path])
            batch.append({"file": descriptor, "selectors": row["selectors"], "roles": row["roles"]})
        publish("files", batch)
    census_batch=[]
    for selector, root, rows in selection.censuses:
        for path,directory in rows:
            census_batch.append({"selector":selector,"root":root,"path":path,"directory":directory})
            if len(census_batch)==PAGE_SIZE:
                publish("census",census_batch)
                census_batch=[]
    if census_batch: publish("census",census_batch)
    for page in paginate(selection.absences):
        publish("absences", list(page))
    index = {"schema": "cho51_p2_physical_index_v1", "status": "PROVISIONAL_PHYSICAL_MAP_REQUIRES_FINAL_VERIFICATION",
        "recipe_sha256": hashlib.sha256(canonical_bytes(selection.recipe)).hexdigest(),
        "files": len(selection.files), "total_bytes": total, "pages": refs,
        "scope_roots": {k: selection.recipe[k] for k in ROOT_KEYS if k in selection.recipe},
        "final_input_verification_established": False,
        "coverage_review_established": False, "actual_result_accepted": False,
        "abi_loader_qualified": False, "launch_authorized": False, "scientific_admission": False}
    prepared.index = index
    outputs.write("physical-index.json", canonical_bytes(index))
    return prepared






