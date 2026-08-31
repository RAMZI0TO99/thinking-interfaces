# Phase I methodology and datasets draft

The evaluation is leave-one-subject-out. For each target subject, all other
subjects form the source set. The target support set contains the earliest five
trials per class; every remaining target trial is query-only. Source and target
identifiers are asserted disjoint, and support/query trial indices cannot overlap.

In the main seven-method matrix, source and target-support trials are fitted
jointly. This is distinct from the separate 45-run two-class EEGNet baseline
that first fits on source subjects and then fine-tunes on target support only
(`eegnet_support_finetuning.md`). Neither protocol is mislabeled as the other.
The pinned Braindecode EEGNet implementation is reviewed in
`eegnet_implementation_review.md`; known differences from the authors' Keras
model prevent any claim of exact implementation parity.

For Cho2017, "earliest" refers to the available within-class order: the installed
MOABB loader concatenates left and right arrays, not a reconstructed original
acquisition timeline. Its noncontinuous-trial edge warning and the use of
zero-phase Profile A filtering are explicit limitations. The subject 43 red-team
review and six shuffled-label controls are documented in `cho_subject43_review.md`;
they do not establish absence of all preprocessing or acquisition confounds.

Profile A applies 8-30 Hz filtering, common-average reference, 128 Hz resampling,
a one-second pre-cue baseline, and a four-second post-cue epoch. Profile B applies
the LaBraM-compatible 0.1-75 Hz band, origin-specific 50/60 Hz notch, 200 Hz
resampling, 0.1 mV scaling, and one-second patches.

The A01 Profile A/B compatibility check yielded 56.60% versus 25.35% balanced
accuracy. Trial metadata matched exactly, but the comparison also changed input
units, effective temporal-kernel duration, referencing and baseline correction.
It does not isolate a causal effect of filtering or establish interchangeability;
the unresolved differences are detailed in `profile_comparison_review.md`.

The public cohort contains nine BCI Competition IV 2a subjects (5,184 trials),
52 Cho2017 subjects (10,520 trials), and 109 MMIDB subjects (4,917 trials before
artifact rejection). S088, S089, S092, and S100 follow the precommitted
retain-with-structural-validation policy. One incomplete terminal motor cue in
S104 is dropped because it cannot supply the full baseline and epoch.

Artifact rejection is label-blind and frozen before the final benchmark. Each
dataset's threshold is its complete-cohort 99.9th percentile absolute trial peak:
54.483 µV for BCI IV 2a, 5.895795 mV for Cho2017, and 986.971 µV for MMIDB. This
rejects 6, 11, and 5 trials respectively. Rejection occurs before splitting, and
every subject retains every class.

The benchmark methods are EEGNet, ShallowFBCSPNet, Deep4Net, filter-bank CSP,
Riemannian tangent-space logistic regression, Euclidean-aligned EEGNet, and
Euclidean-aligned tangent-space logistic regression. Euclidean Alignment is fit
separately per source domain and from target support only; query trials do not
contribute to the target alignment matrix.

Five fixed model seeds are used; the earliest support/query partition is identical
across those seeds. Neural fits vary their training random state. Deterministic
classical fits are computed once and explicitly reused in the other seed-labelled
records, with zero additional fitting time. These are not five support resamples.
The build plan's seeded-earliest-draw wording requires a still-pending protocol
decision (`phase1_protocol_decisions.md`); no larger early-trial pool is invented.

Every fold writes an atomic run record immediately.
Aggregation averages seeds within subjects before reporting a 95% interval over
subjects. Each record includes class support, a flattened confusion matrix, kappa,
calibration error, coverage, latency, and rejected-trial counts. Failed, stale, or
absent records remain visible in the configuration-hash completeness report.
