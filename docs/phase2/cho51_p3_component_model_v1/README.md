# CM1 bounded component-model runner design

2 November2026. Design only. This package specifies a new CM1 component runner
and supplied-data contracts after [HB1 source acceptance](../cho51_p3_hb1_implementation_20261102.md).
It does not implement or launch that runner. P stays disabled, all guards and
obligations remain, and runtime readiness is refused pending explicit prerequisites.

- [Runner and original guard boundary](runner.md)
- [Retained loading and exact collection](collection.md)
- [Finite reporting, capture and accounting](capture-accounting.md)
- [Qualification and implementation gates](qualification.md)
- [Exact current and planned identities](roster.json)
- [Readiness and unchanged limits](readiness.json)
- [Pinned source trace and unresolved dependency edges](source-map.json)

The current roster remains700 implemented source identities/28 modules;184 are
the proposed existing component selection. CM1 proposes32 explicitly named new
contract-test methods in two modules, yielding a future732/30 complete collection
and216 selected methods. These32 are unimplemented declarations, not new passing
tests. The exact source bytes and complete method/subcase/effect table must be
reviewed before admission. HB1's immutable700 verifier is not edited or widened.

Two concrete design changes follow the source trace. Live resource/retention
instrumentation must be isolated from eight shared module attributes mocked by
the SC tests. A new result sink must bypass all unittest traceback formatters,
which otherwise allocate exception text before the old writer's byte check.
Neither change proves complete native custody or capture feasibility by itself.

The trace found real memory/layout work, a16MiB allocation, RLock construction
and a wall-clock read in selected model paths. It is not a proof that all184
recursive paths lack other effects. This is component-model qualification with
real interpreter/runtime work, not a declaration of zero native effects.

The source plan is finite. Bootstrap/runtime closure, complete source-derived
event bounds, native ownership/guard qualification, raw failure/tool capture,
real parent attribution and the asynchronous publication lifecycle remain
explicit admission gates. The next source-only implementation can supply the
CM1 registry, collector contracts, event/accounting verifier and default refusal;
it cannot silently turn those gates into successful Booleans.

No original provider, durable claim, real complete census, full Q,117/V34 or
scientific result is established. Model confirmation cannot become production
authority. Historical QD17/16 refusal, consumed attempts and UNKNOWN custody
stay unchanged. Full continuation remains infeasible under unchanged guards.
