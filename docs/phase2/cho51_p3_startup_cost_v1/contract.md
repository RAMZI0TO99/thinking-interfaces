# SC1 design contract

2 November 2026. Design only. Preserve all substantive guards and obligations;
P remains disabled. The parent [QD execution record](../cho51_p3_qd_execution_20261102.md)
is a refused operation with supported timing and lifecycle observations. This
design neither repairs it nor spends a second diagnostic admission.

## Selected improvements

**SC-H: invocation-local hash scratch.** Both LP18 and LQ18 retained readers
allocate a new byte buffer and read counter on every iteration of `_hash`.
A future successor may allocate one buffer of `min(65_536, length + 1)` bytes
and one unsigned 32-bit read counter per hash invocation. Allocate lazily at
the first existing loop checkpoint, after rewind and before its first read.
Retain the same checks before and immediately after every ReadFile call.
Reset the counter before each call. The requested amount remains exactly
`min(65_536, length - count + 1)`, including the one-byte growth/EOF sentinel.
Its original 1..65,536 check remains on every iteration. Native failure,
oversized returned length, premature EOF and extra data still refuse.

Every invocation owns a new SHA-256 state and performs a fresh rewind and full
read. Copy only the validated returned bytes into an independent immutable
chunk before hashing or collecting it. No scratch view or pointer escapes.
The buffer, counter and chunks cannot be shared with another invocation,
reader, thread or process. Reentrant calls have independent local storage.
Short positive reads remain legal; their bytes are accumulated as before.
No assumption that a ReadFile fills its request may reduce checks or bounds.
An empty file still requires an actual read proving EOF. Poisoned unused tail
bytes must never enter a hash, returned data or record.

The maximum scratch capacity is 65,536 bytes; no growing pool is introduced.
An exact immutable chunk adds at most 65,536 bytes at a time. Existing collected
chunks and their final immutable join retain their original aggregate and
per-file bounds. This is an allocation argument, not a measured process-memory
or timing result. If a precondition or allocation fails, ordinary refusal and
owned cleanup remain; no fallback weakens checks or reopens a file by path.

**SC-M: declared memory-status layout, fresh instances.** Guard.sample currently
creates a 64-byte raw buffer and two ctypes views per RAM query. A successor
may declare the MEMORYSTATUSEX layout once, with unsigned 32-bit length/load
followed by seven unsigned 64-bit fields. Require size64, alignment8 and the
available-physical-memory offset16 on the admitted 64-bit Windows ABI before
using it. Instantiate a fresh zeroed structure per sample; set length64 and
perform the same GlobalMemoryStatusEx call. The disk query, fresh `_Counters`
instance, GetCurrentProcess/GetProcessMemoryInfo calls, aggregate lock updates,
threshold comparisons and elapsed-time read remain in the same order.

Only layout declarations are reused. Every foreground and watchdog sample
owns independent mutable storage and reads fresh observations. Do not cache
RAM, disk, private bytes, stop/cache presence, QPC, UTC, custody or exceptions.
Keep every checkpoint, the independent watchdog, its fault/cleanup behavior,
startup samples and all current sensing cadence. No serialized sample bottleneck,
new lock, new thread or altered threshold is part of SC-M. ABI mismatch refuses;
it is not grounds to select an unreviewed fallback.

SC-H applies equally to the LP/Q reader counterparts in a new namespace. SC-M
applies to the supervisor/child Guard implementation where actually used; it
does not replace the already-qualified native bootstrap RAM sensor. A changed
source set must include exact dependency closure, counterpart comparison and
fresh independent source review. No implementation name or version in this
document is a runnable grant.

## Work that remains deliberately unchanged

The source map distinguishes measured stages from their internal work. S14
includes a whole-reader verify in addition to bundle/PE checks; it is not a
measurement of PE parsing alone. Preserve all of the following:

- Independent source/runtime retention, original handle identities and full hashes.
- Both hashes in read_small, fresh pre/post facts and every ancestry checkpoint.
- S14 whole-reader verification and the separate S17 final full verification.
- Runtime membership recensus at S07 and S18; directory custody is not membership.
- Three narrowly authenticated handoffs and ordinary readers' strict sharing.
- Fresh native compiler/build artifacts, tool verification and original writer
  custody through consumers; no prebuilt artifact cache or preclock compilation.
- All native bundle identity/PE/export checks and before/after-use verification.
- Original process generation, Job, pipe, thread, watchdog, stream and ancestry
  ownership, including partially initialized and failure paths.

