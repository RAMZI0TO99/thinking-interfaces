# CM3 independent evidence verification and failure/capture design

2 November 2026. Source-only design successor to the
[CM2 implementation](../cho51_p3_cm2_implementation_20261102.md). Root owns this
seven-file design and publication; cm3_boundary_trace supplied read-only source
analysis. A different peer reviews the design, and a separate peer reviews the
metadata closeout. No code, test identity, runtime operation or admission is added.

The next implementation is an independent supplied-byte parser for the frozen
CM2 event schema and a raw collection/event/table join. It must not instantiate
CallbackModel, replay callbacks to manufacture validation, trust caller-created
Facts, or coerce CM2 records into the older CM1 wire format. Shared frozen literal
registry and canonical data primitives may be used after exact pin review.

| Contract | What it settles |
| --- | --- |
| [Event verifier](event-verifier.md) | Exact observable grammar, state, trace ownership, hashes and conservative dispositions |
| [Evidence join](evidence-join.md) | Full collection first; separate original/projection digests; supplied context and table bindings |
| [Failure domain](failure-domain.md) | Upstream formatting and lifecycle gaps; requirements for a real case/suite successor |
| [Capture](capture.md) | Finite raw/envelope obligations, unchanged allocation and negative feasibility decision |
| [Qualification scenarios](qualification.json) | Finite adversarial requirements, not implemented tests or passing controls |
| [Readiness](readiness.json) | Explicit current pins/counts, missing capabilities and held operational gates |

CM2 raw bytes do not expose cleanup_done, duration, close_suite, checkpoint
enforcement or the producer's final refusal latch. Even identical complete
all-PASS transcripts can accompany different final producer states. Therefore
this verifier can establish only observable supplied transcript consistency.
It cannot prove real lifecycle completion or recover an invisible late refusal.
No positive model result grants COMPONENT_MODEL_ONLY or any execution authority.

The current source roster remains 764 identities / 32 modules, with 248 proposed
selected identities and 516 outside execution. CM3 adds zero test methods. The
32 CM2 methods and earlier unqualified cohorts remain unexecuted. The conditional
normal CM2 bound stays 1,000 events / 512,000 bytes; complete failure/capture and
runtime feasibility remain NOT_ESTABLISHED. No additional runtime slot, larger
ceiling, new clock or omitted obligation is authorized by this design.

Implementation must separately freeze any new method identities and an explicit
current roster/budget successor. A historical CM2 report remains a fixed-schema
764/248 verification target; it must never be described as full collection of a
later enlarged checkout. Full current collection, selection and event production
need their own reviewed versioned join before any later execution. This avoids
both hiding verifier tests and silently rewriting frozen validators.

All existing guards, unknown custody and consumed attempts remain. Full Q32/100/
384, candidate117/V34, P and science stay held. QD a1f12701 stays INCOMPLETE_REFUSED
17/16; complete continuation remains infeasible under its original guards and G2
remains INCOMPLETE_REFUSED. All resolver debt stays open, science remains 0/1020
and the final freeze is unsigned. Next is source-only implementation and review
of the independent parser/join, with explicit roster adoption and no live runner.
