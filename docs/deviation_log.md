# Deviation log

## 2026-08-30 — Gate A reference mismatch

**Historical entry, corrected on 2026-08-31:** the absence/classical-only claims
below are incorrect against the verified official table. They are retained as
history, not current evidence. See the correction appended at the end of this log
and the current `gate_a_status.md`.

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

The initial committed snapshot is `bf78379b6ec67a6fef3db83d8e3c34f37b35299b`.
Subsequent runs capture the current commit, exact source fingerprint, and dirty
state. This optional, backward-compatible metadata extension does not change the
frozen scientific configuration, existing records, or the H2 source freeze.
Deterministic fit reuse preserves the original fit's identity. Final local
completion also requires lint, type checks, and tests with unchanged source and
verified output logs (`scripts/verify_phase1_quality.py`).

## 2026-08-31 — Integrated native streaming closure

The original-plan audit found that LSL transport and array-based decoder replay
had been tested separately. That did not establish the requested true-rate,
on-screen end-to-end path. A distinct live LSL/native Windows Forms demo now
joins these pieces, hashes received samples, requires every prediction to be
acknowledged by the display, and records failure instead of accepting a closed
or missing UI. The final completion checker now requires a visible rehearsal.

The new demo uses source-only training and zero target support, so its held-out
subject framing is literal. Earlier array demonstrations included target support
and cannot truthfully be described as never seeing any data from that person.
No earlier artifacts were rewritten. The source fingerprint now includes native
PowerShell display code as well as Python, configuration and environment locks.

## 2026-08-31 — Atomic filter-bank caches before the remaining classical sweeps

The restart audit found that the old FBCSP cache accepted an array solely by its
shape and dtype. A process interrupted while filling it could leave a plausible
header and incomplete signal values. New caches are written to unique temporary
files and published atomically, then sealed with input/filter identity and a
content hash. Missing, unsealed, changed-input or corrupted caches are rebuilt.
Interruption and corruption regression tests verify this behavior. The actual
filter operation and frozen training configuration are unchanged; original
completed records remain untouched.

## 2026-08-31 — Complete-cohort copy review

The targeted subject 43 check was extended to every retained trial across all
170 public subjects, reading one artifact at a time. No exact duplicate groups
were found among 20,599 retained trials. The 22 frozen exclusions were unchanged.
The audit normalizes channel order but excludes labels and subject identities
from signal signatures, and verifies the actual numeric subject inventories,
including MMIDB's three-digit file names. Final local completion now requires a
current artifact-hash snapshot, no exact train/query copies, and a plausibility
review tied to that same input snapshot. Near-duplicate, chronology, filtering
and pretraining-overlap limitations remain open; no scientific sign-off follows.

## 2026-08-31 — Temperature-aware operational pauses

The fixed five-second pause after every neural fold is replaced, for subsequently
launched workers, by `configs/runtime_limits.toml`: pause at 80 C and resume at
76 C or below. The local NVIDIA status reported a target temperature of 87 C;
no hardware power, clock, fan, driver or sleep setting was changed. Cold folds
need no artificial delay. An unavailable initial sensor retains the prior
five-second delay; a failed sensor while known-hot or failure to cool within
60 seconds of scheduled pauses stops the batch with completed records intact.

Unit tests cover cool, hot, unavailable, malformed and failed-sensor cases.
This changes operational waiting only, not epochs, labels, seeds, fitting,
preprocessing, benchmark configuration hash or acceptance criteria. Earlier
workers retain their original fixed pauses and code provenance. Fit/prediction
timing reports continue to exclude cooling pauses explicitly.

## 2026-08-31 — Cross-check saved results against independently audited inputs

The plausibility evidence packet now joins every valid saved result to the
independent complete-cohort audit. It checks support/query size, class counts,
and full-dataset input/rejection totals, in addition to the result auditor's
existing arithmetic checks. A changed result hash aborts packet generation;
newly completed folds belong to the next snapshot. Every high two-class
subject/method case is listed with per-seed class recall and an unresolved
disposition. The packet cannot grant final review completion or scientific
clearance automatically, and it does not alter training or frozen records.