Per-reader WinDLL/prototype setup already happens once. There is no repeated
per-file DLL binding to remove. Reusing `_facts` scratch is deferred: it adds
alias/reset complexity without an isolated cost measurement. Sensor reuse,
fewer checks, merging hashes, skipping verification, cached census, parallel
processes and shifting work outside the admitted clock are rejected here.

## Complete Q: a closed feasibility gate

The unchanged Q rosters contain 32 probe, 100 supplied-mechanism and 384 inherited
methods: 516 distinct methods. Each cohort still needs eight UTC controls, two
actual fault controls, five native observer controls, two bootstrap controls
and three sharing checks. Sharing checks already in the inherited384 are not
counted again in the distinct union. Probe actual acceptance precedes separate
100 admission, then separate384 admission. No partial aggregation or redistribution
of a cohort's controls across clocks is allowed.

The ten TimingFormatTests added by QD are additional unexecuted obligations.
Copying the old collector would include them in its inherited group and violate
the exact384 gate. A successor must explicitly partition all discovered IDs:
the preserved516, these10, and any newly implemented SC checks, with exact
membership and no overlap/omission/skip. Do not simply raise384, filter additions
away, or mislabel the36 diagnostic scenarios as36 test methods. The supplied
old rosters in feasibility.json are a held reference, not new namespace IDs or
admission. An implementation-specific reviewed roster and finite qualification
runner remain prerequisites. No new qualification partition is admitted here.

Every complete-Q budget must include caller startup/native build/controls;
supervisor source/runtime/bundle retention; all eight sequential mode launches,
child startup/retention, suite and supplied probe/transport verification;
five native cases, malformed-frame and intentional-stall control; every child
closure; both final verification passes; final census/output readback and
publication; owned cleanup; and explicit margin. The intentional stall's
expected timeout must be distinguished from a native-case timeout, which fails.
Every per-mode cap stays as narrow as the existing contract (suite at most40,
native mode at most12, fault mode at most2 seconds, additionally constrained
by remaining original time). Do not treat those caps as observed durations.

Keep the absolute child55 boundary, work60, cleanup5, hard65 and whole90 from
the original caller origin. A future Q dispatcher must explicitly prove every
child deadline is no later than original55 and the tighter per-mode bound;
the old `remaining - 5` expression is not an independently reviewed substitute
for a complete successor timing contract. Final verification must complete
under live work guards, never a cleanup-only callback. Original hard limits
remain armed through owned closure. QD45/53/55 remain unchanged for QD; they
cannot be reinterpreted as a new full-Q admission or time reset.

feasibility.json carries exact arithmetic and unknown terms. As an illustration
only, the observed QD prefix37.7609334 plus tail7.6913694 leaves14.5476972
seconds before work60 for all missing Q work, or12.5476972 with a proposed
2-second planning margin. Those are subtraction results, not validated Q
budgets: child costs, full-Q final/output costs and variance are not measured
by QD. The 104-second sum of eight mode caps also proves no lower bound and
cannot establish impossibility. Prior accepted codec operations show feasibility
for their older exact source/runtime operations only.

Complete-Q timing feasibility is NOT_ESTABLISHED. Full-Q output/transport bounds
for the changed successor are likewise NOT_ESTABLISHED until every runtime and
metadata copy, failure frame and serialized tool envelope is bounded against
its fixed partition. Design review accepts this negative readiness decision,
not a claim that these optimizations will save enough time. No retry follows.

## Fixed-slot metadata publication

metadata-ownership.json retains the 16 named closeout roles and their original
3,293,184-byte reservation sum within16 files/4MiB. It applies prospectively to
a new operation with new exact paths; all old ledgers remain immutable.
Root is the sole filesystem publisher for operation metadata. Source and actual
reviewers send bounded text in chat only. They neither create review sidecars nor
rename/copy/write an operation slot. Independent judgment remains theirs: Root
records authorship, exact review text and its digest, and requests confirmation
of the published bytes from that reviewer before adopting the result.

Before launch, freeze the full16-role ledger, canonical paths, caps, payload
schemas, source/runtime/review references, writer implementation and capture
transport. Confirm source/adoption reviews and transport compatibility before
admission. Allocation has one explicit bootstrap exception to the later ledger-pin
requirement: before any create, Root verifies the reviewed writer/design/source
pins and the complete closed in-memory16-role ledger against that fixed template,
checks each unused path and every cap, and charges all16 reservations. Allocation
is then the first exclusive CreateNew. It does not supply or claim a self-hash.
Immediately after create, before any payload write, verify the returned original
handle is an ordinary disk file with one link, exact canonical final path and
native identity, using the same post-create rules as every other role below.
Original-handle identity/length/full-readback verification and successful closure
yield its immutable pin, which every subsequent role requires before create.
If allocation creation, verification or closure fails, the metadata UUID and
all16 charges remain consumed; no other role may be created and no runtime may
be admitted. Preserve any partial ledger and record the bounded failure in the
original chat/tool trace, without inventing an out-of-ledger file. Reserve all
unused/failure roles at full caps. There is no slot reassignment, retry-to-new-path,
borrowing, overwrite, deletion or repair.

