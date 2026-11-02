# HB1 verifier, refusal and exact collection implementation

2 November2026. The13-file [HB1 package](../../tools/local_validation/hb1/README.md)
is implemented and independently accepted for source only. It checks supplied
frames, parent maps/census models and collection reports, and provides an
always-refusing production-host interface. P remains disabled. No runtime,
import, collection, AST, compiler, native operation or test was executed.

## Implemented and reviewed

| Area | Source behavior | Evidence limit |
| --- | --- | --- |
| Frame verifier | Exact8-byte prefix, bounded lengths, strict header/request/refusal data, exact checksum and response joins, original peer bytes | Supplied data only; every result unauthenticated |
| Refusal handling | Production-shaped host always unavailable; separate replay/sequence/one-claim model consumes ambiguous failures and refuses retry | Local model state cannot prove durable consumption or native cancellation |
| Parent accounting | Complete reservation/census correspondence, all four partitions, fixed16 main slots and optional distinct16 native-fixture slots, aliases and failed/partial/unused charges checked before views | No real producer barrier, native census or original preclaim approval |
| Collection checks | Literal580 existing plus120 new identities; exact28 module pins, class/method provenance declarations and ordered membership; skips/xfail/hooks/partial/substitution refuse | Supplied report checked; no executed discovery, outcomes or qualified runner |

The [implementation contract](cho51_p3_hb1_implementation_contract_20261102.md)
defines exact model schemas, refusal boundaries and source dependencies. The
original [HB1 design](cho51_p3_host_binding_v1/README.md), SC1 publisher,
LP19/LQ19/lplan16 and all predecessor sources/receipts remain frozen.

The source roster now contains700 distinct methods across28 modules. The120
new methods comprise13 common-data,38 frame,30 refusal,25 parent-join and14
collection cases. All120 are written but unexecuted. The proposed component
verifier selection is184 (64 existing plus120 new); this does not change the
separate full-Q32/100/384 cohorts or any controls. The24 HB scenarios remain
distinct from test methods and from40 SC/36 diagnostic obligations.

## Independent review and preservation

Root and one active peer worked locally with assigned file ownership. A reviewer
who authored none of the implementation inspected the exact
[candidate](../../runs/coordination/cho51_p3_hb1_implementation_20261102_v1/source-candidate-v1.json)
and all120 new method bodies. The two preliminary observations were corrected
before freeze: zero native identities now refuse; expected-failure and xfail
flags are explicit and must be exact false. Both have negative test subcases.
The frozen candidate has no outstanding source findings.

The [independent review](../../runs/coordination/cho51_p3_hb1_implementation_20261102_v1/source-review-v1.json)
is published verbatim by Root, with its saved-byte confirmation embedded in
[Root acceptance](../../runs/coordination/cho51_p3_hb1_implementation_20261102_v1/root-source-acceptance.json).
All288 source/reference pins matched, including263 unchanged inherited pins;
all8,768 preservation-baseline files matched. The
[pre-step archive](../history/hb1_implementation_20261102/manifest.json)
preserves12 active pages. Text enumeration and literal pin checks establish the
700-method map only; they are not parsing, import, discovery or test execution.

The [final static checks](../../runs/coordination/cho51_p3_hb1_implementation_20261102_v1/final-static-checks.json)
and separate [metadata closeout review](../../runs/coordination/cho51_p3_hb1_implementation_20261102_v1/closeout-review.json)
record documentation/link/preservation checks. Neither certifies a runtime
result. Root is the sole metadata publisher; reviewers create no sidecars.

## Remaining boundary and next step

The production provider/bridge remains UNAVAILABLE. There is no original
authentication/delegation, atomic durable cross-session claim, native channel
cancellation/closure, loaded-code/runtime witness, complete attributed census,
asynchronous publication lifecycle or complete capture bound. The supplied
model's fixed unadmitted namespace is lexical only; it creates no directory.
Only explicit native HB scenario IDs are mapped for the model inner ledger;
SC-specific fixture mappings conservatively refuse pending a reviewed successor.
No parent-map result or symbolic model confirmation can become a positive SC1
projection. Complete-Q timing/output feasibility remains NOT_ESTABLISHED.

Next is design and independent review of a finite component-model qualification
runner, including exact source/runtime loading, complete discovery, original
guards and full capture/accounting on every success/failure path. Any later
runtime needs fresh pins, an unused operation, a reviewed runner and separate
admission/result review. Missing prerequisites remain a refusal. No new window,
old launcher replay, second QD, split-Q acceptance or changed cap is inferred.

All time, process/Job/pipe/channel/handle ownership, cleanup, RAM/disk, CPU/thread,
hidden-device, stop/startup/freshness, output partition and final-verification
guards remain. Historical QD a1f12701 remains INCOMPLETE_REFUSED for17/16
accounting, with its supported timing/final-verification/owned-closure facts
unchanged. Six older probe Q failures stay consumed;131bc595/8bf386d1/6f9c898c
UNKNOWN custody remains unknown.

All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,
1,786 binding loads and3,972 effects remain open. Complete continuation remains
INFEASIBLE_UNDER_CURRENT_GUARDS, at least31,002 rows against24,000; conditional
node/raw-byte findings retain scope. G2 remains INCOMPLETE_REFUSED. No original-
package-path custody, continued state or debt discharge is established.
Candidate117/V34 and science remain unexecuted, cells0/1020 and final freeze
unsigned. No commit or push occurred.
