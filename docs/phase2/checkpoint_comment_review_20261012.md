# Released LaBraM checkpoint: public comment review and maintainer request

12 October 2026. The reviewed public discussion does not establish the released
checkpoint's recording-level training coverage or evaluation overlap. The owner
approved the exact prepared request, and it was posted as
[LaBraM issue #75](https://github.com/935963004/LaBraM/issues/75) from `RAMZI0TO99`
at **11:23:25 UTC**, without attachments. A fresh authenticated GET confirmed
the repository, author, title and exact normalized body hash. No maintainer
response has been reviewed in this step.

## Scope and result

The bounded GitHub API acquisition completed at **11:08:14.728719 UTC**. It
captured **67 issues, 6 pull-request entries and 222 issue comments**, including
65 comments with GitHub's `OWNER` association. Every comment count matched its
listed entry and every included issue-comment page was complete. The capture
precedes our new issue. English and Chinese discussion was reviewed, including
the maintainer comments and the surrounding questions for the findings below.

Literal searches of captured bodies found no occurrences of the checkpoint SHA,
official commit, `MMIDB`, `Cho2017`, `IV-2a`, `manifest`, `PhysioNet` or
`motor imagery`. This is a limited search observation; it does not establish
that any evaluation subject or recording was excluded from training.

| Public maintainer statement | What it establishes here | Limit |
| --- | --- | --- |
| [Issue 13: subjects in the random train/validation split were not recorded](https://github.com/935963004/LaBraM/issues/13#issuecomment-2062855260) | The [preceding question](https://github.com/935963004/LaBraM/issues/13#issuecomment-2060984494) specifically asks about TUAB fine-tuning. | This does not attest to the released checkpoint's pretraining cohort. |
| [Issue 48: AR references, four TUEG subsets and other jointly used datasets](https://github.com/935963004/LaBraM/issues/48#issuecomment-2540452438) | Additional preprocessing and dataset context; some company-developed code and access were held by colleagues. | No checkpoint-bound subject, recording, version, split or exclusion manifest. |
| [Issue 11: pretraining used no labels](https://github.com/935963004/LaBraM/issues/11#issuecomment-2040891284) | General statement about the pretraining objective, paraphrased from Chinese. | Unlabeled EEG exposure can still overlap evaluation recordings; no hash-bound coverage attestation. |
| [Issue 66: sequential training across datasets](https://github.com/935963004/LaBraM/issues/66#issuecomment-3204438310) | The author describes forgetting and a later shuffled-dataset approach in NeuroLM, paraphrased from Chinese. | NeuroLM's implementation and provenance cannot substitute for this LaBraM checkpoint. |
| [Issue 35: downstream preprocessing is distinct](https://github.com/935963004/LaBraM/issues/35#issuecomment-2270321673) | `make_TUAB.py` and `make_TUEV.py` prepare downstream tasks; a separate helper handles pretraining, paraphrased from Chinese. | A preprocessing helper does not identify the files actually used in a training run. |
| [Issue 35: most pretraining datasets were publicly obtainable](https://github.com/935963004/LaBraM/issues/35#issuecomment-2285361279) | The author directs readers to original dataset publishers, paraphrased from Chinese. | Public availability is not an execution record or an actual cohort mapping. |
| [Issue 60: larger models and some preprocessing code unavailable](https://github.com/935963004/LaBraM/issues/60#issuecomment-2870835041) | Release constraints and SEED-V/MoBI preprocessing context. | No recording inventory for the released base checkpoint. |

PR inline review comments, Discussions, images, attachments, deleted entries,
external archives/repositories and future comments are outside this capture.
Third-party replication reports are public context, not accepted project cases.
The existing [checkpoint release audit](../checkpoint_release_provenance_20261010.md)
and [pretraining audit](../checkpoint_pretraining_provenance_20261010.md) keep
their earlier scope; this step did not deserialize or inspect weights again.

## Verified publication

The original approved draft's raw SHA256 was
`5563ed7a099de9a9d031a04773e491cf42d78503ebcb2fb4c29492835d53f52c`.
The posted body, normalized to LF, has SHA256
`e8db8f6c1e690df9b1ceb763797dea21ae51acdac8233c29b3128881c272eed5`.
The authorization request is preserved with SHA256
`c07b98420d5f6de1b0a4c38190c56e70eb474df3428b1804fd0d193249c214f7`.
The new issue has GitHub ID `5812871791`; POST returned 201 and the independent
verification GET returned 200. Account and repository access were freshly
checked; a complete bounded issue listing found no matching existing request.
Exactly one POST was made. The local evaluation inventory, arrays, labels and
weights were not uploaded. Credentials remained in memory and are absent from
the saved request/response bodies and logs.

The issue identifies the 96,612,769-byte released base checkpoint at official
commit `c431221e6cfd23dbfa9950e0180682fb322b0548`, SHA256
`7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`,
and asks about actual coverage of MMIDB, BCI IV-2a and Cho2017. The seven owner
decisions and the [owner packet](cho_owner_decision_packet_20261010.json) have
not changed. No follow-up message, inventory attachment or automatic poll is
authorized by this single posting action.

## Executed evidence and continuation

[Portable evidence](../../evidence/checkpoint-comments-20261012/README.md)
preserves the raw API captures, exact approved draft/body, POST and GET responses,
executed recipe bytes, byte identities and native supervision receipts.
Metadata operations used fresh finite Windows Jobs, startup RAM 10 GiB,
active RAM 4 GiB, disk 20 GiB, process 256 MiB, Job 512 MiB and one native thread.
The account check, acquisition, publication and evidence assembly Jobs completed
successfully. The three earlier Jobs were physically absent when assembly ran;
each guard also confirmed its own Job empty, closed and absent at completion.
The finalized offline verification passed for **111 indexed files**, the 222
comments, their 65 owner associations and the exact public request in Job
`20261012T113237Z_7f5562a17e`. Its
[qualification manifest](../../evidence/checkpoint-comments-20261012/qualification/manifest.json)
binds the checked index SHA256 and preserves the final admission/log/receipt.
Five earlier owned Jobs were freshly physically absent at finalization; the
final verification Job also completed empty, closed and absent. Recipe lint
passed with only the deliberate isolated import bootstrap excluded (`E402`).
This is offline evidence identity checking, not scientific validation.

Canonical source remains **432 files / `3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529`**.
Historical quality SHA256 remains
`4eb4d5566f496bc3d6143fc7046ca505e750829631332fc3697cb60dc2a01357`;
the historical full suite was not replayed. Owner packet SHA256 remains
`2a890980541120b4d311078436fe85aac13e77f3f33871739ab62347320ff400`.
No raw EEG, cache rebuild, model inference, fit, recorder or original case ran.
Gate A, the experiment freeze and seven owner decisions remain unsigned.
The original case has **two spent attempts and zero remaining**. Current
checkpoint recording coverage and evaluation overlap remain **unknown**.

When authentic new provenance arrives, capture it with its date, author and
checkpoint binding, then review the mapping against the
[170-subject/397-recording inventory](evaluation_recording_provenance_package_20261011.md).
An incomplete or unavailable mapping needs an explicit limitation and an owner
decision about permissible claims. Owner decisions are still required before
scientific advancement; an issue reply alone does not admit a new runtime case.
Any subsequent execution needs fresh scope, pins, coordination and admission.
