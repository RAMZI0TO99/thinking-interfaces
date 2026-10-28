# Canonical boundary bounded implementation plan, 25 October 2026

## Current authorization and outcome

The owner authorized the interface audit and this bounded plan. These documents
complete that source-only task; they do not launch implementation, validation,
profiling, numerical work, canonical execution, recovery or study work.
See the [static audit](cho51_canonical_pipeline_interface_audit_20261025.md).
No new candidate, launcher, pins, admission or compute grant is created now.

Recommended next implementation: a metadata-only canonical-facing boundary,
separately versioned as
`docs/phase2/cho51_canonical_boundary_v1/{boundary.py,test_boundary.py,README.md}`.
This is a proposed ownership namespace, not an existing implementation or an
approved production entry point. Root owns plan/coordination/control metadata;
one assigned implementation child may own only that new package. Serialize an
independent reviewer under Pro3 Root+one<=2, Pro2<=3/shared<=5. Preserve frozen
canonical432, accepted factory/worker/route packages and every used operation,
receipt, raw input, weight and historical document snapshot.

## P1: read-only metadata contract

Implement an immutable CanonicalBoundaryRequest plus BoundaryAssessment
(names provisional until source review), with a versioned schema that embeds
canonical pin bytes by external digest without extending the canonical schema.

Required inputs and joins:

1. Exact canonical execution-pin file/hash and static method/config/protocol
   bytes; strict finite JSON, duplicate/unknown-key rejection and exact integer/
   Boolean types. Independently derive each field, not only a pinned Boolean
   saying it was checked. Retain the canonical method inventory, but admit
   no method execution; the historical proof references are linear-only.
2. Actual CasePlan and exact original1040/adopted1020 mapping; subject02 linear/
   five shots/seed11/repetition1 is the sole candidate engineering episode for
   any later proposal, not an episode launched by preflight. Preserve all52
   source catalogs/assets; reject target01, missing/duplicate/extra identities,
   changed seeds/repetitions/method configuration and altered adoption evidence.
3. Actual typed full/adopted route/catalog/asset metadata plus independently
   pinned origin/owner evidence. Recompute plan/selection/episode/configuration
   joins over supplied metadata. Record physical raw-input/weight verification
   as NOT performed; preflight must not claim that structural compatibility
   replaces fresh signal hashing, selected tensor restoration or full historical
   selector verification. Do not call route builders that read NPZs.
4. Separate historical producer, current executor and current recorder roles,
   plus accepted package/origin/owner-decision digests and the prospective
   numerical budget. Never substitute current source for historical source or
   flatten distinct runtime identities merely because version strings match.
   Freeze request JSON and return defensive copies of mutable views.
5. Direct normalized paths, explicit metadata byte limits, regular-file/
   ancestor identity checks and before/open/after stability. Proposed JSON
   bound8MiB and explicit total report/input-count limits must be reviewed.
   No recursive unbounded inventory, arrays/weights/environment dumps or
   arbitrary path extension. Hardlinks/reparse paths/aliases fail closed.
6. An immutable finite report whose positive meaning is only
   metadata_contract_compatible. It must separately carry execution_admitted=false,
   measured_publication_allowed=false, scientific_admission=false,
   raw_input_verification_performed=false, weight_verification_performed=false,
   unchanged_canonical_worker_qualified=false,
   unchanged_canonical_parent_qualified=false and
   single_root_factory_qualified=false. All current numerical ledger entries0.

No backend/execute/recover callback or capability is returned. No claim, lock,
fixture/output tree, source selection, adapter/model, array decoder, optimizer,
query, publication or recovery is performed. Reports return in memory; a
separate externally supervised custodian may persist canonical report bytes
after validation. Compatible metadata must not be convertible to execution
admission by changing a report flag.

Reuse canonical read-only config/digest/envelope/types and load_execution_pins
only with independently bounded strict metadata reads. That function's current
source checks must remain genuine. The single-root restore, full selector/
publication APIs and manifest-file verifier cannot be used to disguise producer/
executor mismatch; the latter also reads weight bytes. No monkeypatching,
noop record_cell, fake CellIdentity, fake manifest witness, fabricated measured1,
relaxed source equality or intercepted terminal promotion is acceptable.

## P2: planned metadata validation

This matrix is proposed, not executed and not a fixed inherited test count:

