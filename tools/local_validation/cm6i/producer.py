"""Bounded serial supplied-command model, with no operational authority."""
import hashlib
import json
from types import MappingProxyType
from ..hb1 import common as c
from ..cm6.collection import verify_collection
from .tables import parse_tables

Refusal = c.Refusal
FAULTS = ('NONE', 'PRE_REFUSE', 'POST_REFUSE', 'REENTER_PRE', 'REENTER_POST')
EXCEPTIONS = ('ASSERT', 'EXCEPTION', 'SYSTEM_EXIT', 'KEYBOARD_INTERRUPT')
ARITIES = {'BEGIN': 1, 'START': 2, 'SUB_ENTER': 3, 'SUB_OUTCOME': 6,
           'SUB_EXIT': 3, 'OUTCOME': 5, 'CLEANUP': 2, 'DURATION': 3,
           'END': 2, 'FIXTURE': 4, 'CLOSE_SUITE': 1, 'RESTORED': 1,
           'INPUTS_VERIFIED': 1, 'FINISH': 1}


def _check(): return True

def _encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')

def _digest(value): return hashlib.sha256(value).hexdigest()

def dispatch_runtime(): raise Refusal('REFUSED_UNADMITTED')


class ProducerModel:
    def __init__(self, raw_q, raw_d, raw_c, raw_t, expected_q_pin, expected_d_pin, operation):
        try:
            collected = verify_collection(raw_c, raw_q, raw_d, expected_q_pin, expected_d_pin, operation)
            table = parse_tables(raw_t, raw_q, raw_d, raw_c, expected_q_pin, expected_d_pin, operation)
            self.operation, self.context = operation, collected.context
            self.codes, self.fixtures = table.codes, table.fixtures
            self.input_pins = tuple((len(raw), _digest(raw)) for raw in (raw_q, raw_d, raw_c, raw_t))
            self.order = tuple(range(360))
        except BaseException:
            raise Refusal('INVALID_COMMAND') from None
        self._out = (b'', 0, _digest(b''))
        self.attempts = self.settled = self.in_flight = self.post_footer_attempts = 0
        self.first_refusal = None
        self.refused = False
        self.accounting_complete = True
        self.busy = self.detached = self.footer = False
        self._sealed = None
        self.failure_code = None
        self.stage = 'BEGIN'
        self.active = self.sub = None
        self.sub_state = None
        self.started = self.ended = self.subs = 0
        self.primary = 'NONE'
        self.negative = self.badcase = self.cleanup = self.duration = False
        self.seen = frozenset()

    def _refuse(self, code, ordinal=None):
        self.refused = True
        self.failure_code = code
        if self.accounting_complete and self.first_refusal is None and ordinal is not None:
            self.first_refusal = ordinal

    def _reject(self, code, ordinal=None):
        # Construct the intended fixed exception before recording. Any helper
        # failure, including Refusal after partial mutation, is secondary.
        try:
            intended = Refusal(code)
            self._refuse(code, ordinal)
        except BaseException:
            self.accounting_complete = False
            self.failure_code = 'SECONDARY_FAILURE'
            raise
        raise intended

    def _footer_entry(self, ordinal):
        if self.footer:
            if self.post_footer_attempts >= 65535:
                self.accounting_complete = False
                self._reject('COUNTER_EXHAUSTED', ordinal)
            self.post_footer_attempts += 1
            self._reject('POST_FOOTER', ordinal)

    def _enter(self):
        if not self.accounting_complete or self.attempts >= 65535 or self.in_flight >= 65535:
            self.accounting_complete = False
            self._reject('COUNTER_EXHAUSTED')
        self.attempts += 1
        self.in_flight += 1
        return self.attempts

    def _settle(self):
        if self.settled == 65535 or self.in_flight < 1:
            self.accounting_complete = False
            raise Refusal('COUNTER_EXHAUSTED')
        self.in_flight -= 1
        self.settled += 1

    def _nested(self):
        ordinal = self._enter()
        try:
            self._footer_entry(ordinal)
            self._reject('REENTRY', ordinal)
        finally:
            self._settle()

    def apply(self, command, fault='NONE'):
        if self.detached:
            raise Refusal('DETACHED_ENTRY')
        try:
            ordinal = self._enter()
        except Refusal:
            self.accounting_complete = False
            raise
        except BaseException:
            self.accounting_complete = False
            self.failure_code = 'SECONDARY_FAILURE'
            raise
        owner = False
        try:
            self._footer_entry(ordinal)
            if self.busy: self._reject('REENTRY', ordinal)
            self.busy = owner = True
            if self.refused: self._reject('STICKY_REFUSAL', ordinal)
            if type(fault) is not str or fault not in FAULTS: self._reject('INVALID_FAULT', ordinal)
            if fault == 'PRE_REFUSE': self._reject('PRE_CHECK', ordinal)
            if fault == 'REENTER_PRE':
                try: self._nested()
                except Refusal: pass
                self._reject('STICKY_REFUSAL', ordinal)
            try:
                rows, changes = self._prepare(command)
                self._commit(rows, changes)
            except Refusal as error:
                code = error.args[0] if type(error) is Refusal and len(error.args) == 1 and type(error.args[0]) is str and error.args[0] in ('INVALID_COMMAND', 'INVALID_TRANSITION', 'GROUP_LIMIT') else 'ENCODE_FAILURE'
                self._reject(code, ordinal)
            except BaseException:
                self._reject('ENCODE_FAILURE', ordinal)
            if fault == 'REENTER_POST':
                try: self._nested()
                except Refusal: pass
            if fault == 'POST_REFUSE': self._reject('POST_CHECK', ordinal)
            if self.refused: self._reject('STICKY_REFUSAL', ordinal)
        except Refusal:
            # _reject separates intended Refusal from failure of its helper.
            raise
        except BaseException:
            self.accounting_complete = False
            self.failure_code = 'SECONDARY_FAILURE'
            raise
        finally:
            try: self._settle()
            except BaseException:
                self.accounting_complete = False
                self.failure_code = 'SECONDARY_FAILURE'
                raise
            finally:
                if owner: self.busy = False

    def _prepare(self, cmd):
        if type(cmd) is not tuple or not cmd or type(cmd[0]) is not str or cmd[0] not in ARITIES or len(cmd) != ARITIES[cmd[0]]:
            raise Refusal('INVALID_COMMAND')
        verb = cmd[0]
        def need(ok):
            if not ok: raise Refusal('INVALID_TRANSITION')
        def integer(x, lo, hi): return type(x) is int and lo <= x <= hi
        def row(event, **kw): return (event, kw)
        def trace_rows(event, case, sub, fixture, kind, trace):
            need(type(kind) is str and type(trace) is tuple and len(trace) <= 128)
            zero = event in ('SKIP', 'XPASS') or (event == 'FIXTURE_ERROR' and kind == 'NONE')
            if event in ('PASS', 'SUBPASS'):
                need(kind == 'NONE' and not trace)
                return [row(event, case=case, sub=sub, fixture=fixture)]
            need((zero and kind == 'NONE' and not trace) or
                 (not zero and kind in EXCEPTIONS and 1 <= len(trace) <= 128))
            for pair in trace:
                need(type(pair) is tuple and len(pair) == 2 and integer(pair[0], 0, 65535)
                     and integer(pair[1], 1, 2147483647) and pair in self.codes)
            result = [row(event, case=case, sub=sub, fixture=fixture, kind=kind, count=len(trace))]
            result.extend(row('TRACE', case=case, sub=sub, fixture=fixture, kind=kind,
                              code=pair[0], line=pair[1], count=i) for i, pair in enumerate(trace, 1))
            return result
        changes = {}
        if verb == 'BEGIN':
            need(self.stage == 'BEGIN'); changes['stage'] = 'BODY'
            return [row('HEADER', count=360), row('SUITE_OPEN')], changes
        if verb in ('RESTORED', 'INPUTS_VERIFIED', 'FINISH'):
            required = {'RESTORED':'RESTORE', 'INPUTS_VERIFIED':'VERIFY', 'FINISH':'FOOTER'}
            need(self.stage == required[verb]); changes['stage'] = {'RESTORED':'VERIFY', 'INPUTS_VERIFIED':'FOOTER', 'FINISH':'DONE'}[verb]
            if verb == 'FINISH':
                changes['footer'] = True
                return [row('FOOTER', count=self._out[1], prefix=self._out[2])], changes
            return [row(verb)], changes
        need(self.stage == 'BODY')
        if self.sub is not None:
            need(verb == ('SUB_OUTCOME' if self.sub_state == 'OUTCOME' else 'SUB_EXIT'))
        if verb == 'CLOSE_SUITE':
            need(self.active is None and self.ended == self.started and (self.negative or self.ended == len(self.order)))
            changes['stage'] = 'RESTORE'; return [row('SUITE_CLOSE')], changes
        if verb == 'START':
            case = cmd[1]; need(integer(case, 0, 359) and self.active is None and not self.negative and self.started < len(self.order) and case == self.order[self.started])
            changes.update(active=case, started=self.started+1, primary='NONE', badcase=False, subs=0, cleanup=False, duration=False)
            return [row('CASE_START', case=case)], changes
        if verb == 'FIXTURE':
            slot, kind, trace = cmd[1:]; need(integer(slot, 0, 4095) and self.active is None and slot not in self.seen)
            matches = tuple(r for r in self.fixtures if r[0] == slot); need(len(matches) == 1)
            _, _, phase, affected = matches[0]; begun = frozenset(self.order[:self.started])
            need(not any(i in begun for i in affected) if phase == 'setup' else all(i in begun for i in affected) or self.negative)
            changes.update(seen=self.seen | frozenset((slot,)), negative=True)
            return trace_rows('FIXTURE_ERROR', None, None, slot, kind, trace), changes
        case = cmd[1]; need(integer(case, 0, 359) and self.active is not None and case == self.active)
        if verb == 'SUB_ENTER':
            sub = cmd[2]; need(integer(sub, 1, 4096) and self.sub is None and not self.cleanup and self.primary == 'NONE' and not self.negative and sub == self.subs+1)
            changes.update(sub=sub, sub_state='OUTCOME'); return [row('SUB_ENTER', case=case, sub=sub)], changes
        if verb == 'SUB_OUTCOME':
            _, _, sub, event, kind, trace = cmd; need(type(sub) is int and sub == self.sub and self.sub_state == 'OUTCOME' and type(event) is str and event in ('SUBPASS','SUBFAIL'))
            changes['sub_state'] = 'EXIT'
            if event == 'SUBFAIL': changes.update(negative=True, badcase=True)
            return trace_rows(event, case, sub, None, kind, trace), changes
        if verb == 'SUB_EXIT':
            sub = cmd[2]; need(type(sub) is int and sub == self.sub and self.sub_state == 'EXIT')
            changes.update(sub=None, sub_state=None, subs=self.subs+1); return [row('SUB_EXIT', case=case, sub=sub)], changes
        if verb == 'CLEANUP':
            need(not self.cleanup); changes['cleanup'] = True; return [row('CLEANUP_DONE', case=case)], changes
        if verb == 'DURATION':
            value = cmd[2]; need(self.cleanup and not self.duration and integer(value, 0, 2**63-1)); changes['duration'] = True
            return [row('DURATION', case=case, count=value)], changes
        if verb == 'END':
            need(self.cleanup and self.duration and (self.primary != 'NONE' or self.badcase)); changes.update(active=None, ended=self.ended+1)
            return [row('CASE_END', case=case, count=self.subs)], changes
        if verb == 'OUTCOME':
            _, _, event, kind, trace = cmd; need(type(event) is str and event in ('PASS','FAIL','ERROR','SKIP','XFAIL','XPASS'))
            if event == 'PASS':
                need(self.cleanup and self.duration and self.primary == 'NONE' and not self.negative and not self.badcase); changes['primary'] = 'PASS'
            elif event in ('FAIL','ERROR'):
                need(not self.cleanup and self.primary in ('NONE','SKIP')); changes.update(negative=True, badcase=True)
            else:
                need(self.primary == 'NONE' and not self.badcase and ((not self.cleanup) if event == 'SKIP' else (self.cleanup and self.duration)))
                changes.update(primary=event, negative=True, badcase=True)
            return trace_rows(event, case, None, None, kind, trace), changes
        raise Refusal('INVALID_COMMAND')

    def _commit(self, rows, changes):
        prefix, count, _ = self._out
        lines = []
        for event, fields in rows:
            value = dict(schema='cho51_cm6_event_v1', seq=count+len(lines)+1, op=self.operation,
                         context=self.context, event=event, case=None, sub=None, fixture=None,
                         kind='NONE', code=None, line=None, count=None, prefix=None)
            value.update(fields); line = _encoded(value)
            if len(line) > 512: raise Refusal('GROUP_LIMIT')
            lines.append(line)
        new_count = count + len(lines); data = prefix + b''.join(lines)
        footer = rows[-1][0] == 'FOOTER'
        if new_count > (4096 if footer else 4095) or len(data) > (2097152 if footer else 2097152-512):
            raise Refusal('GROUP_LIMIT')
        bundle = (data, new_count, _digest(data))
        # Prebuild both output and lifecycle changes. No fallible per-field
        # transition follows the single serial-model state replacement.
        state = self.__dict__.copy()
        state.update(changes)
        state['_out'] = bundle
        self.__dict__ = state

    def raw_prefix(self): return self._out[0]

    def facts(self):
        return MappingProxyType(dict(attempts=self.attempts, settled=self.settled, in_flight=self.in_flight,
            post_footer_attempts=self.post_footer_attempts, first_refusal=self.first_refusal, refused=self.refused,
            accounting_complete=self.accounting_complete, failure_code=self.failure_code, busy=self.busy, detached=self.detached,
            records=self._out[1], bytes=len(self._out[0]), sha256=self._out[2], footer=self.footer,
            authenticated=False, execution_accepted=False, debt_discharged=False))

    def seal(self):
        if self._sealed is not None: return self._sealed
        if self.busy or self.in_flight:
            try:
                self._reject('SEAL_ACTIVE', self.attempts if self.in_flight else None)
            except Refusal:
                raise
            except BaseException:
                self.accounting_complete = False
                self.failure_code = 'SECONDARY_FAILURE'
                raise
        try:
            self.detached = True
            terminal = None
            if not self.footer and self.failure_code is None: self.failure_code = 'INCOMPLETE_PREFIX'
            if self.footer and self.accounting_complete and self.attempts and self.attempts == self.settled:
                value = dict(schema='cho51_cm6_supplied_terminal_v1', operation=self.operation,
                    context=self.context, inputs={name: dict(bytes=pin[0], sha256=pin[1]) for name, pin in zip(('cohort', 'descriptor', 'collection', 'tables'), self.input_pins)},
                    events=dict(bytes=len(self._out[0]), sha256=self._out[2]), boundary='SUPPLIED_SEALED_CHANNEL_SNAPSHOT',
                    attempts=self.attempts, settled=self.settled, in_flight=0, post_footer_attempts=self.post_footer_attempts,
                    first_refusal=self.first_refusal, refused=self.refused, producer_detached=True)
                terminal = _encoded(value)
                if len(terminal) > 65536: raise Refusal('GROUP_LIMIT')
            self._sealed = MappingProxyType(dict(raw=self.raw_prefix(), terminal=terminal, facts=self.facts(),
                                                 authenticated=False, execution_accepted=False, debt_discharged=False))
        except BaseException:
            self.accounting_complete = False
            self.failure_code = 'SECONDARY_FAILURE'
            raise
        return self._sealed





