# Bounded startup diagnostic proposal

31 October 2026. **Draft for Root and independent design review.** This file
authorizes no execution, source change, helper loading or retry. Only this new
document was written; all L, LQ2/LP2 sources and records remain frozen.

## Evidence and smallest next step

LP2 operation a29c2264-da0e-4306-9bc8-f7c1fea976af returned exit1 with empty tool
output after5.553409 seconds. Its journal ends at assembly_loaded; source places
PerformanceCounter('Memory','Available Bytes') construction before the next
counter_created marker. This identifies the last observed boundary, not a
proved deadlock, timer branch, termination reason or closed caller. The
[failure review](../../runs/coordination/cho51_p3_loader_implementation_20261031_p2/failure_a29c2264-da0e-4306-9bc8-f7c1fea976af/actual-review.json)
and [Root disposition](../../runs/coordination/cho51_p3_loader_implementation_20261031_p2/failure_a29c2264-da0e-4306-9bc8-f7c1fea976af/root-disposition.json)
preserve FAILED_STARTUP_CONSUMED_CLOSURE_UNPROVEN and hold further unchanged P.

Q2's first operation0a56af13-c1f2-47e7-b521-c9ad09123712 has the same last
observed boundary and unresolved closure. Its later separately admitted
operation611baed2-cdb9-4ac5-aa67-091058962ec3 completed356 methods and five native
cases in51.0094698 seconds with accepted owned lifecycle evidence. That
[review](../../runs/coordination/cho51_p3_loader_implementation_20261031_q2/actual-review.json)
does not explain or close either failure.

Recommend **D1 only**: use the exact retained Q-qualified PNative helper to
guard a diagnostic controller and own one fresh pwsh child probing the PDH
constructor. Add stage markers and externally schedule owned Dispose at the
original5-second boundary. No old caller, P preparation, Python/package/candidate
import, collection or production bootstrap redesign is part of D1.

## Existing helper and authority dependency

Both frozen callers arm managed timers against their cached original Process
handle, open a journal and start a PowerShell runspace. It loads the performance
counter assembly and constructs the counter before establishing two resource
samples. Admission/hash/review/adoption checks occur afterward. The direct
Process.Kill delegate has no persisted reason or final cleanup receipt if it
terminates its own caller.

LP2 loads its qualified PE only after authority_verified. PNative.Owner creates
an empty unnamed kill-on-close Job, verifies4096MiB process/5120MiB Job limits
and starts a watchdog. Sample directly calls GlobalMemoryStatusEx,
GetDiskFreeSpaceExW and GetProcessMemoryInfo; Check also checks stop and the
original clock. This path does not use PDH. The
[Q qualification](../../runs/coordination/cho51_p3_loader_implementation_20261031_q2/root-qualification.json)
binds its complete native-helper reference:21504 bytes, SHA256
4308e2243171f0670f5e25fa6594aab87b22b23f77e8d2f820d6c2489e5d8f84, plus native
identity and original writer/receiver continuity. D1 must consume that exact
record, not infer authority from this digest alone.

Owner.Start atomically creates a suspended owned child with original process/
thread handles and stdout/stderr pipes. Dispose terminates an active owned Job,
confirms empty Job, waits the original process, drains/joins captures/watchdog
and closes original handles within at most5 seconds. Its internal work/hard
ceilings are240/245 seconds; they do not enforce D1's5-second stop.

Sample returns RAM and updates disk minima/private maxima. Aggregate fields
must retain those names; they are not contemporaneous raw readings. Successful
Sample enforces all three native resource predicates. Private P/Invoke reflection,
new native compilation and pre-guard Add-Type are excluded. This P helper cannot
serve as Q's governing512/768MiB guard.

Moving the helper load/constructor before a PDH guard is a new bootstrap effect
order. Existing qualification does not authorize that move. A fresh, closed,
independently reviewed Root capsule/adoption must authorize only D1's exact
retained helper load, empty Job/native guard and one fixed probe. Relevant
authority joins precede those effects; there is no full P dispatch.

## Finite new sources and review

Assign ownership before implementing only:

| New file | Responsibility |
| --- | --- |
| tools/local_validation/startup1/diagnostic.ps1 | Capsule/pins, original origin, native guard, exact probe, deadline delegate and original-handle receipt |
| tools/local_validation/startup1/pdh_probe.ps1 | Bounded assembly/constructor/sample/dispose markers and no other workload |
| tools/local_validation/startup1/test_diagnostic.py | Supplied-record/faithful-owner-seam controls, with separately reviewed fresh Q integration |

Reuse the existing qualified managed PE unchanged. A fresh mechanism Q operation
must qualify this new controller/probe/delegate use before D1 admission. Its
existing PDH bootstrap may itself refuse and consume its UUID. No automatic
retry, unqualified fallback or self-qualification follows; any alternative Q
bootstrap requires separate review.

The capsule binds exact caller/probe bytes, caller runtime closure, helper,
accepted source/Q reviews and Root qualification, UUID, interval, stop, roots,
P-shaped resource role and exact commands/effects. Validate closed types,
duplicate keys, size/depth/node bounds, review roles/independence/order and hashes
from original strict read streams before load. No unchecked nested path or
expression is authority. Retain sharing/ancestry and final byte checks.

The first helper load uses explicitly reviewed bootstrap trust and exact retained
bytes. Do not claim a native ID was checked before load when its reader is inside
that helper. Compare the original retained ID immediately afterward, before
construction/sampling/Job effects. Independent review must accept this precise
ordering and inspect assembly initializer/dependency behavior. Missing authority
or continuity refuses.

