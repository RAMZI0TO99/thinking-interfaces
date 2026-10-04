# Deviation log

## 2026-10-03 — Private repository publication after research stop

The user requested committing the work, then clarified that `beyond-uncertainty` is a different project and authorized creating a new repository with a chosen name. `RAMZI0TO99/thinking-interfaces` was created private, matching the user's explicit visibility choice. The existing local history and current source, configuration, tests and documentation are packaged without raw/processed data, credentials, weights, caches or run outputs. Local-evidence links remain local; frozen receipts and their recorded document hashes are not rewritten.

Publication checks cover the file inventory, credential patterns, sizes, Git history and staged diff. The command-local commit-hook override prevents the existing hook from starting full Python quality/CI checks without a fresh guarded compute window. The tracked hook is preserved; this exception is not a quality pass. No research validation or experiment is started. TYPE005 remains failed, full current-source QA/Windows remain pending, Gate A and the experiment freeze remain unsigned, and accepted real cases remain zero. The publication commit is attributed using the authenticated GitHub account's no-reply identity, which is not evidence of manual review or gate approval.

## 2026-08-31 — Literal support-seed requirement and CI evidence scope

A complete reread of the unchanged Phase I DOCX confirmed that Week 1 Day 2
assigns the seed a role in choosing earliest support trials. The implemented
splitter instead selects the same first five retained trials per class for all
model seeds. This was already described in the seed-reuse note, but was not
explicitly distinguished from the plan's literal seeded-draw requirement in the
completion matrix. That claim is now qualified, and the user has been asked to
decide whether to retain the fixed-earliest deviation or define a new early pool.
No approval, early-pool size, new split, rerun or change to frozen evidence is
assumed while the current sweep continues.

The same review confirms that the local merge checks freshly assert subject
disjointness but revalidate historical shuffled-label/pre-cue records. They do
not establish current-source training-pipeline control results. The completion
matrix now distinguishes historical evidence from the remaining current-source
control binding/rerun work. Original control scores and provenance are preserved.
See `docs/phase1_protocol_decisions.md` for the exact scope and consequences.

## 2026-08-31 — Qualify and bound the Cho alignment scheduling change

After pausing at saved Cho EA+tangent subject 25, the isolated two-fold process
qualification matched every original non-timing metric exactly. The optional
production scheduler is now restricted to this dataset/method, the reviewed
receipt and reference hashes, and the same NumPy/backend identity. Below the
unchanged 10 GiB startup threshold or on backend mismatch, it uses the original
calculation; active worker calls retain the 4 GiB stop. Other methods and MMIDB
remain unchanged. New operational diagnostics are independently audited and
deterministic copies retain their original measured provenance.

No scientific setting, completed measurement, artifact threshold, subject/seed
selection or gate approval changed. Historical timing differences are not a
controlled speed claim. See `docs/tangent_process_runtime_review.md` for both
qualified folds, exact hashes, paused-record preservation and interpretation.

## 2026-08-31 — Qualify isolated tangent scheduling without adoption

Two full Cho normal-tangent folds reproduced every saved non-timing metric exactly
using a bounded two-process eigensolver candidate while retaining the original
24-thread NumPy operations. The same-process threaded approach had failed with a
native access violation and was rejected. Both investigations are diagnostic only.
See `docs/tangent_process_runtime_review.md` for the persisted qualification,
historical-timing limitations and exact source identity.

The main benchmark paused only after saved EA+tangent subject 21. All 2,114 saved
records were rehashed unchanged before resumption at 13:57:43 UTC. Insufficient
free memory deferred the alignment-enabled qualification without lowering its
10 GiB startup guard. The benchmark resumed with its original calculation; no
production speed-up, frozen-setting change, retroactive provenance, or gate
approval was introduced.

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

Update 2026-08-31: an inert metadata/ZIP audit established exact shape and byte
identity for all 221 retained safe tensors (5,819,936 elements). The original
student dictionary additionally contains a 200-element mask token and
1,646,592-element output layer. This accounts for the original-to-conversion
student difference, not the plan's 5,822,770 count. No pickle was executed, no
allowlist changed, and no implementation/inference parity is inferred.
`docs/checkpoint_correspondence_review.md` records the full tensor accounting,
input hashes, report hash, and unchanged unresolved literal count check.

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

## 2026-08-31 — Later native-runtime interruption and preserved resumption

The long-running main worker exited after saving Cho EA+tangent subject 13 at
12:58:35 UTC. Its log again reports libzmq "Bad file descriptor", followed by
supervisor exit status 1073741845; the exact underlying cause is not established.
The old launcher/supervisor/worker tree was confirmed absent before restarting.
All 2,106 saved records passed arithmetic/configuration auditing and were checked
byte-identical after resumption. The preserved interruption audit is
`runs/compute_logs/interruption_20260831T1303_integrity.json`, SHA-256
`1c6e7da5af5f0ca4f069ebb5f070467e975109ddcb8a0eab3d1d348e47d7727b`.
The original terminal log is
`runs/compute_logs/20260831T1126123805071Z.stderr.log`.

The queue resumed at 13:07:21 UTC from clean `86193812cf487939000c312477af7e82897b548c`
with source fingerprint `125b2e191b42910a46d3567d1db675e769fd01567140bb7c10816d520c3d7aed`.
New log: `runs/compute_logs/20260831T1307219034652Z.stdout.log`.
The benchmark configuration, BLAS thread settings, model operations and saved
results were not changed. Four additional reference fits completed in the memory
window; that separate queue then deferred normally at its 10-GiB startup guard.
See `docs/moabb_reference_reproduction.md` for the five-fit input-audit proof.

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

## 2026-08-31 — Isolate the verified MOABB reference software

The linked reference resolves to commit 507a4cccda9efbd5ef019aceeeeb3d298308ec43,
later than the 2024 paper; it is the currently linked implementation, not proof
of the paper's original dependency lock. Its older NumPy/scikit-learn requirements
are incompatible with the main environment's versions. A separate Python 3.12
environment was installed under runs/moabb_reference/environment from an explicit
configuration and a successful dependency dry-run. All install URLs were restricted
to official package hosting/GitHub source archives and bound to the resolved hashes.
The initial Seaborn version conflict was corrected before installation; no dependency
was downgraded in the main environment, whose package/version snapshot hash remained
unchanged. Installed logical file size was approximately 2.04 GB.

The installation passed dependency consistency, archive identity, nine source-file
hash checks and installed-version verification. Resource readiness was false at
7.20 GiB available memory against the unchanged 10 GiB startup limit; no ML import,
training, or benchmark interruption was performed for this check. The live Cho
benchmark continues on its original loaded source. Environment verification is
not a reproduced score, a leakage control, or a gate sign-off. See the separate
MOABB reference investigation for the evidence and remaining smoke/full-run work.

## 2026-08-31 — Prepare a guarded reference fold smoke

A separate two-epoch, one-fold real-data smoke now uses the upstream Keras EEGNet
and preprocessing directly. A process-local download-path redirect reuses the two
existing MAT files without duplicate downloads or signal changes. The reference's
final-20%-of-training validation split and no-best-weight-restoration behavior are
preserved and explicitly recorded, rather than substituting the project's earlier
cross-session checkpoint convention. Split identities, raw hashes, probabilities,
training history and RunRecord provenance will be retained upon a successful run.

Three new tests verify low-resource deferral, failure before training when the
environment check fails, and rejection of edits that expand the smoke beyond two
epochs/one five-fold split. The first on-laptop call correctly deferred at 6.95 GiB
free memory. No reference model was imported or trained, no numerical smoke result
was produced, and no gate or benchmark record was changed. The running benchmark
keeps priority; the 10 GiB startup guard has not been lowered.

## 2026-08-31 — Specify the complete reference grid before training

The newly verified reference motivates a separate nine-subject, two-session,
five-fold grid. It contains the published model seed 42 plus the four earlier
Gate A seeds as a separately reported extension: 90 anchor fits and 360 repeat
fits. No source benchmark or historical gate record is overwritten. The reference
CV split seed stays 42; model seeds change only the training random state.

Configuration and aggregation tests require the full grid, reject altered
reference settings or a newly inserted acceptance tolerance, and keep confidence
intervals at the nine-subject level. Both between-subject/session SD conventions
are labeled; neither is an acceptance band. These are planning/aggregation tests
only; numerical reference training and independent run-integrity review remain
outstanding. A short pause at the next saved main-benchmark boundary is planned
to test the new reference safely, followed by immediate benchmark resumption.

## 2026-08-31 — Real MOABB reference smoke passed; benchmark resumed

The verified main queue was deliberately paused only after Cho tangent subject 38
was saved. All 1,870 preceding records and the new record remained byte-identical
through the pause. The two-epoch reference smoke first deferred below 10 GiB, then
ran after a fresh memory check passed the unchanged guard. It used subject 1's
first session and produced finite probabilities with ROC-AUC 0.6523809524; fit time
was 2.073 seconds. That is an integration result, not the published-protocol score.

The actual reference input was 144 x 22 x 1,001 native samples and resampled query
input was 29 x 22 x 513. Its inclusive endpoint is retained, not changed to Profile
A's 512. The 92/23/29 optimization/validation/query partition and both raw hashes
were independently checked, and ROC-AUC was recomputed from saved predictions.
Receipt: runs/moabb_reference/smoke/20260831T105139058810Z/result.json.

After rehashing all 1,871 benchmark files, the main queue was resumed at 10:52:23
UTC, reused its completed work and returned to Cho classical fitting. The smoke
does not authorize a gate threshold, replace the complete 300-epoch/four-repeat
evaluation, or change the frozen main benchmark. Full reference execution and
independent record auditing remain outstanding.

## 2026-08-31 — Replace historical-only CI with current-source full controls

The original local checks revalidated historical control records without a source
fingerprint. A separate current-source refresh now preserves all original settings
and cohorts: nine shuffled-development-label fits and 36 pre-cue fits. It passed
at subject-weighted means 48.7654% and 24.8553%, under unchanged 60%/35% limits.
Independent raw/artifact reconstruction matched all 45 recorded inputs and query
targets. Historical records/checkpoints were not overwritten or relabeled.

The local hooks and Phase I status now require a complete verified bundle keyed
to source, configurations, input files and environment. Matching records can be
reused after independent validation; changed contexts fail until refreshed. This
closes the local current-source control evidence gap, not remote branch protection,
Gate A reproduction, the support-seed decision or all-dataset plausibility flags.
See `docs/source_bound_controls_review.md` for immutable evidence identifiers.

The preceding benchmark stopped after Cho EA tangent subject 39 with a native
libzmq bad-file-descriptor error. Its cause remains unresolved. All 2,132 completed
benchmark records audited valid, including byte-identical preservation of all
2,118 earlier snapshotted files. The full control refresh used this existing stop;
no unrelated process was terminated and no scientific benchmark settings changed.

## 2026-08-31 — Retire completed Cho filter cache to preserve disk headroom

After all 1,820 Cho records completed and the worker exited, six generated FBCSP
band arrays were independently checked against their content hashes and removed
from the exact configuration-keyed Cho cache directory. They totaled
8,264,614,656 bytes. Their six original JSON metadata files and the verification
receipt remain. All raw/processed recordings, models and 2,353 completed results
were kept; each result was independently rehashed before and after cleanup.

These are rebuildable temporary arrays, not unique evidence. The original
`FilterBankCSP.filtered_bands_memmap` path can reproduce them from the retained
inputs, filter/version key and metadata. They were not moved to a recovery bin.
Completed methods skip cache preparation, so ordinary resume does not recreate
them. Free disk after removal was 20.497 GiB, leaving room for the MMIDB cache
without reducing the reference runner's 10-GiB disk guard.

Pre-removal inventory: `runs/runtime_probe/cho_cache_retirement_20260831T1637.json`,
SHA-256 `ee125602182066855739e8d8595e63fd946fead73c680e24bf29d3a2d0ae5ec3`.
Post-removal verification:
`runs/runtime_probe/cho_cache_retired_verified_20260831T1638.json`, SHA-256
`5bd7f9211a387e993f4c5403343f95f528cfe50c5aca763ff5ba88a8c678022e`.

## 2026-08-31 — Bounded, alternating unattended compute after another native stop

The MMIDB worker stopped after EEGNet seed 37/subject 037 with the same reported
native libzmq bad-file-descriptor failure and exit code 1073741845. Its cause is
not established. No driver, security-agent, model or data settings were changed.
All 2,390 saved records audited valid, including exact preservation of the earlier
2,353-file Cho-complete snapshot. The reference queue then saved four additional
fits before a separate, explicit low-memory deferral. These are distinct events,
not evidence that memory pressure caused the native failure.

Receipt: `runs/runtime_probe/mmidb_native_interruption_20260831T1719.json`, SHA-256
`a302c27d2981281abd180c5f3ec326f69d1de0636dcdcb8a5606c7436ea49268`.
A subsequent unchanged-protocol `--max-new-runs 20` batch completed normally,
bringing the valid main-grid count to 2,410. Bounded process lifetime is an
operational precaution, not a demonstrated repair of the native failure.

The unattended supervisor now alternates at most 20 missing main-grid records
from one method with one missing full-protocol reference fit. Existing seed order,
deterministic seed-copy semantics, model settings and numerical runners remain
unchanged. It validates both grids before work and after every child, requires
append-only file hashes and positive bounded progress, and refreshes integrity
snapshots. It requires current-source controls and clean, unchanged source.
An exclusive parent lock blocks duplicate supervisors; stale locks are preserved
for explicit process-identity review. Independently launched workers must still be
checked before launching this supervisor.

Before either type of child starts, the supervisor checks the reference's unchanged
10-GiB available-memory and disk floors, waiting up to five minutes in five-second
increments before returning a deferral. The reference retains its own per-epoch
4-GiB stop; this scheduler does not add or claim a new in-epoch main-model monitor.
Each worker has separate timestamped logs. Any child failure stops the supervisor,
without blind retries, source changes, deletion of partial evidence or process
termination. Completing both grids still does not approve either scientific gate.

## 2026-09-01 — Reference startup admission lowered operationally to 8 GiB

The shared queue reached 269/450 valid reference fits before unit 269 returned a
resource deferral. The supervisor measured 10.036 GiB free before launch, but the
child's independent preflight measured 9.621 GiB and stopped before importing the
training stack. The result count and all prior hashes were preserved; no unit lock
or Phase I worker remained.

Successful neighboring reference workers used less than 0.8 GiB observed working
set. A tested command-line operating mode now permits reference admission at 8
GiB, leaving over seven times that measured working set and a 4-GiB margin above
the unchanged 4-GiB per-epoch emergency stop. The 10-GiB disk guard, CPU-only
execution, one-process isolation, numerical dependencies, model settings, seeds,
splits, epochs, output identity and acceptance state are unchanged. Each new
environment receipt records the effective startup threshold. Historical receipts
and records are not edited or relabeled.

This is resource scheduling, not a scientific protocol change or evidence that
resource pressure caused any earlier native error. A nonzero child still stops the
supervisor without an automatic retry.

## 2026-09-01 — Preserve stale locks and detach the verified supervisor

Attached terminal sessions could end while the OS child process had already
exited, leaving lock files whose recorded owners no longer existed. Each incident
was handled by checking the exact supervisor and child PIDs through both process
and CIM views, checking the target record and hashing the associated logs before
moving the stale locks to preserved runtime-probe inventories. No live lock was
deleted and no unrelated process was touched. The native libzmq error remains
unexplained; no driver, security or operating-system setting was changed.

A harmless detached-process probe established the Windows process behavior. The
productive supervisor was then launched once through a hidden one-shot wrapper;
the scientific command, source, inputs, model settings and output identity were
unchanged. Launch receipt:
`runs/runtime_probe/20260901T1811014494137Z.os_detached_supervisor_launch.json`,
SHA-256 `b3220d5d17b82512b4915d2e2efc141a48df91822748ead1dbc27de3029a691a`.

## 2026-09-01 — Exact low-disk cache cleanup

Available disk fell below the unchanged 10-GiB guard after a reference fit had
completed and no compute child remained. The only eligible project-owned target
was the derived MMIDB FBCSP cache under the frozen benchmark configuration: 12
files totaling 3,862,956,102 bytes. Its six array hashes and full file inventory
matched the preserved manifest, every file was exclusively openable and no
remaining task depended on retaining the rebuildable cache. It was moved to an
exact quarantine and permanently removed. Free disk increased from 8.915470 to
12.513153 GiB. Raw inputs, processed source artifacts, weights, source, saved
scientific records, logs and audit evidence were not removed. Receipt:
`runs/runtime_probe/fbcsp_cache_cleanup_executed_20260901T173100Z.json`, SHA-256
`97879f3f8e88dc27319415e8dc4377a9537bd08c400ab6ffe33ad467d1281fbb`.

## 2026-09-01 — Both compute grids and local final audits completed

The shared queue reached 5,950/5,950 valid main records and 450/450 valid separate
MOABB reference fits, then exited naturally with no compute lock or child process.
Its final stdout SHA-256 is
`2b69eb3110b99ae941bc206473277d18d5049e748721e0f8bffcaa593354d930`;
stderr is empty. The main record snapshot is
`ff7076b53efd77569d35b6b4d9460be3505376dd174cd690e22c6dee3cfe461a`.
The reference record snapshot is
`196b419bf2f15c02fd55b9046fd78260605e2be869e3695bb09196616921427e`;
its 450-fit raw-input reconstruction found zero mismatches.

Final inventory, threshold, public-artifact, duplicate, support-adaptation,
record, split and metric checks passed. The 21-row table and diagnostics retained
hashes `34a9fe6c…` and `aa874801…`; all three final figures retained their recorded
hashes and passed visual QA. All 261 plausibility cases remain bound to the final
benchmark/config/artifact snapshots and manually reviewed. The separate BCI audit
also covers all 315 records, 63 subject/method cases and all eight 65–78% band
cases. Unresolved chronology, filtering and control-coverage limitations remain
explicit. Gate A is still unsigned, Gate B cannot be scientifically signed, and
the fixed-earliest versus seeded-support choice still requires user direction.

## 2026-09-05 - Version 2 Phase II execution begins exploratorily

The user requested execution of the revised Phase II plan after receiving both
version 2 documents. The v2 default nested fixed-earliest support policy and
explicit roster/primary comparison are now the working Phase II choices, recorded
in `docs/phase2/decision_register.md`. The maximum 20-per-class support pool is
excluded from a common query set at all shot levels. These new identities do not
change the historical Phase I partitions or records.

Continuation does not sign Gate A or Gate B. Work is labelled exploratory.
Training is deferred while storage fails the unchanged 20 GiB preflight floor;
bounded implementation and one-artifact-at-a-time partition audits proceed.
The frozen H2 margin, Phase I artifacts and original plans are preserved. New
source-bound controls will be required before a checked source commit; old
receipts are not relabelled as evidence for the new code.

## 2026-09-05 - Bounded forward parity while storage remains constrained

The user requested step-by-step continuation on work that can proceed without
more storage. A CPU comparison against pinned official LaBraM forward code
established exact agreement at 119 stages across seven float32 cases, without
changing the encoder. The reference loader bypasses timm registration and
initialization imports only; its explicit scope and preserved forward definitions
are documented in `docs/phase2/forward_parity_review.md`.

A supplementary float32 joint-channel-permutation check fails its unchanged
tolerance. Both implementations agree exactly for each order; a post hoc float64
diagnostic passes. The failure remains visible and the command returns nonzero
for the aggregate checks. No tolerance was increased to turn it into a pass.
Full code validation passes 359 tests and 422 subtests. Source controls, training
and scientific gates remain deferred. The next bounded task is the bottleneck
adapter and state-isolation tests.

## 2026-09-05 - LaBraM adapter step completes

Following the user's instruction to keep going, the next bounded step adds
verified post-block bottleneck adapters and a separate explicit support-only
episode helper. Full-checkpoint synthetic one-shot checks pass with both a frozen
and trainable head, including source/frozen/query invariance and exact episode
reset. Full code validation passes 364 tests and 439 subtests. Exact placement,
engineering settings and evidence are in `docs/phase2/adapter_integration_review.md`.

These checks do not select scientific hyperparameters or imply source-trained
accuracy. No heavy training, source-bound control refresh, or gate signing occurred.
Linear/full/partial parameter-mask and episode-policy checks are next.

## 2026-09-06 - Linear, partial and full tuning step completes

The next user-authorized bounded step verifies 14 depth masks and representative
one-shot support updates on the full safe LaBraM checkpoint. The original encoder
depth behavior is unchanged. A new explicit support helper keeps the existing
head, clones source state and creates fresh SGD state for each episode, with all
modules in evaluation mode. Partial tuning at depth 12 freezes non-block backbone
parameters; full tuning includes them. Invalid/ambiguous policies and hybrid
adapter/LoRA inputs are rejected by the new entry point.

Full lint/types and 369 tests / 467 subtests pass. Exact masks, state/reset/query
checks, source fingerprint and retained logs are documented in
`docs/phase2/tuning_integration_review.md`. The test log's overnight elapsed time
is not treated as a runtime pilot. Training remains below its storage floor;
scientific gates and source-bound controls are not advanced. Support-generated
prompts are the next bounded task, with faithful TCPL kept separate.

## 2026-09-06 - Support-generated LaBraM prompts complete

The user requested the next bounded step. The new same-backbone prompt path
uses class-mean support features to retain signal/label association; the older
independently averaged feature/label prototype is preserved as historical code.
Four tokens enter after position/time assembly with CLS at index zero, and
persist through the original LaBraM blocks. This is not faithful TCPL.

An initial strict support-order check exposed float32 batch-position sensitivity.
Fixed batch-one support feature extraction resolves that check without changing
its tolerance. The observed failure and final scope are recorded in
`docs/phase2/prompt_integration_review.md`. Full-checkpoint conditioning, support
updates, frozen source/context/query state and episode-reset checks pass, as do
lint/types and 375 tests / 476 subtests. No scientific selection, heavy training,
control refresh or gate signing is implied. TCPL reference/architecture
verification is the next bounded task.

## 2026-09-06 - TCPL reference review completes

The next user-authorized bounded step pins the publisher article and algorithm
image and separates reported TCPL settings from missing implementation details.
The review verifies a Cho class mismatch against the original dataset and retains
the previously identified BCI LOSO/ten-fold conflict. Subject-normalization fit
scope remains ambiguous; leakage is not asserted. Current benchmark classes and
support/query rules are unchanged.

No author implementation/checkpoint was verified in the reviewed sources, and
faithful architecture and numerical reproduction remain unverified. Evidence and
the next causal TCN component contract are in
`docs/phase2/tcpl_reference_review.md`. Metadata/hash validation replaces a code
test run for this documentation/config-only step. No heavy training, gate signing
or source-bound control refresh occurred.

## 2026-09-08 - TCPL causal TCN component completes

The next bounded step implements the reviewed four-block TCN dimensions with
explicit local choices for stride, padding, activation ordering, bias and
initialization. Causality is tested with future perturbations and a noncausal
negative control; gradients measure the exact 61-sample receptive field. Residual
paths, effective updates, variable shapes and exact state restoration pass.

Full lint/types and 384 tests / 526 subtests pass. Every pre-existing source,
configuration and test file retains its before-step hash. The reference inventory
is preserved as historical evidence; the component is not author-verified parity.
See `docs/phase2/tcpl_tcn_review.md` for evidence and the next constructor/support
generator step. No heavy training, source-bound control refresh or gate signing
occurred; free disk remains below the 20 GiB training floor.

## 2026-09-08 - TCPL support encoder and generator complete

The next bounded step adds a dedicated TCPL support-conditioning module and a
separate local constructor contract. Width-64 convolution/ReLU trial encoding
feeds a per-episode embedding mean and ten-token generator. No support-label
embedding or independent prompt parameter is introduced. Unreported constructor
choices are explicit local decisions; the original reference inventory and all
pre-existing source/config/test files retain their before-step hashes.

Full lint/types and 392 tests / 554 subtests pass. Tests distinguish encode-then-
mean from raw-signal averaging and verify support order, signal sensitivity,
episode isolation, effective gradients and exact state restoration. See
`docs/phase2/tcpl_prompt_review.md` for evidence. Transformer/readout assembly is
the next step; faithful reproduction, scientific protocol reconciliation, heavy
training and source-bound control refresh remain outstanding.

## 2026-09-08 - Local TCPL model assembly completes

The next bounded step assembles the TCN, support generator, Transformer and
classifier under the recorded local contract. Hooks verify the real token path
and EEG-only readout. Query loss itself reaches support conditioning, and bounded
synthetic updates reach every component group. Fixed-target tests verify input,
weight and prompt preservation, query batching and exact state restoration.

Full lint/types and 400 tests / 582 subtests pass. Existing source/config/tests
are unchanged except the local contract's two implementation statuses and comment;
that narrow change is verified separately. See `docs/phase2/tcpl_model_review.md`
for evidence. This is a local model reconstruction; author parity, protocol
reconciliation, episode-runner integration and scientific source training remain
outstanding. No heavy training, source-bound control refresh or gate signing
occurred.

## 2026-09-08 - TCPL meta-episode and fixed-target helpers complete

The next bounded step implements the explicit TCPL meta-loss, a trainer owning
its source clone and persistent Adam optimizer, and frozen target sessions that
snapshot support prompts before queries. The penalty is a sum over prompt
coordinates counted once per episode, then averaged over episodes. Adam beta/eps
choices are local engineering defaults; no scientific schedule or budget is frozen.

Full lint/types and 410 tests / 604 subtests pass. Tests independently verify loss
aggregation, optimizer ownership/moments/reset, caller preservation, nonfinite
rejection and target/query isolation. All pre-existing source/config/test files
retain their hashes. See `docs/phase2/tcpl_episode_review.md` for evidence.
Audited-manifest enforcement is next; tensor helpers cannot infer trial permissions.
No heavy training, source-bound control refresh, author parity or gate approval
is claimed.

## 2026-09-08 - TCPL audited-manifest binding completes

The next bounded step connects TCPL helpers to reconstructed selection/episode
envelopes and pinned NPZ artifacts. Outer-target and inner-validation subjects
are rejected from source updates. Tensor rows, label order and montage are checked
against the audited catalog, with rehashed tampering rejected before execution.

Full lint/types and 419 tests / 609 subtests pass. A real-data check reconstructed
all nine BCI catalogs/episode records and ran untrained subject-01 inference on
496 common queries with zero training steps. All input/audit hashes remain intact;
historical provenance is not relabeled. This is Profile A identity integration,
not scientific decoding/preprocessing evidence. See `docs/phase2/tcpl_manifest_review.md`.

All pre-existing source/config/test files retain their hashes. Source-episode
scheduling for support-ineligible subjects, scientific preprocessing/selection,
checkpoint provenance and result publication remain outstanding. No heavy
training, scientific gate approval, author parity or control refresh is claimed.


## 2026-09-08 - TCPL checkpoint and prediction publication completes

The next bounded step adds safe tensor checkpoints and immutable engineering
prediction records with actual Git/source, input, method and runtime identities.
Repeat publication recomputes predictions and preserves identical files; conflicting
or rehashed tampered records are rejected. Checkpoints alone are not completion.
An initial Windows concurrent-path comparison failure was traced to equivalent
ordinary/extended path spellings and fixed in comparison normalization only.

Full lint/types and 428 tests / 614 subtests pass. Real BCI checks verified nine
catalogs/episode records, published 496 untrained subject-01 queries and reproduced
the same checkpoint and prediction bytes without changing modification times.
All input/audit hashes and pre-existing source/config/test hashes remain intact.
See `docs/phase2/tcpl_publication_review.md` for evidence and trust boundaries.

Prior training history and reported seed remain unverified; optimizer resume,
scientific evaluation, author parity and preprocessing readiness are not claimed.
The next step is the integrated P2 readiness review and pilot specification.
Free disk is 7.69 GiB; heavy training, gate approval and control refresh remain
deferred.


## 2026-09-08 - Integrated P2 readiness review and pilot specification

The thirteenth bounded step consolidates component evidence against the v2 exit
requirements. P2 remains incomplete and P3 unadmitted. It adds a 59-case timing
pilot draft and cost formula; no runtime, source-fit or scientific score is invented.
The current audit has 168 eligible targets out of 170 input subjects, making the
expanded seven-system grid 23,520 cells plus 6,720 anchor cells. This updates the
planning estimate without changing the original paired plan documents.

All 170 Profile A artifact hashes and both LaBraM checkpoint hashes match their
pinned evidence. E1 remains locally blocked by the compatible-tokenizer and masked
forward/loss dependencies; TCPL author parity is unverified. Only BCI currently
has Profile B subject artifacts in the inspected processed-data directories.
The next bounded package is BCI cross-profile trial and encoder-input binding.

Preflight returns 1 for insufficient disk (7.7 GiB versus 20 GiB); the check-only
control audit returns 1 with 0/45 valid current-source fits. These failures remain
visible. No source/config/test changes, training, control refresh or gate signing
occurred. Existing regression evidence is verified by hash, not rerun. Current
Python reports 3.12.14; earlier numerical receipts used 3.12.13, so future runtime
admission must not inherit numerical verification without checking its environment.
See `docs/phase2/integration_review.md` and `docs/phase2/pilot_specification.md`.


## 2026-09-08 - BCI cross-profile binding and encoder-input checks complete

The fourteenth bounded step binds audited Profile A episode IDs to unchanged
Profile B values through a complete original-trial join. Rejection and the maximum
support pool remain governed by the frozen A audit. The loader verifies fixed BCI
classes/montage, profile shape/sampling/units and pinned configuration/artifact
identities before returning copied arrays; no second scaling or fitted transform
is introduced. Missing, duplicate, relabeled and rehashed inconsistent inputs fail.

All nine subjects at all four shot levels pass independent signal/label comparisons:
36 episode conditions and 4,458 unique common queries. One small safe-checkpoint
CPU encoder forward produces finite features and preserves model/input state.
All 36 input/manifest files and nine episode records remain unchanged. Full lint,
strict types and 437 tests / 640 subtests pass. An initial drift-test mock call-count
error was corrected and recorded; production acceptance criteria were not weakened.

This establishes input binding, not scientific raw-preprocessing reproduction,
accuracy, causal deployment or source-selection readiness. Pre-existing source,
configuration and tests are preserved. See `docs/phase2/profile_binding_review.md`.
The next bounded package is LaBraM adaptation runner integration, starting with
linear/partial/full tuning and subject-role enforcement. Free disk is now 19.56
GiB against the unchanged 20 GiB floor; no heavy training, control refresh or
scientific gate signing occurred.


## 2026-09-08 - LaBraM manifest-bound support tuning completes

