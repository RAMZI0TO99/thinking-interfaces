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

Source and actual reviewers are distinct; Root adopts exact reviewed records.
The v8 observation rechecked10 source inputs,732 runtime files and572 preserved
predecessors. New workloads require their own scope and admission. The original
48-case matrix is not completed by these subset tests.

Historical coordination pages are preserved in the
[documentation archive](docs/history/project_focus_20261028/README.md).
They explain past events and do not impose current scheduling prerequisites.
