# CM6 stable cohort and current-census integration design

3 November 2026. Source-only design after the
[CM5 implementation](../cho51_p3_cm5_implementation_20261103.md).
Root authors these eight files; a source-analysis peer is separate from the
independent design reviewer and metadata closeout reviewer. Acceptance is
recorded externally to the frozen candidate. No code or new test method is added.

| Contract | Decision |
| --- | --- |
| [Cohort](cohort.json) | Exact ordered360-member qualification anchor, independently pinned canonical bytes |
| [Identity and context](identity.md) | Separate cohort, full census and legacy target; externally expected acyclic input pins |
| [Collection](collection.md) | Complete current census before stable and exact historical views; every held row conserved |
| [Producer/verifier integration](integration.md) | New CM6 raw schemas and independent parsing; frozen CM4/CM5 stay unchanged |
| [Budgets](budgets.md) | Stable event arithmetic, finite input/line bounds and unchanged original guards |
| [Qualification scenarios](qualification.json) |32 design obligations, unimplemented/unexecuted/unqualified |
| [Readiness](readiness.json) | Design scope, unchanged source census and held runtime prerequisites |

The qualification anchor **Q** is the existing CM5 selection of360 identities.
Its identity order stays fixed when the full checkout census **C** grows from
876 identities/38 modules. **H** is the frozen CM4 fixture target836/36/320.
CM6 event case ordinals address Q, never C or H. Full C must be checked before
any selection; added tests remain explicit held qualification obligations.
This stops an added test from silently changing the meaning of old event ordinals
or requiring another wire-target migration just to describe the checkout.

Q360 is a regression anchor, not a claim that its old tests exercise a future
CM6 implementation. Newly authored CM6 tests remain unqualified until their own
finite supplemental cohort is explicitly reviewed/adopted and eventually admitted.
No future supplemental identity list, execution or budget is approved here.
The bounded supplied codec can use externally pinned cohort data, but this design
adopts only the exact Q360 manifest. A change of admitted cohort requires a new
manifest/context and explicit scope accounting; no automatic promotion or merge.

Next is source-only implementation/review of the CM6 expected-context and full
collection contracts, including explicit accounting for any new held test methods.
Producer/verifier/terminal integration follows as a versioned source successor.
Neither step implements an original loader, dispatcher or trusted observer by
inference. Every real lifecycle, failure/effect, capture/custody, allocation,
finite closeout and timing/memory gate remains open. P remains disabled.

All9,474 preserved inputs remain immutable. Current source stays876/38/360 with
516 outside the qualification anchor; no method is added or run. All CM5/CM4 and
earlier scenarios retain their original status. Full Q32/100/384 and117/V34 remain
held; QD a1f12701 is INCOMPLETE_REFUSED17/16, consumed failures and UNKNOWN custody
remain. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1782
frontiers,1786 loads and3972 effects remain open. Full continuation remains
infeasible at least31,002 rows against24,000; G2 refused. Science0/1020, freeze
unsigned. No Python/import/project parser/AST/compiler/native/tests/Git/runtime.
