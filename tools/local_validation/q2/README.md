# Q2 qualification supervisor and retained reader

This version implements only Q under the accepted
[local validation contract](../../../docs/phase2/cho51_p3_local_validation_contract_20261029.md).
It is not bootstrap006, P dependency preparation, L collection, V117/34 or C.
No source file supplies an admission. Frozen v1 and predecessor sources stay exact.

Root owns protocol.py, supervisor.py, child_entry.py, job_adapter.py and
test_protocol.py. q_native_reader_impl authored the initial reader/native tests
and the final caller/watchdog/pipe fixes in invoke_q.ps1, caller_native.cs and
this protocol; Root owns the other integrated fixes.
An independent source reviewer must accept the entire exact source roster.
A different reviewer assesses actual saved results and external tool return.

## Fixed Q operation

A fresh admission binds one UUID, the complete source map in protocol.REQUIRED,
fresh explicit base-runtime pins, the PowerShell executable/version, accepted
source/design review, implementation-specific Q adoption, Q1 failed disposition,
all limits, exact test IDs and the only three modes: suite, badframe and stall.

The suite contains31 immutable foundation methods,29 native-reader methods and
12 protocol methods:72 expected IDs, each executed once, with no skip, expected
failure or unexpected success. Static source counts are not passing outcomes.
The two additional native supervisor controls are separate sequential Jobs:
badframe must refuse trailing bytes; stall must reach its short declared
deadline and terminate its owned Job. These are explicit controls in the single
Q operation, not retries of the suite or new use of an old UUID.

All three Jobs are unnamed and noninherited, with atomic Job-list assignment
during suspended CreateProcessW. Query-back-verified kill-on-close,
512MiB process/768MiB Job and one-active-process limits precede resume.
Only the anonymous result-pipe writer appears in the inherited handle list.
The parent owns the original reader, Job and process/thread handles. Original
process creation FILETIME and PID are descriptive evidence, never a reopen key.
No PID/tree sweep or unrelated-process termination occurs.

The frozen framed supervision primitive is loaded from pinned bytes. The new
adapter preserves its framing and cleanup path and adds atomic Job assignment,
aggregate and process-count limits, handle tracking and generation observation.
The original migration adapter is not edited or run as an old launcher.

## Runtime and input custody

The outer reviewed PowerShell body is executed from the same bytes checked by
Root's tool bootstrap. It retains read-only, read-sharing FileStreams for the
admission, all sources/runtime files and review/adoption inputs. The Python
supervisor is compiled from the exact verified in-memory bytes, not reopened
after a hash. Child code paths are pinned and held through use by that parent.

The twenty-one-input source map includes the ten Q files and the immutable
foundation, primitive, policy, design, Q2 supplement and Q1 failure inputs.
The [Q2 supplement](../../../docs/phase2/cho51_p3_q2_bootstrap_contract_20261029.md)
requires independent review of the explicit treatment of Q1's unknown custody.
Q1 remains consumed and unreleased; Q2 does not prove its cleanup or cause.
The version2 adoption binds the supplement's exact digest before admission.

Q2 creates a bounded bootstrap journal through an original read/write handle
with read sharing only. Root's external verified dispatch binds the fresh
canonical operation filename and source bytes. This small diagnostic effect
precedes internal authority checks and does not admit compilation or a child.
The caller and guard use a separate shared journal lock;32 records,4096 bytes
per record and64KiB total are hard bounds. Every append flushes and reads back
through the original handle. Stage/fault records carry original caller PID,
creation FILETIME, UTC and QPC; these are not PID reopen keys. The original
journal closes while the guard is still active; original journal closure and
subsequent guard shutdown are included in final external evidence. Partial or
missing journal data never imply cleanup. A direct-action50ms stop deadline is
armed before fault logging, so diagnostics cannot defer a substantive stop.
An independent original-clock5s timer covers startup, including journal and
runspace setup. Readiness must be observed before5s to disarm it. An independent
1s timer also bounds guard shutdown. The65s whole-caller fallback remains.

After an external create-once
claim, the caller compiles exact verified caller_native.cs bytes in memory via
PowerShell Add-Type. This is an expressly admitted Q bootstrap effect, not
static inspection or the later P preparation stage. No OutputAssembly, disk
assembly output, compiler subprocess or package installation is requested.
PowerShell's in-process .NET compiler, framework loading and host initialization
are trusted platform behavior; their transitive images are not fully attested.
The original clock includes compilation. Before any pin or compiler effect,
the caller caches its original current-process SafeHandle and binds a managed
Action directly to that Process object's Kill() method. A built-in .NET
CancellationTokenSource arms that action for the original origin plus65 seconds.
It runs independently of PowerShell's runspace; no PowerShell callback is used.
The timer and original process handle remain live through final publication,
input/output closure and external JSON emission. Uncertain file closure invokes
that same original-process action rather than releasing its protection.

