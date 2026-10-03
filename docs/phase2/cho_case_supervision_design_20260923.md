# Cho case supervision design before scientific execution

23 September 2026. This design addresses an execution gap in the bounded
Phase II pilot. It is engineering preparation only. The proposed Cho tranche
remains unratified and cannot start complete selection under the unchanged
256-step ceiling; no case worker or scientific cell is launched by this note.

## Observed seam

`TargetCaseExecutor.run_case` calls `adapter.predict_target` in its own process
and checks the ten-minute case cap after that call returns. A stalled fit can
therefore exceed the cap. It also claims attempt 1 directly. `CaseRecorder`
supports a second attempt after a verified failure, but writes the cell and
success receipt as two separate no-clobber files. A process death between
those writes can leave a cell without its success receipt. Current restore
code can rebuild a selected source from pinned evidence, but no production
caller joins that restore to an externally timed Cho case.

## Proposed parent-owned transaction

1. Before a claim, the parent verifies the exact committed configuration,
   selected route, complete selector evidence, restored source model, quality
   and controls, source/environment identity, full-work admission and current
   machine guards. The public selector verifier continues to refuse the
   proposed 5,253-step work until a separate ratified contract and admitted
   workload exist. The supervisor is not a way to split or evade that bound.
   It publishes a write-once **case execution contract** before attempt 1:
   full `CellIdentity`, repetition, method settings, selected candidate and
   evidence/store hashes, episode and fixed support/query identities, source
   catalog and asset pins, and a durable session deadline. A retry must match
   that contract byte for byte and reverify its live inputs. `CasePlan` alone
   is insufficient because its identity key omits these fields.
2. Under a cross-process per-case lock, the parent writes a `CaseRecorder`
   attempt claim and a durable start/deadline record, then starts a fresh Windows
   child for exactly one target case. The child receives only pinned paths and
   digests. It constructs the model, repeats preclaim checks and writes a
   content-addressed **result proposal** containing fixed query identities,
   predictions, support identities, checkpoint and evidence digests, stage
   timings, source/environment pins and exact-rational metric inputs. The
   child does not publish an evaluation cell or success receipt. It must not
   call `TargetCaseExecutor.run_case` unchanged, because that method claims
   attempt 1 and publishes a cell itself. Reusable validation should be
   extracted so the child and parent can check the same fixed case.
3. The parent creates the child suspended, assigns it to an owned Windows Job
   Object with a noninherited kill-on-close handle, then resumes it;
   assignment failure prevents
   execution. It enforces the declared
   ten-minute case cap, 120-minute session cap, 20 GiB disk floor, 4 GiB
   available host RAM floor, existing 8,192 MiB GPU admission and cooling
   policy. The persisted deadlines continue across parent restarts. A guard
   or deadline stop terminates the owned process tree and
   writes a verified failure for that attempt. The parent never kills an
   unrelated worker on the other project.
4. On normal completion, the parent records a write-once completion
   attestation while the owned child is observed to exit within both
   deadlines. A partial or unobserved proposal is not sufficient after a
   crash. The parent reopens the attested proposal and all pinned
   evidence, recomputes query labels and exact-rational metrics from the
   fixed episode, rechecks source/environment, model state and live admission.
   Before publishing it writes a durable intent with the **exact canonical
   cell bytes and digest**, including timing values. Publication is replayable:
   if a crash leaves the same cell but no success, the parent verifies the
   immutable intent and identical cell bytes before writing the missing
   success receipt. Conflicting bytes stop without replacement. The per-case
   lock spans claim, child, failure or attestation, and terminal publication;
   otherwise another parent could write a failure between cell and success.
5. A retry uses attempt 2 only after attempt 1 has a verified failure and a
   fresh resource/compute admission. The same scientific identity and inputs
   are required; a second failure ends that case. Partial proposal files are
   preserved as failed-attempt evidence, never treated as a completed cell.

The parent should supervise only a case whose entire selection and target
workload is admitted within a declared budget. Per-fit checkpoint retention
also needs a bounded storage policy: the existing retain-every-step option
projects tens of TiB for the first tranche and is not enabled by this design.
The [current evidence storage review](cho_selection_evidence_storage_review_20260923.md)
shows that even final weights plus inline source-identity maps exceed today's
space above the project disk floor.

The existing `TargetCaseExecutor` 120-minute session clock starts when that
executor is constructed; it does not supervise the preceding 102-fold source
selection. The draft's no-reuse timing proxy implies approximately **93.5,
96.1, 123.3 and 36.7 minutes** for a complete linear, LoRA, full-tuning and
EEGNet selection respectively, before unpriced startup, persistence and
cooling. These are planning proxies, not observed complete-selection times
or guaranteed upper bounds. In particular, applying the existing 120-minute
session limit to selection plus target would already reject the full-tuning
proxy. A future selection worker therefore needs its own explicit, ratified
wall and resource envelope. This case supervisor cannot inherit a suitable
selection deadline from the present pilot or silently raise its cap.

