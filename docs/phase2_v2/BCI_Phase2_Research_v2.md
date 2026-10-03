# Phase II research plan

Version 2.0 | Revised experiments, gates and schedule | 5 September 2026

## Purpose, scope and status

This version replaces the research schedule for planning purposes while preserving the supplied original and every Phase I artifact. It incorporates the requested methodological corrections. It does not sign Gate A, adopt an unresolved scientific decision, or authorize training, publication or expenditure.

The central question is whether a pretrained EEG encoder, with carefully controlled target-support adaptation, improves cross-subject motor-imagery decoding over credible baselines. Cho2017 is the primary dataset; BCI IV 2a is for development and secondary four-class evaluation; MMIDB is secondary with explicit pretraining-overlap disclosure.

### What changes in version 2

- Entry decisions precede experiments. Validation, support and query roles are explicit. The shot curve uses a common query set.

- E1 first proves that the tokenizer and masked-prediction path are available. Its observational evidence cannot establish causal memorization.

- Engineering correctness and scientific performance are separate gates. Electrode shuffling is a sensitivity experiment, not a required accuracy collapse.

- E3 requires causal preprocessing and supported encoder windows. E4 distinguishes channel ablation from a deployable reduced-electrode system.

- The primary E2 comparison runs before optional expansion. The calendar is conditional on measured runtime and actual ownership.

### Evidence carried forward

The existing records report 5,950 main benchmark results and 450 protocol-matched reference fits. Gate A remains unsigned; Gate B has complete local deliverables but no scientific pass. The current source fingerprint matches the handoff. A read-only preflight on 5 September measured 13.9 GiB free against the committed 20 GiB floor. Recheck before work; this is a transient measurement.

The frozen H2 margin remains +/-0.0520290793 balanced-accuracy units. Historical configurations, records, provenance, thresholds and receipts remain unchanged. All new experiments receive Phase II identities and output roots.

## 1. Entry gate and decision register

G0 is an admission gate. Preparation and bounded implementation can proceed while scientific choices are pending; work dependent on those choices cannot be presented as a frozen experiment.

| ID | Decision and proposed treatment |
| --- | --- |
| D01 | Gate A: obtain a documented, defensible acceptance decision or explicit authorization for exploratory Phase II. Creating this revision supplies neither. |
| D02 | Support: proposed nested fixed-earliest 1/5/10/20 trials per class, with all first 20 excluded from the common query set. Seeded early-pool selection remains an alternative requiring a defined eligible pool. |
| D03 | E2: adopt the proposed roster and primary comparison in section 3, or amend them before pilot outcome inspection. Specify BCI class inventory explicitly. |
| D04 | Verification: establish TUAB/TUEV access or document the weaker reference-forward/local-validation route. Record the limits of any formal interpretation. |
| D05 | E1: verify a compatible tokenizer and complete masked-prediction weights. If unavailable, approve a scoped feasibility report; do not substitute a different loss under the E1 identity. |
| D06 | Capacity: meet storage and RAM/VRAM guards; identify actual reviewer and any external compute or backup resources. No assumed cloud budget or five-person team. |

### Required G0 receipt

Record decision text, owner, date, source/config hashes, exploratory or formal status, unresolved dependencies, and admitted work. Decisions may permit independent work streams without pretending all gates passed. Never invent missing criteria from the absent Full Project Plan or Team Execution Plan.

### Scope and stop rules

A data leak, mismatched checkpoint, unverified split or numerical incompatibility stops affected experiments. A lower score, inconclusive TOST or weak electrode sensitivity is a reportable outcome. Missing E1 resources stop E1 only unless its absence changes the agreed overall deliverable. Resource deferral is operational, not scientific failure.

## 2. Shared experimental contract

### Subject separation and selection

For each outer target subject, source subjects alone supply model development and inner validation. Select depth, learning rate, epochs, normalization policy and confidence/evidence rules using source-only subject-disjoint validation. Freeze the selection procedure before outer evaluation. Never choose a globally best depth or method using the target-query results later used for inference. A single depth chosen solely on a declared development dataset is an alternative, with its transfer assumption disclosed. [R1]

