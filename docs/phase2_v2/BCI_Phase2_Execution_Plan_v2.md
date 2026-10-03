# Phase II execution plan

Version 2.0 | Implementation sequence and acceptance evidence | 5 September 2026

## Execution approach and boundaries

This companion specifies how I will implement and execute the revised research plan when implementation/experimental work is requested. The present deliverable is the plan itself. No training, gate approval, deletion, remote publication or external expenditure is authorized merely by creating these documents.

### Operating assumptions

I am the implementation owner across the existing core, data, encoder, adaptation, evaluation and real-time lanes. The schedule assumes one active coding agent and one admitted GPU job, not five simultaneous researchers. An actual independent reviewer and scientific decision owner must be identified before claiming independent review or sign-off.

I will work in small reviewable changes, keep Phase I source interfaces stable where possible, and put Phase II configuration and result identities in new namespaces. Existing source-bound controls must be refreshed when source/config/test/environment changes invalidate them. Historical receipts remain historical.

### Work sequence

- P0: inspect current state and assemble the decision/admission receipt.

- P1: implement the split, manifest, provenance and experiment-contract foundation.

- P2: verify the encoder and real adaptation paths; establish E1 feasibility.

- P3: measure a representative pilot, freeze settings and admit compute.

- P4: run and audit primary E2, then expand only within the measured budget.

- P5: complete admitted E1 and core causal E3/montage E4 work.

- P6: analyze, obtain review, regenerate outputs and package release readiness.

### Definition of an executable milestone

Each package below has an input, concrete artifacts, checks and exit evidence. A package is done only when its evidence exists and passes; writing scaffolding is not an experiment result. Proposed filenames are implementation targets, not claims that commands or modules already exist.

## P0-P1: admission and experiment foundation

### P0 - Read-only admission; intention: day 1

Inspect Git identity/status, project process trees, locks, logs, available disk/RAM/VRAM and cooling state. Re-run scripts/preflight.py. Confirm the Phase I evidence hashes and original plan hash. Verify lock ownership before restarting anything; never delete a live or unverified lock.

Create a dated Phase II decision register covering D01-D06. Present the revised roster, primary comparison and support proposal as concrete choices. While decisions are pending, continue static contract design and tests that do not depend on those choices. Do not request scientific sign-off on an incomplete result.

Artifacts: docs/phase2/decision_register.md and runs/phase2/admission/<timestamp>.json (proposed). Exit: admitted scope and unresolved choices are explicit; heavy runs remain deferred until resource guards pass.

### P1 - Partitions and run schema; intention: days 2-4

Add a Phase II episode-manifest module alongside core/splits.py rather than changing the frozen earliest_balanced_episode behavior. Proposed modules: evaluation/phase2_protocol.py and evaluation/phase2_records.py. Proposed configs: configs/phase2/protocol.toml, methods.toml and analysis.toml.

Implement outer target exclusion, source-only inner folds, nested support and fixed query identity, class eligibility, explicit model/support/montage seeds, and stable hashes. Attach selection provenance and preprocessing/checkpoint identities to each evaluation cell. Keep original RunRecord contracts intact or use a separately versioned envelope.

Tests: query identity is identical across shots; unused support examples are inaccessible; outer target cannot enter source validation; all methods share partitions; malformed manifests, class loss, duplicate subjects and changed hashes fail closed. Tampering with labels or partitions invalidates a saved receipt.

Exit: synthetic tests and representative real-data manifest audits pass; excluded-subject counts are visible before training. User-owned support and roster choices are adopted before frozen experiment identities are generated.

## P2: verified encoder, adaptation and E1 feasibility

### Encoder integration; intention: days 5-8

Work in encoder/labram.py and new narrowly scoped helpers. Pin reference code/checkpoints, map retained weights, verify actual feature dimensions and channel identity semantics, and compare forward outputs on identical inputs. State tolerance and backend/precision assumptions in the receipt. Preserve the actual parameter count.

Resolve external TUAB/TUEV verification versus the documented weaker route. Missing access does not justify describing local depth ordering as external reproduction. Deliver a verification report with separate tensor identity, numerical parity, downstream reproduction and scientific-approval fields.

### Adaptation integration; intention: days 8-12

Implement a LaBraM-specific LoRA path that reaches the actual QKV computation. Add verified adapters and support-generated prompts with explicit names and dimensions. Use the current adaptation loop only after its parameter-selection and normalization semantics are declared; its default currently selects all parameters.

