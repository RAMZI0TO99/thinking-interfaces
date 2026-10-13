# Phase I Gate A status

## Fresh retained-record audit completed, 12 October 2026, 14:29 UTC

The [new readiness review](phase2/phase2_readiness_review_20261012.md) passed
all450 saved record hashes, configurations, split/history fields and retained
probability ROC-AUC arithmetic. It used current installed dependencies without
new fitting, raw-input replay or historical environment reconstruction. Scores
and the numerical shortfall are unchanged. The owner's exact retrospective
Gate A acceptance below remains authoritative; this separate audit supplies no
scientific signature. Earlier unexecuted-audit descriptions are dated snapshots.

## Current decision: accepted under retrospective amendment, 12 October 2026

The owner directly approved the exact amendment at `eb45c000` through the
explicit choice **Accept the amended Gate A criterion**. The
[successor decision](phase2/gate_a_acceptance_20261012.md) preserves the literal
answer, immutable proposal identity and scope. Gate A is accepted as a
historically audited linked-procedure EEGNet baseline under a retrospective
process-based criterion, adopted after results were known.

Retained 75.6606% ROC-AUC remains below the published 77.15%. Numerical
equivalence, exact numerical reproduction, an original 2024 runtime match and a
pre-existing tolerance remain unestablished. Published SD and the subject
interval are descriptive. The original stronger acceptance condition is not
claimed to have passed; it has been explicitly amended.

Checkpoint-cohort independence and final freeze are not accepted. No model
budget or original-case reset follows. The corrected record audit has no passing
receipt; approval relies on dated evidence in the exact proposal. The historical
unsigned status and acceptance condition below retain their earlier date and
are superseded only within this amended scope.

**Status: not signed off — protocol-matched grid complete; acceptance decision outstanding.**

On 2026-08-30, the user explicitly directed the build to continue to the next
milestone despite this unsigned gate. Downstream work is therefore exploratory
and does not retroactively change the Gate A result.

Note (4 October 2026): the Phase II engineering chain completed on source
`62536382…` (guarded quality pass with published pointer, environment pin,
controls 45/36, raw verification, and one accepted engineering cell from the
first real Cho case) is engineering validation only. It neither signs this
gate nor changes its evidence; the acceptance decision remains the owner's.

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
| Protocol-matched MOABB seed 42 | 75.66% mean ROC-AUC, 90 anchor fits | Descriptive comparison only |
| Protocol-matched repeat seeds 11/23/37/53 | 75.02% subject mean; 95% interval 59.04–91.00% | Descriptive comparison only |

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
preprocessing, split, training and dependency behavior was checked before the
separate matching grid was launched; see `docs/moabb_reference_reproduction.md`.

## Completed local reproduction and remaining acceptance decision

The separate grid now contains all 450 declared fits: nine subjects, two sessions,
five folds, published seed 42 and repeat seeds 11/23/37/53. Its record audit found
450 valid fits, no missing/invalid/unexpected units or locks, with snapshot
`196b419bf2f15c02fd55b9046fd78260605e2be869e3695bb09196616921427e`.
The independent raw-input audit reconstructed every saved fit and found zero
mismatches. Earlier diagnostics and the frozen cross-subject benchmark remain
unchanged.

The published seed comparison is 75.6606% versus 77.15%, a difference of −1.4894
percentage points. The published 19.33-point SD is descriptive, not an acceptance
band, and the exact original 2024 environment is not established by the later
linked implementation. Final sign-off therefore still needs an explicit,
scientifically defensible acceptance decision; no tolerance has been inferred,
invented or changed automatically. Gate A remains unsigned.
