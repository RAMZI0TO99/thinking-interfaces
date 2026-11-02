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

The [Q4 supervisor and retained reader](docs/phase2/cho51_p3_q_qualification_20261029.md) retain their accepted
73-method scope. The [P1 preparation engine](docs/phase2/cho51_p3_preparation_engine_20261029.md) now has accepted Q qualification:
108 methods (including 35 new preparation methods), eight timestamp controls
and two native fault controls passed under fresh admission. Independent source
and actual-result reviews are adopted by Root; the new owned lifecycle closed.
Next is a concrete complete physical dependency recipe and a reviewed file-only
P caller, followed by separately admitted P/L/V/C. The engine's synthetic maps
do not establish dependency completeness. Q1 cause and cleanup remain unproved.

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
