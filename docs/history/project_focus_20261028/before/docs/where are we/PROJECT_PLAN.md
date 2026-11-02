# Project plan — Thinking Interfaces

## Publication checkpoint, 28 October 2026

The [publication record](../phase2/cho51_push_checkpoint_20261028.md) collects
the completed engineering work and this project overview. Exact P3 sources,
failed bootstrap records and static reviews are preserved in the
[P3 archive](../../evidence/cho51-p3-source-checkpoint-20261028/README.md).

The immediate next step is **custody-resolution design and independent review,
followed by a distinct successor implementation**. Bootstrap004 remains failed
and unreleased; diagnostics005 remains static-only and deliberately launch-held.
The 117 candidate tests and 34 controls are still unexecuted. Source014 expired;
Pro2 reports Source015 closed unadopted. No runtime or scientific validation is
added by publication; scientific cells remain 0/1020 and the freeze unsigned.

Earlier dated sections below preserve the history of their own checkpoints.

**28 October milestone:** diagnostics005 source and independent static review are
complete; actual exercise remains deliberately held. Next: separately coordinate
and review custody-resolution design plus a distinct successor. No ordinary005
grant can resolve unknown004custody; no rerun,Boolean shortcut,native request or
scientific execution follows. [Current bounds/status](../phase2/cho51_p3_custody_diagnostics_20261028.md).

**Latest next action,27 October17:17UTC:** the independent review of the actual
failed/unreleased bootstrap004 packet is complete. Plan bounded refused-row and
cleanup-stage diagnostics in separate sources. Preserve its consumed
identity; no automatic retry or conditional native request. The refused process
row was not saved,so its identity must not be guessed or whitelisted. Tests remain
unexecuted. Any future corrective source/protocol and exact operation would need
new review,coordination and admission; current evidence is not runtime acceptance.

**Current next gates,27 October16:57UTC:** obtain the genuine exact004 bootstrap
decision and fresh Root admission; execute its once-only guarded observation,
review the complete actual manifest and accept only observational coverage.
Then separately admit native preparation003/pin review,the117-case nonnumerical
unit and bounded external closeout. None has run. Current Source011 is only
scheduling through21:30Riyadh,not execution authority. The owner clarified the
P3-only engineering admission question; science,capture,training and numerical
execution remain held. Preserve original14 sources and all refusal history.

**Subsequent next action:** repair the explicitly refused bootstrap control chain
in separate002 sources, review them independently, then seek a new exact genuine
peer/Root decision. Do not dispatch001. Runtime observation acceptance, native
preparation/pin review and unit/external grants remain later separate gates.

**Latest next action:** the phase-only startup4GiB choice is now owner-adopted;
do not ask again. Source009 coexistence is fresh,not native/test admission.
Independently reviewed bootstrap/preparation sources await the distinct exact
observational decision,then accepted runtime observations/native preparation/
pin review and unit/external grants. All117 candidate cases remain unexecuted.

**Later27 October milestone:** the metadata/profile and supplied-telemetry
contract source unit is implemented and independently statically reviewed:
[status and holds](../phase2/cho51_p3_contracts_implementation_20261027.md).
Next is its separately coordinated/admitted117-case nonnumerical validation and
bounded external closeout,not a runnable P3 bridge. Actual timing diagnostics,
observer/custody qualification and terminal-controller integration remain later
separate engineering phases. No proposed timing margin or scientific gate is
adopted by this source checkpoint.

Before that next validation: resolve the fresh owner RAM question or meet the
unchanged default floors,and independently review/admit the exact native
pin-preparation protocol. Pro2's actual ACK covers lightweight Source only;
neither it nor the clean source review authorizes preparation/tests. Current
14:17UTC RAM observation (~3.53GiB) is below even active4GiB. No start occurred.

**27 October design checkpoint:** P3-D is now documented and independently
statically reviewed in the [adapter design](../phase2/cho51_p3_adapter_design_20261027.md)
and [telemetry design](../phase2/cho51_p3_telemetry_design_20261027.md).
This closes design only, not P3-T implementation/diagnostics or P3-I execution.
The [review](../phase2/cho51_p3_adapter_review_20261027.md) records the exact
boundaries and proposed separately authorized metadata/telemetry next unit.

Prepared **27 October 2026 (Asia/Riyadh)** from the local project evidence through
25 October. This is a consolidated roadmap and recommendation, not a replacement
for the adopted decisions or a new execution authorization. Source documents are
listed in [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md).

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

## 4. Recommended next work, in dependency order

These are proposed work packages. Preparing this folder does not start them.

