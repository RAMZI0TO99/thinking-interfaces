# Thinking Interfaces

A reproducible EEG motor-imagery research project investigating how pretrained
representations and adaptation methods behave with small target support sets.
Engineering correctness, scientific validity and useful real-time interaction
are separate goals.

The project currently focuses on the Cho2017 five-shot comparison: LaBraM linear
probing, LoRA, full tuning and EEGNet, across51 evaluation targets and five seeds.
The available source cohort contains52 subjects. The planned first tranche has
1,020 evaluation cells; **zero accepted final scientific cells are complete**.

## Start here

- [Current handoff and next step](HANDOFF.md)
- [3 November publication checkpoint](docs/phase2/cho51_push_checkpoint_20261103.md)
- [Project plan, progress and literature review](docs/where%20are%20we/README.md)
- [Project execution policy](docs/PROJECT_EXECUTION_POLICY.md)
- [Same-project agent coordination](AGENT_COORDINATION.md)
- [Windows setup](WINDOWS_SETUP.md) and [continuation guide](CONTINUE_HERE.md)

Work is scheduled and reviewed within this project. Root handles local admission
under the owner's scope and the resource/cleanup rules in the execution policy.

## Engineering progress

The provenance-aware restoration factory, parent/numerical-worker composition
and metadata boundary have scoped engineering qualifications. P3 metadata/profile
and telemetry sources are implemented and statically reviewed.

The [local validation contract](docs/phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](docs/phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](docs/phase2/cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [BD1 B0/B1 provider/driver and qualification-entry design](docs/phase2/cho51_p3_b0b1_design_20261103.md) is independently accepted for design only. Eight files define proposed native G0/S0 under an independently adopted H0, a distinct one-request E1_PROTOCOL entry, witness ownership and conditional fixed-record packing. No test child or Q/S discovery is part of E1. Source remains1125/51, fixed Q360/S140 and765 exact held rows; no new methods or execution. All33 report roles and16 closeout roles remain unchanged; P stays disabled.

The [PC1 supplied implementation](docs/phase2/cho51_p3_pc1_implementation_20261103.md), PC1 design and whole-operation predecessors remain frozen. BD1's40 scenarios join all32 PC1,32 whole-operation,32 CM6 and24 S140 scenarios as unqualified obligations. Conditional byte fit does not establish original H0 availability/isolation, full populations, final M witness retention or complete capture/closure/resource feasibility. Execution remains REFUSED_UNADMITTED. Next is source-only native G0/S0 skeleton and fixed wire/record codecs with unavailable-H0 refusal, finite effect/transition accounting and independent review; no compile/run. All original guards and debt remain.

The [bounded resolver](docs/phase2/cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](docs/phase2/cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](docs/phase2/cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](docs/phase2/cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](docs/phase2/cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](docs/phase2/cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

## Research and evidence

[The project plan](docs/where%20are%20we/PROJECT_PLAN.md) explains the first tranche
and wider research program. [The literature review](docs/where%20are%20we/LITERATURE_REVIEW.md)
covers the datasets, models and previous studies.
[The evidence index](docs/where%20are%20we/EVIDENCE_INDEX.md) distinguishes static
review, executed engineering checks and scientific decisions.

Gate A is accepted only under the owner's retrospective amendment. The final
scientific freeze remains unsigned. No engineering pass establishes predictive
performance, checkpoint independence or completion of the study.

## Repository layout

| Area | Responsibility |
| --- | --- |
| `core/`, `configs/` | Contracts, configuration, run records, metrics and gates |
| `encoder/` | LaBraM loading and representation controls |
| `adaptation/` | Episodic adaptation, LoRA, adapters and prompts |
| `data/` | Dataset loaders, channel mapping and preprocessing |
| `evaluation/` | Baselines, leakage checks, statistics and figures |
| `realtime/` | Causal buffering, LSL, abstention and interface |
| `docs/phase2/` | Designs, versioned candidates and dated engineering reports |
| `evidence/` | Published source and metadata packets |
| `tools/migration/` | Verified Windows restoration tooling |

Raw recordings, processed signals, selected weights, runtime environments and
live run trees are not ordinary Git payloads. Historical receipts remain dated
evidence; a fresh clone needs authenticated assets and current runtime checks.

The previous long status pages are preserved in the
[documentation archive](docs/history/project_focus_20261028/README.md).
Current operational rules come from the active handoff and policy.
