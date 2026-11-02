# Phase II documentation index

Current status: 1 November 2026, Asia/Riyadh.

Read the [current handoff](../../HANDOFF.md),
[project plan](../where%20are%20we/PROJECT_PLAN.md) and
[project execution policy](../PROJECT_EXECUTION_POLICY.md) first.
Root manages scheduling and admission within this project.

## Current engineering work

The [local validation contract](cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [bounded resolver](cho51_p3_bounded_resolver_20261031.md) retains accepted LP10/LQ10/lplan7 Q and file-only P2 evidence: 21,777 files and 18,793 resolver rows. The [supplied-state kernel](cho51_p3_frontier_continuation_20261031.md) retains accepted LP11/LQ11/lplan8 Q384+72 with all required controls; operational P refuses. The [lossless state representation and capacity decision](cho51_p3_lossless_state_design_20261101.md) has independent design-only acceptance. Exact payload storage and full-frame transport preserve expanded-state accounting. The complete real resolver continuation remains INFEASIBLE_UNDER_CURRENT_GUARDS: its first successor needs at least 31,002 rows against the unchanged 24,000-row cap. The 28,892-node combined-inventory and raw-bundle byte findings are explicitly conditional. Next is implementation and review of the supplied-data-only codec, replay/accounting verifier and refusal path, followed by fresh Q; P stays disabled. Real complete continuation needs an explicit later contract/scope decision, not another encoding workaround. No guard or accounting change is adopted. All historical/frontier/binding/effect obligations remain open, including 724 queued contexts and 1,782 import-frontier records; G2 is INCOMPLETE_REFUSED. The 117 candidates, 34 V controls and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

[Current lossless representation and capacity decision](cho51_p3_lossless_state_design_20261101.md) records the accepted design, unchanged accounting and completed negative real-case feasibility. The next implementation is a supplied-data verifier under fresh Q; P remains disabled. [Reconstruction obligations](cho51_p3_reconstruction_design_20261101.md) and [kernel qualification](cho51_p3_frontier_continuation_20261031.md) retain their original scope.

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
| [Local validation contract](cho51_p3_local_validation_contract_20261029.md) and [foundation milestone](cho51_p3_validation_foundation_20261029.md) | Independently accepted design and supplied-data implementation; static-only at those milestones; foundation methods subsequently passed in Q4 |
| [Q4 qualification](cho51_p3_q_qualification_20261029.md) |73 methods,eight timestamp controls and two native fault controls passed; scoped owned lifecycle closed; P dependency closure remains separate |
| [P1 preparation-engine qualification](cho51_p3_preparation_engine_20261029.md) |108 methods including35 new,eight timestamp controls and two fault controls passed; complete physical recipe and actual P remain separate |
| [P2 dependency map and file-only caller](cho51_p3_dependency_preparation_20261029.md) | Q10 accepted 198 methods and scoped controls; P10 accepted 20,406-file physical preparation with complete final verification and owned closure; L/V/C remain separate |
| [L observer and collection design](cho51_p3_loader_design_20261029.md) and [independent review](../../runs/coordination/cho51_p3_loader_design_20261029_v1/design-review-revision1.json) | Five documents accepted as design; 40 unexecuted qualification scenarios; implementation, fresh Q/P and L admission remain separate |
| [L implementation checkpoint](cho51_p3_loader_implementation_20261031.md) | Source review and Q2 accepted: 356 methods, five native cases and scoped controls; P2 startup failed, physical preparation unaccepted; complete plan and L remain separate |
| [Startup diagnostic checkpoint](cho51_p3_startup_diagnostic_implementation_20261031.md) | SQ3 accepted 124 methods and required controls; separate D2 observation accepted with final verification and owned cleanup; later native-memory successor recorded below |
| [Native-memory bootstrap and fresh preparation](cho51_p3_native_memory_bootstrap_20261031.md) | LP4/LQ4 source-reviewed; fresh Q2 accepted 368 methods and required controls; P2 returned 21,115 files, 893 images and 4,847 edges with final verification and owned cleanup; physical preparation accepted; finite L plan incomplete |
| [Finite L plan and Lhost compatibility](cho51_p3_finite_l_design_20261031.md) | Eight-file revision1 design independently accepted; two static syntax defects, explicit candidate migration and 34 new unexecuted qualification scenarios; complete materialized plan and execution remain pending |

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
