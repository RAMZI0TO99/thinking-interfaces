# Phase II: current starting point

Updated 29 October 2026, Asia/Riyadh.

Phase II asks how adaptation methods compare under a fixed, small target support
budget, with authentic inputs, controlled selection, immutable query state and
subject-level statistical analysis. The current first tranche is Cho2017:
targets02–52, four methods and five seeds, for1,020 planned cells.

Start with the [handoff](HANDOFF.md),
[project plan](docs/where%20are%20we/PROJECT_PLAN.md) and
[local execution policy](docs/PROJECT_EXECUTION_POLICY.md).
Implementation and reviews are organized entirely within this project.

## Where implementation stands

The restoration factory and parent/numerical-worker composition have bounded
engineering evidence. The read-only canonical metadata boundary is qualified.
P3 design, metadata/profile mapping and supplied telemetry sources are implemented
and independently statically reviewed;117 candidate tests and34 controls remain
unexecuted.

The [local validation contract](docs/phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](docs/phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Next is the separately reviewed and admitted L loader and collection stage. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

## Decisions and scientific limits

- [Gate A acceptance](docs/phase2/gate_a_acceptance_20261012.md) is retrospective
  and limited to its exact amended criterion.
- [Adopted design choices](docs/phase2/cho_design_decisions_20261012.md) and
  [51-target amendment](docs/phase2/cho_51_target_amendment_adoption_20261013.md)
  govern the first tranche.
- Checkpoint/cohort provenance and overlap claims require their own evidence.
- [The scientific freeze](docs/phase2/scientific_freeze_draft.md) remains unsigned.
- Accepted final scientific cells remain0/1020. Engineering work does not admit
  a scientific experiment or reset original spent attempts.

The [literature review](docs/where%20are%20we/LITERATURE_REVIEW.md) explains the
research lineage; the [progress report](docs/where%20are%20we/PROGRESS_REPORT.md)
separates completed work from pending claims.
The [Phase II index](docs/phase2/README.md) links the technical reports.

Dated reviews and [archived status pages](docs/history/project_focus_20261028/README.md)
retain their historical meaning. They do not impose superseded scheduling rules
on current work.
