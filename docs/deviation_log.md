# Deviation log

## 2026-08-30 — Gate A reference mismatch

The Phase I plan requires a four-seed, nine-subject, within-subject EEGNet result on
BCI Competition IV 2a to reproduce a published MOABB score.

The official MOABB public result table does not publish an EEGNet result for this
dataset. Its four-class `001-2014` table contains classical pipelines only. MOABB
also distinguishes `WithinSession` evaluation from the cross-session protocol used
by this project (train session to evaluation session), and its public issue tracker
states that cross-session benchmark results have not yet been released.

Impact: the benchmark, leakage controls, subject-level aggregation, and run records
can be completed, but Gate A cannot honestly be signed off against the named
reference until a valid published EEGNet number and matching protocol are selected.
No substitute threshold has been invented.

The first completed diagnostic attempt used all four classes and produced 52.37%
mean balanced accuracy across nine subject means (four seeds per subject). The day
plan, however, explicitly introduces Gate A with a two-class run. That four-class
result is retained as a diagnostic and is not treated as the Gate A reproduction.

The second attempt used the documented left-versus-right classes with Profile A and
produced 68.15% mean balanced accuracy (95% subject-level interval 53.24–83.07%).
This remains a cross-session result and does not match MOABB's public
`WithinSession` table. A separate diagnostic now mirrors Braindecode's official
cross-session example preprocessing and training settings.

The reference-aligned diagnostic produced 72.92% mean balanced accuracy across
nine subjects for seed 11. Because this materially improved on Profile A, the exact
configuration was promoted to the full four-seed Gate A attempt.

The full reference-aligned attempt produced 71.72% mean balanced accuracy across
nine subject means and four seeds (95% subject-level interval 58.28–85.16%).
Subject means ranged from 50.52% to 96.01%, confirming substantial cross-session
heterogeneity rather than a loader failure.

The original plan also conflates three distinct references: MOABB's public
`WithinSession` classical-pipeline table, Braindecode's two-class `CrossSession`
EEGNet example, and later four-class papers that report an EEGNet reproduction.
The latter gives 74.50% ± 15.23 across the same nine subjects, but it is not a
MOABB-published EEGNet score and therefore cannot silently replace the named gate.

An unscaled one-seed four-class diagnostic reached only 47.96%, with several models
stopping near chance. Because Profile A's microvolt-scaled four-class training did
not show that failure, a unit-scaled reference diagnostic was added before changing
any architecture parameter.

Microvolt scaling did not materially alter the broadband four-class result
(47.88%). The next diagnostic therefore changes only the band from 4–100 Hz to the
4–38 Hz setting used in Braindecode's official four-class BCIC IV-2a workflow.

The 4–38 Hz diagnostic reached 43.17%, so narrowing the band alone did not resolve
training. Common-average reference was therefore isolated next on two subjects
before any all-subject rerun.

Common-average reference recovered the two-subject diagnostic to 74.65% for A01
and 87.85% for A03. The unchanged 4–38 Hz model was therefore promoted to a
nine-subject one-seed run.

The nine-subject common-average run reached 57.91%. Subjects A04–A07 stopped near
epoch 100 while strong subjects trained much longer, so early stopping was isolated
next by forcing those four difficult subjects through all 300 epochs while retaining
best-validation checkpoint selection.

The full-300-epoch diagnostic improved A04 from 42.36% to 54.17% and A07 from
44.79% to 68.06%, while A05 and A06 remained at 35.07% and 32.64%. Substituting
these results into the nine-subject run would raise its mean only to about 61.8%,
so early stopping alone does not explain the reproduction gap.

The cited 74.50% comparison used materially different training settings: 1,000
epochs, batch size 16, learning rate 0.001, and dropout 0.2. A difficult-subject
diagnostic now isolates those published settings before they are promoted to all
nine subjects.

The paper-training diagnostic reached 52.43% across A04–A07. A05 improved to
58.33% and A06 to 50.00%, but A04 reached 47.22% and A07 only 54.17%, far below
the paper's 67.01% and 89.58% for those subjects. The settings therefore were not
promoted to a costly all-nine run. Gate A remains unsigned, and the build stops at
the gate pending an explicit, reproducible reference decision.

The user subsequently directed the build to continue to the next milestone on
2026-08-30. Gate A remains unsigned; all work after this point is explicitly
exploratory until a reproducible reference and acceptance target are approved.

