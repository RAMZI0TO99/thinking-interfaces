# SC1 hash scratch, fresh RAM storage and fixed-slot publisher

2 November 2026. Engineering-only, source-only implementation in new
LP19/LQ19/lplan16 namespaces and the sc1 publisher package. Independent source
review is accepted, with both findings resolved. No runtime admission,
qualification or measured speedup is established. P remains disabled;
the new Q/QD caller, supervisor and child
dispatch entry points also refuse explicitly.

## Implemented scope

| Component | Implemented behavior | Remaining evidence |
| --- | --- | --- |
| Hash scratch | Each LP19/LQ19 hash invocation owns one lazily allocated read buffer and reset uint32 counter; validated bytes are copied immutably | Actual Windows reads, native faults, sharing and guard-equivalence qualification |
| Fresh RAM storage | LQ19 declares and checks the exact64-byte MEMORYSTATUSEX layout, then creates a fresh zeroed instance for every sample | Actual ABI/resource behavior and foreground/watchdog concurrency qualification |
| Fixed-slot publisher | Closed16-role/3,293,184-byte reservation, allocation-only bootstrap, immutable ledger, exact confirmations/capture bounds and consumed failures | Concrete trusted-host binding, real transport/output proof and native qualification |
| Native publication backend | Exclusive original handle, immediate file facts before writing, bounded writes, full original readback and observable owned closure | Actual NTFS race/reparse/hardlink/alias/sharing/fault/custody evidence |

The [implementation contract](cho51_p3_sc1_implementation_contract_20261102.md)
applies the [accepted SC1 design](cho51_p3_startup_cost_design_20261102.md).
All original rewinds, reads, before/after checkpoints, exact-length/sentinel
rules, fresh hashes and whole-reader verification passes remain. No file, byte,
hash, census, native-fact or resource sample cache is added. RAM/disk/private
queries, thresholds, watchdog checks and aggregate locking remain.

The [publisher interface and limits](../../tools/local_validation/sc1/README.md)
make its host boundary explicit. Durable cross-session one-use claims,
authenticated peer messages, complete operation artifact attribution (including
off-directory copies), actual loaded-code/runtime identity and live guards must
come from a separately reviewed trusted host. No concrete host binding exists
in this change. A supplied flag or fake test adapter is not authentication.
Production publication remains unavailable without valid capabilities.

Root alone publishes metadata. Source confirmation occupies contract_adoption;
actual confirmation occupies root_disposition, each within its original cap and
8,192-byte confirmation envelope. Extra/missing artifacts, bad or consumed roles,
capture overflow, changed ledger/input bytes and unknown closure refuse without
a sidecar, retry, overwrite, release or reassignment. This phase did not execute
the new publisher to produce its own review records.

## Source review and unexecuted tests

The [frozen candidate](../../runs/coordination/cho51_p3_sc1_implementation_20261102_v1/source-candidate-v2.json)
pins263 source files, six accepted design inputs and the supporting maps. The
[implementation map](../../runs/coordination/cho51_p3_sc1_implementation_20261102_v1/implementation-map.json)
accounts for43 copied counterparts, of which35 differ only by namespace and
eight have the selected changes or explanatory README updates. Frozen
LP18/LQ18/lplan15 and all older accepted/failed evidence remain unchanged.

There are54 new unexecuted methods:19 hash/RAM supplied-call checks,31 publisher
controller checks and four native-backend algorithm checks using simulated
reader/API primitives. Text inspection maps all516 held legacy identities and
the10 QD additions to the new namespaces, with580 distinct mapped/new identities.
This is not executed collection or a complete runnable qualification roster.
The inherited256-source protocol roster remains inert reference/library code.

No SC scenario is discharged. The40 planned SC scenarios and36 diagnostic
scenarios remain unqualified. In particular, nested fake sample storage is not
actual watchdog concurrency; repeated injected hashes do not establish full
native read_small/final-verification behavior; the fake host cannot authenticate
real messages, durable consumption or a complete global artifact census.

The first independent review identified two publisher gaps. Their corrections
are independently accepted in candidate-v2; the exact affected v1 files and first
review remain preserved. The [independent source acceptance](../../runs/coordination/cho51_p3_sc1_implementation_20261102_v1/source-review-v2.json)
and [Root adoption](../../runs/coordination/cho51_p3_sc1_implementation_20261102_v1/root-source-acceptance.json)
bind the exact candidate and the reviewer's published-byte confirmation.

| Finding | Correction and unexecuted control |
| --- | --- |
| SC-I1: census preceded final verification/closure | A fresh guarded census after successful backend closure must pass before CLOSED; new source tests inject artifacts during input verification, publication verification and closure |
| SC-I2: admission trusted cached source confirmation | Admission metadata freshly verifies and retains both source-review and contract-adoption byte pins/native identities; new source tests alter each artifact's bytes or identity and require consumed refusal |

Root transcribes independent review messages into predeclared slots and obtains
peer confirmation of the exact published bytes. A separate reviewer checks final
documentation and metadata closeout. Neither review is runtime-result acceptance.

## Preservation, checks and next step

Only file/text/JSON/hash/link inspection is used. No Python, project imports,
AST parsing, compilation, native operation, test execution or Git command was
run. The [pre-step archive](../history/sc1_implementation_20261102/manifest.json)
preserves12 active pages. All8,652 preservation-baseline files were rehashed
without a mismatch during implementation.

Next is the bounded trusted-host and qualification approach: concrete one-use
claims, authenticated message/Root binding, complete artifact attribution,
loaded-code/runtime and live-guard binding, exact discovery partition, complete
capture/output bounds and finite qualification/measurement runner. Design and
independent review precede implementation-specific qualification and any fresh
admission. Complete-Q timing/output feasibility remains NOT_ESTABLISHED; no
second QD or full-Q run follows automatically from source acceptance.

Keep whole90/work60/cleanup5/hard65/child55 and QD-only45/53/55 boundaries;
startup5, two samples at least200ms apart,250ms freshness,512/768MiB caps,
4GiB RAM,20GiB disk, one CPU/library thread, hidden GPUs, project stop,
native/process ownership, full verification and every output partition.

Historical QD a1f12701 remains INCOMPLETE_REFUSED for17/16 metadata accounting;
its independently supported timing/final-verification/owned-closure facts retain
their scope. All six older probe failures remain consumed. Historical131bc595,
8bf386d1 and6f9c898c UNKNOWN custody remains unchanged. All18,793 resolver rows,
13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and
3,972 effects remain open. Complete continuation is still
INFEASIBLE_UNDER_CURRENT_GUARDS, at least31,002 rows against24,000; conditional
node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED. No original-package
custody, continued state or debt discharge is established. Candidate117/V34 and
science stay unexecuted, accepted scientific cells0/1020 and final freeze
unsigned. No commit or push occurred.