### Support and query identity

Under proposed D02, reserve the first 20 retained trials per class as the maximum support pool; select its first 1, 5, 10 or 20 trials for each shot condition. All remaining trials form the same query set for every condition. Unused support-pool trials are unavailable to that condition. Require query examples of every class; report all exclusions and changed eligible-subject counts before fitting.

All methods share exact target partitions and seeds. Model initialization and support-draw seeds are separate fields. Fixed-earliest draws have no sampling variability; Cho loader order is not established acquisition chronology. A seeded alternative must define pool bounds, nested draws and a query set outside that pool before results.

### Fair learning and preprocessing

Declare permitted source data, target labels, architecture, preprocessing, optimizer search budget, update steps and stopping rule per method. Fairness means equal permitted information and comparable selection opportunity, not forcing every architecture to use identical updates. TCPL may condition on support without target gradient updates. Any normalization or alignment learned for a target uses support only; query runs in evaluation mode with full state unchanged.

### Records and failure visibility

Every evaluation cell stores configuration and hash, source commit/fingerprint, dirty state, environment and checkpoint identity, dataset/subject, split hashes, class/channel inventory, seeds, selection provenance, timings, metrics, resource observations and status. Store failures and retry lineage. Commit records atomically and validate identity before resuming. Reused source fits retain their original provenance.

Use shared cohorts for paired comparisons. Aggregate seeds within subject; do not count seeds, trials or overlapping windows as additional independent subjects. Report descriptive intervals with their dependence assumptions and prespecified sensitivity analyses.

## 3. E2: adaptation and the primary claim

E2 is the mandatory quantitative core. Proposed primary endpoint: paired subject-level balanced-accuracy difference, LoRA minus linear probing, on Cho2017 at five shots per class, with training seeds 11, 23, 37, 53 and 71. This is a proposed new contract under D03, not a recovered definition from the missing Full Project Plan.

| Panel | Proposed seven-system roster |
| --- | --- |
| Same LaBraM backbone | 1 Linear probe; 2 full fine-tuning; 3 partial fine-tuning with depth chosen by source-only validation; 4 LoRA; 5 bottleneck adapters; 6 support-conditioned prompts. |
| Separate architecture | 7 Faithful TCPL with its published support encoder and TCN/Transformer. Report as a system comparator; do not attribute differences to prompt adaptation alone. |
| Reference anchors | EEGNet and EA + tangent-space logistic regression under matched Phase II support/query identities. These anchors are additional to the seven systems; Phase I scores are contextual only. |

### Three distinct questions

- Utility: does the prespecified LoRA method improve over linear probing? Report paired difference, 95% interval and the predeclared Wilcoxon test.

- Regularization: how does LoRA compare with full fine-tuning at small support sizes? Use matched access and credible source-only tuning. Describe performance evidence; a single win does not prove a mechanism.

- Equivalence: is the prespecified comparison inside the frozen +/-5.20290793 percentage-point bounds? Use paired TOST at one-sided alpha .05 and its 90% interval. Failure to reject both bounds is inconclusive, not inequality.

Choose one primary comparison before inspecting outcomes. Treat other methods, shots and datasets as secondary; predeclare comparison families and Holm adjustment for multiple superiority claims. A best method selected from final results is descriptive unless evaluated through a separately frozen selection procedure.

The frozen margin is resource/planning-derived, not established clinical or practical interchangeability. Keep it unchanged. Report power assumptions using plausible paired-difference variability and effect sizes; do not present observed post-hoc power as new evidence or guarantee 80% power from 52 subjects. [R2]

## 4. E1: observational checkpoint probe

### Feasibility before corpus inference

