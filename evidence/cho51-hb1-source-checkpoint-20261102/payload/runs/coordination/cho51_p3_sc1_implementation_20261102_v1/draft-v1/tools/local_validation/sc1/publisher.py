"""Closed fixed-slot metadata publisher. Unintegrated and unqualified source.

The supplied host is a trust boundary, not a JSON approval flag. A future
reviewed host must authenticate peer messages, atomically consume operation
identities across sessions, pin loaded code/runtime, and supply live guards.
This module has no CLI and never authorizes Q, P or scientific execution.
"""

import copy
import hashlib
import json
import re
import uuid


ROOT = "D:/Aenv/pro3"
PHASE = ROOT + "/runs/coordination/cho51_p3_sc1_publication_v1"
SLOT_SPECS = (
    ("admission", 1048576), ("scope", 65536), ("external_return", 65536),
    ("raw_tool_return", 1048576), ("journal_analysis", 131072),
    ("actual_review", 131072), ("root_disposition", 131072),
    ("source_recheck", 65536), ("runtime_recheck", 65536),
    ("output_census", 131072), ("cleanup_assessment", 65536),
    ("timing_join", 65536), ("allocation", 65536), ("source_review", 131072),
    ("contract_adoption", 16384), ("closeout", 65536),
)
RESERVED_BYTES = 3293184
MAX_AUTHORITY_BYTES = 1048576
MAX_PEER_BYTES = 131072
CONFIRMATION_BYTES = 8192
SOURCE_REQUIRED = frozenset(ROOT + "/" + path for path in (
    "tools/local_validation/sc1/__init__.py",
    "tools/local_validation/sc1/publisher.py",
    "tools/local_validation/sc1/native_backend.py",
    "tools/local_validation/lq19/native_reader.py",
    "tools/local_validation/v1/records.py",
    "docs/phase2/cho51_p3_startup_cost_v1/contract.md",
    "docs/phase2/cho51_p3_startup_cost_v1/metadata-ownership.json",
    "docs/phase2/cho51_p3_startup_cost_v1/qualification.md",
))
FALSES = ("runtime_admission", "qualification_accepted", "p_admitted", "scientific_admission")
HEX = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9_./:-]{1,128}\Z")


class PublicationRefusal(ValueError):
    """A consumed transaction cannot continue, repair or release reservations."""


def require(value, message):
    if not value:
        raise PublicationRefusal(message)


def closed(value, fields):
    require(type(value) is dict and set(value) == set(fields), "closed fields required")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _integer(value, low, high):
    require(type(value) is int and low <= value <= high, "exact bounded integer")
    return value


def _token(value):
    require(type(value) is str and TOKEN.fullmatch(value), "bounded identity token")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def _no_number(_):
    raise PublicationRefusal("floating/nonfinite JSON number refused; retain native payload as text")


def _load(raw, cap):
    require(type(raw) is bytes and 0 < len(raw) <= cap, "bounded immutable UTF-8 input")
    try:
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs,
                           parse_float=_no_number, parse_constant=_no_number)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise PublicationRefusal("strict JSON input refused") from error
    return value


