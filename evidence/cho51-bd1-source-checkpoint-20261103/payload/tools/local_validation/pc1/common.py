"""Supplied projection primitives. No host or filesystem access."""
import hashlib
import json
import re

REFUSAL_CODES = frozenset(("DUPLICATE", "NUMBER", "INPUT_TYPE", "INPUT_CAP", "ENCODING", "GRAPH", "JSON", "CANONICAL", "FIELDS", "UUID", "INTEGER", "PIN", "EMPTY_PIN", "LITERAL", "ALGEBRA", "EVENTS", "CUTOFF", "PENDING", "FAULT", "BOUND_ACTIVITY", "BOOLEAN", "EOF", "OPERATION", "EXPECTED_BINDING", "BINDING_PIN"))

class Refusal(Exception):
    """A predictable supplied-input refusal, carrying only a fixed code."""
    def __init__(self, code):
        if type(code) is not str or code not in REFUSAL_CODES:
            raise ValueError("invalid refusal code")
        self.code = code
        super().__init__(code)

def require(condition, code):
    if not condition:
        raise Refusal(code)

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE")
        result[key] = value
    return result

def _number(_):
    raise Refusal("NUMBER")

def _integer_token(token):
    require(len(token.lstrip("-")) <= 7, "NUMBER")
    return int(token)

def decode(raw):
    require(type(raw) is bytes, "INPUT_TYPE")
    require(0 < len(raw) <= 8192, "INPUT_CAP")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise Refusal("ENCODING") from None
    # Bound JSON nesting before invoking the standard decoder, including strings.
    depth = 0
    quoted = False
    escaped = False
    for ch in text:
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch in "[{":
            depth += 1
            require(depth <= 24, "GRAPH")
        elif ch in "]}":
            depth -= 1
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_float=_number,
                           parse_constant=_number, parse_int=_integer_token)
    except json.JSONDecodeError:
        raise Refusal("JSON") from None
    stack = [(value, 1)]
    nodes = 0
    while stack:
        item, level = stack.pop()
        nodes += 1
        require(nodes <= 100000 and level <= 24, "GRAPH")
        if type(item) is dict:
            require(len(item) <= 4096, "GRAPH")
            stack.extend((v, level + 1) for v in item.keys())
            stack.extend((v, level + 1) for v in item.values())
        elif type(item) is list:
            require(len(item) <= 4096, "GRAPH")
            stack.extend((v, level + 1) for v in item)
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
    require(canonical == raw, "CANONICAL")
    return value

def fields(value, names):
    require(type(value) is dict and value.keys() == set(names), "FIELDS")

def uuid(value):
    require(type(value) is str and len(value) == 36 and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value) is not None and value != "00000000-0000-0000-0000-000000000000", "UUID")

def integer(value, maximum):
    require(type(value) is int and 0 <= value <= maximum, "INTEGER")

def pin(value, minimum, maximum):
    fields(value, ("bytes", "sha256"))
    integer(value["bytes"], maximum)
    require(value["bytes"] >= minimum, "PIN")
    digest = value["sha256"]
    require(type(digest) is str and len(digest) == 64 and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "PIN")
    require(value["bytes"] != 0 or digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "EMPTY_PIN")

def literal(value, choices):
    require(type(value) is str and value in choices, "LITERAL")

def freeze(value):
    if type(value) is dict:
        return tuple((key, freeze(value[key])) for key in sorted(value))
    if type(value) is list:
        return tuple(freeze(v) for v in value)
    return value

def raw_pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
