"""P1 bounded physical-map observation; never dependency-completeness authority.

Only Root's separately admitted supervisor calls this module. No CLI, imports of
candidate/package code, discovery imports, compilation, or operational grants.
"""

import hashlib

from ..v1.records import (MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, ROLES,
                         canonical_bytes, closed, defensive_copy, exact_int,
                         exact_string, path_key, require, strict_loads,
                         validate_snapshot, windows_path)
from ..v1.preparation import assemble_proposal, compare_census
from ..q4 import native_reader as nr

SCHEMA = "cho51_lv_physical_recipe_p1"


def _below(path, root):
    return path.startswith(root.rstrip("/") + "/")


def validate_recipe(value):
    """Closed supplied recipe. Pins describe the entire proposed physical map.

    A valid recipe is not proof that transitive imports/resources are complete.
    Scope and exclusions must receive independent coverage review outside here.
    """
    value = defensive_copy(value)
    closed(value, ("schema", "scope_roots", "groups"))
    require(value["schema"] == SCHEMA, "recipe schema")
    scopes = value["scope_roots"]
    require(type(scopes) is list and 1 <= len(scopes) <= 256, "scope roots")
    for root in scopes:
        windows_path(root, absolute=True)
        require(len(root) > 3, "drive-wide scope refused")
    require(len({path_key(p) for p in scopes}) == len(scopes), "scope aliases")
    require(not any(_below(a.lower(), b.lower()) for a in scopes for b in scopes if a != b), "scope overlap")
    groups = value["groups"]
    require(type(groups) is list and 4 <= len(groups) <= 256, "group count")
    labels, paths, roles, footprints = set(), set(), set(), []
    total = 0
    for group in groups:
        closed(group, ("label", "role", "kind", "root", "seeds", "suffixes", "excluded_dirs", "pins"))
        label = exact_string(group["label"], 128)
        require(label and label not in labels, "group label")
        labels.add(label)
        require(type(group["role"]) is str and group["role"] in ROLES, "group role")
        roles.add(group["role"])
        require(group["kind"] in ("file", "tree"), "group kind")
        root = windows_path(group["root"], absolute=True)
        require(any(root == scope or _below(root, scope) for scope in scopes), "outside physical scope")
        footprint = root.lower()
        require(not any(footprint == p or (kind == "tree" and _below(footprint, p))
                        or (group["kind"] == "tree" and _below(p, footprint)) for p, kind in footprints), "group overlap")
        footprints.append((footprint, group["kind"]))
        suffixes, excluded = group["suffixes"], group["excluded_dirs"]
        require(type(suffixes) is list and type(excluded) is list, "recipe lists")
        require(all(type(s) is str for s in suffixes + excluded), "exact string recipe items")
        require(len(set(suffixes)) == len(suffixes) and len(set(excluded)) == len(excluded), "duplicate recipe item")
        if group["kind"] == "file":
            require(not suffixes and not excluded, "exact file has no expansion")
        else:
            require(1 <= len(suffixes) <= 32 and len(excluded) <= 256, "tree recipe bound")
            for suffix in suffixes:
                require(type(suffix) is str and suffix.startswith(".") and 1 < len(suffix) <= 32
                        and suffix.isascii() and all(c.isalnum() or c in "._-" for c in suffix), "literal suffix required")
            for name in excluded:
                windows_path(name)
                require("/" not in name, "one excluded directory name")
        pins = group["pins"]
        require(type(pins) is list and 1 <= len(pins) <= MAX_FILES, "nonempty bounded pins")
        local = set()
        for pin in pins:
            closed(pin, ("path", "bytes", "sha256"))
            path = windows_path(pin["path"], absolute=True)
            require(path == root if group["kind"] == "file" else _below(path, root), "pin outside group")
            require(group["kind"] == "file" or any(path.endswith(s) for s in suffixes), "pin outside suffix expansion")
            require(not any(part in excluded for part in path[len(root):].strip("/").split("/")[:-1]), "excluded pin")
            key = path_key(path)
            require(key not in paths, "duplicate or alias pin")
            paths.add(key)
            local.add(path)
            exact_int(pin["bytes"], upper=MAX_FILE_BYTES)
            require(type(pin["sha256"]) is str and len(pin["sha256"]) == 64
                    and all(c in "0123456789abcdef" for c in pin["sha256"]), "pin digest")
            total += pin["bytes"]
            require(len(paths) <= MAX_FILES and total <= MAX_TOTAL_BYTES, "aggregate physical map bounds")
        require(group["kind"] != "file" or len(pins) == 1, "one exact file pin")
        seeds = group["seeds"]
        require(type(seeds) is list and 1 <= len(seeds) <= len(pins), "seed count")
        require(all(type(p) is str for p in seeds) and len(set(seeds)) == len(seeds)
                and set(seeds) <= local, "seed must be an exact expected member")
    require(roles == ROLES, "all four physical roles required")
    return value