## 2026-08-31 — Avoid unused raw-signal copies in cached folds

Ahead of the remaining classical batches, cached FBCSP no longer allocates raw
source/query signal copies that it never passes to the decoder. Cached alignment
also avoids an unused raw source copy before constructing the aligned input.
Split indices, filtering, alignment fitting domains, decoder inputs and frozen
settings are unchanged. A regression test makes any raw-signal indexing fail in
the cached FBCSP path and verifies identical non-timing fold metrics against the
direct path; the existing cached/local alignment parity test remains in place.
Already-running workers and completed records retain their original provenance.

## 2026-08-31 — Final original-plan audit: contract, prompts and local checks

The contract module still carried a v0 label with no dated freeze receipt. The
existing interface is now explicitly recorded as local v1 at 03:45:40 UTC, with
normalized-text hashes of its two interface files and a regression test. This
does not backdate a freeze, team announcement, or the earlier experiment history.

The prompt design note described unimplemented prototypes/masks, and the TCPL
note attributed three uncited objections to a paper. These claims are corrected
against current code and primary-source method sections. The missing Full Project
Plan section 5.2 remains an external source gap. Local variants are differentiated
from exact published LoRA, adapter, input-prompt and key/value-prefix recipes.

The prior prompt smoke classified generator outputs without a transformer.
A distinct synthetic CPU attention smoke now tests both injection modes with
real query token sequences, support-only adaptation, unchanged frozen weights,
and no query-time state updates. No EEG accuracy or TCPL reproduction is claimed.
Final local completion requires this smoke for the current tested source.

Local commit and non-fast-forward merge hooks invoke source-quality checks and
three leakage checks. Negative-control verification now reads individual results,
checks the configured subject/seed grid and configuration, and recomputes subject
means instead of trusting saved pass flags alone. It validates historical
controls; it does not retrain those models on every commit. Local hooks remain
bypassable and do not replace remote required checks or branch protection.

## 2026-08-31 — Bound the extra CSP selection copy

The first Cho FBCSP fold completed in 356.949 seconds of fitting while the laptop
experienced memory pressure. MNE already converts selected epochs to writable,
C-contiguous float64. Future workers now construct that identical float64 array
directly in 32-trial chunks, avoiding a retained full-size float32 selection
(about 1.3 GB for Cho training). Each band selection is released before the next.
MNE's internal rank, covariance and CSP algorithms remain unchanged and can still
require considerable memory. This is not a bounded-memory CSP implementation.
The regression check compares predictions bit-for-bit with the original MNE
float32-selection path. Previously completed records retain their actual source
and timings; neither the scientific configuration nor earlier results is edited.

## 2026-08-31 — Interrupted native worker and isolated runtime probe

The resumed classical queue saved Cho FBCSP subjects 01–04. Its console later
reported a libzmq "Bad file descriptor" error; the worker remained present but
its CPU time stayed at 2,387.25 seconds across checks approximately two minutes
apart, with no subject 05 result. The exact project supervisor, worker and launcher
were verified and terminated using the Windows process-management API. Completed
atomic results and verified filter caches were preserved. The underlying native
communication failure is not diagnosed, and dependency pins were not changed.

`scripts/probe_classical_runtime.py` and its separate configuration perform an
isolated four-BLAS-thread check against two already saved FBCSP folds. Probe
results go outside the benchmark directory, bind the independently verified input
snapshot and reference-record hashes, and require exact equality for every
non-timing metric. Runtime comparisons are historical, not a controlled paired
speed experiment. No model/data setting is changed merely by running this probe.

The four-thread probe matched both reference folds exactly but was slower, so
that setting was not adopted. A separate full-numerical-rank certificate was
then validated against MNE on small full-rank/rank-deficient cases and two full
Cho folds. It bounds the original numerical threshold using a training-only
column subset and chunked norm, retaining MNE's original automatic calculation
whenever inconclusive or when the installed MNE version is not the reviewed
1.12.1. It never unconditionally assumes full rank or infers physical rank.

