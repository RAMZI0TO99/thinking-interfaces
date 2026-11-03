# CM5 supplied producer/refusal/seal implementation

3 November 2026. **Independently accepted for source only; CM5-S01/S02 resolved.**
The [six-file package](../../tools/local_validation/cm5/README.md) implements the
accepted primitive-command producer, refusal accounting and immutable supplied
seal. Its [implementation contract](cho51_p3_cm5_implementation_contract_20261103.md)
records the exact roster, budgets and continuing runtime boundaries.

The model counts represented entries before checking commands, faults, busy or
sticky state; settles each once; and preserves the first observed refusal.
Pre-check refusal retains the previous prefix. Post-check refusal preserves the
committed group, including a valid footer. Entire output and lifecycle changes
are prepared before one serial-model state replacement. No arbitrary callback,
test body, native provider or real dispatcher runs through this interface.

Seal returns immutable raw bytes, either a raw terminal or None, and bounded
diagnostic facts. Overflow, incomplete prefix or secondary failure cannot produce
a completed terminal. All-PASS event bytes can coexist with a refused terminal;
independent raw verification must retain both. After-detach entry does not mutate
the snapshot and cannot be evidence of no later activity. Facts are always
unauthenticated and execution_accepted=False; operational dispatch refuses.

Independent review found two issues in the first frozen candidate. **CM5-S01**
identified missing late-attempt accounting for nested reentry after FINISH;
common entry accounting now handles both paths. **CM5-S02** identified refusal
reporting failures hidden by an earlier sticky latch; intended refusal creation
is now separate from helper recording, whose failures mark accounting incomplete.
Focused examples cover exact nested terminal counters and partial/preexisting
sticky helper failures in apply and active seal. Five affected files were
archived before correction. The second review accepted the source with no findings.

The [source roster](cho51_p3_cm5_roster_successor_20261103.json) is now
**876 identities /38 modules /360 proposed selections**, retaining516 outside
execution. **40 new methods** (20 producer,20 refusal) remain unexecuted. The
[source/scenario index](cho51_p3_cm5_source_coverage_20261103.json) conserves320
prior direct-method rows and adds40, with77 declaration rows and21 import rows.
All32 design scenarios remain unqualified:14 model source-example scenarios,
14 original dispatcher/terminal scenarios and four accounting/partial examples.
Direct text and mocked failure examples do not establish recursive effect closure.

The producer deliberately keeps the frozen **CM4 836/36/320 target**. Its normal
conditional envelope remains2368 records /1,212,416 bytes and2367 guarded attempts.
With zero new subTest contexts and254 inherited contexts, a hypothetical compatible
expanded mapping would require2568 records /1,314,816 bytes and2567 attempts.
An expanded collector/producer/verifier is not implemented. Synthetic inner
records and privileged counter/capacity seeds are not original test callbacks.
The33-file report proposal, all memory/time/disk/capture/cleanup guards and
original native allocation obligations remain unchanged.

| Evidence | Scope |
| --- | --- |
| [Candidate v2](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/candidate-v2.json) | 387 source pins including nine new files; four external reference-only pins |
| [Independent source review](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/source-review-v2.json) | ACCEPTED_SOURCE_ONLY; CM5-S01/S02 resolved |
| [First review](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/source-review-v1.json) and [archived candidate files](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/draft-v1/manifest.json) | Exact original findings and affected bytes |
| [Root adoption](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/root-source-acceptance.json) | Exact source, saved-review confirmation and scoped adoption |
| [Static closeout](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/final-static-checks.json) | File/text/JSON/hash/link/arithmetic checks only |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm5_implementation_20261103_v1/closeout-review.json) | Metadata/documentation scope only |
| [Pre-step archive](../history/cm5_implementation_20261103/manifest.json) | Twelve preceding active pages |

No Python, import, project parser/AST/compiler, native call, test or Git operation
occurred. Source review does not certify executable syntax or runtime behavior.
All9,436 preserved inputs remain unchanged. P is disabled; full Q and117/V34 stay
held. QD a1f12701 remains INCOMPLETE_REFUSED17/16; consumed failures and UNKNOWN
custody remain. All original resolver/continuation debts remain open; full
continuation remains infeasible and G2 refused. Science0/1020, freeze unsigned.
Last push remains05b3a88; subsequent CM1–CM5 work and current docs are uncommitted.

Next is **source-only design/review of a stable qualification cohort and
current-roster collection/producer/verifier integration**. That decision must keep
the source census, validation cohort and supplied fixture target distinct.
Original dispatcher/observer integration remains held pending its semantic,
failure/effect, capture/custody, allocation and finite closeout/resource gates.
