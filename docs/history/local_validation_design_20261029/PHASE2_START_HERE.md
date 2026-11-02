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
