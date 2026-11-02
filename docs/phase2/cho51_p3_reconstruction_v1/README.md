# Real-source reconstruction and obligation reconciliation

Engineering design, 1 November 2026, Asia/Riyadh. This package specifies the
producer boundary missing from the accepted supplied-state kernel. It does not
implement a producer, admit Q/P, or change a resource or conservation guard.
Root authors the design; an independent peer reviews its pinned bytes.

Read the [reconstruction contract](reconstruction-contract.md),
[reconciliation contract](reconciliation-contract.md),
[capacity and admission decision](capacity-and-admission.md), and
[qualification plan](qualification.md) together. They refine the accepted
[continuation design](../cho51_p3_frontier_v1/README.md); LP11/LQ11/lplan8,
their accepted Q evidence, LP10/P2 and all earlier failures remain frozen.

## Decision before implementation

Direct integration of the complete retained resolver graph into lplan8 cannot
advance under its current accounting. The 15,501 origin/node rows alone require
at least 31,002 counted rows at the first successor; the limit is 24,000. This
is a static lower-bound proof, not an attempted execution or measured byte fit.
Smaller batches, paging the same snapshots, dropping old records, resetting
counters, or calling the capacity limit a yield cannot remove this conflict.

File/hash/JSON inspection also joins every occurrence tuple in the retained
15,486-node resolver and 13,406-node five-source inventory. Their intersection
is zero, so the union is 28,892 distinct retained tuples. **If** combined in one
kernel graph, nodes alone exceed the initial row cap. The two inventories are
historically separate scopes; this does not retrospectively charge either
accepted observation for the other's rows, or prove that every future design
must combine them. Their obligations must still be exhaustively accounted for.

The [pinned static observation](../../../runs/coordination/cho51_p3_reconstruction_design_20261101_v1/static-capacity-observation.json)
records these joins. It authenticates current file content against historical
page hashes, not retained native handles, current source semantics or fresh P
custody. No old AST is reparsed. Initial serialized/structural byte fit is
unmeasured, and no complete real-source reconstruction has run.

The immediate next step is a separately reviewed **lossless state-representation
design and capacity feasibility decision** before producer/P implementation.
It must retain every payload and historical identity, bound the whole retained
history, and show how its accounting relates to the current guards. This package
does not adopt deduplication, external-reference debt, relaxed history accounting,
or larger limits. If a representation cannot meet the existing contract, record
the precise proposed contract change for explicit scope resolution; do not code
around the refusal. A refusal-only producer remains possible but is not claimed
to unblock continuation. No known-infeasible full P is admitted just to rediscover
this lower bound.

## Work separated by claim

1. This design establishes required input joins, reconstruction semantics,
   reconciliation outputs, refusal states and qualification obligations.
2. A feasible representation requires its own reviewed design before adoption.
3. New producer/consumer sources then require independent source review, fresh
   Q, complete current physical coverage, and separately admitted file-only P.
4. Actual P review may accept a bounded observation or a well-evidenced refusal;
   it cannot call either G2 complete without complete decisions and matching
   implemented/qualified Lhost capabilities and complete-plan acceptance.

The 117 candidates and 34 V controls remain unexecuted; scientific cells remain
0/1020 and the final freeze unsigned. No L, numerical work, Git, commit or push
is part of this design. Bootstrap004 remains consumed, diagnostics005 held,
custody UNRESOLVED and006 unadmitted. There is no outside-chat dependency.
