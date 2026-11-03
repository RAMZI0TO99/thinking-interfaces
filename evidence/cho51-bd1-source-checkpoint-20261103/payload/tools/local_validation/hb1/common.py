"""Bounded pure data primitives. Checkpoints are supplied, never native evidence."""

import hashlib
import json
import re

from ..v1 import records as _paths


MAX_BYTES = 1_048_576
MAX_DEPTH = 24
MAX_NODES = 100_000
MAX_CONTAINER = 4096
CHUNK = 65_536
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9_./:-]{1,128}\Z")


class Refusal(ValueError):
    """Malformed, incomplete or unavailable supplied evidence; no grant."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def checkpoint(check):
    require(callable(check) and check() is True, "checkpoint must return exact True")


def integer(value, low=0, high=2**63 - 1):
    require(type(value) is int and low <= value <= high, "exact bounded integer required")
    return value


def text(value, max_bytes):
    require(type(value) is str and len(value) <= max_bytes, "bounded exact string required")
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError as error:
        raise Refusal("invalid Unicode") from error
    require(len(encoded) <= max_bytes, "UTF-8 string bound")
    return value


def uuid_text(value):
    text(value, 36)
    require(UUID.fullmatch(value) and value != "00000000-0000-0000-0000-000000000000",
            "canonical nonzero UUID required")
    return value


def token(value):
    text(value, 128)
    require(TOKEN.fullmatch(value), "bounded safe ASCII token required")
    return value


def sha256_text(value):
    text(value, 64)
    require(HEX.fullmatch(value), "SHA256 required")
    return value


def closed(value, fields):
    require(type(value) is dict and len(value) <= MAX_CONTAINER
            and set(value) == set(fields), "closed exact fields required")


def absolute_path(value):
    try:
        _paths.windows_path(value, absolute=True)
    except _paths.Refusal as error:
        raise Refusal(str(error)) from error
    require(not value.endswith("/"), "ordinary file path required")
    return value


def digest(raw, check):
    require(type(raw) is bytes and len(raw) <= MAX_BYTES, "bounded immutable bytes required")
    checkpoint(check)
    result = hashlib.sha256()
    for offset in range(0, len(raw), CHUNK):
        checkpoint(check)
        result.update(raw[offset:offset + CHUNK])
        checkpoint(check)
    checkpoint(check)
    return result.hexdigest()


def _lexical_bounds(value, check):
    containers = []
    quoted = escaped = atom = False
    tokens = 0
    for index, char in enumerate(value):
        if index % 4096 == 0:
            checkpoint(check)
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted, atom = True, False
            tokens += 1
        elif char in "[{":
            containers.append(0)
            require(len(containers) <= MAX_DEPTH, "JSON depth before decode")
            tokens += 1
            atom = False
        elif char in "]}":
            require(containers, "JSON unmatched close")
            containers.pop()
            atom = False
        elif char == ",":
            require(containers, "JSON comma outside container")
            containers[-1] += 1
            require(containers[-1] < MAX_CONTAINER, "JSON container before decode")
            atom = False
        elif char in ": \t\r\n":
            atom = False
        elif not atom:
            tokens += 1
            atom = True
        require(tokens <= MAX_NODES, "JSON nodes before decode")
    require(not containers and not quoted, "incomplete JSON")
    checkpoint(check)


def _graph(value, cap, check):
    active = set()
    nodes = string_bytes = 0

    def visit(item, depth):
        nonlocal nodes, string_bytes
        checkpoint(check)
        nodes += 1
        require(nodes <= MAX_NODES, "JSON node bound")
        kind = type(item)
        if kind is dict or kind is list:
            require(depth < MAX_DEPTH and len(item) <= MAX_CONTAINER,
                    "JSON depth/container bound")
            require(id(item) not in active, "cyclic supplied data")
            active.add(id(item))
            try:
                if kind is dict:
                    for key, child in item.items():
                        require(type(key) is str, "exact string keys required")
                        visit(key, depth + 1)
                        visit(child, depth + 1)
                else:
                    for child in item:
                        visit(child, depth + 1)
            finally:
                active.remove(id(item))
        elif kind is str:
            text(item, cap)
            string_bytes += len(item.encode("utf-8"))
            require(string_bytes <= cap, "aggregate string bytes")
        elif kind is int:
            integer(item, -(2**63))
        else:
            require(item is None or kind is bool, "exact JSON types; no floats")
    visit(value, 0)


def strict_json(raw, cap, check):
    integer(cap, 1, MAX_BYTES)
    require(type(raw) is bytes and 0 < len(raw) <= cap, "bounded immutable JSON bytes")
    checkpoint(check)
    try:
        value = raw.decode("utf-8", "strict")
        _lexical_bounds(value, check)

        def pairs(items):
            require(len(items) <= MAX_CONTAINER, "JSON object bound")
            result = {}
            for key, item in items:
                require(key not in result, "duplicate JSON key")
                result[key] = item
            return result

        def number(item):
            require(len(item.lstrip("-")) <= 19, "integer token bound")
            return integer(int(item), -(2**63))

        def no_float(_):
            raise Refusal("float/nonfinite JSON refused")

        result = json.loads(value, object_pairs_hook=pairs, parse_int=number,
                            parse_float=no_float, parse_constant=no_float)
        checkpoint(check)
        _graph(result, cap, check)
        checkpoint(check)
        return result
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise Refusal("invalid bounded JSON") from error


def bounded_bytes(value, cap, check):
    """Deterministic JSON copy; no filesystem writer or native observation."""
    integer(cap, 1, MAX_BYTES)
    output = bytearray()
    active = set()
    nodes = string_bytes = 0

    def emit(raw):
        checkpoint(check)
        require(len(raw) <= CHUNK and len(output) + len(raw) <= cap, "encoded byte bound")
        output.extend(raw)

    def string(item):
        emit(b'"')
        for offset in range(0, len(item), 4096):
            escaped = json.dumps(item[offset:offset + 4096], ensure_ascii=True)[1:-1]
            emit(escaped.encode("ascii"))
        emit(b'"')

    def encode(item, depth=0):
        nonlocal nodes, string_bytes
        checkpoint(check)
        nodes += 1
        require(nodes <= MAX_NODES, "JSON node bound")
        kind = type(item)
        if kind is dict or kind is list:
            require(depth < MAX_DEPTH and len(item) <= MAX_CONTAINER,
                    "JSON depth/container bound")
            require(id(item) not in active, "cyclic supplied data")
            # Snapshot only this bounded container before calling checkpoints
            # again. Descendants are validated at traversal time, never trusted
            # from a previous pass over a mutable caller graph.
            children = list(item.items()) if kind is dict else list(item)
            require(len(children) <= MAX_CONTAINER, "JSON container bound")
            active.add(id(item))
            try:
                if kind is dict:
                    require(all(type(key) is str for key, _ in children), "string keys")
                    # Bound key comparisons before sorting a caller container.
                    key_bytes = 0
                    for key, _ in children:
                        text(key, cap)
                        key_bytes += len(key.encode("utf-8"))
                        require(key_bytes <= cap, "key byte budget")
                    children.sort(key=lambda pair: pair[0])
                emit(b"{" if kind is dict else b"[")
                for index, child in enumerate(children):
                    if index:
                        emit(b",")
                    if kind is dict:
                        key, child = child
                        encode(key, depth + 1)
                        emit(b":")
                    encode(child, depth + 1)
                emit(b"}" if kind is dict else b"]")
            finally:
                active.remove(id(item))
        elif kind is str:
            text(item, cap)
            string_bytes += len(item.encode("utf-8"))
            require(string_bytes <= cap, "aggregate string bytes")
            string(item)
        elif kind is int:
            integer(item, -(2**63))
            emit(str(item).encode("ascii"))
        elif kind is bool:
            emit(b"true" if item else b"false")
        else:
            require(item is None, "exact JSON types; no floats")
            emit(b"null")
    encode(value)
    emit(b"\n")
    checkpoint(check)
    return bytes(output)
