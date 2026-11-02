# SC1 source-only implementation contract

2 November 2026. Implements the independently accepted
[SC1 design](cho51_p3_startup_cost_v1/contract.md) in new LP19/LQ19/lplan16
namespaces and a separate sc1 publisher component. This is source-only work.
No executable source, test, AST parser, compiler or native operation is run in
this phase. The new publisher is not used to publish this phase's records.
P remains disabled; Q/QD and child dispatch entry points refuse explicitly.

## Hash scratch and fresh RAM storage

Both retained-reader counterparts allocate their scratch buffer and uint32 read
counter once per `_hash` invocation, lazily after the existing first loop
checkpoint. Every rewind, requested amount, bounded sentinel read, before/after
guard, returned-count check, EOF/growth/short-read rule and fresh SHA state stays.
The counter resets before every ReadFile. An exact immutable copy of validated
returned bytes enters the hash/collection; scratch and pointers never escape.
Each invocation owns its storage. No source/bytes/hash/facts/census cache is added.

LQ19 declares a64-byte `_MemoryStatus` structure with two uint32 and seven uint64
fields. Before Guard native initialization, its layout check requires a64-bit
pointer ABI, size64, alignment8 and all expected field offsets/widths. Every
sample creates a fresh zeroed instance, sets length64 and calls the same RAM
sensor. Disk/private-memory queries, `_Counters`, thresholds, aggregate locking,
time reads and every checkpoint/watchdog call remain. No mutable sample buffer
is shared and no live observation is reused. The native bootstrap sensor stays
unchanged apart from namespace strings in its copied source context.

S06/runtime retention, read_small's full passes, S14 whole-reader verification,
S17 final verification and S07/S18 membership recensus all remain. Original
process/Job/stream/ancestry custody and failure cleanup code are retained. The
two allocation changes have no measured speedup or memory result in this phase.

## Fixed-slot publisher boundary

The sc1 component implements the closed16-role/3,293,184-byte ledger, bounded
payload/review/confirmation handling and original-handle Windows publication.
Root is the sole publisher; peers are read-only message authors. Initialization
requires exact reviewed authority/source pins, the complete fixed path/cap
template, fresh path absence and an irrevocable one-use operation claim. Only
allocation may bootstrap from the complete reviewed in-memory reservation.
All later roles require its verified immutable pin. A failed initialization or
publication consumes the operation and all reservations; no release or resume.

The backend uses the new LQ19 retained reader's existing original-handle APIs.
It retains ordinary ancestry, creates only the exact target exclusively, checks
disk-file/one-link/final-path/native identity before any write, and verifies
original identity/length/full readback plus retained ancestry before closing.
Closure failures remain visible and prevent clean publication. No path reopen
substitutes for original publication readback. Temporary files, sidecars,
overwrites, append, deletion and fallback writers are unavailable.

Peer authentication, cross-session one-use claims and a complete operation
artifact census (including off-directory artifacts) require a supplied trusted
host adapter. The exact census is checked around publication and at close;
unknown, extra or missing artifacts refuse. No concrete production host binding
is provided or inferred from JSON flags. The adapter's message identity/lookup,
claim and complete-census semantics require separate integration and
qualification. An absent or invalid host must refuse;
fake adapters in test sources provide no real authentication/custody evidence.
This boundary is explicit, not a claim that the component can issue admission.

Source review confirmation belongs to contract_adoption; actual review
confirmation belongs to root_disposition. Each complete confirmation envelope
fits8,192 encoded bytes inside its original role cap. Missing, mismatched,
unavailable, consumed or oversized confirmations refuse adoption. Positive
runtime/Q/P/scientific authority is not created by publishing metadata. Complete
UTF-8 capture size, including escaping/chunk envelopes/failure output, is checked;
no raw evidence is silently truncated to fit. A complete changed-Q maximum
capture/output bound remains a separate pre-admission obligation.

## Source closure and tests

The43 predecessor counterpart files are preserved and copied with explicit
LP18/LQ18/lplan15 to LP19/LQ19/lplan16 substitutions and new held namespaces.
The old256-source compatibility roster is retained as inert protocol/library
source. It is not a runnable coverage/admission roster for SC1. Independent
source review must bind the actual union with the added SC1 tests, publisher
sources and this contract. The implementation map names every substantive
change and the source review pins every file in that union.

test_sc1.py adds19 supplied-call methods:11 hash and8 memory. These are test
sources, not passed cases. They use injected byte reads and sensor calls; they
do not establish actual native I/O, ABI, resource failures, NTFS sharing,
watchdog concurrency or custody. H10's original native cap/sharing obligations
remain in inherited sources. The publisher adds33 methods:29 supplied-host/
controller checks and four backend algorithm checks using simulated retained-reader
primitives. All52 new methods are unexecuted and cannot qualify the native backend
or trusted host.

Preserve all516 legacy methods, the additional10 QD methods,36 diagnostic
scenarios and40 planned SC scenarios, with exact new test identities accounted
separately. Textual method enumeration is not executed test collection. A complete
discovery partition and bounded qualification runner still need separate design,
implementation, source review and fresh admission. No full-Q mode loop or second
QD investigation is enabled by this implementation. Source review accepts code
reasoning only; result acceptance uses a different reviewer and scope.

## Preserved limits and next gates

Keep all original90/60/5/65 whole/work/cleanup/hard and child55 boundaries;
QD45/53/55 remain QD-only. Startup5, samples at least200ms apart,250ms freshness,
512/768MiB process/Job,4GiB RAM,20GiB disk, one CPU/library thread, hidden GPUs,
project stop, original ownership and all output partitions remain. No execution
exception, live guard caching or weakened verification is introduced.

Complete-Q timing and output feasibility remain NOT_ESTABLISHED. Next requires
the missing trusted-host/qualification-runner and exact roster/output/measurement
contracts, then independently reviewed implementation before any fresh admission.
Source acceptance itself admits nothing. Historical QD a1f12701 remains
INCOMPLETE_REFUSED for17/16 accounting; all failed charges and extra evidence
remain frozen. Six older probe failures and historical UNKNOWN custody remain.

All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,
1,786 binding loads and3,972 effects remain open. Complete continuation remains
INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional
node/raw-byte findings retain their scope. G2 is INCOMPLETE_REFUSED. No original
package-path custody, continued state, obligation discharge or scientific
eligibility is established. Candidate117/V34 and science stay unexecuted,
accepted scientific cells0/1020 and the final freeze unsigned.