def parse_recipe(raw):
    return validate_recipe(strict_loads(raw))


class PreparationSession:
    """Caller retains this session through report publication, then closes it.

    Exceptions do not release handles automatically: caller's finally must close
    and record cleanup. No report remains fresh after release. `verify` must run
    immediately before and after caller-owned publication under caller guards.
    """
    def __init__(self, recipe, checkpoint):
        self._recipe = validate_recipe(recipe)
        self.reader = nr.RetainedReader(checkpoint)
        self._initial = None
        self._closed = False
        self._attempted = False
        self._failed = False

    @property
    def recipe(self):
        return defensive_copy(self._recipe)

    def _observe(self, group):
        root = group["root"]
        if group["kind"] == "tree":
            census = self.reader._enumerate(root, tuple(group["suffixes"]), tuple(group["excluded_dirs"]))
            require(census[2] == {p["path"] for p in group["pins"]}, "missing/extra physical expansion member")
            directories = census[1] | set(nr._ancestors(root, include=True))
        else:
            root = group["root"].rsplit("/", 1)[0]
            if len(root) == 2:
                root += "/"
            self.reader.retain_directory(root)
            directories = set(nr._ancestors(root, include=True))
            census = None
        files = [self.reader.retain(p["path"], {k: p[k] for k in ("bytes", "sha256")})
                 for p in sorted(group["pins"], key=lambda p: p["path"])]
        if census is not None:
            require(self.reader._enumerate(group["root"], tuple(group["suffixes"]), tuple(group["excluded_dirs"])) == census,
                    "directory membership changed during observation")
        snapshot = validate_snapshot({"schema": "cho51_lv_observed_snapshot_v1", "label": group["label"],
            "role": group["role"], "root": root, "complete_enumeration": True,
            "directories": [self.reader._directories[p][1] for p in sorted(directories)], "files": files})
        return snapshot, census

    def observe(self):
        require(not self._closed and not self._attempted, "once-only observation")
        self._attempted = True
        try:
            self._initial = [self._observe(g) for g in self._recipe["groups"]]
            return self.verify()
        except BaseException:
            self._failed = True
            raise

    def verify(self):
        require(not self._closed and not self._failed and self._initial is not None, "active observation required")
        try:
            return self._verify()
        except BaseException:
            self._failed = True
            raise

    def _verify(self):
        self.reader.verify()
        final = [self._observe(g) for g in self._recipe["groups"]]
        for (before, census), (after, final_census) in zip(self._initial, final):
            require(census == final_census, "initial/final full directory census changed")
            compare_census(before, after)
        pins = [{**pin, "role": group["role"]} for group in self._recipe["groups"] for pin in group["pins"]]
        proposal = assemble_proposal([s for s, _ in self._initial], [s for s, _ in final], pins)
        report = {"schema": "cho51_lv_physical_observation_p1", "status": "PROPOSED_PHYSICAL_MAP_ONLY",
            "recipe_sha256": hashlib.sha256(canonical_bytes(self.recipe)).hexdigest(),
            "recipe": self.recipe, "proposal": proposal,
            "coverage_review_established": False, "actual_result_accepted": False,
            "abi_loader_qualified": False, "launch_authorized": False,
            "scientific_admission": False}
        return defensive_copy(report)

    def close(self):
        self._closed = True
        self.reader.close()

    def __enter__(self):
        require(not self._closed, "session closed")
        return self

    def __exit__(self, *_):
        self.close()