Both real folds reproduced every original non-timing metric exactly, with fit
times 164.272/171.887 seconds versus historical 356.949/369.696 seconds. The guarded
shortcut is enabled for later workers, with per-record certified/fallback band
counts and the minimum bound ratio checked by the independent auditor. The
scientific configuration hash and completed records are unchanged. Full details,
mathematical assumptions, source link and limitations are in
`docs/csp_runtime_optimization.md`.

## 2026-08-31 — Original-plan pairing and evidence check

The paired TOST helper could silently broadcast one score across multiple
subjects, and accepted nonfinite equivalence margins. Regression tests first
reproduced three mismatched-shape failures and two nonfinite-margin failures.
Input checks now require finite, equally sized one-dimensional subject vectors
and a finite positive margin. Caller identity alignment remains necessary;
shape validation cannot prove matching subject/fold/seed identities. Valid-input
TOST arithmetic, the H2 freeze, preprocessing and benchmark records are unchanged.

The scope checklist now distinguishes the supplied Phase I/II day-by-day files
from the absent Full Project Plan and Team Execution Plan. It also distinguishes
observed file-modification spans from unavailable instrumented download times,
and local resumability from the unconfigured off-machine backup requirement.
None of these historical or external gaps is relabelled as completed.

## 2026-08-31 — Bounded CPU/GPU overlap after the memory-heavy CSP stage

The first three Cho tangent-space fits took 282-297 seconds including prediction,
while the GPU was idle. After verifying more than 10 GiB free system memory and
an idle GPU at 64 C, a separate MMIDB EEGNet batch was limited to ten new fits.
It completed subjects 001-010 for seed 11 under the unchanged scientific config
`434fc4d25a5071a094268ab410c47f79bd92823aacd8e9d06e9f684609aab258`.
All ten records passed the independent arithmetic/provenance and corpus-count
checks. Observed free system memory remained above 8 GiB; GPU temperature was
76 C during a check and 70 C after the bounded batch. The existing 80/76 C cooling
policy and hardware settings were not changed. This is sampled monitoring, not
continuous thermal telemetry or proof of the maximum temperature reached.

The batch's separate stdout/stderr logs are
`runs/compute_logs/20260831T0715420524418Z.mmidb-eegnet-10.*.log`.
Its worker exited before a second bounded batch of the remaining 99 subjects
was started. Concurrent work is restricted to distinct datasets and checked for
existing MMIDB workers; the original queue remains on Cho classical methods.
Do not launch another overlapping worker for the same dataset/method, or let an
auxiliary batch overlap the original queue's later MMIDB stage. Reassess memory,
temperature and queue position before each further bounded launch; stop the
auxiliary work if free system memory falls below 4 GiB. This is not authorization
for unbounded parallel batches. Logs and actual process identities, not a stale
launch receipt, determine whether a batch is still running.

These are genuine planned benchmark fits, not speed-probe results. Their timings
were measured under mixed CPU/GPU load and are not dedicated-machine performance
measurements. No model, split, seed, artifact threshold or acceptance criterion
was tuned. High scores in MMIDB subjects 001, 002 and 007 remain unresolved flags;
their roughly 35 query trials per subject do not support a scientific claim on
the basis of the first seed alone.

## 2026-08-31 — Tangent-thread speedups rejected on real-fold parity

The main queue was deliberately paused after Cho tangent seed 11 subject 15 was
atomically saved. Its 1,848 valid benchmark records were preserved, with snapshot
`642142cc88fa1807eaacfbd7dd117d9a7e9d85d32b5c4098f24c11d627d3253e`.
Three isolated probes extended the existing runtime tool without changing any
production decoder or runtime configuration. All used the frozen benchmark
configuration and independently verified corpus snapshot; probe files are outside
the benchmark tree. Reference subject 01 record SHA-256 is
`e9b3dd307fb50dbcd37c69eb534c843998debaa734bb2d016ad609f8e1f9adb4`.