The fifteenth bounded step adds an owned-source BCI runner for linear/partial/full
support tuning. It reconstructs selection, enforces fixed outer/inner roles,
binds checked A/B artifacts, and sends support labels only to fresh-episode SGD.
Query labels are returned solely for scoring; altered query labels cannot change
adaptation or predictions. Query-time state mutation and nonfinite logits are
rejected by negative controls. Source-training history is explicitly unverified.

The full checks pass: 445 tests / 660 subtests, lint and strict types. All three
methods pass at all four shot levels on fixtures. Real checks used a pinned
pretrained backbone with random head: three one-step subject-01 adaptations, an
exact linear repeat, and one subject-02 inner-validation adaptation, each predicting
496 common queries. Five bounded support steps occurred on separate copies;
zero source-subject training steps and no accuracy evaluation occurred.

All pre-existing source/config/test files, consumed input/audit files and caller
model state remain unchanged. Evidence is recorded in
`docs/phase2/labram_manifest_review.md`. Next is effective-QKV LoRA manifest runner
integration. Free disk now measures 22.04 GiB, above the unchanged 20 GiB floor;
this snapshot does not admit training before the remaining runner/selection/pilot
requirements are met. No source-control refresh or scientific gate signing occurred.


## 2026-09-08 - Disk readmission passes; control refresh remains RAM-deferred

Following the user's report of freed space, fresh preflight measured about 74.04
GiB free disk and passed. The existing guarded source-bound control command was
attempted without changing code, configurations or historical records. It returned
exit 2 with `training_performed=false`: available RAM at admission was approximately
6.51 GiB against the unchanged 10 GiB startup requirement. No control fit ran.
The 45-fit current-source inventory remains incomplete; the user was asked to
close unused applications before retrying. Evidence is under
`runs/phase2/resource_readmission/20260908T160928Z/`. Source identity is unchanged.


## 2026-09-08 - LoRA manifest integration completes while controls remain deferred

At the user's request, coding continued after the second control-refresh attempt
returned exit 2 before training. The sixteenth step connects seeded effective-QKV
LoRA support adaptation to the existing audited BCI runner. Explicit head policy,
source/RNG isolation and complete common queries are verified for target and inner
validation roles. Both head policies pass a bounded real-data CPU check; four fresh
support steps occurred, with zero source fitting and no accuracy evaluation.

Full checks pass: 452 tests / 692 subtests, lint and strict types. Source identity is
`f4a8501f868511fbaec29c2ede6d228e657b4fdc7f91b5ebdf20222d60a3eefc`.
The prior quality status is preserved in the step evidence; the new quality status
identifies this source. All other pre-existing source/config/test files except the
intended manifest runner retain their hashes. See `docs/phase2/lora_manifest_review.md`.
Adapters are next. The resource-dependent 45-fit refresh, source-fit/selection
work and measured pilot remain pending. No scientific settings or gates were signed.


## 2026-09-08 - Adapter manifest integration completes; controls stay deferred

The seventeenth step connects the existing adapter support loop to the audited BCI
LaBraM runner, using explicit targets, width, seed and head policy. Seven new tests
verify common queries, role enforcement, intended updates, query-label isolation,
seeded reset and failure-state preservation. A misplaced test assertion was fixed;
the initial failed log and final passing evidence are retained.

Full checks pass: 459 tests / 715 subtests, lint and strict types. The bounded real
CPU check passes both head policies, exact repetition and fixed inner validation,
each with 496 common queries. Four fresh support steps occurred, with zero source
fitting and no accuracy evaluation. Source identity is
`6e7d0992848f7c2375dbc3337f5de0aeb703640e9895fe326a66f0b3d7411c21`.
See `docs/phase2/adapter_manifest_review.md` for evidence and remaining limitations.

The original adapter implementation and other pre-existing source/config/tests
apart from the intended manifest runner retain their hashes. The prior quality
status is preserved. Support-generated prompt integration is next. The control
refresh remains deferred at the user's request; no refresh, full experiment or
scientific gate signing occurred.


## 2026-09-08 - Support-generated prompts connected to the audited BCI runner

The eighteenth step adds seeded prompt settings and metadata to the existing
LaBraM manifest runner, reusing the class-conditioned support-prompt implementation.
Seven new tests verify all shots, intended generator/head updates, exact cached
support features, query-label isolation, seeded reset and failure-state preservation.
The full checks pass: 466 tests / 740 subtests, lint and strict types.

Real CPU checks pass both head policies, exact repeat and fixed inner validation,
each covering 496 common queries. Four support steps occurred across fresh copies;
zero source fitting and no accuracy calculation occurred. Source identity is
`527c0c8b0d4cdb575e0f3c359740e199d68a906374aaf8283f587c10713d148b`.
See `docs/phase2/prompt_manifest_review.md` for evidence and limitations.

Only the intended existing runner file changed among pre-existing source/config/
tests. The prompt implementation and historical quality status are preserved.
All six local LaBraM support paths now connect to the BCI runner; source training,
selection, broader dataset coverage and measured-pilot requirements remain open.
Matched anchors are next. The control refresh remains deferred at the user's
request, and no full scientific experiment or gate signing occurred.


## 2026-09-08 - Matched EEGNet and EA-tangent anchors integrated

The nineteenth step adds an independently checked Profile A loader and BCI anchor
runner under fixed outer/inner roles. Trial partitions match the Profile B LaBraM
binding. EEGNet uses fresh support-only SGD with normalization buffers fixed; EA
fits the existing source-plus-support recipe, including support-only target alignment.
Nine new tests cover identity matching, fitting boundaries, state preservation,
invalid inputs and operation without Profile B. Full checks pass: 475 tests / 759
subtests, lint and strict types.

Real CPU checks pass both anchors and both roles, each with four support and 496
query trials. EEGNet repeats exactly. Three EEGNet support steps and two classical
source-plus-support fits occurred; there were zero neural source-training steps
and no accuracy calculation. All input/audit files and caller source/RNG are preserved.
Source identity: `99bebe21cb6553892fe9a41b6acd4ab069e67541394e59b20509e5e340d1304a`.
See `docs/phase2/anchor_manifest_review.md` for fit counts, evidence and limitations.

The new source loader is additive; other existing source/config/tests are unchanged.
The prior quality status is preserved. Next is the source-training/selection contract
and bounded executor. The control refresh remains deferred, and scientific selection,
full experiment admission and gate signing remain incomplete.


## 2026-09-08 - Bounded EEGNet source fitting and source-only selection

Milestone 20 adds an explicit candidate/source-fit contract and a BCI EEGNet
executor. Complete eight-fold inner LOSO uses only source subjects, exact balanced
accuracy aggregation and declared-order tie breaks, followed by a fresh final fit.
Single-fold records remain incomplete. Histories pin sampled trials, losses and
state hashes; engineering evidence is immutable and supports atomic no-clobber writes.

Real two-candidate selection, final fit and repeated first fold passed: 127 small
source steps and 17 support steps, with no outer-target prediction. Full checks
pass: 482 tests / 774 subtests, lint and strict types. Source identity:
`0c0ae1438d8faa5371c0d43edffd50f69604bf2161d154d9554d1dfe223ef955`. Existing source/config/tests and all original
data/audit bytes are preserved; historical quality status is saved. See
`docs/phase2/source_selection_review.md` for evidence and training semantics.

Only the EEGNet BCI source/selection path is integrated. LaBraM and other method
source contracts, broader cohorts, scientific schedules/history validation and
the measured pilot remain open. No general source-history certification, guard
change, control refresh, scientific freeze or gate signing occurred.


## 2026-09-08 - Bounded plain LaBraM source fitting and selection

Milestone 21 adds a BCI selector for linear, partial and full LaBraM source tuning.
Audited Profile B training batches exclude outer and inner subjects. Every fit has
explicit masks, a common seeded head initialization, fresh SGD and recorded trial/
state history. Complete source-only LOSO selects settings within one support method
using exact balanced-accuracy means and declared-order ties, then fits afresh.

Real two-candidate linear selection and separate partial/full diagnostics passed,
including repeat and safe checkpoint reload: 141 bounded source steps, 19 support
steps and zero outer-target predictions. Full lint/types and 490 tests / 794 subtests
pass. Source identity: `c3b08d8556e5dd639f6ba1860faa5faad785020ef6977f7a6b609aa13f9c0004`. Existing
source/config/tests, original artifacts/audits and caller template/RNG are preserved.
Prior quality status is saved. See `docs/phase2/labram_source_review.md` for evidence.

This integrates only plain LaBraM source masks. Learned LoRA/adapter/prompt components
and their preservation through validation are next. Scientific source-history trust,
full environments, broader dataset/method coverage and the pilot remain unfinished.
No guard, method configuration, control refresh, scientific freeze or gate changed.


## 2026-09-08 - Source-trained effective-QKV LoRA retained through validation

Milestone 22 extends the BCI source selector with explicit LoRA candidates and a
trained-LoRA manifest path. Learned A/B weights are continued during support tuning
instead of initialized again. Query inference must preserve tensor state and LoRA
scaling; source and support head policies are independently declared. Architecture
admission uses replacement QKV modules in a copy, avoiding installed Torch's shared
parametrized-class removal behavior that could affect the trained caller.

Two-candidate real source-only selection, final fit, repeat, head-policy diagnostics
and safe structural checkpoint reconstruction passed: 141 source steps, 19 support
steps, zero outer-target predictions. Full checks pass: 497 tests / 810 subtests,
lint and strict types. Source identity: `1354b457030270632fe6bcff3a98142bd7c6ee1692dd128ffd5b713c3cc84649`.
See `docs/phase2/lora_source_review.md` for boundaries and evidence.

Only `adaptation/labram_source.py` changed among pre-existing source/config/tests;
all other implementation, artifact and audit hashes are preserved, as are caller
template/RNG and historical documentation. Prior quality status is saved. Adapters,
prompt generators, scientific history validation and the measured pilot remain open.
No control refresh, guard change, scientific freeze or gate signing occurred.


## 2026-09-09 - Source-trained post-block adapters retained through validation

Milestone 23 adds adapter source candidates and a continuation manifest runner to
the bounded BCI LaBraM path. Learned down/up projections and biases are retained
under explicit source/support head policies. The existing support loop is reused;
adapter identity, dimensions, activation/dropout and frozen state are checked.

Two-candidate real selection, fresh final fit, exact repeat, frozen-head diagnostics
and safe checkpoint reconstruction passed: 141 source steps, 19 support steps and
zero outer-target predictions. Full checks pass: 505 tests / 830 subtests, lint and
strict types. Source identity: `a416fe551ecfd2924d31987619690a3a30b2b02ef154b7872632e8ed35754561`. See
`docs/phase2/adapter_source_review.md` for evidence and engineering limits.

Only `adaptation/labram_source.py` changed among pre-existing source/config/tests.
All other implementation/data/audit hashes, caller template/RNG and historical
documentation prefixes are preserved. Previous quality status is saved. Source-
trained prompts, broader coverage and scientific history/pilot work remain open;
no guard, control refresh, scientific freeze or gate signing changed.


## 2026-09-16 - Source-trained support-prompt generator retained through validation

Milestone 24 adds prompt source candidates and a continuation manifest runner to
the bounded BCI LaBraM path. Source fitting is episodic and class-balanced: each
step draws distinct support/query trials per class from one permitted subject,
conditions the generator on batch-one frozen unprompted support features and
optimizes query cross entropy, preserving generator weights across subjects. The
learned generator is continued during validation support tuning instead of
seeded again; generator structure, activation semantics and frozen classifier
state are checked around inference.

Two-candidate real selection, fresh final fit, exact repeat, frozen-head
diagnostics and safe container checkpoint reconstruction passed: 141 source
steps, 19 support steps and zero outer-target predictions. Full checks pass:
513 tests / 849 subtests, lint and strict types. Source identity:
79de610c49e2e6eab7fc843ddb3f2cf939d4f1a7406195b757602b77bd8c12a7. See
docs/phase2/prompt_source_review.md for evidence and engineering limits.

Only adaptation/labram_source.py changed among pre-existing source/config/tests.
All other implementation/data/audit hashes, caller template/RNG and historical
documentation prefixes are preserved. Previous quality status is saved. Remaining
selection paths, broader coverage and scientific history/pilot work stay open;
no guard, control refresh, scientific freeze or gate signing changed.


## 2026-09-16 - EA-tangent bounded candidate selection completed

Milestone 25 adds the classical EA-tangent selection path. Every candidate is a
fixed classical recipe (regularization, C, iterations, query batch); each of the
eight source-only inner folds refits permitted sources plus the held-out
subject's support through the audited anchor runner and scores exact rational
balanced accuracy over the fixed common queries. Selection declares winning
settings, not weights; there is no seed, final refit or outer-target read.

Two-candidate real selection completed 16 folds with 7,924 common-query
predictions while the outer artifact was unreadable, plus one exact repeated
fold: 17 classical fits, zero outer-target predictions. Full checks pass:
519 tests / 859 subtests, lint and strict types. Source identity:
94c198bd0363e96783f58b279e5143060b668e3f70e10be76b3564ad313eabbb. See
docs/phase2/ea_selection_review.md for evidence and engineering limits.

Process incident, recorded for transparency: the first real-check execution
completed its fits but was correctly rejected by the selector's source-identity
guard because TCPL selection edits were concurrently applied to source files; it
emitted no evidence. The source was restored byte-for-byte to the recorded
baseline (verified against before.json) and the check re-ran against that fixed
source. The invalidated log is preserved under
runs/phase2/ea_selection_checks/20260916_step25/.

The EA selection module/tests are new; no pre-existing source/config file
changed. TCPL source-fit selection, broader dataset coverage and the scientific
run recorder remain open; no guard, control refresh, scientific freeze or gate
signing changed.


## 2026-09-16 - EA-tangent bounded candidate selection completed

Milestone 25 adds the classical EA-tangent selection path. Every candidate is a
fixed classical recipe (regularization, C, iterations, query batch); each of the
eight source-only inner folds refits permitted sources plus the held-out
subject's support through the audited anchor runner and scores exact rational
balanced accuracy over the fixed common queries. Selection declares winning
settings, not weights; there is no seed, final refit or outer-target read.

Two-candidate real selection completed 16 folds with 7,924 common-query
predictions while the outer artifact was unreadable, plus one exact repeated
fold: 17 classical fits, zero outer-target predictions. Full checks pass:
519 tests / 859 subtests, lint and strict types. Source identity:
94c198bd0363e96783f58b279e5143060b668e3f70e10be76b3564ad313eabbb. See
docs/phase2/ea_selection_review.md for evidence and engineering limits.

Process incident, recorded for transparency: the first real-check execution
completed its fits but was correctly rejected by the selector's source-identity
guard because TCPL selection edits were concurrently applied to source files; it
emitted no evidence. The source was restored byte-for-byte to the recorded
baseline (verified against before.json) and the check re-ran against that fixed
source. The invalidated log is preserved under
runs/phase2/ea_selection_checks/20260916_step25/.

The EA selection module/tests are new; no pre-existing source/config file
changed. TCPL source-fit selection, broader dataset coverage and the scientific
run recorder remain open; no guard, control refresh, scientific freeze or gate
signing changed.


## 2026-09-16 - Processed-artifact corruption incident and byte-identical recovery

During the first EA-tangent real-check execution (already rejected by the
source-identity guard for concurrent source edits), the script's
outer-target-unreadable discriminator left data/processed/bci_iv_2a/profile_a/
subject_01.npz as its 31-byte placeholder because the restore ran only after a
successful selection. The subsequent re-run failed immediately on the truncated
file. The artifact was regenerated from the untouched raw MOABB sources through
the unchanged Phase I Profile A pipeline and verified byte-identical to the
pinned catalog hash (e95fa5611cf27d9fb121f99f924a2b5150d61e999c1094153346727d343c)
before replacement; no other data file was touched. The check script now
restores the artifact in a finally block, and the recovery script is preserved
under runs/phase2/ea_selection_checks/20260916_step25/. Raw data, all other
Profile A/B artifacts and every audit record remained intact throughout.


## 2026-09-16 - Quality-command timeout ceiling raised from 600 to 1800 seconds

The regression suite passed 575 seconds at milestone 24 (513 tests) and the
milestone-25 EA-tangent tests add about a minute, so the full suite now exceeds
scripts/verify_phase1_quality.py's hung-command timeout of 600 seconds and the
quality bundle fails with exit -1 despite all tests passing. The timeout is a
guard against hung commands, not a cap on suite growth, so it was raised to
1800 seconds for every quality command. No check, tolerance, threshold or
comparison was weakened; the failing run is preserved under
runs/quality/20260916T185649410842Z/. This changes
scripts/verify_phase1_quality.py, so milestone-25 evidence was re-run against
source identity 4770763f81a568a159a9499d637c7f0e54194f478128f7b3ef7c5b0e25dc284d
(the EA module/tests remain unchanged); the earlier claim that no pre-existing
source file changed this milestone is corrected by this entry.


## 2026-09-16 - TCPL bounded source-fit selection completed

Milestone 26 adds the TCPL source-selection path. Every fold owns a fresh trainer
from the pinned caller template, draws class-balanced one-plus-one-shot episodes
from each permitted source subject's retained Profile A trials (eight trials per
step, exact IDs recorded), and validates through the audited manifest runner with
the fitted trainer admitted directly. Dropout draws from a per-fold isolated
seeded RNG, so fits repeat exactly. Selection ranks exact rational balanced
accuracy over the fixed common queries with declared-order tie-breaks; the
winner gets a fresh eight-source fit whose runner is returned under its declared
roles.

A first design trained through the manifest runner's full-episode source_step at
maximum shots; on real data that single attention/activation footprint requested
about 4.3 GB and the bounded CPU check died. Full-query-pool episodic training is
not a bounded CPU workload; the selector was redesigned to the class-stratified
bounded episodes above, and the manifest runner gained an explicit owned-trainer
admission (plus optional trainer optimizer settings and a source-state digest
property). The failed log is preserved under
runs/phase2/tcpl_source_checks/20260916_step26/.

Real checks passed two candidates / 16 inner folds, a fresh final fit and an
exact repeated fold: 127 Adam steps over eight-trial episodes, 7,924 common-query
predictions, zero outer-target predictions. Full checks pass: 527 tests / 873
subtests, lint and strict types. Source identity: 59eda9438085b6533a8d6aa1431736ff5c1e3716b5660633911768b1ccc4ce8c. See
docs/phase2/tcpl_source_review.md for evidence and engineering limits.

The TCPL selector/tests are new; adaptation/tcpl_manifest.py changed additively
(its prior defaults and behavior are unchanged and its existing tests pass
unmodified). With EA-tangent and TCPL complete, every method family in the
bounded roster now has a selection path. Broader dataset coverage, the scientific
run/history recorder and the measured P3 pilot remain open; no guard, control
refresh, scientific freeze or gate signing changed.


## 2026-09-17 - Scientific run recorder foundation completed

Milestone 27 adds evaluation/phase2_runner.py: deterministic pilot case
manifests, atomic case claims with a single linked retry, immutable failure
records, and no-clobber publication of evaluation_cell envelopes whose metrics
must cite selection evidence and match the exact rational mean class recall of
their confusion matrix. The recorder executes no method, reads no target data
and publishes nothing without a matched selection digest; it is the prerequisite
for the pilot executor, not its authorization.

The real-identity check enumerated the pilot specification's full matrix from
the saved audits: 177 deterministic cases (54 measurable BCI main-matrix cases;
123 Cho/MMIDB cases blocked on missing Profile B inputs, grounded in directory
checks). The claim lifecycle was exercised end-to-end and completion accounting
derived 0 measured / 1 failed / 176 pending from immutable records. Zero
scientific cells and zero outer-target predictions. Full checks pass: 535 tests
/ 899 subtests, lint and strict types. Source identity: e85c32ae66ff358e1cb97ba255cf2431fe398d41f9d3e3863e4b72a1129068a9. See
docs/phase2/runner_review.md for the contract and evidence.

The runner module/tests are new; no pre-existing source/config/test file
changed. The pilot executor, compute admission and the scientific freeze remain
open; no guard, control refresh, gate or method configuration changed.


## 2026-09-17 - Pilot target-case executor completed

Milestone 28 adds evaluation/phase2_pilot.py: fail-closed compute admission
(explicit operator decision plus unchanged disk/GPU/RAM machine guards, with
the pilot specification's ten-minute probe and two-hour session caps), method
adapters for the full nine-method roster, and a target-case executor that
verifies the supplied cell identity against the live source, Git identity,
environment and audited episode before claiming, predicts the outer target
through the existing audited runners, records failures immutably and publishes
the evaluation cell with staged timings through the run recorder.

Focused checks passed 6 tests / 8 subtests including a complete published cell
with recomputable exact-rational metrics and every pre-claim refusal. The
real-machine check took a live admission snapshot, digested nine explicit
method configurations, enumerated the 54 measurable BCI pilot cases and
verified the unadmitted executor refuses before any claim or prediction: zero
claims, zero cells, zero outer-target predictions. Full checks pass: 541 tests
/ 907 subtests, lint and strict types. Source identity: 4b202213194c710e2b1ce8cd17dded7665b015566e279c110e6776a4c538dbba. See
docs/phase2/pilot_executor_review.md for the contract and evidence.

The executor module/tests are new; no pre-existing source/config/test file
changed. The bounded engineering track is complete end to end; the measured
pilot now waits on the D01-D06 decisions, operator compute admission, the
scientific freeze, Cho/MMIDB Profile B preparation and the RAM-deferred
control refresh. No gate or guard changed.


## 2026-09-17 - Cho2017 Profile B preparation completed

Milestone 29 gives the primary E2 dataset encoder-ready inputs. The shared
Profile B pipeline gained a refactored run collector (BCI behavior unchanged)
and a Cho2017 subject function over the pinned local GIGADB raw files, plus a
bounded preprocessing script with explicit roster guards. Full-cohort
generation would push free disk below the unchanged 20 GiB floor, so only the
pilot's two Cho subjects (development target subject_01, inner fold
subject_02, about 76 MB) were generated; the audit verified per-trial label,
session, run and montage correspondence with the untouched Profile A
artifacts, finite (200, 64, 800) signals at 200 Hz, matching manifests and
byte-stable re-reads. Focused checks passed 5 tests including a new offline
synthetic-raw collector test. Full checks pass: 542 tests / 907 subtests, lint
and strict types. Source identity: 3733247558ab82063a0e6af00a2b270dd057ef56828a79de954bd863934975f1.
See docs/phase2/cho_profile_b_review.md for evidence and limits.

data/profile_b.py changed by the behavior-preserving refactor plus the new Cho
function; tests/test_profile_b.py gained one test; the preprocessing script is
new. The Cho cross-profile episode binding remains the next milestone; the
remaining fifty subjects wait for freed disk. No guard, control refresh,
scientific freeze or gate changed.


## 2026-09-17 - Cho2017 cross-profile episode binding completed

Milestone 30 binds the audited Cho2017 Profile A episodes to the generated
Profile B encoder inputs. The new loader mirrors the verified BCI contract
with three declared differences: Cho Profile A identity is the audited catalog
hash rather than sidecar manifests, the guards pin the Cho2017 two-class
52-subject roster, and the internal artifact reader and manifest checker are
parameterized by montage and classes with BCI callers unchanged. Saved episode
envelopes verify against reconstructed partitions; A/B trials join by
session/run/index with equal labels; pinned hashes, preprocessing digests and
byte-stability are enforced before and after tensor loading.

Focused checks passed 4 new tests / 7 subtests (13 tests / 33 subtests with
the BCI regression). The real check bound the pilot development target
subject_01 at all four shot levels: 200 retained trials, finite
(2*shots, 64, 800) float32 support arrays, the fixed 160-trial common query
pool matching the pilot specification, byte-exact repeats and unchanged input
hashes; all 64 channels map one-to-one into LaBraM's montage (maximum index
87). Full checks pass: 546 tests / 914 subtests, lint and strict types.
Source identity: a01d74b7c1c55ddb64cd0611b8c07ba8bf7f4e569450b56a4fcb369c0e2d1188.
See docs/phase2/cho_binding_review.md for evidence and limits.

evaluation/phase2_profile_binding.py changed by the parameterization plus the
Cho section; tests/test_phase2_cho_binding.py is new. Next is generalizing the
manifest runners beyond the fixed nine-subject BCI cohort, then the remaining
fifty Cho subjects once disk is freed. No guard, control refresh, scientific
freeze or gate changed.


## 2026-09-17 - LaBraM runners and selector generalized beyond the BCI cohort

Milestone 31 removes the fixed nine-subject BCI assumption from the primary
comparison path. Admission in the tuning manifest runner, the three trained
runners and the source selector now derives the complete subject roster,
classes and montage from the protocol configuration; episode loading
dispatches on the pinned asset inventory (BCI three-digest, Cho two-digest);
class counts, confusion sizes, exact-rational scores and gradient-step
admission come from the actual cohort and logits instead of literals.
BCIProfileAssets moved to the binding module with ChoProfileAssets beside it.

Focused checks passed 4 tests on a synthetic three-subject 64-channel
two-class Cho world covering the tuning runner, a complete selection, the
trained prompt runner and refusal paths; every unchanged BCI suite passes
unmodified. The real check ran the generalized admission over the full BCI
world with the safe checkpoint (496 four-class queries) and confirmed the
real partial two-subject Cho cohort fails closed. Full checks pass: 550 tests
/ 914 subtests, lint and strict types. Source identity:
e2b0dfdf3413615b07f629ff1ae6799ff9385286753cf0d69e1231467dd3a91c. See
docs/phase2/runner_generalization_review.md for evidence and limits.

Seven pre-existing files changed (six substantive, one import-only) and one
test file is new. The anchors and TCPL paths remain BCI-bound by design; the
next prerequisite is the remaining fifty Cho Profile B subjects, which needs
freed disk. No guard, control refresh, scientific freeze or gate changed.


## 2026-09-17 - Full Cho2017 cohort and first real Cho engineering folds

Milestone 32 completes the primary dataset's data preparation. The remaining
fifty Cho2017 Profile B subjects were generated with the unchanged
milestone-29 pipeline under the user's explicit disk authorization (1.9 GiB
consumed; 23 GiB remained free). All 52 subjects (10,520 trials, shapes 200
or 240 by 64 by 800) passed the preparation audit against untouched Profile
A artifacts. The primary E2 machinery then ran on real Cho data for the first
time: bounded linear and source-trained LoRA diagnostic folds over fifty
permitted source subjects with inner-validation predictions of all 159 fixed
common queries of subject_02, exact trial/state histories and zero
outer-target reads. Both folds scored 1/2 - chance under one-step
engineering fits, carrying no performance meaning. Complete 51-fold
selections remain unexecuted: the 256-step engineering ceiling permits
diagnostic folds only, and complete selections are separately charged
scientific work awaiting admission.

No source/config/test file changed this milestone; the exact-source suite
re-passed at 550 tests / 914 subtests with lint and strict types. Source
identity unchanged: e2b0dfdf3413615b07f629ff1ae6799ff9385286753cf0d69e1231467dd3a91c.
See docs/phase2/cho_cohort_review.md for evidence. The pilot's Cho cases are
now data-complete; the D01-D06 decisions, operator compute admission, the
scientific freeze and the RAM-deferred control refresh remain user-gated.


## 2026-09-17 - Anchors and TCPL selectors beyond the BCI cohort

Milestone 33 completes cohort generalization. A new Cho2017 Profile A loader
pins identity by the audited catalog hash (no sidecar manifests) and enforces
the 64-channel contract; the anchor runner admits any declared cohort,
requires manifests only where sidecars exist, accepts EEGNet matching the
declared montage/head and derives probability shapes from the catalog; the
EEGNet, EA-tangent and TCPL selectors dispatch loading by dataset, build
models from the declared dimensions and derive class counts from predictions.

Focused checks passed 3 new tests (25 tests / 44 subtests with unchanged
regressions). The real check ran both anchors on the full Cho cohort: an
EA-tangent fold over fifty permitted sources and an EEGNet fold with fifty
source steps, each predicting all 159 fixed common queries of subject_02
(scores 0.505 and 0.473 - near chance under one-step engineering fits, no
performance meaning) with zero outer-target reads. Full checks pass: 553
tests / 914 subtests, lint and strict types. Source identity: fe9e513a818ccfd7a43a4ddc2d67fcda05e3010db8458e297d510512a60d36e0.
See docs/phase2/anchor_cho_review.md for evidence and limits.

Five pre-existing files changed and two are new. The pilot's primary Cho
tranche (linear, LoRA, EEGNet, EA-tangent) now runs end-to-end engineering
on real data; MMIDB remains unstarted and a real Cho TCPL fold is optional
bounded future work. No guard, control refresh, scientific freeze or gate
changed.


## 2026-09-17 - Roster completion: remaining real Cho folds

Milestone 34 completes real-data coverage of the adopted roster. LaBraM full
tuning (5,818,138 trainable parameters) and the local TCPL reconstruction
each ran a bounded real Cho fold over fifty permitted source subjects with
159-query inner-validation predictions and zero outer-target reads; both
scored exactly chance under one-step engineering fits, carrying no
performance meaning. One admission fix landed: the TCPL selector now accepts
Cho Profile A catalog-hash identity without sidecar manifests and refuses a
nonempty inventory. The first check execution was invalidated by that
concurrent fix (preserved under superseded_tcpl_fix/); a window full-suite
run also crashed with a transient Windows stack overflow at 23% (identical
source had passed earlier) and the clean re-run is the evidence of record.

Full checks pass: 553 tests / 914 subtests, lint and strict types. Source
identity: 504724f716024594a4a5ed22a7dcb2d9178e5cb83c530141acbdcac3fe3d9264.
See docs/phase2/roster_cho_review.md. Only adaptation/tcpl_source.py changed;
no new source files. Every roster method family has now run bounded real
folds on both the BCI and Cho2017 cohorts. The MMIDB dataset remains the only
bounded gap; the D01-D06 decisions, operator compute admission, the scientific
freeze and the RAM-deferred control refresh remain user-gated.


## 2026-09-17 - Roster completion: remaining real Cho folds

Milestone 34 completes real-data coverage of the adopted roster. LaBraM full
tuning (5,818,138 trainable parameters) and the local TCPL reconstruction
each ran a bounded real Cho fold over fifty permitted source subjects with
159-query inner-validation predictions and zero outer-target reads; both
scored exactly chance under one-step engineering fits, carrying no
performance meaning. One admission fix landed: the TCPL selector now accepts
Cho Profile A catalog-hash identity without sidecar manifests and refuses a
nonempty inventory. The first check execution was invalidated by that
concurrent fix (preserved under superseded_tcpl_fix/); a window full-suite
run also crashed with a transient Windows stack overflow at 23% (identical
source had passed earlier) and the clean re-run is the evidence of record.

