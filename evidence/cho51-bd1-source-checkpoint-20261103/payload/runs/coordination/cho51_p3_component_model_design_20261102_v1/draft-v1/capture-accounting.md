# CM1 finite events, complete capture and parent accounting

## Bounded primary event representation

The old TextTestResult formats exceptions before BoundedText checks writes.
The pinned stdlib reference calls _exc_info_to_string in error, failure,
subtest and expected-failure callbacks, then materializes formatted traceback
text. A new CM1 TestResult must override every outcome path without calling
those superclass formatters: start/stop, success/failure/error, subtest, skip,
expected failure/unexpected success, fixture _ErrorHolder and duration callbacks.
Set buffer=False. No runner-side str/repr of exception/test/subtest objects,
traceback formatter, locals capture or linecache lookup is permitted.

The proposed event body is a closed ASCII JSON record with exactly schema, seq,
op, roster, event, case, sub, fixture, kind, code, line, count and prefix.
schema is cho51_cm1_event_v1; seq is exact integer1..4096; op is the canonical
operation UUID; roster is the exact64-hex full-roster digest. No duplicate keys,
unknown fields, floats, non-ASCII text or noncanonical spelling is accepted.
Every line ends with one LF and has no other literal control bytes.

| Field | Closed value/meaning |
| --- | --- |
| event | HEADER, CASE_START, PASS, FAIL, ERROR, SKIP, XFAIL, XPASS, SUBPASS, SUBFAIL, FIXTURE_ERROR, TRACE, CASE_END or FOOTER |
| case | Original full-roster ordinal0..731, or null for a module/class fixture or header/footer; execution ordinals must belong to the exact216 selection |
| sub | Per-case subtest ordinal1..4096 for SUBPASS/SUBFAIL and their TRACE records; otherwise null |
| fixture | Frozen fixture-table index0..4095 for fixture failures/traces; otherwise null. The table joins exact module/class owner and setup/teardown/cleanup phase, not arbitrary text |
| kind | NONE, ASSERT, EXCEPTION, SYSTEM_EXIT, KEYBOARD_INTERRUPT or UNSUPPORTED; exact exception-class identity maps to the frozen table, never a user-defined class-name conversion |
| code, line | Frozen code-table ordinal0..65535 and exact positive line<=2147483647 for TRACE only; otherwise null |
| count | HEADER: expected selected count216; CASE_END: observed subtest count; FOOTER: prior event count; otherwise null |
| prefix | FOOTER only: SHA256 of every exact prior event line, excluding the footer. Otherwise null; the external result separately pins the whole file |

The event-specific nullability and transitions are mandatory. HEADER is first,
FOOTER is last, and seq is contiguous. TRACE records immediately follow their
failure event and preserve every frame in innermost-to-outermost order under a
proposed128-frame ceiling; no frame is silently dropped. The source-derived
trace-depth proof remains required. Unknown code/fixture references or a body
that does not fit refuse; no generic arbitrary string payload is allowed.

The primary format records the exact test index, subcase ordinal, event enum,
bounded exception-type enum and pinned code-location indexes.
It never embeds arbitrary messages, object graphs or a caller-defined test ID.
Locations come directly from bounded traceback/code objects and the retained
source/code table; unsupported objects, missing locations, extra frames or
unexpected callbacks produce a refusal, never a truncated successful report.
Code records must distinguish module/class fixture failures from a method result.
Automatic unittest duration floats are not live timing evidence; original native
clock observations remain separate. Skip/xfail/unexpected success always fails
component eligibility, including suite-fixture SkipTest routes.

One record is at most512 encoded bytes including its LF; the proposed event
ceiling is4096, giving2,097,152 bytes. This is a refusal ceiling, not an assertion
that all216 methods and subcases fit. Before admission, the complete source
table must derive every possible normal/failure callback, subcase/fixture count,
traceback depth and code-location bound and prove the ceiling sufficient. The
current trace has not completed that proof. Unknown/unbounded rows block
admission; do not accept a prefix, drop a subcase or increase the cap silently.
Static compact-ASCII JSON arithmetic for an overestimate with every nullable
field populated at its maximum is372 bytes including LF. Actual event-specific
nullability reduces that size. This verifies only the declared data envelope;
the implementation/serializer and complete event-count proof remain unqualified.

The event verifier conserves each selected index exactly once: one start and
one CASE_END after test cleanup, with every subcase and fixture event
joined to its parent. Failure/error/skip/expected/unexpected outcome is sticky.
The reviewed runner uses failfast=True: the first failed outcome requests stop;
the current test's bounded teardown/cleanups and event finalization still run.
Further selected methods do not start, and the attempt is refused, never accepted
as216 passes. An early fixture error accounts for all selected cases that could
not run as not-started due to that exact failure; it never invents their completion. Missing,
reordered, duplicate, unjoined, unknown or postterminal events refuse. A final
summary binds full collection, selection and all event digests/counts. It cannot
assert success independently of the original complete byte streams and closure.

