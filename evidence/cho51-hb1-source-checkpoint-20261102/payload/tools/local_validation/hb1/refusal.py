"""Unavailable production capability and explicitly separate supplied-state model.

No function here connects, sends, writes, launches, reads a clock, or claims
durable consumption. Model transitions are hypotheses, not provider evidence.
"""

from dataclasses import dataclass

from .common import Refusal, checkpoint, integer, require, sha256_text, token, uuid_text
from .frames import parse_request, parse_response, qpc_text


@dataclass(frozen=True, slots=True)
class UnavailableSnapshot:
    local_disposition: str
    claim_attempted: bool

    @property
    def capability(self):
        return "UNAVAILABLE"

    @property
    def claim_transport(self):
        return "NOT_SENT"

    @property
    def durable_consumption(self):
        return "UNKNOWN"

    @property
    def scope(self):
        return "LOCAL_OBJECT_ONLY"

    @property
    def authenticated(self):
        return False


class UnavailableHost:
    """SC1-shaped refusal only. A new instance cannot prove a UUID is unused."""

    def __init__(self, *, check):
        require(callable(check), "checkpoint required")
        self._check = check
        self._attempted = False

    @property
    def snapshot(self):
        return UnavailableSnapshot(
            "FAILED_CONSUMED" if self._attempted else "UNAVAILABLE", self._attempted)

    def claim_operation(self, operation, authority_pin):
        # Consume this local mutation attempt BEFORE any check can fail. Neither
        # argument can supply a host witness, even when syntactically valid.
        duplicate = self._attempted
        self._attempted = True
        try:
            checkpoint(self._check)
        except Exception as error:
            raise Refusal("UNAVAILABLE: checkpoint refused; local attempt consumed; NOT_SENT") from error
        if duplicate:
            raise Refusal("UNAVAILABLE: local claim already consumed; durable outcome UNKNOWN")
        raise Refusal("UNAVAILABLE: no qualified provider; local attempt consumed; NOT_SENT")

    def peer_message(self, peer, message_id):
        checkpoint(self._check)
        raise Refusal("UNAVAILABLE: original peer provenance is not established")

    def operation_artifacts(self, operation):
        checkpoint(self._check)
        raise Refusal("UNAVAILABLE: complete provider census is not established")


@dataclass(frozen=True, slots=True)
class ModelSnapshot:
    state: str
    claim_outcome: str
    requests_started: int
    pending_request_id: str | None
    locally_consumed: bool
    closed: bool

    @property
    def scope(self):
        return "MODEL_ONLY"

    @property
    def authenticated(self):
        return False

    @property
    def production_capability(self):
        return "UNAVAILABLE"

    @property
    def durable_consumption(self):
        return "NOT_ESTABLISHED"


