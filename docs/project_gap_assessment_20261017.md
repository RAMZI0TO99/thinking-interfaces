# Project gap assessment — 17 October 2026

## Purpose, baseline and limits of this assessment

This document records the gaps found when reviewing the current project: what is genuinely unfinished, why it matters, what evidence exists, and what would close each gap. It also separates adopted design limitations from implementation defects and from optional work in the wider research program.

The assessment baseline is the published `main` commit `d71f3c3dc05208d01bef92ef02ccf40beb417c69`, following the [17 October publication checkpoint](phase2/cho51_push_checkpoint_20261017.md). It uses the current heads of [HANDOFF.md](../HANDOFF.md), [AGENTS.md](../AGENTS.md), the dated qualification reports, adopted scientific decisions and relevant implementation interfaces. This is a documentation and source review. No new model execution, test suite, native Job, external provenance inquiry or scientific experiment was performed to produce it.

The facts below are current to that local evidence baseline. Dated external-dependency notes are not fresh verification of a website, maintainer response, institutional approval or remote configuration. Historical reports remain evidence of their exact source and execution; they do not automatically qualify a later source revision.

Proposed priorities, work packages and closure criteria in this document are recommendations. They do not change adopted scientific decisions, sign the final experiment freeze, grant a compute lease, reset an attempt, authorize scientific execution or introduce a new autonomous working window.

## Overall assessment

The project has a substantial working foundation, but it is not merely waiting for the final result files. The main unfinished work is the integration of separately qualified components into a current, provenance-correct, scientifically admitted real-data execution path. Important scientific evidence and the final experiment freeze are also outstanding.

There is no evidence here that the whole approach is fundamentally invalid. There is also no evidence yet that the planned adaptation method improves real EEG decoding. Engineering correctness, scientific eligibility and predictive usefulness are three different questions; the project has made much more progress on the first than on the third.

The most consequential gaps are:

1. Checkpoint-specific pretraining exposure remains unresolved, limiting claims about unseen subjects and recordings.
2. The final named scientific experiment freeze remains unsigned, despite several already adopted scope and analysis decisions.
3. Historical selected-source artifacts and current execution provenance need a compatible restoration-factory path.
4. The accepted numerical worker records an engineering success; it does not yet satisfy the parent measured-cell contract.
5. The adopted 51-target route, worker, publication, collection and analysis components need complete production composition.
6. Method coverage is uneven: linear is furthest along, while EEGNet, LoRA and full tuning have different remaining integration work.
7. Full real-data execution cost and a practical 1,020-cell operating plan have not been established.
8. No accepted final Phase II scientific evaluation cells have been produced: **0 of 1,020**.

Many tests and extensive custody evidence are useful foundations. Their counts are not a percentage of scientific completion. A complete set of fabricated metadata records is not a completed experiment, and a negative scientific outcome would still be a valid result if the study were executed and analyzed correctly.

## What is already established

| Area | Established evidence | Boundary of that evidence |
| --- | --- | --- |
| Data preparation | All 170 Profile A subjects and 20,621 stored epochs were reconstructed exactly through the current processing path: BCI IV 2a 9/5,184, Cho2017 52/10,520, MMIDB 109/4,917. Cho Profile B has another 52 caches/10,520 epochs. | Profile B is another processing view of the same Cho participants, not 52 additional independent subjects. Current reconstruction does not authenticate checkpoint training membership or missing acquisition chronology. |
| Earlier benchmark | The Phase I sweep contains 5,950 validated records across 170 subjects, seven variants and five seeds. The retained artifact-filtered inventory has 20,599 trials after 22 exclusions. | This is an earlier benchmark and protocol, not completion of the current Phase II adaptation study. |
| Baseline gate | Gate A was directly accepted on 12 October under its exact retrospective process-based amendment. A later saved-record audit passed 450/450. | Acceptance does not establish exact reproduction of the published numerical score or recreation of the original historical training runtime. |
| Adopted first tranche | 51 targets, subjects02–52; four methods; five seeds; five shots per class; all 1,020 retained cells required. | The source cohort remains 52. Subject01 is excluded from evaluation but remains source/inner-validation eligible. This adoption does not sign the final freeze. |
| Methods | Numerical probes, source-fold work and lifecycle work exist for all four selected methods. Linear and EEGNet have substantially deeper source-selection/publication evidence. | These are bounded engineering qualifications, largely on synthetic fixtures; they are not complete real-data method results. |
| Latest numerical worker | One real identity-locked engineering transaction performed a fresh selected restore, one head-only support update and a two-trial query. Backend ran once; independent verifier ran twice. | One engineering success, zero measured scientific cells, no fresh source fitting. The 38 focused tests are separate from this one numerical case. |
| Latest prediction | Synthetic predictions `[1,0]` against `[0,1]`: 0/2 correct, balanced accuracy 0. | Two synthetic queries cannot estimate real-data accuracy or establish that the method is defective. No accuracy threshold was used for engineering acceptance. |
| Custody and native closure | Independent final audit passed with zero findings; the latest accepted numerical Job closed empty and was freshly absent. Frozen exact document snapshots and metadata packets are published. | File integrity and process cleanup establish those properties. They do not prove general model quality, absence of every confound or availability of local numerical assets on another machine. |

Sources: [data reconstruction summary](phase2/cho_all52_cache_reconstruction_20261011.md), [Phase I matrix](phase1_completion_matrix.md), [Gate A decision](phase2/gate_a_acceptance_20261012.md), [readiness review](phase2/phase2_readiness_review_20261012.md), [51-target adoption](phase2/cho_51_target_amendment_adoption_20261013.md), [fresh numerical qualification](phase2/cho51_linear_numerical_worker_qualification_20261017.md), and [publication checkpoint](phase2/cho51_push_checkpoint_20261017.md).

## Reading the gap register

Status labels are deliberately different:

- **Open integration:** relevant components exist, but the required combined behavior has not been qualified.
- **Missing evidence:** a fact needed for a claim is unknown or not authenticated; this is not proof of the opposite fact.
- **Pending decision:** a scientific owner decision explicitly remains outstanding.
- **Design/reporting limitation:** an adopted choice or historical fact limits interpretation; it is not automatically a code defect.
- **Conditional wider scope:** relevant only if the project pursues a broader research or deployment objective.

Priority is proposed sequencing, not a numerical score for project quality:

- **P0:** must be resolved or explicitly bounded before the corresponding scientific launch or claim.
- **P1:** main engineering work needed to reach an admitted, reproducible study workflow.
- **P2:** interpretation, maintainability or additional scope; it may matter greatly to a particular claim without blocking every engineering step.

