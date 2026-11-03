# CM6 expected context and full current collection

3 November 2026. **Supplied-data implementation independently source-reviewed.**
CM6-S01 is resolved: the source index explicitly marks manifest dependency and
provenance checks as partial. No code correctness finding was identified.
The [implementation contract](cho51_p3_cm6_implementation_contract_20261103.md)
and [package](../../tools/local_validation/cm6/README.md) define three raw-input
boundaries: expected context, full current collection, and conservative comparison
of supplied prior/current collections.

Expected-context checks bind independently supplied Q/D size/hash pins, canonical
schemas, exact types, baseline identities/module pins and held obligations.
Full collection checks every declared current row before making stable Q and
frozen historical H views. The H bytes are independently passed through the
frozen historical verifier. The separate prior/current helper refuses dropped
identities, changed module pins or debt, promotions and additions to prior modules.

These are immutable supplied facts, always unauthenticated and execution
unaccepted. They do not establish original discovery, source/runtime manifest
contents, authentic predecessor selection or debt discharge. In particular, CM6-08
checks only hash-reference shapes and local context construction; actual manifest
dependency sets, cycles and expectation provenance remain open.

The [roster](cho51_p3_cm6_roster_successor_20261103.json) now records
**936 identities /41 modules**, with fixed **Q360** and **576 held**. All60 new
methods are held and unexecuted. Q membership/order/digest is unchanged; no
supplemental cohort is adopted. The
[actual source-phase debt ledger](cho51_p3_cm6_held_reconciliation_20261103.json)
preserves the prior516 held identities, prior876 identities and38 module pins,
and adds60 NEW_TEST_UNQUALIFIED debts. There was no original predecessor CM6
runtime descriptor/collection, and none was fabricated.

The [source index](cho51_p3_cm6_source_coverage_20261103.json) preserves360 prior
anchor body rows and adds60 held rows:420 accounted bodies, not420 selected tests.
It records110 declarations and36 direct imports, without claiming exhaustive
recursive effects. Zero new subTest contexts are added. All32 CM6 scenarios
remain unqualified; source examples are partial where stated.

Conditional Q arithmetic stays2568 events /1,314,816 bytes /2567 attempts;
CM5's actual supplied producer remains frozen H2368 events /1,212,416 bytes.
Current Q/D/C raw input ceilings total2,162,688 bytes; the separate pair helper's
five input ceilings total4,259,840 bytes. These are representation limits,
not peak memory, failure capture or whole-operation feasibility. All original
time, resource, ownership, stop, cleanup, output and allocation guards remain.

| Evidence | Scope |
| --- | --- |
| [Candidate v2](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/candidate-v2.json) |408 source pins, including13 new files; four external reference-only pins |
| [Initial source review](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/source-review-v1.json) |CM6-S01 metadata finding; no code finding |
| [Final source review](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/source-review-v2.json) |Source-only acceptance; finding resolved |
| [Frozen correction archive](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/draft-v1/manifest.json) |Exact pre-correction source index and confirmed review provenance |
| [Root adoption](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/root-source-acceptance.json) |Separate supplied comparison and independent source/adoption obligations |
| [Static closeout](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/final-static-checks.json) |File/text/JSON/hash/link/arithmetic checks |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm6_implementation_20261103_v1/closeout-review.json) |Metadata/documentation scope only |
| [Pre-step documentation archive](../history/cm6_implementation_20261103/manifest.json) |Twelve exact preceding active pages |

All9,503 preserved inputs remain unchanged. No Python, imports, project parser,
AST/compiler, native calls, tests, runtime or Git operation occurred. Source
review is not executable syntax or test success. P stays disabled, full Q and
117/V34 remain held, consumed failures and UNKNOWN custody remain unchanged.
All original resolver/continuation obligations remain open; QD a1f12701 remains
INCOMPLETE_REFUSED17/16, full continuation infeasible and G2 refused.
Science remains0/1020 and the final freeze unsigned.

Next is **source-only CM6 producer/verifier/terminal integration and independent
review**, preserving fixed Q, held-test debt and CM5-S01/S02 failure accounting.
Original collection/dispatcher/observer and effects/capture/custody/allocation/
finite closeout/timing/memory gates remain separate. Last push remains05b3a88;
later CM1–CM6 work and current documentation remain uncommitted.
