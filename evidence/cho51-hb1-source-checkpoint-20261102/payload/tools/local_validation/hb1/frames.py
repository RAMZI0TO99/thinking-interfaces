"""Bounded HB1 supplied-frame checks; no channel or provider authentication.

Every clock and checkpoint is supplied data/caller behavior. These functions do
not observe a live clock, own a transport, establish custody or project SC1 data.
An OK header is a peer's untrusted claim, never a positive provider witness.
"""

from dataclasses import dataclass
import struct

from .common import (
    checkpoint, closed, digest, integer, require, sha256_text, strict_json,
    text, token, uuid_text,
)


HEADER_FIELDS = (
    "schema", "session_id", "provider_epoch", "operation_id",
    "authority_sha256", "request_id", "sequence", "method", "direction",
    "status", "payload_bytes", "payload_sha256", "clock_domain", "deadline_qpc",
)
JOIN_FIELDS = (
    "session_id", "provider_epoch", "operation_id", "authority_sha256",
    "request_id", "sequence", "method", "clock_domain", "deadline_qpc",
)
METHODS = ("claim_operation", "peer_message", "operation_artifacts")
REASONS = (
    "UNAVAILABLE", "AUTHORITY", "IDENTITY", "CLAIM_DUPLICATE", "CLAIM_UNKNOWN",
    "MESSAGE", "CENSUS_UNKNOWN", "ACCOUNTING", "TRANSPORT", "DEADLINE",
    "CUSTODY", "OUTPUT", "SCHEMA",
)
HEADER_CAP = 4088
REQUEST_CAP = 4096
RESPONSE_CAP = 131072
REQUEST_FRAME_CAP = 8192
RESPONSE_FRAME_CAP = 135168


def qpc_text(value):
    """Validate a canonical supplied unsigned64 counter, not an OS reading."""
    text(value, 20)
    require(bool(value) and all("0" <= char <= "9" for char in value),
            "QPC must be unsigned ASCII decimal text")
    require(value == "0" or value[0] != "0", "noncanonical QPC")
    number = int(value)
    require(number <= 18446744073709551615, "QPC exceeds unsigned64")
    return number


@dataclass(frozen=True, slots=True)
class ParsedFrame:
    """Immutable untrusted data; constructor cannot grant host capability."""

    _header_items: tuple
    payload: bytes
    body_kind: str

    @property
    def header(self):
        return dict(self._header_items)

    @property
    def authentication(self):
        return "UNAUTHENTICATED"

    @property
    def authenticated(self):
        return False

    @property
    def provider_schema(self):
        return "UNAVAILABLE"


def _header(header, direction, payload_length, now_qpc, clock_domain):
    closed(header, HEADER_FIELDS)
    require(header["schema"] == "cho51_hb1_exchange_v1", "header schema")
    for name in ("session_id", "operation_id", "request_id"):
        uuid_text(header[name])
    for name in ("provider_epoch", "clock_domain"):
        token(header[name])
    for name in ("authority_sha256", "payload_sha256"):
        sha256_text(header[name])
    integer(header["sequence"], 1, 4096)
    require(type(header["method"]) is str and header["method"] in METHODS,
            "unknown method")
    require(type(header["direction"]) is str and header["direction"] == direction,
            "wrong direction")
    statuses = ("REQUEST",) if direction == "request" else ("OK", "REFUSED")
    require(type(header["status"]) is str and header["status"] in statuses,
            "wrong status for direction")
    integer(header["payload_bytes"], 0, RESPONSE_CAP)
    require(header["payload_bytes"] == payload_length, "header/prefix length mismatch")
    deadline = qpc_text(header["deadline_qpc"])
    now = qpc_text(now_qpc)
    token(clock_domain)
    require(header["clock_domain"] == clock_domain, "supplied clock domain mismatch")
    require(now < deadline, "supplied deadline reached")


