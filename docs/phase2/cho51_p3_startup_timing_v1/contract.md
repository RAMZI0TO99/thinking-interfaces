# QD startup-prefix contract

## Purpose and authority

This is a design proposal under the existing project execution policy and local
validation contract. It does not edit either frozen contract. Implementation must
have a new namespace and explicit source comparison with LP17/LQ17/lplan14.
Root's later implementation-specific adoption must bind the independent source
review, this accepted design and the exact QD-only purpose before any admission.

The closed request kind is `cho51_startup_timing_admission_v1`, with purpose
`QD_STARTUP_PREFIX_ONLY` and stop point `BEFORE_MODE_LOOP`. No selectable full-Q,
P, package discovery, test collection or continuation mode exists in this first
successor. QD is allowed to investigate implementation startup without claiming
that the implementation has already passed Q. It cannot supply a Q qualification
predecessor, replace required controls or unlock P/L/V/C. This breaks no
qualification prerequisite: its only possible positive claim is an independently
reviewed diagnostic prefix, while the qualification prerequisite remains unmet.

Admission binds one fresh UUID and unused namespace, exact command and caller
origin, source/runtime/helper/host pins, independent review/adoption, local stop,
exclusions, original resource envelope, output reservations, fixed stage/format
version, soft diagnostic watermarks and expected artifacts. No prior operation is
replayed. Current source closure must fit the unchanged 256 common-source cap;
it may replace namespace counterparts and an implementation contract, but may not
omit a live dependency to make the count fit. Actual implementation closure and
runtime feasibility remain unproven. Changed byte identity requires review/pins.

The native bootstrap qualification and its exact retained chain remain required
as in the predecessor. QD must not load a helper using only a historical digest,
bypass bootstrap identity checks, substitute a successful Q return, or treat the
older startup-D contract as a grant. Any new journal primitive is initially
source-reviewed and unqualified; its first admitted QD use is an investigation,
not self-certification. Its adversarial qualification cases remain obligations
until genuinely executed under separately reviewed admission.

## Measured scope and unchanged execution

Execute the selected caller and supervisor prefix in the original order, with
every existing sensor invocation, startup sample, predicate, native build/check,
pin/hash/census and authority check intact. Additional markers snapshot counters;
they never replace or cache availability, stop, identity or custody predicates.
Do not move expensive work outside the clock, warm caches, skip source bytes,
reuse builds, kill unrelated processes or alter CPU affinity to obtain a pass.

Stop immediately before `lq17/supervisor.py`'s current `for mode in protocol.MODES`
at line391. Do not load mode primitives/adapters, construct a dispatch/deadline
record for a nonexistent child, run suite discovery or call its production probe.
Record a fixed `prefix_stop` marker. Existing caller-side native/bootstrap
fixture controls still run and close; their observed results are not full Q.

The map in stages.json distinguishes caller spans, supervisor spans and external
closure witnesses. A nested native-build span may contain named component spans;
inclusive durations must not be added as disjoint costs. Parent waiting and child
execution overlap. Attribute only complete local spans, never causal bottlenecks.
Counts describe completed loop work, not authorization or complete scope. An
open begin supplies a lower-bounded elapsed observation to the last witnessed
timestamp, not an end, complete duration or successful stage.

Initial supervisor entry/admission/import/Guard/native-reader events are buffered
in a fixed 16-record/8-KiB scratch buffer through S03 end, charged to the same final 128-record
sequence, not extra events or output. They use the original caller domain already
passed by the caller; domain validation must succeed before publication. No event
before the first actual instrumentation point is fabricated. Before durable
publication, process loss leaves those events UNKNOWN.

## Journal custody and earliest publication

Keep the existing bootstrap journal unchanged. New names are exactly
`timing-caller_<UUID>.jsonl` and `timing-supervisor_<UUID>.jsonl`, under the new
operation's fixed phase directory. Reserve one full 64-KiB file in the respective
caller/supervisor bucket before any creation, including creation failure.

The caller can create its journal only in the existing bootstrap-journal window:
original UTC/QPC and independent hard/startup/fault deadlines armed, canonical
admission path/operation and caller identity established. Record authority as
pending until the existing review/adoption transition succeeds. Journal creation
does not grant authority to native compilation, supervisor dispatch or Q tests.
No extra work precedes deadline arming or delays/refactors bootstrap checks.