Full checks pass: 553 tests / 914 subtests, lint and strict types. Source
identity: 504724f716024594a4a5ed22a7dcb2d9178e5cb83c530141acbdcac3fe3d9264.
See docs/phase2/roster_cho_review.md. Only adaptation/tcpl_source.py changed;
no new source files. Every roster method family has now run bounded real
folds on both the BCI and Cho2017 cohorts. The MMIDB dataset remains the only
bounded gap; the D01-D06 decisions, operator compute admission, the scientific
freeze and the RAM-deferred control refresh remain user-gated.


## 2026-09-17 - MMIDB Profile B preparation completed

Milestone 35 data-completes the third audited dataset. All 109 MMIDB subjects
were generated from the pinned local PhysioNet EDF runs (892 MB; 21 GiB free
afterward) and audited against untouched Profile A artifacts: exact per-trial
label, session, run and index correspondence; canonical 64-channel montages;
finite (trials, 64, 800) signals at 200 Hz; matching manifests; and pinned
Profile A hashes. Subjects 079 and 100 are recorded as the audited-ineligible
pair (no episode records; artifacts remain source-usable). The cohort totals
4,917 trials with a fixed-pool query ceiling of 556.

Two engineering findings: subjects 88 onward are native 128 Hz, below the
Profile B bandpass Nyquist, so a documented upsample-before-filter policy was
adopted (order differs from BCI/Cho; no information above the native Nyquist
is added); and the A/B join-key conventions required Profile A's session/run
naming. Two intermediate generation bugs (a run-grouping collapse and
mismatched naming) were caught by the audit's join checks and fixed before
finalization; the failed attempts remain in the generation logs.

Full checks pass: 553 tests / 914 subtests, lint and strict types. Source
identity: 704d838597fdb01842ea9fdcf3be7aae709216155dad8be3cd57bdcd06bfdbb4.
See docs/phase2/mmidb_cohort_review.md. data/profile_b.py changed and the
preprocessing script is new. The MMIDB binding is optional low-priority future
work; the D01-D06 decisions, operator compute admission, the scientific freeze
and the RAM-deferred control refresh remain user-gated.


## 2026-09-17 - MMIDB Profile B preparation completed

Milestone 35 data-completes the third audited dataset. All 109 MMIDB subjects
were generated from the pinned local PhysioNet EDF runs (892 MB; 21 GiB free
afterward) and audited against untouched Profile A artifacts: exact per-trial
label, session, run and index correspondence; canonical 64-channel montages;
finite (trials, 64, 800) signals at 200 Hz; matching manifests; and pinned
Profile A hashes. Subjects 079 and 100 are recorded as the audited-ineligible
pair (no episode records; artifacts remain source-usable). The cohort totals
4,917 trials with a fixed-pool query ceiling of 556.

Two engineering findings: subjects 88 onward are native 128 Hz, below the
Profile B bandpass Nyquist, so a documented upsample-before-filter policy was
adopted (order differs from BCI/Cho; no information above the native Nyquist
is added); and the A/B join-key conventions required Profile A's session/run
naming. Two intermediate generation bugs (a run-grouping collapse and
mismatched naming) were caught by the audit's join checks and fixed before
finalization; the failed attempts remain in the generation logs.

Full checks pass: 553 tests / 914 subtests, lint and strict types. Source
identity: 704d838597fdb01842ea9fdcf3be7aae709216155dad8be3cd57bdcd06bfdbb4.
See docs/phase2/mmidb_cohort_review.md. data/profile_b.py changed and the
preprocessing script is new. The MMIDB binding is optional low-priority future
work; the D01-D06 decisions, operator compute admission, the scientific freeze
and the RAM-deferred control refresh remain user-gated.


## 2026-09-19 - MMIDB cross-profile binding completed

Milestone 36 completes dataset readiness end to end. The new MMIDB loader
mirrors the Cho contract with MMIDB's own T9/T10 montage, catalog-hash
identity, the recorded upsample-before-filter policy in its binding schema,
and hard refusal of the audited-ineligible subjects 079 and 100. The dataset
tables now include mmidb, admitting the full roster through the cohort-generic
runners. Focused checks passed 5 new tests / 7 subtests (11 / 15 with the
Cho and BCI regressions); the real check bound the pilot development target
and inner fold at all four shot levels with byte-exact repeats, unchanged
input hashes and ineligible-subject refusals; all 64 channels map into
LaBraM's montage (maximum index 87).

One testability fix landed in the pilot executor: machine_snapshot gained an
injectable free_host_ram_gib parameter mirroring disk and GPU after a full
suite flipped ten pilot tests by dipping below the 4 GiB live-RAM floor
mid-run; real admission checks still read live values. Full checks pass:
558 tests / 921 subtests, lint and strict types. Source identity:
74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9. See
docs/phase2/mmidb_binding_review.md. Three pre-existing files changed and the
MMIDB binding test file is new. Every dataset now has generation, audit and
binding end to end; the measured pilot is entirely user-gated.


## 2026-09-19 - Delegated decision resolution recorded

The user instructed: "i want you to analyze the best decisions and make them
for me" and "do not push anything to github or gitlab until i tell you to."
The first instruction delegates execution-decision analysis; it is recorded
here as a deviation and is explicitly NOT converted into Gate A acceptance,
scientific freeze, or operator compute admission. The second instruction is a
standing no-push rule; nothing has been pushed and the tree remains
uncommitted (the RAM-deferred control refresh still gates commits).

Adopted choices (full analysis in docs/phase2/decision_analysis.md): Gate A
stays exploratory - any acceptance band adopted now would be post-hoc against
the observed 75.66 vs 77.15 reproduction gap; fixed-earliest support stays;
the structural roster draft freeze is confirmed while budgets stay pending
the measured pilot; TUAB/TUEV and E1 remain blocked unchanged; and the
measured pilot is refused by the machine guard today (17.59 GiB free against
the unchanged 20 GiB floor, measured live; GPU passes). No source/config/test
file changed for this record.


## 2026-09-19 - User admits the measured pilot below the disk floor

Following the milestone-37 decision record, the user instructed: "ok do it
and then keep moving." In context this authorizes the two recorded owner
actions: pilot compute admission, and below-floor disk operation as a
documented deviation (17.59 GiB free against the unchanged 20 GiB floor,
live-measured). The guard itself is NOT weakened: every admission record
carries the failing storage snapshot and this deviation reference. The
operating mode is the "separately measured, tested operating mode" the
handoff allows: CPU-only bounded pilot execution with small record writes
(under 100 MB per session), no cohort reduction, no deletion, and the
session/probe caps unchanged (10 minutes per probe, two hours for the first
session). Provisional pilot weights produce engineering measurement records
only; no scientific cell is published from this session.


## 2026-09-19 - First measured pilot session executed

Following the recorded pilot admission and below-floor authorization, the
first measured pilot session ran all five primary-tranche methods
(labram_linear, labram_full, labram_lora, eegnet, ea_tangent_lr) on the real
Cho2017 cohort at the primary five-shot configuration with development target
subject_01, model seed 23 and one repetition. Every case was claimed
atomically, measured with per-stage timings, and recorded as an engineering
measurement record; no scientific cell was published (provisional one-step
weights). Case totals: 40.7 s, 47.6 s, 39.4 s, 17.5 s and 248.0 s
respectively - all far inside the ten-minute probe cap, the session well
inside its two-hour cap, each case predicting all 160 fixed common queries.
The admission record carries the honestly failing storage snapshot
(17.59 GiB free); the guard is unchanged. No source file changed; the
exact-source suite re-passed at 558 tests / 921 subtests with lint and
strict types. Source identity unchanged: 74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9.
See docs/phase2/pilot_session_review.md. P3 is now in measured execution
under the documented deviation; repetitions, the remaining 54-case matrix
and the source-cost probes remain, followed by the scientific freeze.


## 2026-09-19 - Pilot repetitions completed for the primary tranche

Milestone 39 completes the pilot specification's repetition requirement for
the primary tranche: two warm-cache repetitions ran after the milestone-38
cold run, giving three measured repetitions per method with median and
maximum reported (never only the fastest). Case-total medians: linear 46.6 s,
full 50.1 s, LoRA 42.1 s, EEGNet 18.2 s, EA-tangent 300.1 s; maxima 54.5 s,
71.8 s, 56.0 s, 21.4 s and 357.9 s. Every repetition claimed atomically and
wrote an immutable engineering record with the honestly failing storage
snapshot in the admission; no scientific cell was published. No source file
changed; the exact-source suite re-passed at 558 tests / 921 subtests with
lint and strict types. Source identity unchanged: 74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9.
See docs/phase2/pilot_repetitions_review.md. The remaining pilot matrix,
source-cost probes and the scientific freeze remain; Gate A stays unsigned
and nothing is committed or pushed.


## 2026-09-19 - Pilot matrix complete on Cho2017: full roster and shot extremes

Milestone 40 completes the pilot's Cho2017 coverage: all nine roster methods
measured at the primary five-shot configuration (TCPL 45.4 s, partial 60.5 s,
adapter 55.7 s, support-prompt 72.1 s joining the five earlier methods), and
the full nine-method matrix at both shot extremes. Eighteen extreme cases
measured cleanly (one-shot 20.9-359.4 s; twenty-shot 20.7-369.0 s), showing
the envelope's most important fact: per-case cost is approximately flat in
shots because the 51-subject source fit dominates and is shot-independent.
Combined with milestone 39: neural methods 39-79 s, TCPL ~46 s, EEGNet
~18-21 s, EA-tangent 248-369 s per case; a full Cho five-shot scientific
tranche extrapolates to roughly 15-25 hours at these bounded settings. Every
case claimed atomically with immutable engineering records and the honestly
failing storage snapshot in the admission; no scientific cell was published.
No source file changed; the exact-source suite re-passed at 558 tests / 921
subtests. Source identity unchanged: 74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9.
See docs/phase2/pilot_matrix_review.md. The BCI/MMIDB targets, throughput
probes and the scientific freeze remain; Gate A stays unsigned and nothing
is committed or pushed.


## 2026-09-19 - Pilot BCI development-target cases completed

