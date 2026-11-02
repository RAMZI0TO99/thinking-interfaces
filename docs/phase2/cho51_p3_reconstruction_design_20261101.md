# Real-source producer design and capacity decision

1 November 2026, Asia/Riyadh. Engineering only; no runtime operation in this step.

The five-file [reconstruction and reconciliation design](cho51_p3_reconstruction_v1/README.md)
specifies fresh retained input handling, deterministic source reconstruction,
exhaustive historical obligation joins, bounded publication/refusal and 24 planned
qualification scenarios mapped to FP01-FP12. The
[independent design review](../../runs/coordination/cho51_p3_reconstruction_design_20261101_v1/design-review-v1.json)
and [Root acceptance](../../runs/coordination/cho51_p3_reconstruction_design_20261101_v1/root-design-acceptance.json)
accept design only. No producer, new Q/P consumer or representation change is
implemented or admitted by these records.

## Static finding that changes the next step

The complete retained resolver graph cannot make a first continuation in lplan8
under the current row accounting. Its 15,501 origin/node rows alone count at least
twice across the first two retained snapshots: **31,002 rows exceeds 24,000**.
Seeds, edges, obligations and context/history rows only add to that lower bound.
This follows from the frozen capacity code and retained counts; it is not a
failed Q/P attempt or a measurement of initial snapshot byte fit.

The [file/JSON observation](../../runs/coordination/cho51_p3_reconstruction_design_20261101_v1/static-capacity-observation.json)
also joins every `(module, source SHA256, AST field path)` occurrence in 74 resolver
pages and 53 candidate-inventory pages. There is no overlap: 15,486 plus 13,406 gives
**28,892 distinct historical node tuples**. If both inventories were combined in
one initial kernel graph, nodes alone would exceed the row cap. These were
separate historical scopes; the comparison neither invalidates their accepted
observations nor asserts a current transitive source census.

All 136 review input files match their recorded pins. The independent reviewer
rechecked those pins, 127 ordered page layouts and tuples, and all 7,197 preserved
predecessor files. No source AST, import, compiler, test or native observation ran.
Current bytes matching old hashes do not refresh released P handles/custody.

## What the design preserves

Every old row keeps its index/page/row identity and complete payload, including
724 queued contexts, 1,782 import-frontier rows and embedded 1,786 unresolved binding
loads and 3,972 effects. The five-source inventory has a separate exhaustive join.
Equal byte observations never become effect, host or historical-custody approval.
An old immediate import site cannot invent a root requester; missing or ambiguous
ancestry remains unresolved. Native/missing origins cannot become empty source
templates. Export/member state must be reconstructed, not guessed from the queue.

The design distinguishes a complete non-resumable reconciliation report, a valid
checkpoint and bounded failure evidence. Partial output, capacity refusal or a
digest-only summary cannot masquerade as a complete checkpoint. All source,
runtime, process/Job, memory, time, disk, stop, final-verification, cleanup and
consumed-attempt guards remain effective. No numeric or accounting change is
adopted. LP11 operational P still refuses; its Q-only aggregate is not a P grant.

## Next implementation gate

Next is a lossless state-representation design and capacity feasibility decision
before producer/P implementation. It must preserve all payloads and bound the
whole history, explicitly compare its accounting to the current contract, and
receive independent review. This step adopts no deduplication or relaxation of
history accounting. A proposed contract change must be stated and resolved in
scope before implementation; no known-infeasible full P is admitted to repeat
the static failure. The design does not promise that an alternative will fit.

After feasibility and contract acceptance: implement and review new producer and
matching Q/P consumers; qualify all inherited 456 methods plus mapped producer
tests under fresh Q and all required controls; review current physical coverage;
separately admit file-only P and independently review its actual results. Then
complete G2 source decisions and matching Lhost capabilities before complete-plan
acceptance and separately admitted L. These remain pending, not completed steps.

The [archive](../history/reconstruction_design_20261101/manifest.json) preserves 12
pre-step active pages. The execution policy, frozen sources and old receipts are
unchanged. The 117 candidates and 34 V controls remain unexecuted; science remains
0/1020 and final freeze unsigned. Bootstrap004 is consumed, diagnostics005 held,
custody UNRESOLVED and 006 unadmitted. No Git, commit or push occurred.
