# Bounded EEGNet source training and selection

8 September 2026, milestone 20. P2 now has an executable source-fit and candidate
selection path for the BCI EEGNet anchor. This is engineering integration, not a
converged scientific source fit or a frozen experiment search. Other methods and
datasets still need their own source-training integration.

## Contract and execution

`adaptation.source_selection.BCIEEGNetSourceSelector` consumes the complete nine
BCI catalogs, reconstructed source-selection envelope, pinned Profile A manifests,
outer subject, immutable candidate tuple, explicit seed, shot count and total
gradient-step ceiling. It reuses the actual anchor's cohort admission and audited
Profile A loader. Each `EEGNetCandidate` contains explicit source settings and
the existing `EEGNetAnchorSettings`; source and support input scales must agree.
Unknown candidates, duplicate settings, incomplete cohorts and invalid roles fail.
All nested episodes must be eligible before fitting starts. Cho/MMIDB are rejected;
their source eligibility policies are not guessed or silently reduced.

`run_fold(candidate_name=..., validation_subject=...)` runs one diagnostic fold.
Its evidence says `complete=false` and has no winner. `run_selection()` runs all
eight source-only inner folds for every declared candidate. Each fold starts from
identically seeded random EEGNet weights, fits only the seven permitted sources,
then uses the existing anchor runner for selected support adaptation and complete
common-query inference on the inner-validation subject. The outer target's signals
and outcomes are never read by the executor. Its catalog remains part of the
audited cohort identity and eligibility checks.

Source fitting uses the installed EEGNet with 22 channels, four outputs, 512 samples,
128 Hz and a constrained linear head. All parameters receive fresh SGD with no
momentum or weight decay. Every module remains in evaluation mode: dropout is off,
normalization buffers stay fixed, and affine parameters remain trainable. Sources
are visited in canonical order. An independent CPU generator seeded with the
declared model seed generates a subject permutation; fixed-size batches wrap that
permutation when needed. Every step records its subject, exact trial IDs, wrap
count, loss and resulting full-state digest. RNG state is isolated from the caller.
No pretrained initialization or early stopping is inferred from earlier smoke runs.

The score is balanced accuracy from each inner subject's full query confusion
matrix, averaged equally across subjects. Class ties use NumPy's first-index argmax.
Recall fractions and their means use exact rational arithmetic; a score tie chooses
the first candidate in the declared roster. External scores and partial-result
imports are unsupported. Any failed fold prevents a selection result and final fit.
After all folds finish, the winner is initialized afresh and fitted on all eight
non-target sources. Inner-fit weights are never reused as the final source weights.

The executor preflights the worst-case source-plus-support gradient count, including
the winning final source fit. It rejects requests above the caller's ceiling or the
hard engineering ceiling of 256 steps. Source and query batches are capped at 32
trials. These bounds cover this small CPU implementation; they neither admit heavy
training nor replace existing RAM, disk and thermal guards. There is no scheduling,
parallelism, automatic retry or optimizer resume.

## Evidence and reuse

`SelectionEvidence` holds canonical immutable JSON. Its decoded dictionary is a
copy, and `write()` uses the existing atomic no-clobber Phase II writer. Records
remain `engineering_smoke`; no scientific-cell writer or gate is invoked. The
contract pins candidate order/settings, seed, protocol, catalogs/manifests, current
source/Git identity, Python/Torch/NumPy/Braindecode versions and CPU execution mode.
Source/config identity is checked again before returning evidence. Fit records pin
actual source artifacts and base configuration. Validation records include audited
support/query IDs, their input identities, support fit, adapted-state digest and
confusion matrix. The final fit has a separate history and state digest.

The returned final model can be supplied to the existing EEGNet anchor runner.
It is mutable, so a consumer must check its state digest against the final-fit
record before reuse. The old runner's `source_training_history_verified=false`
is preserved: this addition does not silently certify arbitrary source templates.
Histories are complete only for the bounded fits performed here. Failed attempts,
safe scientific checkpoint publication, trusted history import and complete installed
environment validation still belong to the future scientific run recorder.

## Verification

The focused suite initially passed **7 tests / 15 subtests**. It independently
replays the recorded source batches and reproduces every state hash; checks fixed
buffers, cleared gradients, seed effects and caller RNG; and completes actual
eight-fold selection after replacing the outer artifact with unreadable bytes.
Further checks cover score ranking and exact ties, fresh final fitting, failed-fold
refusal, no-clobber writes, incomplete evidence, invalid contracts/budgets, source
corruption, nonfinite loss and iterator wraps. Full lint and strict types pass;
the exact-source suite passes **482 tests / 774 subtests**. The four warnings are
the existing EEGNet deprecations, sklearn warning and pytest cache access warning.
The full raw test summary is retained in the milestone receipt and quality log.

Real check: outer subject 01, inner subjects 02 through 09, one shot per class,
seed 23, CPU float32 and two Torch threads. Two candidates were declared before
execution: source SGD rates 0.0001 and 0.0002, one four-trial source step per subject,
input scale 1,000,000 from stored volts, and identical one-step support SGD at 0.0001
with query batches of eight. The selection ceiling was 136 total gradient steps.
These values exercise the implementation and are not scientific search defaults.

Both candidates completed all eight inner folds: **16 fits of seven source steps**,
28 sampled source trials per fit, four support trials per inner subject and all
7,924 query predictions across the 16 folds. Subject 09 has 490 queries; the other
inner subjects have 496. The winner received a fresh **eight-step source fit** on
32 sampled trials. Repeating candidate one's subject-02 fold was exactly identical
and produced incomplete diagnostic evidence rather than a second winner.
Including that repeat, actual work was **127 source steps and 17 support steps**.
There were **zero outer-target predictions**. No outer accuracy was computed.

The final source was saved as safetensors and strictly reloaded with an identical
state digest. All 36 pre-existing A/B artifacts/manifests, nine episode records and
the original selection record retained their hashes; caller RNG and source identity
were preserved. No existing source/config/test file changed: only the new executor
and tests were added. Previous quality status is saved in the evidence directory.

Evidence directory: `runs/phase2/source_selection_checks/20260908_step20/`.
It contains the check script/log, immutable complete selection and repeated-fold
records, bounded final-source safetensors, real-data receipt, focused/full-quality
logs and preservation receipts. Current source fingerprint:
`0c0ae1438d8faa5371c0d43edffd50f69604bf2161d154d9554d1dfe223ef955`.

## Next work and unchanged gates

Next is source-fitting and selection integration for LaBraM, including each method's
source-trained components, followed by the remaining method adapters and scientific
run recorder. EEGNet normalization/search schedules also remain subject to the
measured pilot and scientific freeze. Cho/MMIDB profiles and source-policy handling,
complete environment/resource admission, measured P3 pilot, faithful TCPL parity
and broader scientific experiments are still open. The RAM-dependent control refresh
remains deferred at the user's request. No guard, method configuration, scientific
gate, original experiment count or frozen H2 margin changed in this step.