## Tests before connecting a real adapter

Synthetic children should cover a normal result proposal, a hung child, a
child that spawns a grandchild, disk/RAM guard stops, a source or evidence
change after claim, partial and conflicting proposals, interruption between
cell and success publication, a failure racing an orphan cell, two competing
parents, a changed retry contract, and a linked second attempt after a
recorded failure. Parent-crash tests must verify owned grandchildren die,
unrelated processes remain untouched, and persisted deadlines do not reset.
Then a bounded Cho engineering case can exercise the integration under the
existing 256-step ceiling without representing complete scientific selection.
Full scientific execution still needs owner freeze ratification, committed
configuration, complete-work compute/storage admission and current quality
and controls.

## Isolated Windows primitive proved on this host

`evaluation/phase2_supervision_primitives.py` now supplies an engineering-only
`DeadlineLease` and `run_supervised` operation. A write-once deadline file is
loaded immediately before launch; proposed deadlines above the existing
10-minute attempt or 120-minute session limits are rejected. The active
parent also uses monotonic time so a backward wall-clock adjustment does not
extend a started run. The operation reads local disk and available physical
RAM before launch, immediately before resume, on each poll and at observed
job completion. It refuses a reading below the 20 GiB disk or 4 GiB RAM floor, and a
sensor error prevents a success result.

