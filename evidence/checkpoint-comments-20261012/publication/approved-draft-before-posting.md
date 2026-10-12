# Proposed public checkpoint-provenance request

Prepared and **unsent**, 11 October 2026. Proposed channel: a new issue in
[935963004/LaBraM](https://github.com/935963004/LaBraM/issues/new).
Recipient: the repository maintainer. Posting account is not yet confirmed.
Attachments: **none**. The local evaluation inventory will not be uploaded by
this action. The exact proposed title and body follow.

Title: Recording-level pretraining provenance for the released LaBraM base checkpoint

---

Hello, and thank you for making LaBraM available.

We are preparing a subject-level motor-imagery evaluation and would like to
describe pretraining exposure accurately for the released base checkpoint:

- File: `checkpoints/labram-base.pth`, 96,612,769 bytes.
- Official commit: `c431221e6cfd23dbfa9950e0180682fb322b0548`.
- SHA-256: `7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`.
- Git blob: `221148b5af403e9178629bb61e94b2e7d89ef172`.

Could you provide a manifest, execution-record reference or provenance
statement linked to these exact checkpoint bytes, identifying the datasets,
versions, subjects and recordings actually used for pretraining?

Our planned evaluation catalogs are:

1. **MMIDB 1.0.0:** S001-S109, runs 04, 08 and 12. Which of these subjects,
   runs or splits were included, and were any evaluation recordings excluded?
2. **BCI Competition IV-2a:** A01T/A01E through A09T/A09E. Were any of these
   subjects or recordings included? We understand that the paper's named
   BCI Competition IV-1 dataset is distinct from IV-2a.
3. **Cho2017:** s01.mat through s52.mat. Were any of these subjects or
   recordings included, and which versions or exclusions apply?

We understand that MMIDB is named in the paper. We are asking about the actual
released checkpoint's recording/subject coverage, rather than assuming that
the paper's dataset list or source placeholder paths determine its cohort.
Please also distinguish unlabeled EEG exposure from any use of task labels.

Public identifiers or reproducible pseudonymous mappings would be sufficient;
we are not requesting raw-data redistribution. We have prepared a local
metadata-only catalog of 170 evaluation subjects and 397 recording filenames
and hashes, which we can provide separately if useful. No recording arrays,
labels or weights are attached to this request.

Please identify the statement's source/date, how its training run is linked
to this checkpoint, and whether the supplied coverage is complete. If the
mapping is unavailable, an explicit statement of that limitation would also
help us constrain our evaluation claims.

Thank you.

---

## Local review notes, not part of the proposed public body

Four bounded, unauthenticated public API searches covered `pretrain`,
`training data`, `manifest` and the exact original checkpoint SHA-256 in this
repository's indexed issue titles/bodies. All four completed with HTTP 200,
without incomplete-result or pagination flags. They returned 11 distinct
candidate issues: 17, 25, 28, 34, 35, 39, 51, 56, 63, 64 and 65. Their bodies
cover preprocessing, architecture and training problems; none supplies the
requested checkpoint-bound manifest or a matching SHA-specific request.
The searches exclude comments and are not an exhaustive provenance search.
Previously reviewed author comments in issues 35 and 60 remain context.

The [broader request](checkpoint_provenance_request_draft_20261011_package.md),
[evaluation inventory](evaluation_recording_provenance_package_20261011.md)
and [public-source refresh](../checkpoint_public_provenance_refresh_20261011.md)
remain unchanged. This version chooses a concrete proposed channel and
omits the optional attachment. No public issue or outside message has been
posted. Publication requires an explicit user instruction covering this exact
title, body, repository and no-attachment action; account access must be
confirmed before posting.

No model, weights, fitting, recorder or scientific case ran. Gate A, the
seven owner responses and the experiment freeze remain unsigned. Actual
checkpoint training coverage and evaluation overlap remain unknown; both
original case attempts remain spent, zero remaining.
