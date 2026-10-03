# LaBraM runner and selector generalization beyond the BCI cohort

17 September 2026, milestone 31. The LaBraM manifest runner, the three
source-trained runners and the source selector now admit any declared
dataset cohort instead of the fixed nine-subject BCI world: admission derives
the complete subject roster, classes and montage from the protocol
configuration, episode loading dispatches on the pinned asset inventory, and
class counts flow from the catalogs instead of literals. The primary E2
comparison path (linear vs LoRA on Cho2017) is now cohort-ready end to end;
executing real Cho cases waits only on the full fifty-two-subject Profile B
cohort, which is disk-gated.

## Contract and implementation

`evaluation/phase2_profile_binding.py` gained `ChoProfileAssets` (two pinned
digests; Cho Profile A has no sidecars), the `DATASET_CHANNELS` /
`DATASET_CLASSES` tables and `dataset_cohort()`, which derives the complete
declared subject roster from `expected_subjects` and refuses any pruned
cohort. `BCIProfileAssets` moved into the binding module beside it and is
re-exported for compatibility.

`LaBraMTuningManifestRunner` admission now requires the dataset-declared
cohort, classes and montage, the profile directories matching that roster, the
classifier montage/head matching the dataset, and an asset inventory whose
type matches the dataset's sidecar convention (BCI three-digest inventories,
Cho two-digest inventories). Episode loading dispatches per asset type to the
BCI or Cho binding; the prompt generator's class count, the logits-shape
check and the prediction binding field follow the declared classes. The three
trained runners (LoRA, adapter, prompt) received the same dispatch, widened
asset inventories and head-derived logits checks; their admission flows
through the generalized tuning runner. `BCILaBraMSourceSelector` records the
actual dataset in its contract, sizes confusion matrices and exact-rational
scores by the logits' class count, derives gradient-step admission from the
actual cohort size instead of the hardcoded eight-subject arithmetic, and
dispatches source-fit episode loading per asset type.

## Verification

The focused suite passed **4 tests** on a complete synthetic three-subject
Cho world (64-channel, two-class, one rejected trial per subject): the tuning
runner predicting the outer target and an inner-validation fold with
(7, 2)-shaped logits over the fixed query pool; a complete single-candidate
selection with two inner folds, a fresh final two-source fit and 2×2
confusion matrices; the trained support-prompt runner continuing a fitted
generator to a (7, 2) target prediction; and mismatched asset inventories
plus pruned cohorts refusing. The unchanged BCI suites — manifest, LoRA,
adapter, prompt, source, trained-source — all pass unmodified.

The real-data check ran the generalized admission over the full BCI world
with the safe checkpoint (496 four-class queries predicted through the linear
path) and confirmed that the real partial two-subject Cho cohort fails closed
at the selection layer, as it must until the remaining fifty subjects exist.

Full lint and strict types pass. The exact-source suite passes **550 tests /
914 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/cho_runner_checks/20260917_step31/`.
Current source fingerprint:
`e2b0dfdf3413615b07f629ff1ae6799ff9385286753cf0d69e1231467dd3a91c`.
Changed pre-existing files: `evaluation/phase2_profile_binding.py`,
`adaptation/labram_manifest.py`, `adaptation/labram_lora_trained.py`,
`adaptation/labram_adapter_trained.py`, `adaptation/labram_prompt_trained.py`,
`adaptation/labram_source.py`, `evaluation/phase2_pilot.py` (import only);
new: `tests/test_labram_cho_runner.py`.

## Next work and unchanged limits

The anchors and TCPL paths remain BCI-cohort-bound (the pilot's primary
tranche needs none of them), and MMIDB remains unstarted. Generating the
remaining fifty Cho Profile B subjects is the next prerequisite and needs
freed disk (~2 GB against the unchanged 20 GiB floor). The D01-D06 decisions,
operator compute admission, the scientific freeze and the RAM-deferred
control refresh remain user-gated. P2 remains partial; no gate or guard
changed and no scientific experiment ran.
