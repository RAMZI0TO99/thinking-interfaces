# CM2 supplied retained-byte and callback adapters

Source-only implementation of the bounded next step in the accepted CM2 design.
No importer, compiler, TestResult subclass, case dispatcher, native guard, provider,
publisher or live evidence aggregator is provided. Operational dispatch refuses.

- `retained.py` verifies canonical supplied manifest/source bytes, acyclic module
  dependencies, package/parent/token joins, bounded code trees and location pairs,
  then exact before/after loaded-token snapshots. It performs no filesystem reads,
  compilation or object inspection. Model source/manifest input is conservatively
  limited to 1 MiB; the design's future 4 MiB manifest and larger graph/native
  requirements remain unimplemented. Source/source-package/closed namespace only;
  native/builtin/frozen and cyclic/over-depth graphs refuse. Tokens are untrusted.
- `callbacks.py` translates primitive supplied callbacks into a bounded canonical
  successor event stream. It enforces cleanup before PASS, exact starts/ends,
  subcases, trace groups, failfast, duration order and suite closure. It preserves
  negative cleanup/fixture facts and a bounded prefix on sticky refusal. A supplied
  cleanup_done or close_suite call is not evidence of real lifecycle closure.
  Flat sequential subcases only; nested/unknown/UNSUPPORTED routes refuse. Fixture
  slots each describe one declared boundary; distinct slots can share owner/phase.
- `registry.py` declares the explicit source successor: 764 full identities in
  32 modules and 248 selected, including 32 new model methods. Exact test pins are
  literal; the external candidate pins the registry, avoiding a self-hash cycle.
- `collection.py` verifies the full successor before deriving the unchanged
  732/30 CM1 projection and its frozen 700/28 HB1 projection. All three byte
  digests remain separate. The other 516 cases stay accounted but unexecuted.

Every result remains unauthenticated and execution_accepted=False. Model success
cannot grant COMPONENT_MODEL_ONLY, Q, P, L, V or science. The new schema
cho51_cm2_event_v1 explicitly changes the roster/selection while preserving all
13 fields, 4,096-record/512-byte/2-MiB ceilings and 128-frame cap. It does not alter
or claim wire compatibility with frozen CM1. Actual emitted streams require a
future independent external verifier and original custody before acceptance.

All 32 new tests are unexecuted. Their normal unittest subtests total 44; together
with the frozen predecessor's 210, conditional normal output is 1,000 records /
512,000 bytes at the record cap. Synthetic 746-record full-model fixtures and
4,095-record overflow prefixes are model data, not actual outer test callbacks.
Complete failure/runtime/capture/native/allocation/lifecycle feasibility remains
open. P is disabled and no old launcher is used.
