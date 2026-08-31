# Phase I completion matrix

This matrix audits the Week 0–5 build plan against current local evidence. A local
item is complete only when a file or machine-written run artifact proves it.
Team, institutional, private-data, and external-correspondence items remain
separate and are never silently converted into local successes.

## Week 0 — Mobilisation

| Requirement | State | Evidence |
|---|---|---|
| Supplied plans read; lane skeleton and ownership | Complete for the supplied Phase I/II day-by-day documents | Lane READMEs and root `README.md`; the referenced Full Project Plan and Team Execution Plan were not supplied |
| Local source repository | Complete locally | Local `main` branch, initial snapshot `bf78379b6ec67a6fef3db83d8e3c34f37b35299b`; raw data, weights, run outputs and secrets excluded |
| Branch protection, five-person PR/conflict rehearsal | External-only | `docs/external_dependencies.md`; no remote/team supplied |
| Cloud instance, persistent disk, hourly cost | Replaced by approved laptop | `configs/benchmark.toml`, `runs/dataset_inventory.json`, and measured cost report |
| Reproducible pinned environment | Complete | `requirements.lock` plus three exact component lockfiles |
| Official LaBraM Base checkpoint load and real forward pass | Functional evidence complete; literal parameter-count check unresolved | `runs/labram_ready_state.json`, `configs/labram.toml`, `docs/checkpoint_correspondence_review.md`: all 221 retained tensors match original bytes/shapes without executing pickle; no claim of forward parity |
| Email authors about Large/Huge | External-only | No correspondence fabricated; external ledger |
| TUH agreement and ethics submission | External-only/unconfirmed | Requires user identity/institution; TUAB/TUEV disabled |
| TCPL/LoRA/adapter/prompt design study | Local method review complete; missing original critique remains external | `docs/adaptation_reference_notes.md`, corrected TCPL source review and implemented prompt contract; generic variants are not claimed as paper reproductions |
| BCI IV 2a, Cho2017, MMIDB downloaded; anomalies and footprint recorded | Complete | 9/52/109 subjects; inventory, artifact audits, channel/anomaly docs |
| Actual download elapsed times | Not retrospectively verifiable | Inventory records first-to-last file-modification spans, not instrumented transfer durations; no missing historical times are fabricated |
| LSL stock loopback and 60-second true-rate replay | Complete | `runs/lsl_loopback_60s.json` (7,680/7,680 samples, drift gate passed) |
| Interface/stream contract drafted | Complete | `core/contracts.py`, `realtime/streaming.py` |

## Week 1 — Contract and data foundation

| Requirement | State | Evidence |
|---|---|---|
| Contracted Epoch, Split, Decoder, Stream, RunRecord/Episode types | Complete | `core/contracts.py`, tests |
| Explicit local contract v1 freeze | Complete, recorded late rather than backdated | `configs/contract_freeze.toml`, hash-verification tests; original team circulation remains unavailable |
| Deterministic configuration and machine-written atomic run records | Complete | `core/config.py`, `core/run_record.py`, tests |
| BCI IV 2a all subjects, named canonical channels, Profile A | Complete | Processed artifacts, manifests, 9/9 structural audits |
| Earliest balanced support and disjoint query | Fixed-earliest implementation complete; literal seeded-draw requirement unresolved | `core/splits.py` has no seed argument; all model seeds share the same partition. User decision pending in `docs/phase1_protocol_decisions.md`; frozen results remain unchanged. |
| Cho earliest-trial chronology caveat | Documented limitation | Loader concatenates class arrays; available within-class order is not proven acquisition chronology |
| Channel inventory/canonicalisation including MMIDB dot padding | Complete | `data/channel_names.py`, canonicalisation table, tests |
| Configured amplitude rejection | Complete and permanently frozen | Complete-cohort 99.9th-percentile rule and audit record |
| LSL outlet/inlet, no sample loss, causal ring buffer and windowing | Complete | LSL record, streaming modules and tests |