This grammar represents the declared result semantics, not an exception's
arbitrary memory graph. It prevents the runner from generating unbounded
diagnostic formatting; it does not remove assertion-internal formatting, standard
suite SkipTest stringification, interpreter startup/uncaught messages, native
compiler/loader errors, raw writes or tool envelopes. Those remain in the
complete capture proof. A separately reviewed suite successor may be needed
for any formatting path that cannot be bounded without changing obligations.

## Complete original stream and tool capture

Capture stdout/stderr independently outside the mocked interpreter as exact
bytes, before decoding or newline normalization. Preserve each original chunk,
order and stream identity; reject uncertainty rather than guessing encoding.
Both existing1MiB stream ceilings remain. Source-derived finite producer bounds
must prove that every allowed success/failure path fits; the ceilings themselves
do not prove complete output. A capture failure consumes and refuses, preserving
partial evidence and bounded cleanup, not an accepted truncated result.

The proposed controller returns a small closed ASCII completion descriptor with
operation, artifact pins, bounded enum disposition and original native integer
text. This separates stored child reports from the command's actual return; it
does not permit replacing, summarizing or omitting the original external tool
return. Preserve that original return and all its envelopes/chunks exactly in
the unchanged raw_tool_return1MiB and external_return65536 slots. Known report
file bounds do not bound pre-entry, startup, cancellation or wrapper/tool errors.

The existing counterexample still applies:1MiB of permitted control characters
can need6,291,456 escaped JSON string bytes before envelopes. A successful small
return is not proof for all failures. The actual producer/transport grammar and
escaping must be frozen and bounded before runtime admission. No raw cap is
reduced, evidence truncated, unaccounted sidecar added or exception text exported
outside the parent ledger to make this fit. Complete capture feasibility is
NOT_ESTABLISHED; this design does not close that gate.

## Typed parent accounting and conditional report reservations

The proposed runtime stage is COMPONENT_MODEL, with distinct unused parent and
metadata UUIDs and fixture_publication=null. Model-native fixture paths remain
strings; do not create HB1's unadmitted model namespace or patch SC1's PHASE.
CM1 needs a separately source-reviewed fixed operational namespace and typed
parent validator; frozen HB1.parse_join is not a production path adapter.

The report-only reservation proposal below is a finite lower-bound inventory,
not a complete executable allocation. It gives concrete size requirements for
implementation without pretending that native/bootstrap/compiler artifacts
have already been enumerated. Every later necessary artifact must receive an
exact path, publisher, partition, cap and transaction before effects. Unnamed
temporary/compiler/cache/export files are not allowed, even under aggregate caps.

| Partition | Proposed report artifact | Reserved bytes |
| --- | --- | ---: |
| caller | full collection JSON |1048576|
| caller | complete event stream |2097152|
| caller | raw child stdout |1048576|
| caller | raw child stderr |1048576|
| caller | original caller return |65536|
| caller | caller journal |131072|
| caller | complete input inventory |4194304|
| caller | guard/closure observations |131072|
| supervisor | retained input manifest |4194304|
| supervisor | supervisor journal |131072|
| supervisor | exact command descriptor |65536|
| supervisor | complete output census |131072|
| supervisor | loaded-code joins |65536|
| supervisor | original return/closure |65536|
| closeout | unchanged16 SC1 roles |3293184|

This minimum is30 files/17,711,104 bytes: caller8/9,764,864,
supervisor6/4,653,056 and closeout16/3,293,184. Fixtures currently has zero model
report writes, not a reduced global fixture cap or proof that all test effects
are zero. The exact recursive effect map must settle that before admission.
Any necessary native/bootstrap additions must fit the unchanged partitions;
the minimum inventory alone cannot admit compilation or a runner.

Keep global256/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB and original per-file8MiB. All16 role names/caps remain, including
3293184 reserved bytes and embedded confirmations; unused/failed/partial slots
retain full charges. The complete actual parent allocation must fit its original
allocation/admission envelope and independently approved acyclic authority/join
pins. No auxiliary map file or borrowed metadata slot is introduced.

Full native parent conservation precedes all views. Every partial create,
failure, copy, unexpected writer, off-directory artifact and unused reservation
must remain accounted. The child cannot certify its own complete domain. Actual
provider/observer evidence, atomic consumption, original producer closure and
preclaim approval remain unavailable. The frozen SC1 transaction also lacks the
required asynchronous review handoff; no clock reset, failed resume, prewritten
actual review or borrowed C-export window resolves it. A qualified finite
lifecycle is required before invoking any live publisher. P remains disabled.