The safe downstream backbone omits masked-modeling tensors. The original local checkpoint contains omitted mask/output components, but the full inference architecture and compatible neural tokenizer must be recovered, pinned and checked. Official masked pretraining predicts tokenizer code indices, not arbitrary signal reconstruction. Verify masks, units, channel identities, output vocabulary and loss normalization against the reference path on identical inputs. No tokenizer retraining is silently added. [R3, L3]

### Matched contrast

Compare MMIDB and Cho2017 under declared 64-channel mappings, 200 Hz, identical duration, scaling, filtering and sample budgets. Record matching variables and sampling seeds. Match measurable cohort/session properties where available; do not imply the same individuals exist across datasets. Freeze selection before loss comparisons.

Run pretrained and multiple random-weight encoder controls with the same verified tokenizer, masks and target codes. Freeze tokenizer state during inference. Report both dataset contrasts and their pretrained-versus-random interaction descriptively; this does not remove acquisition confounding or establish training membership.

### Entropy and inference

Distinguish target-code occupancy entropy from the encoder prediction entropy. Target-code entropy characterizes tokenizer/data distributions and is not independent evidence of encoder memorization. Equalize token counts or prespecify a sample-size correction. Do not assume memorization must reduce entropy.

Calculate recording-level losses, then aggregate within subject or use a subject-cluster bootstrap. Do not apply an independence-based Mann-Whitney test to multiple recordings from the same person. If Mann-Whitney is retained, use one prespecified subject summary per subject. Report effect size and clustered uncertainty; dataset-level exposure still has only one exposed corpus.

### Completion and interpretation

A complete E1 has a verified inference path, both datasets, random-weight and entropy diagnostics, sampling identities, uncertainty and an explicit amplifier/reference/noise/task-confounding statement. Downstream dataset margins remain descriptive E1b. Missing tokenizer or head parity produces a documented feasibility failure. An approved scope amendment may accept that outcome, but it cannot be reported as a completed E1 probe.

## 5. Encoder verification and adaptation readiness

### Deterministic correctness first

Check retained checkpoint tensors and actual parameter counts without modifying the model to match the plan. Verify electrode-name lookup including CLS offset, duplicate/unknown-channel errors, temporal embeddings, units and expected feature shapes. Compare reference and local implementations on identical real and synthetic inputs with a stated numeric tolerance justified by precision/backend differences.

Paired signal-and-name reordering should preserve equivalent representations where architecture semantics permit; changing names alone must change the selected embeddings. Tests should directly inspect those semantics rather than assert an arbitrary accuracy drop.

### Performance evidence second

Prefer an accessible protocol-matched TUAB/TUEV reference. Define acceptance rationale before the new evaluation. If access is absent, numerical parity and local smoke evidence can support explicitly weaker integration confidence; a matching local depth ordering is supplementary, not a pass criterion. Report what was and was not reproduced.

### Real adaptation checks

The generic Linear replacement does not currently support LaBraM QKV direct-weight access. Implement and verify an effective-weight or forward-path integration that actually changes attention outputs; exposing base weights alone is insufficient. Enumerate exact target names and trainable counts for LoRA, adapters and prompts.

For every method: prove expected initial identity where relevant, support updates change intended parameters, source state remains unchanged, and query inference changes neither parameters nor buffers. Declare BatchNorm/dropout behavior, head training, regularization and stopping. Smoke all shot levels, including one-shot without target-query early stopping.

### TCPL identity

Reproduce the specified support encoder, mean pooling, ReLU generator, ten 64-dimensional prompts and TCN/Transformer as a separate system. The local label-conditioned GELU prototype is not TCPL. Replace the original blanket contradictory-table allegation with the narrower protocol discrepancies documented in the source review. Pin the article version and reconcile LOSO versus ten-fold reporting before a numeric reproduction claim. [R4, L4]

## 6. E3: causal decoding and interface performance

### Declare the deployment signal path

Implement causal filtering and stateful resampling from a continuous stream; account for filter delay, warm-up and state resets. The existing zero-phase Profile A artifacts remain offline evidence. Training/calibration should match the deployed signal path, and no future samples may affect an emitted decision. Prove causality by perturbing future input and checking past outputs.