The Week 3 one-second pre-cue negative control completed across all nine subjects
and four seeds. Mean balanced accuracy was 24.86% (95% subject-level interval
24.20–25.51%), effectively equal to four-class chance and below the predefined
35% maximum. The control passed.

## 2026-08-30 — Local execution replaces cloud and team-only tasks

The user selected this RTX 4080 laptop for Phase I. The benchmark therefore records
zero metered instance cost and measured local wall-clock time instead of cloud
instance-hours and billing. Persistent-cloud restart testing, remote result sync,
branch protection, and the five-person pull-request rehearsal cannot be reproduced
inside the supplied non-Git folder. The CPU path on the same laptop passed as a
fallback, but it is not represented as a second physical replay machine.

TUH access and author correspondence were not fabricated. The TUH agreement needs
the user's identity and institution; no accepted agreement or private TUH data is
present. No email was sent to the LaBraM authors. These remain in the external
dependency ledger and do not block public-dataset software validation.

## 2026-08-30 — LaBraM checkpoint parameter count

The official `labram-base.pth` file was downloaded and hash-verified as
`7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`. Direct
pickle loading was not allowlisted because it would weaken the safe-loading rule;
the corresponding Braindecode safetensors conversion is used for execution.

The safely loaded checkpoint contains 5,819,936 parameters, not the plan's
5,822,770. The configured 800-sample model contains 5,817,736 after temporal
position cropping. A real `(2, 22, 800)` forward pass produced finite
`(2, 88, 200)` features and `(2, 4)` logits. The count mismatch is retained rather
than hidden by adding unused parameters.

## 2026-08-30 — Profile A/Profile B cross-check

On the same A01 fold, Profile A reached 56.60% balanced accuracy and Profile B
reached 25.35%; Profile B minus Profile A was -31.25 percentage points. This is a
negative compatibility result. The two profiles are not treated as interchangeable,
and no favourable explanation is inferred from a one-subject diagnostic.

## 2026-08-30 — Ten-shot LoRA stand-in result

The real A09 two-class episode used ten support trials and 278 untouched query
trials. LoRA changed the model output (maximum probability change 0.3627) with
1,032 trainable adapter parameters, satisfying the functional smoke test. Balanced
accuracy decreased from 59.35% to 52.52%; this is recorded as a negative empirical
result, not an adaptation improvement.

## 2026-08-30 — Deterministic baseline seed reuse

FBCSP, tangent-space logistic regression, and Euclidean-aligned tangent-space
logistic regression contain no stochastic fitting step, and the precommitted
earliest-trial support draw is identical across seeds. Each deterministic fold is
therefore computed once; the remaining seed-tagged records reuse those exact
metrics and explicitly set `reused_from_seed`, with zero additional fit/prediction
time. Neural baselines remain independently initialized and trained for all five
seeds.

## 2026-08-30 — MMIDB subject 104 boundary annotation

In addition to the four anomalies named in the plan, S104 contains one T1/T2 cue
too close to a recording boundary to supply the configured one-second baseline
and four-second epoch. The initial import failed closed and wrote no partial
artifact. The dataset loader now removes only motor cues that cannot provide the
full configured window, reports the dropped count, and preserves unrelated
annotations. S104 was rebuilt with one boundary cue dropped and 42 balanced
left/right trials retained. A synthetic regression test fixes this policy.

## 2026-08-30 — Preprocessing and artifact thresholds frozen

After all 170 public subjects were present, the absolute trial peak was audited
label-blind across each complete dataset. The permanent dataset-specific threshold
is the observed 99.9th percentile: 0.00005448345685727081 V for BCI IV 2a,
0.005895795032848071 V for Cho2017, and 0.0009869709666818407 V for MMIDB.

The frozen rule rejects 6/5,184 BCI trials, 11/10,520 Cho trials, and 5/4,917
MMIDB trials. Every subject retains every class. The benchmark loader applies the
threshold before source/target and support/query splitting, records the input and
rejected counts, and invalidates records whose configuration hash predates the
freeze. The values and rule are frozen in `configs/artifact_rejection.toml` and
mirrored in `configs/benchmark.toml`.

## 2026-08-31 — Cho2017 subject 43 plausibility flag

The exploratory Cho2017 benchmark produced unusually high held-out performance
for subject 43: ShallowFBCSPNet seed 11 reached 98.42% balanced accuracy, while
EEGNet reached 98.42–99.47% across the five seeds. This exceeds the plan's
65–78% plausibility-review band and is therefore flagged rather than accepted at
face value.

