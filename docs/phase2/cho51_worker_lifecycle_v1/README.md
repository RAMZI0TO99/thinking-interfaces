# Synthetic numerical engineering worker lifecycle candidate

`run_engineering_case(recorder, plan, *, context, workspace, backend, verifier)`
holds the unchanged real `CaseRecorder.case_session` identity lock from fresh
`claim_new(attempt=1)` through backend execution, two independent verifier calls,
durable parent attestation and `record_engineering_success`. It never calls
`record_cell`. Canonical completion must report one engineering success and zero
measured cases.

The frozen context requires the exact 1,020 adopted plans, independently pinned
owner decision and canonical execution-source metadata, a physical parent pins
file, a separate fixture source provenance and environment digest. Every case
uses subjects 02–52, four methods, seeds 11/23/37/53/71, five shots and repetition
one. The selected integration rehearsal uses subject 02/seed 11 for four
engineering cases. Subject 01 and retries are refused.

The claim's exact payload, worker, source, environment, engineering-only scope,
envelope and physical bytes must match the independently supplied context.
Fixture fingerprints remain distinct from the independently pinned canonical
execution source. Live fixture source and environment are rechecked before
claiming, before attestation and before terminal publication. The request is
written exclusively outside the recorder; its SHA is the physical digest of
canonical JSON plus a newline. `load_worker_request` reconstructs its exact
serialized schema. Workspace ancestors must remain direct and owned.

Backend and verifier are explicit synthetic engineering callbacks. The reviewed
operational implementation must launch and independently check real native
Jobs; a caller-created `VerifiedWorkerProof` alone establishes no native fact.
The immutable proof binds request, case, physical claim, source, environment,
owner, pins, native receipt and qualification digests; measured peaks and the
exact eight numerical fixture updates must fit the reviewed caps. EEGNet,
LaBraM linear and LoRA use 2/3 GiB process/Job caps; full uses 3/4 GiB. Each child
is bounded to 300 seconds. Parent attestation is create-once outside the child's
writable output and recorder directories. Physical identity rereads bracket
proof admission and detect late drift or same-byte replacement.

A preacceptance failure records one linked engineering failure and never
launches a retry. If a parent attestation, engineering intent or engineering
success exists, any subsequent exception raises `RecoveryRequired` without a
competing failure. An interrupted writer that created a file is quarantined
conservatively. `recover_engineering_case` is explicit and requires independent
request and attestation file digests; it only replays an existing canonical
engineering intent, is idempotent, and never launches work or creates a missing
intent. A durable attestation without an intent remains quarantined.

The prepared tests use real recorder writes and locks in owned temporary
fixtures. Source capture is replaced only in those unit fixtures; backend,
native verification and numerical qualifications are fabricated. The native
file anchor is redirected to the same temporary fixture. These tests do not
execute a model, child, study asset, selector, original-case attempt or measured
cell. Passing them qualifies engineering orchestration boundaries. Full study
worker, numerical source-selector integration and scientific admission remain
false until separately established.