def encode(value, cap, checkpoint):
    """Canonical bounded JSON, with <=4096-codepoint string escape blocks.

    Strings are copied into this role's complete envelope, so escaping and all
    headers count. No native JSON payload is parsed/reformatted to save space.
    An encoded block has at most49152 ASCII bytes (surrogate-pair escaping).
    """
    _integer(cap, 1, MAX_AUTHORITY_BYTES)
    output = bytearray()
    nodes = 0
    active = set()

    def emit(raw):
        require(checkpoint() is True, "live metadata checkpoint refused")
        require(len(output) + len(raw) <= cap, "complete encoded role cap")
        output.extend(raw)

    def string(text):
        require(type(text) is str and len(text) <= MAX_AUTHORITY_BYTES, "bounded string")
        emit(b'"')
        for offset in range(0, len(text), 4096):
            part = text[offset:offset + 4096]
            # Reject invalid supplied surrogates rather than normalizing them.
            part.encode("utf-8", "strict")
            escaped = json.dumps(part, ensure_ascii=True)[1:-1].encode("ascii")
            require(len(escaped) <= 49152, "escape block bound")
            emit(escaped)
        emit(b'"')

    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        require(nodes <= 100000 and depth <= 24, "JSON traversal bound")
        require(checkpoint() is True, "live metadata traversal refused")
        kind = type(item)
        if kind is dict or kind is list:
            require(id(item) not in active and len(item) <= 4096, "container/cycle bound")
            active.add(id(item))
            try:
                if kind is dict:
                    require(all(type(key) is str and len(key) <= 128 for key in item), "bounded keys")
                    emit(b"{")
                    for index, key in enumerate(sorted(item)):
                        if index:
                            emit(b",")
                        string(key); emit(b":"); visit(item[key], depth + 1)
                    emit(b"}")
                else:
                    emit(b"[")
                    for index, child in enumerate(item):
                        if index:
                            emit(b",")
                        visit(child, depth + 1)
                    emit(b"]")
            finally:
                active.remove(id(item))
        elif kind is str:
            string(item)
        elif kind is int:
            _integer(item, -(2**63), 2**63 - 1); emit(str(item).encode("ascii"))
        elif kind is bool:
            emit(b"true" if item else b"false")
        elif item is None:
            emit(b"null")
        else:
            raise PublicationRefusal("non-JSON or floating value refused")

    visit(value, 0)
    emit(b"\n")
    return bytes(output)


def _pin(value, path=False):
    closed(value, ("path", "bytes", "sha256") if path else ("bytes", "sha256"))
    _integer(value["bytes"], 0, 16 * 1024**2)
    require(type(value["sha256"]) is str and HEX.fullmatch(value["sha256"]), "SHA256 pin")
    if path:
        require(type(value["path"]) is str and value["path"].startswith(ROOT + "/")
                and len(value["path"]) <= 4096, "project absolute pinned path")
    return value


