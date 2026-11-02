# Retained current-byte inventory

29 October 2026, Asia/Riyadh. Engineering-only result.

The [log search](cho51_p3_sysmon_recovery_20261029.md) found the original local
command transcript, but Windows denied every Sysmon query. Root therefore
prepared a [separate inventory-only contract](cho51_p3_inventory_contract_20261029.md),
independently reviewed and explicitly adopted before two fresh admissions.
It permits current byte observation without asserting extinction of the old
process domain. The historical custody disposition remains unchanged.

## What ran

| Operation | Attempt | Actual tool result |
| --- | --- | --- |
|19 adversarial tests |4c50aa8e-d819-459a-9b48-b35cfb2711b0 |304733, exit0,6.1163091s |
|Separate retained inventory |00fd3db3-2bea-4ddc-9f25-7a0b93155662 |e9f0b1, exit0,5.6009869s |

All19 tests passed with zero failures, errors or skips. They cover existing/new
writer conflicts, native identity and descriptor failure cleanup, hardlinks,
output collisions/write/delete exclusion/read-back, size/count limits, explicit
roster semantics, cooperative stop checks, verified bootstrap bytes and the
frozen deadline consumer. They are focused controls, not the original48-case
matrix or the pending117 candidate tests/34 controls.

The separate actual operation retained **742 files:10 source inputs and732
declared base-runtime files, totaling37,411,436 bytes**. Native identities and
hashes were checked through original handles. The parent held files against
ordinary incompatible writes/deletion, ran one contained no-output probe, then
created and read back its own inventory under retained output handles.
Both new owned processes exited normally; Jobs closed empty and original
process/thread handles closed. No stream-EOF claim is made because this path
does not use a result stream. External caller-return evidence remains separate.

The [source review](../../runs/coordination/cho51_p3_inventory_observation_20261029_v8/source-review.json)
resolved bootstrap, descriptor ownership, checkpoint, canonical deadline,
test-report and adoption-join findings before sealing. The distinct
[actual review](../../runs/coordination/cho51_p3_inventory_observation_20261029_v8/actual-review.json)
accepted the limited observation. Root rechecked its artifact pins, all10
source/732 runtime pins and572 preserved predecessors before
[adopting the result](../../runs/coordination/cho51_p3_inventory_observation_20261029_v8/root-qualification.json).

## Meaning and next step

The accepted claim is the exact declared roster's identities and bytes during
the retained-handle window. It does not certify the complete installation,
loaded images, historical host, restart, global machine quiet or old cleanup.
Ordinary local Windows/filesystem/observer assumptions and the exclusions for
privileged compromise, injected observer and preexisting writable mappings are
explicit in the contract. A later operation must freshly retain its own inputs.

This provides a current engineering inventory that can support preparation of
a separate project-local validation contract. Next design and source-review
that operation's full dependency roster, side effects, input/output ownership,
runtime loading assumptions and guards; then obtain fresh admission and actual
review for preparation and117/34. The inventory itself does not admit those steps.

Bootstrap004 remains FAILED_UNRELEASED_CONSUMED;005 stays launch-held. The v6
UNRESOLVED disposition is not replaced,006 is unadmitted, scientific cells are
0/1020 and the final freeze is unsigned. No commit or push occurred.