Milestone 41 completes the pilot's BCI coverage: all nine roster methods at
both shot extremes on the nine-subject world - 18 measured cases at 4.6-32.5
s each, roughly a third of their Cho counterparts because the eight-source
cohort makes the dominant source-fit stage cheap despite the 496-query pools.
The milestone-40 shot-flatness finding replicates exactly, and EA-tangent
inverts its cost position (second-cheapest at 11 s with seven sources to
refit, versus most expensive at 358 s on Cho's 51) - its cost scales with the
source cohort. Every case claimed atomically with immutable engineering
records and the honestly failing storage snapshot (15.56 GiB at session
start); no scientific cell was published. No source file changed; the
exact-source suite re-passed at 558 tests / 921 subtests. Source identity
unchanged: 74feed107b258b533b5fce964d1562462fc4aa26172a3d144b77ab3ec3c80ae9.
See docs/phase2/pilot_bci_review.md. Only the MMIDB target, the throughput
probes and the scientific freeze remain; Gate A stays unsigned and nothing is
committed or pushed.


## 2026-09-19 - Pilot MMIDB cases and the episode-eligibility finding

Milestone 42 surfaced the pilot's most important structural finding: episode-
bound methods cannot use MMIDB subjects 079/100 as sources because no audited
episodes exist for them and none can exist (insufficient retained trials),
while the audit's selection includes them under the source-cohort policy.
The admission guards correctly refused every workaround (a pruned 107-cohort
fails completeness; the full 109-catalog world fails episode construction).
Resolving this needs an explicit episode-eligible source-cohort policy - an
owner-level scientific-contract decision, per the milestone-37 resolution.
EA-tangent, needing no episodes, measured on the full cohort (125.6 s and
154.1 s at one/twenty shots; cost scaling now measured at three cohort
sizes). Two genuine code gaps were found and fixed: dataset_cohort's
subject-name width (two-digit padding broke MMIDB's three-digit names) and
the LaBraM manifest runner's missing MMIDB asset dispatch; all BCI/Cho
suites pass unmodified and the exact-source bundle re-passed. The eight
episode-bound methods' refusals are recorded as honest failure records with
the exact guard messages. See docs/phase2/pilot_mmidb_review.md. Gate A
stays unsigned; nothing is committed or pushed.


## 2026-09-19 - Source-cost throughput probes completed

Milestone 43 completes the pilot specification's neural source-cost probes:
two warm-up plus three blocks of twenty measured gradient steps per method on
one fixed class-balanced eight-trial audited batch, for all six LaBraM
methods on both Cho2017 and BCI - twelve probes, sixty measured steps each,
all inside the 100-step cap. Median per-step costs: linear 0.221/0.061 s
(Cho/BCI), adapter 0.227/0.062, LoRA 0.263/0.067, partial 0.302/0.082,
full 0.778/0.212, support-prompt 0.839/0.278 - a stable ordering with
component methods clustering at the bottom and full tuning / prompt episodes
at 3-4x, and maxima within ~1.15x of medians. These numbers close the loop
between the measured case envelope and its components: any scientific step
count now costs out by multiplication (e.g. 50 steps x 51 Cho sources:
linear ~9.4 min, LoRA ~11.2, prompt ~35.7 per fit). No source file changed;
the exact-source suite re-passed at 558 tests / 921 subtests. Source
identity unchanged: 37dbc5e91a1581b56d7c59f46112f3939a6403646c32503c6a46f54c7e939d24.
See docs/phase2/source_probes_review.md. The freeze now has every measured
input the specification requires from the pilot; the freeze itself is the
owner's scientific-contract act. Gate A stays unsigned; nothing is committed
or pushed.


## 2026-09-19 - Scientific freeze draft prepared from the measured pilot

Milestone 44 prepares the P3 exit artifact the plan requires: the complete
scientific freeze draft (docs/phase2/scientific_freeze_draft.md) - candidate
counts and budgets for all nine methods at the pilot-measured settings,
selection/stopping rules (complete LOSO, declared-order ties, no early
stopping), the scientific seed set 11/23/37/53/71, failure policy, the 1.25x
retry-adjusted resource envelope, and the expected 1,300-cell primary-tranche
dependency manifest. The milestone-37 deferral reason ("budgets stay pending
the measured pilot") is now gone: every freeze input was measured in
milestones 38-43. The draft is adopted as the working contract under the
user's standing delegation and remains a draft for owner ratification - it
does not sign Gate A, start E2 execution, or modify frozen Phase I records.
The draft flags EA-tangent's classical-refit cost (~350-450 h for the
primary tranche if included) as the single dominant envelope decision. No
source file changed; the exact-source bundle re-passed at 558 tests / 921
subtests. Source identity unchanged: 37dbc5e91a1581b56d7c59f46112f3939a6403646c32503c6a46f54c7e939d24.


## 2026-09-19 - Start-here handoff refreshed for a new agent

Milestone 45 refreshes the designated entry document (PHASE2_START_HERE.md)
for agent continuity: the previous version still described the 2 September
state and would have misled a fresh session. The refreshed handoff states
the one-paragraph position (Phase II engineering and measured pilot
complete, freeze drafted pending ratification), the ordered reading list
(phase2 README, decision register, freeze draft, deviation log), the five
owner-gated pending items it must not do itself, the standing discipline
rules (no push/commit, guards unchanged, 16 GiB free disk noted as below
the floor with the recorded pilot deviation's scope), the milestone working
conventions (baseline/test/quality/finalize receipts; byte-safe doc
writers; pristine-config and write-once evidence rules), and explicit
first actions - including that no bounded engineering work remains to
invent. The old handoff (docs/phase2_agent_handoff.md) is now explicitly
marked historical in the new entry document. No source file changed.


## 2026-09-19 - Freeze draft reconciled; execution-readiness overclaims corrected

Milestone 46 follows the owner's explicit authorization to reconcile the
freeze draft for review ("yes do what you have to and what you see fit").
The prior draft contained BCI fold counts in the Cho contract, counted
260 selections across a 1,300-cell tranche, contradicted its own primary
full-tuning inclusion, and treated pilot settings and incomplete time
estimates as a complete scientific envelope. The original draft and
status documents are preserved byte-for-byte in the new baseline.

Delegated decision deviations, adopted without scientific sign-off:
(1) retain full tuning in the proposed primary tranche, consistent with
the pilot specification and regularization reference; (2) use complete
cohort-derived LOSO, 51 inner folds for Cho; (3) count one selection per
target/method/seed at five shots, 1,300 total, with no unverified reuse;
(4) retain proposed candidate values and make paired source/support SGD
rate scope explicit, while correcting TCPL to no target gradient updates
and four-trial Cho source episodes; (5) replace the unsupported timing
envelope with maximum-stage, full-search proxy accounting and explicitly
unknown missing costs; (6) withdraw the claim that ratification alone
makes current E2 execution ready. See docs/phase2/freeze_reconciliation_review.md.

The real-data check hashes all 52 Cho Profile A artifacts against saved
catalogs and reconstructs all 52 episode and selection envelopes. Explicit
enumeration gives 132,600 candidate/fold evaluations, 106,080 neural inner
fits, 1,040 neural final fits and 26,780 EA fits. Saved timing envelopes
give a no-reuse proxy of 1,893.4 neural hours plus 3,328.0 EA hours after
the 1.25 allowance; this is not a measured complete selection or admitted
budget. The pilot's LaBraM lr was 0.01, unlike the proposed 0.001/0.002.
No decoding score informed any adopted correction.

Read-only source-expression diagnostics expose actual remaining limits:
LaBraM/TCPL request 5,253/5,151 steps for complete Cho selection against
the unchanged 256 ceiling; EEGNet admission requests 136 instead of 5,253,
and EA requests 16 fits instead of 102; LaBraM divides the 51-fold score
sum by 8 (an all-one-half discriminator reports 51/16, not 1/2). Earlier
cohort-generic and immediate-execution claims were too broad. No production
source fix, cap change, private-helper workaround or experimental run is
performed by this milestone. These are verified prerequisites for later
work, not permission to bypass any guard.

The milestone evidence is under
runs/phase2/freeze_reconciliation/20260919_step46/. Finalization checks
unchanged source/config/tests, prior evidence and append-only historical
documentation against the baseline, with the required fresh exact-source
quality bundle. Its receipt records the actual quality result. All owner
decisions remain open; frozen Phase I records and H2 margin are untouched;
the RAM-dependent controls remain deferred. Nothing is committed or pushed.


## 2026-09-19 - Cohort-aware selector arithmetic repaired without raising caps

Milestone 47 follows the owner's "next step" instruction after the
milestone-46 findings. Three production files change: LaBraM uses the
actual inner-fold count for its exact candidate mean; EEGNet uses actual
source/fold counts for single-fold and complete-selection admission,
including a pre-score worst-case final fit; EA counts every actual
candidate/fold fit. New EEGNet/EA evidence names the actual dataset and
all three source-policy labels stop claiming eight sources for Cho.
Fit algorithms, partitions, scientific settings and all ceilings remain
unchanged. Old mislabeled evidence and means are preserved as history.

Delegated decisions, recorded as deviations: repair these actual defects
instead of altering the scientific cohort or budget; correct the related
metadata at its source; preserve 256-step/fit ceilings and every resource
guard; verify refusal before fitting on the real cohort; do not treat
correct arithmetic as scientific execution admission. The owner retains
freeze ratification, EA inclusion, MMIDB policy, Gate A and commit/push.

The new checks fail before the repair (seven failed outcomes, including
metadata subtests; BCI boundary checks pass). After repair, 10 focused
tests / 4 subtests pass. LaBraM means are independently reconstructed from
confusion matrices; anchor admission tests cover exact boundaries,
mixed-candidate worst-case final work, ties, truthful metadata and
unchanged hard-cap rejection. Full quality results are in the finalized
milestone receipt, bound to the changed source.

The separate real-data check rebuilds all 52 Cho Profile A catalogs,
reconstructs audited episodes/selection, uses the safe LaBraM checkpoint
and verifies input/model preservation. Actual admission requests are
LaBraM 5,253, EEGNet 5,253 and EA 102; limits 256/256/101 refuse before
any fitting. There are zero real-data training steps, target predictions
or scientific cells. Full Cho neural selection remains beyond the
unchanged ceiling; no hidden splitting or private-helper bypass is used.

One byte-edit attempt asserted on an incorrect CRLF assumption before any
file was written; the note and clean retry are retained. Baseline source,
docs, historical evidence and quality are saved under
runs/phase2/selector_arithmetic_checks/20260919_step47/. Unrelated source,
configs, frozen Phase I records, H2 and historical evidence are preserved.
The new source requires its own control refresh before a checked commit;
RAM-dependent controls remain deferred. Nothing is committed or pushed.


Milestone-47 finalization note: the first finalizer refused while reading
PowerShell-redirected UTF-16 test logs as UTF-8, before publishing any
receipt. The failed script/log are preserved; finalize_evidence_v2.py
uses BOM-aware decoding with every validation assertion retained. No
production source, test result or historical log was changed.


## 2026-09-19 - Milestone 48: owner-requested regenerable-cache cleanup

The owner asked to free space and remove project junk. The delegated operational
choice removed 13,523 source-backed bytecode/tool/font cache
files totaling 329,345,439 bytes (314.09 MiB), preserving
all data, weights, source, reference environments and historical evidence.
Exact paths, hashes, no reparse-point traversal, exclusive opens and no active
project Python worker were checked before deletion. No recursive delete or
permissions change occurred. 28 unreadable directories
were skipped with their unknown sizes recorded. The first prevalidation failed
on a PowerShell parameter combination before any deletion; the original failure
and corrected helper are retained. The required fresh quality bundle passes:
564 passed, 4 warnings, 925 subtests passed in 1284.44s (0:21:24); lint and strict types pass. Caches regenerated by that verification
were removed afterward. All 77,109 readable retained baseline files
match SHA-256; the quality pointer's old bytes are preserved separately. Source
fingerprint remains `1e79dfc779b0cf616243c3e33f2f8a0893397bf41e02ebdf36b0e29e7bdf05f9`. Final disk snapshot is
33.28 GiB, above 20 GiB; unrelated volume fluctuations mean this
snapshot is not a claim about net cleanup gain. No scientific workload,
control refresh, commit, push, guard change or owner-only decision occurred.
Evidence: `runs/phase2/cleanup_checks/20260919_step48/receipt.json`;
review: `docs/phase2/cleanup_review.md`.


### C-drive cleanup follow-up, 19 September 2026 (milestone 48 maintenance)

The owner authorized removing only unwanted C-drive files established to belong
to this project. Six old pytest runs (18, 19, 20, 47, 48, 49) held 264 synthetic
`tests/test_gate_evidence.py` fixtures. Verified truncated test names, literal
11-byte subject placeholders, four `git_commit: "fixture"` records per fixture,
allowed file paths, hashes and absent stale-lock PIDs before deletion. Removed
5,103 files totaling 2,222,172 logical bytes (2.12 MiB), then only empty
directories; zero deletion failures. No recursive delete or permissions change.

Pytest-31 is retained: its incomplete fixture failed ownership prevalidation;
all 159 retained files match their baseline hashes. Shared pip/runtime
caches and unclassified/inaccessible temp contents were not removed. Initial
process prevalidation also refused before deletion; subsequent inspection
positively isolated another project's tests to their explicit D-drive basetemp.
Project/shared-temp/unclassified pytest workers still blocked the final helper.
No unrelated process was stopped and no project resource guard changed.

This is a cleanup continuation, not a new engineering or scientific milestone.
No source, dependency package, data, checkpoint or research evidence changed.
The full quality run just completed at milestone 48 (564 tests / 925 subtests,
lint and strict types) remains byte-identical and verified against the same
source fingerprint. It was not rerun for deletion of disposable test fixtures;
verification checked exact target absence, retained hashes, source, Git and
quality-bundle integrity without recreating those fixtures. Prior failures,
inventories and receipts remain under
`runs/phase2/cleanup_checks/20260919_c_drive_followup/`.
C-drive free-space snapshot: 2.87 GiB; this small cleanup does not
solve its broader space pressure. Unknown/shared files are outside the owner's
cleanup scope. Freeze/EA inclusion, MMIDB policy, Gate A and commit/push remain
owner decisions; no experiment, control refresh, commit or push occurred.


## 2026-09-19 - Milestone 49: authorized bounded GPU readiness probe

The owner permitted GPU use if useful and requested clarification of the
1,893-hour CPU proxy. Adopted operational choices: compare CPU and CUDA on
fixed audited source-support batches without changing scientific settings;
prefer GPU-capable LaBraM development and retain CPU EEGNet at the tested batch
size; keep end-to-end costs unknown until measured. The 96-step, 600-second
engineering cap, live machine checks and existing cooling policy all passed.
No source-selector guard was bypassed, no private fitting helper was used,
and the 256-step scientific-execution obstruction remains. This extends the
engineering measurement scope under explicit owner GPU authorization; it is
not freeze ratification or an experiment from an uncommitted scientific config.

The probe completed 48 CPU + 48 GPU gradient steps using four methods and two
proposed rates. Observed resident-batch step ratios favor GPU about 1.6-1.7x for
linear/LoRA and 1.8-3.4x for full tuning; EEGNet favors CPU at batch four. These
are five-sample medians on one subject/seed, not complete-workload accelerations.
Initial logits pass the separately declared 1e-4 float32 sanity tolerance;
selected-state updates, finite gradients, frozen state and caller isolation
pass. Input hashes, source and the scientific draft remain unchanged. Full
quality was not repeated: the existing milestone-48 exact-source 564-test /
925-subtest lint/types/tests bundle verifies; actual new GPU checks are saved.
No target-query evaluations, complete selections, scientific cells, control
refresh, commit or push occurred. Owner-only decisions remain open.
Review: `docs/phase2/gpu_readiness_review.md`; final evidence:
`runs/phase2/gpu_readiness_checks/20260919_step49/receipt.json`.


## 2026-09-19 - Milestone 50: owner-authorized GPU source and crash checkpoints

The owner's GPU/checkpoint request and subsequent 12-hour delegation authorize
this bounded engineering extension. Decisions: opt-in plain/LoRA GPU source
SGD, retain CPU support/query, save immutable pickle-free checkpoints every
gradient step, preserve every generation, and resume only after full original
work admission. OS locks release on process death; context/input/cursor/RNG,
optimizer/model identity and chain integrity are validated. Corrupt committed
records refuse; partial unpublished blobs remain visible and unused. No guard
was weakened, historical record changed, or scientific setting ratified.

Focused verification: 28 tests / 50 subtests. Full quality: 571 passed, 4 warnings, 935 subtests passed in 845.69s (0:14:05);
lint and strict types pass. Initial lint/type failures remain in the evidence
directory and were corrected before final verification. Two real GPU processes
hard-exited after durable checkpoint 3. Saved progress was resumed, including a further full-tuning stop when the GPU
temperature sensor became unavailable during step-47 publication. Step 46 was
committed; after the sensor responded again, recovery repeated the uncommitted
step and finished without weakening any guard. Full/LoRA histories, loss/state
hashes and validation folds match uninterrupted runs exactly. Total: 205
engineering gradient steps (201 GPU source, four CPU support); zero outer-target predictions, full selections or scientific cells.
Each public invocation still admits 51 logical steps under the 256-step cap;
the actual full-cohort selection refuses before fitting. Existing live guards,
600-second process timeouts and the probe's 8 GiB allocator cap remain active.

Source changed only in adaptation/labram_source.py plus the new checkpoint
helper and tests. Fingerprint: `6d01ec59d7323af0fd91f141d1484a419717062b43d7d52dc221d27ea9be19a2`.
All 1660 baseline Phase II evidence files and
the freeze draft are preserved. Resume covers source SGD; unfinished support/
query work restarts. Cross-driver/device and power-loss recovery are untested;
retaining all generations is bounded engineering, not a scientific storage plan.
The existing control refresh remains outstanding and may be retried when RAM
admission permits. Owner-only scientific decisions and commit/push prohibitions
remain; no control refresh is claimed here. Review:
`docs/phase2/gpu_checkpoint_review.md`; final receipt:
`runs/phase2/gpu_checkpoint_checks/20260919_step50/receipt.json`.


## 2026-09-19 - Milestone 51: existing current-source controls refreshed

Under the owner's autonomous-work/GPU delegation and the existing authorized
RAM-dependent retry, ran the original 45-fit CUDA refresh with committed,
unchanged configurations. Startup 12.08 GiB RAM/30.70 GiB disk passed; the
10 GiB startup/4 GiB active RAM and cooling guards remained intact. Additional
external monitoring retained the project 20 GiB floor. Minimum observed active
RAM 10.53 GiB and monitored disk 30.70 GiB; no stop or override.
All 45 records pass independent split/label/history/metric reconstruction;
shuffled-label mean 48.7654% <= 60% and pre-cue 24.8553% <= 35%.
Completed-fit records are recovery units; an interrupted partial fit restarts
(largest actual fit 6.86s). No historic control code was changed.

Operational verification deviation: reused and revalidated the just-completed
milestone-50 exact-source 571-test/935-subtest lint/types/tests bundle rather
than rerunning unchanged tests. Actual new compute was independently audited.
All 44,968 historical run files retain their
hashes; source/config/tests, quality bytes and the scientific draft are unchanged.
Source `6d01ec59d7323af0fd91f141d1484a419717062b43d7d52dc221d27ea9be19a2` now has a matching 45/45 control bundle.
This closes the deferred control prerequisite only. No Gate A acceptance rule,
freeze ratification/EA inclusion, MMIDB policy or commit/push decision was taken.
No Phase II scientific cell, commit or push occurred. Review:
`docs/phase2/control_refresh_review.md`; receipt:
`runs/phase2/control_refresh_checks/20260919_step51/receipt.json`.


## 2026-09-19 - Milestone 52: measured guarded whole-fold device preference

The owner's GPU-if-better request left whole-workflow latency unmeasured after
kernel and crash-recovery checks. Under the autonomous delegation, fixed four
51-step public folds (full/CPU, full/GPU, LoRA/GPU, LoRA/CPU), with a predeclared
1.15x elapsed threshold. Adopted full: gpu (CPU/GPU elapsed ratio 1.777x); lora: cpu (CPU/GPU elapsed ratio 0.337x). All initial states, settings,
masks, data identities and sampled trials match across devices. No score-based
choice or default/scientific setting change occurred. Guard overhead differs
between native GPU and externally guarded legacy CPU; these are observed
workflow timings, not hardware-isolated or full-campaign accelerations.

All four calls passed under original admission/cooling constraints and 600-second
worker caps. 204 engineering steps, zero complete selections, outer-target
predictions or scientific cells. Completed calibration cases are write-once
resume units; equal exclusion of per-step checkpoint serialization is explicit.
All 45,040 historical run files and the scientific draft are preserved. Source,
configs and tests are unchanged. Verified and reused exact-source quality
(571 tests/935 subtests, lint/types) and 45/45 controls; no redundant rerun is
claimed. No commit or push occurred. Review:
`docs/phase2/whole_fold_device_review.md`; receipt:
`runs/phase2/whole_fold_device_checks/20260919_step52/receipt.json`.
The bounded GPU/checkpoint/control scope is complete. Explicit owner-only
scientific decisions and committed/admitted execution remain the actual next
blocker; the time delegation does not authorize inventing work or bypassing them.


### Milestone-52 documentation follow-up, 19 September 2026

Final orientation review found one pre-status README sentence still saying the
control refresh was RAM-deferred, despite the completed milestone-51 bundle.
Replaced only that stale sentence with the verified 45/45 current-source status
and the requirement to refresh after future source/environment changes. Saved
prior bytes and a supplemental receipt; original milestone receipts are not
rewritten. The first byte-precondition assertion refused before any write
because this older segment uses LF, not the newer status block's CRLF; the
corrected edit preserves those observed endings. Source, tests, controls,
scientific draft and all research evidence are unchanged. No new engineering
milestone, experiment, commit or push occurred.


## 2026-09-20 - Session close after milestone 52

The owner requested updating the documentation and ending the session. Refreshed
the handoff, current status and decision register to record the blocked autonomous
goal, its three preserved blocker audits and the remaining explicit owner decisions.
The requested 12-hour window was not completed; no project Python workers were
running at the close inspection. No new milestone, training, scientific cell,
commit or push occurred.

Documentation-only verification deviation: revalidated and reused the existing
exact-source milestone-50 quality bundle (571 tests / 935 subtests, lint/types)
and milestone-51 45/45 controls instead of rerunning unchanged tests or training.
Captured document baselines and diffs; verified source/config/test hashes, the
unratified freeze draft, prior final receipts, Git HEAD and 87-path status are
unchanged. Historical documentation remains append-only outside current status
heads. A first newline precondition refused before any document write; its
receipt preserves the LF/CRLF mismatch and the corrected byte-safe match.
No owner-only decision was inferred. The new immutable close receipt is
`runs/phase2/handoff_checks/20260920_session_close/receipt.json`.


## 2026-09-23 - Owner Cho scope and Profile B preparation choices

The owner selected the four neural methods linear, LoRA, full tuning and
EEGNet for the first exploratory Cho2017 five-shot tranche and deferred
EA-tangent to a separately predeclared and costed comparison. The owner
also selected preparation of a newly versioned 60 Hz Cho Profile B path
while current config/artifacts still use 50 Hz. These are planning and
preprocessing-policy choices, not full scientific freeze ratification or
preprocessing/compute admission. No code, config, data, frozen result or
historical run record changed; no experiment, commit or push occurred.
The corrected four-method planning count is 1,040 cells/selections and
1,893.4 CPU proxy hours with 1.25 allowance, not an admitted budget.
Complete-work, resource, committed-config, Gate A and MMIDB decisions remain
open. Review: `docs/phase2/freeze_decision_packet_20260923.md`; receipt:
`runs/phase2/freeze_scope_decision_checks/20260923_owner_choices/receipt.json`.


### Cho 60 Hz rebuild planning follow-up, 23 September 2026

Read-only inspection found 52 existing Cho Profile B NPZ artifacts and 52
manifests (1.848 GiB); every manifest pins the current 50 Hz Profile B
config. The earlier milestone-29 review described its then-bounded two-subject
preparation, not the current full cohort. The new
`docs/phase2/cho_profile_b_60hz_rebuild_plan_20260923.md` specifies a
separate output namespace, Cho-specific config and versioned binding path,
no-clobber publication, and staged audits. Its size estimate is planning
arithmetic only; disk remains below the 20 GiB floor. No code/config/data
changed and no preprocessing or scientific experiment ran. Supplemental
receipt: `runs/phase2/freeze_scope_decision_checks/20260923_owner_choices/plan_supplement_receipt.json`.


## 2026-09-23 - Cho 60 Hz engineering preparation after owner continuation

Prepared the owner-selected 60 Hz Cho Profile B path in a separate versioned
config and output namespace. Added a write-once subject writer, explicit
60 Hz binding and asset inventory, mixed 50/60 Hz cohort refusal, and a
read-only subject-01 spectral diagnostic. The shared 50 Hz config and
historical 52-subject directory were not rewritten. An independent code
review found that a linked output directory could alias the legacy namespace
and that the first binder draft did not rehash raw source bytes; both were
fixed and covered by regression tests. Focused synthetic tests passed.

This is an engineering implementation of the selected preprocessing policy,
not scientific freeze ratification or real-data validation. At the later
resource snapshot, 6.071 GiB disk free failed the 20 GiB floor and 9.611 GiB
available RAM failed the separate 10 GiB control-refresh startup guard.
No 60 Hz EEG artifact, bounded real-signal diagnostic, control refresh,
source selection, scientific cell, commit or push occurred. Exact-source
quality passed 589 tests / 935 subtests, lint and types, and a read-only
hash comparison confirmed all 52 historical Cho NPZ artifacts against the
saved cohort receipt. Previous source-bound controls are stale after these
code/config/test edits; another guarded control refresh is needed for this
source. The new write-once receipt is
`runs/phase2/cho_60hz_preparation_checks/20260923_prepared/receipt.json`.
See `docs/phase2/cho_60hz_preparation_review_20260923.md`.


## 2026-09-23 - Guarded real Cho 60 Hz cohort completion

After the earlier low-disk stop, fresh admission showed enough headroom for
one bounded subject and then the remaining cohort. The new versioned 60 Hz
Profile B directory contains 52 independently audited artifact/manifest
pairs. The predeclared read-only subject-01 diagnostic found 30.67 dB
attenuation of the 60 Hz line-to-sideband ratio, above its 6 dB engineering
threshold. The full audit passed 52/52 Profile A-to-B trial/label joins,
raw/config binding, and real five-shot episode bindings. It rechecked all
52 historical 50 Hz NPZ hashes against the saved milestone-32 receipt;
all match. Review:
`docs/phase2/cho_60hz_real_cohort_review_20260923.md`; write-once audit:
`runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json`.

This is preprocessing and binding evidence only. No scientific cell,
current-source control refresh, freeze ratification, commit or push occurred.
At the later resource snapshot, 7.98 GiB RAM was available against the
unchanged 10 GiB control-refresh startup guard. The remaining scientific
and execution gates are recorded in the review.


## 2026-09-24 - Exact-rational Phase II aggregation preparation

Added a pure subject-method-shot aggregation core that accepts an explicit
expected cell roster and externally verified exact-rational balanced-accuracy
rows. It rejects duplicate, missing and extra identities and reused digests,
keeps different shot counts separate, and computes seed means with `Fraction`.
It reads no scientific cell files, runs no inference and publishes no report.
The first review found that grouping by subject and method would mix shot
counts; the implementation and synthetic test were corrected before the full
quality run. The [engineering receipt](../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/receipt.json)
pins the module, tests and current source. Full exact-source quality passed
771 tests, 1 skip, 1,002 subtests, lint and strict types for source
`f2d4acdd3d5fab96e96ecb63044c2224b9927c52049719c3dd373350f1fd7f87`.

The current-source no-future check-only wrapper recomputed all nine sealed
raw inputs and found 0 valid / 36 missing matched fits, no invalid records,
unexpected records or score; it started no fit and did not sign Gate A.
The 45-control current-source preflight deferred at 9.589 GiB available RAM
against the unchanged 10 GiB startup guard, with 27.622 GiB disk free and no
fit. The [handoff snapshot](../runs/phase2/handoff_checks/20260924_f2d4acdd/receipt.json)
verifies the pinned receipts and 213 local document links. The four-method
scientific freeze, Gate A, complete-work resource admission and committed
executable configurations remain open. No scientific Cho cell, commit or
push occurred.

After this source update, a fresh [read-only candidate-route receipt](../runs/phase2/freeze_readiness/20260924_f2d4acdd_candidate_routes/run_receipt.json)
matched the unchanged unratified template to all 1,040 real Cho case input
routes under the current runner and execution-gate code. It started no
selection or target fit. A separate [read-only control-context receipt](../runs/phase2/control_refresh_checks/20260924_subject_aggregation_f2d4acdd/inventory_receipt.json)
verified 0 valid / 45 missing controls, no invalid or unexpected record.
The [full-roster synthetic aggregation rehearsal](../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/full_roster_synthetic_receipt.json)
checked 1,040 dummy input rows and 208 five-seed groups against the selected
planning crosswalk, without reading any real scientific cell score.

## 2026-09-28 - Pure Cho paired inference preparation

After the owner's request to continue to the next step under limited RAM,
added an unratified, pure numerical Phase II calculation for the proposed
Cho LoRA-minus-linear analysis. It requires all 52 canonical subject IDs
and exact-rational paired differences, preserves exact absolute rank ties
before one-sided Wilcoxon–Pratt, handles all-zero input, and returns separate
95%/90% paired-mean t intervals. It has no cell reader, scientific admission,
claim Boolean or report writer. See the [engineering review](phase2/cho_pure_inference_review_20260928.md)
and [write-once receipt](../runs/phase2/analysis_inference_checks/20260928_9bf0516c/receipt.json).

Focused synthetic checks passed 13 tests, lint and strict typing. Full
exact-source quality passed 796 tests, 1 skip and 1,009 subtests plus lint
and strict types for source
`9bf0516c11aec1e3cda0635e79fc58a7cc3db5d2df4d496a2039ab661ad597b9`.
A read-only candidate-route check matched 1,040/1,040 proposed cases; a
read-only control inventory found 0 valid / 45 missing with no invalid
record. The previous 24 September source-bound receipts are historical.
Available RAM was 6.369 GiB at the inventory snapshot, below the unchanged
10 GiB control-fit startup guard; no fit started. The complete Cho selection
still requires 5,253 steps above the 256-step engineering cap. No real
scientific cell, inferential report, freeze ratification, Gate A sign-off,
commit or push occurred.

The later [full-roster synthetic inference rehearsal](phase2/cho_full_roster_inference_synthetic_review_20260928.md)
reused this exact source and quality bundle. It compared an independent
1,040-cell Cartesian roster with the planning crosswalk, generated two
synthetic 1,040-row score sets, checked 208 five-seed means and 52 paired
differences in each, and matched the mixed Pratt result against a separate
common-denominator calculation. Its [write-once receipt](../runs/phase2/analysis_inference_checks/20260928_9bf0516c_full_roster_synthetic/receipt.json)
records zero real cell scores, fits, scientific cells or claims. The freeze,
controls, cap and Gate A boundaries above are unchanged.

The subsequent [recorder-format synthetic rehearsal](phase2/cho_full_roster_recorder_inference_synthetic_review_20260928.md)
prewrote external expected pins and checked all 1,040 fixture cells through
the read-only bridge, then 208 means and 52 paired differences. It rejected
a post-pin cell change and an unlisted claim. The
[write-once receipt](../runs/phase2/analysis_inference_checks/20260928_9bf0516c_recorder_bridge_synthetic/receipt.json)
records zero real cell scores, fits, scientific admissions or report. The
4,160 temporary recorder-format files were removed. This was not a full
recorder writer lifecycle or real selection-evidence verification; no owner
freeze, Gate A, cap or control decision changed.

## 2026-09-28 - Guarded no-future current-source check stopped

After the synthetic bridge rehearsal, a monitored read-only
`scripts.run_no_future_matched_control --check-only` attempt was bound to
source `9bf0516c11aec1e3cda0635e79fc58a7cc3db5d2df4d496a2039ab661ad597b9`
and its verified full quality bundle. The wrapper started with 5.204 GiB
available RAM and 32.335 GiB free disk, then stopped its owned child after
491.5 seconds when RAM reached 3.954 GiB below the 4 GiB active floor.
See the [review](phase2/no_future_current_source_guarded_stop_20260928.md)
and [write-once receipt](../runs/phase2/gate_a_diagnostics/20260928_no_future_pure_inference_9bf0516c/receipt.json).
The child emitted no audit report, so there is no current-source count for
the 36 expected fits from this attempt. The prior-source 0/36 result remains
historical. No fit, scientific cell, Gate A decision, freeze ratification,
commit or push occurred; the 10 GiB control-fit startup guard is unchanged.

## 2026-09-28 - Cho analysis identity binding preparation

Added a pure first-tranche identity binder and focused synthetic tests for
the proposed 52 x 4 x 5 Cho roster. It rechecks protocol, episode, source
selection, preprocessing and externally reviewed method digests, and rejects
mixed source identities without reading scores. Full exact-source quality
passed Ruff, strict mypy, 802 tests, 1 skip and 1,016 subtests for source
`5dce82b17ee36d791d78659900ba87cd1f3d4c425e1fc237bf0fd6cbb8198d20`.
The [review](phase2/cho_analysis_identity_binding_review_20260928.md)
links the write-once quality, 1,040-route, 0 valid / 45 missing control,
and actual-route synthetic rehearsal receipts. No real cell evidence,
fit, scientific admission, analysis freeze, Gate A sign-off, commit or push
occurred. Previous `9bf0516c` source-bound receipts are historical.

The subsequent [guarded no-future read-only check](phase2/no_future_identity_source_check_20260928.md)
completed on the same exact source. Its [write-once receipt](../runs/phase2/gate_a_diagnostics/20260928_no_future_identity_binding_5dce82b1/receipt.json)
records 0 valid / 36 missing matched-control records, no invalid or
unexpected record. The nine-subject preprocessing writer check ran; final
record-bound raw verification remains false because the records are
missing. Minimum available RAM was 9.185 GiB, minimum free disk 27.842
GiB. No fit or gate decision occurred. The 45 source-bound controls, full
freeze, cap decision and Gate A remain open.

## 2026-09-28 - Pure Cho paired-input bridge

Added a pure builder for the frozen 52-subject x four-method x five-seed
Cho first tranche. From caller-supplied externally verified rational score
rows, it requires exact 1,040-case coverage, computes 208 five-seed means
and forms 52 exact LoRA-minus-linear subject differences. The
[review](phase2/cho_paired_inputs_review_20260928.md) records the trust
boundary and 12 passing focused tests, Ruff and strict mypy. The current
source is `a7841e14fde97a8badc62ad5ce1e0c204183ab79e023e2b7138c42d6c3c5f311`;
the preceding `5dce82b1` full quality and controls are historical for
their source. D: remained below the unchanged 20 GiB fit floor, so no fit
was launched. Full current-source quality, controls, the scientific
freeze, selector-cap resolution and Gate A remain open.

## 2026-09-28 - Guarded full-quality attempt and test resource fixture

The [first exact-source full-quality attempt](../runs/phase2/quality_attempts/20260928_cho_paired_inputs_a7841e14_disk_floor/receipt.json)
for `a7841e14` passed Ruff and mypy but failed four synthetic
case-engineering tests at the unchanged 20 GiB result-frame disk
prelaunch guard (810 passed, 1 skipped). The failed attempt and logs are
preserved; no passing quality archive was made. A function-scoped
deterministic sensor was then added to the synthetic lifecycle tests.
Production floors and child supervision remain unchanged. A new
channel-specific regression verifies that a post-child disk drop prevents
proposal and attestation publication.

Source at that step was
`ef8b3f8289de6d23418d5e4d287be2ddc1a745f6b6ad164ae21cfc034f12be9c`.
Its [focused receipt](../runs/phase2/analysis_pairing_checks/20260928_ef8b3f82_focused/receipt.json)
pins 37 passed, 1 skipped, Ruff and strict mypy. A second full-quality
run was deferred before launch as D: fell to about 9.3 GiB free. The
20 GiB fit floor remains unmet, so no control or scientific fit started.
Current-source full quality, controls, the freeze and Gate A remain open.

## 2026-09-28 - Read-only recorder preparation and Cho buffer provenance

Added a read-only composition that checks an independently supplied source
and all 1,040 case identities before reading a pinned recorder, then forms
208 exact means and 52 paired subject inputs. The [review](phase2/cho_analysis_preparation_review_20260928.md)
and [focused receipt](../runs/phase2/analysis_pairing_checks/20260928_c535f457_focused/receipt.json)
pin source `c535f457`, Ruff, mypy, 11 passed tests and 9 passed subtests.
The Cho episode loader now hashes the exact A/B artifact and B manifest
buffers it parses. Published cells still lack the observed target B binding;
the review records the prospective attestation requirement. This is
engineering preparation only. D: remained about 9.05 GiB free, below the
unchanged 20 GiB fit floor. Full exact-source quality, controls, the
scientific freeze, selector cap and Gate A remain open. No fit, real Cho
cell, inferential report, commit or push occurred.

## 2026-09-28 - Prospective Cho target-input attestation

The [target-input review](phase2/cho_target_input_attestation_review_20260928.md)
records the subsequent case-executor change: the observed LaBraM 60 Hz
target binding, or the EEGNet Profile A anchor identity, is checked against
the selected Cho case and included in a proposed success cell. The Profile
A EEGNet loader hashes its parsed artifact buffer. A read-only verifier
checks the attestation inside externally pinned cell bytes against the
planned route before paired scores may be formed. Earlier cells do not
gain target-use proof; the verifier does not replay inference or by itself
authorize scientific claims. It syntax-checks B profile-config,
base-config and B manifest source digests without independently binding
them to persisted bytes; that comparison remains necessary for admission.

The `c535f457` [guarded full-quality attempt](../runs/phase2/quality_attempts/20260928_cho_preparation_c535f457_guarded/receipt.json)
passed Ruff and mypy, then its monitor stopped the owned test process at
the quality-only active disk floor after about 462 seconds. No passing
quality archive was made. Source `98f6f523` has a
[write-once focused receipt](../runs/phase2/analysis_pairing_checks/20260928_target_attestation_focused/receipt.json)
with stable source, Ruff and strict mypy passing and 9 tests / 15
subtests passing. Full current-source quality remains pending. The
production 20 GiB fit
floor is unchanged. Earlier inventories found 0/45 source-bound controls
and 0/36 no-future records; current-source inventories are pending. The
5,253-step selector exceeds the unchanged 256-step cap;
the full scientific freeze and Gate A remain unsigned. No real Cho fit,
cell, score, report, commit or push occurred.

## 2026-09-28 - Persisted Cho target declaration checks

Following the prospective [target-input attestation](phase2/cho_target_input_attestation_review_20260928.md),
the read-only Cho preparation path now requires an independent base-config
digest and reviewed project root. It verifies bounded persisted bytes of
the base config, 60 Hz variant and all 52 B manifests, then compares their
config and raw source declarations against the recorded LaBraM B target
binding. It also checks EEGNet's Profile A anchor base digest against the
independent pin. See the [review](phase2/cho_persisted_target_declarations_review_20260928.md)
and [focused receipt](../runs/phase2/analysis_pairing_checks/20260928_persisted_target_focused/receipt.json)
for source `147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`.
The receipt pins stable source, Ruff, strict mypy, 13 passed, 1 skipped
and 15 passed subtests. The prior `98f6f523` focused receipt is historical.
Full exact-source quality was pending at that step and later passed as
recorded below. No production fit guard, scientific policy, freeze
or Gate A decision changed. Artifact/raw-file hashing, inference replay,
complete selection, checkpoints and environment remain separate
admission requirements. No real Cho fit, cell, score, report, commit or
push occurred.

## 2026-09-28 - Full exact-source quality for persisted Cho target preparation

The guarded [full quality attempt](../runs/phase2/quality_attempts/20260928_cho_persisted_target_147c0d11_guarded/receipt.json)
completed for source `147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`.
The [passing archive](../runs/phase2/quality_history/20260928_cho_persisted_target_147c0d11.json)
pins Ruff, full strict mypy, 830 passed tests, 2 skips and 1,033 passed
subtests. Source stayed stable; minimum free disk was 9.572 GiB.
Previous documentation receipts pin pre-quality status and earlier
document bytes. Current-source control and no-future refresh is
underway, without a reported outcome. No production fit guard or
scientific policy changed. No fit, real Cho cell, score, admission,
report, commit or push occurred.

## 2026-09-28 - Current-source control inventory and no-future resource deferral

Following the [passing full-quality archive](../runs/phase2/quality_history/20260928_cho_persisted_target_147c0d11.json)
for source `147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`,
the [read-only control inventory](../runs/phase2/control_refresh_checks/20260928_persisted_target_147c0d11/inventory_receipt.json)
found 0 valid / 45 missing source-bound records and no invalid or
unexpected records. It started no fit. The
[no-future check-only preflight](../runs/phase2/gate_a_diagnostics/20260928_no_future_persisted_target_147c0d11/preflight_receipt.json)
deferred before raw recomputation because the writer and prepared wrapper
require 20 GiB free disk and 10.494 GiB was free. No current-source
36-record result was established; the historical 0/36 inventory applies
to a different source. Production guards were not changed. Complete
selection, checkpoint/environment evidence, the 5,253-step selector-cap
decision, scientific freeze, Gate A and current-source controls remain
open. No training, real Cho cell, score, report or claim occurred.

## 2026-09-28 - Source `48e668e3` query, route, raw and quality evidence

The [new engineering review](phase2/cho_query_route_raw_review_20260928.md)
records a query-metric guard that compares pinned cell confusion-row
totals with the planned target query labels and requires independent
`ChoCaseInputPins` and exact route rederivation before cell/score reads.
The [read-only raw audit](../runs/phase2/freeze_readiness/20260928_cho_raw_source_readonly/receipt.json)
rebuilt 1,040 routes, checked 52 A catalogs and 52 B assets, and directly
hashed 52 declared raw Cho files totaling 10,704,036,837 bytes. The
[method-template receipt](../runs/phase2/freeze_readiness/20260928_48e668e3_method_template_readonly/receipt.json)
checked 40 typed candidates; it remains unratified. Source
`48e668e3bc8ed9b8b277454de460d359e686c3519ea5173d2107d771cdb58dcf`
then [passed full quality](../runs/phase2/quality_history/20260928_cho_query_route_48e668e3.json)
under a [guarded attempt](../runs/phase2/quality_attempts/20260928_cho_query_route_48e668e3_guarded/receipt.json):
Ruff, strict mypy, 832 tests and 1,033 subtests passed, with 2 skips;
minimum disk/RAM were 10.809/15.077 GiB and source stayed stable.

The [source-bound inventory](../runs/phase2/control_refresh_checks/20260928_query_route_48e668e3/inventory_receipt.json)
found 0 valid / 45 missing records with no invalid or unexpected record.
The [no-future preflight](../runs/phase2/gate_a_diagnostics/20260928_no_future_query_route_48e668e3/preflight_receipt.json)
deferred before raw recomputation at 11.525 GiB free against 20 GiB
required. The 36-record inventory is unverified for this source; the
source `147c0d11` snapshot and earlier 0/36 findings are historical.
Complete selection, checkpoint/environment evidence, the 5,253-step
selector versus 256-step cap, scientific freeze and Gate A remain open.
The production 20 GiB fit floor is unchanged. No fit, real Cho cell,
score, report, scientific admission, commit or push occurred.

## 2026-09-28 - Source `a80b571d` selection-file binding and evidence refresh

The [selection-file review](phase2/cho_selection_file_binding_review_20260928.md)
records a bounded read-only check of the persisted selection file named by
each externally pinned Cho cell. It checks route case claims, candidate
settings, selected winner, method digest and final-fit digest claim, then
rechecks physical file stability after paired-input construction. A
recorded completion flag does not prove the full selector or final fit.
The execution-gate canonical selection reader now uses the same bounded
canonical-record guard.

Source `a80b571d64460dbe18285bb367520195810bccf66fc0b7d1034bad85d2fd7344`
[passed full exact-source quality](../runs/phase2/quality_history/20260928_cho_selection_binding_a80b571d.json)
under a [guarded attempt](../runs/phase2/quality_attempts/20260928_cho_selection_binding_a80b571d_guarded/receipt.json):
Ruff and strict mypy passed, with 847 tests and 1,033 subtests passed
and 2 skips. Source was stable; minimum free disk/RAM were 11.182/13.945
GiB. The [read-only raw audit](../runs/phase2/freeze_readiness/20260928_a80b571d_raw_source_readonly/receipt.json)
verified 1,040 routes, 52 A catalogs, 52 B assets and 52 declared raw
files totaling 10,704,036,837 bytes. The
[method-template receipt](../runs/phase2/freeze_readiness/20260928_a80b571d_method_template_readonly/receipt.json)
checked 40 typed candidates and four matching method digests, but the
draft remains unratified.

The [current-source control inventory](../runs/phase2/control_refresh_checks/20260928_selection_binding_a80b571d/inventory_receipt.json)
found 0 valid / 45 missing, with no invalid or unexpected record. The
[no-future preflight](../runs/phase2/gate_a_diagnostics/20260928_no_future_selection_binding_a80b571d/preflight_receipt.json)
deferred before raw recomputation at 11.37 GiB free against 20 GiB
required. The 36-record inventory remains unverified for this source.
The 5,253-step selector still exceeds the unchanged 256-step cap; full
scientific freeze, Gate A, complete selection and checkpoint/environment
evidence remain open. No real Cho fit, cell, score, report, scientific
admission, commit or push occurred.

## 2026-09-30 - Source `08751a39` tensor-state composer verification and audit

The [selected-source tensor-state review](phase2/cho_selected_tensor_state_review_20260930.md)
records read-only tensor reconstruction added to the 1,040-case paired-input
composer. The composer now requires independently supplied full static
configuration objects and digests for all four methods, rederives every route,
and calls [verify_cho_selected_source_state](../evaluation/phase2_cho_source_restore.py)
for each recorded winner before any score row is read. The helper derives the
architecture independently, rebuilds a fresh seeded model and restores the
published `full_v1` tensor state through the
[SelectedSourceStore](../evaluation/phase2_selected_source_store.py), whose
manifest, evidence and weights reads are bounded on opened descriptors with
identity rechecks (64 MiB LaBraM / 1 MiB EEGNet weights caps, 6 GiB RAM
required before a case, 4 GiB during). The helper returns only a frozen digest
witness and releases no target adapter. Cases still run sequentially in the
composer process; isolated per-case lifetimes, a verified Job memory cap and a
measured LaBraM peak remain open before a real sweep.

At source `08751a3919971f47c65f0dd14bd4061dc0dd7f070b07908023374a89361e6387`,
focused restore tests passed 39 tests and 29 subtests, all five composer tests
passed, and focused Ruff and strict mypy passed. The
[method-template revalidation](../runs/phase2/freeze_readiness/20260930_08751a39_method_template_readonly/receipt.json)
checked 40 typed candidates and four method digests and remains unratified.
The [raw-source read-only audit](../runs/phase2/freeze_readiness/20260930_08751a39_raw_source_readonly/verify_raw_sources.py)
and [guarded full-quality runner](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded/run_guarded_quality.py)
are prepared and pinned to this source but have not started below their
unchanged 8/6 and 9/6 GiB resource floors; no receipt exists for either and no
current-source full-quality archive exists. A later same-day handoff audit
recomputed the fingerprint unchanged, re-ran the focused restore tests with
the same 39/29 result, sampled disk/RAM below both floors, and changed
documentation only. The historical `90d822aa` full-quality archive attests
only its own earlier source.

Current-source 45-control and 36-record no-future inventories remain
unverified. The 5,253-step selector still exceeds the unchanged 256-step
engineering cap. The scientific freeze and Gate A remain unsigned. No real
Cho fit, cell, score, report, scientific admission, commit or push occurred.

## 2026-09-30 - Source `08751a39` raw-source read-only audit passed

The [read-only raw audit](../runs/phase2/freeze_readiness/20260930_08751a39_raw_source_readonly/receipt.json)
ran once shared D: recovered to 8.213 GiB free and 6.956 GiB available RAM,
and passed for source
`08751a3919971f47c65f0dd14bd4061dc0dd7f070b07908023374a89361e6387`:
status `pass_readonly_unratified`, `source_stable=true`, both recorded
source hashes equal to the live fingerprint, 1,040 proposed cases across the
exact four 260-case method counts, 52 Profile A catalogs, 52 pinned 60 Hz
Profile B assets and 52 declared raw Cho files totaling 10,704,036,837 bytes,
the same total as every prior exact-source raw audit. Minimum disk/RAM during
the 22.2-second run were 8.213/6.180 GiB. No training, cell, score or
admission occurred. The guarded full-quality attempt for the same source
remains prepared and unwritten below its unchanged 9/6 GiB startup floor;
current-source 45-control and 36-record no-future inventories remain open.
The source fingerprint stayed `08751a39` throughout. No fit, commit or push
occurred.

## 2026-09-30 - Source `08751a39` guarded quality stopped on the active RAM floor

The first guarded full-quality attempt for source `08751a39` stopped at 646.4
seconds when available RAM fell below the unchanged 4 GiB active floor
(observed minimum 3.489 GiB after about 11 GiB two minutes earlier; the
machine is shared with another agent's active workloads). Lint and strict
mypy had passed and pytest was interrupted near 40%. The guard terminated the
owned child tree cleanly, and the attempt directory
[20260930_tensor_state_08751a39_guarded](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded/receipt.json)
is preserved write-once with `status=stopped_or_failed`, `source_stable=true`
and no archive written. Per the write-once rule a fresh attempt directory
[20260930_tensor_state_08751a39_guarded_retry1](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded_retry1/run_guarded_quality.py)
was prepared with the same pinned source and unchanged guards; it launches
only when disk >= 9 GiB and RAM >= 9 GiB hold for several consecutive
samples. No guard was weakened, no source file changed, and no fit, cell,
score, report, commit or push occurred.

## 2026-09-30 - Source `08751a39` quality retry also stopped on the RAM floor

The first retry attempt
([20260930_tensor_state_08751a39_guarded_retry1](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded_retry1/receipt.json))
launched after disk/RAM held at 278.891/13.203 GiB and stopped at 496.8
seconds when available RAM touched 3.987 GiB against the unchanged 4 GiB
active floor. Lint and strict mypy passed; pytest was interrupted near 40%.
The receipt is preserved write-once with no archive. Machine reconnaissance
found no stale project process: a 31.7 GiB host carries SentinelAgent.exe at
about 7.9 GiB plus browser, WSL and tooling, so available RAM oscillates
between roughly 3.5 and 13 GiB on a minutes cadence. A patient four-hour
watcher now fires a third fresh attempt directory only after disk >= 9 GiB
and RAM >= 10 GiB hold for five consecutive minutes. No guard was weakened;
no source file changed; no fit, cell, score, report, commit or push occurred.

## 2026-09-30 - Isolated-case implementation drafted and verified in runs/drafts

While the pinned quality attempts wait for shared RAM, the isolated-case
execution design was implemented as fingerprint-excluded drafts under
[runs/drafts/isolated_case](../runs/drafts/isolated_case/), so the pinned
`08751a39` scripts stay valid. The drafted supervision module adds an
optional `process_memory_limit_bytes` to both supervised runners: the Job
Object gains `JOB_OBJECT_LIMIT_PROCESS_MEMORY` with an exact query-back
echo check before any child is created, and peak process/job commit are
accumulated by polling while the child runs because Windows can reset the
peak counters once a job empties. The draft passes Ruff and strict mypy;
against the draft module, six new cap tests (validation refusals, a real
child under a generous cap with a reported bounded peak, an over-cap child
failing on commit, a tampered query-back refusing without creating a child,
absent peaks without a cap, and framed-runner peaks) and all 24 existing
supervision tests redirected to the draft pass.

The [drafted child entrypoint](../runs/drafts/isolated_case/run_cho_tensor_case_child.py)
performs exactly one `verify_cho_selected_source_state` call per process and
publishes a digest-only witness through an exclusive-create write; its
wrong-schema and existing-witness refusals were smoke-tested with real child
processes. The [drafted composer](../runs/drafts/isolated_case/phase2_cho_analysis_preparation.py)
gains `case_workspace`, a required positive `case_memory_limit_bytes`, a
supervision-capped `case_attempt_seconds`, and an injectable executor that
runs each case through the supervised child; any child failure, cap breach
or missing peak refuses the whole roster before score rows. It compiles and
passes Ruff; type checks and full tests run at application time because the
cap parameter exists only in the applied drafts. No source file changed and
no fit, cell, score, report, commit or push occurred.

## 2026-09-30 - Third quality stop; validation target advances to the applied source

The second retry
([20260930_tensor_state_08751a39_guarded_retry2](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded_retry2/receipt.json))
launched after disk/RAM held at 278.766/13.893 GiB and stopped at 526.6
seconds when available RAM touched 3.588 GiB. Three attempts now share one
signature: an external consumer periodically removes roughly 9 GiB of
available RAM for one to two minutes about every ten minutes, below the
unchanged 4 GiB active floor, defeating any 40-minute suite window. All
three receipts are preserved; source stayed stable and no archive exists
for `08751a39`. Following the `69d671ac` precedent, the validation target
now advances to the applied isolated-case source; the `08751a39` raw-audit
pass remains valid permanent evidence, and its control-inventory and
no-future wrappers will be repinned for the new source per the application
runbook. A resource sampler was started to identify the periodic consumer
for the owner, and an opportunistic quality watcher stays armed. No guard
was weakened; no fit, cell, score, report, commit or push occurred.

## 2026-09-30 - Isolated-case execution applied; source advances to `cb6eb49a`

The verified drafts were applied to source: both supervised runners gained
the query-back-verified `process_memory_limit_bytes` Job commit cap with
polled peak accumulation,
[scripts/run_cho_tensor_case_child.py](../scripts/run_cho_tensor_case_child.py)
now performs exactly one tensor-state verification per owned child process
with an exclusive-create digest witness, and the
[composer](../evaluation/phase2_cho_analysis_preparation.py) invokes it per
case through `run_cho_tensor_case_child` under a caller-pinned workspace,
memory cap and supervision-capped attempt seconds, refusing the whole roster
on any child failure, cap breach or missing measured peak. The applied
fingerprint is
`cb6eb49a2ff0ec04557e58b5729e2df8af19e3218f246d631915e709d26eda44`.

Gates against the applied source: Ruff and strict mypy pass on all changed
files; supervision, cap, child and transaction tests pass 51 with 1
symlink-privilege skip, including a real supervised child restoring a real
synthetic EEGNet publication end to end and executor refusals for a reused
workspace and a wrong state pin; the restore/store focused tests pass 39
tests and 29 subtests; the full composer suite passes 5 tests in 575
seconds with the executor boundary mocked at 1,040 synthetic cases. The
[exact-source raw audit](../runs/phase2/freeze_readiness/20260930_cb6eb49a_raw_source_readonly/receipt.json)
passed for 52 raw sources totaling 10,704,036,837 bytes with
`source_stable=true`, and the guarded full-quality attempt for this source
was launched into an observed quiet resource window. Measured peak-commit
per method kind, the control-inventory and no-future repins, and the new
quality receipt remain open. No fit, cell, score, report, commit or push
occurred.

## 2026-09-30 - Independent application audit: core verified, three minor issues queued

A read-only audit subagent checked the applied isolated-case source
`cb6eb49a` against the design document, the code and the receipts. Every
core claim verified with file:line evidence: the cap constant, flag
OR-ing, exact dual query-back echo and pre-creation refusal; cap
validation including bool rejection; in-loop peak accumulation with the
post-loop sample in `run_supervised`; the child's single-verification
protocol, refusals and exclusive-create witness; the executor's
supervised acceptance gates (exit 0, reason normal, measured peak present
and under cap, witness schema and case id); the composer's six-field
comparison, workspace/cap/attempt validation, strict-roster coverage and
all-or-nothing ordering before any score row; and the raw-audit receipt,
including an independent recomputation of both the fingerprint
(`cb6eb49a...`) and the 10,704,036,837-byte raw total. Three minor issues
were found and are queued for the next source batch, because editing source
now would break the running quality attempt's source-stability check: the
framed runner lacks the plan's post-loop peak sample (no functional loss;
its sole normal break path already observes an empty job), the plan's
"records the child's measured peak" is enforced but not yet recorded
(already disclosed as open, covered by the pending measurement probe and
future sweep receipt), and one stale draft sentence remains in the child
docstring. A leftover draft temp file was removed. No guard was weakened;
no fit, cell, score, report, commit or push occurred.

## 2026-09-30 - Source `cb6eb49a` full validation chain complete

In one quiet resource window (minimum available RAM 9.602 GiB throughout),
source `cb6eb49a2ff0ec04557e58b5729e2df8af19e3218f246d631915e709d26eda44`
completed every staged read-only validation step. The
[guarded full quality](../runs/phase2/quality_attempts/20260930_tensor_state_cb6eb49a_guarded/receipt.json)
passed with `status=pass`, `source_stable=true` and
`quality_bundle_verified=true`: Ruff, strict mypy and **916 passed tests,
3 skips and 1,041 subtests in 1,383 seconds**, archived at
[20260930_tensor_state_cb6eb49a.json](../runs/phase2/quality_history/20260930_tensor_state_cb6eb49a.json).
The [control inventory](../runs/phase2/control_refresh_checks/20260930_tensor_state_cb6eb49a/inventory_receipt.json)
found 0 valid / 45 missing records with no invalid or unexpected record. A
[peak-commit probe](../runs/phase2/case_memory_measurements/20260930_peak_commit_probe/receipt.json)
measured one real supervised child per method kind under the verified
8 GiB cap: eegnet 2.545, labram_full 2.621, labram_linear 2.628 and
labram_lora 2.667 GiB peak process commit, every child exiting 0 with the
cap respected; a production cap of about twice the 2.667 GiB maximum would
carry an explicit safety factor while staying far below the 6 GiB
host-before-case floor. The [no-future matched-control
check](../runs/phase2/gate_a_diagnostics/20260930_no_future_tensor_state_cb6eb49a/receipt.json)
raw-recomputed the proposed artifacts in 396 seconds and found 0 valid /
36 missing fits with no invalid record, `expected_incomplete=true`,
source and quality both stable, and no training. Three minor audit fixes
remain queued for the next source batch. Complete selection, the 5,253-step
selector decision, method-template ratification, the scientific freeze and
Gate A remain open. No real Cho fit, cell, score, report, commit or push
occurred.

## 2026-09-30 - Audit fixes applied; source advances to `4542cc11`

The three queued audit findings were fixed in one small batch: the child
entrypoint docstring no longer claims a draft location, the framed
supervisor now takes the plan's post-loop peak sample (normally reading
reset zeros at an empty job, catching only the still-running edge), and the
execution plan's item 3 now states that per-method measured peaks are
recorded by the measurement probe and the future sweep runner rather than
threaded through the composer's return value. Ruff, strict mypy and the
supervision-plus-cap tests (30 passed) cover the batch. The new source
`4542cc117917b9c577642ce4bf2beb052cbc8985394ab2ee0510b0f06dee3d18`
[passed its exact-source raw audit](../runs/phase2/freeze_readiness/20260930_4542cc11_raw_source_readonly/receipt.json)
(52 sources, 10,704,036,837 bytes) and its guarded full-quality attempt is
running in the continuing quiet window. No fit, cell, score, report, commit
or push occurred.

## 2026-09-30 - Source `4542cc11` full validation chain complete

Source `4542cc117917b9c577642ce4bf2beb052cbc8985394ab2ee0510b0f06dee3d18`
completed the full staged chain in one quiet window. The
[guarded full quality](../runs/phase2/quality_attempts/20260930_audit_fixes_4542cc11_guarded/receipt.json)
passed every completion field (916 passed, 3 skips, 1,041 subtests in
1,365 seconds; minimum available RAM 10.197 GiB) and archived
[20260930_audit_fixes_4542cc11.json](../runs/phase2/quality_history/20260930_audit_fixes_4542cc11.json).
The [control inventory](../runs/phase2/control_refresh_checks/20260930_audit_fixes_4542cc11/inventory_receipt.json)
again found 0 valid / 45 missing with no invalid or unexpected record, and
the [no-future check](../runs/phase2/gate_a_diagnostics/20260930_no_future_audit_fixes_4542cc11/receipt.json)
raw-recomputed the proposed artifacts (396 seconds) with 0 valid / 36
missing, `expected_incomplete=true`, and source and quality both stable.
The per-method peak-commit measurement stands at its `cb6eb49a` receipt;
the fix batch changed only a docstring and a parent-side post-loop sample
that cannot affect child memory. Every engineering prerequisite from the
isolated-case execution plan is now implemented and validated. Remaining
before any real sweep: owner decisions on the 5,253-step selector versus
the 256-step cap, the production cap ratification, method-template and
scientific-freeze ratification, control-fit scheduling, and Gate A. No
real Cho fit, cell, score, report, commit or push occurred.

## 2026-09-30 - Final chain audit passes; session documentation settled

A second read-only audit subagent verified the complete session evidence
with primary receipts and independent recomputation: the live fingerprint
`4542cc11...`, both raw-audit byte totals summed independently, the
quality archive hash matched against the receipt, the hash-pinned test log
(916 passed, 3 skipped, 1,041 subtests), the 0/45 and 0/36 inventories,
the peak-probe values with their disclosed earlier-source attribution, the
three preserved `08751a39` stop receipts, and every documentation claim.
Verdict AUDIT_PASS with two stale understatement bullets in the handoff's
lower sections, both corrected to the settled state afterward. A
[sweep-runner considerations note](phase2/cho_sweep_runner_considerations_20260930.md)
now frames the owner decisions that gate any real execution. Documentation
changed only; the source stayed `4542cc11`. No fit, cell, score, report,
commit or push occurred.

A same-source peak probe
([receipt](../runs/phase2/case_memory_measurements/20260930_peak_commit_probe_4542cc11/receipt.json))
then re-measured every method at `4542cc11`: eegnet 2.545, labram_full
2.627, labram_linear 2.628 and labram_lora 2.657 GiB, consistent with the
earlier `cb6eb49a` values, so the 5.5 GiB recommendation now rests on a
same-source receipt (2.07x factor). No fit, cell, score, report, commit or
push occurred.

## 2026-10-01 - Control-fit execution started under an auto-relaunch watcher

With the `4542cc11` validation chain complete, the 45 leakage-control fits
(9 gate-a shuffle and 36 pre-cue units across seeds 11/23/37/53, CUDA
device per the versioned configuration) were started through the versioned
[refresh script](../scripts/refresh_source_bound_controls.py). The first
launch deferred safely at the unchanged 10 GiB RAM startup guard (exit 2,
no training) under the morning workload; a patient watcher now relaunches
the resumable script whenever disk and RAM hold at 10/10 GiB, resuming
completed units by their saved records, and reports per-launch progress.
Because the fit context pins the source fingerprint before and during
every unit, no source file may change until the fits complete; the sweep
runner is being specified in documentation meanwhile. No scientific Cho
fit, cell, score, report, commit or push occurred.

The first watcher launch failed before any training: invoking the refresh
script in file mode leaves the project root off ``sys.path`` (the editable
install exposes the packaged roots but ``scripts`` resolves only as a
namespace package from the root), so its ``scripts.diagnose_profile_units``
import raised ``ModuleNotFoundError`` with zero units saved. The watcher was
stopped and relaunched with module-mode execution
(``python -B -m scripts.refresh_source_bound_controls``), whose ``--check-only``
inventory again reported 0 valid / 45 missing before any fit.

## 2026-10-01 - All 45 leakage-control fits completed and audited

The refreshed control run completed every unit at source `4542cc11`:
**45 valid records, zero missing, zero invalid and zero unexpected**, with
the versioned audit reporting `passed: true` and exit 0. The 36 pre-cue
units trained in seconds each on the CUDA device with early stopping (31
epochs at most; balanced accuracies near the four-class chance level,
which is the expected leakage-control signature), and the nine gate-a
shuffle units completed under the same guards. Each record carries its
exact rational metrics, signal identity, split, targets and the single
captured held-out prediction call. The next no-future matched-control fit
run started immediately in module mode. These are Gate A evidence inputs
only; they do not sign Gate A, ratify any freeze, or constitute a
scientific Cho result. No commit or push occurred.

## 2026-10-01 - Sweep orchestration drafted and verified; no-future bug fixed in source

Two parallel tracks advanced. First, the no-future matched-control fit run
exposed a real environment bug on its first-ever execution: the project
virtual environment's ``python.exe`` launcher inserts a trampoline process
between the supervisor and its spawned worker, so the worker's direct
``os.getppid()`` ownership check can never pass on this host. The check now
requires the lock's supervisor pid to appear anywhere on the worker's
ancestor chain, with regression tests for both the ancestor-acceptance and
unrelated-refusal paths; the full matched-control test file passes 15
tests, Ruff and strict mypy pass, and the changed source
`d6be4144f65d447026fd11c8988a79b2ec12f3c498bfeb00573c6a2f10c9b3d8` has a
prepared raw-audit wrapper (floor-gated) and guarded-quality attempt
directory behind a stability-gated chained watcher. Because control and
no-future evidence are source-bound, the completed 45 control records at
`4542cc11` will be re-fit at the settled source; each unit trains in
seconds.

Second, the sweep orchestration layer is drafted and verified in
[runs/drafts/sweep](../runs/drafts/sweep/): a persisted operator admission
record (schema, freshness, affirmative flag, explicit caps) combined with
live machine guards; roster iteration that skips already-measured cases,
advances past per-case failures with recorded reasons, and writes one
write-once receipt stating the exact completed/failed partition with
explicit no-claims fields. Six draft tests pass against the drafted module
and Ruff is clean. The production per-method case runner (selector to
evidence to adapter to publication to cell) is specified against verified
signatures and remains to be drafted with the CHO runner fixture as ground
truth. No scientific Cho fit, cell, score, report, commit or push occurred.

## 2026-10-01 - Execution-evidence milestone: fits run; two latent bugs found and fixed

The `d6be4144` chain completed: [guarded full
quality](../runs/phase2/quality_attempts/20261001_worker_ownership_d6be4144_guarded/receipt.json)
passed with 916 tests / 3 skips / 1,041 subtests (archived; minimum RAM
5.989 GiB), all 45 control fits re-ran at the settled source and the audit
reports 45 valid / zero missing or invalid, and the 36 no-future
matched-control fits ran for the first time in project history: every unit
saved under the supervised worker, subject means 0.219-0.253, overall mean
0.2451 against the 0.35 leakage limit. Executing these never-before-run
paths surfaced two latent source bugs, both now fixed with passing tests:
the venv launcher's trampoline breaks the worker's direct-parent ownership
check (fixed by requiring the supervisor pid anywhere on the worker's
ancestor chain), and the environment identity carried in-memory package
tuples that can never equal their own published JSON context, so the
matched-control audit would always flag the saved context (fixed by
emitting deduplicated JSON-native lists; canonical digests are unchanged).
Because control and no-future evidence are source-bound, the fit records
will be re-run once more at the next settled source, which also carries
the drafted sweep driver. The no-future receipt honestly reports
`complete=false` under the old source; all 36 fit records are individually
valid there. No scientific Cho fit, cell, score, report, commit or push
occurred.

## 2026-10-01 - Sweep driver applied to source; validation target `6523283e`

The Cho first-tranche sweep driver is applied and fully gated at source
`6523283e9be7b24bcdfadbcc5e434ea610d9c00b05e16224bec80108cd01c70f`:
[evaluation/phase2_cho_sweep.py](../evaluation/phase2_cho_sweep.py) carries
the persisted operator admission record (schema, freshness, affirmative
flag, explicit caps combined with live machine guards), the roster
orchestration that skips measured cases, advances past per-case failures
with recorded reasons and writes one write-once receipt with explicit
no-claims fields, and the production per-method case runner wiring the
real selectors, candidate materialization, evidence persistence, adapter
construction, cell identity, evidence verification, selected-source
publication and the admission-gated executor. The operator CLI
[scripts/run_cho_first_tranche.py](../scripts/run_cho_first_tranche.py)
admits nothing alone. Tests pass 7/7: six orchestration tests and one real
production wiring test at the full 52-subject cohort that runs a genuine
two-candidate selection (about six minutes), publishes a real selected
source, and separately asserts that the real evidence binder refuses the
run's own evidence with the exact documented refusal "complete Cho
selector work exceeds the declared gradient-step ceiling: 5253 > 256" —
the owner decision rendered concrete. Ruff and strict mypy pass on all
changed files. The exact-source raw audit passed (52 sources,
10,704,036,837 bytes) and the guarded full-quality attempt is running.
Control and no-future fits re-run at this source once quality passes. No
scientific Cho fit, cell, score, report, commit or push occurred.

## 2026-10-01 - Source `6523283e` full chain: quality, controls and a passing no-future inventory

The final source's chain completed end to end. Guarded full quality passed
with **925 tests, 3 skips and 1,041 subtests in 1,866 seconds** (minimum
available RAM 9.66 GiB), archived at
[20261001_sweep_driver_6523283e.json](../runs/phase2/quality_history/20261001_sweep_driver_6523283e.json).
All 45 control fits re-ran and the audit reports 45 valid / zero missing
or invalid. The 36 no-future matched-control fits re-ran and, with the
environment-identity fix, the inventory now reports **complete=true,
passed=true, 36 valid records, subject means 0.234-0.253 and overall mean
0.2451 against the 0.35 leakage limit** — the first complete no-future
inventory in the project's history. Every engineering artifact needed
before the real Cho sweep now exists at one settled, fully validated
source; what remains are owner decisions: the 5,253-step selector ceiling,
the persisted admission record, the 5.5 GiB analysis cap, the method
template and scientific freeze, and Gate A. No scientific Cho fit, cell,
score, report, commit or push occurred.

## 2026-10-01 - Independent day-chain audit: all substance passes; doc gaps fixed

A read-only audit subagent verified the full two-day milestone chain with
primary evidence and a live fingerprint recomputation. Every substantive
claim passed: the applied sweep driver's admission, resume, failure-advance
and write-once receipt semantics; the seven sweep tests including the real
52-subject selection and the exact `5253 > 256` binder refusal; the
`6523283e` raw-audit and quality receipts (925/3/1,041 archived); the 45
control fits and the complete, passing 36-record no-future inventory (mean
0.2451); the strictness of every guard including the selector clamp,
worker ancestor-ownership and environment identity; and the scientific
boundary (no tranche fit, cell or score anywhere, no commit or push, no
receipt of the sweep schema in runs). Four documentation-consistency gaps
were the only findings — a stale skip count, an incomplete decision list,
and two stale contradicting handoff bullets — all corrected immediately
afterward; documentation only, with the source fingerprint unchanged. The
one precision note (the production test also stubs `run_case` as a
documented argument-observation seam, beyond the three ceiling mocks) is
recorded here for accuracy.

## 2026-10-01 - Owner directs the next step; execution-enabling decisions delegated

After the milestone summary listing the open owner decisions, the owner
instructed "move to the next step". Acting on that instruction, this
session proceeds with the execution-enabling subset, delegated and recorded
here: the selector gradient-step ceiling moves from the hard-coded
engineering value 256 into a committed configuration pinned at exactly
5,253 — the arithmetic requirement of the proposed, still-unratified
minimal two-candidate template over the full 52-subject cohort (2
candidates x 51 leave-one-source-out folds x 50 source subjects x 1 step
plus finals) — admitting exactly the declared work and nothing more; the
5.5 GiB per-case analysis memory cap is ratified in the pinned sweep
configuration (2.07x over the measured 2.657 GiB peak); and the persisted
sweep admission record is written with the owner as operator and this
delegated session noted. Gate A is NOT signed and the scientific freeze
and method template remain unratified: execution produces engineering
evidence only, exactly as before. The first real tranche case follows once
the ceiling configuration passes its own gates and pin cycle.

## 2026-10-01 - Selector ceiling committed at the declared 5,253 steps

The delegated owner decision is implemented as committed configuration:
[configs/phase2/selection_ceiling.toml](../configs/phase2/selection_ceiling.toml)
pins `maximum_gradient_steps = 5253`, exactly the arithmetic requirement of
the proposed minimal two-candidate template over the full cohort (2
candidates x 51 leave-one-source-out folds x 50 source subjects plus
finals), and both source selectors and the selection-evidence binder now
enforce the committed value instead of the former hard-coded 256, which
was sized for smoke fixtures. A committed
[cho_sweep.toml](../configs/phase2/cho_sweep.toml) ratifies the 5.5 GiB
per-case analysis memory cap (2.07x over the measured 2.657 GiB peak) and
the 480-second per-case analysis attempt window. The persisted sweep
admission record is written under runs/ with the owner as operator and the
delegation noted. Tests updated faithfully: refusal boundaries move to
ceiling+1, a new binder test asserts the committed ceiling admits the
declared complete Cho work, the sweep production test now runs with no
verification mocks and asserts the real binder admits the runner's own
evidence, and every fixture world carries the committed ceiling file. All
affected suites pass (53 tests, 59 subtests), Ruff and strict mypy pass.
An earlier full-quality attempt at an intermediate fingerprint honestly
recorded nine fixture-driven failures before these fixes; its receipt is
preserved. The exact-source raw audit passed at the final fingerprint
`6566e348e470edcc40d8171e86f24a5453c913357bb0bfefa28a64ee4b60e91d` and its
guarded quality attempt is running. The first real tranche case follows.
No commit or push occurred.

The first guarded quality attempt at this fingerprint stopped honestly on
the unchanged 4 GiB active RAM floor ten minutes in (evening dips), with
its write-once receipt preserved; a patient stability-gated retry is
armed. The nine earlier fixture failures and this stop are both ordinary
honest guard records, not weakened checks.

## 1 October 2026, 16:36 UTC: 30-hour engineering session and baseline reconciliation

The user authorized 30 hours of autonomous project work with docs/handoff
updates and independent audits at every major step, plus coordination with
other agents. The deadline is 2 October 22:36 UTC. Engineering authorization
does not sign Gate A or ratify the scientific freeze.

The baseline source was independently recomputed as `6566e348` over 419
files. The latest raw audit passed; latest quality stopped at about 40% on
3.9508 GiB available RAM. The prior source's 925-test pass and 45/36 controls
are retained as historical evidence only. Status documents had incorrectly
continued naming `6523283e` or `08751a39` and describing ceiling/admission
decisions as absent. Their leading sections now distinguish current work
from historical snapshots. Cho's ceiling is now 5,253; engineering admission
and the 5.5 GiB analysis-cap configuration exist. No completed real Cho
evaluation cell or first-case receipt was found.

Pro2 confirmed its active CPU-gate ownership; heavy pro3 work will await
coordinated release. Only the verified pro3 stale quality watcher
(PIDs 49248/55072, pinned to 6566e348) was stopped after ownership checking,
preventing it from launching obsolete checks during source edits. Its
unstarted retry directory and every earlier receipt remain untouched.
The retirement evidence and session ledger are under `runs/coordination/`.

Workers have nonoverlapping source ownership for sweep integration/resume
repairs and supervised CLI execution. A separate read-only auditor reviews
each milestone. Focused/full tests, current-source controls and any real fit
remain pending coordinated resources; no verification pass is invented.

## 1 October 2026: M1 sweep repair, static audit passed and runtime pending

The sweep now passes an empty asset map for EEGNet through the actual target
preclaim gate. Resume requires matching source/Git/environment, method and
partition identities, current successful claim and complete selected-source
publication; the recipe is derived independently rather than self-pinned
from the manifest. Per-case and post-case source/configuration/admission,
resource and deadline checks precede completed accounting. Shared refusals
halt the roster, while receipts retain honest partial/quarantined outcomes
and exact parsed admission-file hashes.

Independent review caught premature completed accounting after drift,
missing source-resource stop classifications and insufficient historical
claim provenance; each was corrected. Scoped Ruff and strict mypy pass.
Focused Torch-import tests and the existing real synthetic full-selection
test await coordinated resources; no runtime verification is claimed yet.
`runs/coordination/20261001_m1_static_audit.json` pins the reviewed files.
Physical isolation remains the caller's responsibility: the legacy
first-case wrapper must not run. Actual engineering work will use M2's
whole-case supervised staged-child/parent-publication path after validation.

## 1 October 2026: M1b exact-input snapshot optimization, training verification pending

The performance review counted 5,253 repeated Cho Profile A loader calls
per complete EEGNet selection and a roughly 1.26 GiB retained source signal
working set. The selector now owns a lazy source-only snapshot cache bounded
to 1.5 GiB of signals plus labels. It stores immutable bytes-backed views,
shares them with private inner validation, retains pins across LRU eviction,
and unconditionally hashes every touched artifact/base/threshold file before
public evidence returns. The outer target is never prefetched. Existing
standalone loaders, models, source/support roles, initialization, sampling,
SGD updates and evidence fields remain unchanged.

Nine NumPy-only tests, scoped Ruff and focused mypy passed. Independent
static review found no blocking issue, but transient loader memory still
needs the whole-case process cap and exact cached/uncached training/evidence
equality remains unrun. No speedup, full-case runtime or full-source quality
pass is claimed. Shared resource ownership continues to defer heavy checks.

## 1 October 2026, 17:23 UTC: M3a quality-tooling audit and resource hold

The reusable quality runner and standalone verifier now reject surviving
owned descendants after normal parent exit. Passing archives are checked
again after creation; a later failure quarantines only the current attempt's
archive and preserves its hash. Current-pointer rollback requires the
attempt's exact bytes, leaving another writer's status intact. Independent
review and 20 lightweight tests passed, including real orphan cleanup and
post-archive log corruption, source drift and cancellation. These checks
validate the tooling, not the whole source tree. The optional receipt-digest
hardening was statically reviewed; a final focused rerun is pending.

RAM fell to 3.191 GiB at 17:21 UTC. Further Python checks were paused and
pro2 notified. Its active gate retains the heavy-work lease; it offered the
first 60-minute pro3 CPU validation window after explicit terminal release.
Neither the estimate nor elapsed time authorizes compute. Full quality keeps
the 10 GiB startup threshold and 4 GiB active floor.

A second old-source auto-retry watcher, PIDs 53788/32412, was discovered.
The exact pro3 executable, unique obsolete retry command, parentage and
creation times were verified before stopping only that pair. Its attempt
remains unstarted and unchanged. The originating ZCode app and all pro2
processes were left running. A separate retirement receipt records the
observed absence of the two target processes. No scientific claim changed.

## 1 October 2026, 17:38 UTC: M2 supervised CLI static audit accepted

The actual staged parent/child execution path has passed final independent
static review. Parent acceptance now binds complete target A/B attestations
and query-label totals, retains hashes of the exact verified proposal/cell
buffers, strictly checks current claims, re-pins admission/configuration/source
after resource checks, and enforces UTC and monotonic deadlines. Setup/expiry
paths retain terminal receipts; ordinary escaped failures link to the recorder.
Durable accepted/intent/success evidence remains a deliberate recovery case
rather than an ordinary retryable failure. Implicit CLI resume is refused.

Prepared tests cross the actual parent acceptance callback and genuine recorder
lifecycle, include resealed target forgeries and late admission revocation,
and retain two real Windows Job checks. These tests and latest lint/type checks
have not run because the shared-machine resource hold remains active. The
reviewed files are pinned in `runs/coordination/20261001_m2_static_audit.json`.
All source edits are frozen pending runtime validation. The explicit initial
6 GiB per-process execution probe remains uncalibrated, with separate measured
Job peak; no production training cap or scientific approval is inferred.

A separate ZCode session regenerated the obsolete baseline watcher a third
time. Its new file and processes were observed read-only. The shared agent
coordination notice requests a hold; user pause/relay clarification is pending
because the available thread tools cannot contact ZCode. No new source-quality
pass, completed real case, commit, push, freeze or Gate A sign-off is claimed.

## 1 October 2026, 17:49 UTC: M1c narrow LaBraM input snapshot authorized within session

Read-only analysis identified 5,151 source plus 102 validation Profile B loads
per complete two-candidate Cho case. Existing raw-file metadata and two hashes
per load imply about 1.97 TiB of raw hashing alone for outer subject 01; its
51 original source B signal arrays total about 1.968 GiB. These are static
counts, not current timing or memory measurements.

Within the user's engineering session, a worker now owns a private lazy
source-fit-only Cho 60 Hz cache bounded to 2 GiB. It will preserve immutable
signals/labels, all source exclusions, model/device/RNG/update/history and
contract semantics, exact pinned input identities and unconditional final
hash verification. Ordinary validation loaders remain unchanged to keep the
role/episode boundary small. Arrays must be cleared before publication/target
and after failures. Implementation review and exact cached/uncached tests are
mandatory acceptance work; no speedup or 600-second completion is inferred.
CLI, quality tooling, Profile A cache and sweep files remain frozen. Full
quality/control pins will be generated only after this source work settles.

## 1 October 2026, 18:05 UTC: M1c source-input cache static audit accepted

The three owned M1c files passed independent static review with no blocking
finding; exact hashes are retained in `runs/coordination/20261001_m1c_static_audit.json`.
The cache calls the original verified loader on misses, retains only immutable
source episode signals/labels within 2 GiB, verifies all touched inputs including
evicted/bypassed files before public evidence, and clears arrays on success and
failure before the selected winner reaches target execution. Validation loading,
owned batch construction and training/evidence/device semantics remain unchanged.
The static binding-call count becomes 51 cold source plus 102 normal validation
loads, with an additional final full verification stream.

Ten NumPy and six lazy-Torch regression tests are authored. None has run;
latest lint/type checks and all runtime/peak/speed measurements remain pending
the shared-machine lease. All assigned code is now frozen. At 18:04 UTC free RAM
was 1.699 GiB. Pro2 reports 36/45 partitions of its active gate accepted; it has
not released the heavy-work lease. Existing resource floors remain unchanged.

## 1 October 2026, 19:15 UTC: M3b quality lease deadline static audit accepted

The guarded quality runner's fixed 4,200-second ceiling exceeded the offered
60-minute CPU lease. Within the user's engineering session, a worker added
an optional finite positive shorter wall limit that cannot exceed 4,200.
Prelaunch, active monitoring and final acceptance use the effective limit;
receipts retain effective and policy limits separately. Independent static
review accepted the two file hashes in
`runs/coordination/20261001_m3b_quality_lease_audit.json`.

Authored coverage includes startup and active expiry, invalid caps/CLI defaults,
and final expiry with quarantine plus exact prior-pointer restoration or removal
of a new pointer. All 25 focused test methods and latest lint/type checks remain
unrun. The earlier 20-test M3a pass is historical tooling evidence. The next
quality launch will clip its cap to the confirmed lease and overall deadline,
reserving 60 seconds for cleanup/receipts. Historical full quality took about
31 minutes; that observation does not predict this version's runtime.

All assigned source is frozen again. At 19:13 UTC available RAM was 2.226 GiB,
and pro2's saved evidence showed 41/45 accepted gate partitions without an
explicit lease release. No Python checks, training, new full-quality pass,
real cell, commit, push or scientific sign-off occurred in this milestone.
An independently reviewed `AGENTS.md` now points future sessions to the current
handoff and shared-machine coordination; the separate ZCode relay remains pending.

## 1 October 2026, 19:28 UTC: latest native scoped lint passes

Pro2 expressly permitted a tiny read-only standalone Rust Ruff check without
Python during the low-RAM hold. The first 17-file check found six line-length
errors and one import-layout error in two CLI files. Their owning worker made
only the seven layout corrections; an independent reviewer confirmed unchanged
behavior, APIs, literals and test logic, and unchanged other CLI files.
Updated hashes are in `runs/coordination/20261001_m2_lint_cosmetic_audit.json`.

The second 17-file native check passed in 0.1085 seconds with stable before/after
file hashes. Both attempts are retained under `runs/phase2/focused_validation/`.
No Python process was launched and no heavy lease activated. Available RAM
was 1.954 GiB after the check. Type checks, focused tests, exact-source full
quality, controls and the first real case remain pending. All source is frozen.

## 1 October 2026, 20:02 UTC: M3c canonical source identity verified

Pro2 permitted a single controlled standard-library-only source pin under a
10-second limit, without opening a native quiet or heavy compute window.
The isolated interpreter loaded `core/provenance.py` directly, avoiding the
core package initializer, NumPy and Torch. It completed in 0.8851 seconds,
exit zero; owned PID 55320 exited. The canonical before/manifest/after hashes
agree on `9d32cb1a460081b53f870a762a12e83d9abe95e59124a159f1803de6981d52e1`.

Independent PowerShell audit enumerated and hashed all 430 current files and
reconstructed the same LF-joined manifest digest, finding no extras, missing
paths or mismatches. All 17 native Ruff pins remained unchanged. Evidence is
retained in `runs/coordination/source_pins/20261001T195150739Z/` and
`runs/coordination/20261001_m3c_source_pin_audit.json`. Original receipts remain
unchanged; the audit clarifies an empty-import-list serialization difference.

This verifies source identity only. Current raw/full quality/controls and the
first real case remain pending, as do latest type/runtime checks. The native
Git HEAD is still `e378dfd5f65e53b7ae7da62c778e829b60c61b98`; no commit or push
was made. Available RAM was 1.827 GiB at 20:02 UTC and the heavy CPU lease is
still inactive pending explicit peer release and recovery to the 10 GiB floor.

## 1 October 2026, 20:33 UTC: M3d current raw verifier preparation reviewed

A fresh operational verifier under
`runs/phase2/freeze_readiness/20261001_9d32cb1a_raw_source_readonly/`
changes only the baseline script's expected source literal and mismatch label.
Independent PowerShell review verified byte identity after reversing those two
replacements, correct root/output paths, unchanged base/route/resource guards,
the native lint log pin, and all 430 current source-file pins. Its write-once
audit is `runs/coordination/20261001_m3d_raw_preparation_audit.json`.

This is preparation evidence. No Python/raw check ran, no current raw receipt
exists and no current quality/control/real-cell pass is inferred. Execution
requires explicit peer CPU release and two fresh 10 GiB startup samples;
the retained internal historical 6 GiB guard does not weaken that requirement.
At 20:28 UTC RAM was 1.615 GiB. The separately prepared 25-test component scope
requires explicit component release, two 5 GiB samples, a 4 GiB active floor,
a verified 1 GiB aggregate private-Job cap and a 60-second outer deadline.
Its numerical/psutil imports are disclosed; it is not a standard-library-only
suite. No component launch or heavy-work lease activation occurred.

## 1 October 2026, 21:10 UTC: M4a first-case readiness audited

The operational readiness report and independent audit agree that the first
EEGNet/subject_01/seed_11 probe is not ready to launch. Eight static file pins,
four canonical method digests and the roster agree. EEGNet skips LaBraM tensor
loading but retains all 52 A/B route validations and the shared GPU inventory
admission. The report is `runs/coordination/20261001_first_case_static_readiness.json`;
the audit is `runs/coordination/20261001_first_case_readiness_audit.json`.

Local execution clocks begin after parent Torch/pin setup, so a concrete audited
outer supervisor must cover parent startup, all descendants and canonical
publication under the absolute peer/global deadline and an explicit parent/
child memory policy. Current raw/full quality/45/36, a measured case environment
pin and explicit heavy release remain pending. Durable partial publication
requires deliberate recovery. No source patch, Python, fit or real case ran.

The case environment binds Torch thread count/deterministic mode; the control
context instead binds OS thread variables, packages and GPU identity. The
36-control context also binds exact quality-status bytes. The proposed first
probe uses Torch API thread count 1 and preserves verified control environment
variables. This engineering preparation grants no scientific ratification.

## 1 October 2026, 21:18 UTC: M3e bounded component preparation accepted

Independent static review accepted the operational parent, fixed 25-test child,
native PowerShell launcher and selected-runtime pin mirror. Root transcribed
the review and exact hashes into
`runs/coordination/20261001_m3e_component_supervision_audit.json`. Initial review
findings corrected native handle-close reporting, one-use attempt binding,
receipt timing and the watchdog's creation-to-assignment cleanup gap. Extended
Windows process creation now attaches the already-capped private Job atomically;
membership and attribute cleanup are verified before resume. Microsoft API/SDK
details were checked with the BrowserOS neo skill and retained in the operational
primary-source record. Fingerprinted project source remains `9d32cb1a`.

Native Ruff passes both operational Python files; both PowerShell files parse
without errors. Native default-plan and runtime preparation completed without
Python. Independent review rehashed all 24 runtime files and reconstructed
their canonical digest. Selected runtime pins and sampled peaks have explicit
limits; neither is a full binary inventory or continuous peak measurement.

The held proposal retains null window/confirmation fields. No Python plan,
component test or heavy-work lease ran. Actual launch still requires explicit
component release, two fresh 5 GiB samples, active 4 GiB/20 GiB floors, whole-Job
1 GiB aggregate cap and a 60-second outer limit. Internal receipts remain
provisional until root observes physical native-launcher completion inside that
limit and the release/global window. Full quality and real-case admission are
separate. Whole-CLI first-case supervision is now being prepared independently;
no scientific freeze, Gate A, commit or push is implied.

## 1 October 2026, 21:30 UTC: documentation audit and continued compute hold

The independent M3e/M4a documentation audit reconciled operational/runtime
pins, current Ruff pins and active links. It corrected the M2 description:
the existing Job contains the staged child, while parent initialization precedes
the local timers and canonical promotion remains outside that Job. Local
deadline checks still guard promotion; whole-CLI containment is being prepared.
The preserved audit is `runs/coordination/20261001_m3e_documentation_audit.json`.

The later read-only coordination refresh pins peer urgent hold005 and its
isolated-component refusal review in
`runs/coordination/20261001_resource_hold_2131.json`. No exclusive executor
acknowledgement or pro3 release is present. Peer inspector-only results and a
worker fixture setup failure do not certify pro3. RAM was 1.847 GiB at 21:30 UTC;
both startup floors remain unmet. Direct thread messaging tools are absent in
the current context, so shared records remain the coordination path. No Python,
component validation, training, cleanup or peer-file mutation occurred.

## 1 October 2026, 22:05 UTC: M4b whole-CLI preparation statically accepted

Separate execution and native workers completed five operational files under
`runs/coordination/first_case_supervision/`. Independent reviews accepted Job
boundaries and input/control evidence; root reviewed the native launcher.
The preserved audit is
`runs/coordination/20261001_m4b_first_case_supervision_audit_v2.json`.
Its first version remains preserved; v2 clarifies that native checker processes
ran while no supervised Python/CLI workload launched.

Audit fixes moved Git capture inside the capped child, covered late/unknown
publication recovery, bound control-unit hashes to validated snapshots and
actual context files, and retained the executed writer receipt. Training fields
distinguish actual engineering invocation/completion from unsigned formal
scientific scope. The copied atomic adapter reverses exactly to its reviewed
origin after explicit cap/diagnostic and nonexecuting comment substitutions.

Native lint, both PowerShell parsers/default plan and a fresh 33-file runtime
rehash pass without Python. The 120-second environment-only and 600-second
fixed-case modes remain proposals requiring matching heavy release, two fresh
10 GiB samples, active 4 GiB/20 GiB floors, 6 GiB process/aggregate caps and root
physical-exit observation. Windows nesting/cleanup, actual environment, current
raw/full-quality/45/36 and a real case remain unverified. Gate cost is unmeasured;
insufficient remaining time refuses before fitting without extending limits.
Source/component files remain frozen and unchanged. No Gate A/freeze signature,
commit or push occurred.

## 1 October 2026, 22:49 UTC: M4c Windows qualification preparation statically accepted

Four new operational files under `runs/coordination/first_case_windows_qualification/`
are frozen after independent Job and release/witness reviews. The preserved
audit is `runs/coordination/20261001_m4c_windows_qualification_audit.json`.
Root native Ruff passed in 0.1145 seconds; PowerShell parsing and the default
plan passed. The native worker rehashed the existing 33 selected runtime pins
without Python. The M4b adapter, component wrappers and project source are
unchanged. Native checker processes ran; no supervised Python workload did.

Review corrected primitive result-field names, isolated startup checks,
observer restoration, loop callback bindings and cancellation evidence.
Immediately before exact-private-Job termination, a bounded native PID query
must contain both actual ready Python PIDs and their created-process identities,
with venv parent links and immutable ready-file hashes. Observation failures
still delegate cleanup and refuse acceptance. Cleanup must establish an empty
Job and closed owned handles. Microsoft primary documentation confirmed the
pointer-sized PID-list ABI. No actual Windows scenario has run.

The proposed 120-second scope includes normal exit, six-second deadline
cancellation and optional 64 MiB process-cap denial of a 96 MiB allocation.
It requires new explicit mode-specific heavy release, two fresh 10 GiB RAM
samples, active 4 GiB/20 GiB floors, 6 GiB process/aggregate outer containment
and independent root physical-exit acceptance. No extension or retry is implied.
Deadline cancellation is not UI Ctrl-C; small-cap denial does not ratify training
capacity. Current quality/raw/45/36, actual environment and a real case remain
pending. Gate A/freeze are unsigned.

Peer Step009/coordination006 still hold pro3 leases; local ACK006 confirms only
this root's hold. RAM was 0.9733 GiB at 22:34 UTC. Known obsolete watcher IDs
were absent, and no absolute-pro3 Python watcher match was observed at 22:48.
No process was stopped and no whole-host quiet or release follows.

**Preserved separate-actor snapshot below:** it describes baseline `6566e348`
and reports an overnight watcher. Its claims do not certify current `9d32cb1a`,
activate compute, establish a current watcher identity or authorize an obsolete
retry. The active coordination/handoff and fresh receipts govern new work.
Its text is retained as another actor's snapshot.

## 2026-10-01/02 - Overnight wait for the execution-enabled quality window

The final execution-enabled source
`6566e348e470edcc40d8171e86f24a5453c913357bb0bfefa28a64ee4b60e91d` has its
exact-source raw audit passed, all affected suites green, the committed
ceiling and sweep configuration landed, the persisted admission record
written and the first-real-case driver prepared. Its guarded full quality
stopped honestly on the unchanged 4 GiB active RAM floor ten minutes into
the first attempt, and a five-hour stability watcher then timed out
without a single 10 GiB sample: the shared host has been pinned at 1-3
GiB available through the night by SentinelAgent (about 8.5 GiB), a
Docker backend (about 3-4 GiB), WSL and other agents' sessions — roughly
16 GiB of external consumption that no project guard may preempt. A
twelve-hour overnight watcher is armed to fire the preserved retry the
moment a stable window opens; every downstream step (control and
no-future fits at this source, then the first real Cho tranche case) is
staged behind it. No guard was weakened and no fit, cell, score, report,
commit or push occurred.

## 3 October 2026, 05:49 UTC: original session closed; audit and handoff only

The original 30-hour window ended 2 October at 22:36:13 UTC. The user
explicitly selected existing-session audit and handoff only, with no renewed
execution interval. The original engineering outcome remains incomplete.
Documentation now leads with this closeout scope and retains earlier blocked,
source and separate-actor snapshots as history.

The new native source drift audit at
`runs/coordination/20261003_source_drift_audit_0543.json` found 430/430 frozen
file hashes and selected paths unchanged, zero additions/removals/errors and
17/17 unchanged native lint pins. It computed no new canonical aggregate and
supplies no runtime certification. The fresh scoped inventory at
`runs/coordination/20261003_runtime_readiness_inventory_0542.json` found no new
current-source validation or real-case receipt. Current quality status remains
failed for `25ab4f3d`; current raw/component/qualification/supervisor execution
and the default recorder root remain absent in the stated scope.

The obsolete retry script was edited by another actor on 2 October at
04:49:55 UTC to a four-hour watcher. Its bytes are preserved; file modification
does not prove a process launch or confer execution authority. Root's narrow
Python CIM query at 05:47:36 UTC found no matching absolute-pro3/obsolete-watcher
command line or Python PID62728. Available RAM was 8.5027 GiB and D: free space
273.1848 GiB. These are bounded observations, not whole-host quiet or admission.
No process was stopped and no Python/test/Job/fit/raw/weight workload launched.

Native Codex thread tools are available again. Pro2 directly acknowledged
closeout-only scope, no renewed interval, no new pro3 lease/request and continuing
Canonical/Pro3 holds. Its keeper/monitor restoration remains peer-owned and is
not native quiet evidence. The root-owned transcript is
`runs/coordination/session_closeout_20261003/peer_closeout_message.md`.
The original ledger is preserved byte-for-byte as
`runs/coordination/session_closeout_20261003/session_ledger_before_closeout.json`.

The three operational wrapper families' global deadline and the old 24-hour
engineering admission have expired. Frozen reviewed versions were not retimed.
Future execution needs fresh owner scope/window, ownership/release, resource
samples, matching reviewed operational versions/runtime pins and admission.
Focused/type/raw/full quality, Windows qualification, matching45/36 controls,
environment evidence and a first accepted real case remain pending. Gate A and
the experiment freeze remain unsigned. No commit or push occurred.

The independent closeout documentation review subsequently accepted the bounded
reconciliation:10 root evidence pins,22 frozen artifacts,22 active links and12
readable JSON records. Its immutable receipt is
`runs/coordination/session_closeout_20261003/documentation_audit.json`.
The user's approved audit/handoff scope is closed; the original engineering
objective remains incomplete. The closeout receipt records that distinction.

After that review snapshot, pro2 reported its owner's separate continuation,
initially static/docs with isolated standard-library validation planned but
not launched at message time. This renews no pro3 scope, expired lease or native
quiet. Root replied that no active heavy/Python/test/Job/fit workload is owned
here and retained audit-only scope. The separate attributed transcript is
`runs/coordination/session_closeout_20261003/peer_continuation_message.md`.

## 3 October 2026, 07:00 UTC: next step prepared; startup RAM refusal

The user authorized moving to the next engineering step after the closeout.
Root selected one guarded-quality25 component check and an internal 08:18:47 UTC
phase cap, without inventing a new owner deadline or 30-hour session. A new
operational copy changes exactly two deadline literals; independent review
accepted the preparation, identical child/runtime-mirror bytes and 24 selected
runtime pins. Original frozen wrappers, source and historical receipts remain
preserved. Native preparation checks supply no executed component result.

Peer release001 granted 06:40:42.6796148–06:50:42.6796148 UTC for this narrow
scope. Root's unchanged 5 GiB startup guard refused before creating any
consumable release, attempt, launcher, Python process or Job. The original
failed sample was not persisted; the separately recorded 06:43:04 observation
was 3.7708 GiB. The independent refusal audit and window closeout are under
`runs/coordination/next_step_20261003/`. The grant expired without entry and
cannot be replayed; peer was notified of no-entry closure.

Native RAM was 3.1428 GiB at 07:00:18 UTC. The user answered the proposed shared
WSL cache reclaim with "wait until it frees or work with what you have." No
cache change, process stop, service shutdown or guard lowering was performed.
Light work continues while awaiting sufficient memory. Any actual component
execution requires two fresh startup samples and a new distinct peer grant.
No current-source component/full-quality pass, fit, real case or scientific
approval is claimed. Gate A and the scientific freeze remain unsigned.

## 3 October 2026, 08:20 UTC: bounded component phase ended without entry

The native RAM monitor recorded 60 samples and exited normally after two
qualifying observations at 07:53:01/02 UTC (6.6530/6.8221 GiB). This supplied
readiness observations, not launch admission. Root made no shared cache,
service or unrelated process change. Peer granted a distinct window002 ending
08:06 UTC. The reviewed native root admission helper completed with exit 1 at
08:05:10 UTC: less than its unchanged 65-second reserve remained, so it refused
before sampling RAM or creating a consumable release, attempt, launcher or
Python process. The refusal and window closeout preserve this time outcome.

Candidate003 and a helper copy changing only identity/path/pin literals passed
independent static review. Reversing those substitutions reproduces the accepted
predecessor bytes. RAM fell below startup again; a second native reader exited
normally with eight samples, all below 5 GiB. The late conditional003 request
was cancelled when insufficient time remained. Neither helper003 nor any
Python/test/Job/fit launched. All receipts, refused requests and frozen versions
are preserved under `runs/coordination/next_step_20261003/`.

The root-selected operational cap elapsed at 08:18:47 UTC. The phase closeout
records **incomplete runtime validation**, unchanged operation/quality pins and
ten absent execution paths. This is not completion of the next-step engineering
objective. The user's current authorization persists; it does not renew elapsed
operational deadlines or peer grants. Future execution needs a fresh reviewed
bounded operational version, sufficient RAM and actual scope-specific release.
The quality pointer remains failed for older source `25ab4f3d`; current component,
full quality, matching controls and the first accepted real case remain pending.
Gate A and the scientific freeze remain unsigned. No commit or push occurred.

## 3 October 2026, 08:50 UTC: current bounded component preparation accepted

The user's next-step authorization continues, including the instruction to wait
for memory or work with available resources. Root selected a second bounded
component phase in
`runs/coordination/next_step_20261003_phase2/phase_plan.json`, with an internal
10:30 UTC operational cap. This cap is neither an owner expiry nor a compute
lease and does not renew the original 30-hour session or prior grants.

The v3 operational package is sealed. Independent delta review accepted its
preparation as `ACCEPTED_STATIC_PREPARATION_ONLY` in
`runs/coordination/next_step_20261003_phase2/preparation_audit.json`
(SHA256 `ca618f71a811a79e216e450c756aef03d7163b62fbe112da95636e501561b06a`).
The new held candidate004 was accepted as `ACCEPTED_STATIC_HELD_CANDIDATE` in
`runs/coordination/next_step_20261003_phase2/release_candidate_004_audit.json`
(SHA256 `db0db6408622365625d77a6c404ec02ffd25f6a15b94bf1a0d5e4b59dba2de9b`).
The native admission helper was accepted as `ACCEPTED_STATIC_PREPARATION` in
`runs/coordination/next_step_20261003_phase2/root_admission_004_review.json`
(SHA256 `0ba66e05d3bd5bd5c688bb5cd7dca140eb33e672afde225fae0a6a86e3a5670b`).
All three reviews have no blocking findings. They preserve prior algorithm
reviews and evidence rather than claiming executed Windows interoperability.

At this checkpoint all preparation is complete, but no actual compute lease,
test entry or runtime pass is established. Candidate004 remains held with null
window and confirmation. A new affirmative peer grant, two fresh 5 GiB startup
samples, the 4 GiB active and 20 GiB disk floors, a 1 GiB process/aggregate Job
cap and root-observed physical completion within 60 seconds remain required.
Preparation does not certify full quality, controls, raw inputs or a real Cho
case. Shared cache and services were not altered for this step; implementation,
prior operational versions and historical closeout evidence are preserved.
Gate A and the scientific freeze remain unsigned. No commit or push occurred.

## 3 October 2026, 09:16 UTC: component004 executed; independent acceptance pending

The admitted component004 executed all 25 guarded-quality tests, with zero
errors, failures or skips. The root's complete physical tool call `fe036f`
exited with code 0 between 09:16:30.935 and 09:16:40.299 UTC, an external interval of
9.364 seconds within the 60-second cap and the actual peer window. Its immutable
witness is
`runs/coordination/next_step_20261003_phase2/root_execution_witness_004.json`
(SHA256 `a40f3b1af72edde224fd52830d0493b68adea2873b22291d49ee4be9d925cc30`).
Independent acceptance is pending; the child, parent, completion and native
launcher receipts remain provisional.

Native evidence records atomic assignment to the private Job, queried 1 GiB
process and aggregate limits, verified launcher membership, an empty Job before
close, observed root exit and closed Job/process/thread handles. The numerical
test interpreter reports PID 75152 while the created venv launcher is PID 63016.
That precise launcher-to-interpreter edge is inferred rather than directly
recorded. The retained contract supports bounded review, and the inference
must remain explicit; this result does not establish the broader nested-Job
Windows qualification or whole-case supervision.

Source `9d32cb1a` and selected runtime `a439111c` remained stable. The current
quality pointer is unchanged and still failed for older `25ab4f3d`. Numerical
libraries loaded for the tests; no Torch, model fits or real cells ran. No
source, raw data, weights, shared cache, services or unrelated processes were
changed for this step. Full quality, raw validation, matching controls, broader
Windows qualification and a first accepted real Cho case remain pending.
Gate A and the scientific freeze remain unsigned. No commit or push occurred.

## 3 October 2026, 09:38 UTC: actual component004 independently audited and accepted

Independent execution review accepted this actual 25-test component and normal
private-Job launch/cleanup only, with no blocking findings. Its immutable record,
`runs/coordination/next_step_20261003_phase2/execution_audit_004.json`, has
SHA256 `4423dfc0bc5e4044980fbe7f652d9572af19ba3859a4d07132fbf45f88268205`
and decision `ACCEPTED_ACTUAL_GUARDED_QUALITY25_COMPONENT_ONLY`.
Root then wrote the separate final acceptance at
`runs/coordination/next_step_20261003_phase2/component_acceptance_004.json`
(SHA256 `a84d18993ac26070af8e40e20fc672587468d776e4742074c47c4f483f52a8ef`),
with decision `ACCEPTED_ONE_ACTUAL_GUARDED_QUALITY25_COMPONENT_ATTEMPT`.

The accepted result is 25/25 tests with zero errors, failures or skips, complete
physical exit with code 0 in the external 9.364-second interval, and normal
atomic private-Job launch/cleanup under 1 GiB process/aggregate limits. Source
`9d32cb1a` and selected runtime `a439111c` stayed stable. The exact edge from
venv launcher PID 63016 to interpreter PID 75152 and direct native membership
of PID 75152 were not recorded; the supported delegation inference remains
explicit in both audit and acceptance. Internal `accepted=false` receipts are
preserved as provisional evidence rather than rewritten.

The one actual attempt is consumed. There is no active pro3 compute or future
lease from this acceptance; Source002 and other workloads require fresh
coordination. Full quality, broader Windows qualification, raw checks, matching
controls and a real Cho case remain pending. The older failed quality pointer
is unchanged. This component imported no Torch and performed zero fits or real
cells; no source, raw data, weights, cache, service or unrelated process change
was made for this step. Gate A and the scientific freeze remain unsigned.
No commit or push occurred.

## 3 October 2026, 11:12 UTC: separate Windows qualification prepared; reviews pending

The user's next-step instruction now targets normal exit, cancel-grandchild
and the 64 MiB cap/96 MiB allocation-denial probe in the separate no-fit
Windows qualification. The phase plan at
`runs/coordination/next_step_20261003_windows/phase_plan.json` selects an
internal 14:30 UTC cap, not an owner expiry, compute lease or new 30-hour window.
The new package under `runs/coordination/windows_qualification_20261003_v2/`
is sealed; its preparation manifest has SHA256
`c7a2ed6ac8c6a2c676bed7384f8b30c8b3afab19e603845bb009c67b1c1ee961`.
The held candidate at
`runs/coordination/next_step_20261003_windows/release_candidate_001.json`
has SHA256 `6636c2d27dafdca8c961d19eb200eeb0b730dcd808956539453900d22a4c1203`,
with null window and confirmation. Independent preparation/candidate/admission
reviews remain pending, and no qualification launch or lease exists.

Native source observations at 11:03 UTC found all 430 current paths/hashes
matching the settled source, with no changes, metadata instability, errors or
reparse entries. The first audit producer joined rows with literal backslash+n
instead of LF; its refused receipt remains preserved and must not be consumed.
The separate corrected
`runs/coordination/next_step_20261003_windows/source_pin_audit_v2.json`
(SHA256 `398bb62300e7b68e741db772b479a9d39f31cbf20d41ea5ca647d133a6271c18`)
uses explicit LF and reconstructs `9d32cb1a` from baseline and current rows.
This is selected source identity, not executed qualification or full quality.

Native readiness samples at 11:03:08/10 UTC recorded 11.0576/11.0786 GiB RAM
and about 254.147 GiB free disk, with 1.248 seconds between sample completions.
Their receipt is
`runs/coordination/next_step_20261003_windows/readiness_observation_001.json`
(SHA256 `ea08aff92843357a92367f67679b61fbcbafc546f5a950d94525bb4e2f913ee3`).
These observations establish neither actual admission nor release. Entry still
requires two fresh 10 GiB startup samples, 4 GiB active RAM, 20 GiB disk,
6 GiB process and aggregate outer Job caps, and complete physical native exit
within 120 seconds including cleanup and the genuine peer/internal window.

The fresh conditional UNIT006 acknowledgement at
`runs/coordination/next_step_20261003_windows/pro2_unit006_conditional_ack_001.json`
(SHA256 `d924ef0efecdc60aabc01a1fa17cbc5945dbe42c30a3bbb01a4e0c31a74c4a47`)
creates no current hold, concrete GO or concurrent pro3 qualification authority.
The accepted 25-test component remains bounded to that component and normal
Job path. The older failed quality pointer is unchanged, zero real cases are
accepted, and no Torch, fit, cache/service or unrelated-process action is
performed by this preparation checkpoint. Gate A and the scientific freeze
remain unsigned. Historical wrappers, source and receipts are preserved.

## 3 October 2026, 11:28 UTC: Windows preparation statically ready; startup still unmet

Independent package, held-candidate and admission-helper reviews are accepted
under their static and caller-contract boundaries. The respective records in
`runs/coordination/next_step_20261003_windows/` are:

- `preparation_audit.json`, SHA256
  `9a980a66f6fbfcf2baed5e1246674b89b155ff48ddf3c4a0f380253ca864b26c`;
- `release_candidate_001_audit.json`, SHA256
  `1a29f16fa1f7a0a4af0b02e91b27dc80f4149125b5a075cced9afdb075384226`;
- `root_admission_001_review.json`, SHA256
  `717541f8ea74967ec79ff3bc50146a46b47e549f2f564aa579ff2f5f48df790a`.

Root checked accepted decisions, bindings and exact pins in
`runs/coordination/next_step_20261003_windows/preparation_ready.json`
(SHA256 `54b535d7b05982057017d90a1b57c3d3cadb0bb53160718c8545fb2d2e6d06ec`).
Source audit v2 remains accepted for 430/430 selected paths/hashes; its refused
producer receipt remains preserved. The sealed operational package is unchanged.
This establishes static readiness, not a lease, admission or runtime result.

Review caught a pre-entry exact-string mismatch in `global_deadline_utc`:
`2026-10-03T14:30:00Z` versus `2026-10-03T14:30:00+00:00`. The original held
candidate is preserved as `release_candidate_001_pre_review.json` with SHA256
`6636c2d27dafdca8c961d19eb200eeb0b730dcd808956539453900d22a4c1203`.
The reviewed `release_candidate_001.json` has SHA256
`c69d65110bbd517096a35371ba3a08c92fd6f7f248f0fc424860503934944a45`.
Only that field changed; the instant, internal 14:30 UTC cap and implementation
remain unchanged. The cap is not an owner expiry, compute lease or new 30-hour window.

Native RAM at 11:25 UTC was 9,916,575,744 bytes, about 9.24 GiB, below the
unchanged 10 GiB startup floor. Waiting continues naturally. Actual entry
requires a genuine new peer grant and fresh startup admission, the preserved
4 GiB active/20 GiB disk floors, both 6 GiB outer Job caps and complete
physical native exit within 120 seconds including cleanup. No qualification
lease, admission, Python process, Job, test or fit has begun.

UNIT006's fresh conditional acknowledgement remains future-only: a mutually
confirmed concrete interval and Root GO are required, at most 900 seconds,
with no concurrent pro3 qualification. No cache, service or unrelated-process
action occurred. The older failed full-quality pointer is unchanged, zero
real cases are accepted, and Gate A/freeze remain unsigned. Historical
preparation, source and receipts remain preserved.

## 3 October 2026, 12:30 UTC: Native lint accepted; separate mypy component preparation

Root accepted one actual native Rust Ruff check over `core`, `encoder`,
`adaptation`, `data`, `realtime`, `evaluation`, `scripts` and `tests`, using
`--no-cache`. It exited 0 at 11:54 UTC in 0.1734643 seconds. The
[root acceptance](../runs/coordination/next_step_20261003_windows/root_native_lint_acceptance_001.json)
has SHA256 `9c341bd30e65a951be96bd91b37c0d23b576f96131b2018b6f535c1e8c106886`.
The [native receipt](../runs/coordination/next_step_20261003_windows/native_source_lint_001.json)
has SHA256 `5002c6b9456ed753c079e71c5343dcec247e59843155dc295b5520fa225595c0`;
the [log](../runs/coordination/next_step_20261003_windows/native_source_lint_001.log)
has SHA256 `881cfd5721e7a4fb07cf1316b0463993ad071843d5b25c2781482eefe195fc02`.
Native before/after path sets and hashes matched all 430 files to `9d32cb1a`,
and root independently reconstructed both aggregates. The receipt retains
the prelaunch PowerShell list-conversion error and explicit `ToArray()` fix;
that error preceded any output or Ruff launch. Exactly one lint run occurred.
No frozen source fix or quality-pointer publication occurred. The pointer
remains failed for older `25ab4f3d`; this acceptance establishes lint only.

The [full-quality activation map](../runs/coordination/next_step_20261003_windows/full_quality_activation_map_001.md)
preserves two 10 GiB RAM startup samples; the runner's 9 GiB constant is disk,
not RAM. Full QA includes Torch synthetic engineering fits and needs its own
reviewed scope and fresh peer grant. It is not authorized by native lint or
the queued Windows qualification phase.

Root selected a [separate mypy-only phase](../runs/coordination/next_step_20261003_types/phase_plan.json),
`20261003_guarded_types_001`, with SHA256
`1f7489a873c585f39ef4dba0440591dcac6fe62403ca4cbf5185d295f0b551ff`.
New operations are being authored under `type_component_20261003_v1`;
no imports or execution occur during preparation. The profile retains both
1 GiB process/aggregate Job caps, two 5 GiB startup samples separated by at
least one second, 4 GiB active RAM/20 GiB disk and a 120-second physical limit.
The `-I -B` normal-site child requires fresh mypy/dependency/site-hook pins,
explicit strict configuration with no plugins and an owned cache. All
static reviews, a distinct fresh type-specific peer window and independent
actual execution audit are required. The 14:30 UTC cap is internal, not an
owner expiry, lease or renewed 30-hour session.

Windows preparation remains statically accepted and queued with its held
candidate and no actual scenario run. Its 10 GiB startup floor and the full-QA
10 GiB floor are unchanged; latest recorded RAM at 11:54 UTC was about
7.91 GiB. The [checker25 acknowledgement](../runs/coordination/next_step_20261003_types/pro2_checker25_interval_ack_001.json)
covers only 12:28-12:30 UTC, holding pro3-owned Python/tests/Jobs/fits while
allowing native preparation. It attests neither peer Root GO/pass nor a
pro3 compute grant, and is not extended. Future UNIT006 remains conditional.
No scientific fits/cases are accepted; Gate A/freeze remain unsigned.
Historical preparation and receipts are preserved.

## 3 October 2026, 13:15 UTC: Type preparation statically ready; fresh window requested only

All mandatory independent reviews are accepted for the separate type phase:
[package](../runs/coordination/next_step_20261003_types/type_preparation_audit_001.json)
(`ab74ab5d`),
[held candidate](../runs/coordination/next_step_20261003_types/type_candidate_audit_001.json)
(`68522861`) and
[admission helper](../runs/coordination/next_step_20261003_types/type_admission_review_001.json)
(`b1c0f81e`). Root checked their semantics and exact pins in
[preparation_ready_001.json](../runs/coordination/next_step_20261003_types/preparation_ready_001.json),
SHA256 `f96ab4b030c89aa23d4739964e815f49c2f4be04635ab032a2c00d00e681de19`.
The [sealed manifest](../runs/coordination/type_component_20261003_v1/preparation_manifest_20261003.json)
has SHA256 `f334f28eae504fe477b7bcf0f4180377c0b5df3773df7dfe4cd8c5110e6b6920`;
held candidate `a1f41db7` binds source `9d32cb1a` and the seven strict targets.
The selected normal-site inventory covers 3,142 runtime files and 765
absences. It certifies selected tool/runtime pins, not the entire installed
third-party type-input closure. Static AST/stub reads remain distinct from
forbidden runtime imports or model fits.

A fresh type-specific peer window has been requested only. No grant,
admission, Python/Job launch or type pass is established at this checkpoint.
The [phase](../runs/coordination/next_step_20261003_types/phase_plan.json)
retains two 5 GiB startup samples separated by at least one second, 4 GiB
active RAM/20 GiB disk, both Job caps of 1 GiB and physical exit/drain/cleanup
within 120 seconds. Fresh source/runtime checks, genuine release, the
admission helper's physical-exit/durable-receipt/fresh-window contract and
independent actual audit remain mandatory. The internal 14:30 UTC cap is
not an owner expiry, lease or new 30-hour session; no limit increase or
automatic retry is authorized.

[Peer ACK002](../runs/coordination/next_step_20261003_types/pro2_checker25_interval_ack_002.json)
(`b7a51bb5`) closed on explicit early release at 12:41 UTC. Root's
[physical verification](../runs/coordination/next_step_20261003_types/pro2_checker25_physical_verification_002.json)
(`3483ec06`) verified six bound pins, exit 0 and a conservative 19-second
upper bound. A separate independent peer result audit has been reported,
but root result acceptance remains pending. Peer evidence supplies no pro3
compute grant or type acceptance.

Native Rust lint remains accepted only for its actual lint scope. Windows
qualification remains queued with accepted static reviews; Windows/full-QA
10 GiB startup floors and the failed older-source quality pointer remain
unchanged. No scientific fits or real cases are accepted; Gate A/freeze
remain unsigned. Historical sections, source and receipts are preserved.

## 3 October 2026, 13:51 UTC: Type attempt001 failed before mypy; physical closeout retained

One actual type bootstrap attempt ran under the genuine grant `92fac836`.
The [root physical witness](../runs/coordination/next_step_20261003_types/root_type_physical_witness_001.json),
SHA256 `744d5f83ac770008d1ea21a29773060c0f9aa633833cb02ab1adf6fe0fd248c6`,
records native exit 1 from 13:42:40.876 to 13:43:12.836 UTC in
31.9593598 seconds, with streams drained inside the physical/window limits.
The child refused its current Job-cap check before the leaf handshake or
mypy API. Observed mismatching cap fields were not retained; the root cause
is unknown. No mypy check/pass or source type errors are established.

The [failed-attempt cleanup closeout](../runs/coordination/next_step_20261003_types/root_failed_type_cleanup_closeout_001.json),
SHA256 `76033dbda9db658a4df9056beda637c910415c3fd03f2a5f21c537832cf94110`,
retains the parent report of atomic private-Job assignment, 1 GiB process
and aggregate caps, flags 8960, an empty closed Job, all handles closed and
no cleanup errors. Scoped observations found PIDs 42108, 62108 and 36104
absent at 13:46:45 UTC. The native whole-cleanup field remains false and
the candidate remains failed. These are scoped cleanup observations, not
host-quiet or successful leaf interoperability evidence. Independent actual
failure audit remains pending.

Root [explicitly released the peer window](../runs/coordination/next_step_20261003_types/root_type_peer_release_closeout_001.json)
effective 13:46:45 UTC; closeout SHA256 is
`d2c1a9395fbbeef8241b9c956fe35e2a94979d23836c081b0442c505c7693d4b`.
The grant and failed attempt are consumed: no retry or replay. The
[peer hold qualification](../runs/coordination/next_step_20261003_types/pro2_type_hold_qualification_001.json),
SHA256 `e5ab38feae9acf06c0fca938a691289c14fdd543b1c340858f7dd2f087505e2a`,
records a reported 0.4-second native source reconstruction/comparison with
unretained exact timing between 13:39:19 and 13:48 UTC. It may overlap the
hold. Full interval conformance is unconfirmed; no causal link to the type
failure is established, and no failed result is promoted.

Read-only diagnostic preparation for a new version is underway. Manual
failure audit, independent static reviews, a new attempt and fresh peer
grant are required before any execution. No source or operational fix is
claimed here. Canonical source remains `9d32cb1a`; native Rust lint acceptance
`9c341bd3` still covers lint only. The failed older-source quality pointer
remains unchanged (`fbe512e6`), as do Windows/full-QA 10 GiB startup floors.
Zero scientific fits or real cases are accepted; Gate A/freeze remain
unsigned. Historical sections, original operations and receipts are preserved.

## 3 October 2026, 14:05 UTC: Failure audit complete; distinct V2 preparation manually authorized

The [independent failure audit](../runs/coordination/next_step_20261003_types/type_execution_audit_001.json),
SHA256 `b514dc3a2ca2f2a1ac521372a072369ce2c31a8e1a1fbbb0f4d4440a38b2c153`,
accepts failure-evidence review only. Its `accepted=false` and false
type/runtime-pass fields remain unchanged. Attempt001 physically exited 1
in 31.959 seconds before mypy; observed cap mismatch values were not retained,
so the cause remains unknown. No mypy result or source type errors are
established. The failed branch omitted final source/runtime checks and did
not certify a pass.
The failed attempt, original V1 and spent grant stay preserved.

Root's [manual review](../runs/coordination/next_step_20261003_types/root_manual_failure_review_001.json),
SHA256 `5817547ede2b0c09555eac5661400d5723e867fea5df7c3d680a1ccf0ca089cb`,
permits distinct successor preparation only. The
[read-only proposal](../runs/coordination/next_step_20261003_types/type_bootstrap_repair_proposal_001.md)
has SHA256 `ddaf115795f148bc30cfcac737f7603b271353eba7e44d2c569191101ab7e67d`.
The [new phase plan](../runs/coordination/next_step_20261003_types2/phase_plan.json),
SHA256 `8464a4fb9671c59fb75a5ea4785e2d4e03d54521e52273b0dfcd617b98aafd0e`,
selects `20261003_guarded_types_002`, operations V2, release002 and fresh
attempt/launcher directories002. Authors are preparing new copies for
independent static reviews. The proposal retains nullable-query diagnostics
and requires selected parent-owned Job cap/PID witnesses before mypy.
No genuine successor grant is requested and no actual retry, Python/mypy
or Job execution is authorized now. All new package/candidate/helper reviews,
fresh grant/admission and eventual independent actual audit remain mandatory.
The 5 GiB startup/4 GiB active/20 GiB disk floors, both 1 GiB caps,
120-second physical limit and internal 14:30 UTC cap are unchanged.

The [peer hold qualification](../runs/coordination/next_step_20261003_types/pro2_type_hold_qualification_001.json)
(`e5ab38fe`) still lacks exact timing; complete hold conformance and a causal
relation to failure remain unestablished. Native Rust lint remains accepted
only, source binding `9d32cb1a` and failed quality pointer `fbe512e6` are unchanged,
Windows/full-QA retain 10 GiB startup, Gate A/freeze remain unsigned and zero
real cases are accepted. No elapsed grant or renewed 30-hour authority is
inferred; historical evidence remains preserved.

## 3 October 2026, 14:39 UTC: TYPE002 expired before seal; prepared package held, no execution

Root's [phase closeout](../runs/coordination/next_step_20261003_types2/root_phase_closeout_001.json),
SHA256 `1e61f64d157fa4de510ee7ba4ac6e55b1d86d12ff539271678f07b5175441f76`,
records `CLOSED_TO_EXECUTION_EXPIRED_CAP_PREPARED_HELD`. The internal
14:30 UTC cap expired before seal/admission/new grant. No genuine TYPE002
grant, admission, Python/mypy/Job/fit or attempt002 occurred. The peer was
notified of closure without a presumed hold. No cap extension, retiming or
renewed 30-hour window is inferred.

The [V2 manifest](../runs/coordination/type_component_20261003_v2/preparation_manifest_20261003.json),
SHA256 `a529f89686088a0ae5293bbf2b97d466fb6059f0811422a774d60c130760ad74`,
binds 16 sealed artifacts at 14:34:36 UTC. The
[candidate](../runs/coordination/next_step_20261003_types2/release_candidate_001.json)
(`f3d0ba33`) remains held. Independent package/candidate/helper reviews are
finishing separately. Native parse/lint/default-plan and selected runtime
hash checks passed without Python execution. Corrected ASCII-prose plan
time 14:31:46 UTC is retained as truthful post-cap preparation. The repaired
exact selected-Job witness gate remains static preparation, not an actual
leaf handshake or mypy pass.

The [selected-file recheck](../runs/coordination/next_step_20261003_types2/root_selected_file_recheck_001.json),
SHA256 `c5dd68dfb7a21b88ff0e49fce7b4213fbf64ded9a94f3b48645f73b3fa4aff7a`,
matches 430 settled baseline paths/hashes and `9d32cb1a`; it does not establish
a fresh full-selector path set. Runtime inventory remains selected 3,142
files/765 absences, not the entire installed type-input closure. Future
execution requires distinct coordinated phase/cap/candidate/reviews,
fresh admission/source/runtime checks and genuine new peer grant/attempt.

Attempt001 remains failed: exit 1 in 31.959 seconds before mypy, unknown
cause, no mypy result or established source type errors. Its failure audit,
manual review, qualified cleanup, spent grant and uncertain peer-hold timing
remain preserved. Native Rust lint is accepted only for its actual lint scope.
Quality pointer `fbe512e6` remains failed for older `25ab4f3d`; Windows/full-QA
10 GiB startup, unsigned Gate A/freeze and zero accepted real cases are
unchanged. Source, original operations, historical receipts and other agents'
edits are preserved.

## 3 October 2026, 14:49 UTC: TYPE002 statics accepted held; distinct TYPE003 preparation selected

TYPE002's package, held-candidate and admission-helper static reviews are
accepted (`d376029d`, `de1fc82d`, `043e4ddc`). Root's
[final readiness](../runs/coordination/next_step_20261003_types2/preparation_ready_001.json),
SHA256 `22d0526e5f4f9980c23dce25d3c6240b971deed14c786a56a69dd5bb3b2c59fd`,
checks their decisions, exact pins and all 16 sealed artifacts. Execution
and runtime acceptance remain false. The
[TYPE002 closeout](../runs/coordination/next_step_20261003_types2/root_phase_closeout_001.json)
(`1e61f64d`) remains expired and held, with no grant, admission or attempt002.
Its 14:30 cap and post-cap preparation timestamps are preserved.

Under the current keep-working instruction, root selected a
[distinct TYPE003 phase](../runs/coordination/next_step_20261003_types3/phase_plan.json)
at 14:44 UTC, SHA256
`ea8fe636a73631939007e3507f98971213b04839b406fef9b7187d20bff494c4`.
Phase `20261003_guarded_types_003` has internal cap 15:45 UTC and new
operations V3, release/grant003 and fresh attempt/launcher directories003.
Metadata substitutions must preserve the accepted V2 gate and unchanged
source/runtime/configuration/targets/environment/limits, with explicit
reviewed lineage. New native sealing and three independent static reviews
are pending. TYPE002 readiness supplies preparation lineage only, not
authority to replay its expired candidate or extend its cap.

The peer's 15:15-15:30 UTC proposal is acknowledged only; no genuine grant,
hold, admission, Python/mypy/Job or attempt003 exists at this checkpoint.
Fresh settled reviews, scope-specific grant and actual complete
source/runtime/resource admission remain mandatory. Limits stay two 5 GiB
startup samples at least one second apart, 4 GiB active/20 GiB disk, both
1 GiB caps, strictly more than 125 seconds of launch reserve and physical
120 seconds including stream drain and cleanup. No lease or new 30-hour
window is inferred.

Attempt001 remains a failed 31.959-second/exit-1 bootstrap before mypy,
unknown cause and no established project type errors. Its qualified cleanup
and uncertain peer-hold timing remain preserved. Source binding `9d32cb1a`,
failed older-source quality pointer `fbe512e6`, native-lint-only acceptance,
Windows/full-QA 10 GiB startup, unsigned Gate A/freeze and zero accepted
real cases remain unchanged. Frozen V1/V2, prior receipts and other agents'
edits are preserved.

## 3 October 2026, 15:10 UTC: TYPE003 static readiness accepted; genuine window requested only

TYPE003 package/candidate/helper static reviews are accepted (`cbc2cafb`,
`55aac486`, `4f5f03b5`) with no blockers. [Root readiness](../runs/coordination/next_step_20261003_types3/preparation_ready_001.json),
SHA256 `d510d801387a0656612945361acfa6575ebdbe93f297185306d7d3a046b48d47`,
verifies 13 sealed pins, flat bindings, unchanged limits and held absences.
Execution/runtime acceptance remain false. Root requested a genuine
15:15-15:30 UTC peer window with explicit holds; the request remains pending.
No grant, hold, admission, Python/mypy/Job or attempt003 is established.
RAM at 15:07 UTC was about 5.51 GiB, above 5 GiB component startup and below
10 GiB heavy startup; it is readiness, not admission. The internal 15:45 cap,
historical failures/expiry, failed quality pointer, zero accepted real cases
and unsigned Gate A/freeze remain unchanged. No lease or replay is inferred.

## 3 October 2026, 16:00 UTC: Actual TYPE003 type errors reviewed; narrow correction frozen, new pin pending

The [TYPE003 failure audit](../runs/coordination/next_step_20261003_types3/type_execution_audit_001.json),
SHA256 `e7103786d9ee380b63932a3de357349e31ce903fb8c13a56c2a5c8421b05e7f3`,
accepts failure evidence only. Actual mypy invocation and return were
observed: exit 1, four errors in one file among 205 checked files, inside
a 56.482-second physical attempt. The exact selected-Job/actual-leaf gate
worked. Scoped cleanup qualifications and incomplete final source/runtime/
operations checks remain attached; no type/runtime pass is accepted and
the original TYPE001 cause is still unknown.

Root's [manual review](../runs/coordination/next_step_20261003_types3/root_manual_failure_review_001.json),
SHA256 `0e4425f1a28e2255e96fde7ea97e78965e0782097e96ece11965c42eaa087436`,
verifies 38 evidence pins and authorizes the sole-file typing correction
in `evaluation/phase2_cho_execution.py`. Its assigned worker finished and
was interrupted. The [fix proof](../runs/coordination/next_step_20261003_source_fix/source_fix_proof_001.json),
SHA256 `739607aee54c3c647271a429ee73f2aed6611f7de477c00cb4f45ff8e8731407`,
records four exact replacements whose reversal reconstructs the original
bytes. The new frozen file hash is
`d4073a28633fec71b41509d37a068260bb4a487ce67933f0e14a11cf6a4de568`.
Numeric narrowing retains exact-type/finite/positive/cap guards; a prepared
string digest is separated from nullable setup-failure receipt state.
Native file-only Ruff passed. This is static correction evidence, not an
executed runtime-equivalence or post-fix mypy test. Independent patch audit
is finishing.

The [source-fix plan](../runs/coordination/next_step_20261003_source_fix/phase_plan.json),
SHA256 `019058afd8f61522338dba33090eadf5e986107eb5d7e39515ddc52cb6a346fc`,
sets internal cap 17:00 UTC without a lease or new 30-hour window. Fresh
full 430-path canonical source reconstruction is pending. Old `9d32cb1a`
receipts, operations and candidates cannot admit the changed source.
Accepted patch review/new pin and distinct TYPE004 guard/candidate/helper
reviews, genuine new grant and actual admission are required before any
revalidation; no new Python/mypy/test pass or TYPE004 grant exists.

Peer checker28 explicitly released after its own pre-start metadata failure,
with no Python/test events; its 15:55 hold has elapsed. This is not pro3
or scientific acceptance. The failed quality pointer, Windows/full-QA
10 GiB startup, unsigned Gate A/freeze and zero accepted real cases remain
unchanged. Historical failed attempts, original operations, raw data,
weights and other agents' edits remain preserved.

## 3 October 2026, 16:37 UTC: Narrow patch accepted; source423f pinned, TYPE004 preparing

The [independent patch audit](../runs/coordination/next_step_20261003_source_fix/source_fix_audit_001.json),
SHA256 `5274f5ebd54fed14c6510262a0dfca7f3be12fce40ee5b8fd9fca2d49d786a3c`,
accepts only the static narrow correction. The [manifest](../runs/coordination/next_step_20261003_source_fix/source_manifest.json)
(`d12c961c`) and [native source audit](../runs/coordination/next_step_20261003_source_fix/source_pin_audit.json)
(`7118c4ca`) establish canonical
`423faa138200b85c56463ad8e0cfad48469fc9a061a7429782ea7b1be170f820`.
All 430 selected paths are pinned; the reviewed module is the sole changed
hash and 429 baseline hashes remain unchanged. Saved-manifest reconciliation
also reproduced the LF digest. No post-fix Python/mypy/test or runtime
equivalence pass is established. TYPE003's actual four errors among 205
checked files remain tied to historical `9d32cb1a`.

The [fresh TYPE004 phase](../runs/coordination/next_step_20261003_types4/phase_plan.json),
SHA256 `a52cbf4281e1ef816c87797676a1d9fc4ec543cd20fafc52fd8ffc62a79e31b1`,
prepares V4 operations and independent reviews, with internal cap 17:00 UTC.
Current-source bindings use 423f/7118/d12; historical failed-attempt bindings
remain 9d32. Root readiness, genuine new peer grant and actual guarded
admission are still required before one fresh attempt004. Existing gate,
targets, runtime, environment, both 1 GiB caps and 5/4/D20/125s/120s policy
remain unchanged. Old operations, receipts and candidates are preserved.

Peer checker28 [ACK002](../runs/coordination/next_step_20261003_types4/pro2_checker28_interval_ack_002.json),
SHA256 `dcacfe8e516d1e12591abbd31736998fa9adc1060aa00c31f1898353553637d4`,
covered 16:30-16:35 UTC. The peer explicitly released it after native GO
writer 8fd2ad exited 1/drained in 0.3157098 seconds for insufficient reserve,
before writing a GO or entering parent002. No peer checker/test result or
pro3 compute grant follows from this coordination. No renewed 30-hour
window is inferred. The older failed quality pointer, Windows/full-QA
10 GiB startup, unsigned Gate A/freeze and zero accepted real cases remain
unchanged; raw data, weights and other agents' edits are preserved.

## 3 October 2026, 17:00 UTC: TYPE004 mypy returned zero; native deadline-witness gate failed

Actual [root admission](../runs/coordination/next_step_20261003_types4/root_admission_physical_witness_001.json),
SHA256 `7d11defba91cdfaa899463b81db07fca1773b964ca87d6ab8786d7dfaed9d63a`,
exited 0/drained in 22.318 seconds. The single native attempt then exited
1/drained in 86.412 seconds, within 120 seconds and both deadlines, as
recorded in the [physical witness](../runs/coordination/next_step_20261003_types4/root_type_physical_witness_001.json)
(`065032e8`). Actual mypy invocation and return were observed with status 0:
[no issues in 205 source files](../runs/phase2/type_validation/pro3_types_20261003_004/mypy.stdout.log).
The [child result](../runs/phase2/type_validation/pro3_types_20261003_004/result.json)
(`607c1c19`) records matching Source423f before/after for all 430 selected
paths and valid exact private-Job membership. Parent completion records
stable runtime/operations and complete Job cleanup in its [completion receipt](../runs/phase2/type_validation/pro3_types_20261003_004/completion.json)
(`a993a6e6`).

The native wrapper refused the completed candidate with "Passed native
deadline witness differs." Observed timestamps differ by 800 ns between
native seven-digit fraction .5788168 and Python six-digit .578816. A
future normalization proposal is read-only and not implemented; independent
actual audit is pending. The checker returned zero, but the full guarded
component is not accepted. The native failed-candidate whole cleanup=false
qualification is retained, rather than promoted to a successful receipt.

[Root scoped cleanup](../runs/coordination/next_step_20261003_types4/root_failed_type_cleanup_closeout_001.json),
SHA256 `4b7a3694a306b4b6fdca1c0b8b055a4044e68e7966798110786de908d2d4f87a`,
confirmed owned PIDs 62196/76240/55972 absent, the private Job empty/closed,
handles closed and no cleanup errors. The [peer release closeout](../runs/coordination/next_step_20261003_types4/root_type_peer_release_closeout_001.json)
(`efc71561`) records explicit release after cleanup at 16:54:57.408 UTC,
physical message completion and received peer acknowledgement. Exact
message-completion timestamp was not recorded; the cleanup timestamp is
an earliest boundary, not the release time.

Attempt004/grant004 are spent, with no automatic retry. The internal
17:00 UTC cap remains unchanged and supplies no renewed 30-hour window,
compute lease, full-QA/Windows or scientific acceptance. The older failed
quality pointer, heavy 10 GiB startup floors, unsigned Gate A/freeze and
zero accepted real cases remain unchanged. Historical failed attempts,
operations, raw data, weights and other agents' edits remain preserved.

## TYPE004 reviewed and TYPE005 native precision repair: 3 October 2026, 17:30 UTC

**3 October 2026, 17:30 UTC:** TYPE005 is preparing the reviewed native deadline precision
repair under its [new finite phase](../runs/coordination/next_step_20261003_types5/phase_plan.json),
with an internal 18:30 UTC cap. The [TYPE004 actual audit](../runs/coordination/next_step_20261003_types4/type_execution_audit_001.json)
and [root manual review](../runs/coordination/next_step_20261003_types4/root_manual_failure_review_001.json)
confirm the 800 ns witness mismatch and preserve mypy exit 0 for 205 files versus
native exit1/full component unaccepted. The project source remains unchanged at `423faa13`.
The [independent native patch review](../runs/coordination/next_step_20261003_types5/native_deadline_patch_audit_001.json)
accepts static evidence only: flooring to microseconds advances the deadline
0 to 900 ns earlier, while retaining exact equality and all limits.
New package, candidate and helper reviews, a genuine grant005 and actual admission
are still required. No attempt005, Python, mypy or Job has launched. The failed
quality pointer, heavy 10 GiB floors, unsigned scientific gates and zero accepted
real cases remain; no renewed 30-hour session or compute lease is inferred.
See [HANDOFF.md](../HANDOFF.md).

## TYPE005 static readiness: 3 October 2026, 17:41 UTC

**3 October 2026, 17:41 UTC — TYPE005 static readiness:** The [three static reviews and root readiness](../runs/coordination/next_step_20261003_types5/preparation_ready_001.json) accept the repaired package with all 16 artifact pins verified. Root requested a fresh 17:45–18:00 peer grant; no grant, admission or attempt005 exists yet. Physical admission and fresh resource/time checks remain required. The unchanged source is `423faa13`; actual TYPE004 mypy exit 0 for 205 files remains qualified by its native gate failure. Full QA/Windows and science gates remain pending. See [HANDOFF.md](../HANDOFF.md).

## TYPE005 failure review and user-requested stop: 3 October 2026, 18:11 UTC

Work is stopped at the user's request. The final [independent failure audit](../runs/coordination/next_step_20261003_types5/type_execution_audit_001.json) (`ccaa4845`) accepts the evidence review only; component, type and runtime acceptance remain false. The [deadline chronology](../runs/coordination/next_step_20261003_types5/type_deadline_failure_analysis_001.json) (`db79651a`) is a separate later receipt, and the sealed audit was not rewritten to include it. Root [manual review](../runs/coordination/next_step_20261003_types5/root_manual_failure_review_001.json) (`4be3b890`) rehashes all 67 saved pin entries and closes the current task without authorizing any successor or retry. The [phase closeout](../runs/coordination/next_step_20261003_types5/phase_closeout_001.json) (`d5566467`) makes the unused internal 18:30 cap inactive. The original 30-hour goal is already complete, verified live; no new active goal was created.

Exactly one TYPE005 [admission](../runs/coordination/next_step_20261003_types5/root_admission_physical_witness_001.json) exited 0/drained in 41.562 seconds, and one [native attempt](../runs/coordination/next_step_20261003_types5/root_type_physical_witness_001.json) exited 1/drained in 96.922 seconds, within 120 seconds and both deadlines. The parent stopped on `session_deadline`. Its persisted nested deadline was native deadline minus 20 seconds; only 38.041703 seconds remained at the membership witness. The exact UTC-versus-monotonic trigger and last child stage were not retained. Child result and mypy logs are absent, so API invocation/return and any new type pass are not certified. Final source/runtime/operations checks were incomplete, which does not establish actual drift. The raw floored timestamps agree, but the native precision-comparison stage was not reached; the full repaired gate is unaccepted.

Parent Job termination, empty/closed Job and closed handles are recorded without cleanup errors. Root [scoped cleanup](../runs/coordination/next_step_20261003_types5/root_failed_type_cleanup_closeout_001.json) observed reported PIDs85968/84912/76084/85844 absent. Native failed-candidate cleanup=false remains preserved. The [explicit peer release](../runs/coordination/next_step_20261003_types5/root_type_peer_release_closeout_001.json) followed terminal/drain/cleanup, and peer acknowledged; exact message completion time is unmeasured. Grant and attempt005 are spent. Authors and reviewers have finished and received interrupts; no further work is queued. The uninitialized quality-runner stub has received interruption requests; no obsolete watcher was armed or rearmed.

The last completed mypy output remains TYPE004's [no issues in 205 source files](../runs/phase2/type_validation/pro3_types_20261003_004/mypy.stdout.log), qualified by that attempt's native deadline-witness failure. Source `423faa13`, frozen operations and all failed receipts are preserved. Full QA/Windows remain unexecuted on current source, their 10 GiB startup floors remain, and the global quality pointer is still failed. Gate A and experiment freeze remain unsigned, with zero accepted real cases. Raw data, weights, shared services and WSL cache were preserved.

Future work requires an explicit user resume and fresh coordination. First investigate stage timing and durable API-entry/return evidence within the original caps; do not infer a pass from buffered output or enlarge limits automatically. Any later validation needs settled source/runtime pins, independent reviews, a fresh genuine grant and a new attempt. This is a handoff recommendation, not scheduled work.

## Session resume: 3 October 2026, 18:54 UTC

The user explicitly resumed engineering work for a bounded 12-hour window
ending 2026-10-04 06:54:53 UTC, with instructions to test and audit every
major step, fix problems found, coordinate cooperatively with any other agent
on the shared machine, and commit after docs/handoff updates before pushing.
The [session ledger](../runs/coordination/12h_session_20261003.json) records
the authorization and resource policy; Gate A and the experiment freeze remain
unsigned owner decisions.

The settled source was reverified live at 18:55 UTC as `423faa13` (git clean
at `560ebc0`; disk 245.99 GiB, RAM 7.13 GiB — below the 10 GiB full-quality
startup floor). No peer coordination records newer than the 18:22 UTC
publication existed at session start. The selected first step is the
[quality phase](../runs/coordination/next_step_20261003_quality/phase_plan.json):
one guarded full-quality attempt on `423faa13` with a fresh attempt directory
and current-pointer publication, subsuming lint/types/tests instead of a
sixth isolated type attempt. A read-only
[RAM monitor](../runs/coordination/next_step_20261003_quality/ram_monitor.py)
waits for two consecutive 10 GiB samples while light preflight and
documentation proceed. Controls refresh, Windows qualification and the first
real case follow as floors permit. No guard lowering or scientific admission.

## Execution-path import fix: 3 October 2026, 19:20 UTC

Session preflight reproduced a deterministic blocker: `scripts/verify_phase1_quality.py`
executed in script mode (the exact child invocation of the guarded quality
runner and of the tracked pre-commit hook) crashed with
`ModuleNotFoundError: No module named 'scripts'` before creating any output.
Cause: the venv's editable install maps only the six pyproject packages
(`core`, `encoder`, `adaptation`, `data`, `realtime`, `evaluation`), script
mode puts the scripts directory rather than the project root on `sys.path`,
and the file imports `from scripts.run_guarded_quality import ...`.
`scripts/run_no_future_matched_control.py` has the identical latent fault on
its `from scripts.refresh_source_bound_controls import ...` line.

The repair adds the guarded root bootstrap already used at the top of
`scripts/run_guarded_quality.py` to exactly those two files; no other logic,
literals, guards or outputs changed. Whole-project ruff, strict mypy over 205
files, and script-mode `--help` from a foreign cwd all pass for both files.
The [independent patch audit](../runs/coordination/next_step_20261003_quality/source_fix_audit_001.json)
accepted the change `ACCEPTED_STATIC_ONLY` with no blockers, and noted that
`refresh_source_bound_controls.py` remains script-mode-unsafe on its training
path inside `main()`; this session invokes it in module mode as documented.
The canonical source pin moved from `423faa13` to
`23bdfb5fc60e4b64fe3b6f7de185253f1839aeeaa2ff9aeb6e995b043ad3093b`; the
guarded quality attempt targets the new pin.

## Full-suite pre-verification and three Windows test repairs: 3 October 2026, 19:55 UTC

Before spending the scarce 10 GiB window on the guarded attempt, the full
pytest suite was pre-verified unguarded at ~5-7 GiB available RAM:
**3 failed, 1038 passed, 3 skipped, 1121 subtests passed in 1727 s** (the
historical 1 October pointer failure's nine selector-budget failures are
already repaired at this source). The three failures were diagnosed and
repaired:

1. `tests/test_phase2_cho_execution.py::test_parent_claim_rehash_cannot_hide_git_provenance_change`
   and 2. `tests/test_phase2_cho_sweep_resume.py::SweepResumeTests::test_resealed_historical_claim_cannot_complete_a_current_cell`
   resealed forged records with `Path.write_text(... + "\n")`, which on
   Windows writes CRLF, so the (correct) canonical-bytes guard refused the
   forged file before the provenance branch under test. Both now write exact
   bytes with `write_bytes((...) + "\n").encode("utf-8")`, preserving the
   adversarial intent. These tests had never executed before (per the 30h
   ledger M2 note).
3. `tests/test_phase2_cho_sweep.py::ProductionChoCaseRunnerTests::test_eegnet_case_full_real_wiring_and_ceiling_boundaries`
   failed because the fixture's hard-coded method template lacked the
   `support.query_batch_size` field (default 8) that the typed candidate
   schema now carries; both candidates now include it.

After the fixes the three tests and all 65 tests in the three files pass;
ruff passes. Strict mypy over the three TEST files reports 27 pre-existing
structural findings (FakeRecorder arg-types, JsonValue indexing, untyped
braindecode import) at sites unrelated to these edits; test files are outside
the authoritative seven-package types gate, so these are recorded as known
out-of-gate findings, not gate blockers. Canonical source pin moves from
`23bdfb5f` to `88de6af5ae1595c40f4da6e23a9facac770c285f2e86d71db3f9d0f68c8d9698`;
the guarded attempt targets the new pin.

## First guarded full-quality attempt failed on transient MemoryError: 3 October 2026, 20:36 UTC

The guarded attempt on `88de6af5` (launched 19:59:21 UTC after RAM recovered to
six consecutive samples at/above 10 GiB) ran clean preflight, lint exit 0,
strict types exit 0 inside the guard, and the full pytest stage for 1,876
seconds with available RAM sustained at 7.7-9.8 GiB — then failed on exactly
one test,
`tests/test_phase2_cho_source_restore.py::ChoSelectedSourceRestoreTests::test_real_store_round_trip_still_refuses_incomplete_cho_evidence`,
with a `MemoryError` at `evaluation/phase2_selected_source_store.py:228`
inside `_read_bounded_regular`'s already-bounded read (≤64 MiB). 1,040 tests
passed; source stayed stable before/after; no resource-floor stop; no pointer
publication; the failed attempt and receipt are preserved at
`runs/phase2/quality_attempts/20261003_88de6af5_fullq_guarded/` and the
previous (failed, 1 October) pointer bytes are untouched.

Diagnosis: transient system commit-charge pressure while both projects' Python
test suites ran concurrently (the peer pro2 session runs its own suite in
parallel; its availability note is
`runs/coordination/pro2_peer_session_20261003_001.json`). The read is bounded
by design; no code defect is indicated. This test passed in the same session's
unguarded pre-verification an hour earlier.

Response: pro3 posted a cooperative quiet-interval request
(`runs/coordination/pro3_request_peer_quiet_interval_001.json`, 20:40-~21:20
UTC) asking pro2 to hold its partitions for one rerun in a fresh attempt
directory; absent an acknowledgement by 20:50 UTC pro3 proceeds then anyway.
No guard is lowered; the 10 GiB startup floor and all limits are unchanged.

## Guarded full-quality pass on 88de6af5: 3 October 2026, 21:23 UTC

Attempt 3 ([receipt](../runs/phase2/quality_attempts/20261003_88de6af5_fullq_guarded3/receipt.json),
launched 20:55:52 UTC inside the peer-agreed quiet interval) **passed**:
lint 0, strict types 0 (205 files), pytest 1041 passed / 3 skipped / 1121
subtests in 1617 s; total elapsed 1626.9 s; source stable `88de6af5` before,
during and after; minimum available RAM 6.90 GiB and disk 235.95 GiB never
approached the 4/8 active floors; the current quality pointer was published
(sha `152f972e…`) replacing the 1 October failed pointer (preserved bytes
sha `fbe512e6…`); the pass archive is
`runs/phase2/quality_history/20261003_88de6af5_fullq_guarded3.json`. The
[independent audit](../runs/coordination/next_step_20261003_quality/quality_pass_audit_001.json)
recomputed all artifact hashes (before/stdout/archive/pointer/logs),
re-verified `verify_quality_bundle` against the live tree, confirmed the two
failed predecessor attempts remain preserved, and accepted the result
`ACCEPTED_QUALITY_PASS_ENGINEERING_ONLY` with zero blockers. Engineering
quality only: Gate A and the experiment freeze remain unsigned and no real
case is accepted. Next: refresh the 45 source-bound and 36 no-future controls
on this source.

## 45/45 source-bound controls refreshed on 88de6af5: 3 October 2026, 21:48 UTC

With the current quality pointer now certifying `88de6af5`, the
source-bound control refresh ran in module mode
(`python -m scripts.refresh_source_bound_controls`, self-deferring below its
configured 10 GiB startup floor) and completed with exit 0:
**45 valid records, zero invalid, zero unexpected**, in the fresh
context-digest batch
`runs/source_bound_controls/16b9105ef6632a5a1a6bbd12ab04a62ae227b2c20e35fcb019520b7a6ff660b7/`
(36 `pre_cue_control` + 9 `gate_a_shuffle` receipts, each a real CUDA EEGNet
training record bound to source `88de6af5`; the runner's audit_context
re-verified every unit against its actual code, inputs and environment).
Historical batches, including the 1 October `6523283e` batch, remain
preserved. Engineering control evidence only; no scientific admission.
Next: the 36 no-future matched controls, which bind the new pointer bytes.

## Current-source raw audit passes on 88de6af5: 3 October 2026, 22:04 UTC

The staged raw-verifier repin pattern was applied: a fresh dated copy at
`runs/phase2/freeze_readiness/20261003_88de6af5_raw_source_readonly/` changed
exactly two literals (the expected-source hash and its error-label short form;
reverse substitution reproduces the 9d32cb1a-staged bytes — see
[repin_provenance.json](../runs/phase2/freeze_readiness/20261003_88de6af5_raw_source_readonly/repin_provenance.json)),
and the copy passes native Ruff. Executed read-only at 22:04 UTC it
**passed**: 52 Cho raw sources rehashed (10,704,036,837 bytes) in 18.8
seconds with minimum available RAM 9.36 GiB and disk 234.8 GiB, floors 6/8
never approached ([receipt](../runs/phase2/freeze_readiness/20261003_88de6af5_raw_source_readonly/receipt.json)).
This closes the current-source raw-validation gap; the older
9d32cb1a-staged copy remains preserved unexecuted. Read-only audit; no
training, no cells, and Gate A remains unsigned.

## 36/36 no-future matched controls pass on 88de6af5: 3 October 2026, 22:30 UTC

The no-future matched control (module mode, self-deferring below its 10 GiB
startup floor; first try deferred at 9.949 GiB and retried) completed with
exit 0: **36 valid records, zero invalid, zero unexpected**, mean balanced
accuracy **0.2451** under the 0.35 limit, in the fresh batch
`runs/no_future_matched_control/893a7ea57fb2749e571c5b19591cead424357f1ebe382126ca2eb72b674d6a9f/`,
every record bound to source `88de6af5`, and the batch context pins the
newly published quality pointer bytes (`quality_bundle.status_sha256 =
152f972e…`, source `88de6af5…`). Historical batches, including the 1 October
`6523283e` set, remain preserved.

With this, the full settled-source validation chain on `88de6af5` is
complete for the first time since 1 October: guarded full quality (lint 0 /
strict types 0 / 1041 tests), the current-source raw audit, the 45
source-bound controls and the 36 no-future controls — each with preserved
receipts and independent audits where required. Engineering evidence only:
Gate A and the experiment freeze remain unsigned and no real case is
accepted.

## Windows qualification V3: sealed, executed twice, host-Job defect found: 3 October 2026, 23:30 UTC

The Windows-qualification package was repinned to `88de6af5` as V3
(`runs/coordination/windows_qualification_20261003_v3/`): complete
byte-substitution proofs from frozen V2 (five literal pairs plus intra-package
pin repinning), a fresh native runtime record, the seal check completed
(native parse 0 errors, plan exit 0, ruff exit 0, 33/33 runtime rows, 14
preserved originals intact), and independent reviews — a consolidated receipt
superseding an accidentally deleted first review
([incident record](../runs/coordination/windows_qualification_20261003_v3/receipt_incident_001.json)),
then `ACCEPTED_SEALED_PREPARATION_ONLY` from
[seal_review_001](../runs/coordination/windows_qualification_20261003_v3/seal_review_001.json)
with zero blockers.

Execution under pinned release records consumed two one-use attempts
(`winqual88de6af5a001/b002`, all receipts preserved; releases 001-003 were
unconsumed schema-learning steps, each supersession documented in the record
itself). Attempt b002 ran the full supervised chain in 1.6 seconds and
failed with the driver exiting 1 before any driver log. Root cause
established by reproducible probe and preserved in
[host_job_conflict_root_cause_001.md](../runs/coordination/windows_qualification_20261003_v3/host_job_conflict_root_cause_001.md):
**this host runs every session process inside a Job (flags 0x3000), Windows
nests Jobs, and the ceremony's child-side NULL-handle job query returns the
host Job rather than the ceremony Job**, so `current_job`'s exact comparison
can never pass under this host. The same pattern exists in the type-component
v5 child and retroactively explains the TYPE001 bootstrap refusal. A named-Job
repair is proposed in the root-cause record and left for the next session; no
guard was lowered and the qualification remains unaccepted (candidate_pass
false, accepted false, honestly recorded).

Diagnostics under
`runs/phase2/first_case_windows_qualification/diag88de6af5x001/` are
root-session probing artifacts (contract/driver/leaf/probe outputs), clearly
separated from the launcher's one-use attempt directories. The peer was
informed via
[closeout record](../runs/coordination/pro3_windows_qual_closeout_001.json),
including the honest disclosure that its request-002 acknowledgement never
arrived before execution and that the ceremony's failures were unrelated to
its workloads.

## Named-Job repair mechanism validated by probe: 3 October 2026, 23:40 UTC

The repair proposed in the Windows-qualification root-cause record was
validated under the same jobbed host: a child process opened the named
ceremony-style Job by name, read back its exact `0x2300` flags and both
6 GiB caps through an explicit handle, and verified its own membership —
all steps green (`repair_probe_out.txt` in the diagnostics directory). The
next session can implement the V4 package repair from a proven mechanism.

## Named-Job repair implemented through V4-V6 review iterations: 4 October 2026, 06:40 UTC

Under the next-session authorization (`runs/coordination/session_20261004_next.json`),
the validated named-Job repair was implemented as successive sealed packages,
each independently reviewed by the same reviewer agent whose blockers drove
the fixes:

- **V4** (`windows_qualification_20261004_v4`, manifest `c9a99c9a…`): the
  repair itself — `current_job` opens the named ceremony/per-leaf Job via
  `OpenJobObjectW`, verifies exact limits by handle and own membership via
  `IsProcessInJob`; the adapter names the ceremony Job
  (`pro3_winqual_{attempt_id}`) and the contract carries
  `ceremony_job_name`; leaves receive `--job-name` with cancel-root and
  grandchild sharing one name; caps/deadlines/pins updated. Review
  `repair_review_001.json` **REJECTED**: BLOCKER-001 — `leaf_verified`'s
  strict dict equality can never accept the additive `job_name` key.
- **V5** (`…_v5`, manifest `45a9208c…`): per-key comparison added. Review
  `repair_review_002.json` **REJECTED**: BLOCKER-002 — the generator used
  `is` (identity), which fails for large ints from `json.loads`
  (empirically demonstrated: `limit_flags` 8448 and 6 GiB/64 MiB caps are
  never identical).
- **V6** (`…_v6`, manifest `2f8aaacf…`): `==` equality with the strict
  boolean retained. Review `repair_review_003.json`
  **ACCEPTED_REPAIRED_SEALED_PREPARATION_ONLY** with zero blockers; the
  reviewer re-demonstrated acceptance for both cap classes, rejection of
  tampered flags, and tolerance of additive keys.

Release `release_001.json` (window 06:03–06:18Z) expired unconsumed:
available RAM stayed 5.7–7.5 GiB (largest holders: `vmmemWSL` 3.6 GiB —
preserved per the standing no-reclaim direction — Windows memory compression
and a security agent; neither project runs compute). An auto-launcher
(`windows_qualification_20261004_v6_build/auto_launch.py`) now gates on two
fresh ≥10.05 GiB samples, writes a fresh one-use release per try
(tags c004–c006) and invokes the sealed V6 launcher, bounded by the session
cap 17:45Z. No guard lowered; all V3-V6 packages, reviews and releases
preserved; the qualification remains unaccepted until a ceremony passes.

## First-case supervisor repinned and repaired for the current source: 4 October 2026, 07:45 UTC

While the qualification auto-launcher waits for RAM recovery, the next chain
step was prepared. The frozen M4b first-case supervisor
(`runs/coordination/first_case_supervision/`, binding source `9d32cb1a` and
the expired 2026-10-02 deadline) was repinned in two reviewed stages:

- **V1** (`first_case_supervision_20261004_v1/`): four literal pairs
  (source→`88de6af5`, both deadline forms→2026-10-04T17:45:00, the parent's
  deadline constructor), fresh native runtime record (33 rows, digest
  `1013164d…`), reverse-byte proofs. Review `repin_review_001.json`
  ACCEPTED_STATIC_PREPARATION_ONLY — but its point-7 note wrongly called the
  child's NULL-handle job query "distinct" from the host-Job defect.
- **V2** (`first_case_supervision_20261004_v2/`): direct inspection proved
  the child's `require_outer_job` does the exact flags/limits comparison
  against a NULL-handle `QueryInformationJobObject` — the identical
  cannot-pass defect under this jobbed host (the first real case would have
  refused at "verified outer6GiB … Job required before imports"). The
  validated named-Job repair was applied: the parent names the outer Job
  (`pro3_firstcase_{attempt_id}`), passes `--job-name`, and the child
  verifies by open-by-name, explicit-handle limits query and own-membership
  check. Review `repair_review_001.json`
  ACCEPTED_REPAIRED_STATIC_PREPARATION_ONLY with the point-7 correction
  retracted on the record; V1 and the frozen original are marked
  must-not-execute.

Both stages preserve their originals byte-exactly; all packages, reviews and
runtime records are under `runs/coordination/`. First-case execution
additionally requires the Windows qualification to pass first, a measured
Torch environment pin, a fresh scoped engineering admission, two 10 GiB
startup samples and root physical-exit witness. Gate A and the experiment
freeze remain unsigned.

## Audit sweep of unaudited session artifacts, remediation verified: 4 October 2026, 08:00 UTC

Per the user's instruction to audit the unaudited work, an independent sweep
([audit_sweep_001](../runs/coordination/session_20261004_next/audit_sweep_001.json))
examined every artifact this session produced without a prior receipt: the
auto-launcher, the four package build scripts, the hand-written release
record and the session ledger. Findings and outcomes:

- The auto-launcher's release generation was verified field-by-field against
  both the launcher's and the child's validation code — correct.
- **DEFECT-001 (real)**: the retry loop was inert (unconditional return
  inside the tag loop), so a launcher refusal would end the watch. Fixed by
  rewriting `auto_launch.py`: a real re-gated retry over six one-use tags
  (c004–c009), one-use existence checks on every release record, an
  `O_EXCL` single-instance lock, and a JSONL event log of every transition.
- **DEFECT-002 (false positive)**: the "two live instances" were a
  venv-launcher trampoline parent-child pair (child ppid == launcher pid) —
  one logical instance; both were terminated anyway and the new lock makes
  duplicates structurally impossible.
- The corrected state was independently re-verified
  ([audit_sweep_002](../runs/coordination/session_20261004_next/audit_sweep_002.json),
  REMEDIATION_VERIFIED): one live instance holding the lock, event log
  consistent, old PIDs gone, release semantics unchanged.
- Low-severity documentation items (build scripts partially generate the
  provenance chains; ledger wording) were recorded and stand as notes.

The launcher remains armed behind the unchanged 10 GiB gate.

## Windows qualification PASSES on the repaired V6 package: 4 October 2026, 10:35 UTC

After the user freed RAM at ~10:24 UTC, the audited auto-launcher's gate
passed and fired the sealed V6 ceremony under one-use release
`release_auto_c004.json` at 10:27:27Z. **All three scenarios passed in 8.45
seconds** — normal nested exit, exact owned-tree cancellation (live-PID
witness before termination) and the 64 MiB cap denying the 96 MiB allocation
— with the launcher observing its owned parent's physical exit 0 at
10:27:41Z. The attempt receipts record `candidate_pass`,
`validation_passed`, `source_stable` (88de6af5) and
`whole_job_cleanup_confirmed` true with `manual_review_required` false;
the named-Job repair is visible in the evidence itself (outer Job
`pro3_winqual_{attempt_id}` at 0x2300/6 GiB/6 GiB; per-leaf Jobs
`{ceremony}:{role}` at 0x2100 with the scenario-specific process caps).
Root acceptance is recorded separately per the ceremony's design
([root_acceptance_001](../runs/coordination/windows_qualification_20261004_v6/root_acceptance_001.json)),
and the independent post-run audit recomputed every hash, window and pin
([postrun_audit_001](../runs/coordination/windows_qualification_20261004_v6/postrun_audit_001.json),
ACCEPTED_QUALIFICATION_PASS_ENGINEERING_ONLY, zero blockers). This is the
first Windows-supervision qualification pass in project history; engineering
acceptance only — Gate A and the experiment freeze remain unsigned.

Immediately after, the next chain step began: the Torch environment pin via
the repaired M4b supervisor's `prepare-environment` mode. Release
`release_env_001.json` was written to the V2 package's schema; two launch
attempts were refused at the launcher's own two-fresh-10-GiB-sample gate
(RAM settled at 9.3–9.9 GiB). A dedicated RAM-gated auto-launcher is being
armed for it.

## Environment pin passes; first case attempt exposes the host-Job defect in project source: 4 October 2026, 12:50 UTC

The RAM floor was cleared by an explicit delegated decision
([wsl_shutdown_decision_001](../runs/coordination/session_20261004_next/wsl_shutdown_decision_001.json);
data-preserving VM restart under the user's "decide for me" delegation;
physical free RAM rose 8.16 → 12.94 GiB). Two further real defects were
found and fixed en route, then the chain advanced two full steps:

- The env-pin watcher was corrected to measure `ullAvailPhys` (the
  launcher's native metric) after psutil's standby-credited "available"
  produced phantom margins and seven futile release tags.
- The M4b supervisor V3
  ([API-drift repair](../runs/coordination/first_case_supervision_20261004_v3/repair_provenance.json))
  replaced the removed `primitive.create_deadline_lease` call with the
  current `DeadlineLease.open_or_create` (observed live as AttributeError
  in preserved attempts a017/a018).
- **The Torch environment pin then PASSED** (attempt envpin88de6af5b001,
  13.1 s): Torch 2.13.0+cu130, threads=1, deterministic algorithms on,
  full package/GPU inventory, source-bound at `88de6af5` — independently
  audited with zero blockers
  ([envpin_audit_001](../runs/coordination/first_case_supervision_20261004_v3/envpin_audit_001.json)).
- The full first-case prerequisite board was assembled with fresh
  schema-exact audits (quality, 45/45, 36/36, raw, environment,
  readiness), an engineering admission, execution pins and the 15-key
  inputs board (`first_case_prep_20261004/inputs_v1.json`, sha
  `e9f657df…`).
- The **first real Cho engineering case was launched** (EEGNet /
  subject_01 / seed 11, execute mode, release `release_exec_c001.json`).
  The whole supervision chain worked — launcher, named-Job parent,
  sweep admission, contract, staged child — and the innermost engineering
  child refused with
  `SupervisionError: child is not inside the exact capped kill-on-close
  Job`. Diagnosis: **the same host-Job NULL-query defect, third
  occurrence, this time in project source**
  (`evaluation/phase2_cho_execution.py:340-356` — NULL-handle
  `QueryInformationJobObject` with exact flag/cap comparison). The
  attempt is preserved with quarantined staged outputs and a manual
  recovery record; nothing was retried.

The repair is known and validated (the named-Job pattern, twice proven),
but it lives in project source: fixing it moves the canonical pin off
`88de6af5` and requires the matching revalidation cascade (pin, scoped
checks/full quality, fresh environment pin, fresh inputs board) before
the case can relaunch. That cascade is the staged next action.

## Named-Job repair applied to project source: 4 October 2026, 13:25 UTC

The first real case's innermost-child refusal (third host-Job NULL-query
occurrence) was repaired in `evaluation/phase2_cho_execution.py`: the child
now verifies the exact **named** engineering Job
(`_require_capped_job(memory_limit, job_name)` opens it via
`OpenJobObjectW`, checks the limits through that handle and its own
membership via `IsProcessInJob`, refusing when unnamed), the contract
carries `job_name` (`pro3_choexec_{uuid}`), and `supervise_attempt` wraps
the default `run_supervised` with `_named_job_supervisor` — a scoped
class-replacement of the primitive's API class that rebinds `create_job`
per instance (the proven V6/M4b pattern). The first wrapper draft used a
class-attribute patch that the independent audit proved could never work
(`create_job` is bound per-instance in `__init__` — audit-001 REJECTED
with live reproduction); the stopped quality run on the intermediate pin
`a87a1615` certified nothing. The corrected repair was verified live
end-to-end (a real child inside the named Job executed
`_require_capped_job` successfully), passes ruff + strict mypy + 46
focused tests, and was re-audited
([source_repair_audit_002](../runs/coordination/next_step_20261004_source_repair/source_repair_audit_002.json),
ACCEPTED_SOURCE_REPAIR_VERIFIED, zero blockers; a wrapper-path regression
test is a recorded advisory). Canonical pin:
`62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0`; a
guarded full-quality pass on this pin is running and its receipt is the
authoritative current-source quality evidence. The M4b supervisor was
repinned to the new source (V4 package, fresh runtime record).

## Machine-state lessons and staged chain after the source repair: 4 October 2026, 14:22 UTC

Three guarded quality attempts on the repaired pin `62536382` stopped
honestly at the RAM floors (receipts preserved: `guarded` at the 4 GiB
active floor with WSL regrown to 6.5 GiB; `guarded2` at the same floor
within 21 s; `guarded3` at the startup floor with WSL at 7.7 GiB at the
launch instant). Root cause identified by process forensics: an
**interactive Ubuntu session launched from explorer.exe**
(`wsl.exe --cd ~`) restart-cycles a ~6–8 GiB VM every few minutes. The
coordinator's WSL shutdown under the 3 October delegation remains valid
([decision record](../runs/coordination/session_20261004_next/wsl_shutdown_decision_001.json))
and enabled the qualification and environment-pin passes earlier; a
service hold was attempted and recorded
([record](../runs/coordination/session_20261004_next/wsl_service_hold_decision_001.json))
but did not hold. The user's own session is not closed by the coordinator.
A patient auto-retry
([quality_retry.py](../runs/coordination/session_20261004_next/quality_retry.py))
fires the pass when WSL stays down 60 s with ≥10.5 GiB free (fresh one-use
directories g4–g11, deadline 17:45Z), and the user has been asked to close
WSL for ~35 minutes if they want the chain sooner.

Operational notes recorded for future sessions: (1) my truncated
`MEMORYSTATUSEX` probes read 0.0 garbage — the launcher's full-struct
native gate is authoritative; (2) the M4b V4 package
(`first_case_supervision_20261004_v4`) repins the supervisor to `62536382`
with a fresh runtime record and a pre-built environment-pin release whose
window must be refreshed at fire time; (3) the first-case prerequisite
board (`first_case_prep_20261004/inputs_v1.json`, sha `e9f657df`) binds
the previous pin `88de6af5` and must be regenerated (fresh audits,
admission and inputs) after the new environment pin lands. The failed
first-case attempt `execcase88de6af5c001` remains preserved with
quarantined outputs and a manual recovery record.

## Quality pass on the repaired source after a day of RAM contention: 4 October 2026, 17:58 UTC

The repaired pin 62536382 got its guarded full-quality pass on the fifth
honest attempt of the day. Attempts guarded4-6 were refused at the startup
floor seconds after watcher gates of 10.14-10.20 GiB (the boundary flaps
~0.3 GiB within seconds; receipts preserved), and guarded7 was killed by the
safety floor 16 minutes in when the user's WSL VM returned mid-run (min RAM
3.93 GiB). The user then closed WSL deliberately and held it closed;
guarded8 ran clean 16:54:04-17:29:31Z (lint/types/tests exit 0, min RAM
10.62 GiB) and published the pointer (09df1f6b...; the 88de6af5 pointer
152f972e... preserved). An independent subagent audit recomputed 57 checks
and accepted it (ACCEPTED_QUALITY_PASS_ENGINEERING_ONLY, zero blockers;
1041 passed / 3 skipped / 1121 subtests).

Operational lessons recorded: (1) killing another session's background task
makes its harness respawn it ~60 s later - suspend (NtSuspendProcess) is the
durable neutralization, and the respawn/interference is documented in
session_20261004_next/old_retry_respawn_note_001.json; (2) a two-sample RAM
gate at the floor is insufficient - the watcher now requires three samples
spanning the launcher's own startup re-sampling delay (~32 s); (3) the WSL
VM re-absorbs any RAM the user frees within minutes, so a sustained window
requires the VM actually down for the whole run.

With the pointer authoritative, the chain advanced rapidly: the fresh Torch
environment pin passed supervised inside the original deadline (release
b003, candidate_pass, ~13 s child), the 45 source-bound controls (45/45,
mean 0.2486) and 36 no-future controls (36/36, mean 0.2451, raw writer
verified) re-ran on the pin in fresh namespaces, and the 52-source raw
verifier was repinned and passed (10.7 GB rehashed). Because the supervisor
launcher's hardcoded 17:45Z global deadline passed during the RAM wait, a
V5 package extends only that literal to 21:00Z (reverse-provable
substitution, provenance + independent static review in the package dir);
the fresh prerequisite board was delegated to an independent subagent. Gate
A and the experiment freeze remain unsigned; nothing here is a scientific
result.

## First real Cho engineering case completes after measured cap recalibration: 4 October 2026, 19:35 UTC

The fresh prerequisite board (first_case_prep_20261004_v2, 74 checks) caught
four real launch blockers before execution: V5 was structurally unlaunchable
(parent.py and design.json carry their own 17:45Z deadline literals),
recorder state from the failed 88de6af5 attempt blocked the case claim
(resolved by deliberate bit-exact quarantine relocation), the working tree
was dirty relative to the env pin's captured source (resolved by reverting
the deviation-log edit until post-run), and the controls36 audit pins the
live session ledger (ordering constraint). The V5->V6 package fix was itself
REJECTED by its review (a build-loop overwrite left one design.json literal
unsubstituted - exactly why every package gets an independent review); V7
passed.

