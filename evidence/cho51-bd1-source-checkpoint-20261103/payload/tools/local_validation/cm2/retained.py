"""Bounded supplied source/code joins; never reads, compiles or imports source."""
from dataclasses import dataclass
import re

from ..hb1 import common as c

CAP = 1_048_576  # Conservative model subset of the future 4 MiB manifest slot.
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*\Z")
PHASES = ("RETAINED_BOOTSTRAP", "SOURCE_LOAD", "OBJECT_CHECK")


def _name(value):
    c.text(value, 256)
    c.require(NAME.fullmatch(value), "module name")
    return value


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    kind: str
    path: object
    size: int
    sha256: object
    parent: object
    package_paths: tuple
    phase: str
    dependencies: tuple
    object_token: str
    loader_token: str
    parent_token: object


@dataclass(frozen=True, slots=True)
class Code:
    slot: int
    module: str
    parent_slot: object
    qualname: str
    token: str
    lines: tuple
    depth: int


@dataclass(frozen=True, slots=True)
class RetainedFacts:
    raw: bytes
    manifest_sha256: str
    modules: tuple
    codes: tuple
    locations: tuple

    @property
    def authenticated(self):
        return False

    @property
    def execution_accepted(self):
        return False

    @property
    def scope(self):
        return "UNAUTHENTICATED_SUPPLIED_RETAINED_MODEL"


def parse_manifest(raw, *, check):
    c.checkpoint(check)
    value = c.strict_json(raw, CAP, check)
    c.closed(value, ("schema", "modules", "codes"))
    c.require(value["schema"] == "cho51_cm2_retained_model_v1", "model manifest schema")
    c.require(c.bounded_bytes(value, CAP, check) == raw, "canonical model bytes")
    rows = value["modules"]
    c.require(type(rows) is list and 1 <= len(rows) <= 4096, "module rows")
    modules, names, paths, tokens = [], set(), set(), set()
    for row in rows:
        c.checkpoint(check)
        c.closed(row, ("name", "kind", "pin", "parent", "package_paths", "phase",
                       "dependencies", "object_token", "loader_token", "parent_token"))
        name = _name(row["name"])
        c.require(name not in names and (not modules or modules[-1].name < name), "ordered unique modules")
        parent = name.rpartition(".")[0] or None
        c.require(row["parent"] == parent and (parent is None or parent in names), "closed parent before child")
        kind = row["kind"]
        c.require(kind in ("source", "source_package", "namespace"), "native/builtin/frozen unavailable")
        phase = row["phase"]
        c.require(phase in PHASES, "permitted supplied phase")
        ppaths = row["package_paths"]
        c.require(type(ppaths) is list and len(ppaths) <= 1, "closed package paths")
        for p in ppaths:
            c.absolute_path(p)
        if kind == "namespace":
            c.require(row["pin"] is None and ppaths == [], "namespace has no file/search fallback")
            path, size, sha = None, 0, None
        else:
            pin = row["pin"]
            c.closed(pin, ("path", "bytes", "sha256"))
            path = c.absolute_path(pin["path"])
            size = c.integer(pin["bytes"], 1, CAP)
            sha = c.sha256_text(pin["sha256"])
            c.require(path.lower() not in paths and path.endswith(".py"), "unique source path")
            paths.add(path.lower())
            if kind == "source_package":
                c.require(path.endswith("/__init__.py") and ppaths == [path.rsplit("/", 1)[0]], "source package origin")
            else:
                c.require(ppaths == [] and not path.endswith("/__init__.py"), "ordinary source shape")
        deps = row["dependencies"]
        c.require(type(deps) is list and len(deps) <= 256, "dependency bound")
        for dep in deps:
            _name(dep)
        c.require(deps == sorted(set(deps)) and name not in deps, "unique ordered dependencies")
        obj, loader = c.sha256_text(row["object_token"]), c.sha256_text(row["loader_token"])
        c.require(obj not in tokens, "unique supplied module token")
        tokens.add(obj)
        pt = row["parent_token"]
        if parent is None:
            c.require(pt is None, "root parent token")
        else:
            c.sha256_text(pt)
            found = next(m for m in modules if m.name == parent)
            c.require(found.kind != "source" and pt == found.object_token, "parent package/token join")
        modules.append(Module(name, kind, path, size, sha, parent, tuple(ppaths), phase, tuple(deps), obj, loader, pt))
        names.add(name)
    for module in modules:
        c.checkpoint(check)
        c.require(set(module.dependencies).issubset(names), "dependency outside manifest")
    # This model implements acyclic supplied graphs only. Runtime INITIALIZING
    # cycle witnesses need a separate adapter, not an inferred permission here.
    by_name = {m.name: m for m in modules}
    states, heights = {}, {}
    for module in modules:
        if states.get(module.name) == 2:
            continue
        states[module.name] = 1
        stack = [(module.name, 0)]
        while stack:
            c.checkpoint(check)
            name, index = stack[-1]
            deps = by_name[name].dependencies
            if index == len(deps):
                height = 1 + max((heights[dep] for dep in deps), default=0)
                c.require(height <= 128, "logical dependency depth")
                heights[name] = height
                states[name] = 2
                stack.pop()
                continue
            dep = deps[index]
            stack[-1] = (name, index + 1)
            c.require(states.get(dep) != 1, "cyclic dependency unavailable")
            if states.get(dep) != 2:
                c.require(len(stack) < 128, "dependency depth")
                states[dep] = 1
                stack.append((dep, 0))
    rows = value["codes"]
    c.require(type(rows) is list and len(rows) <= 4096, "model code row bound")
    codes, slots, code_tokens, locations = [], {}, set(), []
    for row in rows:
        c.checkpoint(check)
        c.closed(row, ("slot", "module", "parent_slot", "qualname", "token", "lines"))
        slot = c.integer(row["slot"], 0, 65535)
        c.require(slot not in slots and (not codes or codes[-1].slot < slot), "ordered unique code slots")
        module = _name(row["module"])
        c.require(module in by_name and by_name[module].kind != "namespace", "code source owner")
        parent = row["parent_slot"]
        if parent is None:
            depth = 1
        else:
            c.integer(parent, 0, 65535)
            c.require(parent in slots and slots[parent].module == module, "code parent before child in same source")
            depth = slots[parent].depth + 1
        c.require(depth <= 128, "code depth")
        qualname = c.text(row["qualname"], 256)
        c.require(qualname and all(32 <= ord(x) <= 126 for x in qualname), "code qualname")
        token = c.sha256_text(row["token"])
        c.require(token not in code_tokens, "unique supplied code token")
        lines = row["lines"]
        c.require(type(lines) is list and 1 <= len(lines) <= 4096 - len(locations), "location budget")
        for line in lines:
            c.integer(line, 1, 2147483647)
        c.require(lines == sorted(set(lines)), "unique ordered locations")
        item = Code(slot, module, parent, qualname, token, tuple(lines), depth)
        codes.append(item); slots[slot] = item; code_tokens.add(token)
        locations.extend((slot, line) for line in lines)
    c.checkpoint(check)
    return RetainedFacts(raw, c.digest(raw, check), tuple(modules), tuple(codes), tuple(locations))


