# Synthetic case transaction and engineering result channel

24 September 2026. `evaluation/phase2_case_transaction.py` provides a legacy
file probe and a framed engineering path. The latter is connected to a
synthetic `CaseRecorder` attempt through `evaluation/phase2_case_engineering.py`.
Neither path executes Cho selection, fits a model, or publishes a scientific
evaluation cell.

The caller creates a durable `DeadlineLease`, pins one small synthetic source
file, and publishes a canonical contract. Its returned SHA-256 digest must be
held outside the mutable transaction directory. The contract binds a case ID,
unique attempt ID, expected integer challenge value, source digest and
deadline-file digest. The parent publishes a unique, write-once start record
before launch. Any existing start or proposal prevents another launch for that
attempt; a crash leaves the attempt for review rather than automatic replay.

In the legacy file probe, the parent calls `run_supervised` for one child,
sampling disk and RAM on the
transaction output volume even when the child working directory is elsewhere.
The default child writes only a canonical result proposal. The parent accepts
it only after the Windows Job Object is empty, the root child exited zero,
the supervisor returned `normal`, the contract and start still verify, the
proposal exactly matches the contract, the source and deadline bytes still
match their pins, both deadlines remain live, and a final resource sample
meets the existing 20 GiB disk and 4 GiB RAM floors. It then publishes a
write-once parent attestation. Its `proposal_validated_utc` records the
pre-publication validation time. The deadline bounds supervised child work
and that validation; it does not prove the final filesystem write or fsync
finished before the deadline. Historical verification requires both the
external contract digest and an external attestation digest; neither a
self-hashed proposal nor an unpinned attestation is trusted on its own.

All records are byte-capped canonical JSON with exact field sets, path
containment checks and no-clobber publication. Record reads compare file
identity and size before, during and after reading. The start record blocks
two cooperating parents from launching the same attempt concurrently. An
abnormal child exit, deadline stop, low resource sample, changed source,
modified proposal, or changed deadline leaves no new attestation.

The proposal is a deterministic synthetic integer echo. In the legacy file
probe, a different process with access to the same output directory can
write the exact proposal while the supervised child merely exits. This path
does not prove child authorship or causal computation.

The engineering path uses `run_supervised_with_frame` and an inherited pipe
writer whitelisted for its suspended Windows child. The child sends one
bounded canonical proposal frame; the parent waits for normal whole-Job
completion, then publishes those bytes with a fresh no-clobber operation.
The `synthetic_case_attestation_channel_v1` record pins the frame SHA-256.
An exact shared-file proposal with no frame fails. The parent holds
`CaseRecorder.case_session` through the child lifetime, binds the case and
worker bytes to an external digest, and writes engineering intent/success
records apart from scientific cells. Recovery requires the caller-held
contract, binding and attestation digests.

This remains a synthetic process rehearsal. It is not proof of EEG
predictions, fixed support/query membership, model state, metrics or
scientific selection. A Cho caller still needs the public complete-selection
verifier, the unchanged 256-step refusal until a ratified workload exists,
GPU admission/cooling, an immutable episode, and real metric validation.
It also inherits the supervisor's documented parent-crash window before Job
Object assignment and its lack of an independent watchdog for a blocked
sensor/API call. Filesystem path checks and stat comparisons do not establish
security against a hostile actor racing reparse-point changes between calls.

The combined framed-supervisor, transaction, engineering-recorder and recorder
suite passed 73 tests and 26 subtests on this Windows host; one linked-source
test was skipped because this account lacks symlink creation privilege. Ruff
and strict mypy also passed. The tests cover normal and malformed frames,
unrelated handle exclusion, grandchild containment, shared-file forgery,
binding rewrites, receipt recovery and the legacy file-boundary cases.
