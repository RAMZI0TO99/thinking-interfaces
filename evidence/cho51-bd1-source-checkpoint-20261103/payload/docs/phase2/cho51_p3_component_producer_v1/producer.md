# Finite supplied producer and refusal kernel

## API and authority boundary

Proposed ProducerModel(operation, codes=(), fixtures=()) holds only exact supplied
primitives and private bounded state. It exposes apply(command, fault='NONE'),
raw_prefix(), facts(), and seal(). No user callable/check hook, filesystem/native
handle, test instance, exception object or dynamic import is accepted. The
constructor validates the frozen CM4 registry and exact immutable tables; it emits
no record and is not a guarded producer attempt. Invalid construction raises a
fixed Refusal with no usable object. A future operational adapter is separate.

command is an exact tuple with the fixed verb and arity below. Every scalar is
the exact CM4 primitive type/range; no coercion, arbitrary attribute lookup,
formatting, class-name conversion or fallback text result. Trace is an immutable
tuple of exact known (code,line) pairs, innermost-first,1..128 frames on exception
routes; tuple() on zero-trace routes. Tables and their aggregate limits are
validated before views. Frozen CM4 parser code is not the producer's state engine.

| Command tuple | Declared effect |
| --- | --- |
| ('BEGIN',) | HEADER and SUITE_OPEN; once and before any case/fixture |
| ('START',case) | Exact next selected CASE_START |
| ('SUB_ENTER',case,sub) | Open next flat subcase |
| ('SUB_OUTCOME',case,sub,event,kind,trace) | SUBPASS/SUBFAIL and complete trace group |
| ('SUB_EXIT',case,sub) | Close matching outcome/trace interval |
| ('OUTCOME',case,event,kind,trace) | PASS/FAIL/ERROR/SKIP/XFAIL/XPASS and complete trace group |
| ('CLEANUP',case) | CLEANUP_DONE claim |
| ('DURATION',case,value) | Required supplied integer duration claim |
| ('END',case) | CASE_END with internally derived completed subcase count |
| ('FIXTURE',slot,kind,trace) | Unique exact owner/phase fixture failure/skip group |
| ('CLOSE_SUITE',) | SUITE_CLOSE claim |
| ('RESTORED',) | Restoration claim |
| ('INPUTS_VERIFIED',) | Final-input claim |
| ('FINISH',) | One FOOTER over exact prior bytes; final ordinary producing command |

State independently enforces every CM4 transition, including D01's closed
SUB_ENTER/outcome/immediate trace/SUB_EXIT interval. Failures do not fabricate a
primary FAIL for SUBFAIL. First negative prevents new cases/subcases but allows
the declared active lifecycle and suite cleanup. Cleanup/duration are mandatory
before END; PASS cannot precede either. SKIP may precede mixed cleanup failures;
XFAIL/XPASS require cleanup/duration and prohibit later case failures. Final
suite/restoration/input claims precede FINISH. These are supplied declarations,
not original execution. The whole raw output must independently pass CM4 parsing
before even a supplied join can be consistent.

## Entry, refusal and settlement

Private state includes lifecycle, exact prefix bytes/hash/record count; attempts,
settled,in_flight,post_footer_attempts; first_refusal or null; sticky refused;
accounting_complete; busy; detached; and an immutable sealed value or none.
All counters have the existing0..65535 range. An admitted attempt increments
attempts and in_flight before checking busy, sticky state, command shape or
pre-check outcome. Invalid commands and calls after refusal are still attempts.
If a FOOTER already exists on entry, increment post_footer_attempts and refuse,
including malformed calls; no further event is emitted.

For each representable attempt, settlement occurs exactly once in finally:
in_flight decreases, settled increases. Normal outer entry sets busy until its
own final settlement; rejected reentry must not clear the outer busy flag.
Invariant attempts=settled+in_flight holds after every represented transition.
The first refusal stores the ordinal of the attempt that first *observed* a
refusal, not the minimum ordinal that eventually fails. Example: outer attempt1,
reentry attempt2 refuses first; outer settlement later fails too, but first_refusal
stays2. Swallowing the inner exception cannot clear the latch; the outer post-check
must observe it before success. Every refusal has a fixed enum, not str(error).

