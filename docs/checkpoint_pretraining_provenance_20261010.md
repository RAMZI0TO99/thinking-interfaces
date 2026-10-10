# Checkpoint pretraining provenance review, 10 October 2026

The pinned original checkpoint declares an epoch and training arguments, but
does not identify a verifiable pretraining cohort. The local paper supplies a
named dataset list; no execution record links that list to this checkpoint.
Target overlap remains unresolved. This is root's Source self-review, with no
numerical validation, independent acceptance or scientific signature.

## Executed read-only inspection

The original `checkpoints/labram-base.pth` retained SHA-256
`7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`.
The existing inert protocol-2 parser retained SHA-256
`50f401968a8d9b6a32a8591c06bd2cc45e9af38e383f54110c96d115a18db812`.
The bounded 100,949-byte ZIP metadata was inspected without `torch`, unpickling,
object reconstruction or model construction. Both files were verified before
and after inspection; execution Git was clean `d8b7a44`.

| Recorded field | Declared value |
| --- | --- |
| `epoch` | 49 |
| `args.epochs` | 50 |
| `args.model` | `beit_base_patch200_1600_8k_vocab_align` |
| `args.input_size` / `args.patch_size` | 1600 / 200 |
| `args.batch_size` / `args.seed` | 64 / 0 |
| `args.data_set` | `image_folder` |
| `args.data_path` | one path, final directory label `061417` |
| `args.eval_data_path` | empty string |

These are stored declarations. Epoch49 does not independently certify a
completed50-epoch run, and the generic loader label/date-like directory label
does not name the training recordings. Absolute paths and other arbitrary
argument values were omitted from the saved path inventory.

The original 1600-sample declaration is separate from the current 800-sample
working configuration and its documented temporal-embedding crop. The prior
[weight correspondence review](checkpoint_correspondence_review.md) establishes
retained tensor-byte identity, not training-cohort identity.

## Local paper review

The local [LaBraM ICLR2024 paper](../runs/references/labram_iclr2024.pdf) retained
SHA-256 `5ac7a9b3ee783d1a70340c7248b91e4f661204e0415393f8b30b10795d82e01d`.
Root extracted text and visually inspected complete pages9,17 and18 using
bundled PDF tools. Pages17-18 contain the complete Appendix D list.

Appendix D declares MMIDB at47.3 hours and BCI Competition IV-1 at8.21 hours.
IV-1 is distinct from IV-2a. Cho2017 and IV-2a are absent from the named list;
that absence cannot establish exclusion from this checkpoint's training.
Page9's TUAB/TUEV disjoint-recording assertion covers those datasets and does
not resolve Cho, IV-2a or MMIDB evaluation overlap.

Appendix D states a2534.78-hour total. Adding the16 grouped entries' printed
hours gives2538.38, a3.60-hour difference. The arithmetic and each entry are
retained in the Source review receipt. No cause, rounding adjustment or
replacement total has been inferred; this needs provenance clarification.

## Evidence and remaining work

- [Inert argument inventory](../runs/coordination/cache_performance_20261008_v1/checkpoint_training_metadata_inventory_20261010_001.json)
- [Dataset path declaration inventory](../runs/coordination/cache_performance_20261008_v1/checkpoint_dataset_path_declarations_20261010_001.json)
- [Paper/metadata root Source review](../runs/coordination/cache_performance_20261008_v1/checkpoint_paper_provenance_root_review_20261010_001.json)

Resolve this with the checkpoint's training manifest/logs or a precise
provenance statement tied to its hash and recording-level cohort. A generic
path, paper list, retained-weight correspondence or engineering cache receipt
cannot supply that missing mapping. Future MMIDB evaluation must disclose the
paper's explicit pretraining inclusion. Scientific Gate A and the experiment
freeze remain unsigned; both spent real LaBraM attempts remain preserved.
