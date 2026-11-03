# H0, native G0 and the B0 trust boundary

## Selected architecture and current availability

Use three named roles, without inventing an available provider:

| Role | Proposed responsibility | Qualification authority |
| --- | --- | --- |
| H0: original external host | Bind original host/session and retained process/Job/pipe handles; own original T0, independent stop/resources, complete caller/tool transport and last-writer observation; authenticate bounded source/result-review messages and durable O/M consumption | Independently adopted OS/host basis; never supplied by G0/S0 or inferred from this chat |
| G0: new native outer provider | Fixed source/runtime validation, native creation of S0, bounded I/O/ownership event loop and exact original observations/retention through its assigned boundary | Candidate B0 facet tested under H0; its own reports cannot qualify its guard |
| S0: new native supervisor/driver | One fixed request, closed finite scenario, bounded reply and owned shutdown; later child-driver behavior requires a separate successor | Candidate B1 behavior, driven and observed under H0/G0 dependencies already accepted for the exact claim |

H0 is an **existing external host role required by the original operation**, not
permission to spawn a fourth process or install a new service. No source currently
establishes this provider or its authenticated channel. If the actual host cannot
supply it, the entry is REFUSED_UNADMITTED. An operator, assistant tool session,
file receipt, supplied UUID or child-produced signature is not a substitute.

The first entry contains G0 and S0 only; the reserved single-child position stays
absent. Future child ownership, original117/V34, Q360/S140 discovery and full
pipeline controls remain unqualified. Parentage, containment, working directory,
loaded image/runtime and allowed inheritance must be observed from retained
native objects, not reconstructed from PID or path text after the fact.

H0 remains independent when G0 or S0 fails, blocks, corrupts its own state or
returns misleading evidence. Native private capabilities, actual access isolation,
original parent/Job binding and authority over every owned process must be
established before use. Merely moving code to another process does not prove
isolation or prevent same-user access. Required source/type/effect and OS access
assumptions must be explicit and independently reviewed. Unknown reachability or
ability to alter the host guard is a pre-effect refusal.

B0 trust adoption is an explicit project decision about the actual foundational
OS/host boundary and its evidence. It is not a recursively self-tested project
node. Above that boundary, project-written G0/S0 code still needs independent
source review, bounded actual qualification and result acceptance. During a G0
qualification experiment H0 supplies every substantive guard and completeness
witness; G0 is not its own authority. B1 may use only accepted earlier
capabilities, never a later target or a convenient legacy receipt.

## Proposed native source split and I/O strategy

A future versioned native package has separate units for the H0 ABI/refusal stub,
fixed wire/record codecs, G0 ownership/event loop, S0 finite driver and readonly
build/source manifests. Use bounded buffers, checked arithmetic and a finite
native-call table; no shell commands, dynamic code, arbitrary callbacks, arbitrary
DLL search, ambient writable paths or formatted platform error strings. The
toolchain, headers, libraries, compiler behavior and runtime/build dependencies
need fresh pins and effect review; no build occurs in this design phase.

The selected I/O strategy is a single bounded control loop per native process,
with overlapped named-pipe operations and one retained OVERLAPPED/event/buffer
per pending operation. No read-worker, watcher service or extra helper is added.
The process/thread/handle inventory must prove this in the actual implementation,
including library/OS-created work; a design assertion is not such a proof.

Microsoft documents event-based overlapped pipe I/O as permitting one thread to
serve several handles. The handle must be opened for overlapped I/O, and each
concurrent operation needs its own structure/event. This supports the proposed
strategy, not its runtime qualification.
[Microsoft pipe I/O reference](https://learn.microsoft.com/en-us/windows/win32/ipc/synchronous-and-overlapped-input-and-output).

Creation must establish reviewed Job membership and an explicit inheritance
allowlist before any candidate instruction is allowed to run. The frozen source
uses process-creation attributes; Microsoft's JOB_LIST attribute associates
specified Jobs at creation, and HANDLE_LIST names inheritable real handles.
Support and exact behavior must be checked against the pinned host/runtime;
unsupported or ambiguous attachment refuses. No running-then-attach window is
accepted. [Microsoft creation-attribute reference](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute).

Cancellation is a request, not proof of completion. Retain pending I/O state and
buffers through the actual completion result and owned closure; a cancellation
race can complete normally, abort or fail. Unknown completion at the original
cleanup deadline remains incomplete/UNKNOWN. This rule follows Microsoft's
CancelIoEx contract. [Microsoft cancellation reference](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex).

These API references are documentation, not image/ABI/source pins or evidence of
this device's behavior. All unimplemented native, loader/ABI, access, stop and
failure qualifications remain open. No deprecated launcher is replayed or edited.

## H0 ABI requirements, not a current implementation

The external ABI must provide the following typed operations with original
native provenance. These are requirements on a future provider, not methods
that presently exist in the assistant's tools.

1. bind_admission: authenticate the exact independently reviewed source/runtime/
   build/profile plan and original host session; atomically consume unused O and
   distinct M; retain original native capability objects and source handles.
2. begin_guarded: establish original T0, containment/stop/resources/capture before
   G0 creation or bootstrap effects; cover failed creation and pre-Job routes.
3. observe_owned: bind original image/creation/ancestry/Job and handle transitions,
   QPC intervals, resource samples and complete I/O observations to exact O.
4. freeze_operation: observe G0/S0 exit, original pipe EOF/error, Job closure,
   final inputs and complete original O response; distinguish incomplete capture.
5. publish_metadata: enforce the existing once-only16 roles, independent review
   message provenance, full ledger/census, nonresumable claims and all charged
   writes under the original clock.
6. finalize_metadata: independently observe the final writer/handle/pipe/transport
   boundary and furnish its bounded original retained witness without a self-pin,
   extra report or recursive closure claim.

Operation6 is a specifically unresolved capability/retention gate. No existing
project file or published fact establishes it. If its actual native delivery and
retention cannot satisfy the existing roles and clock, the operation cannot be
accepted. A fitting prefix or successful native exit cannot hide that gap.

## Guards and resource record schedule

All original caps remain in packing.json: whole90/work60/cleanup5/hard65/child55,
suite40/native12/fault2/startup5 seconds; process512MiB/Job768MiB, RAM4GiB,
disk20GiB, one CPU/library thread, hidden GPUs, original stop and owned cleanup.
The child deadline formula and unproved final reserve F/M are unchanged even
though E1 launches no test child. No new clock window is created.

The proposal retains a100ms watch cadence for stop/time/resource servicing.
Its schedule is explicit, not derived from the200ms startup rule: at most901
periodic sample positions in the original90-second interval, two separately
reserved startup samples and at most32 named transition samples, hence935
positions within a1024-record reservation. Transition sites must be enumerated
in the implementation. Do not fabricate catch-up samples after a missed interval.

The two startup samples remain separated by at least200ms; freshness is<=250ms.
Every action uses a genuinely fresh original observation and continuous
independent native enforcement. If a required sample, heartbeat or transition
cannot be serviced or retained, stop/refuse under the original guard; never
omit it to satisfy the quota. Actual latency, native-call bounds, all guards
during final publication and H0 independence remain unproved entry gates.

The80-byte resource layout preserves full native integer values, start/end QPC,
presence/success flags and the first failed call/status. A failed sample stops
at the first failing native query; fields never queried are explicitly absent,
not claimed as measured zero. The exact sampling-call order, immediate native
error capture and every pending/failure path must be implemented and qualified.