# P3 local custody-resolution design

28 October 2026, Asia/Riyadh. Engineering design and contract sources only.
Author: project Root. Independent review is required before implementation.
The active [project execution policy](../PROJECT_EXECUTION_POLICY.md) governs
ownership and admission. This package has no outside scheduling dependency.

## Decision

Preserve bootstrap004 as FAILED_UNRELEASED_CONSUMED. Introduce a separate
**current execution-domain disposition** for a new operation; never reinterpret
it as historical cleanup. A disposition may be refused, unresolved, or eligible
for local admission review. None of those records authorizes a launch by itself.

The first implementation will support one narrowly specified boundary:
an independently verified complete operating-system restart after the old
operation on the execution host. An isolated alternate execution host remains
a future extension, not an accepted fallback in this version. An empty process
table, elapsed time, a new PID, a console-host guess, or an owner acknowledgement
without technical evidence cannot satisfy the boundary.

No restart has been observed or requested by this design. Do not restart the
machine automatically. Lack of suitable evidence keeps the operational gate
closed while implementation and source review may continue.

## Why the earlier operation cannot be certified

The retained004 failure says Start succeeded, child PID302124 was not proved
reaped, and custody/release remained false. Both output streams reached EOF.
The later PID/parent query returned no rows, but the original process handle,
generation and first refused-row identity were not captured in the audit.
Those missing observations cannot be recreated after the fact.

The historical failure disposition is pinned at SHA256
`1faf198894e0f210e5bb8692a8c0c4b35f10963a1e2c8c928d545eb808c335ec`.
The actual caller-return upper bound was
`2026-10-27T17:05:08.2987118+00:00`; its audit is pinned at
`365153e07d2f925d36168f0218404ae37c18962d0bbabb0598a284ff6740b75d`.
These identify the failed event, not a prior boot identity: the saved record does
not contain one. The new collector must explicitly resolve the association
between that event and the host being assessed; a copied workspace path is
insufficient host authentication.

## Evidence contract and trust boundary

The JSON schemas in [the versioned contract directory](cho51_p3_local_custody_v1/README.md)
define bounded, closed records. Schema conformity alone proves only structure.
It never proves that a restart happened or authenticates a collector.

The complete candidate packet must include:

1. Exact old disposition, actual audit and independently reviewed failure record.
2. Exact collector source/protocol hashes, independent source review, current
   runtime pins and a finite local observation admission issued before capture.
3. Raw bounded native observations with provider/API identity, query bounds,
   UTC and monotonic timing, actual tool return/exit and a host identity binding.
4. Technical evidence of a complete new OS execution generation after the
   failed operation. A wall-clock boot timestamp alone is insufficient. The
   collector implementation must establish restart kind, exclude hibernation/
   resume and fast-start restoration of the relevant process domain, and address
   clock changes and persisted guest/container workloads.
5. An independent review of the actual raw observations and their limitations,
   including the event-to-host association that was absent from the004 packet.
6. A Root disposition tied to those exact inputs and that reviewed boundary.

The collector's exact Windows evidence providers and the accepted full-restart
predicate are **implementation prerequisites, not invented APIs in this design**.
Their platform guarantees must be checked against authoritative documentation
and the actual runtime, then independently reviewed. Unsupported or incomplete
provider coverage yields UNRESOLVED; it cannot be replaced with assertion fields.
The positive path stays disabled until that collector contract is qualified.

## Mandatory verifier joins

The future semantic verifier must enforce all of these conditions in addition
to JSON Schema validation; every missing or contradictory join fails closed:

1. Read JSON with duplicate-property rejection, finite/lossless numeric handling,
   a1MiB encoded-record cap, maximum depth16, maximum8192 nodes and maximum4096
   characters per string. Schema-specific tighter bounds also apply. Parse QPC
   fields as exact integers in0..9007199254740991; never round a value into range.
   Enforce calendar-valid UTC dates explicitly; a schema format annotation is
   not an assertion of timestamp validity.
