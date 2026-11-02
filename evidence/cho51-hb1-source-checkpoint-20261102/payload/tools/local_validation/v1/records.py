"""Bounded supplied-data records. No filesystem observation or authority grants."""

import json
import math
import re

MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_NODES = 200_000
MAX_DEPTH = 32
MAX_STRING = 32_768
MAX_FILES = 25_000
MAX_FILE_BYTES = 2 * 1024**3
MAX_TOTAL_BYTES = 4 * 1024**3
MAX_INT = 2**63 - 1
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IDENTITY_SCHEMA = "cho51_lv_native_identity_v1"
FILE_SCHEMA = "cho51_lv_file_descriptor_v1"
DIRECTORY_SCHEMA = "cho51_lv_directory_descriptor_v1"
SNAPSHOT_SCHEMA = "cho51_lv_observed_snapshot_v1"
ROLES = frozenset(("source", "runtime", "package", "metadata"))


class Refusal(ValueError):
    """Supplied input cannot satisfy this bounded foundation's checks."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def exact_int(value, lower=0, upper=MAX_INT):
    require(type(value) is int and lower <= value <= upper, "exact bounded integer required")
    return value


def exact_string(value, limit=MAX_STRING):
    require(type(value) is str and len(value) <= limit, "bounded exact string required")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise Refusal("invalid Unicode string") from exc
    require(len(encoded) <= limit, "encoded string limit")
    return value


def closed(value, fields):
    require(type(value) is dict and set(value) == set(fields), "closed object fields required")


def _graph(value):
    """Check exact JSON types, container depth, keys, cycles and node budget."""
    stack = [(value, 0, False)]
    active = set()
    scheduled_nodes = 1
    string_bytes = 0
    while stack:
        item, depth, leaving = stack.pop()
        if leaving:
            active.remove(id(item))
            continue
        kind = type(item)
        if kind is dict or kind is list:
            # Bound all pending children before scheduling any of them. A huge
            # already-supplied list must not allocate a huge validation queue.
            scheduled_nodes += len(item) * (2 if kind is dict else 1)
            require(scheduled_nodes <= MAX_NODES, "JSON node limit")
            depth += 1
            require(depth <= MAX_DEPTH, "JSON depth limit")
            require(id(item) not in active, "cyclic JSON graph")
            active.add(id(item))
            stack.append((item, depth, True))
            if kind is dict:
                for key, child in item.items():
                    exact_string(key)
                    string_bytes += len(key.encode("utf-8"))
                    require(string_bytes <= MAX_JSON_BYTES, "JSON aggregate string byte limit")
                    stack.append((child, depth, False))
            else:
                stack.extend((child, depth, False) for child in item)
        elif kind is str:
            exact_string(item)
            string_bytes += len(item.encode("utf-8"))
            require(string_bytes <= MAX_JSON_BYTES, "JSON aggregate string byte limit")
        elif kind is int:
            exact_int(item, -MAX_INT - 1)
        elif kind is float:
            require(math.isfinite(item), "nonfinite JSON number")
        else:
            require(item is None or kind is bool, "exact JSON scalar required")


def canonical_bytes(value):
    """Return bounded canonical JSON; shared references are copied, cycles refuse."""
    _graph(value)
    chunks = []
    total = 0
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                               separators=(",", ":"))
    for chunk in encoder.iterencode(value):
        encoded = chunk.encode("utf-8")
        total += len(encoded)
        require(total <= MAX_JSON_BYTES, "JSON encoded byte limit")
        chunks.append(encoded)
    return b"".join(chunks)


def _lexical_bounds(text):
    # Bound decoder recursion and token allocation before json.loads. This is a
    # conservative token count; json.loads still supplies the syntax check.
    depth = tokens = 0
    quoted = escaped = token = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
            token = False
            tokens += 1
        elif char in "[{":
            depth += 1
            tokens += 1
            token = False
            require(depth <= MAX_DEPTH, "JSON depth limit")
        elif char in "]}":
            depth -= 1
            token = False
        elif char in ",: \t\r\n":
            token = False
        elif not token:
            tokens += 1
            token = True
        require(tokens <= MAX_NODES, "JSON token limit")


def strict_loads(raw):
    require(type(raw) is bytes and len(raw) <= MAX_JSON_BYTES, "bounded exact JSON bytes required")
    try:
        text = raw.decode("utf-8", "strict")
        _lexical_bounds(text)

        def pairs(items):
            result = {}
            for key, value in items:
                require(key not in result, "duplicate JSON key")
                result[key] = value
            return result

        def integer(text_value):
            require(len(text_value.lstrip("-")) <= 19, "JSON integer overflow")
            return exact_int(int(text_value), -MAX_INT - 1)

        def constant(_):
            raise Refusal("nonfinite JSON constant")

        value = json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                           parse_constant=constant)
        _graph(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Refusal("invalid bounded JSON") from exc


def defensive_copy(value):
    return strict_loads(canonical_bytes(value))


def windows_path(path, absolute=False):
    """Lexical canonical spelling only; never resolves or authenticates a path.

    Conservative v1 supports ASCII local drive paths and slash-only relative
    paths. Unsupported Unicode/8.3/device/UNC spellings refuse rather than being
    normalized into apparent identity. Drive roots, e.g. C:/, are supported.
    """
    exact_string(path, 4096)
    require(path and path.isascii() and "\\" not in path, "canonical ASCII slash path required")
    if absolute:
        require(re.match(r"[A-Z]:/", path) is not None, "uppercase local drive absolute path required")
        tail = path[3:]
    else:
        require(not path.startswith("/") and ":" not in path, "relative path required")
        tail = path
    parts = tail.split("/") if tail else []
    require(absolute or parts, "empty relative path")
    require(len(parts) <= MAX_DEPTH, "path depth limit")
    for part in parts:
        require(len(part) <= 255 and part not in ("", ".", "..") and part == part.strip()
                and not part.endswith("."), "path alias segment")
        require(not any(ord(c) < 32 or ord(c) == 127 or c in '<>:"|?*~' for c in part),
                "unsupported path character")
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        require(stem not in {"CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$"}
                and re.fullmatch(r"(?:COM|LPT)[1-9]", stem) is None, "Windows reserved device")
    return path


def path_key(path):
    return windows_path(path, absolute=True).lower()


def _identity(value):
    closed(value, ("schema", "volume_serial", "file_id", "volume_kind", "filesystem"))
    require(value["schema"] == IDENTITY_SCHEMA, "identity schema")
    require(type(value["volume_serial"]) is str and
            re.fullmatch(r"[0-9a-f]{16}", value["volume_serial"]) is not None, "volume serial")
    require(type(value["file_id"]) is str and
            re.fullmatch(r"[0-9a-f]{32}", value["file_id"]) is not None, "native file id")
    require(value["volume_serial"] != "0" * 16 and value["file_id"] != "0" * 32,
            "ambiguous zero native identity")
    require(value["volume_kind"] == "local_fixed" and value["filesystem"] in ("NTFS", "ReFS"),
            "unsupported volume facts")
    return value["volume_serial"], value["file_id"]


def _descriptor(value, directory=False):
    fields = {"schema", "path", "native_identity", "file_type", "reparse_point"}
    if not directory:
        fields.update(("bytes", "sha256", "link_count"))
    closed(value, fields)
    require(value["schema"] == (DIRECTORY_SCHEMA if directory else FILE_SCHEMA), "descriptor schema")
    windows_path(value["path"], absolute=True)
    require(directory or not value["path"].endswith("/"), "file cannot be drive root")
    _identity(value["native_identity"])
    require(type(value["file_type"]) is str and
            value["file_type"] == ("directory" if directory else "regular"), "file type")
    require(value["reparse_point"] is False, "reparse fact must be exact false")
    if not directory:
        exact_int(value["bytes"], upper=MAX_FILE_BYTES)
        require(type(value["sha256"]) is str and HEX64.fullmatch(value["sha256"]) is not None, "SHA256")
        require(type(value["link_count"]) is int and value["link_count"] == 1, "hardlink fact")


def validate_file_descriptor(value):
    value = defensive_copy(value)
    _descriptor(value)
    return value


def validate_snapshot(value):
    """Validate declared observation facts; no claim that they were measured."""
    value = defensive_copy(value)
    closed(value, ("schema", "label", "role", "root", "complete_enumeration", "directories", "files"))
    require(value["schema"] == SNAPSHOT_SCHEMA, "snapshot schema")
    require(exact_string(value["label"], 128) != "", "snapshot label")
    require(type(value["role"]) is str and value["role"] in ROLES, "snapshot role")
    root = windows_path(value["root"], absolute=True)
    require(value["complete_enumeration"] is True, "partial supplied census")
    require(type(value["files"]) is list and type(value["directories"]) is list, "snapshot lists")
    require(len(value["files"]) <= MAX_FILES and len(value["directories"]) <= MAX_FILES,
            "snapshot count limit")
    seen_paths, seen_ids, directories = {}, set(), {}
    total = 0
    volume = None
    for is_directory, entries in ((True, value["directories"]), (False, value["files"])):
        for entry in entries:
            _descriptor(entry, is_directory)
            path = entry["path"]
            key = path_key(path)
            require(key not in seen_paths, "duplicate/case-colliding path")
            seen_paths[key] = path
            identity = _identity(entry["native_identity"])
            require(identity not in seen_ids, "aliased native identity")
            seen_ids.add(identity)
            volume_facts = (identity[0], entry["native_identity"]["filesystem"])
            if volume is None:
                volume = volume_facts
            require(volume == volume_facts, "mixed volume identity/filesystem")
            # A directory can be an ancestor of root or inside root. Files must
            # be strictly below root, using the exact approved spelling.
            below = path.startswith(root.rstrip("/") + "/")
            ancestor = root.startswith(path.rstrip("/") + "/") or root == path
            require(below or (is_directory and ancestor), "outside snapshot root")
            if is_directory:
                directories[path] = entry
            else:
                total += entry["bytes"]
                require(total <= MAX_TOTAL_BYTES, "snapshot aggregate byte limit")
    require(root in directories, "missing root directory fact")
    # Every ancestor down from the drive root has explicit ordinary-directory
    # facts. These are supplied assertions; retained handles are future work.
    for path in seen_paths.values():
        parent = path.rsplit("/", 1)[0] if path != path[:3] else None
        if parent is not None and len(parent) == 2:
            parent += "/"
        if parent is not None:
            require(parent in directories, "missing ancestor directory fact")
    return value