The supervisor journal uses a **new reviewed native create-new append primitive**,
not repeated calls to immutable `RetainedOutputs.write`. To avoid weakening the
existing authority order, v1 deliberately delays physical creation until the
normal source/runtime retention, exact census and review/adoption chain have
all succeeded (current supervisor line347). Before then, bounded timestamps stay
in memory. Extend the buffer to at most 32 records/16-KiB for the full early prefix;
the initial 16/8-KiB limit is its earlier subphase, not a second allocation.
Create no journal on a failed chain. This knowingly leaves early killed startup
unresolved; a durable preauthority journal would require a separate design.

After authority, validate fixed local NTFS ancestry with original retained
directory handles, canonical spelling, non-reparse/non-device/no-hardlink type
and unique native file identity. Create with no inherited handle and no external
write/delete sharing. The supervisor owns its file; the caller never precreates
or shares a writable journal. Keep the exact existing three caller artifact
handoffs and import/read/write audit policy unchanged. A journal capability is
limited to its single fixed path, native handle, operation and reserved capacity;
it admits no arbitrary pathname write. The future primitive must use the existing
qualified API spellings and native identity conventions, not invent a new loader.

Each journal owner retains its own bounded ancestry handles through journal
closure, independently of the immutable-input reader's lifetime. At most 32
extra directory handles per owner are allowed; they remain part of the same
process resource accounting and existing directory ceilings. No borrowed handle
is closed, no original input handle is released early and no cap is reset in a
new object. Every handle has an explicit partial-construction/finally owner.

Encode one closed-format ASCII JSON line at a time, at most512 bytes including
LF and no BOM, before append. Reserve its byte/event charge before the first
write. One owning thread writes; no new background writer, queue, polling thread,
pipe or child handle is introduced. Snapshot existing guard counters under their
existing synchronization; no new sensor query is triggered for telemetry.
Only sequence, bytes, stage progress and explicitly defined successful pin/retain
file/byte counters are new. No paths, source text, exception text, stack, environment,
patient data, model data or free-form strings are permitted.

Reserve capacity for at most122 normal records and at most six final records,
with their sum at most128. These are capacity pools, not absolute sequence-index
ranges: every actual record uses the next contiguous sequence starting at0.
Header and ordinary paired/prefix-stop records consume the normal pool. First
failure, one optional secondary journal-fault marker, the ready-to-close mark and
terminal consume the final pool. Entering the final pool permanently forbids
normal records; unused normal capacity cannot expand the six-record final pool,
and unused final capacity cannot expand the122-record normal pool. A normal
caller trace has57 normal plus two final records, with terminal sequence58; the
supervisor has40 normal plus two final records, with terminal sequence41. There
is no padding, gap or sequence reset. Overflow of any cap, unknown field/token, invalid sequence or
append/flush/readback fault latches refusal and stops new work. Do not drop,
truncate, overwrite, rotate, retry or release failed charges to manufacture a
valid journal. Preserve a partial file as forensic bytes. A torn final line is
not a valid event; the raw file is retained without repair and cannot be accepted.

After the first failure, stop normal stage markers. The reserved-capacity tail permits
only the first failure marker, at most one secondary journal-fault marker, the
owner's ready-to-close mark if reachable, and one terminal record. No repeated
cleanup-error logging is allowed. Cleanup itself always continues through its
original owned path, with its independent original return fields supplying the
post-close evidence. Missing normal stages keep the trace incomplete; this
defined failed suffix can never be promoted to a complete prefix observation.

Each append has the existing live checkpoint before and after bounded encoding
and I/O, plus the original independent watchdog/hard deadline. Do not claim a
Windows I/O call has a deterministic duration. Flush on publication of the early
buffer, stage ends and seal; include this cost in the operation. A journal fault
must not mask the original substantive fault or postpone owned termination.
Cleanup may attempt bounded closure under the existing cleanup machinery; it
does not resurrect a failed work checkpoint to write a successful final event.

## Verification, closure and result types

