# SC1 fixed-slot publisher — source only

These five files implement the fixed-slot state machine and its retained
Windows handle backend. They are unintegrated, unqualified source. No publisher,
test, project import, native operation or runtime launcher was executed to
implement this component. There is no CLI, default trusted host, automatic phase
creation, admission dispatcher or operational integration.

`publisher.py` owns exactly the accepted 16 roles and 3,293,184 reserved bytes
within the 16-file/4,194,304-byte envelope. Its fixed prospective namespace is
`D:/Aenv/pro3/runs/coordination/cho51_p3_sc1_publication_v1`; this directory has
not been created by this component. Every path is `<role>_<canonical-uuid>.json`.
It cannot reuse the historical QD directory. Failed and unused charges remain
reserved. There is no output overwrite, deletion, temp file, fallback file,
replacement role, append, retry or reservation release.

## Supplied capabilities and remaining host gate

`FixedSlotPublisher(authority_raw, authority_pin, host=..., backend=...,
checkpoint=...)` validates a closed, bounded authority. `create_native_publisher`
constructs the real backend explicitly but still requires the supplied host and
live checkpoint. Construction is not runtime admission. A fake backend supports
future pure tests only; it cannot supply native qualification evidence.

The future reviewed host must provide three synchronous, bounded capabilities:

- `claim_operation(operation_id, authority_pin)` atomically consumes an unused
  UUID for Root across sessions and returns the exact closed metadata-only claim
  checked in `_consume`. Consumption must survive a failure before allocation
  exists. Failure cleanup can request this bookkeeping after a guard refusal;
  it must not launch work or create an uncharged project record. The call is
  never retried. An unknown claim is reported as UNKNOWN and cannot continue.
- `peer_message(reviewer, message_id)` returns original authenticated UTF-8 JSON
  bytes from the delegated peer. It must independently bind identity, message
  provenance and delegation. Echoing caller JSON or accepting a boolean approval
  is not an implementation of this capability. Source and actual reviewers must
  differ from the authors and each other. Reviewers never publish a file.
- `operation_artifacts(operation_id)` returns the complete operation census as
  the closed object `{operation_id, paths}`. It must include off-directory
  copies, sidecars, partial files and outputs created by other actors. The
  publisher requires equality with the exact files it has created, and checks
  before/after each create and at close. A local directory listing alone cannot
  establish this global attribution claim. A seventeenth, unknown or missing
  artifact refuses even when byte headroom remains.

**The concrete trusted-host binding does not exist in this source change.** Its
identity/message provenance, durable one-use consumption without a seventeenth
record, complete operation census, bounded failure behavior and checkpoints
require separate design, implementation, independent review and qualification.
The host must pin the actual loaded writer, interpreter/import resolution and
runtime, preserve the live stop/time/RAM/disk/process guards, and bind a future
reviewed admission. Native source-file pins alone cannot prove loaded-code
identity. No supplied record or Python object authenticates itself. With no
valid host binding, production publication must remain unavailable.

The source manifest requires this package's implementation, LQ19 native reader,
the v1 record primitives and the accepted SC1 contract/ownership/qualification
documents. Additional dependency/host/runtime proof sources belong in the
reviewed bounded manifest. Up to 512 source entries, 16 MiB per source and 64 MiB
total retained inputs/publications are allowed; stricter future live guards
remain authoritative. The input authority is at most 1 MiB. The capture proof
is an exact source pin, not a claim that any current transport bound has been
proved. A peer's source authorization must match the complete source/capture
map and fixed phase. The exact writer source pins bind the immutable template.

## State transitions and payloads

`initialize()` consumes the UUID, authenticates exact source authority, retains
and verifies pinned inputs/ordinary ancestry, checks all 16 absences and creates
only the allocation ledger. All 16 full charges already exist in memory before
the first create. Original readback and successful original file/ancestry
closure yield the allocation pin. Every later role verifies that immutable pin,
the original native identity and all retained inputs before its exclusive
create. There is no circular allocation self-hash.

`publish_record(role, text)` handles only the nine ordinary text-record roles.
The source-confirmation slot must exist and be positive before the metadata
`admission` role can be written. Every role has a fixed closed envelope and body
schema; supplied text cannot alter its fields or grant authority. `CLOSED` means
owned metadata handles closed after final verification, not that all reservations
were used or that Q/P/science succeeded. All envelopes and snapshots explicitly
keep runtime admission, qualification acceptance, P admission and scientific
admission false.

`publish_capture(chunks, external_text)` preserves full original tool-response
strings, including original failures/stderr text in those supplied chunks.
Both complete encoded envelopes must fit their independently reviewed maxima
before either create. The bounded encoder accounts for JSON escaping, UTF-8
validity, chunk/envelope overhead and newline. It rejects floats, nonfinite
numbers, invalid surrogates, cycles, oversized depth/nodes and excess bytes.
It neither truncates nor parses native payload numbers; large FILETIME/file-ID
values remain in their exact original strings. The trusted transport must still
prove it supplied every chunk and complete failure paths. Capture is metadata,
not native custody evidence.