Roles are named in every delegation, with an explicit no-files instruction.
Review text can remain in a bounded in-memory draft while findings are resolved;
publish each role only once after that role's evidence is complete. If another
review is needed after an immutable role was published, record a bounded refusal
in an unused designated refusal-capable slot; do not invent a seventeenth output.
No sidecar is exempt because it lives outside the operation directory. Copies,
temporary files and exports produced for this operation also count.

Before create, the publisher validates canonical path, ordinary retained
ancestry, source authority, role/schema, complete UTF-8 encoded size, exact
reservation and target absence. Every non-allocation role also verifies the
already-created immutable ledger pin. The absent target has no file identity or
link count yet. Exclusive CreateNew must return the original handle. Immediately
after create and before any payload write, validate ordinary disk-file type,
one link, exact canonical final path and native identity from that handle;
record that identity as the original witness. This same order applies to
allocation and every other role. Failed checks close the owned handle under the
reviewed failure path, preserve the created artifact and keep its full charge.
Only then write within the reservation, flush, verify original identity/length/
full content by original-handle readback, recheck retained ancestry and close
under the reviewed metadata contract. A partial write stays consumed and preserved. It never
falls back to apply_patch, a shell redirection, append or a temporary file.
Reuse of the old pathname-based metadata helper alone does not prove these
prospective original-handle requirements; its successor needs source review.

Review identity is not a field that Root can self-certify. The already-reserved
`contract_adoption` slot stores the source review's postpublication confirmation
before admission. The already-reserved `root_disposition` slot stores the actual
review's postpublication confirmation before result adoption. Each confirmation
contains the peer/delegation identity, exact published review path/bytes/hash,
review-text digest and full bounded confirmation message. Reserve at most8,192
encoded bytes for that confirmation envelope within each existing role cap;
the rest of the role's payload must fit its remaining cap. Confirmation cannot
live only in a later message while adoption claims it has been persisted.

Root's transcription is disclosed and does not replace peer judgment. Missing,
mismatched, oversized or unconfirmed text, or an unavailable/consumed destination
slot, prohibits adoption. Publish a refusal only if its designated existing slot
is still unused and its full payload fits; otherwise keep the refusal in the
original chat/tool trace with no further operation file. Never modify the review
slot or invent a confirmation sidecar. A negative peer confirmation is retained
as refusal, not rewritten into approval. Later read-only closeout comments
cannot alter an immutable disposition or create a further operation file.
Control metadata contains no authority to execute arbitrary paths or expand slots.

Pre-dispatch admission must bound the complete raw tool capture representation,
including JSON escaping, envelope fields, all chunks and stderr/failure paths.
A 1MiB runtime stream bound does not prove a 1MiB escaped capture fits. The
unchanged65,536-byte external derivative and1MiB raw-capture slots must hold
their complete respective payloads. If a proved maximum does not fit, admission
is refused pending a separately reviewed representation/allocation successor
within unchanged partition caps. This design does not silently tighten stream
guards or truncate evidence to fit. An unexpected post-run overflow retains all
charges and triggers refusal with unavailable evidence/custody stated honestly.

Global documentation updates are separately declared design/handoff work. They
cannot host a displaced operation review or raw capture to evade its partition.
The SC1 design files themselves belong to this new source-only design phase,
not to the already-consumed QD operation or a future runtime ledger.

## Preserved authority and unresolved work

All time, memory, disk, startup/freshness, stop, one-thread/hidden-GPU, stream,
native ownership and output caps remain. No resource exception is requested.
P entry points stay disabled. Original-package-path custody, continued state,
debt discharge, G2 completion and scientific eligibility are not established.
All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,
1,786 binding loads and3,972 effects remain open. Complete continuation remains
INFEASIBLE_UNDER_CURRENT_GUARDS (at least31,002 rows against24,000). Conditional
node/raw-byte findings retain scope; G2 is INCOMPLETE_REFUSED. Candidate117/V34
and science are unexecuted, scientific cells0/1020, final freeze unsigned.
