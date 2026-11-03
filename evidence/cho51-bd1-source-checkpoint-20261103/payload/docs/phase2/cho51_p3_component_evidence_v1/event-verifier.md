# Independent verification of observable CM2 event bytes

## Inputs and parsing boundary

Proposed API: verify_events(raw, operation, *, codes, fixtures, check). It takes
exact immutable bytes and primitive immutable tables. It shares no mutable state
or acceptance function with CM2 CallbackModel. Reparse every supplied input; a
Facts instance, callback history, cached digest or producer's success boolean is
not evidence. Source acceptance and later execution qualification are separate.

The fixed target is cho51_cm2_event_v1, the frozen 764-identity registry and exact
248 selection. Verify literal roster and selection digests before interpreting
case ordinals. Refuse unsupported schema/roster; do not rewrite ordinals or
project event bytes to CM1. The frozen CM1 protocol is not a CM2 validator.

Require exact bytes, 1..2,097,152 bytes, complete ASCII/LF records, 2..4,096 records
and at most 512 bytes per record including LF. Scan bounded line intervals before
decoding; no unbounded split or arbitrary error formatting. Reject duplicate keys,
noncanonical ordering/spacing/escapes, CR, missing final LF, unknown fields, floats,
NaN, bool-as-integer and trailing bytes. Use strict per-line canonical JSON with
the unchanged thirteen fields: schema, seq, op, roster, event, case, sub, fixture,
kind, code, line, count, prefix. seq is contiguous exact integer 1..4,096; op is
the supplied canonical nonzero UUID; roster is the frozen full-roster SHA256.

The event hasher must process up to 2 MiB in bounded chunks with checkpoints.
HB1 common.digest accepts at most 1 MiB and cannot hash this whole stream. The
successor needs its own reviewed bounded streaming hash, without widening HB1.
Checkpoints remain supplied calls, not continuous/native resource enforcement.

## Exact fields and projected state

All unused fields are null. kind is NONE unless a declared exception route.
case is an exact selected full ordinal 0..763. sub is exact integer 1..4,096;
fixture is an exact declared slot 0..4,095. An applicable count is an exact
integer, never bool. The table grammar and context join are in
[evidence-join.md](evidence-join.md).

State contains active case or null; started/passed/ended counts; per-case subcount;
primary in NONE/PASS/SKIP/XFAIL/XPASS; case-negative and sticky global-negative
bits; seen fixture slots; pending trace group; and incremental prefix/whole hashes.
Do not invent a cleanup-complete or suite-closed state from the raw bytes.

| Event | Observable required condition and update |
| --- | --- |
| HEADER | First and unique; count=248, kind=NONE; every owner, location and prefix null |
| CASE_START | No active case, pending trace or sticky negative; exact next selected ordinal; all ancillary fields null; reset primary, case-negative and subcount |
| SUBPASS | Active exact owner, primary NONE and no sticky negative; next sub ordinal; kind=NONE/count=null; increment subcount |
| SUBFAIL | Same start conditions as SUBPASS; complete exception group; increment subcount and set both negative bits; it does not synthesize a parent FAIL |
| PASS | Active exact owner, primary NONE and neither negative bit; no sub/fixture/count/location; set primary PASS and increment passed |
| FAIL or ERROR | Active exact owner; primary NONE or SKIP only; complete exception group; set both negative bits. Repeated mixed failures remain distinct. No post-PASS/XFAIL/XPASS negative callback |
| SKIP | Active exact owner, primary NONE and no case-negative; kind=NONE/count=0; set primary SKIP and both negative bits. Later FAIL/ERROR cleanup callbacks may follow |
| XFAIL | Active exact owner, primary NONE and no case-negative; complete exception group; set primary XFAIL and both negative bits |
| XPASS | Same primary conditions as XFAIL; kind=NONE/count=0; set primary XPASS and both negative bits |
| CASE_END | Active exact owner; no trace; primary is present OR case-negative is true; count equals subcount; kind=NONE; clear active and increment ended. Do not use primary XOR negative: SKIP/XFAIL/XPASS set both |
| FIXTURE_ERROR | Outside an active case; exact unused fixture slot, case/sub null; complete exception group or NONE/count=0 fixture skip; phase and affected-set checks below; set sticky negative |
| FOOTER | Last and unique; no active case/pending trace; ended=started; either sticky negative or all 248 ended. All owner/location fields null, kind=NONE, count=number of prior records, prefix=SHA256 of exact prior lines excluding footer |