The Windows implementation creates an unnamed, noninherited Job Object,
sets and reads back `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, creates the child
with `CREATE_SUSPENDED` and handle inheritance disabled, verifies assignment
to that Job Object, then resumes its main thread. A failed assignment leaves
the child suspended until it is terminated. Closing the Job Object stops its
normal process descendants even if the parent process exits unexpectedly
**after assignment**. A root child exiting with code 0 does not complete the
job while its grandchild remains active. The parent polls
[`JobObjectBasicAccountingInformation.ActiveProcesses`](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information)
and attests normal completion only after that count reaches zero within the
deadline and resource guards. It checks the deadlines again after the final
resource sample and handle cleanup, so a slow final check cannot turn a late
completion into a normal result. For a deadline or guard stop while the child
tree is active, it calls `TerminateJobObject` and verifies the count reaches
zero before returning.
The parent uses only its private Job Object and process handles; it never
enumerates or kills by process name. [Microsoft's Job Object description](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [CreateProcessW contract](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw)
define these Windows behaviors.

`tests/test_phase2_supervision_primitives.py` passed fourteen synthetic tests on
this Windows host: normal exit, attempt deadline, grandchild containment,
root exit 0 with a sleeping grandchild, root exit 0 with a naturally finishing
grandchild,
unrelated worker survival, live disk and RAM stops, sensor failure, failed
assignment before resume, deadline expiry while the pre-resume sensor ran,
deadline expiry during the final resource sample,
persisted deadline after restart, and parent-crash kill-on-close for a child
and grandchild. Focused Ruff and strict mypy passed. No Cho case, selection
step, or classifier fit was launched by these tests.

There is still a parent-crash window between `CreateProcessW` returning a
**suspended but unassigned** process and `AssignProcessToJobObject` succeeding.
If the parent dies in that interval, its cleanup code cannot terminate the
suspended orphan, and no Job Object owns it. The tested parent-crash guarantee
starts after assignment. A production integration needs an atomic job-at-create
mechanism or a separately proved recovery watcher before claiming that every
crash leaves no orphan. This primitive does not silently treat a successful
root exit or a Job Object wait signal as a whole-tree completion signal.

This primitive is not yet wired to a production case transaction. The caller
must still hold a cross-process case lock, pin the write-once deadline record
in the case contract, provide GPU and cooling admission, validate the child
proposal and source evidence, and publish failure or cell records. Standard
`CreateProcess` descendants inherit Job Object membership. The Windows API
documents an exception for processes started through WMI `Win32_Process.Create`;
an integrated worker must not use that route for subprocesses. A blocked
system sensor or Windows API call has no independent watchdog in this
primitive, so a production parent must also verify those calls are bounded
in its actual execution environment before it can claim a hard wall cap.

## Recorder publication recovery implemented

`CaseRecorder` now serializes claim, failure, and cell publication under a
crash-releasing cross-process lock keyed by the shared cell identity. Before
writing a measured cell, it publishes a write-once intent containing the
complete canonical cell envelope, case plan, identity, and claimed attempt.
`recover_cell_from_intent` requires a cell digest pinned outside the writable
intent, verifies that record, its claim and the measured metrics, then replays
the exact cell and success receipt bytes. Completion also checks any present
intent against the successful cell. A late failure,
retry claim, changed timing value, or different cell conflicts with the
existing intent. Synthetic tests interrupted publication both before the
cell and between the cell and success receipt; recovery completed both cases
without recomputing floating-point timing values. Tests also cover a
self-consistent intent rewrite, a later repetition's genuine failure, and an
unreceipted cell from another repetition. The focused recorder suite passed
18 tests; Ruff and strict mypy passed for the implementation.

`CaseRecorder.case_session(plan)` now holds the identity lock through the full
synthetic child lifetime. The engineering parent binds the case plan, initial
contract, source, worker module, interpreter, cwd, and external binding digest.
It writes a separate `engineering_smoke` intent and success receipt; these
never count as scientific cells. Existing
`TargetCaseExecutor` still uses its retrospective cap and direct attempt-1
publication, so these recorder changes do not admit a Cho scientific case.
`CaseRecorder.completion` is accounting, not a trusted recovery inventory: it
checks an intent for a completed case, while an interrupted intent without a
success receipt needs the external attested cell digest and explicit
`recover_cell_from_intent` validation before it can be resumed.

## Synthetic parent and proposal transaction

The [isolated transaction probe](cho_case_transaction_contract_20260924.md)
binds a small synthetic contract to a durable start record, supervises a
Windows child, and checks exact proposal bytes before a parent attestation.
The synthetic engineering parent now connects a framed version of this
transaction to a `CaseRecorder` claim and separate engineering success
lifecycle. It exercises concurrency, replay, deadline, resource and tamper
paths without EEG data or a scientific cell. The legacy standalone file probe
remains for historical tests; the engineering parent requires an owned Job
result frame. The deadline covers child completion and proposal validation;
the subsequent
filesystem publication can finish later. A production case parent still
needs the public complete Cho selection gate, pinned episode/metric
validation, GPU admission, and the crash-window resolution described above.

## Engineering-only completion implemented

The synthetic parent uses `case_session` from claim through supervised child
completion and terminal receipt. `claim_new` requires a fresh attempt, and
the recorder writes a distinct engineering intent before the success receipt.
An externally pinned attestation digest permits exact recovery after a parent
interruption. Completion reports engineering success separately from measured
evaluation cells. The external binding digest also prevents a coordinated
rewrite of the writable binding and failure records from admitting a retry.
This is a synthetic rehearsal, not a complete selected-source Cho case.

The child cannot call `TargetCaseExecutor.run_case` unchanged: that method
claims attempt 1, publishes a cell, and checks the case cap only after target
prediction returns. Extract fixed-episode prediction and validation into a
child operation that never publishes. Pin the `CasePlan`, attempt, episode,
assets, model recipe and worker executable in the parent-held contract. A
shared output file is insufficient to attribute the proposal to the owned
child. The synthetic result channel now exercises that boundary, but a real
Cho parent must independently check support/query identities, model state,
source and environment pins, deadlines and guards.

This engineering path cannot substitute for the public complete Cho
selection verifier. The proposed selection still requires 5,253 source steps
per case and is refused under the unchanged 256-step ceiling. Connecting a
real engineering child would change fingerprinted source, making the present
exact-source quality and any controls for it historical; refresh those gates
after implementation before claiming current-source readiness.

## Owned Job result channel implemented for synthetic cases

The legacy isolated transaction reads a proposal from a shared output
directory. A cooperating unrelated writer can create identical bytes there.
The engineering integration now uses `run_supervised_with_frame`, while the
existing `run_supervised` path remains available for its historical probe.
The parent creates an anonymous pipe, keeps its read handle private, and
passes only the write handle to the suspended child through a
`STARTUPINFOEXW` inherited-handle list. It assigns and verifies the child in
its private Job Object before resuming it. The launch uses scoped
`bInheritHandles=TRUE` and `EXTENDED_STARTUPINFO_PRESENT`. See Microsoft's
[handle-list attribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[CreateProcessW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw),
and [pipe inheritance](https://learn.microsoft.com/en-us/windows/win32/ipc/pipe-handle-inheritance)
contracts.

The child clears the write handle's inherit flag and sends one size-capped,
length-prefixed canonical proposal. A bounded reader thread drains the pipe
while the parent enforces deadlines and resource floors. The parent accepts
one complete frame after normal whole-Job completion, publishes the proposal
with a fresh no-clobber operation, and pins the observed frame SHA-256 in a
new attestation schema. A shared file with the correct bytes and no frame
fails. Windows tests cover missing, truncated, oversized and duplicate
frames; a grandchild deadline; an unrelated inheritable handle; and the
synthetic recorder's receipt recovery. The combined focused suite passed
73 tests, with one Windows symlink-privilege skip and 26 subtests.

The reader cancels a blocked synchronous read and uses a bounded join during
abort. The supervisor's live sensor and Windows API calls still lack an
independent external watchdog, so the full wall cap is not a proven hard
bound against an unresponsive system call. The handle list prevents ordinary
ambient inheritance, but the write handle is briefly inheritable around
`CreateProcessW`; this is not isolation from a hostile same-user process able
to duplicate or inject process handles. See
Microsoft's [anonymous-pipe operations](https://learn.microsoft.com/en-us/windows/win32/ipc/anonymous-pipe-operations)
and [process access rights](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights).
An atomic job-at-create attribute is a separate possible resolution of the
documented suspended-process crash window; it needs its own implementation
and test on this host before a no-orphan guarantee is claimed.
