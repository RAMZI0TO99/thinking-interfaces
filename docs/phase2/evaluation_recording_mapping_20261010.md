# Executed raw-recording mapping and checksum audit

10 October 2026 UTC. All **327 selected MMIDB EDF files** matched both the
[PhysioNet version 1.0.0 SHA-256 list](https://physionet.org/files/eegmmidb/1.0.0/SHA256SUMS.txt)
and the independently pinned installed MNE registry. The scope also freshly
hashed 18 local BCI IV 2a MAT files. The 52 Cho raw hashes retain their earlier
verified audit scope. No EEG signal, annotation or MAT contents were decoded.

The [full map](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/recording_map.json) has SHA-256
`241606bdd6db4e6356cd5e5013c79b82d0537421397874af532096269831e69d`. The [compact evidence summary](evaluation_recording_mapping_summary_20261010.json)
records the two checksum sources and the distinction between loader filename
relations and cached signal-processing lineage. The [preceding inventory](evaluation_identity_inventory_20261010.md)
and its 24-test qualification remain unchanged.

| Dataset | Subjects | Project groups | Distinct raw files | Identity evidence |
| --- | ---: | ---: | ---: | --- |
| BCI IV 2a | 9 | 108 | 18 | Fresh local SHA-256; pinned loader maps `0train`/`1test` to `AxxT.mat`/`AxxE.mat`; publisher checksums not verified here |
| Cho2017 | 52 | 52 | 52 | Sidecar and historical raw-audit SHA-256; pinned loader uses one `sxx.mat` and group `0`/`0` |
| MMIDB | 109 | 327 | 327 | Fresh local SHA-256 equals PhysioNet and MNE registry for `SxxxR04`, `R08`, `R12` EDF files |

## Exact scope

The read/hash Job covered 345 raw files and 1,613,814,207 raw bytes. A single
fixed HTTPS GET fetched the public checksum metadata: HTTP 200, 259,919 bytes,
SHA-256 `7f5d16957d8ee7bce86cc7ccba0e5994f63f33781607eb3f838392d49311a208`.
Its response and whitelisted HTTP metadata are retained. No raw data were
downloaded and no scientific loader was imported or executed.

The mapper traced the pinned [project preprocessing code](../../scripts/preprocess_public_datasets.py)
and [MMIDB loader](../../data/mmidb.py), plus the installed MNE EEGBCI and MOABB
BNCI/Cho source files listed in the [launch plan](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/launch_plan_001.json).
The actual catalog session/run schema agrees with those rules: MMIDB session
`0` uses the source filename's final two run digits; BCI session labels map to
the loader's T/E files; Cho has one stored session/run group per declared file.
All 487 existing groups and their epoch counts were retained without filtering.

This establishes a reproducible filename relation and, for MMIDB, equality of
the local raw bytes to the publisher's checksums. It does **not** demonstrate
that existing cached Profile A signal arrays were processed from those exact
raw bytes: signal processing was not replayed and historical cache-to-raw
lineage was not authenticated. MMIDB sidecars still lack raw-path declarations;
the new mapping is a separate loader-based supplement. Trial indices are
project indices, not authenticated publisher annotation positions.

The local installed MNE registry SHA-256 is
`16f70225ab684d0095d60c7e6922a6ccbce08cc6d200082b2f43291aa8b97be4`.
Root independently parsed both retained checksum lists and compared all 327
actual worker hashes with them; root did not rehash raw files itself. These
raw-file integrity findings do not establish checkpoint pretraining coverage,
label exposure, held-out exclusions or scientific eligibility. All 109 MMIDB
subjects remain inventoried, including 079/100, without an eligibility decision.

## Actual guarded execution

Execution Git `89d136d6e224efa1baee20209ae3a5aaea8b8938`; canonical Source
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529` /432 files and existing accepted quality
pointer `4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`
remain unchanged. No full-quality replay occurred. The separately owned
[candidate](recording_mapping_candidate/README.md) is outside that fingerprint
and has its own nine-test and exact-byte execution evidence.

The fresh `pro3_evaluation_recording_mapping_attempt_001` Job retained startup
10/active 4 GiB RAM, disk 20 GiB floors, process 2.25/Job 2.5 GiB caps and
inner 120/native 150-second limits. Native execution took 8.0427967s;
guard 7.8901300s; peak aggregate commit 33,820,672 bytes.
Atomic Job assignment, membership and queried caps were verified. The Job
emptied and closed, the parent physically exited, handles were disposed and
the awake scope reset. All 16 current owned Job names were freshly absent.
Root's 1,643-check execution self-review passed; this is local execution and
root self-review, not independent scientific acceptance.

- [Nine executed boundary fixtures](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/tests.json)
- [Actual map summary](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/mapping_summary.json)
- [Publisher response receipt](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/publisher_metadata_receipt.json)
- [Preserved public checksum body](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/publisher_SHA256SUMS.txt)
- [Guard](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/guard.json) and [native exit](../../runs/coordination/evaluation_recording_mapping_20261010_v1/candidate/attempt_001/native_exit.json)
- [Execution root self-review](../../runs/coordination/evaluation_recording_mapping_20261010_v1/execution_root_review_002.json)

## Remaining input

The [unsent provenance request](checkpoint_provenance_request_draft_20261010.md)
now supplies concrete local recording identifiers for comparison. A complete,
authenticated, checkpoint-bound actual pretraining cohort response is still
missing. Publisher raw checksums cannot substitute for that evidence.

The [seven scientific owner decisions](cho_owner_decision_packet_20261010.md),
Gate A and experiment freeze remain unsigned. No model, recorder or original
case operation occurred; both original LaBraM attempts stay spent, zero remain.
The 81 controls and 450 historical reference records retain their evidence
scopes. Pro2 requested no pause; its static Source scheduling is disclosure,
not numerical, native Parser/fixture, scientific or host-quiet acceptance.