After the intentional prefix stop, execute the original supervisor retained-input
verification and complete runtime recensus, plus output verification. Then do
the original caller `VerifyCallerInputs`, final original native/tool/artifact
rechecks, stream/Job/process closure, original-file closure, guard shutdown and
external return. Original work/cleanup guards remain active in their original
roles throughout. Failure cleanup's relaxed reader callback must never count as
successful final verification. Partial initialization, including Guard before the
old try/finally boundary, must have an explicit cleanup owner in the successor.

The append primitive seals only after all intended local records are complete.
It flushes, checks original identity/length and hashes the exact original bytes
with bounded live checks, then closes its file and ancestry handles exactly once.
Its seal record means `ready_for_original_close`, not `closed`. Native readback
after seal covers the seal bytes too. The supervisor return, outer caller record
and external tool return supply separate post-close witnesses; no journal can
certify its own close. Caller guard shutdown and external-return timing are
observed in the original return/journal lifecycle fields after timing-file close,
not falsely emitted into a file already closed. Failures may leave no seal.

Use disjoint `cho51_startup_timing_supervisor_return_v1` and
`cho51_startup_timing_external_return_v1` schemas. They bind operation/admission,
original clock, producer native identity, both exact journal descriptors where
available, stage completion, unchanged mapping/helper/native artifact joins,
final verification and original owned lifecycle evidence. Preserve all existing
caller custody fields; stricter Q parsers must reject these diagnostic schemas.
Exit0 alone establishes nothing. Do not put timing lines into stdout/stderr or a
strict child result frame: the outer return stays one bounded structured record
with file references, not journal copies. Exact original tool chunks remain
retained with integer-preserving parsing.

Possible actual dispositions are `OBSERVED_PREFIX_ONLY`, `INCOMPLETE_REFUSED`
and `CUSTODY_UNKNOWN`. Only a different actual reviewer and Root can adopt the
first, after complete selected prefix, valid journals, full final verification,
fresh pins/census, exact allocation and complete original closure. All dispositions
have `qualification_accepted=false`, `probe_observation_accepted=false`,
`p_admitted=false`, `obligations_discharged=0`. A diagnostic cannot enter a Q
aggregate, P preparation, continuation/codec frame or scientific result.

### Closed admission and return interface

The QD admission has exactly these22 predecessor field names: `schema`, `stage`,
`operation_id`, `created_utc`, `expires_utc`, `root`, `python`, `runtime`,
`caller_runtime`, `sources`, `review`, `adoption`, `predecessor`, `limits`,
`modes`, `expected_tests`, `forbidden`, `scientific_admission`, `compiler`,
`native_compiler`, `bootstrap_qualification`, `bootstrap_controls`; plus
`purpose`, `stop_point` and `timing`, making25 keys. `schema` is the QD kind above
and `stage` is exactly`QD`. All nested predecessor field schemas, current pins,
runtime recipes, effects and native bootstrap qualification checks remain intact
under the new typed validator. `expected_tests` retains the exact held32 probe
roster as an unexecuted obligation; `modes` retains the full original Q mode list
as an unexecuted obligation. Neither field dispatches anything in QD. No empty
roster makes a pass.

`timing` has exactly `design_sha256`, `format_sha256`, `stages_sha256`,
`caller_name`, `supervisor_name`, `records`, `record_bytes`, `journal_bytes`,
`prefix_seconds`, `verification_seconds`, `publication_seconds`. Hashes bind the
adopted exact design/interface sources; filenames derive from this UUID, never
free paths. Numeric limits are exactly128,512,65536,45,53,55 respectively. Refuse
extra keys, alternatives, changed values or different scalar types.

Version every affected bootstrap/caller/control schema consumer so QD
authentication is explicit. Common pure field checks may be factored; never
strip QD fields, relabel its admission Q or present an adapted object as evidence
that the original Q schema accepted it. Source review must map every inherited
check to its successor with identical substantive conditions. The exact source
cap remains a separate implementation gate.

