# Present-byte inventory contract, v8

29 October 2026, Asia/Riyadh. Author: project Root. This is a scoped operational
addendum under the [project execution policy](../PROJECT_EXECUTION_POLICY.md),
not a scientific amendment. Independent source acceptance and explicit Root
adoption are required before any operation under it.

## Scope and reason

The [local log search](cho51_p3_sysmon_recovery_20261029.md) recovered the original
command transcript but encountered access denial for all six Sysmon queries.
The [v1 custody contract](cho51_p3_local_custody_design_20261028.md) remains the
contract for claiming exclusion of the old process domain after a full restart.
No such claim has been established.

This addendum permits a different, narrower operation: observe a closed list of
current source/runtime files under retained handles, with a newly owned contained
probe, and publish a parent-owned byte inventory. Old process extinction is not
an input to that observation. This explicitly replaces the restart prerequisite
for this inventory operation only; it does not weaken the full-restart predicate
or issue a positive current-boundary disposition. It is not bootstrap006 and
does not run diagnostics005. Frozen policy and evidence bytes remain intact.

The owner authorized engineering recovery and asked Root to find the logs or
solve the blocker. Root owns scheduling and admission. This narrowly scoped
alternative needs independent technical review, not a new outside approval.

## Claim and trust assumptions

The only accepted claim is that the exact declared files had the reported
identities, lengths and SHA256 bytes during the retained-handle interval.
Inventory completeness means completeness of the declared roster, not every
installed file, every loaded image, an authenticated runtime distribution or
the state of the entire machine. The contained probe's zero exit demonstrates
its own observed lifecycle; it is not the source of the byte inventory.

The ordinary local Windows kernel, filesystem and observer runtime are the
trust base. No claim is made against a compromised kernel, privileged attacker,
injected observer, preexisting writable mapping or arbitrary malicious code
running as the same account. A random UUID is not a security boundary.
These limitations must be explicit in the payload and independent acceptance.

An old ordinary Win32 writer incompatible with the retained sharing mode causes
refusal. New writes/deletes through conflicting opens fail while handles are
held. Directory retention prevents relevant replacement/rename, but does not
freeze membership. Membership changes cannot be hidden behind a completeness
claim: use an exact closed roster and recheck any enumerated roster at both ends.
This does not prove that the same bytes remain present after release; each later
operation must freshly retain and check its own inputs.

## Required controls

1. Closed source/runtime maps, exact policy/addendum/review pins and a new finite
   admission. At most1024 inventory files,64MiB total and16MiB per file. Restrict
   paths to the admitted local project/runtime roots; refuse reparse traversal,
   aliases, hardlinks, unsupported filesystem types and ambiguous identities.
2. Retain read handles denying write/delete sharing throughout hashing, the
   probe, final identity/byte verification and publication. Retain and verify
   ancestor identities. Read bytes and identity from the same handle.
3. Create a new UUID attempt atomically; all existing or unknown namespaces
   refuse. Parent alone creates inventory outputs with create-new access and
   retained handles denying other writers/deletion, checks final identity and
   containment, flushes and verifies read-back through the original handle.
   Retain outputs and their namespace through publication. Refuse collisions,
   identity changes, partial writes or unverifiable read-back.
4. The inventory probe writes no artifact and supplies no byte claims. Start it
   suspended with atomic membership in an unnamed noninherited kill-on-close
   Job; verify limits and membership before resume. Keep original process,
   thread and Job handles. Only owned cleanup is permitted; uncertain creation,
   termination, exit, empty Job or closure is sticky failure. No PID reacquisition.
5. Fresh resource readings, strict local stop, hard process/Job memory caps,
   finite admission/work/child/whole deadlines and cleanup reserve. Failure
   consumes the attempt and stops owned work; no silent retry or unrelated kills.
6. Independent whole-source review, separately admitted adversarial tests and
   actual inventory, genuine external caller-return evidence, a different actual
   reviewer and Root adoption of the exact outcome. Tests do not become real
   inventory acceptance; a provisional receipt never accepts itself.

## Resource envelope and effects

Root defines a new lightweight inventory envelope:4GiB startup and active
available RAM,20GiB free disk,512MiB process/768MiB Job commit,45s child,75s work,
90s whole runner,1MiB result, one library worker and hidden GPUs. This is justified
by the64MiB input cap and the absence of model/data loading. It is not an extension
of the old available-memory exception or a change to006's proposed limits.
Available-resource samples trigger bounded refusal; they do not reserve the
machine against pressure from other applications.

Allowed effects are the new attempt and bounded evidence files, plus a new
owned probe/test process. Test fixtures are confined to the fresh admitted
attempt. No Event Log access, privilege change, security/audit configuration,
restart, native compilation, model, training, numerical case or scientific cell.

## State after acceptance

Historical004 custody/release/retry remain false. The v6 current-boundary
disposition remains UNRESOLVED with null current_boundary;005 remains launch-held.
All boundary, launch and scientific authority fields in inventory records are
false. Inventory acceptance may support source preparation and review for a
separate operation, but does not itself admit native preparation or117/34.

Any later engineering execution needs its own reviewed effect/input/output
contract, fresh retained scope, resource envelope and local admission. It must
explicitly decide which evidence it requires; it cannot inherit host extinction
or a runtime guarantee that this limited observation does not establish.