2. Resolve every artifact beneath the approved project/attempt root using a
   normalized relative path with no empty, dot or parent segments. Refuse aliases,
   reparse traversal, UNC/device paths and unexpected filesystem types. Verify
   its bounded bytes and digest from the retained read identity, and detect
   changes during the read. An identical path string alone is insufficient.
3. Bind historical disposition/audit/failure review to their fixed hashes and
   unchanged false custody/release fields. Bind the collector review to exactly
   the executed collector/protocol/runtime pins. Bind the actual review to all
   raw observation hashes, provider coverage and the event-to-host association.
   The reviewer must be different from the implementation author. Root may issue
   a disposition/admission only after adopting that specific independent review.
4. Require source review before observation admission, observation admission
   before capture, capture end before actual tool return, actual tool return
   before actual review, actual review before disposition, disposition before
   bootstrap admission, and admission before dispatch. Verify each local window
   encloses its operation. A complete-restart event must be strictly after the
   old caller-return bound and before current capture, with independently
   qualified clock-order evidence; UTC arithmetic alone does not supply it.
5. Within one observed execution generation require a positive matching QPC
   frequency, end>=start and elapsed time consistent with the bounded capture.
   Never compare QPC values across different boots as one monotonic clock.
   Require current host/boot identities to match the reviewed disposition and
   the new admission; reobserve them at dispatch and after operation. Any change
   or unknown generation invalidates that operation's acceptance.
6. Require the active policy hash, request digest, exact source map, independent
   source-review digest, current runtime pins and current disposition digest to
   agree across the new request/admission/controller/helper. The request must
   explicitly list resource and timing limits identical to the admission.
7. Require the attempt-directory final UUID segment to equal operation_id.
   Consume that identity using an atomic create-once local claim before any
   child start. Existing, ambiguous or unreadable claims are refusal, not retry.
   No metadata completion path may remove or reset a claim.
8. The current-boundary capture must end no more than300seconds before bootstrap
   admission. Source/runtime/policy and host/boot joins must still hold at entry.
   Require two fresh startup resource samples and a strict local stop state;
   PRESENT or UNKNOWN refuses new work. Maintain the substantive active limits
   and bounded owned cleanup after stop. Finite current entry checks do not
   reconstruct old cleanup or prove global host quiet.

The current host is not asserted quiet or free of all processes. A qualified
boundary supports only that the old relevant process domain cannot persist into
the new assessed generation, under the explicitly verified assumptions. It
does not establish the old cleanup method, time, exit status or missing row.

## State transition

| Input state | Allowed result | Operational meaning |
| --- | --- | --- |
| Historical failure missing, changed or falsely upgraded | REFUSED | Preserve evidence; no operation |
| Complete packet missing or provider coverage insufficient | UNRESOLVED | Continue source/design work only |
| Present-state evidence contradicts the claimed boundary | REFUSED | Preserve contradiction; no operation |
| Qualified full-restart packet, exact independent actual review and all joins | ELIGIBLE_FOR_LOCAL_ADMISSION_REVIEW | Root may consider a separately pinned new operation |
| Fresh local admission plus matching current boundary at entry | New successor may enter its own start protocol | No reuse or release of004 |

All states retain historical_custody_closed=false,
historical_operation_released=false and historical_retry_allowed=false.
The disposition has launch_authorized=false. A later local admission must bind
its exact digest and a new operation identity; it is not created by a schema
validator or by the reviewer.

## Local successor006 implementation contract

Author separately versioned controller/helper/protocol sources. Leave all001–005
files, used outputs and existing native preparation/closeout candidates intact.
The new operation gets a new directory and unique attempt; it never writes
back into the004 or005 namespaces.