fault is exactly NONE, PRE_REFUSE, POST_REFUSE, REENTER_PRE or REENTER_POST.
It is supplied data consumed once per outer apply; no script or callable runs.
PRE_REFUSE stops before output. POST_REFUSE occurs after the complete command's
output commit. REENTER_* simulates exactly one additional entry while busy; that
entry is counted, refused and settled immediately without running a command or
another fault script. The outer attempt then refuses. Maximum modeled in_flight
is2; this is not a proof of real thread/reentry behavior. Invalid fault values
also refuse within the counted outer attempt. No model thread or wait is added.
REENTER_PRE's newly latched refusal must be observed before any output commit;
REENTER_POST preserves the already committed output and still refuses the outer
attempt. Neither injection is a second application of the original command.

Unexpected encoder/hash/allocation BaseException also latches refusal and settles
the entered attempt without formatting the exception. Failure while recording
that refusal must not recursively invoke the producer or manufacture a terminal;
retain whatever bounded state is available and let the outer result be incomplete.
No finite Python allocation reserve or guaranteed runtime error-report success is
established by this model contract.

The closed model failure codes are INVALID_COMMAND, INVALID_FAULT,
INVALID_TRANSITION, PRE_CHECK, POST_CHECK, REENTRY, STICKY_REFUSAL, POST_FOOTER,
COUNTER_EXHAUSTED, GROUP_LIMIT, ENCODE_FAILURE, SEAL_ACTIVE, DETACHED_ENTRY,
INCOMPLETE_PREFIX and SECONDARY_FAILURE. No arbitrary exception payload is copied.
facts() is an immutable diagnostic view of known counters/flags and the last
committed prefix, including accounting_complete; it is never a terminal or an
execution grant. If an unexpected failure prevents a complete accounting update,
mark accounting incomplete and return no completed terminal rather than assert
the normal invariant for an unrepresented entry. Failure while marking/refusing
is an outer incomplete result, not an exception to runtime resource guards.

After pre-check succeeds, validate the full command and reserve its entire
encoded group before committing any bytes. A single negative command may emit
129 records (outcome plus128 traces); preencode at most66,048 bytes. Enforce both
remaining record and byte budgets, preserving the footer reservation. Commit the
complete group using one prebuilt immutable output-state bundle (prefix, count
and digest) and one private reference replacement, then perform the post-check.
Prepare all encoding/hash/copy work before that replacement; no partially updated
output bundle is reportable. Whole-prefix copies remain chargeable allocations.
This is a single-thread model contract, not native publication atomicity. If the
post-check refuses, keep those exact committed bytes and latch refusal; never
roll them back or repair the transcript. FINISH commits a footer before its
post-check, so a valid footer can coexist with a final refusal.

Refusal forbids further output; it does not manufacture cleanup, END, suite close
or FOOTER to make a prefix acceptable. raw_prefix() returns only an immutable copy
of the retained prefix. An interrupted/incomplete prefix remains incomplete, even
if owned outer cleanup later succeeds. No partial file/stream commit semantics
are inferred from the model's in-memory group commit.

## Overflow and seal

Before an unrepresentable increment (including the65536th entry), set
accounting_complete=false and refuse permanently. Do not wrap, clamp and claim
complete counts, overwrite a first refusal or invent an in-range ordinal for the
unrecorded call. Retain exact available prefix and known counters with explicit
incomplete accounting; no CM4 terminal snapshot is available. Bounded failure
facts can carry a fixed COUNTER_EXHAUSTED enum and accounting_complete=false,
but are not completed terminal/join facts. Real ingress must enforce a finite
attempt budget independently; the model ceiling alone cannot bound an attacker.

seal() is an explicit controller transition, not a producer command or callback:
it emits no event, performs no user hook and is not counted in attempts or
post_footer_attempts. It first requires no busy/in-flight activity and closes
future model entry. Repeated seal returns the same immutable value with no new
work. Reentrant seal refuses without returning a value and latches the active
attempt's refusal. A complete snapshot is possible only with exact accounting,
at least one settled attempt, detached=true, and a complete existing footer.
Its raw fields exactly follow CM4 terminal.py, with the whole event byte pin and
final sticky state after the last producer post-check. Refused=true is preserved.

If no complete footer or accounting is incomplete, seal returns bounded model
failure facts and available prefix, never a forged terminal. A rejected apply
after detachment raises a fixed detached-entry refusal without mutating the sealed
value/counters. It is explicitly outside that snapshot's supplied observation
boundary; an outer harness must record its own failure and cannot present the
old snapshot as evidence of no later call. This matches CM4's unavailable
future-activity claim. It is not a real capability-revocation mechanism.

All facts/snapshots are defensive immutable values, authenticated=False and
execution_accepted=False unconditionally. Runtime dispatch always refuses.
Independent CM4 parsing must be invoked on original returned bytes, never on
producer Facts; negative terminal cannot be erased by all-PASS event bytes.