A dedicated PowerShell runspace runs the exact inline guard contained in the
pinned caller source. Its setup is covered by the managed65-second timer; no
input pin, claim, compilation or child effect occurs until the guard records
two successful samples at least200ms apart. The guard loads the trusted host's
System.Diagnostics.PerformanceCounter assembly by name, without Add-Type, and
samples local PDH Memory/Available Bytes through NextSample().RawValue. It
requires NumberOfItems64 and compares exact Int64 bytes to4GiB, avoiding float
rounding. It checks disk20GiB, caller512MiB private memory, ordinary stop-file
ancestry and actual missing-leaf status, and the original work deadline every
100ms. A sensor error, interval over250ms, resource fault, stop or time fault
directly invokes the original process's managed Kill action; no PID reopen or
PowerShell callback runspace is needed. These immediate faults deliberately
refuse the caller rather than offering a new cleanup window.

The guard receives the original cached Process object, direct Action, original
UTC/QPC origins and a synchronized state table through PowerShell.Create,
AddScript/AddArgument and BeginInvoke in its own runspace. Its process-cache
accesses share a monitor with caller accesses. The host .NET assembly loader,
PerformanceCounter/PDH, runspace initialization/scheduling and managed timer are
trusted bootstrap platform behavior, not a newly attested dependency closure.
The guard remains active during source/runtime pinning, Add-Type, native owner
operation/cleanup, record publication and original input/output file closure.
It then stops and joins within one second before the final external JSON return;
failure invokes the same original-process action. The original65-second timer
stays armed during this shutdown and final return emission. Caller records
save the guard's exact first/second samples, minima, count and pending-shutdown
status; the external return records actual joined/closed status and final
minima/counters. A record never claims its future guard shutdown has occurred.
The native watchdog supplies additional independent100ms active checks after
compilation. These sampled guards are not a hard RAM cap on PowerShell.

The native helper creates and verifies an unnamed, noninherited outer Job before
CreateProcessW. Atomic Job-list assignment contains the supervisor and its one
active child with hard512MiB process/768MiB aggregate and two-process limits.
Native process/thread output is stored directly in an owner field; managed
bookkeeping failure cannot lose the native handles. Standard output/error and
an owned NUL input are the only explicitly inherited outer handles. The outer
Job handle is never inherited, and caller exit closes its kill-on-close handle.

Python uses -I -S -B and a new absent pycache prefix; the caller refuses root
zip/_pth/venv configuration. The Q base recipe contains python.exe, root DLLs,
Lib .py files excluding site-packages and __pycache__, and DLLs .py/.pyd/.dll.
It is freshly enumerated and compared before and after the operation. Python
search paths are reduced to the admitted Lib, DLLs and runtime root; no project
package search path or third-party site initialization is installed. Namespace
packages and project modules are constructed from verified source bytes.

The native reader holds file and ancestor handles against ordinary write/delete
opens, requires fixed local NTFS, checks full128-bit identity, final native
spelling, regular-file type, one hardlink and no reparse/device attributes.
Hashes stream in64KiB chunks. Real supported operations use the original handles;
close failures remain failures. observe_tree resamples an explicit bounded
suffix/exclusion recipe, including membership and directory identity, before
and after observation and on verify. Directory handles alone do not freeze names.

Reader ceilings are25,000 files,4GiB total,2GiB each, depth32,25,000 directories
and50,000 enumerated entries. Q itself narrows its retained bootstrap to2,000
files/64MiB/16MiB each. Foundation8MiB/200,000-node representation bounds remain
stricter where applicable. This qualification does not inventory a package
closure or qualify future third-party/native-loader behavior.

## Effects and result transfer

Suite fixtures are created only under the new attempt/fixtures directory.
Fixtures are tiny synthetic byte strings in .json files, including deliberately
malformed data for refusal/byte checks; they contain no data or weights.
The native tests cover actual writer/delete/rename exclusion, hardlinks,
retained identities, output collisions/readbacks and small filesystem recipes.
Reparse attributes and selected failure paths are instrumented; no real
OS-created reparse fixture is qualified. No unavailable fixture is called a pass.

Python audit restrictions reject unlisted ordinary reads, writes outside owned
fixtures/results, network, subprocess APIs, symlink creation and undeclared
ctypes DLLs. Reviewed native calls have fixed purposes and roots; audit hooks
are defense in depth, not an OS sandbox. The standard Windows kernel,
filesystem, Python bootstrap and PowerShell/.NET host are declared trusted
platform components. Their entire transitive loaded-image sets are not
cryptographically authenticated by this Q observation. A hostile same-account
actor, privileged injection or preexisting writable mapping is outside scope.

The child reports test IDs, counts, failures, fixture totals and bounded text
through a length-prefixed anonymous pipe. The original pipe and sole child
writer establish this narrow transfer; a later pathname/hash is not substituted.
The parent requires exact framing through EOF and complete Job/process closure,
then saves the frame with protected create-new original output handles, flush
and same-handle readback. Child failures are retained as reports before refusal
when a complete frame exists. On protocol failure, partial fixture bytes and
the failure/custody record remain; no successful payload is invented.

