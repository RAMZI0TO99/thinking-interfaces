# BD1: native provider, driver and qualification-entry design

This eight-file source-only successor makes concrete choices for the
[PC1 boundary](../cho51_p3_provider_contract_design_20261103.md) and preserves the
[source-reviewed PC1 implementation](../cho51_p3_pc1_implementation_20261103.md).
It creates no executable, native build, test method, admission or qualification.

The proposed architecture is an independently established external host H0,
a new native outer provider G0 and a new native supervisor/driver S0. H0 is the
foundational B0 trust/enforcement/observation boundary; G0 is a candidate B0
facet until independently qualified. S0 supplies B1's finite protocol behavior.
The existing single test-child position is reserved but **absent in the first
E1_PROTOCOL entry**. This is a distinct prerequisite scope, not a smaller
S140/Q360 operation or a replacement for any original control.

The design selects fixed binary requests/replies, an event-driven native owner,
lossless fixed-width witness records and existing report roles. It establishes
conditional representation arithmetic for the bounded E1 domain. It does not
establish a currently available H0, authentic native observations, complete
transport/last-writer retention, source/runtime closure, or timing/peak fit.
Missing prerequisites refuse before effects. All current runtime stays held.

[Provider](provider.md), [driver/entry](driver.md) and [retention](retention.md)
define the protocol and proof obligations. [Packing](packing.json) carries exact
record layouts, source-width bounds and inherited33 role reservations.
[Qualification](qualification.json) defines40 new scenarios, all unimplemented
and unqualified. [Debt](cohort-debt.json) conserves1125/51, Q360/S140 and all765
held rows; [readiness](readiness.json) pins the other seven files.

Next is source-only implementation/review of the versioned native G0/S0 skeleton
and fixed codecs, with an unavailable-H0 refusal route, source/effect/budget
accounting and explicit held-test additions. That successor must not launch,
compile, claim a host capability or borrow an old receipt. Actual H0 adoption,
build/runtime qualification and every entry predicate remain separate.