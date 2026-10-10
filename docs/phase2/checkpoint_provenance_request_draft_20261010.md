# Checkpoint provenance request draft, 10 October 2026

Prepared and **unsent**. Intended recipient: the LaBraM checkpoint author or
maintainer, through a channel selected by the owner. No recipient address or
posting channel has been selected; no third party was contacted. Sending or
posting requires an explicit user instruction covering that action.

Subject: Recording-level pretraining provenance for released LaBraM base checkpoint

Hello,

We are preparing a subject-level motor-imagery evaluation using the released
LaBraM base checkpoint. We have verified that our original file matches the
official release at commit `c431221e6cfd23dbfa9950e0180682fb322b0548`:

- File: `checkpoints/labram-base.pth`, 96,612,769 bytes.
- SHA-256: `7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`.
- Git blob: `221148b5af403e9178629bb61e94b2e7d89ef172`.

Our converted file also matches the public Braindecode snapshot
`0563b6c626e7b40d9a36653b763715db94d945d7`, with SHA-256
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`.

Could you provide a training manifest, execution log reference or a provenance
statement tied to the original checkpoint hash that identifies the datasets,
versions and recording/subject identifiers actually used for its pretraining?
Public identifiers or privacy-preserving mappings would be sufficient; we are
not requesting redistribution of any raw recordings.

For our planned datasets, could that statement specifically establish:

1. Whether Cho2017 motor-imagery subjects or recordings were included, and
   which versions, recordings or exclusions apply.
2. Whether BCI Competition IV-2a subjects or recordings were included. We
   understand the paper's named IV-1 dataset is distinct from IV-2a.
3. Which MMIDB subjects, runs and splits were included in this checkpoint's
   pretraining, and whether any evaluation recordings were excluded. The paper
   lists MMIDB, but does not identify the checkpoint's recording-level cohort.

Please also identify the source/date of the statement and how the released
checkpoint is linked to that training run. If a recording-level mapping is
unavailable, an explicit statement of that limitation would help us constrain
our evaluation claims accurately.

Thank you.

---

Owner note: the reviewed [author discussion](https://github.com/935963004/LaBraM/issues/35#issuecomment-2285361279)
directs users to original dataset publishers and explains limits on
redistribution. This draft asks for provenance identifiers instead. Its
scientific context and local evidence are in the
[release report](../checkpoint_release_provenance_20261010.md) and
[owner decision packet](cho_owner_decision_packet_20261010.md).