`publish_review` retrieves a bounded authenticated peer message, checks its
exact text digest, role and independent reviewer identity, and publishes that
immutable message. `confirm_review` retrieves a new authenticated message that
names the published path/length/SHA256 and review-text digest. Its full encoded
confirmation must fit 8,192 bytes within the already-reserved destination cap.
Source confirmation is stored only in `contract_adoption`; actual confirmation
only in `root_disposition`. A negative confirmation is preserved there as
INCOMPLETE_REFUSED and cannot authorize adoption. Missing, mismatch, overflow or
an unavailable/consumed destination consumes the transaction without a fallback.
Review corrections stay messages; the original published bytes remain immutable.

Any mutating failure on an active transaction consumes it and every reservation.
Partial files remain. A failed operation cannot initialize, publish, repair or
resume. Cleanup runs on owned handles and retains close errors separately from
the primary failure. There is no successful publication following unknown close.
Returned pins are independent copies, so caller mutation cannot alter retained
allocation/native authority. Read-only snapshots do not alter the state.

## Native backend contract

`native_backend.py` uses the reviewed LQ19 `RetainedReader` private API:
`_check`, `_open`, `_facts`, `_hash`, `_close_handle`, retained `_directories`,
and public `retain_directory`, `retain`, `read_small`, `verify`, `close`.
Changing any of those contracts requires fresh source review. The backend does
not change or bypass their strict NTFS/fixed-drive/path/sharing/identity checks.

The input reader retains original source/ancestry handles. Each publication
uses an independently owned retained-ancestry reader. `_open(create=True)` uses
CREATE_NEW and validates the original ordinary disk file, one link, exact final
path and native identity before it returns; no payload is written beforehand.
Writes are bounded to 65,536-byte requests, then flushed. The original handle
is rewound and fully read/hashed, with identity, length, final facts, source pins
and ancestry rechecked. Its original file handle and ancestry are then closed.
Only successful closure produces a publication reference. A failed close is
reported and never retried through a possibly reused numeric handle. Subsequent
verification retains/rechecks the saved native identity and complete pin.
IDs remain exact hexadecimal strings, never floating-point numbers.

## Unexecuted coverage and qualification gaps

`test_publisher.py` contains **33 unexecuted methods**: 29 pure controller/fake
backend methods and four backend-algorithm methods using simulated retained
reader/API primitives. These scenarios are executable source to review, not
passing results or native qualification. There is no direct test CLI here.

| Accepted obligation | Assertions supplied in the test source | Evidence still required |
| --- | --- | --- |
| O01 | Exact ledger/caps, 16 precreate absences, bootstrap failure, ledger recheck, one-use model | Real exclusive-create/readback/closure; durable host claim |
| O02 | Authenticated-lookup model, exact source authorization, distinct peers/authors | Real delegation and message provenance/Root binding |
| O03 | Designated confirmation slots, exact pins/digests, negative/missing/mismatch/overflow | Actual peer confirmation and native persisted bytes |
| O04 | Unknown/off-directory artifact and late census refusal | Complete trusted-host operation attribution/census |
| O05 | Occupied slot refusal and original-facts-before-write traces | NTFS race/reparse/hardlink/alias/sharing/native ancestry faults |
| O06 | Complete envelope/escaping boundary and stricter proof bound | Complete actual transport, failure-path and output feasibility proof |
| O07 | Short write/readback/identity/flush/close model faults and closure ordering | Actual native fault behavior and custody evidence |
| O08 | Consumed UUID/charges, invalid mutations and 17-unit refusal | Durable cross-session no-resume behavior |
| O09 | Unsupported transport refuses before any create | Qualified dispatch integration (currently absent) |
| O10 | Review/counterconfirmation corrections cannot overwrite or use another slot | Actual native immutability/sharing |
| O11 | Exact raw strings/large integers; no alias into internal pins | Completeness of real transport; capture never proves native custody |
| O12 | Separate refused actual review/disposition; all authority flags false | Independent actual evidence review after separately admitted work |

The four backend tests verify the algorithm against a deliberate API model;
they do not establish real Windows fact gathering, ABI, filesystem sharing,
resource timing, stop behavior or cleanup. The complete qualification roster,
bounded runner, output/timing feasibility and fresh admission are later gates.
No SC scenario is discharged by source review. QD does not qualify Q. The prior
`a1f12701` remains INCOMPLETE_REFUSED at 17/16; its files are untouched. Complete-Q
feasibility remains NOT_ESTABLISHED, P stays disabled, and every open resolver,
G2, 117-case/34-control and scientific obligation is unchanged.