class FixedSlotPublisher:
    """One non-resumable metadata transaction; no hidden filesystem fallback.

    `host.claim_operation(op, authority_pin)` must atomically consume the UUID
    across sessions and return the exact closed claim below. `host.peer_message`
    must return original authenticated peer-message bytes, not user JSON echoed
    back. `host.operation_artifacts(op)` must supply a complete authenticated
    operation census, including off-directory files and partial writes. There is
    intentionally no default host. An injected backend supports
    qualification tests, and cannot establish native custody on its own.
    """

    def __init__(self, authority_raw, authority_pin, *, host, backend, checkpoint):
        require(callable(checkpoint), "live guard required")
        require(callable(getattr(host, "claim_operation", None))
                and callable(getattr(host, "peer_message", None))
                and callable(getattr(host, "operation_artifacts", None)), "trusted host binding required")
        _pin(authority_pin)
        require(type(authority_raw) is bytes and 0 < len(authority_raw) <= MAX_AUTHORITY_BYTES
                and len(authority_raw) == authority_pin["bytes"]
                and digest(authority_raw) == authority_pin["sha256"], "exact authority bytes")
        value = _load(authority_raw, MAX_AUTHORITY_BYTES)
        closed(value, ("schema", "operation_id", "publisher", "phase", "sources",
                       "source_reviewer", "source_message_id", "capture"))
        require(value["schema"] == "cho51_sc1_publication_authority_v1"
                and value["publisher"] == "project_root" and value["phase"] == PHASE,
                "closed metadata-only authority")
        operation = value["operation_id"]
        require(type(operation) is str and len(operation) == 36 and str(uuid.UUID(operation)) == operation,
                "canonical new UUID")
        require(_token(value["source_reviewer"]) != "project_root", "independent source reviewer")
        _token(value["source_message_id"])
        sources = value["sources"]
        require(type(sources) is dict and SOURCE_REQUIRED <= set(sources)
                and len(sources) <= 512, "complete bounded required source closure")
        for path, pin in sources.items():
            _pin(pin)
            _pin(dict(pin, path=path), path=True)
        capture = value["capture"]
        closed(capture, ("transport", "raw_max_encoded_bytes", "external_max_encoded_bytes", "proof"))
        require(capture["transport"] == "exact_tool_chunks_utf8_v1", "reviewed fixed capture representation")
        _integer(capture["raw_max_encoded_bytes"], 1, 1048576)
        _integer(capture["external_max_encoded_bytes"], 1, 65536)
        _pin(capture["proof"], path=True)
        require(sources.get(capture["proof"]["path"]) ==
                {key: capture["proof"][key] for key in ("bytes", "sha256")}, "capture proof must be pinned input")
        # Re-encode to check bounded depth/types without trusting parsed JSON size.
        encode(value, MAX_AUTHORITY_BYTES, checkpoint)
        self._authority, self._authority_pin = value, dict(authority_pin)
        self._host, self._backend, self._checkpoint = host, backend, checkpoint
        self._operation = operation
        self._slots = {role: {"path": PHASE + "/" + role + "_" + operation + ".json",
                              "reserved_bytes": cap} for role, cap in SLOT_SPECS}
        require(len(self._slots) == 16 and sum(s["reserved_bytes"] for s in self._slots.values()) == RESERVED_BYTES,
                "closed complete reservation template")
        self._states = {role: "RESERVED" for role in self._slots}
        self._published, self._reviews = {}, {}
        self._source_authors = None
        self._source_confirmed = False
        self._status, self._claim, self._failure, self._cleanup_error = "RESERVED", None, None, None
        self._claim_attempted = False
        self._claim_verified = False

    @property
    def operation(self):
        return self._operation

    def _guard(self):
        require(self._checkpoint() is True, "live metadata checkpoint refused")

    def _expect_state(self, expected):
        if self._status != expected:
            error = PublicationRefusal("transaction state refuses this mutation")
            if self._status in ("RESERVED", "READY"):
                self._fail(error)
            raise error

    def _consume(self):
        require(not self._claim_attempted, "operation claim cannot be retried")
        self._claim_attempted = True
        expected = {"operation_id": self.operation, "authority_sha256": self._authority_pin["sha256"],
                    "publisher": "project_root", "claim": "CONSUMED_METADATA_ONLY"}
        self._claim = self._host.claim_operation(self.operation, dict(self._authority_pin))
        require(type(self._claim) is dict and self._claim == expected, "atomic root operation claim unavailable")
        self._claim_verified = True

    def _census(self, pending=None):
        self._guard()
        value = self._host.operation_artifacts(self.operation)
        self._guard()
        closed(value, ("operation_id", "paths"))
        paths = value["paths"]
        require(value["operation_id"] == self.operation and type(paths) is list and len(paths) <= 16
                and all(type(path) is str and len(path) <= 4096 for path in paths)
                and len(set(paths)) == len(paths), "bounded exact operation artifact census")
        expected = {reference["path"] for reference in self._published.values()}
        if pending is not None:
            expected.add(pending)
        require(set(paths) == expected, "extra, missing or off-ledger operation artifact")

    def _peer(self, reviewer, message_id):
        _token(reviewer); _token(message_id)
        require(reviewer != "project_root", "root cannot self-certify peer judgment")
        self._guard()
        raw = self._host.peer_message(reviewer, message_id)
        self._guard()
        value = _load(raw, MAX_PEER_BYTES)
        encode(value, MAX_PEER_BYTES, self._checkpoint)
        require(value.get("reviewer") == reviewer and value.get("message_id") == message_id,
                "authenticated peer lookup identity differs")
        return value

    def _fail(self, error):
        self._status = "FAILED_CONSUMED"
        self._failure = type(error).__name__ + ": " + str(error)[:512]
        # Consumption is bookkeeping, never a create or an execution grant. The
        # trusted host must retain it even when a live guard has already refused.
        if not self._claim_attempted:
            try:
                self._consume()
            except BaseException as claim_error:
                self._failure += "; operation claim unknown: " + type(claim_error).__name__
        for role, state in self._states.items():
            if state == "CREATE_ATTEMPTED":
                self._states[role] = "FAILED_CONSUMED"
        try:
            self._backend.close()
        except BaseException as cleanup:
            self._cleanup_error = type(cleanup).__name__ + ": " + str(cleanup)[:512]
        raise PublicationRefusal(self._failure + ("; custody unknown: " + self._cleanup_error
                                                  if self._cleanup_error else "")) from error

    def _envelope(self, role, body):
        return {"schema": "cho51_sc1_" + role + "_slot_v1", "operation_id": self.operation,
                "publisher": "project_root", "body": body, **{key: False for key in FALSES}}

    def initialize(self):
        self._expect_state("RESERVED")
        try:
            self._guard()
            self._consume()
            authorization = self._peer(self._authority["source_reviewer"], self._authority["source_message_id"])
            closed(authorization, ("schema", "reviewer", "message_id", "authors", "status", "sources", "capture", "phase"))
            require(authorization["schema"] == "cho51_sc1_source_authorization_v1"
                    and authorization["status"] == "ACCEPTED_SOURCE_ONLY"
                    and authorization["sources"] == self._authority["sources"]
                    and authorization["capture"] == self._authority["capture"]
                    and authorization["phase"] == PHASE, "exact independently reviewed authority/template")
            authors = authorization["authors"]
            require(type(authors) is list and 1 <= len(authors) <= 16 and "project_root" in authors
                    and len(set(authors)) == len(authors)
                    and all(type(author) is str and TOKEN.fullmatch(author) for author in authors)
                    and authorization["reviewer"] not in authors, "independent source authorship")
            self._source_authors = tuple(authors)
            # All16 full charges exist before any native create, including allocation.
            self._backend.prepare(self._authority["sources"], PHASE)
            self._census()
            for slot in self._slots.values():
                self._guard(); self._backend.require_absent(slot["path"])
            ledger = {"schema": "cho51_sc1_allocation_v1", "operation_id": self.operation,
                      "publisher": "project_root", "authority_pin": self._authority_pin,
                      "reserved_files": 16, "reserved_bytes": RESERVED_BYTES,
                      "file_cap": 16, "byte_cap": 4194304, "failed_reservations_released": False,
                      "slots": self._slots}
            raw = encode(self._envelope("allocation", ledger), 65536, self._checkpoint)
            self._create("allocation", raw, bootstrap=True)
            self._status = "READY"
            return copy.deepcopy(self._published["allocation"])
        except BaseException as error:
            self._fail(error)

    def _create(self, role, raw, *, bootstrap=False):
        require(role in self._slots and self._states[role] == "RESERVED", "exact unused role")
        slot = self._slots[role]
        require(type(raw) is bytes and len(raw) <= slot["reserved_bytes"], "complete role encoded capacity")
        self._guard()
        if not bootstrap:
            require(self._status == "READY" and role != "allocation", "verified ledger required")
            # Reopening uses the saved native identity as well as exact content pin.
            self._backend.verify_publication(self._published["allocation"])
        else:
            require(role == "allocation" and self._status == "RESERVED" and self._claim is not None,
                    "allocation-only bootstrap")
        self._backend.verify_inputs()
        self._census()
        self._backend.require_absent(slot["path"])
        self._states[role] = "CREATE_ATTEMPTED"
        reference = self._backend.write_new(slot["path"], raw)
        closed(reference, ("path", "bytes", "sha256", "native_identity",
                           "original_file_closed", "original_ancestry_closed"))
        _pin({key: reference[key] for key in ("path", "bytes", "sha256")}, path=True)
        require(reference["path"] == slot["path"] and reference["bytes"] == len(raw)
                and reference["sha256"] == digest(raw)
                and reference.get("original_file_closed") is True
                and reference.get("original_ancestry_closed") is True,
                "complete original publication/closure evidence required")
        identity = reference["native_identity"]
        closed(identity, ("schema", "volume_serial", "file_id", "volume_kind", "filesystem"))
        require(identity["schema"] == "cho51_lv_native_identity_v1"
                and identity["volume_kind"] == "local_fixed" and identity["filesystem"] == "NTFS"
                and type(identity["volume_serial"]) is str
                and re.fullmatch(r"[0-9a-f]{16}", identity["volume_serial"])
                and identity["volume_serial"] != "0" * 16 and type(identity["file_id"]) is str
                and re.fullmatch(r"[0-9a-f]{32}", identity["file_id"]) and identity["file_id"] != "0" * 32,
                "exact non-floating native publication identity")
        self._census(pending=slot["path"])
        self._published[role] = copy.deepcopy(reference)
        self._states[role] = "PUBLISHED"

    def _publish(self, role, body):
        self._expect_state("READY")
        try:
            require(role in self._slots and role != "allocation", "closed publication role")
            raw = encode(self._envelope(role, body), self._slots[role]["reserved_bytes"], self._checkpoint)
            if role in ("raw_tool_return", "external_return"):
                bound = self._authority["capture"]["raw_max_encoded_bytes" if role == "raw_tool_return"
                                                     else "external_max_encoded_bytes"]
                require(len(raw) <= bound, "complete capture exceeds independently reviewed maximum")
            self._create(role, raw)
            return copy.deepcopy(self._published[role])
        except BaseException as error:
            self._fail(error)

    def publish_record(self, role, text):
        """Preserve supplied text; envelopes are metadata and never launch grants."""
        allowed = {"admission", "scope", "journal_analysis", "source_recheck", "runtime_recheck",
                   "output_census", "cleanup_assessment", "timing_join", "closeout"}
        self._expect_state("READY")
        try:
            require(role in allowed and type(text) is str, "typed text-record role")
            if role == "admission":
                require(self._source_confirmed, "persisted independent source confirmation required")
            return self._publish(role, {"schema": "cho51_sc1_text_record_v1", "text": text})
        except BaseException as error:
            if self._status == "FAILED_CONSUMED":
                raise
            self._fail(error)

    def publish_capture(self, chunks, external_text):
        """Each supplied chunk is its full original tool-response text.

        No stdout-only selection, native JSON parse, truncation or re-encoding of
        the supplied strings. Both entire envelopes must fit before either create.
        A failure in the second create consumes the transaction and preserves first.
        """
        self._expect_state("READY")
        try:
            require(type(chunks) is list and 1 <= len(chunks) <= 64
                    and all(type(chunk) is str for chunk in chunks) and type(external_text) is str,
                    "complete original capture strings")
            bodies = {"raw_tool_return": {"schema": "cho51_sc1_raw_capture_v1", "chunks": list(chunks)},
                      "external_return": {"schema": "cho51_sc1_external_text_v1", "text": external_text}}
            for role, body in bodies.items():
                raw = encode(self._envelope(role, body), self._slots[role]["reserved_bytes"], self._checkpoint)
                key = "raw_max_encoded_bytes" if role == "raw_tool_return" else "external_max_encoded_bytes"
                require(len(raw) <= self._authority["capture"][key], "complete precreate capture bound")
            return [self._publish(role, body) for role, body in bodies.items()]
        except BaseException as error:
            if self._status == "FAILED_CONSUMED":
                raise
            self._fail(error)

    def publish_review(self, role, reviewer, message_id):
        self._expect_state("READY")
        try:
            require(role in ("source_review", "actual_review"), "review slot")
            value = self._peer(reviewer, message_id)
            closed(value, ("schema", "operation_id", "role", "reviewer", "message_id", "decision", "text", "text_sha256"))
            require(value["schema"] == "cho51_sc1_peer_review_v1" and value["operation_id"] == self.operation
                    and value["role"] == role and type(value["text"]) is str
                    and value["text_sha256"] == digest(value["text"].encode("utf-8", "strict")), "exact peer review text")
            require(reviewer not in self._source_authors, "author cannot independently review")
            if role == "source_review":
                require(reviewer == self._authority["source_reviewer"]
                        and value["decision"] in ("ACCEPTED_SOURCE_ONLY", "CHANGES_REQUIRED", "INCOMPLETE_REFUSED"),
                        "source review identity/status")
            else:
                require(reviewer != self._authority["source_reviewer"]
                        and value["decision"] in ("ACCEPTED_METADATA_ONLY", "INCOMPLETE_REFUSED", "CUSTODY_UNKNOWN"),
                        "distinct actual review identity/status")
            reference = self._publish(role, value)
            self._reviews[role] = value
            return reference
        except BaseException as error:
            if self._status == "FAILED_CONSUMED":
                raise
            self._fail(error)

    def confirm_review(self, role, message_id):
        self._expect_state("READY")
        try:
            require(role in self._reviews, "published peer review required")
            review, reference = self._reviews[role], self._published[role]
            confirmation = self._peer(review["reviewer"], message_id)
            closed(confirmation, ("schema", "operation_id", "reviewer", "message_id", "review_pin",
                                  "review_text_sha256", "confirmed", "text"))
            expected = {key: reference[key] for key in ("path", "bytes", "sha256")}
            require(confirmation["schema"] == "cho51_sc1_peer_confirmation_v1"
                    and confirmation["operation_id"] == self.operation
                    and confirmation["review_pin"] == expected
                    and confirmation["review_text_sha256"] == review["text_sha256"]
                    and type(confirmation["confirmed"]) is bool and type(confirmation["text"]) is str,
                    "exact postpublication peer confirmation")
            encode(confirmation, CONFIRMATION_BYTES, self._checkpoint)
            destination = "contract_adoption" if role == "source_review" else "root_disposition"
            positive = confirmation["confirmed"] and review["decision"] in (
                "ACCEPTED_SOURCE_ONLY", "ACCEPTED_METADATA_ONLY")
            body = {"schema": "cho51_sc1_confirmed_metadata_disposition_v1", "review_role": role,
                    "confirmation": confirmation, "status": "CONFIRMED_METADATA_ONLY" if positive else "INCOMPLETE_REFUSED"}
            # Confirmation consumes its reserved8KiB envelope; all other fields
            # must separately fit the remainder of this already-fixed role cap.
            remainder = {key: value for key, value in body.items() if key != "confirmation"}
            encode(self._envelope(destination, dict(remainder, confirmation=None)),
                   self._slots[destination]["reserved_bytes"] - CONFIRMATION_BYTES, self._checkpoint)
            self._backend.verify_publication(reference)
            result = self._publish(destination, body)
            if role == "source_review":
                self._source_confirmed = bool(positive)
            return result
        except BaseException as error:
            if self._status == "FAILED_CONSUMED":
                raise
            self._fail(error)

    def snapshot(self):
        # Scalars and copied maps only; callers cannot release/reassign charges.
        return {"operation_id": self.operation, "status": self._status,
                "reserved_files": 16, "reserved_bytes": RESERVED_BYTES,
                "operation_claim": "CONSUMED_METADATA_ONLY" if self._claim_verified else
                                   "UNKNOWN" if self._claim_attempted else "NOT_ATTEMPTED",
                "failed_reservations_released": False, "states": dict(self._states),
                "failure": self._failure, "cleanup_error": self._cleanup_error,
                **{key: False for key in FALSES}}

    def close(self):
        if self._status == "CLOSED":
            return
        require(self._status != "FAILED_CONSUMED", "failed transaction remains consumed; inspect closure evidence")
        try:
            if self._status == "READY":
                self._census()
                self._backend.verify_inputs()
                for reference in self._published.values():
                    self._backend.verify_publication(reference)
            self._backend.close()
            self._status = "CLOSED"
        except BaseException as error:
            self._fail(error)


def create_native_publisher(authority_raw, authority_pin, *, host, checkpoint):
    """Explicit production construction; no host/guard fallback and no dispatch."""
    from .native_backend import NativeBackend
    backend = NativeBackend(checkpoint)
    try:
        return FixedSlotPublisher(authority_raw, authority_pin, host=host, backend=backend, checkpoint=checkpoint)
    except BaseException:
        backend.close()
        raise
