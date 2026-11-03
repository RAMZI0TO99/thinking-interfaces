# CM3 supplied verifier/join implementation contract

2 November 2026. Source-only implementation of the independently accepted
[CM3 design](cho51_p3_cm3_evidence_design_20261102.md). Root owns tables, raw join,
registry, join tests, documentation and every phase record; cm3_events_author owns
the initial event parser/tests and released them for Root integration and review.
A different peer accepts source, and a separate peer reviews metadata closeout.
Preserve the exact 9,304 predecessor inputs and archived 12 current pages.

## Implemented data boundary

The eight-file `tools/local_validation/cm3` package implements the independent
frozen-CM2 event parser, canonical supplied tables and raw evidence join. It
performs no project execution in this phase: no Python/import/parser/AST/compiler,
native calls, tests or Git. Inspection is file/text/JSON/hash and arithmetic only.

verify_events(raw, operation, *, codes=(), fixtures=(), check) consumes exact
immutable bytes and exact immutable primitive table tuples. It never instantiates
CallbackModel, calls CM1's event verifier, coerces old schemas or consumes caller
Facts. All thirteen field/nullability/type rules, sequence, full selected order,
primary/negative/failfast transitions, fixture phase/slot conservation and complete
declared trace groups are checked independently. SKIP then repeated mixed cleanup
FAIL/ERROR remains negative; XFAIL/XPASS forbid later cleanup callbacks under the
frozen CM2 subset. Flat subcases only; unknown/nested/UNSUPPORTED routes refuse.

The unchanged bounds are 4,096 total records, 512 bytes/record, 2 MiB stream,
4,095 nonfooter records / 2,096,640 nonfooter bytes and 128 frames per exception
group. The footer hashes every exact prior record; whole digest stays separate.
hash_bytes uses 64-KiB chunked hashing with checkpoints for exact 1..2-MiB inputs,
without widening frozen HB1's 1-MiB digest helper. Checkpoints remain supplied
calls, not native or continuous enforcement. No malformed or incomplete stream
produces a completed result, repaired bytes or fabricated trace/footer.

Tables have the accepted closed cho51_cm3_supplied_tables_v1 raw schema, 1-MiB
ceiling, at most 4,096 sorted unique code pairs and 4,096 increasing unique fixture
slots. All tuple/list/row fields use exact types, code/line/slot bounds and exact
selected module/class owner matches. Different slots may share owner/phase.
Aggregate byte/depth/node/container bounds still apply: maximum row counts do
not establish that all maximum-sized rows fit the raw envelope.

join_supplied(descriptor_raw, collection_raw, events_raw, tables_raw, *, check)
reparses all four exact byte inputs. It checks the accepted closed 64-KiB
descriptor, raw sizes/hashes and opaque operation/source/runtime/producer context;
then complete CM2 collection before table and event semantics. All 764/32 rows
must pass before retaining the separate CM1 732/30 and HB1 700/28 projection
digests. Collection has no operation field; the descriptor supplies that binding
without proving original same-operation production. Combined input maximum is
4,259,840 bytes, not an allocation or peak-memory proof.

Results are frozen/defensive with unconditional authenticated=False and
execution_accepted=False properties. Observable dispositions are only
SUPPLIED_TRANSCRIPT_CONSISTENT and SUPPLIED_NEGATIVE_TRANSCRIPT. No hidden
cleanup/duration/suite/final-refusal, actual subcase population, actual trace/type
or original custody is inferred. Any runtime dispatch always refuses. A valid
746-record supplied fixture does not prove the actual 1,000-record CM2 mapping.

## Explicit current source roster, separate historical target

The [source roster successor](cho51_p3_cm3_roster_successor_20261102.json) declares
exactly 16 CM3EventTests and 16 CM3JoinTests with literal test-module pins. It
extends full current source to 796 identities / 34 modules, with 280 proposed
selections and the same 516 outside execution. Frozen CM2 remains exactly 764/32
and 248 selected. The parser targets that historical raw schema; it cannot claim
complete current discovery or silently omit the 32 new tests.

No current-roster collection/event schema, producer or runtime integration is
implemented here. Those require an explicit reviewed successor before execution.
The registry has no own digest; tests do not embed their own source/candidate
hashes, so literal test pins do not create a self-hash cycle. Any method identity
change requires new roster/pin/budget review. The declaration gives no permission
to execute a selected or excluded method.

All new methods have zero normal unittest subtest callbacks; plain assertion
loops, assertRaises and synthetic records do not add unittest subtests. With the
earlier 254, a future normal mapping would conditionally be
280*3+254+2=1,096 records / 561,152 bytes. This arithmetic does not implement a
new event wire or establish complete failure/capture/time/memory feasibility.
The frozen CM2 1,000-record result and CM2-design 860-record result keep their
248- and 216-method scopes respectively.

The [source effect/scenario index](cho51_p3_cm3_source_coverage_20261102.json) joins
280 declared method identities to source pins/locations and the new examples to
the 32 design scenarios. These are source examples, not full scenario acceptance.
Real dispatcher/formatting, original lifecycle, capture/native/allocation/clock
scenarios remain unimplemented and unexecuted. No old control or obligation is
replaced by a supplied model assertion.

## Review, publication and next step

Root alone writes the predeclared records under
`runs/coordination/cho51_p3_cm3_implementation_20261102_v1`. Freeze each candidate;
if findings require changes, preserve every affected exact file and manifest
before revision. Independent reviewers publish message-only verdicts, then
confirm Root's saved bytes. Final closeout confirmation stays conversation-only.
Current pages are archived under `docs/history/cm3_implementation_20261102`.

Next is design and review of explicit lifecycle/final-refusal evidence and
current-roster collection/event integration. A real case/suite dispatcher still
needs semantic-equivalence qualification, full recursive failure/effect closure,
original native/provider custody and capture, complete allocation and finite
asynchronous closeout plus time/memory reserves. The original whole90/work60/
cleanup5/hard65/child55 and every resource/stop/ownership/parent guard remain.
Do not execute a parser, test, discovery or old launcher to bypass those gates.

P stays disabled; full Q32/100/384, candidate117/V34 and science stay held. QD
a1f12701 remains INCOMPLETE_REFUSED17/16; consumed attempts and UNKNOWN custody
remain frozen. All 18,793 resolver rows, 13,406 inventory occurrences, 724 queues,
1,782 frontiers, 1,786 loads and 3,972 effects remain open. Complete continuation
remains infeasible at at least 31,002 rows against 24,000; G2 stays refused.
Scientific cells remain 0/1020 and the final freeze is unsigned.
