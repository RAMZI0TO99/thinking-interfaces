# Nonformatting production, suite lifecycle and evidence aggregation

## Callback semantics

Retain CM1's closed 13 fields, 4,096 records, 512 bytes/record, 2 MiB event report,
128 frames/group, exact roster ordinals and deterministic canonical ASCII bytes.
Use a new result/suite adapter; never invoke frozen TextTestResult/TextTestRunner.
The pinned unittest reference shows this per-case order:

startTest -> setup -> body -> teardown -> LIFO method cleanups -> addDuration ->
addSuccess/expected-failure callback -> stopTest. Setup failure omits body and
teardown but still runs method cleanups. Decorated skips return before duration;
stopTest is still in finally. Class/module teardown and cleanup occur later in
the suite and may fail after individual case PASS/end records.

Therefore a PASS is a provisional primary *case* outcome after its method
cleanup, never component acceptance. CM1 already makes later FIXTURE_ERROR
sticky; the footer/aggregate cannot accept until all suite fixture cleanup and
final checks finish. Do not defer CASE_END to invent a different callback order.
No successful suite fixture emits an extra event in the proposed normal mapping.

Override every result callback: start/stop, success/failure/error, subtest, skip,
expected-failure/unexpected-success, duration and suite fixture errors. Keep
buffer=False and failfast=True. Duration is discarded as non-authoritative test
data or checked against a finite declared route; never call str(test), collect
unbounded duration tuples or use Python duration floats as native time evidence.
The adapter may not invoke superclass traceback formatters, linecache, locals
capture, exception names/repr/str, test.id or subtest descriptions.

On a successful subTest, emit exactly one SUBPASS using a bounded per-case
ordinal, without copying parameter/message values. Expected assertRaises catches
are internal to the test and do not emit failure events. The 210 counted normal
subtests assume those contexts succeed. Nested subtests need an explicit finite
entry/unwind map: inner failure suppresses enclosing success, and failfast uses
both result.shouldStop and _ShouldStop propagation. Unknown nested or in-case
fixture order stays refused; it is not silently flattened or omitted.

## Source-level effects beyond result callbacks

Replacing TestResult alone is insufficient. The pinned case executor formats
SkipTest with str(e) before addSkip; the suite does likewise for fixture SkipTest
and constructs _ErrorHolder textual descriptions. A new, separately reviewed
case/suite boundary must retain the exact callback and cleanup semantics while
mapping those paths directly to original object/fixture slots. Do not monkeypatch
unittest or frozen project classes during execution. If an original TestCase.run
route cannot meet the no-preformat contract, it remains unavailable; a separately
versioned dispatcher needs explicit semantic-equivalence qualification before use.

There are also assertion-internal formatting, mock diagnostics and helper catches.
SC1 NativeBackend.write_new formats str(error) or str(primary) before slicing;
close() has the same issue. Exact selected doubles mostly use short fixed
messages, but the generic helper has no bound on arbitrary exception formatting.
This is a required exception-domain proof or reviewed successor decision, not
evidence that the selected normal path itself overflows. CM2 neither rewrites
SC1 nor excuses its formatting from the complete effect/capture inventory.

## Trace and outcome producer

Map exception *type identity* to the reviewed finite kind table. Use only
retained code-object identities and exact permitted line locations. Do not look
up arbitrary __name__ or render values. At most 128 checked traceback references
may be retained before reversal into innermost-to-outermost order; validate every
frame against the code table before emitting its declared group. CM1's supplied
location table has at most 4,096 pairs with code ordinals 0..65,535. Exact runtime
code/line coverage and depth sufficiency must fit that existing implementation.
Counts and JSON cannot prove that actual traceback traversal was complete.

Every FAIL/ERROR/SUBFAIL/XFAIL or fixture exception emits its actual callback and
complete trace group; explicit skip/XPASS NONE/zero and malformed UNSUPPORTED/zero
routes retain their refusal meaning. Multiple cleanup errors remain separate.
Do not manufacture a FAIL after SUBFAIL or invent starts/ends for fixture-blocked
cases. Preserve unseen ordinals from the immutable selection.

A sticky producer refusal survives exceptions caught by unittest. Cap exhaustion,
unknown type/code/fixture, restoration drift or a swallowed callback refusal
prevents footer acceptance and further cases. Preserve the exact bounded prefix
and a separately attributed original refusal record; no successful truncated
report or new clock is allowed. Interrupts that bypass a result callback cannot
be relabelled as observed callbacks: missing outcome/stop/footer is incomplete.
The independent owner performs only the original bounded cleanup on failure.

## Final aggregate and original evidence

The future aggregator is outside the mocked interpreter. It must bind, in order:

1. Original unused operation/authority/source/runtime/producer-map identity and
   native guard/retained-handle witnesses, established before effects.
2. Complete exact actual 732/30 collection and its canonical raw digest, unchanged
   HB1 projection digest, exact selected216 digest and actual object/code joins.
3. Original event bytes/digest, contiguous prefix/footer, all 216 starts/PASS/ends,
   all observed subcases, complete suite fixture closure and no negative latch.
4. Exact external stdout/stderr chunk order and complete original caller/tool
   return, with full input/final source verification and importer/mock restoration.
5. Full attributed parent census before any projections, failed/partial/unused
   charges, original process/Job/pipe/handle closure, publication barriers and
   separate actual review in the finite original lifecycle.

Only all of these can support COMPONENT_MODEL_ONLY. Exit0, model facts, native
identity strings, independently successful fragments or a child self-report
cannot. No adapter may turn CM1 Facts/CollectionFacts/GuardFacts into a live
capability. Until the actual native/provider/lifecycle/capture prerequisites are
implemented and qualified, the operational entry is REFUSED_UNADMITTED.
