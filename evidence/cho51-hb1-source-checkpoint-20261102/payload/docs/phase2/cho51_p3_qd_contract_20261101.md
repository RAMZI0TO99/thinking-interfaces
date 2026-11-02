# QD startup-prefix implementation contract

1 November2026. Engineering only. LP18/LQ18/lplan15 implement a bounded diagnostic
successor to the [accepted design](cho51_p3_startup_timing_design_20261101.md).
This supplement is source, not an execution grant, runtime qualification or
result acceptance. P remains disabled. The exact source-review/adoption and
admission records must be separate, fresh and tied to this version.

## Scope and typed authority

The request has the25 exact keys specified by the frozen design, schema
`cho51_startup_timing_admission_v1`, stage`QD`, purpose`QD_STARTUP_PREFIX_ONLY`
and stop point`BEFORE_MODE_LOOP`. It binds exact design, event-format and stage
hashes, names derived from its canonical UUID, and128/512/65536/45/53/55 limits.
The exact32 probe identities and all eight old Q modes remain in the request as
unexecuted obligations. They cannot select execution. The prefix supervisor has
no mode loop, suite collection or child fault dispatch. LP18 P entry points
refuse. No conversion of QD into a Q request is permitted.

Review status is`ACCEPTED_SOURCE_QD1`; adoption status is`ADOPTED_QD_ONLY` under
the existing closed`cho51_q_contract_adoption_v2` schema. The loader, actual
caller, P-bootstrap-control harness and supplied bootstrap join explicitly
accept QD. Role`P_Q_CONTROL` denotes the two unchanged bootstrap checks inside
QD; it does not run P preparation. The old accepted bootstrap qualification
and all of its native identity/source/actual-review joins remain prerequisites.
The inert LP18 P caller embeds the same loader for source equality but throws
before any operational effect.

Supervisor, caller-saved and external returns use respectively
`cho51_startup_timing_supervisor_return_v1`,
`cho51_startup_timing_caller_return_v1` and
`cho51_startup_timing_external_return_v1`. Claims and receipt likewise have
diagnostic-specific schemas. Existing custody, artifact, allocation and false
authority fields remain. Added fields are`diagnostic_outcome`,
`diagnostic_prefix_complete`,`timing`,`required_q_obligations_complete` and
`qualification_accepted`. Every Q-acceptance flag is always false. A successful
external prefix is only`prefix_pending_review`; exit0 is never qualification.
Failure is`incomplete` or`custody_unknown`. The saved caller record precedes
stream closure and therefore cannot claim a completed prefix.

## Journals and implementation amendment

The frozen design remains unchanged. This implementation makes one explicit
conservative publication amendment: caller C01–C08 and the header are buffered
until the existing C08 managed-helper compile provides the reviewed native
directory API. The caller then reserves and creates its journal before C09.
The buffer is limited to32 records/16KiB and shares the final sequence. No extra
bootstrap compiler, loader, clock reset, thread, pipe or writable handoff is
introduced. Failure before publication can lose the buffer; those timings are
UNKNOWN. This narrower durable coverage needs explicit independent source
acceptance and does not amend startup5 or permit a positive early-failure claim.

Supervisor initial16/8KiB and total early32/16KiB buffers remain as designed;
publication follows normal source/runtime/census/review verification. Journal
files are fixed canonical absolute paths under the QD phase directory. Caller
native identity is the existing lowercase16-hex volume plus colon plus32-hex
raw file-ID string. Supervisor identity uses the closed
`cho51_lv_native_identity_v1` descriptor. Neither is process custody by itself.

The two native append owners retain independent ordinary NTFS/fixed-volume
ancestry handles, at most32 per owner, and CreateNew read/write file handles
with read sharing only. They reject reparse/device/hardlink/alias identities,
retain the full65,536-byte charge before create, preserve failed charges,
bound each append, flush, and verify original identity/length/full content.
Final readback and ancestry checks occur before seal. Original-handle readback
replays the full closed event graph through a fresh validator for each
role. Caller records use the same pure PowerShell validator before buffering or
append and during a bounded65,536-byte native original-handle replay callback.
Supervisor records use the Python validator before append and on original
readback. Byte/hash equality alone does not satisfy event validation. Original
file/ancestry disposal supplies post-close fields; the seal itself claims only
readiness to close. Incomplete constructor/close evidence cannot count as
observed custody. Torn or failed writes remain unrepaired.

