# P3 bounded timing/telemetry design — 27 October 2026

## 1. Purpose and status

**Prospective design; no instrumentation, profiling or diagnostic has run.**
Companion to the [P3 adapter design](cho51_p3_adapter_design_20261027.md).
All proposed telemetry belongs to new reviewed operations sources, never edits
to frozen candidate/operations code. It observes engineering work; it provides
no authorization, result acceptance, numerical counter or scientific signature.

The accepted v7 actual native Job took **590.082323s** under600s, leaving
**9.917677s** in one observation. Its internal573.828s timer starts later and has
a different endpoint. Its external closeout62.763709s has another scope. These
are not interchangeable phase costs or a production reliability distribution.
Earlier hard600 failures stay failed; this design does not retroactively reject
the accepted v7 pass. See the [timing audit](cho51_canonical_pipeline_interface_audit_20261025.md#timing-evidence-and-uncertainty).

## 2. Scope sequence before a numerical P3 bridge

1. Separately authorize and implement bounded telemetry contracts/format checks
   in new operations sources. Settle independent source pins and review.
2. Run focused **nonnumerical** unit/guard checks only after fresh admission.
   Verify that observation preserves the real enforcement observer and limits.
3. Separately authorize/admit **one** timing diagnostic of the accepted numerical
   contract using new reviewed operations and exact current source/runtime pins.
   Do not run an archived v7 launcher. This new observed execution is not covered
   by the old receipt, even if candidate bytes are unchanged.
4. Review complete native/external evidence and timing coverage. Decide readiness
   before adding the executable P3 controller. No repeat budget is implied.

The diagnostic must keep the same one-episode source0/restore1/support1/query1/
two-query-trial/model1/measured0 scope. It must not fit sources, add another
episode, weaken audits, move more work outside the Job or extend600s. If the
overhead cannot fit, the attempted diagnostic can fail honestly; no “profiling
exception” changes resource limits.

## 3. Clock and process-identity domains

| Domain | Clock and endpoints | Interpretation |
| --- | --- | --- |
| Root dispatch/custody | Native monotonic/QPC-derived measurements plus explicit UTC records before dispatch, actual tool completion and full release | Full caller/release bounds include final artifact writes, output and owned-process cleanup, not just an inner timer |
| Native Job | Guard's independently recorded start/deadline/end; exact process handles, membership, limits, empty/closed/absence | Authoritative hard native limit; Python trace cannot extend it or certify closure |
| Python child | `perf_counter_ns` in one process generation/thread, first explicitly instrumented instruction through final child evidence | Phase wall-time observations only; import/startup before installation remains separately bounded by native evidence |
| External closeout | Its own supervised monotonic interval and actual outer caller completion through final writes/EOF/reap/release | At most the independently granted300s total; a short internal measurement alone is insufficient |

Every trace binds role, PID **and creation identity**, admitted command/source
pins and native directory; PID alone is unsafe. UTC is for correlation and
grant-window checks, not subtraction across different monotonic origins.
Do not subtract child `perf_counter_ns` from a native QPC timestamp or claim
cross-process exclusive time. Record clock name/resolution and, for raw QPC,
frequency. Clock regressions, mismatched process generations, sleep/discontinuity
or missing endpoints produce invalid/incomplete timing, not invented zero cost.

Instrumentation cannot query/terminate arbitrary process IDs. Native owned-tree
custody must use independently reviewed opened-handle PID/parent/creation checks
and conservative lifetime bounds; stale Toolhelp rows are insufficient. Keep
the existing qualified supervisor/guard protections and preserve uncertain
ownership without unrelated termination.

## 4. Phase map and honest measurement coverage

The first diagnostic must declare an exact code-object/call-site allowlist and
the semantic endpoints for every requested span. Repeated checks get occurrence
IDs; do not merge duplicated mandatory audits into a deceptively small span.

| Phase | Planned observation boundary | Coverage limit |
| --- | --- | --- |
| Native admission/startup | Native guard/pre-dispatch operations | Not claimed covered by a Python timer installed afterward |
| Imports/guard installation | New operations' explicit boundaries, followed by native-to-child residual | Bootstrap before the first marker stays unobserved/residual |
| Pins/current source | Each actual operations pin/source recheck | Timing does not cache or replace any hash/authorization |
| Historical origin | Each full origin verification call, separately numbered | Includes its nested metadata/input work; not a fresh numerical restore |
| Physical input audit | Both actual backend audits plus separately labeled external audit | No conversion into a metadata-only check or extra deferral |
| Route/profile/preflight | Explicit operations calls and, later, new P3 mapping/preflight spans | Current boundary imports/metadata rebuilding have their actual cost |
| Target route | Genuine `run_target_route` entry/return | Inclusive of loads, restore, support, query and internal checks |
| Restore | Genuine `ProvenanceRestoreFactory.restore` entry/return | Includes its internal authentication/decoder/model/state checks |
| Support adaptation | Genuine `adapt_labram_tuning_support` entry/return | Function-scope wall time, not all target preparation |
| Query forward | Precisely classified query classifier-forward entry/return under existing independent observer semantics | Label `query_forward_only`; it excludes data loading and is not all query/target latency |
| Verifier1 / verifier2 | Each genuine numerical verifier and P3-specific verification call | Keep two calls and their fresh physical checks distinct |
| Attestation/terminal | New operations/controller's explicit durable-write and terminal boundaries | In the preliminary diagnostic, original v2 attestation/terminal only; P3 versions remain unimplemented |
| Loaded modules/finish | New operations successor equivalent to complete Runtime.finish obligations | Includes all required hash/recheck/final result work; do not time only dictionary construction |
| Native/external closure | Guard receipt plus actual supervising caller and complete external custody | Child result cannot self-certify empty/closed/absent or whole-host quiet |

For a phase that cannot be observed without new source changes, report
`not_observed` and its reason, not0. A classifier-forward span is not a substitute
for acquisition-to-command latency or full query cost. A return event on an
exceptional unwind does not prove successful completion; outcome requires the
actual independent function/controller result.

## 5. Observer integration without weakening enforcement

Use explicit new-operations context spans where call sites are owned. For
unchanged inner functions, a narrowly filtered, read-only Python profile observer
may be proposed, using exact pinned genuine code objects. Do not monkeypatch
functions, add model hooks, inspect tensors/frame locals, execute user callbacks,
format arbitrary objects, serialize arrays or use telemetry as a numerical
permission check.

The accepted target route already installs a profile observer. Its
[_profile](cho51_linear_target_route_v1/target_route.py#L249) forwards events to
its previously installed observer, and its exit restores that observer. A future
new-operations timing observer can use that chaining only after dedicated tests
prove actual call order, single delivery, exception behavior and exact final
restoration. No observer may suppress the existing witness, its exceptions,
independent runtime counters or live-lock checks. Refuse an unknown competing
observer; do not silently replace it or globally enable thread profiling.

For support/query classification, use reviewed function/event occurrence and
the existing independently validated phase contract—not arbitrary caller labels,
frame-local data or the timing observer's own authority. Distinguish restore
layout probes, support forwards and actual query forwards. If exact classification
cannot be demonstrated, preserve a generic forward occurrence rather than
mislabeling it query latency. Numerical counts still come from the independent
guard and physical proof, never the telemetry event count.

Profile events apply only to the admitted single execution thread. If a
required phase crosses threads, declare coverage incomplete unless a separately
reviewed successor models that domain. Do not widen Torch/native concurrency.

## 6. Bounded record format and overhead

Proposed `cho51_p3_timing_trace_v1` fields:

- Fixed schema/controller/profile, process generation/thread and clock domain;
  independent operations/source/native pins and trace role.
- Strictly increasing sequence number, bounded span ID/parent ID, enum phase,
  occurrence number and event enum (`begin`, `end`, `abort`, `coverage`).
- Exact nonnegative integer monotonic nanoseconds; declared outcome
  `completed`, `aborted`, `incomplete` or `not_observed`; a bounded reason enum.
- Final event count/byte count, completeness/truncation status and finite
  coverage inventory. No arbitrary exception message or environment dump.

Proposed limits: maximum256 span instances/512 normal begin/end records,
plus16 reserved coverage/abort records; maximum1024 encoded bytes/record;
maximum512KiB total trace bytes **including reserved records**, maximumdepth16.
Reserve16KiB of that total for terminal/abort metadata. The normal-record limit
and total-byte limit both apply; reaching either normal allowance stops recording
normal events and uses the bounded failure reserve. Rejection/overflow must not
silently drop events while declaring complete timing. No ring buffer erases the
failure lead-up, and no unbounded per-call profiler log is allowed.

Keep only a fixed-size scalar buffer on the hot path; no I/O or hashing per
profile callback. Use at most **two create-once direct segment files**, with the
512KiB/528-record aggregate limits shared across both, not granted per file:
the pre-terminal prefix's event buffer is frozen, then fsynced, closed, hashed
and revalidated before attestation. The **post-prefix finalization tail buffer
starts immediately when that prefix buffer freezes**, before prefix-file
sealing, outer attestation or the engineering terminal. It records those steps,
final controller/result/module-check work and its bounded abort reserve; it is
persisted as a new segment only after its final observed event. Its metadata
links the prefix digest and preserves the same increasing sequence. A prefix
boundary carries a bounded open-span stack so spans crossing the cut can be
validated only after both segments are joined; it does not claim whole-child
completion or closed timing for those spans. The external review binds both
exact segments. The tail must not rewrite the sealed prefix.
Buffer loss on a hard kill means missing/incomplete coverage, not a reconstructed
successful trace. An append-only crash journal is outside this first design.
Never write outside the admitted fresh operations output or let trace output
bypass ordinary hardlink/reparse checks.

All buffering, timestamps, flushes, hashing and cleanup consume the real time
and memory budgets. No overhead is subtracted from the native deadline. A
bounded byte count is not a proven runtime cost; measure overhead behavior in
the admitted diagnostic. Telemetry failure makes timing qualification incomplete
and stops any transition that requires complete timing. Before numerical entry
it refuses entry; after entry it preserves unknown/partial numerical status,
never retries, and follows the actual guard's failure/quarantine policy. It must
not suppress or replace the underlying error with a fabricated success.

## 7. Inclusive, residual and exclusive-like values

For a completed same-domain span, inclusive wall time is end minus begin.
Its **unattributed wall-time residual** is inclusive time minus the union of
fully contained direct-child intervals, only when the stack/clock/thread
relationships are valid. Validate IDs, uniqueness, parent containment, balanced
stack and nonnegative duration. Do not sum overlapping intervals twice.

This residual is not CPU self-time: it can contain I/O, scheduling, interpreter
and instrumentation overhead. Missing/aborted/overlapping invalid spans make
the residual unknown. Do not subtract sums of inclusive nested spans from the
native elapsed time or use artifact modification-time gaps as phase costs.

Publish separate timing tables for:

1. Native start-to-end and full caller/custody bounds.
2. Completed per-process inclusive spans and validated unattributed residuals.
3. Coverage gaps/aborts and their consequences.
4. External-closeout scope and complete release timing.

## 8. Prospective readiness decision, not a cap change

**Proposed review target:** at least30s native arithmetic headroom under600s
(native elapsed<=570s) before adding an executable P3 controller. This target is
a conservative engineering proposal, **not yet an owner-adopted rule**, not a
new native cap and not a statistical reliability claim. The diagnostic may still
be valid timing evidence if it completes under600s but misses that target; in
that case controller readiness stays held. No accepted historical pass is
reclassified by a new prospective target.

Before diagnostic admission, settle and explicitly adopt the target and maximum
trace/observer budget in the reviewed diagnostic scope. If the evidence cannot
support a safe margin, identify actual measured costs and propose a separately
reviewed change. No source optimization, audit removal, extra post-terminal
deferral, hash/permission caching, extra attempt, second episode or cap increase
follows automatically. One run cannot establish a tail-latency distribution;
repetitions would need their own explicit budget.

## 9. Future admission and evidence closure

Fresh default startup10GiB/active4GiB/disk20GiB applies unless the owner supplies
an exact applicable amendment. Preserve two startup samples, CPU/Torch1/1,
hidden GPUs,600s native work/5s existing cleanup policy and4096/5120MiB caps for
the proposed matching envelope. All five genuine peer pause paths and actual
remaining time reserve apply. A peer release estimate or absent pause is not
admission. New reviewed sources, explicit finite grant, unused output/attempt
and full resource/pin checks precede any diagnostic.

The peer window must cover the complete actual startup/dispatch,600s work,
existing5s cleanup, separately bounded300s external closeout and full release,
plus the applicable60s reserve and explicitly bounded preparation overhead.
This is a feasibility requirement for a future request, not a new window or
allocation. Stop/refuse when the remaining window cannot cover that total.

Post-run evidence must include immutable trace and source/ops pins, unit and
actual phase separation, actual observer chaining/restoration checks, physical
numerical proof, native deadline/limit/closure receipts, full caller completion,
external original-input/source/runtime revalidation, EOF/reap and full custody
release. Independent review authenticates actual artifact bytes and all scopes.
The diagnostic closeout binds both final segment hashes and the exact result;
the diagnostic result may bind only segments already sealed before its own
write, never a future tail that records that write. P3's later outer attestation
binds only the sealed pre-terminal prefix, with the separately sealed
post-prefix finalization tail explicitly joined externally to avoid a hash cycle.
Tail-file persistence and the child's final exit happen after its last recorded
event and therefore remain native/caller-covered residual, not a self-timed
claim that the trace contains its own final write or complete process lifetime.

No telemetry result would sign the final freeze, qualify the other method
chains, admit real scientific evaluation, reset target01, prove predictive
performance or certify another device/runtime. Current design-phase numerical
activity is0; future post-entry unknowns must never be rewritten as0.
