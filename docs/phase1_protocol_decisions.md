# Phase I plan-fidelity decisions and remaining verification

This note records unresolved requirements, not approval to change the frozen
experiment or a scientific sign-off. The original Phase I DOCX remains unchanged,
SHA-256 `1bf381fd49edeb3acda2824f591ad4480019bb7cdcc1e926cac4f57c9b47d49e`.

## Support-draw seed: user decision pending

Week 1, Day 2, Adaptation says: "The seed controls which earliest trials, never a
random sample of the whole session." The current `earliest_balanced_episode` in
`core/splits.py` has no seed argument: it deterministically selects the first five
retained trials per class, with every remaining trial assigned to query. Its test
checks those exact earliest indices. The main harness supplies model-training
seeds but does not vary this support draw.

The fixed-earliest behavior was already disclosed in the deterministic-seed-reuse
deviation. This review identifies the additional point that it does not implement
the plan's literal seeded support selection. The plan does not specify a larger
eligible early-trial pool or its time/rank boundary; inventing one would change
support and query identities after the benchmark was frozen.

The user has been asked whether to retain the fixed-earliest rule as an explicit
deviation or define a seeded early-trial pool. No answer or approval is presumed.
The existing sweep continues under its unchanged, disclosed protocol while that
decision is pending. In particular:

- Neural seed variation represents repeated training on the same support/query
  partition, not variation in calibration-trial selection.
- Classical deterministic seed copies are valid descriptions of the existing
  fixed-partition computation, not five independently resampled episodes.
- If a new support protocol is selected, affected results require new identified
  runs and revised reporting; they cannot be mixed into the current config hash.
  Existing records, corpus evidence and the conditional H2 freeze must remain
  preserved rather than be overwritten or retroactively relabeled.
- Cho's unproven acquisition chronology remains a separate limitation. Adding a
  seed cannot reconstruct the original chronology from separate class arrays.

## Merge checks: historical control revalidation is not fresh pipeline coverage

Week 2 installs shuffled-label and subject-disjointness checks in CI; Week 3 adds
the pre-cue control, and the final plan describes three tests on every merge.
The local hooks really execute three checks. `evaluation/leakage_ci.py` freshly
constructs LOSO/grouped subject splits, but the other two checks validate saved
control configurations, cohort/seed coverage, individual metrics and recomputed
subject means. They do not retrain the negative-control models on each merge.

This is useful historical-evidence checking, not proof that the current numerical
training/data path would reproduce those controls. A green check must not be
described as that stronger claim. The historical scores remain valid evidence
with their original provenance; no current code identity is assigned to old fits.

Remaining local verification is to refresh the configured real-data controls and
bind any reused control evidence to the numerical code, input identities and
environment that actually produced it, or rerun it when those change. The
complete configured control cohorts must not be replaced with a conveniently
small chance-level example. This remains separate from the matched MOABB
reference evaluation and from remote branch protection, which is unavailable.
