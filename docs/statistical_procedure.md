# Phase I statistical procedure

Fixed on 2026-08-30 before the Phase I benchmark table was complete.

## Unit of analysis

The subject is the unit of analysis. Repeated seeds are averaged within each
subject before a mean, standard deviation, confidence interval, or hypothesis
test is computed. Trials are never treated as independent replicates for a
cross-subject claim.

The table separately reports the standard deviation of dataset means across
seeds (`seed_mean_standard_deviation`), as requested by the build plan. It is not
the between-subject SD used for intervals or power. Partial-grid seed comparisons
use only subjects present at every observed seed and expose that count; final
reporting requires the complete grid. Deterministic methods have zero seed
variation by design, not five independent fitting replicates.

## Method comparisons

Methods are compared on the same dataset, target subjects, folds, support draw,
and seeds. The primary reported quantity is the paired subject-level difference
in balanced accuracy with a two-sided 95% t interval. The precommitted
non-parametric test is the paired Wilcoxon signed-rank test using Pratt handling
for zero differences.

## Equivalence

Equivalence is evaluated with paired two-one-sided t tests (TOST). The margin is
not three percentage points by default. It is derived once from the Phase I
benchmark's between-subject standard deviation, target power 0.80, one-sided
alpha 0.05, and the available subject count using the normal approximation:

`margin = (z(1-alpha) + z((1+power)/2)) * subject_sd / sqrt(subject_count)`.

Arithmetic correction recorded on 2026-08-31, before any Phase II comparison:
both one-sided bounds must pass. Under zero true difference and known variance,
`power = max(0, 2*Phi(margin/SE - z(1-alpha)) - 1)`. The earlier single-tail
formula labelled a design with 60% joint power as 80%; it is not used for the
freeze. An independent simulation of both bounds tests the correction.

This is an approximate planning calculation, not exact finite-sample t-test
power. Baseline between-subject SD is the plan-prescribed proxy; the future
paired-difference SD and true difference are unknown, so actual H2 power is
not guaranteed by the reported design power.

The selected margin, source benchmark row, subject count, and achieved design
power must be written to the freeze record before any Phase II comparison is run.

## Multiple views

Every benchmark row reports balanced accuracy, standard deviation across
subject means, a 95% subject-level interval, Cohen's kappa, class support,
confusion matrix, expected calibration error, accuracy-versus-coverage, and
latency. Selective metrics never replace the ungated primary score.