Events have only the frozen closed fields/tokens. All clocks/counters other
than version1 are canonical decimal strings. Python UTC ticks use integer
days/seconds/microseconds with the preserved seventh original UTC digit; no
float conversion of native clock identity. Normal<=122 and final<=6 are
capacity pools, not sequence ranges. Success traces have59 caller and42
supervisor records. No padding, reset, borrowing or normal work after a failure
is permitted. Caller file/byte counters remain null where unavailable;
supervisor retention counters count completed files and bytes only. There is
no per-file telemetry or additional sensor poller.

## Stage and guard correspondence

The50 frozen stages retain their substantive operation order. Caller C01–C08
cover bootstrap, guard readiness, admission, pins, review, UTC controls and
managed compilation; C09–C11 retain native helper/empty-Job controls and platform
mapping; C12 contains only declared C13–C21 native build spans; C22 keeps both
bootstrap checks; C23–C25 retain runtime/configuration and original supervisor
launch/custody. C26–C28 cover final retained inputs/artifacts/tools and original
stream/ancestry closure; C29 seals the separate timing journal. Supervisor
S01–S15 retain entry/authority/pins/handoffs/claim/environment, S16 marks the
stop before the former mode loop, and S17–S21 retain full final verification,
census, outputs/input close and journal seal/close.

The unchanged outer envelope is90 whole/60 work/5 cleanup/65 hard seconds,
startup5 with two samples at least200ms apart,250ms freshness,512/768MiB
process/Job,4GiB startup/active RAM,20GiB disk, one CPU/library thread, hidden
GPUs and the existing project stop file. Q's child55 boundary remains an
unexecuted full-Q obligation. QD adds strict original-clock45 prefix,
53 verification and55 publication limits; equality refuses. Caller changes to
53 when dispatching so it may wait for supervisor final verification; the
supervisor itself retains45 through S16. Both change to55 only after their
live-guard final input/census/artifact verification. Supervisor S19 verifies
existing outputs below53; its new receipt publication/readback may use55.
Both roles recheck the original55 clock after watchdog/guard shutdown, directly
before publishing the serialized external return and after output. Crossing
the boundary prevents exit0 even if a positive frame was already emitted.
Original60/65 remain armed.
There is no new dispatch origin or extension. Cleanup-only relaxed callbacks
cannot establish final verification or a successful prefix.

## Allocation and admission assessment

The unchanged whole allocation is256 files/64MiB, largest file8MiB, partitioned
caller40/20MiB, supervisor40/8MiB, fixtures160/32MiB, closeout16/4MiB. Caller
adds one65,536-byte journal to the existing19 slots:20 slots and conservative
17,039,360 bytes. Supervisor reserves only claim4096, receipt1,048,576 and
journal65,536:3 files/1,118,208 bytes. No suite fixture file is created; empty
fixture census is checked before positive return. Bootstrap-control fixture
charges remain separate and unchanged. Conservative whole bound is199 files
and55,906,304 bytes. Raw journals are not copied into stdout or the caller
record; only bounded references are returned. Failed reservations are retained.

The common LP/Q source set remains exactly256 files. Helpers are inline in
existing source slots. lplan15 is an inert namespace counterpart, with no new
probe/codec/continuation execution. Fresh source and runtime hash inventories,
independent source review, an unused UUID/output namespace, current resources,
reviewed allowed command and expected outputs are required before any admission.
Assessing readiness does not dispatch a process or create a reusable grant.

## Qualification obligations and claims

The frozen36 T01–T36 scenarios remain obligations. Ten new pure methods cover
integer/tick conversion, watermarks, early buffer, finite traces, event refusal,
failure tail, torn records and exact QD admission/roster. They are unexecuted;
they do not establish native closure, denied opens, partial initialization,
short writes, real resource/stop faults, full capacity or timing feasibility.
Inherited Q test methods are retained and unexecuted in this successor. A fresh
separately reviewed qualification partition is required before calling them
passed. At most one separately admitted diagnostic investigation may precede
full Q, as the design allows; its result still requires a different independent
actual reviewer and can establish only the observed prefix and owned lifecycle.

All six previous failed Q attempts remain consumed. Previous UNKNOWN caller/
outer/bootstrap custody remains UNKNOWN. Complete fresh probe32,100 and384
cohorts with every control are still required before integration. All18,793
resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786
binding loads and3,972 effects remain open. Complete continuation remains
INFEASIBLE_UNDER_CURRENT_GUARDS (at least31,002 rows against24,000); G2 is
INCOMPLETE_REFUSED. No original-package-path custody, continued state or debt
discharge is established. Candidate117/V34 and science remain unexecuted,
scientific cells0/1020 and final freeze unsigned.