class ModelSession:
    """Finite replay/state model; deliberately has no three SC1 host methods.

    The supplied absolute deadlines and frequency constrain this model only. They
    cannot demonstrate native cancellation, work/cleanup bounds or live guards.
    Positive confirmation is an explicit symbolic model event, never parsed
    from arbitrary provider JSON. Actual supplied OK replies remain unknown.
    """

    def __init__(self, *, session_id, provider_epoch, operation_id, authority_sha256,
                 clock_domain, work_deadline_qpc, cleanup_deadline_qpc,
                 hard_deadline_qpc, frequency, check):
        checkpoint(check)
        uuid_text(session_id)
        uuid_text(operation_id)
        token(provider_epoch)
        token(clock_domain)
        sha256_text(authority_sha256)
        integer(frequency, 1)
        work = qpc_text(work_deadline_qpc)
        cleanup = qpc_text(cleanup_deadline_qpc)
        hard = qpc_text(hard_deadline_qpc)
        require(0 < work <= cleanup <= hard, "original model deadline order")
        self._identity = (session_id, provider_epoch, operation_id, authority_sha256, clock_domain)
        self._check = check
        self._frequency = frequency
        self._work, self._cleanup, self._hard = work, cleanup, hard
        self._last_now = None
        self._state = "ESTABLISHED"
        self._outcome = "NOT_SENT"
        self._seen = set()
        self._pending = None
        self._pending_header = None
        self._claim_attempted = False
        self._consumed = False
        self._closed = False

    @property
    def snapshot(self):
        return ModelSnapshot(self._state, self._outcome, len(self._seen),
                             None if self._pending_header is None else self._pending_header["request_id"],
                             self._consumed, self._closed)

    def _fail(self):
        self._state = "FAILED_CONSUMED"
        self._consumed = True
        self._outcome = "UNKNOWN"
        self._pending = None
        self._pending_header = None

    def _active(self):
        require(not self._closed and not self._consumed, "model is closed or consumed")

    def _now(self, value, bound):
        now = qpc_text(value)
        require(self._last_now is None or now >= self._last_now, "supplied clock rollback")
        require(now < min(bound, self._hard), "supplied absolute deadline reached")
        self._last_now = now
        return now

    def model_begin(self, request_raw, *, now_qpc):
        """Consume a finite modeled request; never send its bytes anywhere."""
        try:
            self._active()
            checkpoint(self._check)
            now = self._now(now_qpc, self._work)
            require(self._pending is None, "one sequential modeled exchange")
            frame = parse_request(request_raw, check=self._check, now_qpc=now_qpc,
                                  clock_domain=self._identity[4])
            header = frame.header
            actual = tuple(header[key] for key in (
                "session_id", "provider_epoch", "operation_id", "authority_sha256", "clock_domain"))
            require(actual == self._identity, "modeled session join")
            require(header["sequence"] == len(self._seen) + 1, "modeled sequence gap/replay")
            require(header["request_id"] not in self._seen, "modeled request ID replay")
            deadline = qpc_text(header["deadline_qpc"])
            require(deadline <= self._work, "request exceeds original work bound")
            require((deadline - now) * 1000 <= self._frequency * 200,
                    "request exceeds modeled 200ms ceiling")
            if header["method"] == "claim_operation":
                require(not self._claim_attempted and self._state == "ESTABLISHED",
                        "one modeled mutating claim")
                self._claim_attempted = True
                # This is the BEFORE-POSSIBLE-COMMIT model state. No transport exists.
                self._state = "CLAIM_SENT"
                self._outcome = "UNKNOWN"
            else:
                require(self._state == "CLAIM_CONFIRMED", "modeled claim not confirmed")
            self._seen.add(header["request_id"])
            self._pending, self._pending_header = request_raw, header
            checkpoint(self._check)
            return self.snapshot
        except BaseException:
            self._fail()
            raise

    def model_confirm_claim(self, request_id, *, now_qpc):
        """Apply an explicit hypothetical event; never interpret a host reply.

        This method tests the state machine's positive branch only. Its frozen
        MODEL_ONLY result cannot be supplied as a production channel witness.
        """
        try:
            self._active()
            checkpoint(self._check)
            uuid_text(request_id)
            require(self._state == "CLAIM_SENT" and self._pending_header is not None,
                    "no pending modeled claim")
            require(request_id == self._pending_header["request_id"], "model confirmation join")
            self._now(now_qpc, qpc_text(self._pending_header["deadline_qpc"]))
            checkpoint(self._check)
            self._state, self._outcome = "CLAIM_CONFIRMED", "MODEL_CONFIRMED"
            self._pending, self._pending_header = None, None
            return self.snapshot
        except BaseException:
            self._fail()
            raise

    def model_observe_response(self, response_raw, *, now_qpc):
        """Check a reply then consume refusal/unknown evidence, never promote OK."""
        try:
            self._active()
            checkpoint(self._check)
            require(self._pending is not None, "unsolicited/duplicate modeled response")
            self._now(now_qpc, qpc_text(self._pending_header["deadline_qpc"]))
            frame = parse_response(response_raw, self._pending, check=self._check,
                                   now_qpc=now_qpc, clock_domain=self._identity[4])
            self._fail()
            if frame.header["status"] == "REFUSED":
                raise Refusal("modeled REFUSED response; failure remains consumed")
            raise Refusal("positive provider schema/witness unavailable; outcome UNKNOWN")
        except BaseException:
            self._fail()
            raise

    def model_transport_failure(self, reason):
        """Record only bounded symbolic failures; absence cannot restore a claim."""
        try:
            self._active()
            checkpoint(self._check)
            require(type(reason) is str and reason in (
                "TIMEOUT", "DISCONNECT", "PARTIAL_SEND", "PARTIAL_REPLY",
                "RESTART", "MALFORMED", "UNCERTAIN_DURABILITY", "STOP"),
                "unknown modeled failure")
            self._fail()
            return self.snapshot
        except BaseException:
            self._fail()
            raise

    def model_close(self, *, now_qpc):
        """Record local model closure without asserting native channel closure."""
        if self._closed:
            raise Refusal("model already closed")
        try:
            checkpoint(self._check)
            self._now(now_qpc, self._cleanup)
            if self._pending is not None:
                self._fail()
            if not self._consumed:
                self._state = "CLOSED"
            self._closed = True
            return self.snapshot
        except BaseException:
            self._fail()
            self._closed = True
            raise
