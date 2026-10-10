# MMIDB subject 001: executed raw-to-cache reconstruction

10 October 2026 UTC. The fresh guarded reconstruction of **subject 001**
reproduced all **45 existing Profile A epochs exactly**: signal values,
labels, session/run/trial identities, channel order, shapes and dtypes agree.
Maximum absolute and RMS signal errors are both **0 V**. All four input files
retain their original hashes, sizes and modification times; the cache was
not rewritten. This is current processing reproducibility for one subject,
not authenticated historical cache-generation provenance or scientific
cohort eligibility. The other 108 MMIDB subjects were not reconstructed.

The [complete executed result](../../runs/coordination/mmidb_cache_lineage_20261010_v1/candidate_009/reconstruct_attempt_002/result.json)
has SHA-256 `57c1d6f86fb062983371ae0df5c1d8cfd6ae665ca01dcab7239b4d2cb80ff609`. The [compact summary](mmidb_cache_reconstruction_summary_20261010.json)
retains all seven actual observations, including failures. Root's
[execution self-review](../../runs/coordination/mmidb_cache_lineage_20261010_v1/reconstruction_execution_root_review_010.json)
passed 3,323 checks, primarily receipt/runtime/input pins.
This is local execution and root self-review, not independent acceptance.

## Method and fixed inputs

The job read the already downloaded `S001R04`, `S001R08` and `S001R12` EDFs,
whose hashes remain equal to the earlier publisher/MNE checksum map. Each
run supplied 15 complete motor cues, with no incomplete cue dropped. The
result is 45 x 64 x 512 float32 samples, with 23 left-fist and 22 right-fist
epochs. The cached artifact is `data/processed/mmidb/profile_a/subject_001.npz`,
SHA-256 `ed85f7e922baf2b6e99552622cf9285324517052280f288859fa604d52038ec9`.

The worker directly reads the pinned local EDFs and calls the frozen
`drop_incomplete_motor_annotations` and `preprocess_raw_runs_profile_a`
functions with the existing `configs/base.toml` Profile A: 8-30 Hz FIR,
average reference, 128 Hz, one-second pre-cue mean subtraction and four-second
post-cue epochs. It bypasses the downloading and saving entry points. The
declared comparison remains absolute 1e-12 V plus relative 1e-6, alongside
exact equality reporting; no tolerance or preprocessing change was needed.

## Measured runtime and admission

The actual scientific probe passed twelve processing/comparison/hash
boundaries before a separate real-data admission. It measured and pinned
3,194 imported files; admission also pins the five reported native threadpool
DLLs, venv/base runtime and six installed distribution metadata/RECORD pairs.
The observed versions are NumPy2.5.2, SciPy1.18.1, MNE1.12.1, MOABB1.6.1,
scikit-learn1.9.0 and threadpoolctl3.6.0, Python3.12.14.
Dataset dependencies import Torch; its CPU thread count and all five reported
native threadpools were one, with no CUDA context. No checkpoint or model was
opened/constructed, and no fitting, inference, recorder or original case ran.

The worker's Python audit hook denies network, subprocess and writes outside
its fresh attempt. Two exact shared-directory creation requests from the
data-package import were denied and recorded as expected: those directories
already exist and pathlib's `exist_ok=True` suppresses the denied requests.
No directory creation permission was added. Network/subprocess attempts and
all other outside-write attempts were zero. This hook is not an OS sandbox
for hostile native libraries. Private caches and logs stay in the attempt.

Execution Git `7777d6ce438fa83b6b9904942dc4ceaefa912b59`; probe Git
`a8c3bd86708848881b184e83b5cc37bee37ff8ab`. Canonical Source
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529` /432 files and accepted quality pointer
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`
are unchanged. No full-quality replay occurred. The separately owned
[candidate](mmidb_cache_lineage_candidate/README_005.md) has exact-byte
probe/revision receipts; the older full-suite result does not certify it.

Each scope retained startup10/active4 GiB RAM and disk20 GiB floors,
one CPU/Job, process4/aggregate5 GiB caps and inner120/native150-second bounds.
Original model-case process6/Job7.5 GiB limits remain unchanged. The accepted
reconstruction took 17.8833662s native,
15.4975637s guard, peak aggregate
1,207,357,440 bytes. Atomic assignment, membership,
queried limits, empty/closed Job, physical parent exit, disposed handles and
awake reset were verified. All 25 cumulative owned Job names are freshly
absent. Pro2 reported no conflicting runtime or pause; that is scheduling
disclosure, not a case/host-quiet/scientific grant.

## Preserved failures

| Scope | Actual outcome | Native seconds | Peak Job bytes |
| --- | --- | ---: | ---: |
| Initial synthetic probe | Failed, retained | 9.0951355 | 1,116,004,352 |
| Logged diagnostic revision | Failed, retained | 6.2117852 | 1,115,369,472 |
| Empty-runtime-file correction | Failed, retained | 9.2243987 | 1,116,360,704 |
| Denied-call stack diagnostic | Failed, retained | 8.7945907 | 1,115,983,872 |
| Qualified synthetic probe | Passed | 10.3525774 | 1,115,693,056 |
| First reconstruction / JSON failure | Failed, retained | 17.8321832 | 1,208,258,560 |
| Scalar-corrected reconstruction | Passed | 17.8833662 | 1,207,357,440 |

The first probe lacked worker error logging. Fresh diagnostics identified
legitimate empty runtime modules, then the two denied existing-directory
probes. New revisions corrected fingerprint/accounting without enabling
the denied operations. The first reconstruction's partial comparison
reported equality but JSON writing failed on NumPy `raw.n_times`; that
failed run is not accepted. A fresh worker converts only that receipt field
to Python `int` and produced the complete passing result. Executed files,
partial outputs and spent per-revision admissions remain untouched; no
original LaBraM attempt was reset or retried.

## Next boundary

The engineering expansion to the remaining 108 subjects requires a defined
finite protocol, current input/runtime pins, measured admission and fresh
coordination. No broader operation is admitted by this report. Checkpoint
cohort/recording overlap remains unknown; the provenance request is unsent.
Gate A and all seven scientific owner decisions/freeze remain unsigned,
and both original LaBraM attempts remain spent, zero remaining. Current
reconstruction does not authenticate the older cache writer or establish
checkpoint training coverage, exclusions, scientific eligibility or accuracy.