def _request_body(header, payload, check):
    body = strict_json(payload, REQUEST_CAP, check)
    method = header["method"]
    if method == "claim_operation":
        closed(body, ("operation_id", "authority_pin"))
        uuid_text(body["operation_id"])
        require(body["operation_id"] == header["operation_id"], "claim operation join")
        pin = body["authority_pin"]
        closed(pin, ("bytes", "sha256"))
        integer(pin["bytes"], 1, 1048576)
        sha256_text(pin["sha256"])
        require(pin["sha256"] == header["authority_sha256"], "claim authority join")
    elif method == "peer_message":
        closed(body, ("reviewer", "message_id"))
        token(body["reviewer"])
        token(body["message_id"])
    else:
        closed(body, ("operation_id",))
        uuid_text(body["operation_id"])
        require(body["operation_id"] == header["operation_id"], "census operation join")
    return "REQUEST_DATA"


def _response_body(header, payload, check):
    if header["status"] == "REFUSED":
        body = strict_json(payload, RESPONSE_CAP, check)
        closed(body, ("reason", "detail"))
        require(type(body["reason"]) is str and body["reason"] in REASONS,
                "refusal reason")
        text(body["detail"], 512)
        return "REFUSED_DATA"
    if header["method"] == "peer_message":
        # Decode only to validate strict UTF-8. Preserve the original payload;
        # no normalization, re-encoding or identity/delegation inference occurs.
        checkpoint(check)
        require(bool(payload), "peer payload unavailable")
        try:
            decoded = payload.decode("utf-8", errors="strict")
        except UnicodeError:
            require(False, "peer payload UTF-8")
        text(decoded, RESPONSE_CAP)
        checkpoint(check)
        return "ORIGINAL_UNAUTHENTICATED_PEER_BYTES"
    # Real provider evidence schemas are intentionally absent. JSON syntax is
    # checked, but these bodies cannot satisfy a provider-specific closed schema.
    body = strict_json(payload, RESPONSE_CAP, check)
    require(type(body) is dict, "claim/census evidence must be a JSON object")
    return "PROVIDER_SCHEMA_UNAVAILABLE"


def _parse(raw, direction, check, now_qpc, clock_domain):
    checkpoint(check)
    require(type(raw) is bytes, "frame must be exact bytes")
    cap = REQUEST_CAP if direction == "request" else RESPONSE_CAP
    total_cap = REQUEST_FRAME_CAP if direction == "request" else RESPONSE_FRAME_CAP
    require(8 <= len(raw) <= total_cap, "frame extent")
    header_length, payload_length = struct.unpack("<II", raw[:8])
    require(1 <= header_length <= HEADER_CAP, "prefix header bound")
    require(payload_length <= cap, "prefix payload bound")
    require(len(raw) == 8 + header_length + payload_length, "frame truncation or tail")
    checkpoint(check)
    header = strict_json(raw[8:8 + header_length], HEADER_CAP, check)
    _header(header, direction, payload_length, now_qpc, clock_domain)
    payload = raw[8 + header_length:]
    require(digest(payload, check) == header["payload_sha256"], "payload digest")
    kind = (_request_body(header, payload, check) if direction == "request"
            else _response_body(header, payload, check))
    checkpoint(check)
    return ParsedFrame(tuple((key, header[key]) for key in HEADER_FIELDS), payload, kind)


def parse_request(raw, *, check, now_qpc, clock_domain):
    """Inspect supplied bytes under a supplied counter/domain; never send them."""
    return _parse(raw, "request", check, now_qpc, clock_domain)


def parse_response(raw, request_raw, *, check, now_qpc, clock_domain):
    """Reparse both exact frames and enforce every supplied request/response join."""
    request = parse_request(request_raw, check=check, now_qpc=now_qpc,
                            clock_domain=clock_domain)
    response = _parse(raw, "response", check, now_qpc, clock_domain)
    left, right = request.header, response.header
    for key in JOIN_FIELDS:
        checkpoint(check)
        require(left[key] == right[key], "response/request join: " + key)
    checkpoint(check)
    return response
