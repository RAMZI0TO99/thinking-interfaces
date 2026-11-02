# Project plan — Thinking Interfaces

Updated **29 October 2026 (Asia/Riyadh)**. This roadmap uses the adopted research
decisions and retained engineering evidence. Execution ownership, independent
review and admission are local to this project under the
[project execution policy](../PROJECT_EXECUTION_POLICY.md).

The [local validation contract](../phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [preparation foundation](../phase2/cho51_p3_validation_foundation_20261029.md) is
implemented and independently source-reviewed: strict records, bounded supplied
dependency snapshots, streaming hashes and drift checks;31 tests are unexecuted. This
source step does not provide native custody, complete dependency coverage or an
operational grant. The next runnable component is a separately reviewed Q
supervisor with fresh source/runtime pins, admission and actual-result review.

The [accepted v8 inventory](../phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

## 1. Purpose and research question

Thinking Interfaces investigates cross-subject EEG motor-imagery decoding and
its eventual use in a reliable brain–computer interface. The central research
question is:

> Does a pretrained EEG encoder, adapted using a small, explicitly limited
> target-subject support set, improve held-out decoding over credible baselines?

The immediate primary contrast is **LaBraM with LoRA minus LaBraM with a linear
probe**, using balanced accuracy. Full fine-tuning is a reference for the
small-support regularization question; EEGNet is a separate compact-architecture
anchor. A useful interface is a longer-term objective, not an already established
consequence of offline accuracy.

The project has three separate success criteria:

1. **Engineering correctness:** authentic inputs, leakage-resistant partitions,
   correct adaptation, immutable query state, trustworthy records and bounded
   execution.
2. **Scientific validity:** an adopted experiment, justified eligibility and
   provenance claims, complete held-out results and appropriate paired analysis.
3. **Practical usefulness:** meaningful command performance, causal signal
   processing, usable acquisition-to-command latency and controlled false
   activations. A transport demo alone does not satisfy this criterion.

## 2. Scope: the current tranche versus the wider program

### Adopted first tranche

The [13 October owner amendment](../phase2/cho_51_target_amendment_adoption_20261013.md)
supersedes the old 52-target evaluation scope, without rewriting its history.

| Item | Current first-tranche contract |
| --- | --- |
| Primary dataset | Cho2017, left/right-hand motor imagery |
| Evaluation population | 51 targets: subjects 02–52 |
| Available source cohort | All 52 subjects; for each target, 51 non-target sources |
| Methods | `labram_linear`, `labram_lora`, `labram_full`, `eegnet` |
| Training seeds | 11, 23, 37, 53, 71 |
| Support condition | Five trials per class, from the adopted nested fixed-earliest support pool |
| Required roster | 51 targets × 4 methods × 5 seeds = **1,020 evaluation cells** |
| Primary unit | Subject, after averaging the five seeds within subject |
| Source selection | Exact adopted two-candidate method templates; up to 5,253 source/inner-support updates per case, not 5,253 target updates |
| Current scientific completion | **0/1,020 accepted final scientific cells** |

Subject01 is excluded as an evaluation target but remains eligible as a source
and inner-validation subject for other targets. Its original exhausted case has
two spent attempts and zero remaining; neither renaming a case nor this roadmap
resets that history.

The support design reserves a maximum pool of the first 20 retained trials per
class. Five-shot uses its first five; the common query set lies outside the
whole maximum support pool. The other 15 pool trials are not query examples for
the five-shot condition. Training seeds do not resample support. “Earliest” is
available within-class loader order, not a recovered global acquisition timeline.
See the [decision register](../phase2/decision_register.md).

### Wider research program: conditional, not current execution scope

The [revised Phase II research plan](../phase2_v2/BCI_Phase2_Research_v2.md)
describes a broader program:

| Workstream | Scientific purpose | Relationship to the first tranche |
| --- | --- | --- |
| E2: adaptation | Compare adaptation systems, shot levels and datasets | The four-method Cho five-shot tranche is the immediate bounded subset |
| E1: checkpoint probe | Investigate matched masked-prediction behavior and exposure-related questions | Requires a verified compatible tokenizer/head; observational contrasts cannot prove training membership or causal memorization |
| E3: causal decoding | Test streaming decisions, latency, abstention and false activations | Requires a genuine causal signal path and deployment-style evaluation |
| E4: montage study | Separate channel ablation from a genuinely reduced-electrode system | Requires montage-specific preprocessing and matched comparisons |
| Optional expansion | Partial tuning, adapters, support prompts, TCPL, EA-tangent, additional datasets/backbones | Separately specified, costed and admitted; not silently added to the 1,020-cell denominator |

BCI IV 2a and MMIDB remain useful development/secondary datasets. Their historical
benchmark results do not complete new Phase II comparisons. MMIDB also needs
especially careful pretraining-overlap disclosure. The wider planned roster
contains six LaBraM systems, the separate TCPL architecture and two anchors;
that is not the current four-method commitment.

## 3. The intended experimental pipeline

1. **Authenticate the study and inputs.** Bind the adopted owner decisions,
   case roster, configurations, source/runtime identities, original recordings,
   processing views, checkpoint and permitted provenance claims.
2. **Construct partitions.** Hold the outer target out of source development;
   keep source-only inner validation separate from target support and query.
3. **Select source settings.** Use the declared two-candidate procedure and
   complete subject-disjoint fold evidence. Preserve failed cases and selection
   lineage instead of choosing settings using final target-query scores.
4. **Publish a selected source artifact.** Bind its recipe, complete selector
   evidence, weights and tensor state to the actual historical producer.
5. **Restore under a current executor.** Authenticate the producer separately
   from the current executor and recorder; restore strictly without falsifying
   a shared source identity.
6. **Adapt using support only.** Update only the intended parameters under the
   adopted method-specific settings. Do not use query labels for selection,
   normalization fitting, stopping, loss or updates.
7. **Evaluate once under the admitted case contract.** Query in evaluation mode,
   demonstrate unchanged query-time state and persist authenticated measured
   predictions and receipts. Engineering-success terminals are not measured
   evaluation cells.
8. **Collect the complete roster and analyze.** Reconcile every retained case,
   failure and provenance binding before computing the subject-level contrast.

The existing platform implements many of these pieces. The full current
production composition and its scientific admission are not yet established.

## 4. Work in dependency order

| Package | Work and dependencies | Completion evidence |
| --- | --- | --- |
| Custody-resolution specification | Completed design and three local schemas;48 acceptance scenarios specified | Independent design review accepted; later implementation evidence is scoped separately; no actual boundary qualified |
| Historical custody evidence | Existing negative intake remains UNRESOLVED;16 v7 tests passed but all six Sysmon reads denied | Historical host, restart and cleanup remain unqualified |
| Present-byte inventory | Adopted scoped v8 contract;19 tests and separate742-file observation accepted | Declared current bytes only;572 predecessors preserved |
| Local validation contract | Design independently accepted;117 cases,34 successor controls,26 qualification scenarios and Q/P/L/V/C stages specified | Static acceptance only; implementation-specific adoption and separate admissions remain required |
| Preparation and qualification implementation | Build supplied-data foundation, then reviewed native reader and Q supervisor; independently qualify before P/L/V/C | Fresh retained closure, guarded collection,117/34 results and complete owned lifecycle; independent actual review at each stage |
| P3 adapter integration | Compose accepted metadata/profile mapping, telemetry and the provenance-aware linear backend without creating scientific authority from metadata | Focused tests and a separately scoped engineering transaction, honest counters and complete closeout |
| Remaining method chains | Complete current EEGNet, LoRA and full-tuning selection/restoration/target/parent composition where missing | Method-specific parameter-change, query-state, provenance, failure and resource evidence |
| Operating feasibility | Measure representative complete workloads, including preparation, selection, persistence, audits and recovery | Measured cost/storage/RAM envelope and a viable complete-roster attempt/recovery plan |
| Scientific eligibility and freeze | Resolve checkpoint-specific cohort/overlap treatment, method versions, protocol, analysis and feasible operating plan | Defensible permitted claims and the separate final owner freeze decision |
| Admitted study | Execute the exact retained roster after all applicable engineering and scientific gates | All 1,020 required cells accounted for with authentic measured records |
| Analysis and release | Apply the adopted paired analysis, regenerate tables/figures and review limitations | Traceable results, independent review and appropriately scoped publication claims |

P3 adapter and telemetry design were completed on 27 October. Metadata/profile
mapping and supplied-telemetry contracts were then implemented and statically
reviewed. Diagnostics005 added bounded failure metadata and passed static
review on 28 October. These milestones do not establish runtime qualification.

The successor must replace old launcher policy bindings with the current local
protocol. Do not remove a guard from a frozen script or reuse a consumed attempt
to make it run. Preserve the actual004 failure, incomplete custody and unknown
refused-row/cleanup facts. Documentation policy supersession alone cannot
establish successful historical cleanup.

### Timing and operating feasibility

The accepted numerical engineering composition took **590.082323 seconds**
inside a 600-second native Job: **9.917677 seconds** of arithmetic headroom in
one observed run. This is not a production reliability distribution or a
complete real-data case budget. Preserve mandatory verifiers and resource
limits; evaluate timing changes in a separately reviewed engineering successor.
The [interface audit](../phase2/cho51_canonical_pipeline_interface_audit_20261025.md)
records the original compatibility and timing findings.

## 5. Analysis contract to preserve

Use the [12 October adopted choices](../phase2/cho_design_decisions_20261012.md)
with the [13 October population amendment](../phase2/cho_51_target_amendment_adoption_20261013.md),
not an older planning paragraph:

- Average exactly five seed results within each subject, then form **51 paired
  LoRA-minus-linear differences**. The 1,020 cells are not 1,020 independent
  participants.
- Primary superiority uses the declared one-sided Wilcoxon signed-rank test:
  Pratt zeros, asymptotic calculation, no continuity correction, alpha .05 and
  the adopted exact rank/tie-preserving encoding. Superiority additionally
  requires an unrounded p-value below .05 and a strictly positive exact paired
  arithmetic mean. All-zero differences give p=1; other nonfinite results stop
  analysis.
- Display the separate 95% paired-mean Student t interval with **50 degrees of
  freedom** under its stated assumptions. Zero variance gives a point interval.
- The secondary superiority family is **empty**. Other first-tranche methods
  and contrasts are descriptive, not undeclared confirmatory tests.
- The margin **±0.05202907926797159 balanced-accuracy units** (about ±5.203
  percentage points) is planning-derived. Its paired-mean estimate and 90%
  interval are **exploratory** under the adopted decision. Do not report formal
  TOST equivalence, clinical interchangeability or guaranteed power from the
  older proposal.

A negative or inconclusive result is a valid possible study outcome. Passing
engineering checks never guarantees that LoRA will outperform the linear probe.

## 6. Project execution and scientific gates

Use the current [handoff](../../HANDOFF.md),
[execution policy](../PROJECT_EXECUTION_POLICY.md) and
[agent coordination rules](../../AGENT_COORDINATION.md). The project lead owns
the bounded plan and admission; a different project reviewer checks source and
actual results. Source authoring and result acceptance remain distinct roles.

Before execution, establish a settled source version, current source/runtime
pins, available resources, an unused attempt/output directory, a bounded
operation and complete owned-process cleanup. Retain directly applicable
phase-specific resource amendments and all remaining time, memory, thread/GPU,
disk and custody protections. Availability is checked locally; old observations
do not establish current resources.

The current scope is engineering-only. Gate A's narrow retrospective acceptance
does not establish checkpoint independence or sign the final experiment freeze.
No former autonomous window, old launcher or saved receipt admits a new run.

## 7. Schedule and definition of completion

There is no defensible calendar completion date yet. The older 45-working-day
schedule is a historical planning horizon. Resolve the current custody and
contract-validation blockers, then measure representative current workloads
before estimating complete-study time, storage growth and recovery allowance.

The immediate engineering milestone is a reviewed and validated successor with
complete ownership/cleanup evidence and the pending nonnumerical tests resolved.
The first-tranche scientific milestone requires the full authentic roster,
adopted analysis and scoped conclusions. Wider E1/E3/E4 work and useful live
brain control remain separate deliverables.

## 8. Owner decisions needed later

No further answer is needed for this documentation update. Later decisions may
concern authenticated checkpoint provenance, a scientifically defensible
treatment of unresolved exposure, the final named experiment freeze, or wider
datasets/methods/hardware and operating budgets. Existing project authorization
and applicable resource choices are retained; this roadmap does not reopen
questions that the owner has already answered.

See [PROGRESS_REPORT.md](PROGRESS_REPORT.md) for completed work and
[LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) for the studies behind the design.
Historical documentation is retained in the
[history manifest](../history/project_focus_20261028/manifest.json).
