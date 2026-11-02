# Bounded continuation design and supplied-state kernel

31 October 2026, Asia/Riyadh. Engineering only.

The four-file [continuation design](cho51_p3_frontier_v1/README.md) has
[independent design acceptance](../../runs/coordination/cho51_p3_frontier_design_20261031_v1/design-review-v1.json)
and [Root acceptance](../../runs/coordination/cho51_p3_frontier_design_20261031_v1/root-design-acceptance.json).
At the owner's request, work proceeded directly to the next bounded step:
implementation and qualification of a supplied-state kernel. Source review and
runtime qualification are tracked separately below.

## Preserved obligations and design

The accepted LP10/LQ10/lplan7 P2 observation retains18,793 rows across74 pages:
15,501 origin/node rows,786 edges,1,782 import-frontier records and724 queued
contexts. Its nodes also retain1,786 unresolved binding loads and3,972 effects.
These overlapping counts must not be summed as distinct occurrences. The
five-source13,406-node inventory also requires an explicit occurrence join.

That output is not a complete restart checkpoint: it does not serialize all
export/member state, and later phase contexts stop at already-seen modules.
The accepted design requires fresh reconstruction and exhaustive old-to-new
obligation accounting before any real-source continuation. No old queue, digest
or current documentation substitutes for fresh retained custody.

The kernel propagates a finite fact `(module, phase, root requester)` through
explicit edges, retaining both incoming links through a diamond and terminating
cycles without enumerating unbounded paths. Late phase/requester facts traverse
previously observed modules. Conditional and deferred edges remain conservative
may-reach facts; missing origins stay blocked. No obligation is discharged.

Snapshots retain the entire asserted graph, debt payloads, work cursors and
history. Replay validates exact state and predecessor joins. All logical and
resource caps remain, with additional finite history limits. A continuation
cannot reset caps or discard evidence to make progress. Capacity refusal is
possible even when the supplied graph is valid; G2 convergence is not promised.

## Implementation and qualification status

LP11/LQ11/lplan8 are independently source reviewed. The
[kernel contract](cho51_p3_frontier_kernel_contract_20261031.md) restricts this
phase to Q. LP11's operational P entry points refuse. Real-source producer,
reconciler and P integration are separate future work.

The first kernel source review recorded three findings: source-root versus seed
binding, live stop checks during replay, and explicit predecessor/sequence joins.
The [findings](../../runs/coordination/cho51_p3_frontier_20261031_q1/kernel-source-review-v1.json)
and exact first draft are preserved. The
[accepted source review](../../runs/coordination/cho51_p3_frontier_20261031_q1/source-review.json)
verifies all256 pins and accepts the corrections. Independent source review is
distinct from the actual reviews below.

| Fresh Q operation | Observed result | Actual disposition |
|---|---|---|
| Inherited `45721d46-1ec2-4548-a985-f6f88afdf3f4` |384 methods;51.6147331 seconds | [Accepted tested scope](../../runs/coordination/cho51_p3_frontier_20261031_q1/actual-review.json) |
| Combined `635926e9-9a1f-4a52-b37a-337cae39b34a` |40 resolver +32 frontier methods;49.3180987 seconds; zero errors/failures | [Accepted tested scope](../../runs/coordination/cho51_p3_frontier_20261031_q1/continuation-actual-review.json) |

Each operation has its own admission, original clock and all required controls:
eight UTC, two supervisor faults, three sharing, five observer and two bootstrap
cases. The combined cohort executes the three sharing methods separately; they
are already among the inherited384, so the distinct method union is456, not459.
Both independent actual reviews accept final input verification and applicable
owned cleanup. The [Q-only aggregate](../../runs/coordination/cho51_p3_frontier_20261031_q1/qualification-aggregate.json)
binds both exact operations, disjoint rosters, reviews and identical source/runtime
pins. Each uses256 source files and1,320 runtime-role files. No P operation was
admitted, and the aggregate is not a matching operational P consumer contract.

The [scenario map](../../runs/coordination/cho51_p3_frontier_20261031_q1/kernel-implementation-map.json)
joins32 method identities to FC01–FC32. These are supplied-state mechanisms,
including live guard callbacks, not real-source custody/producer evidence.
FP01–FP12 and complete L qualification remain separate and unexecuted.

## Evidence boundaries and next work

The design phase checked and pinned6,867 preserved predecessor files. The
[archive](../history/frontier_design_20261031/manifest.json) contains12 exact
pre-step active pages. Policy bytes, frozen sources, old failures and receipts
are unchanged. The [post-run file check](../../runs/coordination/cho51_p3_frontier_20261031_q1/preservation-check.json)
rechecked all6,867 predecessors, four design files,256 executed sources and12
archives with no mismatch. This is metadata verification, not physical P custody.
Post-release documentation does not refresh P custody/census.

The next integration must reconstruct real source observations, reconcile every
old obligation, and qualify under fresh Q
and separately admitted P. Complete G2 decisions and matching implemented host
capabilities require independent complete-plan acceptance before L. Candidate117,
V34, scientific0/1020, unsigned final freeze, Bootstrap004 consumed, diagnostics005
held, custody UNRESOLVED and006 unadmitted remain unchanged. No commit or push.
