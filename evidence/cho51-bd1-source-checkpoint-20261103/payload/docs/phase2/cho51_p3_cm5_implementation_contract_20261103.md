# CM5 supplied producer/refusal/seal implementation contract

3 November 2026. Source-only implementation of the accepted
[CM5 design](cho51_p3_cm5_producer_design_20261103.md). The implementation author
owns the new producer and its tests; Root owns the registry, roster, source index,
documents and phase records. A different peer reviews the exact source candidate;
a separate peer reviews metadata closeout. Preserve all9,436 predecessor inputs
and the12 preceding active pages archived before this step.

## Scope and frozen target

The new tools/local_validation/cm5 package implements an in-memory supplied-data
model. It accepts exact primitive commands and fixed fault enums; it neither
executes test methods nor invokes user callbacks, native providers or arbitrary
check hooks. Its output is checked in test source against the independent frozen
CM4 event and terminal parsers. Those parsers are not its transition engine.
No actual dispatcher, collector, terminal observer, filesystem publisher or
operational admission is added. Runtime dispatch refuses and all returned
facts retain unconditional false authentication and execution-acceptance claims.

Producer target remains **CM4's836 identities /36 modules /320 selections**.
The new registry is a source census successor for the expanded checkout, not a
new event schema, an expanded producer target or implemented current collector.
Never present CM4 collection/events as evidence that the added CM5 tests ran.
No predecessor code, schema, roster, receipt or budget claim is rewritten.

Attempt accounting precedes command/fault validation and sticky/busy checks.
Representable entries settle once; the first observed refusal remains sticky.
Fixed reentry injection models one rejected additional entry, never arbitrary
recursion or concurrency. Entire event groups and the next lifecycle state are
prepared before commit. A post-check failure preserves the committed bytes,
including a valid footer, while making the final terminal negative. Refusal
never fabricates missing cleanup, duration, suite closure or footer records.

Overflow leaves available counters/prefix with explicit incomplete accounting;
it cannot forge a completed terminal. Seal is a controller operation after
settlement, with immutable supplied output. After-detach calls fail outside that
snapshot boundary and cannot establish future absence. Unexpected failures and
secondary refusal-report failures use fixed codes without formatting exceptions;
no guaranteed Python allocation reserve or successful error-report allocation
is claimed. Original effects, capability revocation and cutoff remain separate.

## Test roster and conditional budget adoption

The [roster successor](cho51_p3_cm5_roster_successor_20261103.json) declares40 new
methods in two modules,20 per module. The expanded source census is
**876 identities /38 modules /360 proposed selections**, retaining516 outside
execution. Literal module byte/hash pins and ordered full/selection digests are
acyclic; tests do not embed their own source hashes. All40 methods are unexecuted.

There are zero new unittest subTest contexts. The earlier254 conditional normal
contexts remain. A hypothetical compatible expanded dispatcher/event successor
would require5*360+3*254+6 = **2568 records /1,314,816 bytes** at512 per record,
and2567 normal guarded commands if it retained CM5's BEGIN convention. This is
conditional accounting only: such a current-roster producer/collector is not
implemented. The actual CM5 model still targets CM4's2368 records /1,212,416 bytes
and2367 normal guarded commands; minimal synthetic all-pass fixtures without
subcases contain1606 records. Inner supplied records, mocked failures, manually
seeded counter/capacity states and ordinary test loops are not outer subTest
callbacks or original executions.

The4096-record/2MiB stream,512-byte line,128-frame trace and4095 nonfooter /
2MiB-minus512 prefix bounds remain. One group has at most129 records/66,048 bytes;
attempt counters remain0..65535 and modeled reentry has at most2 in flight.
Prefix copies, prepared state, JSON graphs, immutable returned views, independent
parser storage and mocked failure machinery remain chargeable allocations.
Bounded supplied representation does not establish total peak memory or runtime fit.

The five historical CM4 raw-input caps total4,325,376 bytes. The unchanged report
proposal is33 files/18,890,752 bytes: caller10/10,878,976, supervisor7/4,718,592,
closeout16/3,293,184. No native allocation, new writer, seventeenth closeout role,
per-attempt journal or operational reservation is created. Fixed output slots and
all failed/partial/temp/copy/unexpected effects still need original accounting.

Retain global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB and per-file8MiB. Retain whole90/work60/cleanup5/hard65/child55
seconds; suite40/native12/fault2, startup5; sampling gap200ms/freshness250ms;
process512MiB/Job768MiB; RAM4GiB/disk20GiB; one CPU/library thread, hidden GPUs
and original owned stop/cleanup. T0 does not reset; child deadline remains
min(T0+55,T0+60-F-M), with final-work F and margin M unproved. Raw stdout/stderr
and tool return retain1MiB caps, external return64KiB. Escaped capture expansion
and finite asynchronous closeout remain open; a supplied event buffer is not
actual stream capture or complete parent custody.

## Source evidence and limits

The [source/scenario index](cho51_p3_cm5_source_coverage_20261103.json) conserves
the320 prior direct-method rows and adds40 pinned new rows, declarations/imports
and scenario-to-source examples. It retains the accepted16-class failure/effect
map and every unresolved recursive edge. New local JSON/hash/dataclass allocations,
unittest assertion formatting, private-state test setup and mock replacement /
restoration need original effect qualification. Direct textual calls are only
candidates; absence from that list does not discharge any transitive obligation.

All32 design scenarios remain unqualified. Supplied-model source examples do not
qualify an original dispatcher, real interrupted lifecycle, actual callback/code/
trace/subcase completeness, trusted external observation, native custody or capture.
No original failure/capture/allocation/closeout/resource requirement is removed.

Only file/text/JSON/hash/link/arithmetic inspection and source edits are allowed.
No Python, imports, project parser/AST/compiler, native calls, tests or Git run in
this phase. Source review does not certify executable syntax or runtime behavior.
Root publishes predeclared records under
runs/coordination/cho51_p3_cm5_implementation_20261103_v1; reviewed candidates are
archived before correction. Reviewers send exact message-only verdicts and verify
Root's saved bytes; final closeout confirmation stays in the conversation.

P remains disabled; full Q32/100/384 and117/V34 remain held. QD a1f12701 is still
INCOMPLETE_REFUSED17/16. Consumed failures, UNKNOWN custody and all18,793 resolver
rows,13,406 inventory occurrences,724 queues,1782 frontiers,1786 loads and3972
effects remain open. Full continuation remains infeasible at least31,002 rows
against24,000; G2 remains refused. Science0/1020, final freeze unsigned.