## Week 2 — Baseline harness and Gate A

| Requirement | State | Evidence |
|---|---|---|
| LOSO/grouped splitters, metrics, intervals over subjects | Complete | Split/metric/reporting modules and tests |
| EEGNet under the decoder harness and support-only adaptation | Complete | Baseline/adaptation modules and real episodic LoRA record |
| EEGNet implementation checked against Lawhern et al. | Review complete; exact parity not established | `docs/eegnet_implementation_review.md`; known padding, dropout and classifier-constraint differences remain explicit |
| Distinct source-only EEGNet fit followed by full-model support-only fine-tuning | Complete locally | 45/45 separately audited two-class BCI records; source/support/query boundaries tested, high subject scores remain flagged |
| Shuffled-label and subject-disjointness CI | Complete locally, with current-source full-cohort controls | Nine fresh shuffled-label fits: 48.77%; exact source/input/environment binding, reconstructed inputs and fail-closed merge checks. See `docs/source_bound_controls_review.md`. |
| Figure regeneration and results aggregation | Complete | Scripts plus generated partial/final artifacts |
| End-to-end replay → gate → interface | Complete | Persisted GPU and CPU held-out demo records |
| Actual true-rate LSL → decoder → native command grid | Complete locally, including visible rehearsal | `runs/live_demo/20260831T022419655475Z/result.json`; 6,144 unchanged samples, 12 acknowledged windows, explicit abstention, inspected native renders |
| Gate A MOABB reproduction | **Not signed** | Published reference verified; real Keras smoke and 5/450 full-protocol fits validated, including independent raw-input reconstruction for all five. 445 fits remain; the reference queue defers when RAM is below its unchanged start threshold. Acceptance rule remains unresolved. See Gate A/deviation/reference records. |

Work after Gate A is explicitly exploratory under the user's direction. This does
not convert Gate A into a pass.

## Week 3 — Unified datasets, profiles, adaptation and real-time controls

| Requirement | State | Evidence |
|---|---|---|
| Pre-cue control at chance in CI | Complete locally, with current-source full-cohort controls | All 36 configured fresh fits: 24.86%; all input identities and predictions independently checked. Matching evidence is revalidated on each merge; source/input/environment changes require a new bundle. Historical evidence remains separate. |
| Profile B implementation and Profile A/B cross-check | Local cross-check and ordered conditional explanation complete; no score-equivalence claim | All 576 A01 raw trials match both profiles exactly. Seven predeclared conditions reconstruct the full 31.25-pp score gap; units and CAR give the largest positive conditional effects. All endpoint histories/predictions reproduce exactly; interactions and one-subject limits remain explicit. See `docs/profile_comparison_review.md`. |
| Cho2017 and MMIDB unified Epoch records | Complete | 52/109 artifacts; all structural audits pass |
| Explicit MMIDB anomaly handling | Complete | Named anomalies plus fail-closed S104 boundary policy and regression test |
| Generic LoRA, adapters, prompt generator; stand-in runs | Complete | Modules, tests, `runs/adaptation_standin_smoke.json` |
| Prompt tokens actually condition attention and query predictions | Complete locally | Both modes in `runs/prompt_transformer_smoke.json`; frozen backbone, fixed support context, no query-time updates, bounded sequence length |
| Ten-shot real episodic LoRA number | Complete/negative result | `runs/episodic_lora_eegnet.json`; support-only, timed |
| Confidence gate, explicit neutral state, accumulated evidence | Complete | Modules, tests, persisted demos |
| CPU/GPU latency | Complete | `runs/latency_cpu_gpu.json` |
| Statistical procedure frozen | Complete | `docs/statistical_procedure.md` |

## Week 4 — Baselines and encoder readiness

