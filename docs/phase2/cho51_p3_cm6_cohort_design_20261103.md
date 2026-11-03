# CM6 stable qualification cohort and current-census integration

3 November 2026. **Eight-file design independently accepted; no findings.**
The [design package](cho51_p3_cohort_integration_v1/README.md) separates a stable
qualification anchor, the full checkout census and the older CM4 fixture target.
It adds no implementation, test method, admission or runtime result. P stays disabled.

The canonical **Q360** manifest preserves the exact360 CM5 selected identities
and their order. **C** starts at876 identities/38 modules and must account for
every explicitly reviewed future addition, including held tests. **H** stays the
frozen CM4 full836/36 and selected320 target. New CM6 event ordinals refer to Q,
so inserting a held test earlier in the full sorted census cannot change an old
case's meaning. Frozen CM4/CM5 parsers, producer and evidence are unchanged.

The new expected descriptor is pinned independently of observed reports. Its
operation-bound context joins cohort, census and exact input expectations without
hash cycles. Full C validation precedes required Q and exact H projections.
New producer construction must reparse full collection and tables before entry;
the independent verifier must reparse original raw bytes. Terminal data binds
constructor inputs and the whole event stream. CM5's fixed post-footer and
secondary-refusal accounting remains mandatory. All supplied facts remain
unauthenticated and execution_accepted=False; operational dispatch refuses.

Review expressly limits what a current descriptor can establish: **it does not
prove conservation between descriptor versions**. Every successor adoption must
independently reconcile prior held additions, module pins and qualification debt
against predecessor descriptor/census evidence and current source. A supplied
validator with no predecessor input cannot certify that history. The
[Root adoption](../../runs/coordination/cho51_p3_cm6_cohort_design_20261103_v1/root-design-acceptance.json)
records this scope condition; no supplied join discharges held debt.

Q360 is an existing regression anchor. It cannot qualify newly authored CM6 tests
that it does not contain. Those tests must enter full C as explicitly held and
unqualified. A concrete finite supplemental cohort needs separate membership,
profile, debt, effect and budget review before later admission; no automatic
union or promotion into Q360 is adopted. Generic bounded manifest mechanics
alone do not authorize another cohort.

Conditional Q output is **2568 events /1,314,816 bytes /2567 attempts**, keeping254
normal subcase contexts. This is separate from CM5's frozen H2368-event scope.
Closed-schema field arithmetic gives maximum346-byte event lines,888-byte
terminal and792-byte join payloads within existing512-byte/64KiB caps. Seven raw
input ceilings total5,439,488 bytes. These are representation bounds, not peak
memory, capture, original allocation or whole-operation feasibility. The existing
33-file report proposal and all original guards remain unchanged.

**32 design scenarios** (eight each for identity, collection, integration and
gates) remain unimplemented, unexecuted and unqualified. Current source remains
876/38/360 with516 outside the anchor and no new methods. The40 CM5 methods remain
unexecuted. No original collector, dispatcher or trusted terminal observer exists
by virtue of this design.

| Evidence | Scope |
| --- | --- |
| [Candidate v1](../../runs/coordination/cho51_p3_cm6_cohort_design_20261103_v1/candidate-v1.json) |395 source pins including eight new files; four external reference-only pins |
| [Independent design review](../../runs/coordination/cho51_p3_cm6_cohort_design_20261103_v1/design-review-v1.json) |ACCEPTED_DESIGN_ONLY, no findings; current-descriptor scope clarified |
| [Canonical Q360 manifest](cho51_p3_cohort_integration_v1/cohort.json) |36161 bytes; exact prior360 identity order, distinct raw and identity digests |
| [Static closeout](../../runs/coordination/cho51_p3_cm6_cohort_design_20261103_v1/final-static-checks.json) |File/text/JSON/hash/link/arithmetic checks only |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm6_cohort_design_20261103_v1/closeout-review.json) |Metadata/documentation acceptance only |
| [Pre-step archive](../history/cm6_cohort_design_20261103/manifest.json) |Twelve exact preceding active pages |

All9,474 preserved inputs remain unchanged. No Python, imports, project parser,
AST/compiler, native calls, tests or Git operation occurred. Original guards,
full Q and117/V34 holds, consumed failures, UNKNOWN custody and open resolver/
continuation obligations remain. QD a1f12701 is still INCOMPLETE_REFUSED17/16;
full continuation infeasible, G2 refused; science0/1020, freeze unsigned.
Last push remains05b3a88; subsequent CM1–CM5 work, this CM6 design and current
documentation remain uncommitted.

Next is **source-only implementation/review of the expected-context and full
current-collection contracts**, with explicit held new-test accounting and
prior-debt reconciliation. The versioned producer/verifier/terminal integration
follows separately; original runtime, capture/custody, allocation and finite
closeout/resource gates remain held.
