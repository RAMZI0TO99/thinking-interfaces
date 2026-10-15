# Linear staged engineering recorder, version 1

This separately versioned transaction connects the accepted linear source and
staged detached restoration to the real `CaseRecorder`. It consumes recorded
proofs and performs no new fitting, restoration, tensor loading or inference.
The only admitted plan is `cho2017`, subject 02, `labram_linear`, five shots,
seed 11, repetition 1. The terminal is one engineering success and zero measured
cells. Original scientific case attempts remain zero.

`run_staged_case` retains the real case identity lock while claiming once,
calling the metadata backend once and independently verifying its result twice.
It rechecks current execution pins, the claim, the durable request and every
origin file by physical identity and digest before publishing an fsynced parent
attestation and engineering terminal. A same-byte file replacement changes its
identity and is refused. The claim uses the distinct worker
`cho51_linear_staged_source_restore_engineering`; request, origin contract and
attestation schemas all use the `cho51_linear_recorder_*_v1` prefix.

Historical source provenance remains exactly commit
`4491e2a68126d6b7293261f4954b88c11c29049d`, dirty `true`, fingerprint
`9c2e6ad444c44309f9d4becda2909fba0d2fe315f047560f9adbce56397c9299`.
The fresh control fixture has independently captured current Git provenance,
bound in the request and claim through `fixture_git_commit`, `fixture_git_dirty`
and `fixture_source_sha256`. Historical fields have separate names and cannot
be rewritten by a current capture. The unchanged `CasePlan.case_id` is a digest
of the plan alone: this plan retains
`9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141`
even when current Git provenance changes. The existing lifecycle context check
continues to capture and verify the fresh fixture normally.

The pinned canonical origin contract contains exactly `schema`, `files`, `roles`
and `summary`. Every absolute file path has both a SHA-256 pin and a role:

| Role | Admission | Handling |
| --- | --- | --- |
| `metadata` | Recognized metadata names/extensions; at most 8 MiB | Streamed hashing; small control files use unchanged lifecycle reader |
| `complete_evidence` | Exact 23,087,023-byte accepted JSON, SHA `e497186ff0eece324830731f8cada32ff5698fc8c25e143f0f8f1519061a12c3`; 32 MiB cap | Streamed hashing in transaction; independent verifier may parse metadata |
| `selected_weights` | Exact 23,294,624-byte accepted checkpoint, SHA `3033608533114fc1d484aa37b2c8ccf492ada90b28bef9e0ef617aa467ec8048`; 64 MiB cap | Streamed hashing only |
| `baseline_weights` | Exact 23,299,672-byte baseline, SHA `53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`; 64 MiB cap | Streamed hashing only |

These exceptions require their exact role, suffix, size and digest. They do not
raise the ordinary reader's limit. Direct paths, single links, opened-handle
identity and after-read identity checks apply to every role. Arrays cannot use
the metadata role. Neither checkpoint headers nor tensors are parsed here.

`VerifiedStagedProof` binds the current request, current source, claim, owner,
environment, execution pins and origin contract, plus selected state, physical
weights, manifest, complete-evidence and recipe digests. Its fixed scope records
5,253 historical updates (5,151 source and 102 support), 102 folds, 51 final source
subjects, 223 restored tensors, 5,818,138 elements, 402 head parameters and two
historical restores with explicit 64 MiB limits. Current restores, updates,
target inference and measured cells are all zero. The historical publication
and detached restoration are qualified. The original scientific case remains
unqualified. The staged two-root provenance flag stays true and unchanged
single-root factory qualification stays false.

The production backend and verifier must independently authenticate the accepted
publication final review, frozen source inventories, both native/stage receipts,
tensor and adapter witnesses, archive pairs and physical origin bytes. The
transaction's callback seam by itself does not qualify historical results.
It must not replay the frozen publication bridge, recapture historical Git as
current authority or rewrite accepted evidence to fit a new commit.

Before durable acceptance, a backend/verifier error records one linked failure.
Once an attestation, engineering intent or success exists, errors raise
`RecoveryRequired` and leave the durable bytes for explicit examination.
`recover_staged_case` requires external request and attestation digests, rechecks
the same physical origin and current context under the real lock, and replays
only an existing engineering intent. It is idempotent, never calls the backend
and never creates a missing intent.

The source includes 29 test functions with 73 parameterized cases. They use the
real recorder and locks, explicitly fabricated metadata callbacks, tiny
role-pinned artifacts and mocked fresh source capture. They test lock coverage,
call counts, tampering, durable interruptions, recovery, provenance separation
and role-bound readers. They do not establish actual source/restoration proof.
The recorder imports its pinned numerical dependencies; qualification must
separately demonstrate zero model construction, decoding, restoration, fitting,
inference and numerical tensor operations under a fresh native guard. Source
review and Python AST parsing are preparation only; execution needs its own
fresh guarded receipt and independent closeout.

Canonical sources, historical receipts, checkpoint bytes and scientific gates
remain unchanged. The full 1,020-cell worker, cohort/prior-training lineage,
unchanged single-root factory compatibility and owner final scientific freeze
remain pending.
