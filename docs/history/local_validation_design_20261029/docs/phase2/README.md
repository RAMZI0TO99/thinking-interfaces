# Phase II documentation index

Current status: 29 October 2026, Asia/Riyadh.

Read the [current handoff](../../HANDOFF.md),
[project plan](../where%20are%20we/PROJECT_PLAN.md) and
[project execution policy](../PROJECT_EXECUTION_POLICY.md) first.
Root manages scheduling and admission within this project.

## Current engineering work

The [local log search](cho51_p3_sysmon_recovery_20261029.md) recovered
the original command transcript. All six Sysmon queries were denied access;
16 collector tests passed. This does not establish missing-record absence or
historical host identity.

The separately reviewed and adopted
[inventory-only contract](cho51_p3_inventory_contract_20261029.md)
now has [accepted execution evidence](cho51_p3_inventory_observation_20261029.md):
19 tests passed and a separate operation retained 742 declared source/runtime
files (37,411,436 bytes). This establishes those bytes during the observation,
not installation completeness, loaded-code authentication or old cleanup.

Next design and review the project-local nonnumerical validation operation:
its full dependency roster, runtime-loading assumptions, side effects,
input/output ownership and guards. Preparation and the 117 candidate tests /
34 controls need separate fresh admissions and actual-result review.
Bootstrap004 remains consumed, diagnostics005 held, the existing custody
disposition UNRESOLVED and006 unadmitted. Scientific cells remain0/1020.

| Technical record | What it documents |
| --- | --- |
| [Restoration qualification](cho51_provenance_restore_qualification_20261025.md) | 65 focused tests and selected-source engineering restoration |
| [Parent/worker qualification](cho51_provenance_numerical_worker_qualification_20261025.md) | 63 unit cases,27 controls and one synthetic episode |
| [Metadata boundary qualification](cho51_canonical_boundary_qualification_20261025.md) | 133 distinct cases and accepted aggregation |
| [P3 adapter design](cho51_p3_adapter_design_20261027.md) | Reviewed interface design |
| [P3 telemetry design](cho51_p3_telemetry_design_20261027.md) | Supplied timing and telemetry contract |
| [Contract implementation](cho51_p3_contracts_implementation_20261027.md) | Static source checkpoint and historical failure |
| [Diagnostics005 record](cho51_p3_custody_diagnostics_20261028.md) | Bounded diagnostics and deliberate launch hold |
| [Local custody design](cho51_p3_local_custody_design_20261028.md) and [independent review](cho51_p3_local_custody_review_20261028.json) | Three schemas and48 acceptance scenarios; design acceptance precedes the separately scoped implementation below |
| [P3 source archive](../../evidence/cho51-p3-source-checkpoint-20261028/README.md) | Exact source and historical receipts |
| [Boundary implementation](cho51_p3_boundary_implementation_20261028.md) | 25 passing subset tests; bounded truncated raw diagnostic; positive boundary still unqualified |
| [Retained reader and auxiliary joins](cho51_p3_retained_chain_20261028.md) | 45 passing tests; six retained artifact reads; failed v2 attempt preserved; local bytes and record consistency only |
| [Focused provider capture and decoding](cho51_p3_provider_qualification_20261028.md) | 73 passing v5 tests; four supported records decoded from six saved rows; v4 namespace defect preserved; historical association remains unresolved |
| [Custody evidence intake](cho51_p3_custody_intake_20261028.md) | 25 passing v6 tests; nine retained artifacts; exact reviewed UNRESOLVED disposition; no positive authority |
| [Local log recovery](cho51_p3_sysmon_recovery_20261029.md) |16 passing tests; original transcript recovered; six protected Sysmon reads denied |
| [Inventory contract](cho51_p3_inventory_contract_20261029.md) and [actual observation](cho51_p3_inventory_observation_20261029.md) |19 passing tests;742 declared files retained; scoped current bytes only |

These dated reports retain their original bytes and observations. Their old
scheduling requirements are superseded by the active project execution policy.
They are technical evidence, not current run authorization.

## Scientific decisions

- [Adopted design choices](cho_design_decisions_20261012.md)
- [Gate A retrospective acceptance](gate_a_acceptance_20261012.md)
- [51-target amendment](cho_51_target_amendment_adoption_20261013.md)
- [Decision register](decision_register.md), read alongside the later adopted decisions
- [Unsigned scientific freeze](scientific_freeze_draft.md)
- [Literature and previous studies](../where%20are%20we/LITERATURE_REVIEW.md)

Targets02–52/source cohort52 and zero accepted final scientific cells out of1,020
remain unchanged. No workflow change signs the scientific freeze.

The previous milestone narrative is preserved exactly in
[the documentation history](../history/project_focus_20261028/README.md).
The append-only deviation log and evidence packets remain unchanged.