| ID | Gap | Status | Priority |
| --- | --- | --- | --- |
| G01 | Checkpoint-specific pretraining exposure and permissible claims | Missing evidence | P0 |
| G02 | Final named scientific experiment freeze | Pending decision | P0 |
| G03 | No final real-data Phase II effectiveness evidence | Missing evidence | P0 for claims |
| G04 | Historical-source/current-execution restoration factories | Open integration | P1, next engineering step |
| G05 | Engineering terminal versus measured scientific cell | Open integration | P1 |
| G06 | Complete 51-target production composition | Open integration | P1 |
| G07 | Uneven complete method-chain coverage | Open integration | P1 |
| G08 | Authentic production collection through final analysis | Open integration | P1 |
| G09 | Whole-case resources, throughput and full-study cost | Missing evidence | P1 |
| G10 | Scientific attempts, admission and recovery at study scale | Open integration / pending operating scope | P0/P1 |
| G11 | Restoration and backup of current numerical assets | Missing evidence / open integration | P1 |
| G12 | Runtime and device qualification beyond the narrow accepted scope | Missing evidence | P1/P2 by intended operation |
| G13 | Control coverage across future real method paths | Missing evidence outside tested scope | P1 |
| G14 | Conflicting historical status and document discovery | Documentation gap | P2 |
| G15 | Retrospective decisions and changed evaluation population | Design/reporting limitation | P0 for claim wording |
| G16 | Fixed support partitions and uncertain acquisition chronology | Design/reporting limitation | P2 |
| G17 | Statistical interpretation, margin and power limits | Design/reporting limitation | P0 for final analysis claims |
| G18 | Baseline acceptance and numerical parity claim boundaries | Design/reporting limitation | P2 |
| G19 | First tranche versus the wider research program | Conditional wider scope | P2 |
| G20 | Realtime demonstrator versus useful live operation | Conditional wider scope | P2 |
| G21 | Missing probability-level evidence for empirical calibration plots | Conditional wider scope | P2 |
| G22 | Current external governance, hardware and access state | Missing evidence / conditional wider scope | P2 |
| G23 | Deferred reference implementations and broader parity claims | Conditional wider scope | P2 |

## Scientific eligibility and evidence

### G01 — Checkpoint-specific pretraining exposure remains unresolved

**Current evidence.** The released checkpoint bytes and local tensor correspondence have been checked. A checkpoint-bound account of the actual training run is still missing: dataset versions, participant namespaces, recording identities, exclusions, label use and the mapping to the proposed evaluation inventory. The paper lists MMIDB. The absence of Cho or BCI IV 2a from a paper's dataset list is insufficient to prove that their subjects or recordings were excluded from this particular checkpoint.

The provenance intake, declared-overlap checker and evaluation recording inventory already exist. The overlap checker passed 42 synthetic cases; that establishes checker behavior, not the contents or completeness of a genuine pretraining manifest. Generic statements about unlabeled pretraining do not resolve whether evaluation recordings were exposed or whether any relevant labels were used.

**Why it matters.** A model may execute correctly while the claims about unseen participants, unseen recordings or independent transfer remain unsupported. The present finding is **unknown overlap**, not demonstrated leakage. Hashing the checkpoint more times cannot answer this cohort question.

**Proposed closure.** Obtain a checkpoint-bound manifest, training logs or a precise attributable attestation; assess its completeness and identity conventions; map it against the fixed evaluation recording/subject inventory; and record which exposure and exclusion claims are supported. Keep factual evidence separate from the scientific owner's decision about permissible use. If the required history cannot be recovered, retain that uncertainty and make an explicit limited-claim decision rather than manufacturing a zero-overlap conclusion.

**Dependency.** This can progress in parallel with engineering integration. It must be addressed before the corresponding scientific eligibility and unseen-cohort claims are finalized. Preparing this assessment does not authorize contacting maintainers or sending the prepared provenance package.

Evidence: [checkpoint provenance review](checkpoint_pretraining_provenance_20261010.md), [cohort review contract](phase2/checkpoint_cohort_review_contract_20261010.md), [overlap checker qualification](phase2/cohort_declared_overlap_qualification_20261011.md), [evaluation recording package](phase2/evaluation_recording_provenance_package_20261011.md).

### G02 — The final named experiment freeze is still unsigned

**Current evidence.** Five of seven decisions are adopted. Gate A has its separate direct acceptance. The owner adopted the exact 51-target amendment. The checkpoint-cohort review and final named experiment freeze remain pending. Permission for bounded engineering, successful tests and published source do not sign that freeze.

**Why it matters.** The experiment needs an identifiable version that connects the adopted population, methods, selection budget, support/query rules, analysis, provenance limitations and qualified execution behavior. Otherwise later results could be interpreted against moving or inconsistently documented rules.

**Proposed closure.** Once the scientific evidence and concrete implementation package are ready, consolidate those exact versions and limitations into the named freeze and record the separate owner decision. Preserve the already adopted choices; do not unnecessarily reopen scope, primary statistics or the empty secondary family. The approval should concern a concrete reviewable experiment, not a promise to finish integration later.

Evidence: [adopted decisions](phase2/cho_design_decisions_20261012.md), [51-target successor decision](phase2/cho_51_target_amendment_adoption_20261013.md), [Gate A acceptance](phase2/gate_a_acceptance_20261012.md), [freeze draft](phase2/scientific_freeze_draft.md).

### G03 — The planned scientific effect has not been measured

**Current evidence.** The main Phase II study has **0/1,020 accepted final scientific cells**. The latest worker ran one synthetic subject02/linear/seed11/five-shot/repetition1 episode with ten support trials, two query trials and 30 unused trials. It made both query predictions incorrectly. Its terminal explicitly records an engineering success and zero measured cells.

**Why it matters.** There is no current estimate of real-data LoRA improvement under the adopted study. Neither the earlier 5,950 Phase I records nor the new engineering case can substitute for it. The two incorrect synthetic predictions are too small and too artificial to diagnose the algorithm, but they also cannot be described as positive decoding evidence.

**Proposed closure.** After eligibility, integration and scientific admission are in place, execute the complete eligible real-data roster, retain its valid source-selection and target evidence, and apply the prespecified analysis. Publish the actual outcome, including negative or inconclusive findings. Do not define completion as obtaining a favorable score or adjust held-out choices until the desired effect appears.

**Useful distinction.** Closing the execution gap means producing valid evidence. Closing a superiority claim requires the adopted statistical conditions to hold. The project can finish the study correctly and still find no advantage.

