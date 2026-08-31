# Phase I Gate A status

**Status: not signed off — reference verified; matched reproduction outstanding.**

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

All existing diagnostic evaluation scores use the held-out second session once, after selecting
the model checkpoint from a validation subset of the first session. Evaluation
labels are never used for training or checkpoint selection.

## Correction: verified MOABB reference

On 2026-08-31, direct inspection of the [official benchmark table](https://moabb.neurotechx.com/docs/paper_results.html)
confirmed EEGNet_8_2 results for BNCI2014_001. The earlier assertion that the table
contained only classical pipelines was incorrect. No historical page snapshot
establishes when its content changed, so this is a correction, not a claim of a
new publication.

The table reports within-session five-fold evaluation: left/right hand ROC-AUC
77.15% with SD 19.33 percentage points; all four classes accuracy 60.46% with SD
20.20 points. Its folds are averaged per subject/session, then summarized across
subject/session pairs. The SD is not a confidence interval or an acceptance band.
The day plan asks for within-subject reproduction and introduces two classes;
cross-session evaluation was our implementation choice, not a requirement of that
wording. The old balanced-accuracy scores are not directly comparable to the
published left/right ROC-AUC. The 74.50% Du et al. comparison is separate evidence,
not the MOABB target.

The table links [MOABB v1.1.2's Keras EEGNet pipeline](https://github.com/NeuroTechX/moabb/blob/v1.1.2/pipelines/Keras_EEGNet_8_2.yml).
That is a different implementation from the current Braindecode model. Its exact
preprocessing, split, training and dependency behavior must be checked before
launching a matching run; see `docs/moabb_reference_reproduction.md`.

## Remaining local work and acceptance decision

Prepare and test an isolated, protocol-matched left/right reference reproduction,
then report all nine subjects and the plan's four seeds without selecting a best
seed or tuning to the published mean. Keep it outside the frozen cross-subject
benchmark and retain every earlier diagnostic record unchanged. Final sign-off
still needs an explicit, scientifically defensible acceptance rule; no tolerance
has been inferred from the table's SD, invented, or changed automatically.
