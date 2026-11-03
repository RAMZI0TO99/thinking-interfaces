"""Supplied callback state only; no live result, executor or runtime capability.

Trace pairs arrive in innermost-first order. No object or exception is inspected.
Every case PASS remains provisional until suite closure and a complete footer.
This finite model supports only the declared routes below, not every CM1 route.
UNSUPPORTED callbacks refuse sticky without inventing a completed trace group.
Each unique fixture slot denotes one declared callback boundary; multiple actual
cleanup errors require distinct supplied slots with the same owner and phase.
"""
import hashlib
from dataclasses import dataclass

from ..hb1 import common as c
from . import registry

MAX_RECORDS = 4096
MAX_REPORT = 2097152
EXCEPTIONS = ('ASSERT', 'EXCEPTION', 'SYSTEM_EXIT', 'KEYBOARD_INTERRUPT')


@dataclass(frozen=True, slots=True)
class Facts:
    records: int
    started: int
    passed: int
    ended: int
    negative: bool
    refused: bool
    suite_closed: bool
    complete: bool
    not_started: tuple
    whole_sha256: str

    @property
    def authenticated(self):
        return False

    @property
    def execution_accepted(self):
        return False

    @property
    def supplied_success(self):
        return (self.complete and self.suite_closed and not self.negative
                and not self.refused and not self.not_started
                and self.started == self.passed == self.ended == 248)


def _guard(method):
    def guarded(self, *args, **kwargs):
        if self._busy or self._refused:
            self._refused = True
            raise c.Refusal('sticky callback refusal')
        self._busy = True
        try:
            c.checkpoint(self._check)
            c.require(not self._refused and not self._complete, 'closed callback state')
            result = method(self, *args, **kwargs)
            c.checkpoint(self._check)
            c.require(not self._refused, 'reentrant callback refusal')
            return result
        except BaseException:
            self._refused = True
            raise
        finally:
            self._busy = False
    return guarded


