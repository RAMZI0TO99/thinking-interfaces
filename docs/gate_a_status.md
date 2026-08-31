# Phase I Gate A status

**Status: not signed off — stop before post-Gate-A work.**

On 2026-08-30, the user explicitly directed the build to continue to the next
milestone despite this unsigned gate. Downstream work is therefore exploratory
and does not retroactively change the Gate A result.

## Required acceptance condition

The Phase I build plan requires a four-seed, nine-subject, within-subject EEGNet
result on BCI Competition IV 2a that reproduces a published MOABB score, with a
passing shuffled-label control and subject-disjointness tests.

## Evidence

| Check | Result | Status |
|---|---:|---|
| Subject-disjointness contract | Overlap is rejected by tests | Pass |
| Shuffled-label negative control | 48.77% mean; required maximum 60% | Pass |
| Two-class Braindecode-aligned run | 71.72% mean, nine subjects, four seeds | Diagnostic only |
| Four-class Profile A run | 52.37% mean, nine subjects, four seeds | Fail against 74.50% comparator |
| Four-class 4–38 Hz + common average | 57.91% mean, nine subjects, one seed | Fail against 74.50% comparator |
| Full 300-epoch difficult-subject check | Projected all-subject mean about 61.8% | Insufficient |
| Published-training difficult-subject check | 52.43% mean for A04–A07 | Insufficient |

All final evaluation scores use the held-out second session once, after selecting
the model checkpoint from a validation subset of the first session. Evaluation
labels are never used for training or checkpoint selection.

## Blocking issue

MOABB's public benchmark table does not contain an EEGNet score for this dataset,
and MOABB has not published the cross-session result required by this project. The
74.50% comparison is from Du et al. (2022), not MOABB, and its Keras implementation
and full preprocessing/checkpoint-selection details are not available in the
paper. Matching its stated 1,000-epoch, batch-size-16, learning-rate-0.001, and
dropout-0.2 settings did not reproduce its subject-level results.

## Decision required

Choose and document one valid acceptance target before continuing:

1. Change Gate A to a fully specified, reproducible Braindecode cross-session
   protocol and approve a new threshold; or
2. Supply the exact implementation associated with the 74.50% result; or
3. Keep the current gate and stop Phase I here as a failed reproduction.

No acceptance threshold has been invented or changed automatically.
