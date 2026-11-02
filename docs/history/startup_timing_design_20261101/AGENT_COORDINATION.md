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

The [bounded resolver](docs/phase2/cho51_p3_bounded_resolver_20261031.md) retains accepted LP10/LQ10/lplan7 Q and file-only P2 evidence; the [supplied-data codec](docs/phase2/cho51_p3_lossless_codec_implementation_20261101.md) retains accepted LP13/LQ13/lplan10 Q384+100. The [fixed supplied-byte probe](docs/phase2/cho51_p3_probe_implementation_20261101.md) is implemented and independently source-reviewed as LP17/LQ17/lplan14, but fresh Q is NOT ACCEPTED. Six attempts are consumed. The latest passed 32 probe methods and three sharing checks and retained six exact provisional artifacts, then timed out at native-overflow; later controls and full final verification did not complete. Its owned cleanup is established. Earlier 8bf386d1 final caller custody and 6f9c898c final caller/outer/bootstrap custody remain UNKNOWN, as does prior 131bc595 outer/bootstrap custody. The 100 and 384 successor cohorts remain unadmitted. Next is a bounded startup-timing diagnosis and reviewed successor design; preserve all guards and require complete fresh Q before further integration. P stays disabled. No original-package-path custody, continued state or debt discharge is established. All 18,793 resolver rows, 13,406 inventory occurrences, 724 queues, 1,782 frontiers, 1,786 binding loads and 3,972 effects remain open. Complete continuation remains INFEASIBLE_UNDER_CURRENT_GUARDS: at least 31,002 rows against 24,000; conditional node/raw-byte findings retain their scope. G2 is INCOMPLETE_REFUSED; candidate117/V34 and science remain unexecuted. Old failures stay consumed; documentation does not refresh P custody or census.

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
