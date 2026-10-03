# Scientific freeze draft - Phase II E2 contract specification

**Engineering cohort update, 23 September 2026:** The versioned 60 Hz Cho
Profile B cohort passed a 52/52 artifact, historical-hash, trial-join and
five-shot binding audit; subject 01 passed the predeclared 60 Hz signal
diagnostic. See the [real-cohort review](cho_60hz_real_cohort_review_20260923.md).
This does not ratify the full scientific freeze or admit evaluation cells.
The earlier draft and decision-time language below remain historical.

## Owner scope and preprocessing update - 23 September 2026

The owner selected `labram_linear`, `labram_lora`, `labram_full` and
`eegnet` for the first exploratory Cho2017 five-shot tranche and deferred
`ea_tangent_lr` to a separately predeclared and costed comparison. This
sets a 1,040-cell/selection planning scope and the existing 1,893.4
CPU-hour no-reuse proxy with 1.25 allowance. It does not ratify the full
scientific freeze or admit work. The earlier five-method 1,300-cell
planning manifest remains preserved as a comparison option, not the
selected first-tranche manifest.

The owner also chose preparation of a newly versioned 60 Hz Cho2017
Profile B path to align with the dataset's 60 Hz line-frequency metadata.
The shared 50 Hz config and historical artifacts remain untouched. This was
the decision-time preparation instruction; the separate 60 Hz cohort was
subsequently generated and audited for all 52 subjects, as recorded above.
Scientific use still requires the full freeze and complete-work admission.

The 19 September draft below predates these owner choices. Its secondary
analysis families, proposed candidate settings, full resource envelope
and execution prerequisites remain open.

19 September 2026, reconciled at milestone 46; selector repair at milestone 47.
**Draft for owner review and
ratification; no scientific execution is admitted.** This corrects the
milestone-44 draft against the saved pilot and current selector source.
The original draft is preserved in the milestone-46 baseline. The
[reconciliation review](freeze_reconciliation_review.md) records every
correction, adopted interpretation and unresolved execution prerequisite.
Historical receipts and frozen Phase I records are unchanged.

## 1. Methods, primary tranche and preprocessing

The nine-method roster is the six LaBraM systems `labram_linear`,
`labram_full`, `labram_partial`, `labram_lora`, `labram_adapter`,
`labram_support_prompt`; the separate `tcpl` local reconstruction; and
the `eegnet` and `ea_tangent_lr` anchors. Author parity for TCPL is unverified.

The owner selected **linear, LoRA, full tuning and EEGNet** for the first
exploratory Cho2017 five-shot tranche on 23 September 2026. Full tuning
remains the configured regularization reference. EA-tangent stays in the
nine-method roster but is deferred to a separately predeclared and costed
comparison. The earlier pilot's five-method option is retained below for
planning comparison; it is not the selected first tranche.

The primary comparison remains **LoRA minus linear probe, Cho2017, five
shots, subject as unit**, using within-subject seed means, balanced
accuracy, the configured paired Wilcoxon-Pratt superiority test and 95%
confidence level. The separate configured equivalence comparison retains
alpha 0.05, the 90% interval and the frozen H2 margin
0.05202907926797159 (5.20290793 percentage points).
`analysis.toml` still marks secondary families as pending; this draft
does not silently declare additional confirmatory comparisons. Secondary
family definitions must be explicit before their experiments are admitted.
The [decision packet](freeze_decision_packet_20260923.md) proposes an empty
secondary superiority family for this first tranche, with full tuning and
EEGNet reported descriptively. That proposal is not adopted here. The owner
also needs to settle whether the separate configured TOST equivalence test
is a formal claim or a prespecified exploratory analysis before ratification.

Profile A/B preprocessing, dataset montages/classes, frozen thresholds,
nested fixed-earliest support and fixed common queries are unchanged.
The MMIDB upsample-before-filter policy remains as audited. No score is
used to change methods, support pools or training budgets.

## 2. Proposed candidate counts and budgets; measured settings distinguished

The following retains the milestone-44 proposal for owner review. These
are **proposed settings, not ratified settings or a convergence claim**.
For the SGD methods, the two ordered candidate slots pair the same
learning rate in source and support: slot 0 uses 1e-3; slot 1 uses 2e-3.
This makes the earlier unspecified learning-rate scope explicit. All
other settings must be pinned in executable candidate configurations
before execution; this document and the planning manifest are not those
configurations.

