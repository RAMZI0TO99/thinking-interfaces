# Evaluation recording identity package for checkpoint provenance review

11 October 2026 UTC. The [portable JSON](evaluation_recording_provenance_package_20261011.json)
is prepared locally and unsent:512,992 bytes, SHA-256
`b9ea3dfefed137a2264313bed1b7b3c392a1be799fbd767583500f44024bfc69`. It collects the exact evaluation identifiers and retained
execution hashes needed for a checkpoint-bound actual training-coverage
statement and later reviewed intersection. It contains no raw signal arrays,
labels, checkpoint weights, Windows account names or absolute machine paths.
No third party was contacted or external file published.

| Dataset | Distinct subjects | Raw recordings | Profile A epochs | Project session/run groups |
| --- | ---: | ---: | ---: | ---: |
| BCI IV-2a |9 |18 |5,184 |108 |
| Cho2017 |52 |52 |10,520 |52 |
| MMIDB |109 |327 |4,917 |327 |
| Total |170 |397 |20,621 |487 |

The package includes170 Profile A and52 Cho60 Profile B cache identities,
222 artifacts in total. The Profile B subjects are already counted in the170;
the second representation adds zero independent research cases. Every subject
links to its raw filenames/hashes and session/run groups. Trial ranges encode
the exact original indices with explicit inclusive start/exclusive stop/step;
root reconstructed every range and compared it with the original inventory,
so this is a lossless compact representation rather than an epoch-count-only
summary. Cho60 manifests retain their separate hashes and0.1mV scaling.

Preparation compares all397 raw hashes/sizes and222 cache hashes/sizes with
the already executed reconstruction plans and source inventories. It freshly
checks sizes, mtimes, resolved paths and single-link identities for671 local
raw/cache/manifest files. Hashes are reused from the completed numerical
receipts: raw/cache payloads were not opened or rehashed and numerical
reconstruction was not replayed in this metadata phase. The older Cho raw
mapping has no timestamp field; its hashes/sizes remain pinned, while mandatory
current timestamps come from executed reconstruction plans. The first
preparation failed on that missing field before output creation; its source
remains unchanged and the corrected preparation uses a fresh version/directory.

Root's metadata self-review passed3,697 checks: all397 recording identities,
all170 unique subjects,487 group links,20,621 exact trial indices,222 cache
profiles, all source metadata pins and the unknown/scientific boundaries.
All37 previously created owned Jobs were freshly absent. No new Job, model,
training, scientific library import, checkpoint open, recorder action or
original case operation occurred. The known current processing results remain
exact in their separate [Profile A](cho_all52_cache_reconstruction_20261011.md)
and [Cho60](cho60_all52_cache_reconstruction_20261011.md) scopes.

Metadata preparation Git`b6e5336402540a8042b2f742afc226d548dc9dcf` and canonical
Source`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`/432 files remain settled. The
quality pointer4eb4d556 is retained; no full-suite or numerical replay was
performed. This package cannot authenticate historical cache generation,
pretraining membership, author identity, target independence or eligibility.
MMIDB's327 hashes retain their published PhysioNet/installed MNE match from the
mapping receipt; BCI/Cho publisher checksum identity is not independently
certified. Cho class-block order does not prove acquisition chronology.

The original checkpoint SHA-256 is fixed in the package, while all actual
pretraining-inclusion values, training coverage and target overlap remain
null/unknown. Unknown inclusion is not exclusion. Gate A/seven owner decisions/
freeze remain unsigned; both original case attempts remain spent/zero. The
81 current original controls and450 dated historical reference fits retain
their existing scopes. There is no new30-hour window or future host-quiet/
compute/science grant.

The [updated request wrapper](checkpoint_provenance_request_draft_20261011_package.md)
names the exact optional metadata attachment and hash; it is prepared and
unsent with no recipient/channel selected. Its preceding Cho60 draft remains
byte-exact. A received checkpoint-bound response must follow the
[cohort intake/review contract](checkpoint_cohort_review_contract_20261010.md).
An authenticated actual training manifest and reviewed mapping would support
an explicit recording/subject intersection; local hashes alone cannot supply
it. The [owner engineering addendum](cho_owner_decision_engineering_addendum_20261011.md)
still maps the seven undecided responses. No scientific/model operation is
admitted by creating this package.