def verify_bytes(manifest_raw, module, raw, *, check):
    """Hash exact supplied bytes against supplied pins; no native retention claim."""
    facts = parse_manifest(manifest_raw, check=check)
    _name(module)
    matches = tuple(m for m in facts.modules if m.name == module)
    c.require(len(matches) == 1 and matches[0].kind != "namespace", "source module required")
    item = matches[0]
    c.require(type(raw) is bytes and len(raw) == item.size, "exact source bytes/length")
    c.require(c.digest(raw, check) == item.sha256, "source bytes mismatch")
    return facts


def reconcile(manifest_raw, before_raw, after_raw, *, check):
    """Supplied snapshots must exactly join manifest tokens, paths and code tokens."""
    facts = parse_manifest(manifest_raw, check=check)
    expected_modules = [[m.name, m.object_token, m.loader_token, m.parent_token, m.path,
                         list(m.package_paths), m.phase] for m in facts.modules]
    expected_codes = [[c.slot, c.token, c.module] for c in facts.codes]
    for raw in (before_raw, after_raw):
        value = c.strict_json(raw, CAP, check)
        c.closed(value, ("schema", "manifest_sha256", "modules", "codes"))
        c.require(value["schema"] == "cho51_cm2_loaded_model_v1"
                  and value["manifest_sha256"] == facts.manifest_sha256, "snapshot manifest join")
        c.require(c.bounded_bytes(value, CAP, check) == raw, "canonical snapshot")
        # Canonical byte comparison also rejects bool/int equality substitutions.
        c.require(c.bounded_bytes(value["modules"], CAP, check) == c.bounded_bytes(expected_modules, CAP, check)
                  and c.bounded_bytes(value["codes"], CAP, check) == c.bounded_bytes(expected_codes, CAP, check),
                  "exact supplied loaded identity")
    c.checkpoint(check)
    return facts


def dispatch(*args, **kwargs):
    raise c.Refusal("operational retained loader unavailable; P disabled")