Evidence: [latest numerical qualification](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [publication checkpoint](phase2/cho51_push_checkpoint_20261017.md), [Phase I completion matrix](phase1_completion_matrix.md).

## Implementation and integration

### G04 — Source-restoration factories need historical/current provenance compatibility

**Current evidence.** Selected-source artifacts originate from historical source Git `4491e2a`; recorder history uses `277d797`; the completed numerical execution captured actual Git `3ef0c39`, dirty=true. The current published baseline is `d71f3c3`. These are legitimate different identities with different roles.

The canonical restoration, selected-source store and selection-evidence binding interfaces compare captured source context with the historical source contract. The unchanged high-level single-root composition therefore does not yet provide a qualified way to consume authenticated historical source evidence while executing the fresh worker under the current context. Explicit separately staged publication/restoration has already worked; the gap is the general factory composition, not proof that selected weights cannot be restored.

**Why it matters.** Treating the historical producer and current consumer as the same source would either reject legitimate ancestry or tempt an unsafe workaround that weakens provenance. An accepted historical receipt must remain historical; a current executor needs its own source/runtime identity.

**Proposed closure.** Implement a separately versioned provenance-aware factory or compatibility layer that authenticates the historical selection recipe, evidence, weight bytes and tensor state while independently binding the current executor, runtime, source files and request. Demonstrate genuine strict restoration and adapter delivery under the fresh current context. Reject changed weights, changed recipes, inconsistent ancestor identities, foreign current contexts and stale request bindings.

Use explicit bounded reads for every store caller. Do not spoof an old Git identity, edit frozen evidence, disable the provenance checks or replay a used launcher to make the factory accept the artifact.

**Next concrete deliverable.** A small versioned compatibility implementation, focused contract checks and one freshly admitted bounded engineering integration case with historical/current identities visible in its proof. This is the latest handoff's next milestone; it is not a request to run the entire scientific study.

Evidence: [current handoff](../HANDOFF.md), [linear publication qualification](phase2/cho51_linear_publication_qualification_20261015.md), [source restore implementation](../evaluation/phase2_cho_source_restore.py), [selected-source store](../evaluation/phase2_selected_source_store.py), [evidence binding](../evaluation/phase2_selection_evidence_binding.py).

### G05 — The engineering worker does not yet satisfy the measured-cell contract

**Current evidence.** The new numerical worker deliberately expects zero measured cells and records an engineering terminal. The canonical parent verifier expects a measured evaluation cell, canonical successful completion and independently authenticated input/publication evidence. These are different contracts, not inconsistent labels for one finished scientific case.

The fresh numerical worker does important real work: canonical model/settings/adapter classes, strict selected restoration, a head update, query inference and a real CaseRecorder identity lock. Its independent verifiers inspect physical outputs without repeating numerical execution. That success should be retained exactly, while acknowledging that the canonical measured-cell parent path remains unqualified. Satisfying that measured-record schema would still not grant the final study's scientific admission; the freeze and eligibility gates remain separate.

**Why it matters.** Renaming an engineering receipt, incrementing a measured counter or copying a valid old target witness would not establish a scientifically admitted result. A genuine current cell must connect the actual target computation to the expected input, publication, request, claim and admission.

**Proposed closure.** Compose a versioned numerical path with the required parent contract and demonstrate the intended result type under its proper admission. Preserve the distinction between engineering-only trials and scientific evaluations. Include rejection of an engineering-only receipt presented as a measured cell, mismatched identities, stale evidence and unauthorized admission. Do not bypass the canonical checks before claim, after publication or after target execution.

Evidence: [numerical worker candidate](phase2/cho51_linear_numerical_worker_v1/README.md), [worker implementation](phase2/cho51_linear_numerical_worker_v1/numerical_worker.py), [canonical execution verifier](../evaluation/phase2_cho_execution.py), [parent executor](../evaluation/phase2_pilot.py).

### G06 — The adopted 51-target components need complete production composition

**Current evidence.** The historical canonical preparation, execution, paired-input and analysis-preparation path encodes the original 52-target design: 1,040 cells, 208 subject-method means and 52 subject pairs. Separately versioned adopted-route and analysis candidates support the 51-target successor. Preserving the old implementation is intentional; a historical 52-target path should not silently become the current study path.

**Why it matters.** A correct route candidate alone does not prove that every downstream factory, collector and analysis entry point uses the same adopted roster. Mixed scope could accidentally require excluded subject01, drop retained cases, count the wrong independent units or apply the wrong degrees of freedom.

**Proposed closure.** Provide one versioned end-to-end composition that uses exactly:

- Evaluation targets subjects02–52, four methods, five seeds: **1,020 retained case IDs**.
- All 52 source catalogs, 51 outer sources and 50 inner-training subjects per fold.
- Subject01 retained as a source/validation participant, with all 20 subject01 evaluation rows excluded consistently.
- Five-seed averaging to **204 subject-method means**, then **51 LoRA-minus-linear subject pairs**, with t degrees of freedom 50.
- The adopted fixed support rule, exact method templates and **5,253-step selection ceiling**.

Reject mixed 51/52-target inputs, duplicate or missing identities and attempts to treat source eligibility as evaluation eligibility. Preserve the historical route and its receipts unchanged.

Evidence: [51-target adoption](phase2/cho_51_target_amendment_adoption_20261013.md), [adopted route candidate](phase2/cho51_route_candidate_v1/README.md), [51-unit analysis candidate](phase2/cho_51_target_analysis_candidate/README.md), [historical preparation](../evaluation/phase2_cho_case_inputs.py), [historical paired builder](../evaluation/phase2_cho_paired_inputs.py), [historical analysis preparation](../evaluation/phase2_cho_analysis_preparation.py).

### G07 — Complete numerical method-chain coverage is uneven

All four methods have implementation and executed engineering evidence. The open work is not “implement every method from nothing.” It is completing and qualifying the missing stages for each method under the current composed workflow.

| Method | Executed engineering evidence | Main remaining qualification |
| --- | --- | --- |
| LaBraM linear | Full-shape eight-update probe; public-API 51-update source fold; complete staged selection/final fit totaling 5,253 updates; selected publication and detached strict restoration; fresh real-lock worker with one support update and two query trials. | Provenance-aware factories, parent measured-cell integration, real-data whole-case behavior and complete study roster. |
| EEGNet | Full-shape eight-update probe; public-API source fold; complete synthetic 5,253-update selection and real source publication; a later separate bounded public restore verified all 21 tensors. | A fresh composed restore/target/recorder worker and current parent integration. Earlier complete-parent failures remain failures despite later standalone restoration success. |
| LaBraM LoRA | Full-shape eight-update probe; trained LoRA A/B and effective QKV changes with round-trip checks; public-API 51-update source fold; four-method lifecycle fixture. | Complete-selector/source-publication/restoration chain, fresh target worker, parent integration, real-data resource envelope and complete roster. |
| LaBraM full tuning | Full-shape numerical and trainable-mask/round-trip evidence; public-API source fold; four-method lifecycle fixture. A separately reviewed successor probe passed under a larger resource envelope after an earlier refusal; the earlier exit alone did not establish its cause. | Complete-selector/source-publication/restoration chain, fresh target worker, parent integration, real-data resources and complete roster. |

These source-fold and complete-selector qualifications use declared engineering fixtures, not real study outcomes. “Public” here describes the public implementation API, not a completed public-data scientific run.

**Why it matters.** A linear path cannot establish LoRA correctness, and LoRA is the primary proposed contrast. Likewise, a standalone EEGNet restore cannot retroactively complete the failed parent that preceded it. Cost and memory can differ substantially across methods.

**Proposed closure.** Track one explicit stage matrix per method and qualify the smallest missing genuine chain. Reuse already qualified components when their source, inputs, runtime and contract still apply; add fresh evidence where composition changes their obligations. Preserve failed historical attempts and separate successful successor results.

The current restoration route supports full-state `full_v1`. Sparse publication metadata, where supported, is not evidence of qualified sparse tensor restoration. Sparse restoration is extra work only if the final selected path requires it.

Evidence: [numerical probes](phase2/cho51_numerical_probes_20261015.md), [source folds](phase2/cho51_source_fold_qualification_20261015.md), [linear chain](phase2/cho51_linear_chain_qualification_20261015.md), [linear publication](phase2/cho51_linear_publication_qualification_20261015.md), [complete EEGNet result](phase2/cho51_complete_eegnet_qualification_20261015.md), [successful staged restore](phase2/cho51_staged_restore_qualification_20261015.md), [four-method lifecycle](phase2/cho51_worker_lifecycle_qualification_20261015.md), [publication collector scope](phase2/cho51_publication_collection_v1/README.md).

### G08 — Production collection and final reporting have not consumed a real complete roster

**Current evidence.** Considerable collection and analysis code already exists:

- Recorder and selection collection passed 20 and 43 synthetic cases.
- Actual-input composition passed 28 checks and authenticated 156 processed files totaling 3,266,058,145 bytes. Its recorder rows, selection claims and prediction metrics were explicitly fabricated.
- Receipt/selector collection passed 202 checks, including a complete 1,020-case metadata roster with mocked native proof I/O and public selector checks on fabricated complete histories.
- The separate 51-unit statistical candidate passed 22 checks across six fabricated fixtures, including ties/zeros and disagreement between rank direction and arithmetic mean.

**Why it matters.** These checks provide meaningful boundary and arithmetic evidence. They do not establish 1,020 actual model cases, a full authenticated tensor roster, genuine measured predictions or a published scientific conclusion. Even real input loading does not convert fabricated outcomes into measured outcomes.

**Proposed closure.** Connect genuine execution, recorder history, source selection/publication, native tensor witness admission, full selector verification, score rows and paired reporting. Preserve the same independently bound case identities throughout. Require the full eligible roster and reject missing, duplicate, extra, stale, foreign-context, unverified or replayed cells. Keep fabricated fixtures outside the scientific recorder and report population.

The closure artifact should be a reproducible report backed by its actual accepted cells and exact analysis version. More fabricated full-roster checks alone do not close this gap.

Evidence: [collection qualification](phase2/cho51_collection_qualification_20261015.md), [actual-input composition](phase2/cho51_input_composition_qualification_20261015.md), [receipt/selector qualification](phase2/cho51_receipt_selector_qualification_20261015.md), [synthetic statistical qualification](phase2/cho51_synthetic_analysis_qualification_20261013.md).

## Operations, reproducibility and maintainability

### G09 — Full current real-data cost and throughput remain unqualified

**Current evidence.** The latest accepted native Job took 346.913912 seconds and peaked at 1,498,128,384 process bytes / 1,533,112,320 Job bytes. It included qualification work and a tiny target episode; it did no fresh source fitting. The staged synthetic linear chain used seven fresh Jobs totaling 2,184.335903 seconds plus authenticated historical folds. Neither figure is the cost of one complete current real-data scientific cell.

Cached forward-only diagnostics exclude optimizer work, selection, preparation, persistence, auditing and recovery. Historical resource proposals used older settings and a 1,040-cell design. They are not a current estimate or delivery date for the adopted 1,020 cells.

**Why it matters.** A pipeline can work on a bounded case yet be impractical as a complete study on the shared host. Source selection, cold starts, full-model optimization and repeated verification may dominate the cost. Small fixture memory peaks cannot safely stand in for all real methods and recordings.

**Proposed closure.** Measure representative complete real-data paths for each intended method once the corresponding gates permit them. Include initialization, source selection/fitting, target adaptation/query, writes, audit, cold/warm behavior, native memory, storage growth and interruption/recovery overhead. Produce a dated execution budget with uncertainty, failure allowance and a feasible shared-machine schedule. Do not present a hard completion date before that evidence exists.

The adopted ceiling is a limit on permitted recorded selection work, not proof that every case will consume identical time or that the whole study fits an earlier autonomous window.

Evidence: [numerical worker resources](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [staged linear chain](phase2/cho51_linear_chain_qualification_20261015.md), [complete EEGNet resource history](phase2/cho51_complete_eegnet_qualification_20261015.md), [coordination rules](../AGENT_COORDINATION.md).

### G10 — Study-scale admission, attempt accounting and recovery still need a concrete operating contract

**Current evidence.** The original exhausted case has two spent attempts and zero remaining. The 51-target amendment excludes subject01's evaluation rows; it does not reset that case or grant an equivalent renamed attempt. New engineering terminals have zero measured cells and do not allocate the scientific budget.

The latest worker already has important failure behavior: once a backend starts, incomplete numerical work is not falsely reported as zero. Recovery requires externally pinned request/attestation evidence and may replay an existing durable engineering intent without running the numerical backend again. This is existing functionality, not a missing recovery implementation from scratch.

**Why it matters.** With many long cells, interruption handling must preserve identity and distinguish computation, durable acceptance and post-Job closure. A blind retry can duplicate scientific work or obscure a spent attempt; an expired coordination estimate is not permission to proceed on a busy host.

**Proposed closure.** Carry the qualified identity, durable-state and recovery rules into the complete admitted workflow. Specify the current scientific attempt/budget policy, partial-work records, permitted recovery actions and complete-roster consequences. Verify recovery at the actual boundaries used by the composed worker. Preserve the original attempt ledger and never obtain a fresh identity merely to evade its limits.

Fresh operations must continue to use the required current pins, source review, real coordination/pause checks and resource preflight. The latest numerical envelope retained startup/active RAM floors of 10/4 GiB, disk 20 GiB, CPU/Torch threads 1/1 and hidden GPUs; those historical observations are not a fresh lease or a promise that another method fits the same Job caps. No new 30-hour window is inferred.

Evidence: [51-target adoption and attempt limits](phase2/cho_51_target_amendment_adoption_20261013.md), [worker failure/recovery qualification](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [working instructions](../AGENTS.md), [coordination](../AGENT_COORDINATION.md).

### G11 — Published metadata does not restore the newest numerical assets

**Current evidence.** Git contains source, metadata packets, hashes, receipts and exact historical snapshots. The live run trees, fixture arrays, selected/public weights, environments and caches remain local. The October 12 Windows bootstrap predates the new October 15–17 numerical assets and does not restore all of them.

The latest accepted packet contains 39 source-identical copied artifacts/2,519,748 bytes and 43 total files including its packaging. The closeout export preserves the final review and seven exact document snapshots. These are valuable metadata exports, not standalone runnable model distributions. Some source artifacts also depend on authenticated ancestor proofs.

**Why it matters.** A successful push protects the published contents but does not by itself back up the newest local weights or make a fresh clone runnable. Another agent or machine could understand the result yet be unable to reconstruct the next required numerical input.

**Proposed closure.** Inventory the required assets, their sizes/hashes, storage locations, ancestor dependencies and supported restoration procedure. Confirm a durable copy of the necessary non-Git numerical assets. Qualify restoration into a separate fresh checkout with the required authenticated assets and fresh context; broaden to another device when that is the intended claim. Treat restored launchers/history as inert and establish new admission rather than replaying them.

Do not claim that another physical machine has been tested solely because fresh directories were used on this one.

Evidence: [publication limitations](phase2/cho51_push_checkpoint_20261017.md), [linear chain dependencies](phase2/cho51_linear_chain_qualification_20261015.md), [Windows setup](../WINDOWS_SETUP.md), [latest accepted packet](../evidence/cho51-linear-numerical-worker-20261017-v1/README.md), [exact closeout export](../evidence/cho51-linear-numerical-worker-closeout-export-20261017/README.md).

### G12 — Runtime qualification is narrower than general environment portability

**Current evidence.** The latest worker explicitly records 21 observed Python binary replacements, despite both short version strings being `3.12.14`. It freshly pinned its selected runtime files/extensions and rechecked 4,829 loaded-module file hashes. Its narrow CPU numerical execution succeeded; this is positive current evidence, not a failed runtime.

Existing native Windows migration checks used fresh directories on the same host and representative subject/profile fixtures. They are not proof of every cache, every ABI, a GPU path or a different physical device. The full data reconstruction evidence is separate and should not be discounted because migration sampling was narrower.

**Why it matters.** A short version number does not identify exact executable/extension bytes. Import, memory and behavior can change even when Python's printed version is unchanged. A receipt qualifies its pinned candidate and operation, not all future environments.

**Proposed closure.** Establish fresh source/runtime/asset pins for the actual next candidate and intended device, then qualify its changed obligations under appropriate caps. Keep the binary transition explicit. Broaden testing when the source, runtime, hardware or claim changes; do not repeat the entire reconstruction or historical audit without a concrete reason.

A related integration issue is bounded reading. EEGNet's historical generic 4 GiB read request failed on a 12,664-byte weight file. A later standalone bounded public restore succeeded. That specific successor is established, but future factory callers must still pass appropriate bounds; the generic historical reader did not become universally qualified.

Evidence: [numerical runtime record](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [historical allocation/refusal](phase2/cho51_complete_eegnet_qualification_20261015.md), [bounded restore successor](phase2/cho51_staged_restore_qualification_20261015.md), [Windows setup scope](../WINDOWS_SETUP.md).

### G13 — Existing controls do not certify every future real method path

**Current evidence.** The original 81 EEGNet controls passed: nine shuffled-label cases and two sets of 36 controls, including matched no-future checks. Old findings that the remaining 45/36 controls were missing are superseded. The latest synthetic numerical worker also kept query labels outside support loss, optimization, selection, step count and stopping for its precise scope.

**Why it matters.** Controls are valuable only for the paths and potential confounds they exercise. EEGNet baseline controls do not automatically clear every LaBraM selection/adaptation path, and exact signal-copy audits do not settle pretraining exposure or every form of leakage.

**Proposed closure.** Bind relevant controls and held-out-query separation to the actual real-data methods and source/target contract that will be used. State exact coverage and unresolved limits in the report. Preserve existing successful controls and use new checks only where a defined scientific or integration concern requires them; this assessment does not propose an arbitrary new testing matrix.

Evidence: [owner packet control status](phase2/cho_owner_decision_packet_20261010.md), [Gate A acceptance](phase2/gate_a_acceptance_20261012.md), [numerical query separation](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [Phase I matrix](phase1_completion_matrix.md).

### G14 — Historical status language can mislead a new reader

**Current evidence.** Current resume heads correctly lead with the latest checkpoint, but retain many earlier chronological “Next” sections. Older planning documents still contain superseded statements, including Gate A unsigned in the Phase I matrix and no supplied remote in the external-dependency ledger. Gate A acceptance and the published repository supersede those statements.

**Why it matters.** A new collaborator can reopen a resolved issue, replay an obsolete step or misread an older refusal as the current result. Long documents make it difficult to distinguish the latest next action from a dated next action that already occurred.

**Proposed closure.** Maintain a concise current status/gap index with dated authoritative pointers. Add as-of/superseded notes to mutable planning documents when they are next maintained. Preserve immutable reviewed snapshots and historical failure reports byte-for-byte; do not erase the evidence trail to make the story cleaner.

This document supplies a dated gap index, but it does not by itself repair every historical status paragraph. The live handoff remains the execution resume authority.

Evidence: [current handoff](../HANDOFF.md), [Phase I matrix](phase1_completion_matrix.md), [external ledger](external_dependencies.md), [publication's snapshot rules](phase2/cho51_push_checkpoint_20261017.md).

## Adopted design limitations and claim boundaries

The following issues cannot all be “fixed” by adding code. Some are historical facts or adopted design choices. Their immediate closure is accurate reporting and faithful execution. A different experiment would require a separate declared design, rather than an unnoticed change to this one.

### G15 — Retrospective decisions limit prospective and original-population claims

**Current evidence.** Gate A's amended process criterion was accepted after baseline outcomes were known. The 51-target amendment was adopted after known engineering history, including subject01's EEGNet result. It cites exhausted-case and complete-roster constraints, excludes all 20 subject01 evaluation rows consistently and changes the future target population from 52 to 51.

**Why it matters.** The decision is authorized, but it cannot be described as prospective registration before all relevant observations. The eventual result concerns the retained 51-target population; it does not complete the original 52-target study. Consistent exclusion across methods is an important safeguard but does not erase the timing of the decision.

**Proposed closure.** Preserve the dated decision trail, rationale, known observations and exact excluded population in the final methods/report. Distinguish future outcomes from already observed results. Avoid “prospectively specified before any results” or original-52-target completion claims. Do not reinterpret this limitation as permission for an extra original attempt or a requirement to undo an already adopted amendment.

Evidence: [Gate A acceptance](phase2/gate_a_acceptance_20261012.md), [design adoption](phase2/cho_design_decisions_20261012.md), [amendment proposal](phase2/cho_51_target_amendment_proposal_20261012.md), [direct amendment adoption](phase2/cho_51_target_amendment_adoption_20261013.md).

### G16 — Fixed support and missing global chronology constrain generalization

**Current evidence.** Phase II decision D02 adopts fixed-earliest support with the declared query exclusion rule. The five model seeds vary training on that partition; they do not generate five independent support draws. Earlier Phase I notes about choosing seeded support must not be mistaken for an unresolved Phase II choice.

For Cho, the loader concatenates class arrays. Retained within-class order does not authenticate the full global acquisition timeline. The word “earliest” therefore describes the implemented ordering rule, not a proven online sequence of calibration first and later unseen acquisition.

**Why it matters.** The estimand is performance on a fixed calibration partition with training variability. It does not establish robustness over arbitrary calibration-trial draws or prove prospective temporal deployment performance. Five seeds are neither five new subjects nor five independent calibration sessions.

**Proposed closure.** Describe the fixed partition, maximum-support-pool query exclusion, seed role and chronology limits explicitly. Preserve trial/class identities. Use authentic acquisition chronology if it becomes available and the approved design permits it. A future support-resampling or temporal experiment should be a separate declared extension; changing a seed cannot reconstruct missing timing history.

Evidence: [decision register, D02](phase2/decision_register.md), [decision analysis](phase2/decision_analysis.md), [recording provenance limitations](phase2/evaluation_recording_provenance_package_20261011.md), [Phase I chronology record](phase1_completion_matrix.md).

### G17 — Statistics, power and the exploratory margin need precise interpretation

**Current adopted rule.** Average the five seeds exactly within each subject/method. Form 51 paired LoRA-minus-linear differences. The primary directional procedure is one-sided Wilcoxon with Pratt zero handling, asymptotic p-values and no continuity correction at alpha 0.05. The adopted superiority rule requires both **unrounded p < 0.05** and a **positive exact paired arithmetic mean**. Report the separate 95% paired-mean t interval. The secondary superiority family is deliberately empty; full-tuning and EEGNet contrasts are descriptive.

Preserve exact sign/tie classes through the adopted signed-integer encoding. All-zero differences produce p=1 with no superiority; other non-finite results stop analysis, and zero-variance mean intervals become point intervals. These are existing adopted edge-case rules, not new requirements introduced by this assessment.

The retained margin is ±0.05202907926797159 balanced-accuracy units, about ±5.20 percentage points, with a 90% interval for exploratory context. Its planning derivation used the 52-subject EEGNet baseline standard deviation and a known-variance normal approximation, not the unknown future paired-difference variability. The adopted 51-target amendment retains this margin. Formal TOST, equivalence or clinical interchangeability is not part of the adopted claim.

**Why it matters.** Several tempting interpretations would be incorrect:

- The 1,020 cells are not 1,020 independent subjects. The primary analysis has 51 participant units.
- A signed-rank p-value is not a test of the arithmetic mean; the separate positive-mean condition has a purpose.
- A t interval for the mean is not the inversion of the signed-rank test.
- A planning approximation near 80% power does not demonstrate that the future 51-subject paired comparison has 80% power.
- A baseline-derived margin is not an established clinically meaningful equivalence margin.
- Descriptive secondary comparisons cannot become a new tested superiority family after outcomes are known.

**Proposed closure.** Keep the exact adopted analysis settings in the production path; report all pairs, five-seed means, tie/zero counts, unrounded p, exact mean and separate intervals. Explain the margin's derivation and exploratory status. Retain the signed-rank assumptions and approximation limits. Do not silently switch procedures after inspecting outcomes or introduce an unnecessary normality-test gate. A future formal equivalence objective would require a separate prospective decision.

Evidence: [adopted analysis choices](phase2/cho_design_decisions_20261012.md), [51-target units and retained margin](phase2/cho_51_target_amendment_adoption_20261013.md), [owner analysis packet](phase2/cho_owner_decision_packet_20261010.md), [statistical procedure](statistical_procedure.md), [falsification criteria and limitations](falsification_criteria.md), [qualified synthetic analysis](phase2/cho51_synthetic_analysis_qualification_20261013.md).

### G18 — Accepted baseline and local parity evidence support bounded claims

**Current evidence.** The retained baseline seed42 ROC-AUC is 75.6606% versus the paper's 77.15%, a difference of approximately −1.4894 percentage points. The repeat-seed mean is 75.0192%. Gate A was accepted under its precise process-based amendment. The later 450/450 saved-record audit passed; 450 fits represent nine participant units, not 450 independent participants.

Separately, 221-tensor checkpoint correspondence and 119/119 CPU float32 local/reference forward comparisons provide substantial positive implementation evidence. They do not establish every training-gradient, GPU, TUAB or TUEV path. A float32 joint channel-permutation condition failed its original tolerance for both implementations; a float64 diagnostic passed. That limitation remains documented, with fixed channel order retained.

**Why it matters.** “Gate A accepted,” “checkpoint bytes correspond,” “local forward outputs match” and “published numerical result reproduced” are distinct claims. Passing one does not prove all the others. Conversely, it would be inaccurate to say that Gate A is still unsigned or that no forward parity has been demonstrated.

**Proposed closure.** Keep the accepted baseline in its intended role and disclose the numerical difference and scope. Preserve the failed precision condition and successful successor diagnostics. Pursue stronger historical-runtime, numerical-reproduction or hardware parity only if that becomes a stated objective requiring it; do not reopen already accepted baseline work merely to increase validation counts.

Evidence: [Gate A criterion and acceptance](phase2/gate_a_acceptance_20261012.md), [saved-record audit](phase2/phase2_readiness_review_20261012.md), [checkpoint correspondence](checkpoint_correspondence_review.md), [forward parity review](phase2/forward_parity_review.md).

## Wider research and product scope

These entries are not all prerequisites for the adopted public Cho first tranche. They prevent first-tranche progress from being mistaken for completion of every broader ambition.

### G19 — The first tranche does not cover the full research program

**Current evidence.** The selected tranche covers four methods, Cho2017, five seeds and five shots per class. The wider program discusses more systems, three datasets and multiple shot levels. Euclidean alignment is deliberately deferred.

**Why it matters.** Even a successful complete tranche would not establish all adaptation families, all datasets, cross-shot behavior, general pretraining independence or live deployment. Deferred breadth should not be counted as a current implementation bug, but it should not disappear from an overall project-completion claim either.

**Proposed closure.** Report separate completion states for the current tranche and the wider program. If later experiments are wanted, define their questions, datasets, methods, eligibility, cost and analysis before interpreting them. Do not silently add those runs to the current 1,020-cell commitment or infer that their funding/access is already available.

The original Full Project Plan section 4 is not supplied in the cited hypothesis companion. Do not invent a complete H1/H3 specification or promote an older H2 companion into an adopted formal equivalence test for this tranche.

Evidence: [freeze draft scope](phase2/scientific_freeze_draft.md), [owner packet](phase2/cho_owner_decision_packet_20261010.md), [decision register](phase2/decision_register.md), [hypothesis companion limitations](falsification_criteria.md).

### G20 — The realtime demonstration has not established useful live brain control

**Current evidence.** The recorded demonstration used saved offline-preprocessed A09 epochs: 12 windows over 48 seconds/6,144 samples. All outputs were neutral and no command was issued. Transport, gating and fallback behavior worked for that scope. The processing p95 of approximately 5.245 ms excludes four-second acquisition, file handoff and screen paint. The CPU fallback rehearsal was on the same laptop.

**Why it matters.** A functioning transport loop and appropriate abstention are useful, but they do not demonstrate useful held-out command decoding, causal raw-signal processing or end-to-end live latency. Same-laptop fallback is not independent-device validation.

**Proposed closure if live deployment remains a goal.** Connect authentic raw acquisition and causal preprocessing; use frozen development calibration; measure useful held-out commands, abstention and false activations; account for acquisition-to-action latency; and rehearse defined failures on the intended hardware, including another machine if that claim is needed. Do not lower thresholds after observing the demonstration merely to force visible commands.

Evidence: [realtime system and explicit limits](realtime_system.md).

### G21 — Existing scalar summaries cannot produce genuine empirical calibration curves

**Current evidence.** Existing benchmark summaries retain scalar ECE and selected coverage, not the complete probability vectors and labels needed for authentic reliability bins. The plotting utility's demonstration is synthetic.

**Why it matters.** An attractive reliability curve reconstructed from a scalar would invent information that was never retained. A deployed abstention or confidence claim needs probability-level evidence and clear separation between development calibration and held-out evaluation.

**Proposed closure if calibration claims are in scope.** Save approved future probability vectors, labels and identities with appropriate provenance. Fit or select calibration on the designated development data, then compute empirical reliability, coverage and selective-performance summaries on the held-out evaluation. Label any synthetic plot as synthetic. Do not infer bin counts or confidence distributions from aggregate ECE alone.

Evidence: [realtime calibration evidence limits](realtime_system.md).

### G22 — Current external governance, backup and hardware state is not fully verified

**Current evidence.** Older dependency notes mention branch protection, team/PR rehearsal, immediate off-machine synchronization, a second machine, institutional approvals and TUH access. Some historical statements are now superseded: a remote exists and publication has occurred. This local assessment did not check current branch-protection settings, independent backups of the newest numerical assets, current team workflow, a second physical device or institutional status.

**Why it matters.** “Not verified today” is not the same as “definitely missing.” Conversely, a public source push does not prove off-machine custody of excluded weights or approval for a different dataset/use.

**Proposed closure.** Confirm only the external facts needed for the next intended operation and date those observations. Keep current engineering asset portability under G11 separate from institutional/dataset access. TUAB/TUEV are disabled; their access or ethics status is conditional on expanding scope and is not evidence that the current public Cho integration is blocked by TUH.

Do not turn this documentation task into external messaging, account changes or speculative permission requests.

Evidence: [dated external ledger](external_dependencies.md), [current publication](phase2/cho51_push_checkpoint_20261017.md), [Windows restoration boundary](../WINDOWS_SETUP.md), [current scope draft](phase2/scientific_freeze_draft.md).

### G23 — Deferred reference methods and broader paper claims remain unqualified

**Current evidence.** The dated TCPL review records constructor/training/protocol ambiguities and no verified author asset for faithful reproduction. E1's compatible tokenizer/masked-prediction route remains unverified under decision D05. A substitute local objective cannot count as that paper's specified experiment.

**Why it matters.** A local reconstruction may be useful research, but paper-score proximity alone cannot resolve ambiguous class definitions, splits, objectives or training assets. These items affect wider claims of faithful reproduction, not the existence of the currently selected four-method route.

**Proposed closure if those methods return to scope.** Resolve protocol and asset provenance, define an attributable version and qualify its actual implementation. Until then name a reconstruction as a reconstruction and a substitute objective as a substitute. Keep these deferred questions outside the current tranche's completion denominator.

A smaller provenance clarification also remains: the paper's grouped pretraining hours sum to 2,538.38 versus the printed 2,534.78, a 3.60-hour discrepancy. This may merit clarification but is not evidence of leakage, a demonstrated runtime defect or a primary study blocker.

Evidence: [TCPL reference review](phase2/tcpl_reference_review.md), [decision register, D05](phase2/decision_register.md), [pretraining provenance review](checkpoint_pretraining_provenance_20261010.md).

## Historical problems that should not be listed as current blockers

| Older concern | Current interpretation |
| --- | --- |
| Gate A still unsigned | Superseded by direct acceptance on 12 October under the exact retrospective amendment. Stronger numerical reproduction remains unestablished. |
| No owner choice between 52 and 51 evaluation targets | Superseded by direct adoption of the 51-target amendment. Final freeze remains separate. |
| Later saved-record baseline audit still refused/failed | The subsequent 450/450 audit passed. Historical failures remain preserved. |
| The remaining 45/36 original controls have not run | Superseded: all 81 original controls passed. Their coverage is bounded. |
| No data downloaded or no complete reconstruction | Incorrect: the 170-subject Profile A inventory and 52 Cho Profile B reconstructions are established. |
| No numerical implementation for LoRA/full tuning | Incorrect: both have executed probes, source-fold and lifecycle evidence. Complete chain integration remains open. |
| EEGNet weights have never restored successfully | Superseded by the separate bounded public restore. The earlier failed parent transaction remains failed. |
| No actual locked numerical worker exists | Superseded by the 17 October worker. It is an engineering success with zero measured cells. |
| All 38 numerical-worker tests are model runs | Incorrect: the focused tests are metadata/contract cases; one actual numerical case followed. |
| Blocked optional urllib3 IPv6 probe means uncontrolled network failure | The one exact optional import probe was authenticated and blocked; unexpected denials were zero, and network access was not admitted. |
| Child attestation's pending-native flag means final cleanup is unresolved | The child could not certify its own Job closure. Its immutable pending flag is complemented by a separate verified external post-Job closeout. |
| Per-tensor hashes can reconstruct the aggregate adapted-state hash | Incorrect: aggregate state comes from the authenticated raw-tensor observer, not concatenation of digest strings. |
| No repository remote or no publication | Superseded by the published checkpoint. Excluded numerical assets still need separate custody/restoration. |
| Identical deterministic outputs prove that the fresh worker replayed a stale result | Not established: freshness is bound to the new request/claim and observed numerical work. Output equality alone proves neither freshness nor replay. |
| New engineering success restores the original case's spent attempts | Incorrect: original two-spent/zero-remaining history is preserved. |

The point of keeping these distinctions is practical: spend effort closing actual gaps rather than repeatedly reopening already qualified components or erasing preserved failures.

## Recommended order of work

This sequence is a proposed critical path. It does not replace the handoff or authorize execution. Independent scientific-evidence work and engineering preparation can proceed in parallel within their actual authorization.

### Work package 1 — Close the current restoration-factory boundary

**Primary gaps:** G04, with bounded-reader/runtime obligations from G12.

Produce the separately versioned historical/current provenance factory, focused checks and a fresh bounded engineering restore/adapter case. The evidence should clearly identify the historical selected-source producer and current consumer. This is the narrowest next task already identified by the current handoff.

**Exit evidence:** actual strict restore through the new composition, preserved exact source state, correct current provenance and negative rejection of tampered or mixed-context inputs. An additional report describing the mismatch without changing or exercising the boundary would leave G04 open.

### Work package 2 — Compose the current route and parent result contract

**Primary gaps:** G05 and G06.

Connect the adopted route, correct result type, input/publication proofs, recorder and parent verification. Demonstrate the end-to-end behavior with the appropriate engineering or scientific admission; maintain zero scientific cells for engineering-only cases. Any scientific pilot must follow the required scientific decisions and budget, even if most implementation work is ready earlier.

**Exit evidence:** one coherent current composition, exact retained roster semantics and an explicit path for producing and admitting genuine measured cells when authorized. A complete roster generated only as metadata does not demonstrate execution.

### Work package 3 — Complete the missing method chains and realistic resource qualification

**Primary gaps:** G07, G09, G10 and G13.

Use the per-method matrix to target missing stages. Prioritize the LoRA path sufficiently early because it is essential to the primary contrast. Preserve useful existing linear/EEGNet evidence and qualify fresh composition where required. Measure complete allowed real-data cases when scientific gates permit; otherwise keep engineering fixtures and their limits explicit.

**Exit evidence:** qualified current method chains with appropriate held-out boundaries, resource envelopes and failure/recovery behavior; a credible full-study execution plan. Repeating many metadata-only milestones is not a substitute for crossing the next genuine numerical integration boundary.

### Parallel scientific stream — Resolve provenance and prepare the named freeze

**Primary gaps:** G01, G02 and claim limits G15–G18.

Prepare the checkpoint-specific evidence/uncertainty review and final concrete experiment package. Retain existing owner-adopted scope and analysis choices. Present the remaining owner decision only once its implementation and evidence limits are reviewable. No fabricated overlap manifest or engineering receipt can substitute for this scientific decision.

**Exit evidence:** supported exposure findings or explicit limitations, identified eligible claims and a separately recorded final freeze for the exact version that will run.

### Parallel reproducibility stream — Preserve and restore the actual assets

**Primary gaps:** G11, relevant parts of G12/G14/G22.

Establish the current numerical asset inventory, durable custody and authenticated restoration. Keep a concise current entry point without modifying frozen evidence. This can proceed alongside engineering and avoids reaching a runnable stage that only one local working directory can support.

**Exit evidence:** an actual fresh-checkout restoration with the necessary non-Git inputs, dated context and explicit remaining device limits.

### Work package 4 — Admit and execute the real study, then analyze the complete roster

**Primary gaps:** G03 and G08, dependent on the earlier scientific/engineering gates.

Execute the authorized retained cases with their full evidence, preserve partial failures honestly, collect the complete eligible roster and apply the exact adopted paired analysis. Keep exploratory, descriptive and primary claims distinct.

**Exit evidence:** 1,020 accepted eligible cells, 204 subject-method seed means, 51 paired differences, reproducible prespecified analysis and a report with provenance/design limitations. A partial pilot remains a pilot. A negative effect or non-significant p-value is a valid study outcome, not permission to silently change the plan.

### Optional later work — Broader methods, datasets and realtime use

**Primary gaps:** G19–G23.

Choose later scope deliberately and cost it separately. These extensions should not delay the current integration merely because they exist in the broad vision, and their omission should remain visible when reporting overall project completion.

## Proposed readiness criteria

These criteria summarize closure evidence from the register. They are not new owner-adopted rules or an approval request.

### Ready for the next bounded engineering case

- Exact candidate/source ownership, historical/current provenance roles and intended numerical actions are defined.
- Necessary assets are authenticated and available; the selected runtime is pinned.
- The relevant versioned boundary has focused validation, with failures preserved rather than reset.
- Fresh coordination, pause/resource checks and native admission apply to that particular operation.
- Expected result type and counters are honest: engineering work is not counted as measured science.
- Failure, durable acceptance, recovery and external Job closure have explicit meanings.

The latest worker already satisfies many of these criteria for its historical narrow scope. The next changed factory still needs fresh evidence for its new scope.

### Ready to launch the scientific study

- The checkpoint-cohort evidence/uncertainty review and permissible scientific claims are recorded.
- The final named experiment freeze is separately accepted for the concrete version.
- The 51-target, four-method route and measured-cell parent composition are qualified.
- The required complete method chains, genuine collection/admission and paired reporting path are integrated.
- Scientific attempt/budget and recovery policies preserve the original history.
- A representative current resource plan supports the intended execution and evidence retention.
- Required numerical assets and current-source/runtime identities can be restored and verified.

These conditions concern a valid study launch. They do not require advance proof that LoRA will win.

### Ready to make final first-tranche claims

- All 1,020 retained cells are validly accepted; missing/excluded cells are handled exactly as adopted, without imputation or scope switching.
- The 204 five-seed means and 51 paired differences derive from those actual cells.
- The primary p-value/positive-mean condition and separate intervals are computed with the adopted settings.
- Secondary descriptive and exploratory-margin results remain labeled as such.
- Retrospectivity, fixed support, chronology, baseline and checkpoint-exposure limitations are disclosed.
- The report and analysis are traceable to exact input, source, runtime and evidence versions.

The wider program and realtime deployment require their own additional evidence; first-tranche completion would not close those items automatically.

## Planning risks and reporting discipline

The main planning risk is treating more proof files or passing metadata tests as if they automatically reduce the remaining scientific work. Evidence preservation has been strong, but the next useful milestones should cross the actual factory, method-chain and measured-cell boundaries. A new qualification should answer a specific unresolved question.

The main implementation risk is accepting each component in isolation while leaving incompatible provenance, scope or result contracts between them. This is why the next deliverables should demonstrate genuine composition, not merely produce another independently correct helper.

The main scientific risk is overstating what a valid execution would establish. Unknown checkpoint exposure, retrospective scope changes, fixed support and a narrow first tranche constrain the claims even if every cell executes perfectly. These limitations must remain visible in the final report.

The main operational risk is scaling before cost, recovery and asset custody are concrete. Keep uncertain counts unknown when computation fails; never invent zero work, reuse exhausted identity, weaken resource floors or infer a peer release from an elapsed estimate.

No defensible exact percentage complete or finish date follows from the present evidence. The specific next action is clear: close G04's provenance-aware restoration factory, while scientific provenance and asset restoration progress independently. The final results remain downstream of genuine integration and the remaining scientific decisions.

## Source map

Use current resume documents to choose the next action, adopted decisions for study authority, and dated qualification reports for exact executed evidence. Candidate READMEs describe implementation scope; they do not by themselves prove successful execution.

| Question | Primary local sources |
| --- | --- |
| What is the current next step? | [HANDOFF](../HANDOFF.md), [working instructions](../AGENTS.md), [17 October publication](phase2/cho51_push_checkpoint_20261017.md) |
| What actually ran most recently? | [numerical qualification](phase2/cho51_linear_numerical_worker_qualification_20261017.md), [accepted packet](../evidence/cho51-linear-numerical-worker-20261017-v1/README.md), [exact final closeout](../evidence/cho51-linear-numerical-worker-closeout-export-20261017/README.md) |
| Which scientific choices are adopted? | [design decisions](phase2/cho_design_decisions_20261012.md), [51-target adoption](phase2/cho_51_target_amendment_adoption_20261013.md), [Gate A acceptance](phase2/gate_a_acceptance_20261012.md) |
| What is unknown about pretraining exposure? | [checkpoint review](checkpoint_pretraining_provenance_20261010.md), [review contract](phase2/checkpoint_cohort_review_contract_20261010.md), [evaluation inventory](phase2/evaluation_recording_provenance_package_20261011.md) |
| Which method stages exist? | [probes](phase2/cho51_numerical_probes_20261015.md), [source folds](phase2/cho51_source_fold_qualification_20261015.md), [linear chain](phase2/cho51_linear_chain_qualification_20261015.md), [EEGNet publication/refusals](phase2/cho51_complete_eegnet_qualification_20261015.md), [staged restore](phase2/cho51_staged_restore_qualification_20261015.md) |
| What do collection tests establish? | [collection](phase2/cho51_collection_qualification_20261015.md), [actual-input composition](phase2/cho51_input_composition_qualification_20261015.md), [receipt/selector](phase2/cho51_receipt_selector_qualification_20261015.md), [synthetic paired analysis](phase2/cho51_synthetic_analysis_qualification_20261013.md) |
| What data and earlier results are complete? | [all-subject reconstruction](phase2/cho_all52_cache_reconstruction_20261011.md), [Phase I matrix](phase1_completion_matrix.md), [baseline readiness review](phase2/phase2_readiness_review_20261012.md) |
| What limits interpretation? | [decision analysis](phase2/decision_analysis.md), [statistical procedure](statistical_procedure.md), [falsification criteria](falsification_criteria.md), [forward parity](phase2/forward_parity_review.md) |
| What remains outside the first tranche? | [freeze draft](phase2/scientific_freeze_draft.md), [realtime system](realtime_system.md), [TCPL review](phase2/tcpl_reference_review.md), [external ledger, dated](external_dependencies.md) |

Future updates should name the new as-of baseline, state exactly which gap changed, link its concrete closure evidence and retain the distinction between executed qualification, adopted scientific authority and interpretation. Frozen historical reports and snapshot exports should remain unchanged.
