# Coordination within this project

Effective 28 October 2026, Asia/Riyadh. The owner has selected exclusive focus on
Thinking Interfaces. This page governs collaboration inside this project.

Root owns planning, scheduling, admission and the handoff. Active work does not
depend on another project, external chat response, shared lease or outside
decision. Do not message or poll other project chats unless the owner asks.

Read [the execution policy](docs/PROJECT_EXECUTION_POLICY.md) for local admission
and [the handoff](HANDOFF.md) for current engineering status.

## Roles and file ownership

- Root assigns one bounded task and explicit file ownership to each subagent.
- For current work, use Root plus one author or one independent reviewer at a
  time. Preserve other agents' changes and hand ownership over explicitly.
- Reviewers must not certify their own implementation. Source review and actual
  result review are separate; both stay inside this project.
- Routine documentation and static inspection need no compute window.

## Execution workflow

Root records the exact operation, fresh pins, applicable local resource limits,
unused output directory, local stop control and reviewed cleanup obligations.
The independently reviewed runner must match that contract. Review actual
caller return, child/Job closure and complete saved evidence before accepting a
result. An expected artifact or a successful metadata command is not proof of
an executed operation or physical cleanup.

Legacy scheduling and outside approval dependencies are retired. Frozen scripts
and receipts retain their bytes; replace incompatible dependencies in a new
successor instead of inventing old-format grants or editing historical outcomes.

## Current task boundary

The [local validation contract](docs/phase2/cho51_p3_local_validation_contract_20261029.md)
has independent design acceptance. It binds 117 candidate cases, 34 successor
controls and 26 qualification scenarios to separate qualification, preparation,
loader/collection, validation and closeout stages. The two retired shared-window
controls are explicitly replaced by local-window controls.

The [P2 dependency map and file-only caller](docs/phase2/cho51_p3_dependency_preparation_20261029.md) have accepted Q10 qualification (198 methods, eight UTC controls, two native fault controls and three sharing checks) and accepted P10 physical preparation: 20,406 files, 888 native images and 4,843 dependency edges. The 105.32-second run completed full final input verification and owned cleanup. Earlier failures and unknown cleanup remain frozen; physical preparation does not qualify loader/ABI behavior.

The [native-memory bootstrap and refreshed preparation](docs/phase2/cho51_p3_native_memory_bootstrap_20261031.md) are implemented and source-reviewed. Fresh native-bootstrap Q2 accepted 368 methods and all required controls, including two actual P-bootstrap cases. Separately admitted P2 returned successfully in 116.96 seconds, reporting 21,115 files, 893 native images and 4,847 dependency edges, full final verification and owned cleanup. P physical preparation is independently accepted for this operation.

The [CM5 supplied producer/refusal/seal implementation](docs/phase2/cho51_p3_cm5_implementation_20261103.md) is independently source-reviewed after CM5-S01/S02 correction. The six-file package implements bounded primitive commands, sticky refusal/settlement, post-footer accounting and immutable supplied seals. Current source is 876 identities/38 modules with 360 proposed selections and 516 outside execution; 40 new methods remain unexecuted. All 32 scenarios remain unqualified. No runtime admission occurred; P stays disabled.

The [accepted CM5 design](docs/phase2/cho51_p3_cm5_producer_design_20261103.md), CM4 and all predecessors remain frozen. The producer still targets CM4's 836/36/320 roster, with conditional 2,368 records / 1,212,416 bytes and 2,367 guarded attempts. Expanded-census mapping is only hypothetical: 2,568 records / 1,314,816 bytes and 2,567 attempts; no expanded collector/producer/verifier exists. The 16-class failure/effect map and all original obligations remain open. Next is source-only design/review of a stable qualification cohort and current-roster collection/producer/verifier integration. Original dispatcher/observer, capture/custody, allocation and finite closeout/resource gates remain held.

The [bounded resolver](docs/phase2/cho51_p3_bounded_resolver_20261031.md) and [supplied-data codec](docs/phase2/cho51_p3_lossless_codec_implementation_20261101.md) retain their accepted scoped evidence. The [fixed probe](docs/phase2/cho51_p3_probe_implementation_20261101.md) remains source-reviewed but fresh Q is NOT ACCEPTED: six consumed attempts, latest32 method and three sharing passes followed by a later control deadline and incomplete final verification. Latest owned cleanup is established;8bf386d1 final caller,6f9c898c final caller/outer/bootstrap and131bc595 outer/bootstrap custody remain UNKNOWN. Historical [QD a1f12701](docs/phase2/cho51_p3_qd_execution_20261102.md) retains59/42 timing records,37.7609334s prefix,45.4523028s external return, final verification and owned closure, but overall INCOMPLETE_REFUSED for17/16 closeout accounting. No repair, retry or second QD is inferred. [SC1](docs/phase2/cho51_p3_sc1_implementation_20261102.md) and the [HB1 design](docs/phase2/cho51_p3_host_binding_design_20261102.md) remain frozen source/design predecessors;54 SC1 and10 QD methods,24 HB/40 SC/36 diagnostic scenarios remain unqualified. Complete-Q timing/output feasibility is NOT_ESTABLISHED.

Full Q probe32/100/384 and every control remain held; all guards remain. No original-package-path custody, continuation or debt discharge is established. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete continuation is INFEASIBLE_UNDER_CURRENT_GUARDS: at least31,002 rows against24,000; conditional node/raw-byte findings retain scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain 0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

Source and actual reviewers are distinct; Root adopts exact reviewed records.
The v8 observation rechecked10 source inputs,732 runtime files and572 preserved
predecessors. New workloads require their own scope and admission. The original
48-case matrix is not completed by these subset tests.

Historical coordination pages are preserved in the
[documentation archive](docs/history/project_focus_20261028/README.md).
They explain past events and do not impose current scheduling prerequisites.
