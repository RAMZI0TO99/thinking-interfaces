# CM4 supplied-data contracts and current roster

3 November 2026. **Ten-file implementation independently accepted for source
only, with no findings.** The [package](../../tools/local_validation/cm4/README.md)
implements the accepted CM4 supplied collection, table, lifecycle-event, terminal
and five-input join contracts. See the
[implementation contract](cho51_p3_cm4_implementation_contract_20261103.md).
No Python/import/project parser/AST/compiler/native execution, tests, runtime
admission or Git operation occurred. P stays disabled.

The collection checks the entire current supplied census before separate frozen
CM2/CM1/HB1 projections. The event parser independently checks explicit lifecycle
claims, closed subcase triplets, trace/fixture ownership, negative outcomes and
footer integrity. The terminal parser verifies supplied counter/latch algebra;
the join binds every raw input and preserves event or terminal negatives. Identical
event bytes can yield different supplied dispositions when their joined terminal
snapshots differ. Results are immutable, authority properties always false and
dispatch always refuses. No actual observer cutoff or original closure is proven.

The [roster successor](cho51_p3_cm4_roster_successor_20261103.json) accounts for
**40 new unexecuted tests**:20 CM4EventTests and20 CM4ContractTests. Current source
and parser target are **836 identities /36 modules, with320 proposed selections**
and516 outside execution. The design's796/34/280 target is explicitly historical;
frozen CM3 parsing remains764/248. No predecessor source or module pin changed.
New test-module pins are literal and do not create a self-hash cycle.

The [source/scenario index](cho51_p3_cm4_source_coverage_20261103.json) pins all320
selected method locations,91 new textual declarations and37 direct imports. Of28
design scenarios,18 have supplied source examples; CM4-17 has partial counter/
snapshot examples while mutable producer sticky/reentry/post-checkpoint behavior
remains unimplemented; two have source accounting artifacts; seven original
runtime boundaries remain unimplemented. **None is qualified.**

The new tests add zero normal unittest subTest contexts. With254 inherited
contexts, conditional normal output is5*320+3*254+6 = **2368 records /1,212,416
bytes**, plus the separate terminal snapshot. The1606-record minimal synthetic
fixture,4096/4097 synthetic boundary streams and raw2MiB hash tests are source
examples, not executed output. The33-file/18,890,752-byte report proposal and
4,325,376-byte input ceilings remain unchanged; complete operational allocation,
capture, timing and peak-memory feasibility remain unestablished.

| Evidence | Scope |
| --- | --- |
| [Candidate v1](../../runs/coordination/cho51_p3_cm4_implementation_20261103_v1/candidate-v1.json) | 369 source pins,13 new files, four external reference-only pins |
| [Independent source review](../../runs/coordination/cho51_p3_cm4_implementation_20261103_v1/source-review-v1.json) | ACCEPTED_SOURCE_ONLY; no findings; all new code and40 test bodies inspected |
| [Root adoption](../../runs/coordination/cho51_p3_cm4_implementation_20261103_v1/root-source-acceptance.json) | Exact source and roster/budget adoption, saved-review confirmation embedded |
| [Static closeout](../../runs/coordination/cho51_p3_cm4_implementation_20261103_v1/final-static-checks.json) | File/text/JSON/hash/link and arithmetic only |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm4_implementation_20261103_v1/closeout-review.json) | Metadata/documentation only |
| [Pre-step archive](../history/cm4_implementation_20261103/manifest.json) | Twelve exact preceding active pages |

Next is **source-only design/review of the bounded producer/dispatcher lifecycle
and terminal observation boundary, including finite recursive failure/effect
mapping**. Original collector/dispatcher/producer, semantic equivalence, original
code/type/trace/subcase completeness, trusted external sealing/native custody,
complete capture/allocation and finite asynchronous closeout/final reserves remain
separate gates. No model consistency result admits execution.

All9,369 preserved inputs remain unchanged. Existing guards, full Q and
candidate117/V34 holds remain. QD a1f12701 stays INCOMPLETE_REFUSED17/16, old failures
stay consumed, UNKNOWN custody stays unknown, and no resolver/continuation debt
is discharged. Complete continuation remains infeasible and G2 refused. Science
remains0/1020 and final freeze unsigned. Last push remains05b3a88; later CM1/CM2/
CM3/CM4 work and current documentation are uncommitted.