| Method | Ordered candidates | Source steps/subject | Target/inner support updates |
| --- | --- | --- | --- |
| labram_linear | lr 1e-3, 2e-3 | 1 | 1 |
| labram_lora | lr 1e-3, 2e-3; rank 4, last-block QKV | 1 | 1 |
| labram_full | lr 1e-3, 2e-3 | 1 | 1 |
| labram_partial | lr 1e-3, 2e-3; depth 2 | 1 | 1 |
| labram_adapter | lr 1e-3, 2e-3; width 4, last block | 1 | 1 |
| labram_support_prompt | lr 1e-3, 2e-3; 2 tokens, hidden 8 | 1 | 1 |
| tcpl | Adam lr 1e-3, 5e-4 | 1 | 0; frozen support conditioning |
| eegnet | lr 1e-3, 2e-3 | 1 | 1 |
| ea_tangent_lr | C 1.0, 2.0 | classical refit | source-plus-support classical fit |

TCPL's pilot source episode uses one support and one query example per
class: **four trials on two-class Cho, eight on four-class BCI**. Eight
is the engineering ceiling, not the size of every dataset's episode.
TCPL does not take a target support-gradient step.

The pilot scripts actually measured all six LaBraM methods at source and
support lr **0.01**, EEGNet at 0.001, EA at C=1.0 and TCPL at Adam
lr=0.001. They did not measure both proposed candidates. Plain LaBraM,
LoRA and adapter source batches contained two trials; EEGNet used four;
prompt source episodes used one support and one query trial per class;
query batches were eight. The separate throughput probes used eight-trial
batches, with the prompt probe timing its support wrapper. Their per-step
numbers cannot be substituted as exact source-fit costs for these different
batches or interpreted as proof of convergence. Candidate changes and
longer training require a compatible measured envelope before admission.

## 3. Selection, seeds and stopping rules proposed for ratification

Complete source-subject LOSO means **N-1 inner folds per candidate** for
an N-subject cohort. Each inner fit uses N-2 subjects, excluding the
outer target and inner validation subject. Cho has 51 inner folds, 50
training subjects per inner fit and 51 sources in the fresh final fit.
BCI has 8 inner folds, 7 inner training subjects and 8 final sources.
MMIDB counts depend on the unresolved episode-eligibility policy.

Every candidate must complete every declared inner fold. Select by exact
rational mean balanced accuracy with equal subject weight and declared
candidate order for ties; no early stopping or score-dependent expansion.
Neural winners receive a fresh final source fit. EA selects settings and
refits source-plus-support inside target prediction, with no extra saved
final neural fit. The source implementation issues in section 7 must be
resolved before this intended contract can be claimed as executed.

Model seeds are **11, 23, 37, 53, 71**. They do not resample support.
The workload baseline assumes a separate selection for every target,
method, shot level and seed. It credits **no unverified reuse**. In
particular, deterministic EA predictions do not authorize dropping seed
cells or reusing selection evidence without an explicit compatible
provenance contract. Source reuse across shots is also not assumed:
support-dependent inner selection can change the winner.

## 4. Failure policy proposed for ratification

Keep immutable failed attempts and allow at most one linked retry with
identical scientific identity. A retry requires the cause to be resolved
and fresh admission; it is not an instruction to retry a failing guard.
A second failure ends the case without a cell. Guard failures stop the
session before the next unit. No deletion, cohort reduction, changed
scientific criterion or weaker guard is recovery.

## 5. Corrected workload proxy; complete resource envelope still unknown

For each primary method there are 52 targets x 5 seeds = **260 selections**.
Each selection needs 2 candidates x 51 folds = **102 inner evaluations**,
then a final source fit plus target support/query for neural methods, or
one target source-plus-support refit for EA. The five-method tranche has
**1,300 selections**, not 260 across all methods.

The following transparent CPU timing proxy uses maxima of source and
target stages from the three saved Cho five-shot repetitions (milestones
38-39). It reuses the 51-source outer-case stage sum for each 50-source
inner fold, without a linear source-count discount:

`per-method proxy seconds = 260 x (102 + 1) x (max_source_s + max_target_s)`.

The final +1 includes the neural final fit and target evaluation together;
EA's source cost is already inside its target-stage time. Neither is
charged twice. The maximum of each stage may come from a different
repetition. These are conservative inputs relative to the observed
repetitions, **not a proven upper bound on unseen subjects or candidates**.

| Method | Max source s | Max target s | Proxy hours | With 1.25 retry allowance |
| --- | --- | --- | --- | --- |
| labram_linear | 43.303 | 11.158 | 405.1 | 506.4 |
| labram_lora | 43.851 | 12.120 | 416.4 | 520.5 |
| labram_full | 59.131 | 12.690 | 534.3 | 667.8 |
| eegnet | 20.454 | 0.913 | 158.9 | 198.7 |
| ea_tangent_lr | 0.000 | 357.907 | 2,662.4 | 3,328.0 |
| Four neural methods | | | 1,514.7 | **1,893.4** |
| All five methods | | | 4,177.1 | **5,221.4** |

