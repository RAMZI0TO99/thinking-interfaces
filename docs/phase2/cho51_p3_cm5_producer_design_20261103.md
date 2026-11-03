# CM5 producer/dispatcher lifecycle and terminal boundary design

3 November 2026. **Eight-file design independently accepted; CM5-D01 resolved.**
The [design package](cho51_p3_component_producer_v1/README.md) defines a bounded
primitive-command producer model, original dispatcher mapping/refusal obligations,
the supplied seal and future trusted terminal boundary, and failure/effect mapping.
No executable source, method identity, runtime operation, admission or Git action
was added. P remains disabled.

The model design counts representable attempts before validation, keeps the first
observed refusal sticky, settles each attempt once and preserves outer busy
ownership under simulated reentry. Fixed fault enums invoke no user callable.
Whole encoded groups use a prepared immutable output-state commit; a refusal
after FINISH can preserve a valid footer while still making terminal state
negative. Overflow makes accounting incomplete instead of wrapping or pretending
the missing call fits a completed snapshot. Seal follows final settlement and
does not claim that no future call is possible.

The original dispatcher mapping preserves setup/body/teardown/LIFO cleanup,
duration, primary outcome and stop-finally obligations. Decorated skip,
interrupted lifecycle and nested failfast paths cannot currently produce complete
CM4 evidence and remain refused/unmapped. The future trusted observer must revoke
entry, drain admitted work, observe the final latch and retain original custody;
supplied flags, hashes and footer validity cannot provide that authority.

The [effect map](cho51_p3_component_producer_v1/effect-map.json) pins **16 boundary
classes and all320 direct method obligations**. It explicitly does not establish
complete recursive effect closure. Formatting before callbacks, arbitrary helper
and checkpoint effects, mock restoration, original capture/native/custody and
secondary failure remain open. **32 design scenarios** (14 model,8 dispatcher,
6 terminal,4 effect) remain unimplemented, unexecuted and unqualified.

Source remains **836 identities /36 modules /320 selections**, with516 outside
execution and no new methods. Conditional ordinary output remains2368 events /
1,212,416 bytes; the proposed command interface uses2367 normal guarded attempts
because BEGIN emits two records. Seal/reads are not producer commands. These
counts and the unchanged33-file report minimum do not establish failure, peak
memory, capture, timing or full-operation feasibility.

Independent review found one bad source citation, CM5-D01: a capture anchor pointed
beyond the pinned document's last line. The original effect map was archived before
correction. Candidate v2 fixes that anchor and tightens trace/owner references;
every anchor's range, exact text and hash was checked. No findings remain.

| Evidence | Scope |
| --- | --- |
| [Candidate v2](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/candidate-v2.json) | 378 source pins, eight new files and four external reference-only pins |
| [Independent design review](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/design-review-v2.json) | ACCEPTED_DESIGN_ONLY; CM5-D01 resolved |
| [First review](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/design-review-v1.json) and [archived map](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/draft-v1/manifest.json) | Original finding and exact affected bytes |
| [Root adoption](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/root-design-acceptance.json) | Exact accepted candidate and saved-review confirmation |
| [Static closeout](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/final-static-checks.json) | File/text/JSON/hash/link and arithmetic only |
| [Separate closeout review](../../runs/coordination/cho51_p3_cm5_producer_design_20261103_v1/closeout-review.json) | Metadata/documentation only |
| [Pre-step archive](../history/cm5_producer_design_20261103/manifest.json) | Twelve exact preceding active pages |

Next is **source-only implementation/review of the primitive-command producer,
refusal and seal model**, with explicit roster/pin/effect/budget updates for new
tests. Original dispatcher/native observer integration remains held pending all
semantic, failure/effect, custody/capture, allocation and finite closeout/resource
proofs. The next model cannot itself discharge those original obligations.

All9,403 preserved inputs are unchanged. Original guards, full Q and117/V34 holds,
consumed failures, UNKNOWN custody and open resolver/continuation obligations
remain. QD a1f12701 is still INCOMPLETE_REFUSED17/16; complete continuation remains
infeasible under unchanged guards and G2 stays refused. Science0/1020, freeze
unsigned. Last push remains05b3a88; later CM1/CM2/CM3/CM4 work, this CM5 design and
current documentation remain uncommitted.