The first execute attempt (c002) then exposed the real memory envelope: the
inner CLI died at its first-fold data load with a numpy MemoryError, and the
kernel-tracked parent receipt proved the 6 GiB AGGREGATE Job cap was hit
exactly (peak_job 6.001 GiB; single process only 3.38 GiB). The case
receipt itself labels the cap "initial_unmeasured_engineering_probe; no
production cap ratified", so the designed path was measured recalibration:
V8 raised only the aggregate cap to 7.5 GiB (process stays 6 GiB, keeping
the source ceiling and pin 62536382 untouched) - and was REJECTED by review
(the parent's post-run peak gate still bounded aggregates at 6 GiB); V9
fixed that and was REJECTED again (the child's contract validation still
compared aggregates to the 6 GiB constant - inherited from V8 and missed by
its review); V10 passed an exhaustive 42-site inventory review.

c003 then ran the fixed case (EEGNet / subject_01 / seed 11 / 5 shots) to
completion in 244 s under supervision_reason normal: process peak 4.05 GiB,
aggregate peak 6.673 GiB (inside the recalibrated cap, proving the
measurement right), exactly one accepted engineering cell published
(balanced accuracy 79/160 on the 160-trial query with bound selection
evidence), success record and publication intent durable, parent
attestation present, no recovery required. The native launcher then
rejected at its own final validation - a never-exercised field-name defect
(it checks result.completion.measured_cases while the child schema emits
'measured'; every real field matched). Recorded as a launcher finding for
future cases; the published cell stands on the recorder's own acceptance.
All failed attempts (c001, c002, guarded4-7, V6/V8/V9 packages) are
preserved with their receipts. Gate A and the experiment freeze remain
unsigned; the balanced-accuracy number is engineering output, not a
scientific claim.
