# Phase II: current starting point

Updated 3 November 2026, Asia/Riyadh.

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

The [P2 dependency map and file-only caller](docs/phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](docs/phase2/cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [whole-operation effect/allocation and feasibility plan](docs/phase2/cho51_p3_whole_operation_design_20261103.md) is independently accepted for design only after WO-D01 bootstrap-path correction. Eight design files define ten operation stages, preserve16 effect boundaries and546 indexed bodies, and enumerate33 report reservations with ten memory-lifetime families. Source remains1062/49; Q360/S140 are fixed and disjoint; all702 held rows remain exact, including46 CM6S methods outside both cohorts. No method or implementation was added; P stays disabled.

The [CM6 S140 implementation](docs/phase2/cho51_p3_cm6_supplement_implementation_20261103.md) and all predecessors remain frozen. Complete-operation feasibility is NOT_ESTABLISHED and execution REFUSED_UNADMITTED. The acyclic B0 original trust/guard/observation root -> B1 bounded driver -> B2 scoped targets -> B3 full profile requires independent earlier evidence; B0/B1 remain unimplemented/unqualified and cannot be inferred or self-certified. All32 new,32 prior CM6 and24 S140 scenarios remain unqualified. Next is source-only B0/B1 basis and original provider/ingress/capture witness design with fixed-slot packing; all original effect/allocation/custody/capture/time/memory and46-method qualification obligations remain.

The [bounded resolver](docs/phase2/cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](docs/phase2/cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](docs/phase2/cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](docs/phase2/cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](docs/phase2/cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](docs/phase2/cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

## Decisions and scientific limits

- [Gate A acceptance](docs/phase2/gate_a_acceptance_20261012.md) is retrospective
  and limited to its exact amended criterion.
- [Adopted design choices](docs/phase2/cho_design_decisions_20261012.md) and
  [51-target amendment](docs/phase2/cho_51_target_amendment_adoption_20261013.md)
  govern the first tranche.
- Checkpoint/cohort provenance and overlap claims require their own evidence.
- [The scientific freeze](docs/phase2/scientific_freeze_draft.md) remains unsigned.
- Accepted final scientific cells remain 0/1020. Engineering work does not admit
  a scientific experiment or reset original spent attempts.

The [literature review](docs/where%20are%20we/LITERATURE_REVIEW.md) explains the
research lineage; the [progress report](docs/where%20are%20we/PROGRESS_REPORT.md)
separates completed work from pending claims.
The [Phase II index](docs/phase2/README.md) links the technical reports.

Dated reviews and [archived status pages](docs/history/project_focus_20261028/README.md)
retain their historical meaning. They do not impose superseded scheduling rules
on current work.