For linear, partial and full tuning, test trainable masks and head policy. For all methods, snapshot full state dictionaries, show intended support changes, prove source invariance and query invariance, and exercise the one-shot case. Fit target alignment only on support. Implement faithful TCPL separately from the generic prompt stand-in.

### E1 feasibility in the same milestone

Inventory tokenizer weights and omitted masked-prediction components before corpus preprocessing. Implement a one-recording loss/entropy smoke with pinned targets, masks and normalization. Test that tokenizer codebooks and model buffers do not update during inference. Compare the loss with the reference implementation.

Artifacts: proposed runs/phase2/verification/, adaptation_smoke/ and e1_feasibility/ receipts; docs/phase2/integration_review.md. Exit: every admitted method passes semantic/state tests; E1 is either technically ready or explicitly blocked with the missing component named. No full E2 sweep launches from synthetic success alone.

## P3-P4: pilot, freeze and primary E2 execution

### P3 - Representative pilot; intention: days 13-15

Choose development subjects without inspecting new target-query outcomes. Measure large and small inputs, one-shot and 20-shot support, classical anchors, full tuning, LoRA and prompt/TCPL paths. Include source training and validation cost, target adaptation, query inference, checkpoint storage and control-refresh cost. Add longer model-specific pilots where one batch does not predict runtime.

Proposed files: scripts/phase2_pilot.py and runs/phase2/pilot/<config-hash>/. Record observed seconds, peak RAM/VRAM, disk growth and thermal waits. Forecast remaining cells with per-method measurements and a stated conservative retry allowance. Do not assume a timing smoke supplies a performance estimate.

Freeze adopted protocol, selection procedure, method roster, seeds, primary/secondary comparisons, normalization, retry rules, resource ceiling and output identities. Save a machine-readable matrix manifest with expected cells and reusable source-fit dependencies. Admission requires the measured remaining workload to fit the resource and schedule envelope.

### P4 - Core first; intention: weeks 8-10

Build the resumable orchestrator and audit before long training: proposed scripts/run_phase2.py, scripts/audit_phase2.py and evaluation/phase2_runner.py. Begin with Cho2017 five-shot linear probe, LoRA, full tuning and matched EEGNet/EA-tangent anchors. These establish the primary comparison and regularization reference.

After integration and integrity checks pass, expand to the remaining roster, shot levels and secondary datasets within the admitted budget. Do not decide expansion from favorable accuracy. Where affordable, reuse one immutable source fit across compatible support conditions, retaining its original provenance and charging its compute once.

Checks: interrupted writes never become completed cells; resume rejects identity mismatches; duplicate workers cannot claim the same cell; retries preserve failures; aggregation refuses unexplained missing/duplicate cells. Monitor resources and inspect actual process/log state before restarting.

Exit: the declared primary grid is complete and independently audited against predictions and manifests. Expanded scope is either complete or explicitly deferred; no missing cells are silently treated as successful.

## P5: E1, causal E3 and montage E4

### E1 execution after feasibility

Prepare matched manifest identities, equal token budgets, pretrained/random-weight paths and subject-cluster analysis. Preserve tokenizer and head identity in every record. Generate loss and entropy diagnostics, clustered uncertainty and the confounding statement. If feasibility failed, deliver that report and obtain a scope decision rather than training a substitute tokenizer.

### E3 engineering before timing claims

Add a stateful causal preprocessing component under realtime/ and connect it to the existing stream/window pipeline. Tests perturb future samples, vary chunk boundaries and reset streams to prove past outputs and state transitions behave correctly. Align training/calibration preprocessing with the deployed path.

Run EEGNet 0.5/1/2/4-second windows, then verified LaBraM 1/2/4-second windows. Freeze thresholds, evidence accumulation and reset/cooldown from permitted validation. Keep batched accuracy measurements separate from batch-one CPU timing. Save command traces, received-sample hashes, delay distributions, abstentions and deadline misses.

Report idle-period false activations only when suitable idle data exist. An all-abstention rehearsal establishes integration, not usability. CPU failure or missed deadlines are reported honestly; do not substitute GPU latency for the CPU requirement.

### E4 controls and deployment distinction

