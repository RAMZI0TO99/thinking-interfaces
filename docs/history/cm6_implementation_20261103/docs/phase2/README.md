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

The [CM6 stable-cohort/current-census integration design](cho51_p3_cm6_cohort_design_20261103.md) is independently accepted with no findings. Eight files separate fixed Q360 qualification identities, full C876/38 census with explicit held additions, and frozen H836/36/320 fixture semantics. Full collection precedes projections; independently expected raw pins bind the versioned producer/verifier/terminal join. All 32 new scenarios remain unimplemented and unqualified. No methods or runtime admission were added; P stays disabled.

The [CM5 implementation](cho51_p3_cm5_implementation_20261103.md) and all predecessors remain frozen. Source remains 876 identities/38 modules/360 proposed selections with 516 outside the anchor; CM5's 40 new methods are unexecuted. CM6's conditional 2,568-event / 1,314,816-byte design does not change CM5's 2,368-event fixture target. Current-descriptor checks cannot prove cross-version held-debt conservation: every successor adoption must reconcile predecessor descriptor/census evidence and current source. Next is source-only implementation/review of expected-context and full current-collection contracts, with explicit held new-test accounting. Original producer/dispatcher/observer, effect/capture/custody, allocation and finite closeout/resource gates remain held.

The [bounded resolver](cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

[Current lossless representation and capacity decision](cho51_p3_lossless_state_design_20261101.md) records the accepted design, unchanged accounting and completed negative real-case feasibility. [Supplied-data codec qualification](cho51_p3_lossless_codec_implementation_20261101.md) records fresh Q384+100 acceptance. The [real-source scope design](cho51_p3_real_scope_design_20261101.md) selects a fixed non-resumable observation probe; its [supplied-byte implementation](cho51_p3_probe_implementation_20261101.md) is source-reviewed, but fresh Q remains refused at runtime deadlines. The [QD execution record](cho51_p3_qd_execution_20261102.md) records one admitted prefix run and overall17/16 allocation refusal. The [SC1 design](cho51_p3_startup_cost_design_20261102.md) is independently accepted, and its implementation is now independently source-reviewed. HB1 design and its supplied-data verifier/refusal/collection implementation are independently accepted for source only;120 new methods remain unexecuted. CM1 remains source-reviewed with 32 new unexecuted methods. CM2 supplied retained-data and callback adapters are independently source-reviewed, with 32 new methods unexecuted and a 764/32 roster / 248 selection. Conditional normal output is 1,000 events; complete recursive/failure/capture/runtime gates remain open. CM3 design remains accepted, and its eight-file supplied parser/join is now independently source-reviewed. The 32 new methods are unexecuted; the CM3 source snapshot is 796/34 with 280 selections, while historical parsing remains 764/248. No design scenario is qualified. CM4 supplied contracts are now independently source-reviewed with no findings, an explicit 836/36/320 roster and 40 new unexecuted methods. All 28 scenarios remain unqualified. CM5 design is independently accepted after CM5-D01 correction, with 16 boundary classes / 320 direct-method obligations and 32 unqualified scenarios. CM5 supplied producer/refusal/seal is now independently source-reviewed after CM5-S01/S02 correction, with 40 new unexecuted methods and a separate 876/38/360 source census. Its producer target remains frozen 836/36/320. CM6 stable-cohort/current-census design is now independently accepted, with Q360/C876/H836 identity separation and 32 new unqualified scenarios. Successor adoption must separately reconcile prior held-test debt. Next is source-only expected-context/full-collection implementation and review; runtime admission stays refused. Complete-Q timing/output feasibility remains NOT_ESTABLISHED. P stays disabled and full continuation remains infeasible. [Reconstruction obligations](cho51_p3_reconstruction_design_20261101.md) and [kernel qualification](cho51_p3_frontier_continuation_20261031.md) retain their original scope.

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
