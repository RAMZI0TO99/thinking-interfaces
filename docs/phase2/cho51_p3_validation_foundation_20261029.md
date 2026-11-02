# Local validation design and preparation foundation

29 October 2026, Asia/Riyadh. Engineering only. This milestone separates
accepted design, implemented source and execution evidence.

## Design acceptance

The [local validation contract](cho51_p3_local_validation_contract_20261029.md)
has independent **ACCEPTED_DESIGN** review and
[Root design acceptance](../../runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-acceptance.json).
The [review](../../runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json)
is 5,065 bytes, SHA256
`65526bad7ee6599c403411502ff0e0296b69c3a688daf66a5bb2aa402f017e4b`.
It pins six design documents and selected original evidence. All 636 preserved
inputs matched during that review.

The design specifies 117 candidate cases across 25 functions: 39 mapping and
78 telemetry cases. It maps 34 successor controls to their historical purposes;
two shared-window controls are explicitly replaced with local-window controls.
It separately specifies 26 qualification scenarios. These are expected rosters,
not collected node IDs or passing tests.

Three findings were resolved before acceptance: the narrow relationship to the
frozen execution policy, a single caller clock covering all work and cleanup,
and the exact Git argument vectors used by source capture. The scoped policy
replacement requires implementation-specific adoption. Design acceptance creates
no admission and does not change the historical full-restart predicate.

## Implementation boundary

The next bounded implementation is the
[preparation foundation](../../tools/local_validation/v1/README.md): stdlib-only
record validation, bounded supplied snapshots, source/census comparison and
streaming hashes. It operates on supplied data and streams. It does not enumerate
the installed environment, retain native handles, authenticate those supplied
identities, construct a complete dependency closure or launch a process.

The implementation includes 31 adversarial unittest methods, counted by text
inspection and not executed. Its independent
[source review](../../runs/coordination/cho51_p3_validation_foundation_20261029_v1/source-review.json)
is **ACCEPTED_SOURCE_FOUNDATION_ONLY**, with no unresolved findings. The receipt
is 3,235 bytes, SHA256
`a27dc254e552cdb422beb4ffbb43942801e2c735fb23d8d643a822ec64db55c5`.
Root's [static qualification](../../runs/coordination/cho51_p3_validation_foundation_20261029_v1/root-source-qualification.json)
records the accepted scope and unchanged predecessors.

No foundation imports, compilation or collection have been executed. There is
no operational adoption, Q admission, P manifest, loader observation or new
positive runtime result in this phase. The JSON byte/node caps can refuse a
supplied representation before the maximum file-count ceiling is reached.
Streams/checkpoints are trusted supplied capabilities; this core has no
independent watchdog and does not open project inputs.

## Remaining execution work

1. Implement and independently review the Q supervisor and native retained
   reader, including the complete caller budget, parent resource coverage,
   atomic Job assignment and authenticated child-result transfer.
2. Qualify that implementation under a fresh Q admission and obtain independent
   actual-result review. Qualification tests remain separate from117/34.
3. Admit P to observe the complete bounded dependency recipe, then review its
   physical coverage and accepted pins. Seeds alone are insufficient.
4. Admit L for confined initialization, installed guards and exact117 collection.
   Missing native-loader coverage, stale aliases or unexpected effects refuse.
5. Admit V for34 successor controls and117 unchanged cases with351 phase reports
   and matching physical JUnit, then admit C for complete external closeout.

Each stage has a new identity, current source/runtime pins, separate admission,
complete custody/caller evidence and a different actual-result reviewer. No old
launcher, consumed attempt or inventory admission is reusable.

## Preserved evidence and documentation

Bootstrap004 remains failed, unreleased and consumed; diagnostics005 remains
held. The v6 historical disposition stays UNRESOLVED,006 is unadmitted and the
original48-case custody matrix remains incomplete. The117 candidate tests and34
successor controls remain unexecuted. Scientific cells remain0/1020 and the final
freeze unsigned. No raw data, weights, models or historical receipt was changed.

The twelve preceding active documents are retained in the
[documentation snapshot](../history/local_validation_design_20261029/ARCHIVE_INDEX.md).
The current [handoff](../../HANDOFF.md) and
[project overview](../where%20are%20we/README.md) distinguish this static milestone
from earlier executed observations. No commit or push is part of this step.