### Supported windows

Keep EEGNet windows at 0.5, 1, 2 and 4 seconds with the declared 0.25-second stride. The current LaBraM path requires whole 200-sample patches at 200 Hz: its core sweep is 1, 2 and 4 seconds. Treat 0.5-second LaBraM inference as unsupported unless a separate, validated padding/masking or architecture experiment is adopted. Do not stretch 0.5 seconds to one second or reuse future samples.

### Tuning and measurements

Tune confidence thresholds, evidence accumulation, cooldown and command-reset policy only using source validation or the explicitly permitted target support budget. Freeze before query replay. Keep batched offline accuracy separate from one-stream, batch-one deployment latency.

Measure acquisition-to-command time including window fill, preprocessing delay, inference, accumulation and cooldown. Report p50/p95 latency, deadline misses, queued/dropped samples, correct commands per minute, incorrect activations per minute, abstention, coverage and calibration. Evaluate idle/neutral periods before claiming false-activation performance; cue-only recordings cannot establish asynchronous idle safety.

Use ITR only with its assumptions and the actual command timing disclosed. Overlapping windows or repeated predictions of one intention are not automatically new communicated symbols. Accuracy/coverage and accepted commands must share a traceable denominator. [R5]

### Completion

Run EEGNet first, then the selected verified encoder on the CPU deployment path. Save a replay receipt, emitted commands, sample identity and latency trace. An all-abstention run passes integration only, not useful decoding. Live-brain control and a second physical machine remain separate demonstrations requiring the corresponding resources.

## 7. E4: montage sensitivity and reduced hardware

### Two explicitly different experiments

E4a tests channel ablation in a fixed trained model. E4b tests a system trained/adapted and deployed with fewer electrodes. Report these separately; zeroing channels after full-montage processing cannot establish reduced-hardware performance.

For E4b, remove excluded electrodes before any cross-channel reference or normalization. Recompute the declared reference using retained electrodes only, or use a reference physically available in the proposed hardware. Validate that excluded signals cannot influence retained processed outputs.

### Montage inventory and pairing

On Cho2017 and MMIDB, define named full/32/16/eight-sensorimotor/eight-random/three-minimal montages. Verify every name exists and aligns with the encoder. Random eight-channel montages vary by declared montage seed and are shared across compared methods; keep montage randomness separate from training randomness. Define repeated-draw aggregation before results.

Use identical support/query identities and the same source-only selection policy across montage conditions. Report retained channels, reference, rejected-trial counts and any missing-channel exclusions. A BCI four-class check uses feasible dataset-specific montages as a secondary experiment.

### Spatial identity experiment

Compare correct identities with multiple prespecified identity permutations at inference, with all other settings fixed. Keep this distinct from reordering both signal and names, which checks implementation semantics. A small performance effect is evidence of weak spatial-identity reliance or robustness; investigate and report it rather than forcing a substantial-drop pass condition.

### Completion and claim limits

The core E4 deliverable is a paired retention curve on the primary dataset, uncertainty over subjects, random-montage controls and a verified preprocessing dependency test. MMIDB replication and the full E4b deployment study expand after the primary work passes its budget gate. Sensorimotor montages need not beat random montages for the experiment to be valid.

Keep interpretations scoped to the tested checkpoint, task, montage and adaptation protocol. A second backbone increases evidence breadth but still does not establish a universal claim about EEG foundation models.

## 8. Milestones, capacity and the 45-day horizon

Weeks 6-14 remain a 45-working-day planning horizon. Days are intentions, not promised fit durations. Five lanes denote responsibilities; they do not assert five available workers. GPU-heavy work is queued to one admitted job at a time on the laptop. Runtime estimates replace assumed concurrency.