No new case or subcase follows the first negative callback. An already active
case may record its permitted cleanup failures and END. This models the visible
CM2 subset only: flat sequential subtests. Nested/unmapped callbacks remain
unavailable; their execution cannot be made equivalent by dropping records.

For a setup fixture, none of its affected selected cases may have begun. For
teardown/cleanup, all affected cases must have begun unless a sticky negative
already exists. Distinct slots can share owner and phase for repeated cleanup
failures; a slot cannot recur. Actual fixture execution order and count are not
authenticated by a caller-supplied table.

FAIL/ERROR/SUBFAIL/XFAIL and exception fixture routes require kind in ASSERT,
EXCEPTION,SYSTEM_EXIT,KEYBOARD_INTERRUPT and count 1..128. SKIP, XPASS and fixture
skip require NONE/count=0. CM2 does not emit UNSUPPORTED: that route refuses
before a complete group. Refuse UNSUPPORTED and all unknown event/kind values;
do not import the older CM1 refusal-record semantics.

Exactly count immediately contiguous TRACE records follow each exception event.
They retain the parent's exact case/sub/fixture nullability and kind, use exact
integer code/line pairs in the supplied table, and count=1..N. prefix is null.
There is no intervening event, extra trace or owner substitution. Locations have
code 0..65,535 and line 1..2,147,483,647. Sequence preserves the supplied
innermost-first order, but membership alone cannot detect a reordered *real*
traceback or prove traversal completeness: actual object witnesses are absent.

Only the last record may consume the reserved footer record/512 bytes. The
nonfooter prefix cannot exceed 4,095 records or 2,096,640 bytes. Missing footer,
partial line/group, over-limit input or any semantic discrepancy raises a fixed
bounded refusal. Preserve caller-held original bytes; do not fabricate an END,
footer, repaired transcript or successful truncated result.

## Results and non-observable facts

A completed verifier result is immutable and defensive, containing raw whole
digest, prefix digest, record/start/PASS/end/subcase counts, sticky negative,
not-started ordinals from the frozen selection, and one of:

- SUPPLIED_TRANSCRIPT_CONSISTENT: all 248 started/PASS/ended, no observed negative.
- SUPPLIED_NEGATIVE_TRANSCRIPT: structurally complete footer and visible negative;
  possibly a remaining immutable selection suffix. Never successful eligibility.

Malformed/incomplete/cap cases return no success Facts and raise Refusal; an outer
failure record may label INCOMPLETE_REFUSED without modifying original bytes.
Neither successful disposition is named accepted, authenticated or execution
success. authenticated=False and execution_accepted=False are unconditional;
operational dispatch always raises REFUSED_UNADMITTED.

Explicit unavailable facts are method cleanup completion, duration ordering,
suite closure, final producer refusal latch, native guard effectiveness, original
trace/type identity and original source/transport custody. A complete all-PASS
746-record synthetic CM2 fixture may be protocol-consistent; it is not proof of
the conditional 1,000-record actual normal mapping. Missing observed subcases
cannot be diagnosed solely from CASE_END's self-declared count. Runtime acceptance
requires separately reviewed actual subcase/lifecycle witnesses and effect closure.

In particular, a refusal after finish can leave exactly the same event bytes.
The independent parser must give the same observable result for identical bytes
and must not claim to detect that hidden state. Any supplied final-state assertion
is separately attributed and remains unauthenticated; it cannot upgrade this API.