## Shared original interval and guard

D1 explicitly adopts P-shaped caps:4096MiB caller/child,5120MiB Job,4GiB startup/
active RAM,20GiB disk, one library thread, hidden GPUs and the project stop.
It is not a Q512/768 operation. Work stops at original elapsed5 seconds; owned
child cleanup ends by original elapsed10, and all publication/closure plus genuine
external return fit an admitted original15-second whole interval. These are
smaller bounds within P300/240/5; Q90, P300, startup5 and cleanup5 are not enlarged.

Capture one external UTC/QPC origin at entry; arm the direct managed hard-kill
delegate on the cached original controller Process handle before pin/load work.
Authority/load/guard/probe all consume that same interval. Before RAM is known,
permit only the explicitly admitted trusted bootstrap operations, with available
managed stop/disk/private checks and the hard deadline. No child dispatch occurs
until two successful native Sample calls at least200ms apart and a healthy
independent guard are established before original elapsed5 seconds. Log native
call start/end, returned RAM, honest disk-minimum/private-maximum fields and
predicate outcome. A load/JIT/sensor stall still refuses.

After full D authority and guard readiness, Start creates exactly one fresh
pwsh with NoProfile/NonInteractive, the pinned probe and fixed origin/deadline
arguments. Its three-argument interface inherits an explicitly cleared/
allowlisted controller environment, restored in finally. Retained source sharing
and final checks protect the probe read. Verify atomic Job limits/membership
before resume. The child gets only Owner's owned stdio; no nested subprocess.
The absolute probe deadline remains original elapsed5 seconds. Do not give the
child another5 seconds or dispatch when useful time no longer remains.

Probe markers are assembly_load_begin/end, counter_ctor_begin/end,
first_sample_begin/end and counter_dispose_begin/end, sequenced with the inherited
origin and flushed to owned bounded stdout. Do not clear, repair, prewarm or
reconfigure PDH. A marker proves only its recorded boundary.

## Exact timeout ownership and candid evidence

Register a **direct managed Action bound to this Owner.Dispose** with a
CancellationToken source scheduled for the remaining milliseconds to original
elapsed5 seconds. No PowerShell scriptblock is a timer callback. A simple fixed
path waits for cancellation, then disposes/joins the cancellation registration
before reading any Owner completion state, all under the independent controller
hard deadline.

Prevent overlapping Owner APIs: no main-thread Poll, ExitCode or Dispose while
the callback can close handles. Its ordinary disposed Boolean is not a
synchronization/join guarantee. Registration completion must be established;
observing token cancellation or disposed alone is insufficient. Refuse any
variant that cannot establish this exclusive ownership. No early-exit optimization
is needed.

The native watchdog stays active during probe/Dispose cleanup. Source review must
also establish resource/stop guard coverage through final retained publication,
after Dispose stops that watchdog. A bounded guard may continue calling the
already loaded Sample method only if review explicitly accepts its post-Dispose
safety: it uses current-process APIs, not the closed Job. Keep250ms freshness,
the original stop/private/disk checks and actual guard join/closure evidence.
If this lifecycle cannot be established with the unchanged helper, return for
a separate successor rather than leave an unguarded tail.

Retain original controller identity, intended absolute timer deadline, exact
delegate target, cancellation observation and registration join. Retain Owner's
original child generation, limits/membership/resume, Reaped, JobEmpty/JobClosed,
ProcessClosed/ThreadClosed/InputClosed, both EOF and reader/writer/thread closure,
WatchdogJoined, overflow/errors and partial marker bytes. Create-new outputs
retain original writers and same-handle byte/ID checks; final-check all inputs.
Preserve existing1MiB streams,8MiB JSON,64MiB/256 outputs and64KiB journal caps.

Dispose closes the process handle, so ExitCode may be unavailable on this fixed
path. Record that fact and precise reason; never reopen by PID. No passing child
or positive startup/P/Q qualification follows. A diagnostic may establish its
scheduled deadline path and completed registered Dispose with exact closure
flags. It cannot thereby prove the actual TerminateJobObject branch/native
return (not exposed), exclude natural exit just before disposal, or assign an
old exit1 to a particular cause. Mark those facts unobserved.

If exact native termination reason/exit is required beyond this limited scope,
a separately reviewed/Q-qualified owner successor is necessary. A controller
death, callback/guard/journal/stream/handle gap remains UNPROVEN with consumed UUID.
Do not act on historical failed processes. Genuine external tool return and
independent actual review are mandatory; no synthetic closure follows from exit1.

## Qualification and next decision

Fresh supplied-record/seam controls cover stale capsule/helper/source/roles/
windows; no effect before authority; shared5-second origin and late dispatch;
two200ms-spaced samples and250ms freshness/resource boundaries; exact managed
delegate target/schedule/registration join; exclusive Owner handle access;
sticky faults; partial creation/pipes; missing/malformed/oversized markers;
stalled-probe disposal; honest unavailable exit/cause; and final retained
publication/guard closure. Freeze actual method counts only when the roster exists.

Separately admitted owned Windows controls exercise a benign fast probe and an
intentionally blocked probe, timer/registration completion, empty Job/original
reap/EOF and all cleanup flags. Seams and actual controls are distinct claims.
Independent review may accept only the observed diagnostic scope or preserve
failure/unknown. Root then selects a P successor if justified; none is authorized
here. The original failures, bootstrap004, historical custody and frozen receipts
remain unchanged;005 held,006 unadmitted, candidates117/controls34 unexecuted,
scientific cells0/1020 and final freeze unsigned.
