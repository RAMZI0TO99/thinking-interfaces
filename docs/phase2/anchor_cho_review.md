# Anchors and TCPL beyond the BCI cohort

17 September 2026, milestone 33. The matched anchors and the remaining
selectors are now cohort-generic like the LaBraM path: a new Cho2017 Profile A
subject loader with catalog-hash identity, generalized anchor-runner
admission, dataset-dispatched source loading in the EEGNet and TCPL selectors,
EEGNet dimensions derived from the declared montage and head, and class counts
flowing from the logits everywhere. Real Cho folds ran for both anchors on
the full fifty-two-subject cohort with zero outer-target reads. The pilot's
primary Cho tranche — linear, LoRA, EEGNet and EA-tangent at five shots — is
now fully executable engineering.

## Contract and implementation

`evaluation/phase2_cho_profile_a.py` adds `load_cho_profile_a_subject`:
Cho Profile A identity is the audited catalog's artifact hash plus the frozen
threshold profile (no sidecar manifests), both re-verified against the bytes
on disk; the 64-channel montage, finite float32 shape (retained, 64, 512) and
retained-label correspondence are enforced before owned rows are returned in
the shared subject dataclass.

`adaptation/anchor_manifest.py` admission now derives the cohort, montage and
classes through `dataset_cohort`, requires the manifest inventory only for
datasets with sidecars (BCI), accepts EEGNet matching the declared
montage/head instead of the 22/4/512/128 literals, dispatches subject loading
by dataset, and the prediction's declared classes and probability shape
follow the catalog. `adaptation/source_selection.py` (EEGNet) constructs its
seeded model from the declared montage and class count, dispatches source-fit
loading by dataset, rejects manifest inventories for Cho, and derives
confusion/score class counts from the prediction. `adaptation/ea_selection.py`
derives its class counts the same way. `adaptation/tcpl_source.py` dispatches
its episode assembly loading by dataset. The BCI suites for all four modules
pass unmodified.

## Verification

The focused suite passed **3 new tests** (25 tests / 44 subtests with the
unchanged anchor and selector regressions) on the synthetic three-subject Cho
world: EA-tangent target and EEGNet inner-validation predictions with
(7, 2)-shaped probabilities, single-fold selections through both selectors
with two-class confusion matrices, and manifest-inventory refusal for Cho.

The real-data check ran both anchors on the full fifty-two-subject cohort
with the pilot specification's named subjects: an EA-tangent fold over all
fifty permitted sources (one classical refit) and an EEGNet fold with fifty
source steps, each predicting all 159 fixed common queries of subject_02.
Scores were 0.505 and 0.473 — near chance under one-step engineering fits,
carrying no performance meaning. Zero outer-target reads; exact-rational
scores re-verified from the recorded confusion matrices.

Full lint and strict types pass. The exact-source suite passes **553 tests /
914 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/anchor_cho_checks/20260917_step33/`.
Current source fingerprint:
`fe9e513a818ccfd7a43a4ddc2d67fcda05e3010db8458e297d510512a60d36e0`.
Changed pre-existing files: `adaptation/anchor_manifest.py`,
`adaptation/source_selection.py`, `adaptation/ea_selection.py` and
`adaptation/tcpl_source.py`; new: `evaluation/phase2_cho_profile_a.py` and
`tests/test_anchor_cho.py`.

## Next work and unchanged limits

Every method family in the pilot's primary Cho tranche now runs end-to-end
engineering on real data. The remaining bounded gaps are the MMIDB dataset
(low scientific priority, small query pools) and TCPL's Profile B dependence
(TCPL uses Profile A only and already runs on Cho through the toy-world
tests; a real Cho TCPL fold is bounded future work if wanted). Everything
else is user-gated: D01-D06 decisions, operator compute admission, the
scientific freeze and the RAM-deferred control refresh before any commit.
P2 remains partial; no gate or guard changed and no scientific experiment ran.
