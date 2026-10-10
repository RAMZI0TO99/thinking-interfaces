# Checkpoint public release provenance, 10 October 2026

Both local checkpoint files match their public release records. This resolves
release identity; the reviewed records still do not link the original checkpoint
to a recording-level training cohort. Target overlap remains unresolved.
This is an executed read-only metadata audit and root self-review. Scientific
Gate A and the experiment freeze remain unsigned.

## Exact release identities

| Local file | Size in bytes | SHA-256 | Public identity verified |
| --- | ---: | --- | --- |
| `checkpoints/labram-base.pth` | 96,612,769 | `7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c` | Git blob `221148b5af403e9178629bb61e94b2e7d89ef172` and size at LaBraM commit `c431221e6cfd23dbfa9950e0180682fb322b0548` |
| Local cached `model.safetensors` | 23,299,672 | `53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8` | LFS SHA-256 and size at Braindecode snapshot `0563b6c626e7b40d9a36653b763715db94d945d7` |

Root streamed the local files to compute SHA-256, size and, for the original,
the standard Git blob hash including its header. The original blob and size
match the [official checkpoint entry at the pinned commit](https://api.github.com/repos/935963004/LaBraM/contents/checkpoints/labram-base.pth?ref=c431221e6cfd23dbfa9950e0180682fb322b0548).
The converted file's SHA-256 and size match the
[public snapshot's LFS metadata](https://huggingface.co/api/models/braindecode/labram-pretrained/revision/0563b6c626e7b40d9a36653b763715db94d945d7?blobs=true).
Local file hashes were unchanged before and after collection.

The complete official repository tree was retrieved at that commit: 28 blobs,
without truncation. The four downloaded README/pretraining/utility/dataset-maker
files match the tree's exact blob hashes and sizes. The safe model card and
configuration also match their pinned snapshot's blob identities.

The maintainer's [conversion recipe in Braindecode PR 931](https://github.com/braindecode/braindecode/pull/931#issuecomment-3861882846)
names the official original checkpoint URL, describes parameter mapping and
omitted entries, and uploads the converted model to `braindecode/labram-pretrained`.
That comment was read as text; its code and reported tests were not executed.
The earlier local [tensor correspondence review](checkpoint_correspondence_review.md)
established byte correspondence for 221 retained tensors containing 5,819,936
elements. Neither that historical comparison nor today's release metadata
establishes forward equivalence or training-cohort identity.

## What the reviewed sources say about the cohort

The [pinned official pretraining entry point](https://github.com/935963004/LaBraM/blob/c431221e6cfd23dbfa9950e0180682fb322b0548/run_labram_pretraining.py)
declares four placeholder dataset paths. The pinned utility constructs loaders
from supplied paths, and the generic dataset maker does not enumerate the
released checkpoint's training recordings. These are source templates, not an
executed manifest. The [pinned safe model card](https://huggingface.co/braindecode/labram-pretrained/blob/0563b6c626e7b40d9a36653b763715db94d945d7/README.md)
has an incomplete paper field and no cohort declaration.

In the official repository, the author
[distinguishes downstream TUAB/TUEV preprocessing from pretraining preprocessing](https://github.com/935963004/LaBraM/issues/35#issuecomment-2270321673)
and [explains that users should obtain public datasets from their original publishers](https://github.com/935963004/LaBraM/issues/35#issuecomment-2285361279).
Those comments do not provide a checkpoint-bound recording manifest. A related
author discussion in issue 60 was also reviewed; it supplies preprocessing and
availability context, without that mapping. The request prepared for the owner
therefore asks for identifiers or a hash-bound attestation, with no request to
redistribute raw recordings.

The prior [inert checkpoint and local paper audit](checkpoint_pretraining_provenance_20261010.md)
remains historical evidence. Its stored epoch/training arguments and generic
dataset path do not identify the actual cohort. Appendix D names MMIDB and BCI
Competition IV-1; IV-1 is distinct from IV-2a. Cho2017 and IV-2a are absent from
the named list, which does not establish exclusion from this checkpoint's
training. MMIDB's paper-level inclusion must be disclosed in future evaluation;
the actual recording/subject intersection remains unknown. The printed-hours
sum discrepancy of 3.60 hours remains unresolved.

No recording-level manifest was found in the sources reviewed here. This is a
bounded finding about those sources, not proof that such records do not exist.
An unseen-subject or unseen-recording claim needs an actual overlap assessment;
unlabeled pretraining exposure and supervised label leakage are separate facts.

## Execution and preserved evidence

The two collectors saved 13 successful HTTP 200 metadata responses. Each was
bounded to 1 MiB; the release collector used a 12-second request timeout and
180-second overall deadline. Collection used standard-library HTTPS without
credentials, weight downloads, model imports, unpickling or remote code execution.
The root evidence review passed 680 checks, including exact metadata identities,
the 81 current-source control records and all 450 historical reference records.
Historical reference hash preservation does not recertify its numerical results
against the current source. Root self-review is not independent acceptance.

The execution source was clean Git `c867703e40a61e3b8f9bdb81812649bcc96301cd`,
canonical SHA-256 `3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`
over 432 files. The accepted engineering quality pointer remained
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`;
its existing bundle was verified without replaying numerical validation.

- [Release metadata receipt](../runs/coordination/checkpoint_provenance_decision_20261010_v1/public_release_metadata_receipt_001.json)
- [Author clarification metadata receipt](../runs/coordination/checkpoint_provenance_decision_20261010_v1/author_clarification_metadata_receipt_002.json)
- [680-check evidence self-review](../runs/coordination/checkpoint_provenance_decision_20261010_v1/release_and_decision_evidence_root_review_001.json)
- [Owner decision packet](phase2/cho_owner_decision_packet_20261010.md)
- [Unsent provenance request](phase2/checkpoint_provenance_request_draft_20261010.md)

The next provenance input is a training manifest, execution log or precise
attestation tied to the original SHA-256, with dataset versions and recording/
subject identifiers sufficient to assess Cho2017, IV-2a and MMIDB overlap.
The separate owner decisions are specified in the packet. Both original LaBraM
attempts remain spent; zero remain. This audit admits no scientific case,
relaunch, reset or renamed equivalent attempt.