Build named montage manifests and separate E4a ablation from E4b reduced-hardware preprocessing. Perturb excluded channels and prove retained E4b outputs do not change. Exercise random montages with paired seeds, verify names and publish class/channel exclusions. Electrode identity sensitivity is an outcome, not an arbitrary pass threshold.

Run the primary Cho retention curve first, with fixed query identities and subject-level intervals. Expand to MMIDB and hardware-faithful training only within the frozen scope and budget. Save identity-permutation diagnostics separately from correctness tests.

Exit: admitted E1 evidence or an explicit feasibility outcome; core E3 CPU receipt and causal tests; core E4 curve and preprocessing-dependency tests. Different completion statuses remain visible in the Gate C packet.

## P6: analysis, checks and delivery

### Analysis and scientific review; intention: week 11

Implement analysis from audited records rather than copied spreadsheets. Align subject identities, average seeds within subject, calculate paired differences/95% intervals, prespecified Wilcoxon and TOST/90% intervals, and declared multiplicity adjustment. Keep the frozen margin and label power as design/sensitivity analysis. Investigate cohort attrition before interpreting results.

Prepare a Gate C evidence packet with primary results, failures, deviations, integration limits, E1 confounds, E3/E4 completion and links to every figure input. Obtain a real independent review if available. If unavailable, label self-review and automated checks accurately and leave independent sign-off pending.

### Quality after each substantive change

Run focused tests for changed behavior first, then the established full lint/type/test checks from a stable source snapshot. Use scripts/verify_phase1_quality.py and the source-bound control workflow as documented. A missing or resource-deferred control refresh prevents a checked source commit; do not weaken guards or relabel old evidence.

Existing commands, for later execution in the project environment: python -B scripts/preflight.py; python -m scripts.refresh_source_bound_controls --check-only; python -m scripts.refresh_source_bound_controls; python scripts/verify_phase1_quality.py. Resolve the project Python and Git explicitly; command availability must be checked on the current machine.

### Write-up and reproducibility; intentions: weeks 12-14

Week 12 stays recovery capacity. Week 13 writes methods, results and limitations and regenerates all figures. Week 14 tests installation and figure regeneration from a fresh checkout plus a separately supplied, permitted results bundle; runs are ignored by Git and cannot be assumed present.

Deliver revised methods, analysis tables, figures with source hashes, run manifest, failure/retry log, reproduction instructions, environment specification and demo receipt. Confirm raw data/weights/credentials are excluded from the release package. Public publication, external messages and cloud spend require their own authorization; local packaging can complete first.

### Completion statement

Report exactly which experiments and gates passed, which yielded negative or inconclusive outcomes, which were deferred and why, and which scientific approvals remain unsigned. Do not call the project formally complete solely because code imports, tests pass or the planned calendar has elapsed.

## First ten work intentions and handoff checklist

These are ordered implementation intentions after work is authorized, not guaranteed one-day durations. Dependencies take precedence over the calendar. Unresolved scientific decisions do not prevent independent inspection and scaffolding.

| Day | Concrete output |
| --- | --- |
| 1 | Fresh admission receipt; process/lock/resource inventory; D01-D06 decision register with proposed options. |
| 2 | Versioned episode and evaluation-cell schemas; explicit support/query and source-validation roles. |
| 3 | Nested-support/common-query construction; exclusion counts; synthetic split and leakage tests. |
| 4 | Real-data manifest audit; config and record identity validation; resume/tamper tests. |
| 5 | Checkpoint/reference inventory and electrode/shape correctness checks. |
| 6 | Numerical forward comparison; documented external-verification or weaker-route status. |
| 7 | LaBraM-aware LoRA integration and initial-identity/effective-update tests. |
| 8 | Linear/full/partial adaptation state tests; head and normalization policy. |
| 9 | Adapters/prompts and separate TCPL smoke; E1 tokenizer/head feasibility outcome. |
| 10 | Integrated readiness review; representative pilot specification and remaining-work estimate. |

### Handoff after every milestone

Record completed files, exact source/config identity, checks run and their results, current processes/locks, resource observations, known limitations, unresolved decisions and the next admitted command. Preserve logs and checkpoints before restarting. Give progress updates that distinguish coding progress from experimental evidence.

### Version pairing

This execution plan implements BCI_Phase2_Research_v2.docx, version 2.0 dated 5 September 2026. Scientific definitions live in that document; this companion owns implementation order and acceptance evidence. If either changes, update both version identifiers and record the reason before the affected work.
