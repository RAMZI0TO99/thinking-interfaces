# Lossless representation design and capacity feasibility

1 November 2026, Asia/Riyadh. Engineering design only.

The five-file [lossless state design](cho51_p3_lossless_state_v1/README.md)
specifies exact-byte transport, complete retained frames, canonical snapshot
reconstruction, deterministic replay and unchanged capacity/refusal accounting.
Its [independent review](../../runs/coordination/cho51_p3_lossless_state_design_20261101_v1/design-review-v1.json)
and [Root acceptance](../../runs/coordination/cho51_p3_lossless_state_design_20261101_v1/root-design-acceptance.json)
accept design only. No codec, producer, Q/P successor or runtime operation was
implemented or executed in this step.

## Representation and preservation

A bounded manifest refers to one canonical graph, complete ordered frames and
exact historical index/page assets. Deterministic 1 MiB byte chunks store those
assets without compression or recursive references. Every supplied payload must
be available inside the bundle; every original page/row ordinal remains distinct.
Sharing identical physical bytes never reduces logical occurrence or history
charges. The proposed verifier derives multiplicity, reconstructs every exact
prefix, checks intermediate transitions and preserves the frozen kernel's
structural, canonical-byte, worklist and live-guard predicates.

Its result can verify a supplied state or refuse. Neither result establishes
real-source coverage, native custody, G2, a safe effect or launch authority.
Complete reconstruction/reconciliation and matching qualified host capabilities
remain required for any later real execution. The 28 planned LS scenarios are
unimplemented and unexecuted; they extend the existing obligations.

## Completed feasibility decision

**Full real-data continuation is INFEASIBLE_UNDER_CURRENT_GUARDS.**
The first successor of the complete retained resolver graph requires at least
31,002 counted rows against the unchanged 24,000-row cap. That lower bound is
independent of physical representation. A smaller file, shared graph or single
transition cannot reduce the required historical multiplicity.

The [static case record](../../runs/coordination/cho51_p3_lossless_state_design_20261101_v1/capacity-cases.json)
also distinguishes conditional bounds: combining both historical inventories
would start with 28,892 distinct node rows, while copying all their exact raw
bytes into this uncompressed transport requires at least 20,370,470 bytes before
metadata, exceeding one 16 MiB state-output allocation. All 129 raw index/page
contents have distinct hashes, independently checked; byte sharing removes none.
These are conditional layout/state conclusions, not canonical-snapshot byte
measurements or a claim that every possible representation has that physical size.

The 136 retained input pins were rechecked against the prior independently
reviewed occurrence analysis. The independent reviewer also checked the exact
capacity arithmetic and all 7,231 preservation entries. No source AST, codec,
compression, replay, native process, tests or real-source reconstruction ran.
The small 17-row arithmetic example is illustrative; it is not a passing fixture
or evidence of runtime/canonical-byte feasibility.

## Next bounded implementation

Implement and independently review a supplied-data-only codec and replay/accounting
verifier with the defined refusal behavior, then qualify under fresh Q. Preserve
all 456 inherited method identities and required controls in a reviewed cohort
partition. Keep operational P disabled. Successful small-fixture qualification
would establish the mechanism only and would not unblock the complete real case.

Real complete continuation needs a later explicit contract/scope decision; it
cannot be enabled by another lossless encoding alone. Counting unique payloads,
excluding obligations, pruning history, splitting state to reset caps or raising
limits would change a guard. None is adopted. The design does not claim that a
particular changed limit or accounting scheme would be safe or sufficient.

The [archive](../history/lossless_state_design_20261101/manifest.json) preserves
12 pre-step active pages. Frozen sources, old receipts and execution-policy bytes
are unchanged. All 724 queued contexts, 1,782 import-frontier rows and embedded
binding/effect obligations remain open. LP11 P still refuses; G2 stays
INCOMPLETE_REFUSED. Candidate117, V34 and science remain unexecuted here; accepted
scientific cells remain 0/1020 and final freeze unsigned. Bootstrap004 is consumed,
diagnostics005 held, custody UNRESOLVED and006 unadmitted. No Git, commit or push.