| Week | Priority and completion evidence |
| --- | --- |
| 6 | G0 decisions and headroom; reference/parity checks; support/query contract; adaptation smoke. No outcome-dependent gate criteria. |
| 7 | Source-only depth selection; real LoRA/adapters/prompts; TCPL smoke; E1 feasibility and matched manifests; causal and montage tests. |
| 8 | Measured pilot and cost model; freeze E2 contract; launch primary Cho 5-shot comparisons; run admitted E1 probe. |
| 9 | Complete/audit primary E2; then expand shot levels and methods within budget. Days 4-5 protected float. |
| 10 | Secondary datasets and primary E3/E4; prespecified analysis and deployment rehearsal. Days 4-5 protected float. |
| 11 | Complete evidence, independent review and Gate C packet. Days 4-5 protected float; incomplete work moves to buffer. |
| 12 | Unallocated recovery week. Optional work only after required scope is complete and affordable. |
| 13 | Write-up, figure regeneration, cross-reading and corrections. Day 5 reserved for revision. |
| 14 | Fresh-checkout reproduction, evidence packaging, rehearsals and release readiness. Publication remains a separate authorized action. |

Full E2 expansion is 170 x 7 x 4 x 5 = 23,800 evaluation cells before anchors, tuning, depth sweeps, controls and ablations. Cells are not identical to independent fits: reuse only immutable compatible source fits, and count those fits separately. Measure representative slow methods and large datasets before extrapolating.

Record expected and conservative runtime, peak RAM/VRAM, disk growth and restart overhead. Admit expansion only if it fits remaining compute and buffer. If it does not fit, document reduced scope before inspecting affected outcomes. Never silently drop failed cells or consume float days with new experiments.

Optional order after required work: prompt-token/injection ablation; BCI four-class confirmation; a second backbone such as CBraMod after checkpoint/license and cost verification; then cross-dataset transfer. Optional work never displaces incomplete primary evidence or recovery capacity.

## 9. Gate C, reporting and reference trail

### Required evidence at Gate C

The primary E2 contract and analysis must be complete, with valid records, paired uncertainty, failures accounted for and claims matched to the frozen questions. E1 must be completed or explicitly scoped out through a documented feasibility decision; those statuses are never interchangeable. E3/E4 core results and any deferred expansion are listed separately.

Provide a written independent review where an actual reviewer is available. Automated tests and a second self-review are valuable but are not a five-person rehearsal or independent scientific sign-off. Preserve unsigned status until the named scientific owner signs. Negative and inconclusive findings are eligible outcomes.

### Reproducibility and release

Every reported number traces to a record; every figure regenerates from the declared input bundle. Because runs are ignored by Git, supply a separate redistributable, de-identified results bundle with hashes and retrieval instructions for the fresh-clone check. Check permissions before release; raw EEG and weights remain outside Git. Preserve legacy unversioned Phase I identities rather than assigning them new commits.

### Sources and provenance

Original: BCI_Phase2_Research_DayByDay.docx; SHA-256 b81564fe962d16fbefd7168f9c4f622812fed952fa0acc0d5703970d4b21bb5b. Version 2 prepared 5 September 2026 from that source and the repository handoff. This document and its execution companion are planning artifacts, not experimental records.

L1: docs/phase2_agent_handoff.md and PHASE2_START_HERE.md. L2: docs/falsification_criteria.md and docs/statistical_procedure.md. L3: docs/checkpoint_correspondence_review.md and encoder/labram.py. L4: docs/tcpl_reproduction_plan.md. L5: configs/e3_windows.toml, data/profile_a.py and docs/realtime_system.md.

R1: Cawley & Talbot (2010), model-selection bias. https://www.jmlr.org/beta/papers/v11/cawley10a.html

R2: Lakens (2017), equivalence testing and bounds. https://doi.org/10.1177/1948550617697177

R3: Official LaBraM pretraining code, reviewed 5 September 2026. https://github.com/935963004/LaBraM/blob/main/engine_for_pretraining.py

R4: Wang et al. (2025), TCPL; reviewed 5 September 2026. https://doi.org/10.3389/fnins.2025.1689286

R5: Thompson et al. (2014), BCI performance measurement. https://pubmed.ncbi.nlm.nih.gov/24838070/