The initial split audit found no direct query-label use: training contains all
other subjects plus the earliest five trials per target class, while evaluation
uses the remaining 190 balanced target trials (95 per class). The recorded
confusion matrix totals those 190 trials, and support/query indices are disjoint.
The consistency across architectures remains unexplained. Final sign-off requires
the planned aggregate plausibility review plus targeted shuffled-label and
subject-level signal audits; until those are complete, this fold is retained as
an unresolved red-team finding rather than evidence of exceptional performance.

## 2026-08-31 — Equivalence design-power arithmetic correction

The initial normal-approximation utility used a single normal tail, but symmetric
TOST requires both one-sided tests to reject. At zero true difference the joint
power is `max(0, 2*Phi(margin/SE-z(1-alpha))-1)`. Consequently the target-power
quantile in the margin must be `z((1+power)/2)`, not `z(power)`. The former
80%-labelled design had only 60% joint power under its own assumptions.

The implementation and statistical procedure were corrected before the H2 margin
freeze and before any Phase II comparison. A fixed-seed independent simulation
of both confidence bounds verifies 80% joint normal-approximation power. This
does not claim exact t-test power or knowledge of future paired-difference SD;
the plan's baseline subject SD remains an explicitly labelled design proxy.

## 2026-08-31 — Targeted Cho control results and loader limitation

Six fixed-episode training-label-shuffle controls on subject 43 are complete.
EEGNet averages 48.07% and Shallow 51.75% (three seeds each); the descriptive
combined mean is 49.91%. Exact signal hashes found no training/query or
source/target copies. These findings do not establish universal leakage absence.

Inspection of the installed MOABB Cho loader explains the single transition in
saved labels: all left arrays are stacked before all right arrays, with a zero
buffer and a documented noncontinuous-data edge warning. Available trial order
is not established original acquisition chronology, and reconstructed-boundary
filter effects remain a scientific limitation. The frozen pipeline was not
retuned after observing high accuracy. Full interpretation and per-seed numbers
are in `docs/cho_subject43_review.md`.

The independent result auditor is now required by Gate B and the phase status
report. It verifies identity, embedded configuration, confusion arithmetic,
deterministic reuse, and the exact expected grid. Final phase completion also
requires a plausibility-review snapshot matching the exact benchmark records.

## 2026-08-31 — Empirical H2 margin frozen

The full Cho2017 EEGNet source row contains 260 audited records from 52 subjects
and five seeds. Its mean is 0.6569043549268261 and between-subject SD is
0.12820747693920292. The corrected planning formula gives a margin of
0.05202907926797159 (5.202907926797159 percentage points), one-sided alpha 0.05,
and approximate normal-theory design power 0.80 at zero difference.

The machine-written freeze fingerprints every source record and refuses silent
replacement. All subjects were retained, including the subject 43 flag. This is
not a scientific gate sign-off or a claim of guaranteed paired-test power. The
original Full Project Plan's section 4 is absent, so the local amendment is in
`docs/falsification_criteria.md` rather than an invented edit of that source.

## 2026-08-31 — Separate support-fine-tuning baseline

The final plan audit distinguished the frozen benchmark's joint source-plus-
support fitting from the requested source-only fit followed by support-only
fine-tuning. Existing LoRA functionality did not by itself establish the latter
full-model EEGNet baseline. A distinct 45-run, two-class BCI protocol was therefore
implemented and tested, with separate records and an independent result audit.
The main seven-method table and the H2 source freeze were not silently changed.
See `docs/eegnet_support_finetuning.md`; completion is determined by its run audit.

## 2026-08-31 — Local source version control

The supplied folder originally had no Git repository. A local `main` repository
was initialized during the final build audit, using the bundled Git executable.
Only reviewed source, tests, configuration, lockfiles, and project documentation
are staged; EEG data, model weights, experiment outputs, caches, and secrets stay
excluded. Nothing is uploaded or published. The local snapshot author identifies
the assistant, not a fabricated human team member.

Earlier records labelled `no-git-workspace` or `unversioned-workspace` remain
unchanged. They cannot truthfully be relabelled as having run from a later commit.
This local repository does not satisfy remote branch protection, off-machine
backup, or a five-person pull-request rehearsal.