class CallbackModel:
    def __init__(self, operation, *, codes=(), fixtures=(), check):
        self._check = check
        self._busy = True
        self._refused = False
        self._complete = self._closed = self._negative = False
        self._lines = []
        self._bytes = 0
        self._hash = hashlib.sha256()
        self._started = self._passed = self._ended = 0
        self._active = None
        self._cleanup = self._primary = self._badcase = False
        self._subs = 0
        self._duration = False
        self._special = None
        try:
            self._op = c.uuid_text(operation)
            c.checkpoint(check)
            expected = registry.expected_ids()
            selected = registry.selected_ids()
            self._order = registry.selected_ordinals()
            c.require(type(expected) is tuple and len(expected) == 764
                      and type(selected) is tuple and len(selected) == 248
                      and type(self._order) is tuple and len(self._order) == 248
                      and tuple(expected[i] for i in self._order) == selected,
                      'immutable successor roster')
            self._roster = c.sha256_text(registry.roster_digest(check))
            c.require(type(codes) is tuple and len(codes) <= 4096, 'code table')
            for row in codes:
                c.checkpoint(check)
                c.require(type(row) is tuple and len(row) == 2, 'code row')
                c.integer(row[0], 0, 65535)
                c.integer(row[1], 1, 2147483647)
            c.require(len(set(codes)) == len(codes), 'duplicate location')
            self._codes = frozenset(codes)
            c.require(type(fixtures) is tuple and len(fixtures) <= 4096, 'fixture table')
            owners = set()
            for row in fixtures:
                c.checkpoint(check)
                c.require(type(row) is tuple and len(row) == 4, 'fixture row')
                slot, owner, phase, affected = row
                c.integer(slot, 0, 4095)
                c.token(owner)
                c.require(type(phase) is str and phase in ('setup','teardown','cleanup')
                          and type(affected) is tuple and 0 < len(affected) <= 248,
                          'fixture route')
                for ordinal in affected:
                    c.integer(ordinal, 0, 763)
                matches = tuple(i for i in self._order if
                                expected[i].rsplit('.', 1)[0] == owner or
                                expected[i].rsplit('.', 2)[0] == owner)
                c.require(affected == matches and slot not in owners, 'fixture ownership')
                owners.add(slot)
            self._fixtures = fixtures
            self._fixture_seen = set()
            self._emit('HEADER', count=248)
            c.require(not self._refused, 'constructor reentry')
        except BaseException:
            self._refused = True
            raise
        finally:
            self._busy = False

    def _emit(self, event, *, case=None, sub=None, fixture=None, kind='NONE',
              code=None, line=None, count=None, prefix=None):
        limit = MAX_RECORDS if event == 'FOOTER' else MAX_RECORDS - 1
        c.require(not self._refused and len(self._lines) < limit, 'event record cap')
        row = dict(schema='cho51_cm2_event_v1', seq=len(self._lines)+1,
                   op=self._op, roster=self._roster, event=event, case=case,
                   sub=sub, fixture=fixture, kind=kind, code=code, line=line,
                   count=count, prefix=prefix)
        raw = c.bounded_bytes(row, 512, self._check)
        byte_limit = MAX_REPORT if event == 'FOOTER' else MAX_REPORT - 512
        c.require(not self._refused and self._bytes + len(raw) <= byte_limit,
                  'event byte cap or reentry')
        self._lines.append(raw)
        self._bytes += len(raw)
        self._hash.update(raw)

    def _case(self, case):
        c.integer(case, 0, 763)
        c.require(self._active == case and not self._closed, 'active case required')

    def _trace(self, event, kind, trace, *, case=None, sub=None, fixture=None):
        c.require(type(kind) is str and type(trace) is tuple and len(trace) <= 128,
                  'bounded primitive trace')
        if event in ('SKIP','XPASS'):
            c.require(kind == 'NONE' and not trace, 'zero trace outcome')
        elif event == 'FIXTURE_ERROR' and kind == 'NONE':
            c.require(not trace, 'fixture skip has no trace')
        else:
            c.require(kind in EXCEPTIONS and trace, 'complete exception trace required')
        for pair in trace:
            c.checkpoint(self._check)
            c.require(type(pair) is tuple and len(pair) == 2, 'trace pair')
            c.integer(pair[0], 0, 65535)
            c.integer(pair[1], 1, 2147483647)
            c.require(pair in self._codes, 'unknown trace location')
        self._emit(event, case=case, sub=sub, fixture=fixture, kind=kind, count=len(trace))
        for index, (code, line) in enumerate(trace, 1):
            self._emit('TRACE', case=case, sub=sub, fixture=fixture, kind=kind,
                       code=code, line=line, count=index)

    @_guard
    def start(self, case):
        c.integer(case, 0, 763)
        c.require(not self._closed and self._active is None and not self._negative
                  and self._started < 248 and case == self._order[self._started], 'start order')
        self._emit('CASE_START', case=case)
        self._active = case
        self._started += 1
        self._cleanup = self._primary = self._badcase = False
        self._subs = 0
        self._duration = False
        self._special = None

    @_guard
    def cleanup_done(self, case):
        self._case(case)
        c.require(not self._cleanup and (not self._primary or self._badcase), 'cleanup order')
        self._cleanup = True

    @_guard
    def outcome(self, case, event, kind='NONE', trace=()):
        self._case(case)
        c.require(type(event) is str, 'primitive callback')
        c.require(not self._primary or (self._special == 'SKIP'
                                       and event in ('FAIL', 'ERROR')
                                       and not self._cleanup), 'primary callback')
        if event == 'PASS':
            c.require(self._cleanup and not self._badcase and not self._negative
                      and type(kind) is str and kind == 'NONE'
                      and type(trace) is tuple and not trace, 'provisional pass gate')
            self._emit('PASS', case=case)
            self._passed += 1
            self._primary = True
        else:
            c.require(event in ('FAIL','ERROR','SKIP','XFAIL','XPASS'), 'unknown outcome')
            c.require(not self._badcase or event in ('FAIL','ERROR'),
                      'negative special after observed failure')
            c.require(not self._cleanup or event in ('XFAIL','XPASS'), 'late callback')
            c.require(event not in ('XFAIL','XPASS') or self._cleanup,
                      'expected outcome before cleanup')
            self._trace(event, kind, trace, case=case)
            self._negative = self._badcase = True
            # Multiple teardown/method cleanup errors are actual separate callbacks.
            if event in ('SKIP','XFAIL','XPASS'):
                self._primary = True
                self._special = event

    @_guard
    def subtest(self, case, sub, event='SUBPASS', kind='NONE', trace=()):
        self._case(case)
        c.integer(sub, 1, 4096)
        c.require(not self._cleanup and not self._primary and not self._negative
                  and sub == self._subs + 1 and type(event) is str, 'subtest route')
        if event == 'SUBPASS':
            c.require(type(kind) is str and kind == 'NONE' and type(trace) is tuple
                      and not trace, 'subpass')
            self._emit(event, case=case, sub=sub)
        else:
            c.require(event == 'SUBFAIL', 'unknown/nested subtest route')
            self._trace(event, kind, trace, case=case, sub=sub)
            self._negative = self._badcase = True
        self._subs += 1

    @_guard
    def duration(self, case, value):
        self._case(case)
        c.require(self._cleanup and not self._duration
                  and (not self._primary or self._special == 'SKIP'), 'duration order')
        # This declared supplied route uses integer units only, never native time.
        c.integer(value, 0, 2**63-1)
        self._duration = True

    @_guard
    def stop(self, case):
        self._case(case)
        c.require(self._cleanup and (self._primary or self._badcase), 'stop without outcome/cleanup')
        self._emit('CASE_END', case=case, count=self._subs)
        self._active = None
        self._ended += 1

    @_guard
    def fixture(self, slot, kind, trace=()):
        c.integer(slot, 0, 4095)
        c.require(not self._closed and self._active is None, 'suite fixture boundary')
        rows = tuple(row for row in self._fixtures if row[0] == slot)
        c.require(len(rows) == 1 and slot not in self._fixture_seen, 'fixture slot')
        _, _, phase, affected = rows[0]
        begun = frozenset(self._order[:self._started])
        if phase == 'setup':
            c.require(not any(i in begun for i in affected), 'setup after case')
        else:
            c.require(all(i in begun for i in affected) or self._negative, 'early teardown')
        self._trace('FIXTURE_ERROR', kind, trace, fixture=slot)
        self._fixture_seen.add(slot)
        self._negative = True

    @_guard
    def close_suite(self):
        c.require(not self._closed and self._active is None
                  and (self._negative or self._ended == 248), 'suite closure gate')
        self._closed = True

    @_guard
    def finish(self):
        c.require(self._closed and self._active is None, 'footer before suite close')
        self._emit('FOOTER', count=len(self._lines), prefix=self._hash.hexdigest())
        self._complete = True
        return self.facts()

    def raw_bytes(self):
        """Immutable bounded observed prefix, including after sticky refusal."""
        return b''.join(self._lines)

    def facts(self):
        return Facts(len(self._lines), self._started, self._passed, self._ended,
                     self._negative, self._refused, self._closed, self._complete,
                     self._order[self._started:], self._hash.hexdigest())

    def dispatch(self):
        raise c.Refusal('REFUSED_UNADMITTED')
