# Supplied seal versus original terminal observation

## Model boundary

The supplied producer's seal is a serial state transition after final settlement,
not a watcher, native clock or proof no later invocation is possible. A frozen
snapshot binds one exact whole-event stream and the settled refusal state at that
boundary. Model late entry after detach cannot mutate the snapshot; it must make
the outer test/harness fail. A future-absence claim is always unavailable. CM4
parsing checks raw schema/algebra only and cannot certify the producer that emitted
it. Identical event bytes with refused/nonrefused terminal claims remain distinct
supplied outcomes, neither authenticated.

Complete footer plus refused terminal can be joined as negative supplied data.
No footer, partial trace, counter overflow, missing settlement or incomplete
detachment yields completed join facts. Preserve any available exact prefix,
including zero bytes if construction/emission never began. CM4's positive event
pin size and complete event grammar cannot represent such empty/incomplete output
as a completed join. Do not modify them; a bounded failure result remains separate.

## Future trusted observer state machine

These are mandatory design predicates, not implemented capabilities. They must
fit the same finite original operation and all original guards. Parent operation,
metadata transaction, exact sources/runtime and actor identities must be bound
before effects. Native authority is not created by a JSON UUID or supplied token.

| State | Required original evidence before advancing |
| --- | --- |
| BOUND | Fresh unused admission, exact parent/source/runtime/code identity and independently controlled stop/clock/resource/capture capabilities |
| RUNNING | All original producer entry points accounted; continuous guard/capture outside the tested interpreter; observed actual command/callback mapping |
| REVOKING | Atomically deny new producer entry at the trusted ingress; preserve attempts already admitted and latch every late/reentrant request before cutoff |
| DRAINED | All admitted attempts settled, final post-checks complete, no active producer frame; native counts agree with complete source-bound mapping |
| FROZEN | Producer capability absent/inaccessible, exact event bytes retained through owned handle, final latch observed after settlement; no producer can append or alter state |
| SNAPSHOT_PUBLISHED | Bounded observer writes/flushed/closes the predeclared terminal slot from original facts; producer remains revoked |
| OUTER_CLOSED | External caller joins original guard/owned process/Job/handle/pipe/tool closure, final source/restoration checks and full parent census before disposition |

FROZEN concerns the producer capability, not a claim that the observer has already
terminated before writing its own report. Observer publication has a distinct
write-only role and remains under original containment/deadline/capture until its
outer-owned closure is observed. An observer cannot certify its own complete
custody or every outer/tool failure. Final independent actual review must fit the
existing finite lifecycle; no extra worker/window, polling-until-quiet or recursive
unbounded chain of attestations is authorized. Complete original closeout remains
unqualified, including parent-census/publication ordering.

After original ingress revocation, any observed request before custody closes
invalidates success, even when previously sealed bytes still parse. The outer
disposition must not rely only on an earlier snapshot. Absence of a recorded
request is not absence of capability. A leaked callable, duplicate handle, active
thread, restart, pipe ambiguity or missing original control witness prevents
FROZEN/OUTER_CLOSED. No late snapshot edit or reread can repair the first cutoff.

Timeout, stop, cancellation, loss, overflow, unaccounted writer or verification
drift transitions to INCOMPLETE_REFUSED with original bounded owned cleanup.
Known negative versus incomplete evidence must remain distinct; never substitute
an exit code, PID absence, quiet/EOF guess or model detached flag for custody.
Unknown old custody remains UNKNOWN. All prior attempts remain consumed.

## Exact report ownership

Keep the accepted CM4 report proposal's caller/events.ndjson2MiB and
supervisor/producer-terminal.json64KiB; only the external terminal observer may
publish the latter operationally. The supplied model returns bytes in memory and
owns no filesystem slot. caller/evidence-join.json64KiB is composed after terminal
closure, pinning complete raw inputs. No terminal row pins a later join descriptor.
Use existing caller/return.json64KiB for the future outer failure/return role,
subject to separately reviewed exact payload/capture composition; this design
does not certify that complete failure metadata fits that slot.

No extra per-attempt journal, failure sidecar or seventeenth closeout slot is
allocated. A complete native ingress/cutoff witness schema and its exact packing
into the named guard/closure reports are still required before original execution;
the reserved report sizes do not prove fit. Full parent conservation counts every
failed/partial/unused/temp/copy/off-path write before deriving views. Original
stdout/stderr/chunk/tool capture is separate from the model event buffer.
