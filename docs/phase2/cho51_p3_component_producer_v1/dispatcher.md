# Original dispatcher lifecycle mapping and refusal boundary

This is an obligation contract for a future independently reviewed dispatcher,
not a runnable replacement or permission to call a test. Reference anchors and
hashes are in effect-map.json; the retained unittest files are reference-only,
not fresh runtime/custody pins. Current full836/36 collection and exact320
selection must precede any future dispatch;516 excluded cases still belong to
the census. Discovery cannot run outside the original clock or admission.

## Reference case and suite obligations

| Reference route | Required mapping and disposition |
| --- | --- |
| Ordinary case | startTest; setup; body if setup succeeds; teardown after body route; LIFO method cleanups; duration; success/expected outcome; stopTest finally. Emit PASS only after cleanup/duration, END only after the matching stop lifecycle is known complete |
| Setup error | Body and teardown omitted as in the reference; method cleanups still attempted, duration if reference reaches it, then stopTest. Preserve actual failure callbacks and refuse incomplete lifecycle; no fabricated body/teardown |
| Body failure/skip or teardown error | Preserve each actual callback, allow cleanup failures, stop later case/subcase entries under failfast; complete only the reference's remaining bounded cleanup path |
| Decorated early skip | Reference returns before method cleanup/duration. CM4 cannot represent a complete ended case on this route; refuse the operation without synthesized CLEANUP_DONE/DURATION/END |
| KeyboardInterrupt in a test part | Reference rethrows, potentially skipping cleanup/duration while finally calls stopTest. Preserve interruption/owned cleanup disposition; do not convert it to an ordinary CM4 completed ERROR solely because a primitive enum exists |
| SystemExit in a test part | Reference bare-except route differs from KeyboardInterrupt; do not combine their original behavior merely because both have event enums. Exact source/domain and trace mapping still required |
| Flat subtest | Original entry, one actual result and unwind must be mapped in order. Success/failure plus complete trace precedes SUB_EXIT; no parent callback interposes in the CM4 interval |
| Nested subtest/failfast _ShouldStop | Reference may unwind an outer context without emitting its result. Current CM4 flat triplets cannot represent that route. Refuse before real admission if reachable; never flatten, synthesize SUBPASS or suppress the obligation |
| Class/module setup failure | Use exact source-derived owner and affected set; cases may never start. Preserve actual fixture error/skip cardinality, then the reference's own cleanup routes |
| Late class/module teardown or cleanup | Runs before suite closure even after all case PASS events or failfast break; preserve every emitted callback with a distinct predeclared slot. Negative overall disposition does not rewrite earlier PASS |
| Class/module BaseException escape | Exception-only cleanup catches differ from case test-part handling. Missing suite closure/duration cannot be repaired by a producer; consume/refuse and preserve original available evidence |

Fixture setup/teardown and cleanups do not necessarily emit an outcome on success.
No synthetic success callback is added. Method/class cleanup order is LIFO.
Module cleanup may execute several callbacks yet emit only its first captured
exception; preserve the exact original semantics instead of changing the suite
to an all-errors reporter. A fixture table declares expected slots/owners, not
evidence that all actual boundaries occurred. Unknown/exhausted slots refuse.

Expected failures, unexpected successes and skips remain negative eligibility.
The CM4 wire's deliberate required-duration/flat-subcase subset is not an
equivalence proof for unittest. No source change to a historical case, narrower
selection, skipped failure route or negative-label substitution silently closes
these gaps. A reachable unsupported path blocks real admission, even if a normal
success run would avoid it. If an unexpected path occurs after effects, consume
and use only reviewed original owned cleanup; never retry under a new UUID.

## Bounded dispatch interface and proof obligations

A future original dispatcher must use an exact source/runtime/code/type inventory
and a finite per-case phase plan. Each setup/body/teardown/cleanup/subcase/fixture
entry joins its exact method/code owner, source location and effect-map obligation;
each actual exit records complete or interrupted status. No arbitrary string
name lookup, _ErrorHolder-derived owner or exception repr/str is an authority.
The next supplied model may accept primitive commands only; it cannot invoke this
future phase plan or mark a real phase complete. Original callbacks are not model
commands until a separately qualified adapter establishes the mapping.

Every reachable failure needs finite input/type/message/recursion bounds and
intermediate allocation/output/effect bounds **before** invoking helpers. A
nonformatting result adapter does not stop upstream SkipTest str(e), assertion
pprint/difflib/repr, mock diagnostics, duration str(test), parser/native error
formatting or interpreter/tool failures. Removing those effects requires a
separately reviewed semantic/scope decision and qualification; it is not silently
equivalent to the pinned reference, especially if formatting itself raises or
reenters. No superclass TextTestResult/TextTestRunner fallback or monkeypatch of
frozen classes is permitted to fill a missing route.

Boundary/resource enforcement remains outside tested mutable globals and mocks.
Raw original exception/type/code/trace traversal must be bounded and witnessed;
primitive enums/pairs in supplied tables prove neither identity nor completeness.
The fixed trace128/record4096 caps are refusal ceilings, not sufficient bounds on
all original paths. Restoration and final input verification are separate original
witnesses; their event names alone do not prove them. Source review, model tests,
actual semantic-equivalence qualification and accepted real cases stay distinct.
