# HB1 trusted-host binding and bounded qualification design

2 November 2026. Source-only design, not an adapter implementation or admission.
Root owns this package. P stays disabled. Frozen SC1/LP19/LQ19/lplan16 sources
and every historical receipt remain unchanged.

- [Binding contract](binding.md): provider boundary, exact requests/projections,
  consumption, attribution, bounded transport and refusal.
- [Qualification approach](qualification.md): noncircular evidence gates,
  exact collection, finite component cases and preserved complete Q.
- [Exact existing roster](roster.json): 580 distinct source identities in23
  modules, partitioned as32/100/384/10/19/35; no executed discovery.
- [Readiness and bounds](readiness.json): closed negative readiness decision,
  preserved resource/allocation limits and the capture counterexample.
- [Acceptance scenarios](scenarios.json):24 additional HB design obligations,
  separate from40 SC and36 diagnostic obligations; none implemented or executed.
- [Source map](source-map.json): exact inputs and source anchors.

The selected design is a bounded project-side verifier/bridge to a separately
established provider, with an explicit unavailable-capability refusal. It does
not rename FakeHost or Root-transcribed JSON as an authenticated provider.
No currently inspected project adapter supplies durable atomic claims, original
peer provenance or complete operation attribution. Provider availability is
NOT_ESTABLISHED. Runtime readiness is REFUSED_PENDING_PREREQUISITES.

Three further gates are material: synchronous host calls need real cancellation
bounds; peer review waits cannot be hidden inside or outside a reset runtime
clock; and the existing1MiB stream ceiling alone cannot prove a complete escaped
capture fits the1MiB raw-metadata slot. A production provider/lifecycle/output
contract must resolve these before any positive operational binding is possible.
This design does not grant a new service, process, journal, sidecar, clock or cap.

HB1 also specifies an explicit parent/metadata partition join. Frozen SC1's
16-path census has no representation of Q's other partitions; silently filtering
those outputs is forbidden. This typed join requires a reviewed successor and
complete parent conservation before any derived metadata view is trusted.

Next source work may implement the bounded supplied-frame verifier, refusal
state machine and exact discovery-partition checks against this design, with
independent review. That work must retain an unavailable production binding.
Real provider integration, native/component qualification and complete-Q
feasibility remain separate gates; no automatic Q/QD/P execution follows.

All18,793 resolver rows,13,406 inventory occurrences,724 queues,1,782 frontiers,
1,786 binding loads and3,972 effects remain open. Complete continuation remains
INFEASIBLE_UNDER_CURRENT_GUARDS (at least31,002 versus24,000 rows), with conditional
node/raw-byte findings unchanged. G2 and QD a1f12701 remain INCOMPLETE_REFUSED,
the latter for17/16 accounting. Prior failed attempts and UNKNOWN custody remain.
Candidate117/V34 and science are unexecuted, cells0/1020, freeze unsigned.
