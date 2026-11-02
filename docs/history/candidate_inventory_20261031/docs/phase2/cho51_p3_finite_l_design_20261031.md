# Finite L plan and Lhost compatibility design

31 October 2026. The eight-file design has independent revision1 acceptance
and Root design acceptance. No executable source was changed and no parser, import, native operation,
collection or test was run for this step.

## What the review establishes

The retained P derivation contains 7,873 findings across 36 inspected modules:
5,789 calls, 1,346 branches, 538 from-imports, 174 imports, 11 native loads,
7 dynamic-code sites, 5 resources, 2 dynamic imports and 1 syntax report.
All 31 pages and their module pins are accounted for. These are unresolved
decisions and diagnostics, not 7,873 failed tests. The seed provides no accepted
import edges or complete dependency closure.

Independent source-text inspection identifies two malformed decorator endings
in the frozen telemetry tests, at lines 114 and 157. The old parser recorded
only `SyntaxError` without a position. The first defect plausibly explains that
record; no parser was run to establish the historical cause. Both corrections
belong in a versioned successor, leaving the original source untouched.

The [eight-file design package](cho51_p3_finite_l_v1/README.md) specifies:

- Bounded syntax diagnostics and complete refusal accounting.
- Exact candidate-v2 migration: two colon deletions, two mapping-test import
  prefix changes, unchanged production bytes and a 25-function identity map
  preserving the 39/78 split and 117 expectations.
- A versioned plan compiler with lexical bindings, explicit effect and
  exclusion proofs, finite transitive closure and fail-closed completeness.
- Ordered initialization, guards, native/resource/ABI and plugin contracts.
- Lhost compatibility for native bootstrap, current P authority, retained
  large-image streaming, native-edge joins and exact code-role attribution.
- 34 new, unexecuted targeted qualification scenarios supplementing the
  existing 40 L obligations. These are distinct from the 34 V controls.

The design does not approve any of the 7,873 findings for execution. A complete
materialized plan, implementation review and implementation-specific adoption
remain required. Existing caps are unchanged; unsupported behavior or a closure
that exceeds them must refuse rather than silently widen the contract.

## Next implementation sequence

First implement and independently review the candidate migration and bounded
diagnostic/inventory portion of the new compiler. Fresh Q qualifies the
mechanisms; separately admitted file-only P establishes actual syntax and
candidate identity evidence. Build and review the provisional source-level
decision closure while retaining unresolved capability obligations.

Then implement the matching Lhost/observer/retained-reader successors, qualify
actual owned-fixture lifecycle and remaining mechanisms, and refresh all
invalidated Q coverage and P preparation for the final frozen sources and plan.
Join every plan effect to an implemented qualified capability before final
complete-plan review and acceptance. Only that accepted plan and current Q/P can precede fresh
L-only admission. L collects actual successor IDs; V tests/controls and C
closeout remain separate. No old launcher is rearmed.

## Evidence and preservation

Phase records are in
`runs/coordination/cho51_p3_finite_l_design_20261031_v1`. The
[revision1 candidate manifest](../../runs/coordination/cho51_p3_finite_l_design_20261031_v1/design-candidate-revision1.json),
[independent review](../../runs/coordination/cho51_p3_finite_l_design_20261031_v1/design-review-revision1.json)
and [Root design acceptance](../../runs/coordination/cho51_p3_finite_l_design_20261031_v1/root-design-acceptance.json)
pin the accepted package. The first review and supplement remain preserved,
along with all eight original design files. Revision1 resolves the physical
descriptor compatibility join and separates provisional source closure from
final implemented-capability acceptance. The
[initial file checks](../../runs/coordination/cho51_p3_finite_l_design_20261031_v1/initial-file-checks.json)
match all 4,589 preserved files and 64 traced inputs. These are file checks,
not runtime validation. The
[documentation archive](../history/finite_l_design_20261031/ARCHIVE_INDEX.md)
preserves 13 exact pre-step snapshots.

The [accepted native-bootstrap Q2/P2](cho51_p3_native_memory_bootstrap_20261031.md)
remain unchanged historical evidence. New design and documentation entries
change the declared metadata census; fresh applicable coverage/preparation is
required before reuse. The old P release-time census is not rewritten.

L collection, original and corrected 117 candidate cases and 34 V controls
remain unexecuted. The full 40-scenario L qualification remains incomplete.
Bootstrap004 is consumed, diagnostics005 held, custody UNRESOLVED and006
unadmitted. Scientific cells remain 0/1020 and the final freeze unsigned.
No commit, push, scientific execution or external coordination occurred.
