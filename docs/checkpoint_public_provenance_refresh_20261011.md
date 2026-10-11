# Checkpoint provenance: public-source refresh, 11 October 2026

Fresh public API reads returned the same official repository head, complete
tree and comments from issues 35 and 60 as the retained 10 October audit.
These four records add no new checkpoint-bound training-cohort evidence.
The actual recording/subject coverage and evaluation overlap remain unknown.
This is a bounded read-only finding, not proof that no other records exist.

| Refreshed source | Executed finding |
| --- | --- |
| [Official repository head](https://api.github.com/repos/935963004/LaBraM/commits/main) | Still `c431221e6cfd23dbfa9950e0180682fb322b0548`; commit date 29 September 2025. Exact response bytes match the retained audit. |
| [Complete tree at that commit](https://api.github.com/repos/935963004/LaBraM/git/trees/c431221e6cfd23dbfa9950e0180682fb322b0548?recursive=1) | 28 blobs, no truncation; identical response bytes and no new tracked file. The tree response is metadata; weights and source code were not downloaded through it. |
| [Issue 35 comments](https://api.github.com/repos/935963004/LaBraM/issues/35/comments?per_page=100) | All four comments are unchanged; no pagination continuation. Latest comment/update: 12 July 2025. |
| [Issue 60 comments](https://api.github.com/repos/935963004/LaBraM/issues/60/comments?per_page=100) | All seven comments are unchanged; no pagination continuation. Latest comment/update: 17 December 2025. |

The web lookup also showed that the [official pretraining entry point](https://github.com/935963004/LaBraM/blob/c431221e6cfd23dbfa9950e0180682fb322b0548/run_labram_pretraining.py)
still has four placeholder dataset paths. The [converted model card](https://huggingface.co/braindecode/labram-pretrained/blob/main/README.md)
does not supply a training inventory and retains an incomplete paper field.
These observations do not identify the released original checkpoint's run.
BrowserOS Neo tools were unavailable in this session. The web rendering
omitted issue comments and could not open the API endpoints; the separate
bounded public GETs above supplied the actual comment and tree bytes.

The [owner's issue 35 explanation](https://github.com/935963004/LaBraM/issues/35#issuecomment-2285361279)
directs users to dataset publishers rather than redistributing their data.
The [issue 60 reply](https://github.com/935963004/LaBraM/issues/60#issuecomment-2870835041)
discusses model availability, preprocessing and downstream checkpoint selection.
Neither supplies the recording-level mapping needed here. This refresh did
not search every issue, all external locations or private training logs.

## Executed scope and remaining input

All four HTTPS GETs completed with HTTP 200 on 11 October 2026, about
03:16:17-03:16:19 UTC. Each response was limited to 1 MiB, with an eight-second
socket timeout and a 45-second monotonic collection deadline. That deadline
was checked in code; it was not an OS Job deadline. No token, authenticated
account access, weight read/download, remote code execution, scientific import,
model, fitting or recorder operation occurred. No new named Job was created.
The startup 10 GiB RAM, active 4 GiB RAM and 20 GiB disk floors were met;
available RAM after collection was about 14.29 GiB. Genuine peer pause checks
remained active. No host-wide quiet or future compute grant follows.

The [97-check root metadata review](../runs/coordination/checkpoint_public_refresh_20261011_v1/public_metadata_root_review_002.json)
passed, including exact current and historical response hashes, source/index
identity and fresh absence of all 38 created owned Jobs. It is a self-review,
not independent scientific acceptance. The [collection receipt](../runs/coordination/checkpoint_public_refresh_20261011_v1/public_metadata_receipt_001.json)
preserves all request URLs, HTTP/server dates, sizes and SHA-256 values.

Collection Git was `4d8888afb9ce90fec100964d45a346beb4597761`. Canonical
source remains `3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`
over 432 files, with quality pointer `4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`.
No suite or numerical reconstruction was replayed. All 170 Profile A subjects
and all 52 Cho60 caches retain their earlier exact reconstruction receipts.

The [provenance request](phase2/checkpoint_provenance_request_draft_20261011_package.md)
and its [397-recording/170-subject package](phase2/evaluation_recording_provenance_package_20261011.md)
are ready locally and remain unsent. The next input is an authenticated
manifest, execution record or precise attestation linking the original
checkpoint SHA-256 to actual dataset versions, subjects, recordings, coverage
and exclusions. Explicit mappings can then use the [qualified declared-overlap checker](phase2/cohort_declared_overlap_qualification_20261011.md)
as a review aid; its calculated declarations do not authenticate that input.
Publishing or sending the request requires an explicit instruction selecting
that action and its recipient/channel. No outside party was contacted.

MMIDB's paper-level inclusion remains context; actual recording overlap is
unknown. Cho2017 and IV-2a absence from the paper does not establish exclusion.
Scientific Gate A, all seven owner responses and the experiment freeze remain
unsigned. Both original LaBraM attempts remain spent, zero remaining; the
81 current controls and 450 dated reference fits retain their scopes.
This step admits no model case, attempt reset or new 30-hour session.