Replace old scheduling joins with the local request, independent source review,
Root admission and project-owned stop path. Include the current policy digest.
Keep the old failed-disposition digest separate from the new current-domain
disposition digest. No dummy legacy records or wildcard path substitutions.

Preserve the substantive invariants:

- Mark Start attempted/unknown before the call. Do not infer no-child after an
  uncertain Start; keep the original retained process handle and generation.
- Contain the newly launched process domain with a reviewed native ownership
  mechanism. Existing sample-and-no-spawn reasoning is not a kernel Job proof.
  The implementation must establish which guarantees its actual mechanism supplies.
- Never reacquire ownership or kill by PID alone. Never kill an unowned row.
  Preserve the first refusal and keep a custody refusal sticky.
- Preserve bounded005 diagnostics: controller/helper generations, table site
  and ordinal, refused row, primary failure, cleanup outcomes and truthful
  stream-preservation witnesses. Evidence overflow cannot become success.
- Require actual caller return, both EOFs, retained-handle reap, final ownership/
  containment checks and complete expected payload before accepting success.
- Keep uncertain, failed and successful operation states distinct through
  completion and release. A metadata mode exiting0 does not release custody.
- Check fresh resources, source/runtime hashes and the local stop predicate;
  use finite work/cleanup/effect limits. Stop remains effective through cleanup.

The original bootstrap purpose is bounded runtime-byte observation, not Python
execution, a model, a study case or scientific permission. The future observation
request must state its own resource envelope; the pending contracts' 4/4 GiB
amendment is not silently widened to unrelated diagnostics.

The proposed006 bootstrap admission sets a10GiB startup floor,4GiB active floor,
20GiB free disk,4096MiB per process and5120MiB aggregate Job memory caps, one
thread and hidden GPUs. The memory caps are explicit design limits for this
future bootstrap, even though their numbers match the separate unit envelope;
they must be enforced by the reviewed containment implementation. The10GiB
startup floor retains the default because the existing4GiB exception is scoped
to the pending contracts phase and its named ancillary preparation. This design
does not ask the owner to repeat that exception or claim a current RAM reading.
Any later directly applicable owner amendment requires a versioned local
contract; no source or predicate is silently weakened to obtain a run.

## No circular bootstrap proof

A new boundary observer and a new process controller need their own reviewed
trust bases. Do not justify either one's execution by a runtime manifest it is
supposed to create. Pin and independently review the minimal observer/runtime
dependencies before its local observation admission. Review the actual result
before using it to authorize a different operation.

Similarly, native preparation, the117 candidate tests/34 controls and external
closeout remain distinct later operations. Old preparation003 expects an earlier
manifest schema and is not automatically compatible with successor006.
The future integration must version and review that boundary explicitly.

## Acceptance cases for implementation

The accompanying [acceptance matrix](cho51_p3_local_custody_v1/acceptance-cases.json)
enumerates required positive and negative scenarios. They are design cases,
not executed tests. They cover malformed/duplicate/nonfinite metadata, historical
tampering, missing host identity, unsupported restart evidence, stale/replayed
reviews, time/generation mismatches, unused attempt enforcement, local stop,
uncertain Start, unowned descendants, diagnostic loss and incomplete closure.

Implementation completion requires independently reviewed sources, fresh local
admission and actual bounded tests. A successful schema parse, static review,
or fabricated fixture never supplies actual machine-boundary evidence.

## Completion of this design phase

The phase completes when the specification, all three schemas and acceptance
matrix have independent review with no unresolved design findings, current
document links resolve, and the80-file predecessor baseline remains exact.
This is a complete design/contract-source milestone only. It does not claim an
implemented executable controller, accepted restart, operational disposition,
test pass, native preparation or launch readiness.

The immediate implementation package is the source-bound boundary collector and
its fail-closed verifier, followed by successor006. If no supported current
boundary can be established, report the precise evidence gap after preparing
the source and review; do not silently weaken the predicate or request a restart
before the concrete technical need is established.
