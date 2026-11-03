# CM3 independent supplied-event parser and evidence join

2 November 2026. **Eight-file implementation independently accepted for source
only, with no findings.** The [package](../../tools/local_validation/cm3/README.md)
implements the accepted CM3 event parser, canonical supplied tables and raw
collection/event/table join under the
[implementation contract](cho51_p3_cm3_implementation_contract_20261102.md).
No Python/import/parser/AST/compiler/native execution, tests, runtime admission
or Git operation occurred. P stays disabled.

The parser independently checks the frozen CM2 event schema: exact canonical
bytes and fields, selected order, primary/negative/failfast state, fixture phases,
trace groups, footer reservation and separate prefix/whole hashes. It never
replays CallbackModel or uses CM1's older event verifier. A bounded hash path
handles up to 2 MiB without widening the frozen 1-MiB helper.

The join reparses original descriptor/collection/event/table bytes and exact
hashes. Complete frozen CM2 764/32 collection precedes separate CM1 732/30 and
HB1 700/28 projections, then table/event semantics. Opaque context strings and
caller-created Facts cannot supply authority. Results are immutable and remain
unauthenticated, execution acceptance is always false and dispatch refuses.

CM2 raw bytes do not expose actual cleanup, duration order, suite closure, final
producer refusal, complete actual subcase/trace populations or original custody.
One source test explicitly contrasts different producer states with identical
raw bytes after a late refusal; the independent parser correctly cannot infer
that hidden difference. This is an inspected test, not an executed observation.

The [explicit source roster](cho51_p3_cm3_roster_successor_20261102.json) now has
**796 identities / 34 modules, with 280 proposed selections** and 516 outside
execution. The **32 new methods remain unexecuted**. Historical CM2 parsing stays
764/248; full current-roster collection/event production is not implemented.
New tests are accounted for without silently changing frozen validators.

The [source effect/scenario index](cho51_p3_cm3_source_coverage_20261102.json)
joins all 280 identities to source pins/locations. Twenty-three design scenarios
have source examples; nine real-boundary/capture obligations remain unimplemented.
None of the 32 design scenarios is qualified. New methods have zero unittest
subtest contexts. Future normal mapping is conditionally 280*3+254+2 = **1,096
records / 561,152 bytes**, with no current-roster producer implied. The old CM2
1,000-record bound retains its 248-method scope. Synthetic 746/4,096-record test
inputs are supplied data, not outer callbacks or measured runtime output.

| Evidence | Scope |
| --- | --- |
| [Candidate v1](../../runs/coordination/cho51_p3_cm3_implementation_20261102_v1/candidate-v1.json) | 347 exact source pins; eight package files plus contract/roster/source index |
| [Independent source review](../../runs/coordination/cho51_p3_cm3_implementation_20261102_v1/source-review-v1.json) | ACCEPTED_SOURCE_ONLY; no findings; all new source and test bodies inspected |
| [Root adoption](../../runs/coordination/cho51_p3_cm3_implementation_20261102_v1/root-source-acceptance.json) | Exact source/current-roster adoption; saved-review confirmation embedded |
| [Static closeout](../../runs/coordination/cho51_p3_cm3_implementation_20261102_v1/final-static-checks.json) | File/text/JSON/hash/link and source arithmetic checks only |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm3_implementation_20261102_v1/closeout-review.json) | Metadata/documentation scope; no runtime acceptance |
| [Pre-step archive](../history/cm3_implementation_20261102/manifest.json) | 12 preceding active pages preserved |

Next is **source-only design and review of explicit lifecycle/final-refusal
evidence and current-roster collection/event integration**. A real case/suite
dispatcher still needs semantic-equivalence qualification, recursive effects and
failure bounds, original native/provider/capture evidence, complete allocation,
finite asynchronous closeout and timing/memory reserves. All original guards
remain; supplied model success cannot admit a runtime operation.

All 9,304 preservation inputs remain unchanged. Earlier unqualified cohorts,
full Q32/100/384 and candidate117/V34 remain held. QD a1f12701 remains
INCOMPLETE_REFUSED17/16, consumed failures and UNKNOWN custody remain unchanged,
and every resolver/continuation obligation remains open. Complete continuation
remains infeasible under original guards and G2 stays INCOMPLETE_REFUSED.
Science remains 0/1020 and the final freeze is unsigned. The last publication
remains 05b3a88; subsequent CM1/CM2/CM3 work and current docs remain uncommitted.