This supersedes the unsupported 10-20 neural-hour / 350-450 EA-hour
claims. It is a **planning proxy, not an admitted compute budget or a
wall-clock completion promise**. The pilot did not time a complete Cho
selection, both candidates, or all subjects. Cho query sizes vary; the
timed development target has 160 common queries. Startup/data preparation
outside the case timer, selection bookkeeping, persistence/audit,
checkpoint and intermediate-data retention peaks, control refresh,
cooling and waits are not priced. The 1.25 multiplier is a planning
allowance, not a guaranteed bound on failures or those missing costs.
The complete resource envelope remains unknown.

The 30,240-cell expanded grid (168 targets x 9 methods x 4 shots x 5
seeds) remains a conditional planning count. Its MMIDB portion is blocked;
no complete-grid compute budget is asserted. Similar per-case time across
shots does not remove the shot axis from total work.

## 6. Reviewable cell/dependency manifest

The saved [planning manifest](../../runs/phase2/freeze_reconciliation/20260919_step46/planning_manifest.json)
enumerates all 1,300 proposed primary cells and their selection dependency
keys, audited episode digests and source-partition digests. Each referenced
source-partition record explicitly lists all 51 inner folds and their 50
training subjects. Each fold is evaluated for both ordered candidate
slots. These are planning identities, not runnable `CellIdentity` objects:
candidate configuration, initialization/checkpoint and execution-environment
identities must still be bound before claiming work.

| Dependency, no reuse assumed | Earlier five-method option | Selected four-method first tranche |
| --- | --- | --- |
| Target cells / complete selections | 1,300 / 1,300 | 1,040 / 1,040 |
| Candidate/inner-fold evaluations | 132,600 | 106,080 |
| Neural inner fits | 106,080 | 106,080 |
| Neural final fits | 1,040 | 1,040 |
| Neural source gradient steps | 5,357,040 | 5,357,040 |
| Neural support steps, inner plus target | 107,120 | 107,120 |
| EA inner plus target classical fits | 26,780 | 0 |

Counts are independently enumerated against all 52 saved Cho selection
records and checked against closed-form arithmetic. No source fit is
implicitly shared across target, candidate, method, seed or shot level.

## 7. Execution prerequisites and owner decisions

**Ratification alone does not make current execution ready.**
[Milestone 47](selector_arithmetic_review.md) repaired the verified
arithmetic defects: EEGNet and EA admission now count the actual cohort,
and LaBraM means use the actual inner-fold count. New metadata names the
actual dataset and permitted source cohort. Historical evidence remains
unchanged; the earlier defects and their discriminators are recorded in
the milestone-46 review.

Remaining limits at the proposed Cho settings:

- LaBraM and EEGNet each require **5,253** gradient steps for complete
  two-candidate selection before target adaptation, exceeding the unchanged
  **256** ceiling. TCPL remains at **5,151** source steps and also refuses.
- EA requires **102** inner classical fits. Its accounting is now correct;
  this does not grant scientific or resource admission to execute them.
- The recorder and target adapters remain bounded engineering components.
  A complete scientific selection/execution path must retain the guards
  and satisfy the scientific, provenance and compute prerequisites.
  Splitting calls to evade a ceiling, increasing it or invoking private
  fitting helpers is not admitted by this repair.

The milestone-47 real-cohort check stopped before fitting: no scientific
selection, target predictions or cells were produced. Full scientific
execution remains unadmitted.

Owner decisions remain full freeze ratification (including the proposed
scientific budget), MMIDB episode eligibility, Gate A acceptance and any
commit/push authorization. The first-tranche EA scope and the plan to prepare
a 60 Hz Cho Profile B version were decided on 23 September; neither choice
admits preprocessing or scientific execution. Secondary families and executable
candidate configurations also need completion before the relevant scope
can be admitted. Experiments require committed configurations under the
standing rule, while commits remain prohibited until the owner authorizes
them and current-source controls pass. Ratification does not silently
waive that provenance prerequisite.

Fresh compute admission is mandatory: the pilot's below-disk-floor
deviation does not cover E2. The 20 GiB disk floor, RAM/GPU/cooling guards
and deferred 10 GiB RAM startup condition for control refresh are unchanged.
This milestone neither refreshes controls nor measures current resources.
Gate A stays unsigned; all Phase II results remain exploratory.
