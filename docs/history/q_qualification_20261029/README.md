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

The [preparation foundation](docs/phase2/cho51_p3_validation_foundation_20261029.md) is
implemented and independently source-reviewed: strict records, bounded supplied
dependency snapshots, streaming hashes and drift checks;31 tests are unexecuted. This
source step does not provide native custody, complete dependency coverage or an
operational grant. The next runnable component is a separately reviewed Q
supervisor with fresh source/runtime pins, admission and actual-result review.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain0/1020. The new scoped policy replacement takes effect only through
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