Native output limits:8MiB each,64MiB/256 files total. Fixture use is additionally
checked at240 files/48MiB, leaving room for bounded parent records. Each caller
stream and result frame is at most1MiB; normal reports are smaller. Caller
records use original create-new FileStreams, flush/readback, then close only
after the supervisor and Job have been reaped. Outer standard output/error
capture uses two owned anonymous pipes. Only their writer ends and the owned
NUL input are in the outer inherited handle list. Parent writer originals close
after native creation on both success and failure paths. Two C# reader threads
use fixed4KiB read chunks and retain at most1MiB each; an overflowing chunk
immediately refuses and terminates the owned Job. Each pipe requests a4KiB
kernel buffer; actual OS buffer sizing is trusted platform behavior. No stdio
file grows while the supervisor runs; sampled file length is not a capture cap.

The readers must reach strict EOF and join. A stalled reader is canceled with
CancelSynchronousIo using its own original noninherited duplicated thread
handle, then joined within the shared cleanup deadline. Original reader/thread
handles close only after joining. Join failure retains originals and
self-terminates the caller; no thread/PID reopening occurs. Caller records
include EOF, overflow, retained/observed bytes, cancellation and original
reader/writer/thread closure. Strict UTF-8 decoding follows bounded EOF capture.
The inner child result channel retains its separate framing/EOF requirements.
The caller's1MiB serialized-record cap can additionally refuse an unusually
large combined/escaped stdio report; it never relaxes the pipe limits.

## Time, resources and stop

All clocks start at the external caller's original UTC/QPC sample. Pinning,
startup samples, bootstrap, all Jobs, verification and publication share the
90-second ceiling. Work stops at60 seconds; owned termination/reap is bounded
within5 seconds. The suite's40-second child deadline and each fault probe's
2-second deadline are clamped to the remaining original work interval. No
fresh full-stage clock is created at child dispatch.

The supervisor's independent watchdog samples every100ms, records resource/stop
faults and exits within5 seconds when work cannot stop. Process exit closes its
noninherited kill-on-close Job. The external caller uses original native process,
thread and Job handles, checks memory/disk/stop every100ms and stops work at60
seconds. Its watchdog terminates the owned outer Job on fault and self-terminates
the caller if the fault persists for5 seconds. The native watchdog stays active
during accounting, Job termination, original-process reap and pipe drain/cancel.
Normal cleanup shares one5-second budget for all drains, joins and termination.
The watchdog stops/joins only immediately before original native handle closure.
The independent managed65-second fallback stays armed through later publication
and original input/output file closure. An actual
external return after90 seconds cannot be accepted.

Both caller and supervisor explicitly observe their own512MiB private-memory
ceilings. The caller's private-memory ceiling is sampled; the supervisor also
has the outer Job hard cap, and the child has both nested Job caps. Two startup RAM
samples are at least200ms apart. Active floors remain4GiB available RAM and
20GiB free disk. Cooperative native checkpoints run before/after64KiB chunks;
the watchdog and caller cover blocked child/native work. Threads are1 for
numerical-library environments and GPUs hidden; Q imports no numerical library.

PROJECT_STOP.json present or unknown refuses/stops owned work. Missing leaf
must be observed under existing ordinary ancestry. No shared cache is cleared.
Failed admissions/claims and output namespaces are consumed; no automatic retry.

## Records and acceptance

protocol.py defines closed admission/adoption/test-report fields. Claim,
dispatch, deadlines, payload, receipt and caller return have versioned fixed
output fields in their producers. A source review must bind the exact REQUIRED
map and name independent authors/reviewer. The Root Q adoption binds contract,
design review and implementation review before the admission is issued.
The Q1 failed disposition is pinned predecessor context, not launch authority.
Its actual review and disposition are both retained source inputs. The original
foundation's accepted sources remain unchanged.

Order: source acceptance -> Q contract adoption -> fresh bounded admission ->
create-once external claim -> same-source supervisor -> create-once attempt ->
three declared dispatches -> preserved reports/custody/resources -> original
handle closure, strict outer-pipe EOF and protected record readback -> genuine tool return -> different
actual reviewer -> Root Q qualification. The external audit preserves the
actual tool chunk/session/exit/wall time plus before/after UTC/QPC observations.
No record hashes itself or a future result. Pending flags are immutable and
resolved only by later accepted records.

Acceptance needs all72 suite outcomes, both expected native fault refusals,
complete original owned lifecycle for each Job, exact unchanged source/runtime
pins, resource floors/peaks, original handle and stream closure, actual caller
and tool return in the original window, independent review and Root adoption.
This still does not complete all26 design scenarios, the original48 custody
cases, the117 candidates or34 successor controls.

historical_custody_closed, historical_operation_released, historical_retry_allowed,
restart_qualified, boundary_qualified, complete_dependency_closure,
launch_authorized and scientific_admission all remain explicitly false.
Bootstrap004 stays consumed, diagnostics005 held,006 unadmitted, historical
custody UNRESOLVED, science0/1020 and final freeze unsigned.

Mechanism references: [explicit inherited handles and Job lists](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[unnamed noninherited Jobs](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjectw),
and [Windows file sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

