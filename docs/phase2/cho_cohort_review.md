# Full Cho2017 cohort and the first real Cho engineering folds

17 September 2026, milestone 32. The complete fifty-two-subject Cho2017
Profile B cohort now exists (1.9 GiB, user-authorized against the disk floor;
23 GiB remained free afterward), every subject passed the preparation audit
against its untouched Profile A artifact, and the primary E2 comparison
machinery ran on real Cho data for the first time: bounded linear and
source-trained LoRA diagnostic folds over fifty permitted source subjects
with inner-validation predictions of the fixed common query pool. Zero
outer-target predictions were made.

## Generation and audit

The remaining fifty subjects were generated with the unchanged milestone-29
pipeline over the pinned local GIGADB raw files. The cohort totals 10,520
trials in two shapes (200 or 240 trials per subject, always 64 × 800). The
preparation audit re-verified for every subject: per-trial label and session
correspondence with the audited Profile A catalogs, the fixed 64-channel
montage, finite float32 signals, manifests matching the actual shapes, and
Profile A artifact hashes unchanged from the pinned audit records.

## First real Cho folds

Using the generalized runner/selector path and the safe pretrained LaBraM
checkpoint with the 64-channel electrode mapping, two bounded diagnostic
folds ran on the real cohort with outer target `subject_01` and inner
validation `subject_02` (the pilot specification's named subjects):

- A plain **linear** candidate: fifty source steps (one per permitted source
  subject, both held-out subjects excluded), one support step, then all 159
  fixed common queries of the inner subject predicted with state checks.
- A **source-trained LoRA** candidate (last-block QKV, rank 4): the same
  fifty-step source fit through the trained-component path, its learned A/B
  tensors continued through validation support with the recorded
  no-reinitialization component policy.

Both folds recorded exact trial/state histories, verified that no
outer-target signal was read, and scored 1/2 — chance level for a two-class
problem under one-step engineering fits, which is expected and carries no
performance meaning. The complete 51-fold selections remain unexecuted: the
256-step engineering ceiling permits single diagnostic folds only, and
complete selections are separately charged scientific work awaiting
admission.

## Verification

Full lint and strict types pass. The exact-source suite passes **550 tests /
914 subtests** (no source file changed this milestone; the focused Cho suites
re-passed), with the same four existing warnings; raw results are retained in
the receipt. Evidence directory:
`runs/phase2/cho_cohort_checks/20260917_step32/`.
Current source fingerprint (unchanged from milestone 31):
`e2b0dfdf3413615b07f629ff1ae6799ff9385286753cf0d69e1231467dd3a91c`.

## Next work and unchanged limits

The pilot's Cho cases are now data-complete: cohort, binding, cohort-generic
runners and the executor all exist. What remains before any measured run is
user-owned: the D01-D06 register decisions, operator compute admission with
the scientific freeze of candidate counts and settings, and the RAM-deferred
control refresh before any checked commit. The anchors and TCPL selectors
remain BCI-bound by design; MMIDB remains unstarted. P2 remains partial; no
gate or guard changed and no scientific experiment ran.