| Positive baseline first | Negative/side-effect coverage |
| --- | --- |
| Valid canonical pins/configuration, full/adopted routes and external role metadata | Missing/extra/duplicate plans/catalogs/assets;52-versus51 confusion; wrong actual class |
| Immutable finite request and defensive-copy report | Unknown fields, duplicate JSON keys, nonfinite numbers, Boolean counts, mutable payload substitution |
| Distinct producer/executor/recorder and route fingerprints | Swapped roles, current-source substitution, stale package/owner/config/protocol pins |
| Bound direct metadata bytes | Same-byte physical replacement, changed size/hash, path escape, hardlink, symlink/reparse ancestor, truncated/oversized metadata |
| In-memory compatibility-only assessment | No directories/claims/locks/writes, selector/backend/decoder/model/update/query/publication/recovery calls; all ledger entries0 |
| Explicit unperformed raw/weight/runtime/science obligations | Fake verified-manifest witness, inferred tensor verification, automatic execute token or altered admission/publication flags |

Use fabricated metadata controls with real canonical types. A valid full route
must be independently structurally derived from the controls, not given a fake
assertion that raw input preparation ran. Clearly label fixture metadata versus
accepted historical evidence versus any future freshly verified inputs.
Production reads of signal/weight files are blocked by the reviewed guard.
Any import-side effects must be observed and must not construct models or
perform numerical work.

Before tests: settle new sources, independent static review with zero actionable
findings, fresh source/runtime byte pins and a fresh unused output/attempt.
Obtain a distinct max-one phase-specific peer grant and native admission;
do not reuse011/012, archived launchers, v7 pins as new-source qualification,
or a passing older test count. New tests may require separate metadata-only
phases if the complete selected suite does not fit one reviewed600s Job.
Every phase needs its own exact receipt/grant; do not hide retries or split a
numerical episode. Independent external closeout, owned-child reaping, explicit
full custody release, evidence review and bounded exact metadata export follow.

This source-only task consumes no validation lease. For future admission retain
the project default startup10GiB/active4GiB/disk20GiB unless a fresh directly
applicable owner amendment is explicitly recorded for the new phase. The prior
available-RAM4GiB amendment belonged to the completed factory/worker milestone,
not an automatic new-phase waiver. Retain600s/4096+5120MiB/CPU-Torch1/1/hidden
GPUs/two startup samples and all five genuine pause paths:
`D:/Aenv/pro2/WORK/resume-{20261007,20261012,20261013,20261015,20261025}-001/coordination/PRO2_REQUEST_PRO3_PAUSE.json`.
A future external stdlib-only closeout is separately supervised<=300s.
No process killing/cache clearing, cap increase or inferred peer release.

## P3: hard stop before executable canonical-facing work

Accepting P1/P2 would qualify only the new metadata boundary. It cannot make
the unchanged canonical production runner restoration-only or make its staging/
parent measured==1 contract compatible with measured0.

A later executable successor needs a separate owner-authorized bounded plan
that explicitly selects engineering terminal semantics and names the affected
new versioned modules. It must keep the real canonical recorder lock and
accepted dual-provenance factory/physical proof checks. A call-through wrapper
around the already accepted run_parent_pipeline adds no canonical production
qualification by itself. Do not convert engineering success into evaluation_cell
or run measured-cell recovery to claim interface coverage. Any future validation
of canonical measured-cell behavior requires its own explicit measured-record
scope; that still would not sign scientific admission.

Resolve timing readiness before adding executable overhead: current observed
headroom is only9.917677s. First design bounded nested phase telemetry in new
operations sources, settle/review those sources, and obtain separately scoped
diagnostic admission. No rerun/profile occurs here. Do not infer measured
hotspots from file timestamps or change mandatory audits, live-lock checks,
hashing, verifiers, loaded-module checks or600s limits. A prospective margin
target must be explicitly documented; do not retroactively fail the accepted
v7 pass or invent a statistically proven margin from one sample.

## Acceptance and remaining scientific boundaries

For this audit/plan task: source-linked call map, explicit compatibility gaps,
minimal proposed package, test/admission matrix, timing uncertainty and static
independent review; no implementation or runtime qualification claim.

For a later boundary implementation: all specified metadata checks and refusal
tests pass under fresh native admission, no actionable independent findings,
all production side effects/counters0, complete native/external closure and
exact evidence/document snapshots. Failed attempts stay frozen and unknown
post-entry counts are never relabeled zero or replayed.

Preserve the owner-adopted targets02–52/source52, original target01 attempts0,
narrow Gate A acceptance, unresolved checkpoint-cohort/overlap lineage and
remaining method chains. Final scientific freeze is unsigned; full1,020-cell
execution and predictive performance remain unqualified. Neither a compatible
schema, compute grant, measured recorder shape nor engineering delegation signs
a scientific decision or creates a new autonomous window.
