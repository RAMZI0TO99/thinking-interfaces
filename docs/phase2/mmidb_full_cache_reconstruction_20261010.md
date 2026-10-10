# All MMIDB caches reproduce exactly from pinned raw recordings

10 October 2026 UTC. The existing Profile A arrays for **all 109 MMIDB
subjects and 4,917 epochs** reproduce exactly from the pinned local EDF
recordings under the current frozen preprocessing code and configuration.
Signals, labels, session/run/trial identities, channel order, shapes and
dtypes agree. Maximum absolute and RMS signal errors are both **0 V**.
The aggregate label counts are **2,479 left-fist / 2,438 right-fist**.

This establishes current processing reproducibility of the pinned caches.
It does not authenticate who generated the historical artifacts, establish
checkpoint pretraining coverage or decide scientific eligibility. All IDs,
including079/100 and the documented anomaly subjects, were retained without
an exclusion decision. BCI/Cho processing lineage and scientific approvals
retain their separate evidence scopes.

## Executed coverage

| Scope | Subjects | Epochs | Raw recordings | Result |
| --- | ---: | ---: | ---: | --- |
| [Earlier qualified subject001](mmidb_cache_reconstruction_20261010.md) | 1 | 45 | 3 | Complete passing receipt reused; no numerical replay |
| Fresh bounded batch002..109 | 108 | 4,872 | 324 | All exact matches |
| Combined current processing evidence | 109 | 4,917 | 327 | 161,120,256 signal values agree exactly |

The [complete batch result](../../runs/coordination/mmidb_full_cache_reconstruction_20261010_v1/candidate/attempt_001/result.json) has
SHA-256 `888b0d1de74ae24eef3c987a0a8d8372e553eccde16385d816527da414afc67b` and pins each of the108 subject metadata
receipts. The [compact summary](mmidb_full_cache_reconstruction_summary_20261010.json)
records scope, runtime, aggregate counts and remaining boundaries. The
[root execution self-review](../../runs/coordination/mmidb_full_cache_reconstruction_20261010_v1/execution_root_review_002.json)
passed 4,305 checks, primarily exact receipt/runtime/input
pins and per-subject outcomes. This is root self-review, not independent
scientific acceptance. Earlier failed probes/serializer output remain
unaltered in the preceding single-subject report.

The worker reads local runs04/08/12, calls the unchanged frozen sanitization
and Profile A functions, and compares in memory with each existing cache.
No downloading or saving entry point is called. Settings remain8-30Hz FIR,
average reference,128Hz, one-second pre-cue baseline and four-second epochs.
Absolute1e-12V/relative1e-6 tolerances are unchanged; all matches were exact.
The existing incomplete-cue policy dropped 1 cue:
subject104, S104R08.edf: 1 incomplete cue. The stored epoch count and identity arrays still match exactly.
No anomaly rule or scientific cohort policy was changed.

Per-subject hashing checked raw/cache bytes before use and after processing;
sizes and modification times also remain. Root subsequently checked all
324 raw/108 cache size/mtime/link-count records without decoding signals.
The three subject001 raw inputs and cache were freshly rehashed when its
passing receipt was reused. The earlier publisher/MNE checksum map binds
all327 raw recordings; this batch performed no network access.

## Fresh finite runtime admission

Execution Git `8e9de5c3ff514ac2afffe0e15a90f642c94e2408`, canonical Source
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529` /432 files and accepted quality pointer
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`
remain unchanged. No full-suite replay occurred; the separate
[candidate scope](mmidb_cache_lineage_candidate/README_remaining.md) has its
own exact-byte and executed receipts. The earlier measured twelve-boundary
probe was freshly checked against the same canonical source and3,216 runtime
file pins, including the imported modules and reported threadpool DLLs.

The single sequential Job had inner300/native330-second deadlines, startup10/
active4 RAM/disk20GiB floors, process4/aggregate5GiB caps, CPU/Torch/native1,
and one concurrent owned Job. No new30-hour window or original-case reset
was inferred. Native execution took **65.6960171s**,
guard **63.4116962s**; peak aggregate commit was
**1,213,194,240 bytes**, approximately
1.13GiB. Memory does not accumulate
all subjects: one subject is processed, compared, recorded and released
before the next.

Atomic Job assignment, membership, queried limits, empty/closed Job, physical
parent exit, disposed handles and awake reset passed. All **26** cumulative
owned Job names are freshly absent. The audit hook still denied exactly two
known existing-directory creation requests from the data-package import;
network/subprocess/other outside-write attempts were zero. Dataset
dependencies imported Torch with one CPU thread and no CUDA context, but
no checkpoint, model, fitting/inference, recorder or original case ran.
Pro2 reported no conflict/pause; its Source scheduling is peer disclosure,
not physical host release, case admission or scientific acceptance.

## Next boundary

The original two LaBraM attempts remain spent, zero remaining. Gate A and
all seven owner decisions/experiment freeze remain unsigned. Actual
checkpoint-bound subject/recording cohort evidence and overlap assessment
are still missing, and the provenance request remains unsent. Exact cache
reproduction does not establish exclusion from pretraining, held-out status,
accuracy, query eligibility or permission for a new model case.
Any further BCI/Cho engineering expansion needs its own finite protocol,
fresh measured input/runtime admission and current resource coordination.
