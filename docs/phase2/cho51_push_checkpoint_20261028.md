# Documentation and engineering checkpoint, 28 October 2026

The owner requested an updated handoff and documentation followed by a repository
push. This publication collects the completed work since commit `c177d00`, the
project plan and literature review, and exact historical engineering evidence.
It introduces no new adapter behavior or runtime validation.

## Current evidence

| Milestone | Retained evidence | Limit |
| --- | --- | --- |
| Provenance-aware restoration | 65 passing focused tests; one selected-source restoration | Engineering qualification, not study accuracy |
| Parent/numerical-worker integration | 63 unit cases, 27 guard controls and one synthetic episode | Two predictions were both wrong; zero measured scientific cells |
| Canonical metadata boundary | 133 distinct cases; 399 passing phase reports; 34 controls / 102 instances; accepted aggregate | Read-only metadata compatibility |
| P3 adapter and telemetry design | Completed design and independent static review | No runnable P3 controller |
| Metadata/profile mapping and supplied telemetry | Implemented and statically reviewed | 117 candidate tests and 34 controls remain unexecuted |
| Bootstrap004 | Actual failure and independently reviewed failed disposition | FAILED_UNRELEASED_CONSUMED; missing refused-row and cleanup evidence remain unknown |
| Diagnostics005 | Three successor sources; independent static review; two clean PowerShell ASTs; 75 predecessor files preserved | Deliberate prelaunch hold; no runtime exercise |

These counts describe their own dated checkpoints. Publishing their evidence
does not rerun tests or certify this publication commit as an execution context.
The [progress report](../where%20are%20we/PROGRESS_REPORT.md),
[project plan](../where%20are%20we/PROJECT_PLAN.md), and
[literature review](../where%20are%20we/LITERATURE_REVIEW.md) provide the broader
project context. The literature review retains its stated research cutoff.

## Immediate next step

Develop a separately coordinated **custody-resolution specification** that
defines the evidence and decision rules needed to proceed after the failed
bootstrap. It must preserve the old failure and its unknowns, distinguish a
future disposition from proof of historical cleanup, and define explicit refusal
conditions. Implement a distinct successor only after that design is reviewed.

Fresh source review, coordination and exact admission precede any live successor
bootstrap. Accepted actual observation then precedes separately reviewed native
preparation and pin review, the 117 candidate tests and 34 controls, and external
closeout. Diagnostics005 cannot be enabled by an ordinary new grant. No rerun of
consumed004, retroactive release or readiness Boolean resolves its missing proof.

The publication does not start this next implementation phase. Source014 remains
expired. Pro2 reported Source015 closed unadopted; no later window or acceptance
is inferred. Scientific cells remain **0/1020**, final freeze unsigned, with the
narrow Gate A acceptance and adopted targets02–52/source cohort52 unchanged.

## Publication contents and restoration limits

The existing 25 October evidence packets retain successful executions, refusals,
timeouts, source copies and immutable document snapshots. The new
[P3 archive](../../evidence/cho51-p3-source-checkpoint-20261028/README.md) preserves
108 exact files / 3,024,281 payload bytes, including both local P3 run folders,
the six candidate sources and prepublication documents. Its manifest records
the paths and current copy hashes without changing any original receipt.

Historical hashes bind their archived snapshots, not advanced documentation
heads. The archive's newly measured hash of the Root005 qualification is a
publication observation, not a retroactive Source014 measurement. Pro2 peer
reports remain distinct from independently inspected local evidence.

Only reviewed metadata/source packet files are explicitly included where the
normal `artifacts/` and `runs/` ignore patterns would omit nested archive copies.
Live run trees, EEG arrays, weights, caches, environments and runtime binaries
remain outside this publication. Foreign/local absolute paths in historical
records are provenance, not portable executable commands or restored assets.

The older three files in `docs/where are we` are replaced by the existing five-file
project overview, plan, progress, evidence index and literature review. Their
previous committed versions remain in Git history.

## Publication checks and provenance

Use native file/hash and Git inspection to check packet manifests, the unchanged
canonical source baseline, exact staged scope, source/evidence byte preservation,
bounded text file types and credential-shaped content. These are publication
checks, not a new project quality-suite pass or runtime qualification.

The configured commit hook invokes Python and the canonical quality suite.
Following the established publication procedure, this commit uses a per-command
empty hooks directory after the publication checks. The repository hook files
and persistent Git configuration remain unchanged. No project source or helper
is executed by that procedure.

The completed 25 October runs captured actual executor `c177d00`, dirty=true;
their historical producer identities remain distinct. This new commit becomes
a new Git context. Future execution must capture it and fresh source/runtime pins
honestly; never replace the Git identity in a saved receipt or reuse an old grant.
