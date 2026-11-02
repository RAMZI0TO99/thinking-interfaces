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

The [candidate-v2 migration and bounded inventory](docs/phase2/cho51_p3_candidate_inventory_20261031.md) is implemented and independently source-reviewed as LP8/LQ8/lplan5. Fresh Q4 accepted 384 methods and all required controls. Separately admitted P4 returned successfully in 104.14 seconds: 21,425 retained files, 893 native images, 4,847 edges, exact four-edit migration and 13,406 AST occurrences across 53 pages with zero syntax diagnostics. Independent P review accepted the physical, migration and bounded syntax inventory scope. The 25 mapped functions retain 117 expectations; no candidate IDs were collected and no candidate code ran. The inventory remains INCOMPLETE_REFUSED. Next is provisional source-level decision closure, followed by matching host capabilities, remaining qualification and final complete-plan acceptance before separate L admission. The 117 candidates, 34 V controls and scientific cells remain unexecuted. Earlier failures and the Q1 lost-original-receipt incident retain their explicit limits; documentation changes require fresh future coverage.

The [accepted v8 inventory](docs/phase2/cho51_p3_inventory_observation_20261029.md)
remains a 742-file current-byte observation with 19 passing tests. The 117
candidate tests and 34 successor controls remain unexecuted. Bootstrap004 stays
consumed, diagnostics005 held, custody UNRESOLVED and006 unadmitted. Scientific
cells remain0/1020. The new scoped policy replacement takes effect only through
implementation-specific adoption; the full-restart claim remains unchanged.

Source and actual reviewers are distinct; Root adopts exact reviewed records.
The v8 observation rechecked10 source inputs,732 runtime files and572 preserved
predecessors. New workloads require their own scope and admission. The original
48-case matrix is not completed by these subset tests.

Historical coordination pages are preserved in the
[documentation archive](docs/history/project_focus_20261028/README.md).
They explain past events and do not impose current scheduling prerequisites.
