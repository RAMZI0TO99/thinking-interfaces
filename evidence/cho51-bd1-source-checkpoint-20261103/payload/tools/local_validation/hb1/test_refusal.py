"""Unexecuted refusal/replay models; no real provider/native qualification."""

from dataclasses import FrozenInstanceError
import unittest

from .common import Refusal
from .refusal import ModelSession, UnavailableHost
from .test_frames import AUTHORITY, OPERATION, OTHER, REQUEST, SESSION, frame, guard


class HB1RefusalTests(unittest.TestCase):
    def model(self, **kwargs):
        options = {
            "session_id": SESSION, "provider_epoch": "epoch_1", "operation_id": OPERATION,
            "authority_sha256": AUTHORITY, "clock_domain": "clock_1",
            "work_deadline_qpc": "1000", "cleanup_deadline_qpc": "1100",
            "hard_deadline_qpc": "1200", "frequency": 1000, "check": guard,
        }
        options.update(kwargs)
        return ModelSession(**options)

    def begun(self, **kwargs):
        model = self.model(**kwargs)
        model.model_begin(frame(), now_qpc="100")
        return model

    def confirmed(self):
        model = self.begun()
        model.model_confirm_claim(REQUEST, now_qpc="101")
        return model

    def test_unavailable_host_refuses_all_sc1_methods(self):
        host = UnavailableHost(check=guard)
        for call in (lambda: host.claim_operation(OPERATION, {"bytes": 10, "sha256": AUTHORITY}),
                     lambda: host.peer_message("peer", "message"),
                     lambda: host.operation_artifacts(OPERATION)):
            with self.assertRaises(Refusal):
                call()
        self.assertEqual(host.snapshot.capability, "UNAVAILABLE")

    def test_unavailable_claim_consumes_only_local_attempt(self):
        host = UnavailableHost(check=guard)
        self.assertEqual(host.snapshot.local_disposition, "UNAVAILABLE")
        with self.assertRaises(Refusal):
            host.claim_operation(OPERATION, {})
        snapshot = host.snapshot
        self.assertEqual(snapshot.local_disposition, "FAILED_CONSUMED")
        self.assertEqual(snapshot.scope, "LOCAL_OBJECT_ONLY")
        self.assertEqual(snapshot.claim_transport, "NOT_SENT")
        self.assertEqual(snapshot.durable_consumption, "UNKNOWN")
        self.assertFalse(snapshot.authenticated)

    def test_unavailable_duplicate_and_substituted_operation_refuse(self):
        host = UnavailableHost(check=guard)
        for operation in (OPERATION, OPERATION, OTHER):
            with self.assertRaises(Refusal):
                host.claim_operation(operation, {"bytes": 10, "sha256": AUTHORITY})
            self.assertTrue(host.snapshot.claim_attempted)
            self.assertEqual(host.snapshot.durable_consumption, "UNKNOWN")

    def test_unavailable_new_object_is_not_durable_rearm_evidence(self):
        for host in (UnavailableHost(check=guard), UnavailableHost(check=guard)):
            with self.assertRaises(Refusal):
                host.claim_operation(OPERATION, {})
            self.assertEqual(host.snapshot.capability, "UNAVAILABLE")
            self.assertEqual(host.snapshot.durable_consumption, "UNKNOWN")

    def test_unavailable_failed_guard_still_consumes(self):
        for check in (lambda: False, lambda: 1):
            host = UnavailableHost(check=check)
            with self.assertRaises(Refusal):
                host.claim_operation(OPERATION, {})
            self.assertEqual(host.snapshot.local_disposition, "FAILED_CONSUMED")
            self.assertEqual(host.snapshot.claim_transport, "NOT_SENT")

    def test_unavailable_raised_guard_still_consumes(self):
        def broken():
            raise RuntimeError("supplied stop")
        host = UnavailableHost(check=broken)
        with self.assertRaises(Refusal):
            host.claim_operation(OPERATION, {})
        self.assertTrue(host.snapshot.claim_attempted)

    def test_unavailable_malformed_claim_arguments_cannot_escape_consumption(self):
        host = UnavailableHost(check=guard)
        with self.assertRaises(Refusal):
            host.claim_operation(None, {"trusted": True, "callback": lambda: True})
        self.assertEqual(host.snapshot.local_disposition, "FAILED_CONSUMED")

    def test_unavailable_read_only_failure_is_not_success_or_consumption(self):
        host = UnavailableHost(check=guard)
        for call in (lambda: host.peer_message(None, None), lambda: host.operation_artifacts(None)):
            with self.assertRaises(Refusal):
                call()
            self.assertEqual(host.snapshot.local_disposition, "UNAVAILABLE")
            self.assertEqual(host.snapshot.durable_consumption, "UNKNOWN")

    def test_unavailable_snapshot_is_frozen(self):
        snapshot = UnavailableHost(check=guard).snapshot
        with self.assertRaises(FrozenInstanceError):
            snapshot.claim_attempted = True
        self.assertEqual(snapshot.capability, "UNAVAILABLE")

    def test_model_has_no_production_host_methods(self):
        model = self.model()
        for name in ("claim_operation", "peer_message", "operation_artifacts", "connect", "send", "reset", "rearm"):
            self.assertFalse(hasattr(model, name))
        self.assertEqual(model.snapshot.state, "ESTABLISHED")
        self.assertEqual(model.snapshot.scope, "MODEL_ONLY")
        self.assertEqual(model.snapshot.production_capability, "UNAVAILABLE")

    def test_model_claim_sent_precedes_hypothetical_confirmation(self):
        model = self.begun()
        self.assertEqual(model.snapshot.state, "CLAIM_SENT")
        self.assertEqual(model.snapshot.claim_outcome, "UNKNOWN")
        result = model.model_confirm_claim(REQUEST, now_qpc="101")
        self.assertEqual(result.state, "CLAIM_CONFIRMED")
        self.assertEqual(result.claim_outcome, "MODEL_CONFIRMED")
        self.assertEqual(result.scope, "MODEL_ONLY")
        self.assertFalse(result.authenticated)
        self.assertEqual(result.durable_consumption, "NOT_ESTABLISHED")

    def test_unknown_positive_response_never_confirms(self):
        model = self.begun()
        response = frame(direction="response", body={"trusted": True, "durable": True, "claim": "CONSUMED_METADATA_ONLY"})
        with self.assertRaises(Refusal):
            model.model_observe_response(response, now_qpc="101")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
        self.assertEqual(model.snapshot.claim_outcome, "UNKNOWN")

    def test_refused_response_is_failure_not_empty_success(self):
        model = self.begun()
        response = frame(direction="response", status="REFUSED", body={"reason": "CLAIM_UNKNOWN", "detail": "unconfirmed"})
        with self.assertRaises(Refusal):
            model.model_observe_response(response, now_qpc="101")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
        self.assertTrue(model.snapshot.locally_consumed)

    def test_model_duplicate_claim_and_new_uuid_do_not_rearm(self):
        model = self.confirmed()
        duplicate = frame(header_change={"sequence": 2, "request_id": OTHER})
        with self.assertRaises(Refusal):
            model.model_begin(duplicate, now_qpc="102")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
        with self.assertRaises(Refusal):
            model.model_confirm_claim(OTHER, now_qpc="103")

    def test_model_all_ambiguous_transport_failures_are_unknown_consumed(self):
        for reason in ("TIMEOUT", "DISCONNECT", "PARTIAL_SEND", "PARTIAL_REPLY", "RESTART",
                       "MALFORMED", "UNCERTAIN_DURABILITY", "STOP"):
            model = self.begun()
            result = model.model_transport_failure(reason)
            self.assertEqual(result.state, "FAILED_CONSUMED")
            self.assertEqual(result.claim_outcome, "UNKNOWN")
            with self.assertRaises(Refusal):
                model.model_begin(frame(), now_qpc="102")

    def test_model_guard_failure_after_claim_staging_consumes(self):
        stop = [False]
        def check():
            return not stop[0]
        model = self.begun(check=check)
        stop[0] = True
        with self.assertRaises(Refusal):
            model.model_confirm_claim(REQUEST, now_qpc="101")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
        self.assertEqual(model.snapshot.claim_outcome, "UNKNOWN")

    def test_model_malformed_request_and_guard_exception_consume(self):
        model = self.model()
        with self.assertRaises(Refusal):
            model.model_begin(b"broken", now_qpc="100")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
        enabled = [True]
        def check():
            if not enabled[0]:
                raise RuntimeError("stop")
            return True
        model = self.model(check=check)
        enabled[0] = False
        with self.assertRaises(RuntimeError):
            model.model_begin(frame(), now_qpc="100")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_sequence_gap_and_request_replay_refuse(self):
        for change in ({"sequence": 3, "request_id": OTHER}, {"sequence": 2, "request_id": REQUEST}):
            model = self.confirmed()
            request = frame(method="peer_message", header_change=change)
            with self.assertRaises(Refusal):
                model.model_begin(request, now_qpc="102")
            self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_duplicate_or_unsolicited_response_refuses(self):
        for model in (self.model(), self.confirmed()):
            with self.assertRaises(Refusal):
                model.model_observe_response(frame(direction="response", body={}), now_qpc="102")
            self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_only_one_pending_exchange(self):
        model = self.begun()
        with self.assertRaises(Refusal):
            model.model_begin(frame(header_change={"sequence": 2, "request_id": OTHER}), now_qpc="101")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_session_identity_drift_refuses(self):
        for changed in ({"session_id": OTHER}, {"provider_epoch": "epoch_2"}, {"clock_domain": "clock_2"}):
            model = self.model()
            with self.assertRaises(Refusal):
                model.model_begin(frame(header_change=changed), now_qpc="100")
            self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_confirmation_requires_exact_pending_claim_id(self):
        for model, request_id in ((self.model(), REQUEST), (self.begun(), OTHER), (self.begun(), True)):
            with self.assertRaises(Refusal):
                model.model_confirm_claim(request_id, now_qpc="101")
            self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_clock_rollback_and_equality_refuse(self):
        for now in ("99", "200"):
            model = self.begun()
            with self.assertRaises(Refusal):
                model.model_confirm_claim(REQUEST, now_qpc=now)
            self.assertEqual(model.snapshot.claim_outcome, "UNKNOWN")

    def test_model_original_work_and_per_call_ceilings(self):
        for kwargs, deadline in (({"work_deadline_qpc": "150"}, "200"), ({}, "301")):
            model = self.model(**kwargs)
            with self.assertRaises(Refusal):
                model.model_begin(frame(header_change={"deadline_qpc": deadline}), now_qpc="100")
        model = self.model()
        self.assertEqual(model.model_begin(frame(header_change={"deadline_qpc": "300"}), now_qpc="100").state,
                         "CLAIM_SENT")

    def test_model_constructor_rejects_invalid_original_bounds(self):
        for kwargs in ({"work_deadline_qpc": "0"}, {"cleanup_deadline_qpc": "999"},
                       {"hard_deadline_qpc": "1099"}, {"frequency": True}, {"frequency": 0}, {"check": None}):
            with self.assertRaises(Refusal):
                self.model(**kwargs)

    def test_model_pending_close_remains_unknown_failed(self):
        model = self.begun()
        result = model.model_close(now_qpc="201")
        self.assertEqual(result.state, "FAILED_CONSUMED")
        self.assertEqual(result.claim_outcome, "UNKNOWN")
        self.assertTrue(result.closed)
        with self.assertRaises(Refusal):
            model.model_begin(frame(), now_qpc="202")

    def test_model_failed_close_does_not_clean_failure(self):
        model = self.begun()
        model.model_transport_failure("RESTART")
        result = model.model_close(now_qpc="201")
        self.assertEqual(result.state, "FAILED_CONSUMED")
        self.assertEqual(result.claim_outcome, "UNKNOWN")
        self.assertTrue(result.closed)
        with self.assertRaises(Refusal):
            model.model_close(now_qpc="202")

    def test_model_close_is_not_native_closure_and_respects_cleanup_bound(self):
        result = self.confirmed().model_close(now_qpc="201")
        self.assertEqual(result.state, "CLOSED")
        self.assertFalse(result.authenticated)
        self.assertEqual(result.production_capability, "UNAVAILABLE")
        model = self.confirmed()
        with self.assertRaises(Refusal):
            model.model_close(now_qpc="1100")
        self.assertTrue(model.snapshot.closed)
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")

    def test_model_snapshot_is_frozen_and_old_snapshot_does_not_change(self):
        model = self.model()
        original = model.snapshot
        model.model_begin(frame(), now_qpc="100")
        self.assertEqual(original.state, "ESTABLISHED")
        self.assertEqual(model.snapshot.state, "CLAIM_SENT")
        with self.assertRaises(FrozenInstanceError):
            original.claim_outcome = "CONFIRMED"

    def test_model_read_request_requires_claim_and_remains_untrusted(self):
        with self.assertRaises(Refusal):
            self.model().model_begin(frame(method="peer_message"), now_qpc="100")
        model = self.confirmed()
        request = frame(method="peer_message", header_change={"sequence": 2, "request_id": OTHER})
        result = model.model_begin(request, now_qpc="102")
        self.assertEqual(result.state, "CLAIM_CONFIRMED")
        response = frame(method="peer_message", direction="response", raw_payload=b"original bytes",
                         header_change={"sequence": 2, "request_id": OTHER})
        with self.assertRaises(Refusal):
            model.model_observe_response(response, now_qpc="103")
        self.assertEqual(model.snapshot.state, "FAILED_CONSUMED")
