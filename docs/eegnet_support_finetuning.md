# Separate source-then-support EEGNet baseline

The main frozen seven-method table fits decoders jointly on source trials plus
the earliest target support trials. That is not the same optimization protocol
as first fitting only on other subjects and then fine-tuning on target support.
The main table must not be described as that separate fine-tuning baseline.

The build plan also requests an EEGNet `adapt()` fairness baseline. This distinct
run uses BCI IV 2a left/right hand, nine held-out subjects, and five independent
seeds (45 records). Each source-only model receives five training epochs. A clone
then receives ten full-model AdamW updates from ten target support trials only,
at learning rate 1e-4 and the adapter utility's explicit 0.01 weight decay.
The remaining target trials are never used for adaptation or early stopping.

Settings are fixed in `configs/eegnet_support_adaptation.toml`. Results are written
atomically under `runs/support_adaptation/`, not into the main benchmark table.
Each record contains before/after scores, confusion counts, class supports,
training/adaptation timings, split fingerprints, and model-change invariants.
The source model is cloned and checked unchanged. A real-model test inspects the
actual arrays received by both source training and adaptation.

`scripts/audit_support_adaptation.py` verifies the exact 45-record grid, config
digests, fixed membership across seeds, arithmetic, and functional invariants.
`scripts/phase1_status.py` requires this independent audit before local completion.
The live status, not this document, determines whether all runs have finished.

## Completed local run

All 45 records passed the independent audit on 2026-08-31, with no missing,
unexpected, or invalid records. Subject-and-seed averaged balanced accuracy was
68.60% before and 69.30% after adaptation, a descriptive +0.70 percentage-point
change, not a significance or generalization claim. Total measured adaptation
time was 2.473 seconds (median 0.0536 seconds per fold); source fitting took
61.326 seconds in total. These timings exclude data loading and cooldowns.

Subjects 03 and 08 have five-seed adapted means of 90.58% and 92.45%. These exceed
the plan's plausibility band and remain flagged, not scientifically cleared by
the functional audit. The subject/episode-disjoint tests and source-only fitting
checks pass, but no separate raw-signal or subject-specific shuffled-label
control for these two new readiness folds is claimed.

This check establishes the requested executable calibration protocol, not a
favorable adaptation effect or a fair cross-method E2 result. In particular, its
two-class scores must not be compared directly against the four-class BCI rows
of the main table. A Phase II comparison must match tasks, source/support draws,
seeds, and training budgets across methods. Gate A remains unsigned.
