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

## Merge checks: source-bound controls now required

Week 2 installs shuffled-label and subject-disjointness checks in CI; Week 3 adds
the pre-cue control, and the final plan describes three tests on every merge.
The earlier local hooks freshly constructed LOSO/grouped subject splits but
revalidated historical control records for the other two checks. Those records
had no source fingerprint, so their passing means could not establish current
pipeline coverage. They remain preserved with their actual original provenance.

The implementation now requires all 45 configured real-data control fits, keyed
by the full local source fingerprint, original configurations, 18 raw MAT and nine
pre-cue artifact hashes, installed packages, Python/platform, NVIDIA device/driver
and relevant numerical thread environment. A missing, changed or incomplete key
fails CI. A matching bundle is independently revalidated on each merge; it is
not retrained for documentation-only changes. Source, data or environment changes
require a new full bundle before the local hook can pass.

Verification reconstructs the exact session split and development-only shuffle,
checks full training/early-stopping histories, counts scores from the actual saved
query predictions, and checks the unchanged cohort-level limits. Historical
summary booleans cannot substitute for that evidence. The Phase I status command
also rechecks the current bundle instead of trusting the last saved CI status.

`scripts/refresh_source_bound_controls.py` runs/resumes the complete cohorts in a
separate keyed directory. It preserves historical runs and checkpoints, uses the
original training routine, and retains the 10 GiB start / 4 GiB model-call RAM
guards and GPU cooling policy. This is a check of the configured BCI controls,
not a new blanket clearance for Cho/MMIDB or the matched MOABB reference. Remote
branch protection and the pending support-draw decision remain separate.