| Requirement | State | Evidence |
|---|---|---|
| Checkpoint/resume/incremental atomic records and cost estimate | Complete | Benchmark runner, schema/hash validation, launch estimates |
| EEGNet, Shallow, Deep, FBCSP, tangent LR and EA variants | Complete in harness | Seven configured variants and baseline tests |
| Dry fold and full five-seed sweep | BCI and Cho complete; MMIDB running to final hashes | BCI 315/315, Cho 1,820/1,820; MMIDB tracked in `runs/phase1_status.json` |
| ITR, ECE/reliability and accuracy–coverage | Complete implementation, including chart rendering | Evaluation modules, hand-worked/unit tests and synthetic calibration diagram; benchmark ECE scalars alone cannot reconstruct empirical reliability bins |
| Safe LaBraM real-epoch input, mapping, sequence handling | Complete | Ready-state record, encoder tests |
| Pretraining hours, partial-tuning appendix and matched fine-tuning reference | Complete | `docs/labram_reference_notes.md`, `configs/labram_paper_reference.toml`; targets are not local reproductions |
| Partial depth 0/4/8/12/all | Complete | Config and trainable-parameter counts in ready-state record |
| LoRA 4/8/16, bottleneck adapters, prompt modes | Complete | Frozen adaptation config, modules, tests and smoke record |
| Name-based electrode masking | Complete | Encoder utility and tests |

## Week 5 — Benchmark, Gate B and working system

| Requirement | State | Evidence |
|---|---|---|
| Complete three-dataset benchmark table with intervals | Running | Final-hash resumable sweep; status generator is authoritative |
| Seed variation distinguished from subject variation | Complete in reporting | Separate seed-mean SD and shared-subject count; subject SD still drives intervals and H2 |
| Full aggregated diagnostic table and class balance beside accuracy figures | Complete implementation; final grid regeneration pending | Snapshot-locked primary/diagnostic CSVs, tested subject weighting and repeated-seed counts, visually checked class-balance-labelled figures |
| Plausibility review/red-team above 65–78% | Targeted controls and all completed Cho-method reviews complete; final MMIDB/grid review pending | Six Cho subject 43 and three MMIDB subject 085 shuffled-label controls; Cho reviews including all 52 EA fits retain unresolved flags and the loader-boundary limitation. See `docs/cho_classical_plausibility_review.md`. |
| Complete-cohort exact signal-copy review | Complete; no exact copies found | 170 subjects, 20,599 retained trials; `runs/corpus_duplicate_audit.json` and `docs/corpus_duplicate_review.md`; not blanket leakage clearance |
| Preprocessing/artifact thresholds permanently frozen | Complete | Frozen config, 22 rejected trials total, every class retained |
| Working held-out demonstrator and CPU backup path | Complete locally | A09 GPU and A08 CPU persisted records; no second physical machine |
| Gate B local deliverables | Pending complete table | Gate B now requires the same hash/config-verified visible native LSL receipt as the Phase I status checker; legacy array frames alone are insufficient |
| Gate B scientific sign-off | Cannot pass while Gate A is unsigned | Separate `passed` and `local_deliverables_complete` fields |
| H2 equivalence margin and achieved power from Cho variance | Complete conditional planning freeze | 260 source records, 52 subjects, ±5.20290793 pp; approximate design power 0.80, not guaranteed H2 power |
| E3 window sweep config | Complete | 0.5/1/2/4 s, 250 ms stride, causal/query-only |
| Methodology, datasets, real-time sections | Complete drafts | `docs/methodology_draft.md`, `docs/realtime_system.md` |
| Falsification criteria updated with empirical margin | Local H2 companion complete | `docs/falsification_criteria.md`, machine-written freeze; original Full Project Plan section 4 was not supplied |

## External-only closure items

The following cannot be completed from this folder: institutional ethics/TUH
submissions, LaBraM author correspondence, a remote Git/team rehearsal, cloud
billing/persistent-instance tests, and a second physical replay machine. They are
tracked in `docs/external_dependencies.md`; local substitutes are explicitly
labelled rather than claimed as equivalent.