| Package | Work and dependencies | Required completion evidence |
| --- | --- | --- |
| P3-D: adapter design | Specify a separately versioned bridge between the accepted metadata preflight and provenance-aware **linear engineering** composition. Name exact modules, lifecycle, authority boundaries and recovery semantics. | Reviewed design with no conversion of a compatibility report into an execution token or an engineering terminal into a measured cell |
| P3-T: timing design | Design bounded, nested monotonic telemetry for admission/import/pins/origin/inputs/restore/support/query/verifiers/terminal/closeout. Resolve timing interpretation before adding executable overhead. | Reviewed inclusive/exclusive timing semantics and a separately admitted diagnostic plan; no inferred hotspots from file timestamps |
| P3-I: bounded engineering integration | Only after separate authorization, implement the new adapter with fresh source/runtime pins and resource/peer admission. Keep real recorder locks, strict physical proofs and separate producer/executor/recorder roles. | Focused tests, one explicitly scoped engineering transaction if admitted, honest counters, complete native/external closure and independent evidence review |
| M: remaining method chains | Complete fresh current restore/target/parent integration for EEGNet; complete missing selection/publication/restoration and target/parent stages for LoRA and full tuning. | Method-specific executed evidence, including actual intended parameter changes, query-state invariance, provenance, failures and resource bounds |
| R: operating feasibility | Measure representative current workloads under a separately approved scope, including preparation, complete selection, persistence, audits and recovery—not just forward inference. | A measured cost model, storage/RAM envelope, attempt/recovery policy and viable complete-roster plan; no unapproved scientific pilot by proxy |
| S: scientific eligibility and freeze | Reconcile authenticated checkpoint-specific training coverage with evaluation recordings, permitted claims, complete method versions, protocol, analysis and feasible operating plan. Can progress alongside engineering. | Completed cohort/overlap review or an explicit scientifically defensible treatment of unresolved exposure, followed by the separate final owner freeze decision |
| X: admitted study | Only after all relevant engineering, scientific and operational gates, execute the exact retained roster without resetting excluded/exhausted history. | All 1,020 required cells accounted for with authenticated measured records; no imputation or fabricated replacements |
| A: analysis and release | Apply the adopted paired analysis, regenerate tables/figures, review limitations and prepare a reproducible results bundle. | Traceable results, independent review, appropriately scoped claims and separate publication/release authorization |

### Timing is a real next-step risk

The latest accepted numerical engineering composition took **590.082323 seconds**
inside its 600-second native Job: only **9.917677 seconds** of arithmetic headroom
in one observed run. This is neither a production reliability distribution nor
the cost of a complete real-data case. Earlier hard-cap failures remain failures.
Do not remove mandatory audits, cache authorization decisions or enlarge caps
merely to make an integration pass. See the
[interface audit](../phase2/cho51_canonical_pipeline_interface_audit_20261025.md).

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

## 6. Operational and scientific gates

Before any future validation, diagnostic or training phase, read the current
[handoff](../../HANDOFF.md) and [coordination rules](../../AGENT_COORDINATION.md).
Establish fresh scope, ownership, independent review, exact settled source and
runtime pins, an unused attempt/output root, peer coordination and admission.
Old grants, receipts, estimated peer releases and absent pause files are not
permission to run.

The completed metadata phase's available-RAM amendment does **not** automatically
carry to P3. Default startup RAM is 10 GiB unless a fresh directly applicable
amendment is recorded; active RAM remains 4 GiB and free disk 20 GiB under the
current documented guard. Preserve phase-specific native time/memory limits,
thread/GPU policy, all five peer pause paths and complete external closeout.
No shared-process termination or cache clearing is proposed.

Gate A's narrow retrospective acceptance does not sign checkpoint independence
or the final scientific freeze. The former 30-hour autonomous session has ended;
this roadmap creates no new autonomous window.

## 7. Schedule and definition of completion

There is **no defensible calendar completion date yet**. The older 45-working-day
schedule is a planning horizon, not a newly activated timetable or measured cost
estimate. First settle P3 design and measure current representative workloads;
then estimate expected and conservative totals, reviewer capacity, storage
growth, restart cost and recovery buffer.

The immediate milestone is a reviewed P3 design, not a promise to launch 1,020
cases. The first-tranche scientific milestone requires complete authentic
results, adopted analysis and scoped conclusions. Wider E1/E3/E4 completion and
useful live brain control remain separately assessed deliverables.

## 8. Owner inputs that will matter later

No answer is required to finish this documentation. Before the relevant later
phase, the owner will need to resolve or confirm:

1. Whether a new authenticated checkpoint-provenance reply or recording manifest
   has arrived outside the reviewed local records. Existing documentation is not
   a fresh check of correspondence or a public issue.
2. The exact bounded P3 design/implementation scope and any phase-specific
   resource amendment; neither is assumed from earlier RAM replies.
3. The final named scientific experiment and its acknowledged provenance limits,
   once engineering feasibility and the cohort review are ready.
4. Any wider-program additions, institutional access, hardware, compute budget
   or external reviewer not currently established by local evidence.

See [PROGRESS_REPORT.md](PROGRESS_REPORT.md) for completed milestones and
[LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) for the studies behind these choices.
