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

The [local log search](docs/phase2/cho51_p3_sysmon_recovery_20261029.md) recovered
the original command transcript. All six Sysmon queries were denied access;
16 collector tests passed. This does not establish missing-record absence or
historical host identity.

The separately reviewed and adopted
[inventory-only contract](docs/phase2/cho51_p3_inventory_contract_20261029.md)
now has [accepted execution evidence](docs/phase2/cho51_p3_inventory_observation_20261029.md):
19 tests passed and a separate operation retained 742 declared source/runtime
files (37,411,436 bytes). This establishes those bytes during the observation,
not installation completeness, loaded-code authentication or old cleanup.

Next design and review the project-local nonnumerical validation operation:
its full dependency roster, runtime-loading assumptions, side effects,
input/output ownership and guards. Preparation and the 117 candidate tests /
34 controls need separate fresh admissions and actual-result review.
Bootstrap004 remains consumed, diagnostics005 held, the existing custody
disposition UNRESOLVED and006 unadmitted. Scientific cells remain0/1020.

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
