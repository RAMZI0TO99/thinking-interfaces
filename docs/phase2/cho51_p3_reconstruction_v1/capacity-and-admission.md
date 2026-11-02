# Capacity proof and execution gates

All existing substantive guards remain effective. This design admits no runner
and does not change any numeric limit or accounting rule. A future representation
needs independent review of both conservation and accounting; new names, paging,
compression or references do not by themselves satisfy the current contract.

## Static obstruction in the accepted kernel

In [lplan8/compiler.py](../../../tools/local_validation/lplan8/compiler.py),
`_frontier_capacity` defines graph base rows as twice the module count, plus
seeds, obligations, all module records and edge templates. It multiplies this
base by the number of retained frames, then adds the weighted frame facts,
links, pending work and history entries. `frontier_continue` retains predecessor
frames. An initial state has one frame; the first committed successor has two.

For any faithful mapping of the retained resolver's15,486 node records and15
origins into that graph, base is at least15,501. Therefore the first successor
requires at least `2 * 15,501 = 31,002` rows, before contexts, seeds, edge templates
and other obligations. The row cap is24,000. This is conservative: mapping each
source module normally adds two base units, so no omitted overhead is being used
to manufacture the failure. Packing many source records into one opaque payload
would violate the required complete record accounting and is not an escape.

The retained resolver and candidate inventory have disjoint occurrence tuples:
15,486 plus13,406 gives28,892 nodes. Putting both in one graph would already
exceed24,000 at initialization. This second result is conditional on a combined
graph; separate historical scopes remain distinct. Neither proof measures
serialized bytes, all source modules, current transitive closure, or P runtime.
An initial resolver-only graph might also exceed its8 MiB snapshot cap or
structural payload bound, but this step makes no measurement claim about that.

The [static observation](../../../runs/coordination/cho51_p3_reconstruction_design_20261101_v1/static-capacity-observation.json)
checks all74 resolver and53 inventory pages against ordered descriptors, verifies
their node identity tuples and relevant exact counters, and pins supporting
source/evidence files. It is file/JSON inspection only; it does not independently
validate every historical schema/digest/native descriptor, reparse source, or
qualify a producer. Runtime verification remains broader as specified separately.

## Required accounting before source freeze

| Envelope | Unchanged limits and denominator |
|---|---|
| Common sources / P extras |256 /256; every live dependency included, counterpart replacements justified |
| P shared outputs |256 files,64 MiB total,8 MiB per file; all stages and handoff artifacts count |
| Resolver logical state |128 modules,16 MiB source,2 MiB/module,200,000 nodes,depth128,24,000 rows,10,000 edges,100 pages,256 rows/page,16 MiB output |
| Kernel retained chain |128 snapshots,1,000 transitions per call,8 MiB snapshot,16 MiB canonical retained snapshot bytes; repeated historical graph/frame copies count |
| Q operation |90 whole /60 work /5 cleanup /65 hard seconds;512/768 MiB process/Job; no cohort over384 methods |
| P operation |300 whole /240 work /5 cleanup /245 hard seconds;4096/5120 MiB process/Job |
| Environment |4 GiB startup/active available RAM,20 GiB disk,one CPU/Torch thread,hidden GPUs,local PROJECT_STOP.json |

Retain original process/Job containment, bounded streams, native reader sharing,
all live stop/time/memory/disk checks, full final original-handle verification,
owned cleanup, exact caller evidence and consumed-attempt semantics. Admission
never reserves permission to exceed a guard because implementation ran slowly.

Historical P2 used198 shared files/46,810,857 bytes and208.8519081 seconds. Simply
appending a74-page ledger to that layout would already use272 files, even before
its index or fresh snapshots. This is a warning about *that append-only layout*,
not proof that all possible reorganizations fail. Its old232 extras similarly
do not reserve a free namespace for129 historical index/pages plus new code.
Review the exact fresh physical coverage partition and all overlap; do not
assume the arithmetic sum is the number of distinct extras. Released P custody,
its census and timing are not refreshed by documentation or static pinning.

## Ordered gates and refusal decisions

1. **Representation feasibility:** show exact full-input and worst-case staging,
   logical-history and publication allocation under the current contract. The
   direct lplan8 route is statically refused. No P is needed to confirm that.
   Alternative representation and changed accounting, if proposed, must be
   explicit and separately reviewed/adopted; this design does neither.
2. **Implementation/source review:** use new versioned producer, verifier and
   matching Q/P consumers. Preserve LP11's operational refusal. In particular its
   inherited384+40 aggregate parser cannot consume the accepted384+72 Q-only
   aggregate. Never remove the refusal without a matched reviewed protocol.
3. **Fresh Q:** discover all456 inherited/resolver/frontier methods, add named
   producer methods and an exact reviewed partition, <=384 per operation. Each
   cohort executes all eight UTC, two native faults, three sharing, five observer
   and two bootstrap controls. The three sharing methods are already in384 and
   are executed separately for other cohorts; do not double-count distinct IDs.
   Same exact source/runtime pins across cohort aggregation, distinct unused
   operations, independent source and actual reviewers, explicit Root adoption.
4. **Current coverage and separate P admission:** exact source/runtime/old-data
   pins, unused operation/output directory, reviewed commands/artifacts/refusals,
   current resource observations, local stop, full custody and output budget.
   Physical preparation and bounded nonexecuting AST reconstruction only; no
   candidate/dependency imports, native loads, L collection, V or science.
5. **Actual review:** independently assess real return, all controls as applicable,
   output/input descriptors, complete payload/ledger joins, final verification,
   process/Job closure and measured resource use. A refused operation consumes
   its identity. Source or mechanism acceptance is not a real-case acceptance.

Every downstream grant remains false. Source decisions and matching Lhost
capabilities must still be implemented/qualified and independently accepted as
a complete plan before separately admitted L. Q bootstrap cases are not P runs;
P preparation/reconstruction is not loader/ABI qualification or V execution.
