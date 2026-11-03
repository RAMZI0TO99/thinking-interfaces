# CM4 supplied lifecycle and current-roster integration design

2 November 2026. Source-only successor to the [CM3 implementation](../cho51_p3_cm3_implementation_20261102.md).
Root authors and publishes these seven design files; cm4_boundary_analysis supplied
read-only code analysis. A different peer reviews the frozen design and a separate
peer reviews documentation closeout. Acceptance is recorded outside this candidate.
No executable source, method identity, runtime operation or admission is added.

CM3 verifies historical CM2 bytes correctly but cannot recover hidden cleanup,
duration, suite state or refusal after a valid footer. CM4 specifies new supplied
collection/event/table schemas and a separate terminal snapshot. It makes declared
lifecycle state checkable; it cannot authenticate that state or prove no activity
occurred after the supplied observation boundary. Frozen CM1/CM2/CM3/HB1 sources,
wire meanings, receipts and module pins remain unchanged.

| Contract | Decision |
| --- | --- |
| [Collection](collection.md) | Full current 796/34 census and exact 280 selection before historical views |
| [Events](events.md) | Versioned explicit cleanup/duration/flat-subcase/suite/restoration/final-input claims |
| [Terminal and join](terminal-join.md) | Exact final snapshot and five-input raw join; late-refusal distinction |
| [Allocation](allocation.md) | Named report reservations, conditional normal arithmetic and unchanged gates |
| [Qualification](qualification.json) | 28 finite design obligations, no executed or qualified scenarios |
| [Readiness](readiness.json) | Machine-readable boundaries; acceptance remains external |

The future supplied-only implementation consists of independent collection and
event parsers, current table checks, a terminal parser and a raw join. It may use
pinned primitive canonical/hash helpers and literal registries; it must not replay
CallbackModel, invoke a dispatcher, trust caller-created Facts, or coerce CM4 events
into an old schema. All results have immutable authenticated=False and
execution_accepted=False properties. Runtime dispatch always refuses.

The design target is exactly the frozen CM3 source roster: 796 identities / 34
modules, 280 proposed selections, 516 outside execution. Implementation tests will
change that roster. Before source acceptance, an explicit successor must add every
new method/module, pin its bytes, update all coupled counts/digests/selection and
normal/failure accounting, and review every new effect. Keeping 796 as a historical
target is permitted only if labelled historical; it cannot be current discovery.
No self-hash cycle: tests must not embed their own source or candidate digest.

Next is source-only implementation and independent review of these supplied-data
contracts, including that explicit new-test roster/budget successor. Real original
dispatcher, lifecycle observer, native sealing/custody and operational publisher
are separate later work. Existing CM3-F01..F04 and C01..C05, the 26 local/24 HB/
40 SC/36 diagnostic/48 original scenarios and all unqualified methods remain open.

P is disabled. Full Q32/100/384, candidate117/V34 and science remain held. No
Python, imports, project parser/AST/compiler/native invocation, tests or Git are
part of this design phase. QD a1f12701 remains INCOMPLETE_REFUSED17/16, old failures
stay consumed and UNKNOWN custody stays unknown. All 18,793 resolver rows,
13,406 inventory occurrences, 724 queues, 1,782 frontiers, 1,786 loads and 3,972
effects remain open. Complete continuation is still infeasible at at least 31,002
rows against 24,000; G2 remains refused. Science stays 0/1020, freeze unsigned.