- Whole-pipeline one-thread probe: fit 49.774 seconds, exact parity failed.
  Artifact `runs/runtime_probe/20260831T082232746942Z/result.json`, SHA-256
  `f3476dfafabb13e4de95cb0c7e545812511439380a41867190778434e73dd6ac`.
- Original 24-thread profiled reference: fit 305.930 seconds, every non-timing
  metric reproduced exactly. Profiling adds overhead, so this is not a production
  timing measurement. Artifact `runs/runtime_probe/20260831T082857261291Z/result.json`,
  SHA-256 `00defb605928a57b9c069c48bbcc41e98e5cc4206ad9c281e9295ff97fd62b5e`.
  The saved call profile attributed 282.976 of 306.909 seconds to 44 eigensolver
  calls; covariance estimation occupied about 11.163 seconds.
- One thread only inside those 44 eigensolver calls, with other BLAS work at 24:
  fit 54.116 seconds, exact parity also failed. Artifact
  `runs/runtime_probe/20260831T084208857781Z/result.json`, SHA-256
  `2a307e0261d26ba03b8232830d8f14ad2f1a53b0e452630a460fe605eaf63174`.

Both faster variants reduced balanced accuracy from 0.5578947368421052 to
0.5526315789473685, with one net fewer correct left-hand trial in the confusion
counts (67 to 66 out of 95); kappa and calibration error also changed. Individual
prediction identities were not saved by the original run, so these counts do
not establish exactly how many individual predictions changed. Each failed
two-subject configuration stopped after subject 01; subject 02 was not tested.
Earlier small synthetic/operation checks had matched but did not generalize to
the full iterative pipeline. Historical timings are not a controlled speed trial.

Neither faster setting was adopted, and no parity tolerance or scientific gate
was relaxed. Original 24-thread execution is retained. The temporary selective
hook exists only within the isolated probe process and restores the original
function after each fold. This investigation is diagnostic evidence, not new
benchmark evidence, and does not clear any high-score flag.

## 2026-08-31 — Put targeted control settings into files

A renewed check of Week 1 Day 3 found that the targeted subject-control script
still accepted experimental seeds directly on the command line. Dataset, subject,
methods and seeds now come from `subject_control_cho43.toml` or
`subject_control_mmidb85.toml`; only the configuration-file path is selected on
the command line. These files codify the already executed grids without changing
their settings. They were added after those diagnostic controls and are not
represented as prior registration or retroactively inserted into old run records.

Configuration validation rejects unknown/missing fields, noncanonical subject
identifiers, unsupported/duplicate methods and invalid/duplicate seeds. Resume
also checks the method and seed inside each saved control rather than trusting
its filename. An existing signal audit that differs from the newly computed
audit is preserved and rejected, not overwritten. New controls record their
control configuration/hash and source provenance; old files keep their actual
historical provenance. Benchmark algorithms, frozen settings and completed
records are unchanged; the active benchmark is not restarted for this change.

## 2026-08-31 — Correct the MOABB EEGNet reference claim

Direct inspection of the official benchmark table confirmed EEGNet_8_2 for
BNCI2014_001. The earlier statement that the reference was unavailable, and the
attribution of a required cross-session protocol to the original day plan, were
incorrect. The plan specifies within-subject work; the implementation selected
cross-session evaluation. No historical web snapshot establishes when the table
changed, and this correction does not imply that the result was newly published.

The published left/right target uses within-session five-fold ROC-AUC, whereas
the existing attempts report cross-session balanced accuracy. Their values cannot
be used to claim reproduction. A matching reference implementation is linked by
MOABB and now requires local investigation, not external provision of a missing
reference. Current status documents are corrected; historical configurations and
result hashes remain unchanged, including their then-recorded reference-status
strings. No benchmark setting, acceptance tolerance, gate approval, or scientific
clearance changes as a consequence of this discovery.
