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

The custody-resolution design and three local contract schemas have completed
independent source review. Root authored the six-file unit; separate analysis
and review used the owner's permitted Terra6.1/Sol6.1 subagents in sequence.
All48 acceptance scenarios remain unexecuted and80 predecessors are unchanged.
See the [design](docs/phase2/cho51_p3_local_custody_design_20261028.md) and
[review](docs/phase2/cho51_p3_local_custody_review_20261028.json).

The [subsequent implementation](docs/phase2/cho51_p3_boundary_implementation_20261028.md)
adds25 passing byte-verifier tests and a separately admitted bounded raw capture
(32events, truncated, UNRESOLVED). Independent source and actual-result reviews
remain separate. The [retained-reader successor](docs/phase2/cho51_p3_retained_chain_20261028.md)
adds45 passing local-reader/auxiliary-join tests and a separate six-file retained
read check. Its failed v2 predecessor remains consumed and preserved. The
[focused provider milestone](docs/phase2/cho51_p3_provider_qualification_20261028.md)
adds 73 passing v5 tests and four supported records decoded from a six-row capture.
V4's actual namespace refusals remain preserved. The source reviewer and actual
reviewer are distinct; Root adopts the exact result review locally. Two classic
payloads and Security-log access remain gaps. The
[custody intake milestone](docs/phase2/cho51_p3_custody_intake_20261028.md) adds
25 passing tests and a separately reviewed nine-artifact assessment. Root issued
an UNRESOLVED disposition after actual review; all 499 predecessors remain exact.
Next obtain the missing original technical host witness or review a proposed
boundary-contract change. Successor006 remains unadmitted.
Record consistency and template matching do not authenticate a historical host.
The original48-case matrix is not fully executed by these subset tests.

Bootstrap004 remains FAILED_UNRELEASED_CONSUMED; diagnostics005 remains
independently statically reviewed and deliberately launch-held. The 117 tests
and 34 controls remain unexecuted. All substantive resource, ownership and
cleanup protections continue to apply.

Historical coordination pages are preserved in the
[documentation archive](docs/history/project_focus_20261028/README.md).
They explain past events and do not impose current scheduling prerequisites.
