# H2 falsification and equivalence planning freeze

Frozen locally on 2026-08-31, before any Phase II comparison. The original Full
Project Plan referenced as section 4 in the day-by-day documents is not supplied;
this companion records the requested H2 amendment, not a fabricated edit to that
missing document or an invented complete set of H1/H3 criteria.

## Empirical source and fixed margin

The source is the preselected Cho2017 EEGNet row: 52 subjects, five seeds, 260
independently audited records. Seeds are averaged within each subject. Mean
balanced accuracy is 0.6569043549 and between-subject SD is 0.1282074769.
All subjects, including flagged subject 43, remain included without post-hoc
selection. The benchmark is the frozen source-plus-support training protocol;
it does not estimate the performance of a future separate support fine-tuning
protocol.

The H2 equivalence margin is **±0.0520290793 balanced-accuracy units**, or
**±5.20290793 percentage points**. The one-sided alpha is 0.05 and the approximate
design power is 0.80 at zero true difference under the known-variance normal
approximation. The formula and earlier arithmetic correction are documented in
`statistical_procedure.md` and `deviation_log.md`.

`runs/equivalence_margin_freeze.json` records the exact source-file fingerprint,
benchmark configuration hash, source moments, margin, assumptions, and timestamp.
`scripts/freeze_equivalence_margin.py` validates the complete source grid and
refuses silent changes to an existing freeze. Rerunning unchanged is a no-op.

## Future H2 decision rule

Use the precommitted paired subject-level TOST on comparable folds and seeds.
Equivalence requires both one-sided tests to reject at alpha 0.05; equivalently,
the paired-difference 90% t interval must lie strictly inside the fixed bounds.
A failed equivalence test is inconclusive, not proof of inequality. An interval
clearly beyond a bound is evidence against that equivalence claim. Report the
paired difference and interval regardless of significance; do not widen the
margin after observing Phase II results.

## Limitations and scientific status

Baseline subject SD is a planning proxy, not the unknown paired-difference SD.
Finite-sample t-test power and power under a nonzero true difference can be lower;
80% is not a guarantee for the future experiment. Repeated seeds do not increase
the subject count. The unusually high subject 43 result and reconstructed Cho
trial-boundary risk remain documented in `cho_subject43_review.md`.

Gate A is unsigned; this margin freeze neither signs Gate A/B nor establishes
equivalence, efficacy, or artifact-free decoding. Changing the source protocol or
discarding subjects would require an explicit dated amendment and a new clearly
labelled planning analysis, not replacement of the saved freeze.
