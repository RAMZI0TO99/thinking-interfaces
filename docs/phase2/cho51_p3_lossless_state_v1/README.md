# Lossless state representation and feasibility

Engineering design, 1 November 2026, Asia/Riyadh. This package completes the
representation/capacity decision requested after the accepted
[reconstruction design](../cho51_p3_reconstruction_v1/README.md). It specifies
a new transport format and verifier, not a replacement execution grant or an
implemented codec. Root authors; an independent peer reviews exact pinned bytes.

The proposed format stores one immutable canonical graph, ordered complete
frames and exact historical file bytes. A manifest retains every logical use
and original page/row identity. Reconstructing a snapshot expands those uses
back into the exact accepted kernel schema. Physical sharing never reduces
logical occurrence counts, canonical snapshot bytes or retained-history charges.

Read all four companion contracts:

- [Exact format and losslessness](representation.md)
- [Verification, replay and publication](verification.md)
- [Capacity equations and final feasibility decision](capacity.md)
- [Qualification and next implementation scope](qualification.md)

## Decision

**The complete real-data continuation is infeasible under the existing guards.**
This is a completed negative feasibility decision, not a request for another
encoding design. No lossless encoding that preserves the required expanded-state
accounting can turn the resolver's first successor lower bound of 31,002 rows
into a state satisfying the 24,000-row cap. Changing physical layout cannot
alter that arithmetic. Combining both inventories also has 28,892 distinct node
rows before other obligations. The latter conclusion is conditional on a single
combined graph; the historical observations retain their separate scopes.

The proposed uncompressed transport would also need at least 20,370,470 physical
bytes to carry both historical inventories and their indices, before its new
metadata. That exceeds a single 16 MiB resolver/state output allocation. This
is a bound on this exact-byte transport of that bundle, **not** a measured bound
on a canonical kernel snapshot, compression in general, or all possible layouts.

The [static capacity cases](../../../runs/coordination/cho51_p3_lossless_state_design_20261101_v1/capacity-cases.json)
reuse the prior independently checked occurrence join and recheck its 136 input
pins. No graph reconstruction, codec, compression, source AST, replay, test or
runtime operation was executed. A small illustrative arithmetic case is not a
passing fixture or a positive end-to-end feasibility claim.

The format is useful for bounded supplied states: it specifies exact reversible
storage and a verifier that must preserve the kernel's refusals. Implementation
and fresh Q can qualify that mechanism without pretending to unblock the real
producer. This is the next bounded implementation scope. Operational P stays
disabled; no known-infeasible real P is needed to reconfirm the static result.

Real continuation requires a later explicit contract/scope decision. Counting
unique payloads instead of historical uses, excluding inventory/debt, pruning
history, splitting one state across operations to reset limits, or increasing
limits would change an existing guard. None is adopted or implied here. Any
future proposal must state the exact accounting change, preserve obligations,
justify safety and receive the appropriate explicit authorization and review
before implementation. Current direction is to preserve the guards.

LP11/LQ11/lplan8 and all accepted/failure receipts remain frozen. Their 456
distinct qualified methods remain the inherited baseline. G2 is INCOMPLETE_REFUSED;
117 candidates and 34 V controls remain unexecuted; science is 0/1020 and final
freeze unsigned. Bootstrap004 is consumed, diagnostics005 held, custody UNRESOLVED
and 006 unadmitted. No external chat, Git, commit, push or scientific execution.