For supervisor, saved caller, receipt and external returns, preserve the exact
baseline custody/allocation/artifact fields and semantics. Replace the schema
tag with its QD counterpart; existing Q acceptance Booleans remain false. Add
exactly `diagnostic_outcome`, `diagnostic_prefix_complete`, `timing`,
`required_q_obligations_complete`, `qualification_accepted`. The final two are
always false. `diagnostic_outcome` is `prefix_pending_review`, `incomplete` or
`custody_unknown`; it is not an independent actual disposition. `timing` has
exactly `caller` and `supervisor`, each null when unavailable or a closed object
with `path`, `bytes`, `sha256`, `native_identity`, `records`, `sealed`,
`original_file_closed`, `original_ancestry_closed`. A role reports only facts it
witnessed; the supervisor's caller slot is null and Root joins the two original
records. Nulls/failed closure prevent positive final diagnostic adoption.

Implementation review must materialize these derived exact field sets from the
pinned baseline; arbitrary extra legacy fields are forbidden. Existing bounded
receipt/stream limits apply; adding references grants no extra bytes.

## Finite allocation and time reservations

| Partition | Unchanged cap | Diagnostic addition within the cap |
| --- | --- | --- |
| Caller |40 files /20 MiB| One64-KiB timing journal; fixed predecessor19 named slots become at most20 |
| Supervisor |40 files /8 MiB| QD has exactly claim, receipt and one64-KiB timing journal; no suite/control/probe outputs |
| Fixtures |160 files /32 MiB| No new fixture outputs in QD; unused capacity is not transferred |
| Closeout |16 files /4 MiB| Exact admission/return/review/diagnostic metadata uses reserved slots; no free sidecar files |
| Whole |256 files /64 MiB; existing8-MiB per-file cap| Two journals consume131,072 bytes; duplicate/export copies require their own charge |

The predecessor conservative caller upper bound16,973,824 plus65,536 is17,039,360
bytes, below20 MiB. QD's supervisor claim is additionally capped at4,096 bytes,
its receipt at1,048,576 and its journal at65,536: three files/1,118,208 bytes.
No payload, test report, per-mode dispatch/deadline or six probe artifacts are
created in this prefix-only purpose. Even reserving the entire existing fixture
and closeout partitions gives199 files/55,906,304 bytes, below256/67,108,864.
These are static proposed allocation bounds, not observed resource use. The
implementation must prove its exact output ledger including every native fixture,
failed write and raw-copy reservation. Unknown outputs or inability to prove the
sum refuse admission; they cannot borrow unused capacity or raise any cap.
The fixture-writer limits, six-file498,123-byte probe envelope (unused in QD),
all expanded-state/history caps and immutable failed reservations are unchanged.

Retain90 whole /60 work /5 cleanup /65 hard seconds, startup5, two startup samples
at least200ms apart, existing250ms guard freshness,512/768 MiB process/Job,
4 GiB startup/active RAM,20 GiB disk, one CPU/library thread and hidden GPUs.
The original Q child55-second boundary is not reset or relaxed; QD creates no
such child, and any later full-Q successor must retain it. Existing bootstrap
fixture child deadlines and process/Job limits remain enforced.

Propose tighter QD watermarks measured from the **same original caller origin**:
prefix end strictly before45 seconds; full verification before53; local
publication/closeout before55; equality refuses at each watermark. Retain the
remaining5 seconds inside the60-second work budget as margin.
These are reservations and early-refusal thresholds, not measured upper bounds.
They add no time. Do not begin another selected work stage once its watermark or
the declared remaining verification/publication reserve cannot fit. Live checks
enforce watermarks within stages; the original earlier fault starts its original
bounded cleanup, with hard65 still independent. No deadline is renewed at dispatch,
prefix stop, verification, journal seal or failure.

Historical intervals justify this limited investigation, but do not prove it fits.
Native append, flush/readback, extra ancestry, counters and full verification costs
remain unmeasured. Before QD admission, source review must establish bounded work,
all original and new cleanup paths and exact allocation; Root must record a finite
per-stage/reserve ledger, fresh pins/resources/stop and an unused operation. Its
purpose may be a bounded attempted observation that fails safely; it cannot be
advertised as guaranteed completion or prequalified. If those safety/allocation
gates cannot be met, refuse admission rather than loosen the envelope.

Full Q remains held. Reopening it needs distinct reviewed source and an explicit
evidence-based complete-stage budget with margin, covering suite, all controls,
both final verifications and cleanup. A successful prefix or low CPU/RAM snapshot
alone is insufficient. No automatic retry or automatic transition follows QD.
