# Executed evaluation identity inventory

10 October 2026 UTC. A read-only metadata scope inventoried the fixed Profile A
catalogs: **170 subjects, 20,621 stored epoch identities and 487 session/run
groups**. All 24 independent synthetic binary-reader cases passed before the
actual inventory. The full [inventory](../../runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/inventory.json)
is pinned by SHA-256 `b046ea009cc5cca252ff0d5379b61ab003963e97726a2626dc537f73f3b5e875`. A compact
[evidence summary](evaluation_identity_summary_20261010.json) records counts,
project namespaces and the evidence limits for the future cohort comparison.

| Dataset | Subjects | Stored epochs | Session/run groups | Raw-file evidence |
| --- | ---: | ---: | ---: | --- |
| BCI IV 2a | 9 | 5,184 | 108 | Two sidecar-declared raw paths per subject; no fresh raw-file verification |
| Cho2017 | 52 | 10,520 | 52 | One sidecar path/hash per subject agrees with the earlier verified raw audit |
| MMIDB | 109 | 4,917 | 327 | Inspected Profile B sidecars contain no raw-file mapping |

## What was read

The separately owned [standard-library candidate](evaluation_identity_candidate/README.md)
streamed SHA-256 over 2,098,009,722 compressed-container bytes and decoded only
`sessions.npy`, `runs.npy` and `trial_indices.npy`. Signal, label and channel
members were not opened. No NumPy, model, unpickling or raw EEG-file read occurred.
The bounded reader follows a small subset of the
[official NPY format](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html).
Its regression fixtures cover endian/version differences, object or structured
dtypes, executable header expressions, bounds, malformed payloads, duplicate
members and epoch identities, and workspace escapes. Deliberately invalid
unused signal/label fixtures demonstrate that those members are not decoded.

BCI source declarations came from Profile A manifests; Cho declarations came
from `profile_b_60hz_v1`; MMIDB metadata came from `profile_b` sidecars. Sidecar
subject numbers agree with the fixed artifact basenames. Cho hashes match the
[previously executed raw audit](../../runs/coordination/source_prerequisites_20261010_v1/raw_environment_002/raw52/receipt.json).
That comparison reuses historical raw-hash evidence; this scope did not rehash
raw EEG files. A sidecar from a different profile is a source declaration, not
a new demonstration of cross-profile signal alignment or processing lineage.

The identifiers are project artifact/session/run/trial values. A session/run
group is not asserted to be a publisher recording. Raw paths are not mapped
to individual stored groups. Publisher namespaces, actual pretraining inclusion,
label exposure and checkpoint overlap remain unknown. All 109 MMIDB artifacts
are included for inventory; no eligibility decision for subjects 079/100 or
scientific query freeze was made. No participant contact or external message
was sent. The provenance request remains drafted and unsent.

## Actual execution and custody

Execution Git: `5590735d1b4811c21932f14c514542042df016b5`. Canonical Source remained
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529` /432 files. The existing quality pointer
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`
verified without a full-suite replay. The candidate is outside that canonical
fingerprint and has its own exact-byte execution evidence.

The fresh `pro3_evaluation_identity_inventory_attempt_001` Job retained
startup 10/active 4 GiB RAM and disk 20 GiB floors, with separate process
2.25/Job 2.5 GiB caps and inner 120/native 150-second limits. Native execution
took 2.8787148 seconds; the guard took 2.7318319
seconds. Peak aggregate Job commit was 29,626,368 bytes.
Atomic assignment, queried caps and membership were verified; the Job emptied
and closed, the parent exited, handles were disposed and the awake scope reset.
All 15 current owned Job names were freshly absent.

Root's 1,927-check execution self-review passed. It checks receipts, output
consistency, unique identities, sidecar/hash declarations and post-run file
size/mtime. It does not independently rebuild container hashes or constitute
independent scientific review.

- [24-test output](../../runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/tests.json)
- [Actual inventory summary](../../runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/inventory_summary.json)
- [Guard receipt](../../runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/guard.json)
- [Native physical exit](../../runs/coordination/evaluation_identity_inventory_20261010_v1/candidate/attempt_001/native_exit.json)
- [Execution self-review](../../runs/coordination/evaluation_identity_inventory_20261010_v1/execution_root_review_004.json)

## Next evidence

This inventory supplies the local comparison side for an actual checkpoint-bound
cohort response. The [intake contract](checkpoint_cohort_review_contract_20261010.md)
still requires authenticated claimant evidence, a complete training-run to
checkpoint mapping and compatible subject/recording identifiers. The
[declaration checker](cohort_intake_completeness_20261010.md) cannot authenticate
that evidence or decide overlap. No actual cohort response is present.

The [seven owner decisions](cho_owner_decision_packet_20261010.md), Scientific
Gate A and experiment freeze remain unsigned. The 81 original controls and 450
historical reference records keep their existing evidence scopes. Both original
LaBraM attempts stay spent, zero remain; this phase performed no recorder or
model work and supplies no third attempt or renamed equivalent case. Pro2
requested no pause; its own Source scheduling grants no scientific acceptance
or numerical/native Parser/fixture/Job admission here.
