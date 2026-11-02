# HB1 implementation contract: supplied data only

2 November2026. This successor implements the source-reviewable checks in the
accepted [HB1 design](cho51_p3_host_binding_v1/README.md). It does not adopt a
production provider interface or change the frozen SC1/LP19/LQ19/lplan16 sources.
No runtime, collection, import, AST, compiler, native or test execution is admitted.
P is disabled. All original obligations and guards remain.

## Interfaces and authority boundary

`tools/local_validation/hb1` has no production filesystem/network/native/provider
calls or launcher. Its standard-library imports and frozen v1 lexical Windows
path helper are source dependencies, not proof of actual loaded-code custody.
All entry inputs are complete immutable byte strings or explicit model data;
checkpoint callbacks must return exact True. They are supplied callbacks, not
live sensors. Rejected inputs raise Refusal (a callback's exception may also
propagate); no partial successful result is returned.

`frames.parse_request` and `parse_response` check the exact8-byte little-endian
length prefix,1..4088-byte closed header, payload checksum, complete extent,
request/response joins, closed request/refusal shapes, canonical UUID/tokens and
supplied clock bounds. Request limits remain4096 payload/8192 complete bytes;
response limits remain131072/135168. Header payload length must match the prefix.
The unsigned64 QPC is canonical decimal text. Requests bind operation/authority
or exact reviewer/message IDs. An OK claim/census body is syntax-checked JSON
with provider schema UNAVAILABLE; original peer bytes are retained unchanged.
Neither syntax nor an OK field authenticates a message. No evidence projection
or generic JSON-to-trust conversion exists.

`common` rejects duplicate keys, floats, nonfinite values, invalid Unicode,
nonexact integer types, signed64 overflow, depth beyond24, containers beyond4096
and graphs beyond100000 nodes. Input/encoding maxima are explicit and never
exceed1MiB. Hash updates are at most64KiB between callbacks. Encoding snapshots
each bounded container and validates descendants during traversal; cycles and
callback-time mutation cannot bypass depth/node/type/cap checks. Encoding is a
bounded deterministic copy, not an atomic snapshot of concurrent external state.
No Python parsing call, callback or timing measurement here proves native
cancellation or the proposed200ms live exchange bound.

`refusal.UnavailableHost` exposes the three SC1-shaped methods solely to refuse.
Claim attempts are consumed locally before a callback can fail, but transport is
NOT_SENT and durable consumption remains UNKNOWN. A new object is not proof that
an operation UUID is unused. Read-only methods cannot yield empty success.
`ModelSession` is a separate MODEL_ONLY type without those three host methods.
It models a single pending request, exact sequence/fresh request ID, one claim,
supplied monotone clock and original work/cleanup/hard bounds. Ambiguity, refusal,
malformed evidence and checkpoint failure consume its failure state. Symbolic
`model_confirm_claim` exercises only a hypothetical branch: parsed OK evidence
never invokes it. Native cleanup bookkeeping exchanges, channel closure and
cross-session/restart durability are not implemented or claimed.

## Parent map and census model

`joins.parse_join` consumes the exact accepted `cho51_hb1_parent_join_v1` schema
within65536 bytes. This standalone ceiling does not demonstrate that a complete
map and its references fit SC1's allocation envelope. The four partition schemas
are exact `{files,bytes}` values: fixtures160/33554432, supervisor40/8388608,
caller40/20971520, closeout16/4194304. Total256/67108864 and per-file8388608 remain.
Reservations charge their full caps, including unused/failed entries. All16
closeout roles preserve their fixed3293184-byte aggregate.

For this supplied model only, canonical lexical paths are fixed beneath
`D:/Aenv/pro3/runs/coordination/cho51_p3_hb1_unadmitted/<parent UUID>/`.
No such directory is created. Ordinary paths are within their partition, with
parent UUID/null role. Main slots are exactly
`closeout/<role>_<metadata UUID>.json`. Canonical Windows paths, case aliases,
file/ancestor collisions, foreign roots, alternate streams and reserved names
are checked lexically; this does not establish native path custody.

An optional COMPONENT_NATIVE inner publication has its distinct third UUID and
all16 exact role/path/cap correspondences within fixtures, at
`fixtures/publication_<fixture UUID>/<role>_<fixture UUID>.json`.
At most16 ordinary fixture auxiliaries and901120 bytes give a combined32/4MiB.
MODEL and Q reject populated fixture_publication. The currently mapped scenario
set is the explicitly native HB design IDs HB02/04/08/12/15/16/17/18/20/21, bound
to the frozen scenarios.json SHA256
`3157f7e0316bee6c141fac04d9794ebdf2550888d04de06d92423d0e7aa733a4`.
This is a source mapping, not native-scenario acceptance. SC-specific inner
fixtures and unmapped scenarios conservatively refuse pending an exact reviewed
successor mapping; all40 SC obligations remain open. Ordinary paths cannot use
a publication_ subtree. No role transfer, extra ledger or duplicate charge exists.

`verify_supplied_census` reparses original join bytes rather than trusting a
caller-constructed result. Its separate model schema
`cho51_hb1_supplied_census_v1` is capped at131072 bytes, with exact fields schema,
parent_operation_id, join_sha256, authority_sha256, producer_domain_sha256,
barrier and entries. The exact barrier is `{kind:"SUPPLIED_ONLY", sequence:
positive signed64 integer, producers_closed:true, lost_events:0}`. These are
declared facts, never an authenticated event domain or real producer seal.

There is exactly one entry per reservation. Each has path, state, actual_bytes,
native_identity, sha256, links and reparse. RESERVED_ABSENT/FAILED_ABSENT require
zero bytes and null remaining fields. PARTIAL/PRESENT/FAILED_PRESENT require
bytes within the reservation, a closed `{volume,file_id}` identity with nonzero
lowercase16/32-digit hex values, unique physical identity, a SHA256, exact integer
links=1 and reparse=false. Unknown, missing, extra, duplicate, copy, alias,
overflow and unjoined rows refuse. Empty/partial creates still count. A present
state with an asserted hash does not verify actual content or successful output.

Only after the complete supplied parent is conserved are disjoint main16,
optional NATIVE_FIXTURE16 and other views returned. All unused/failed charges
remain in totals. The result binds exact join/census digests and the fixed inner
scenario pin; it is MODEL_ONLY and cannot certify physical completeness. Actual
original domain/barrier/view evidence and independent preclaim two-pin approval
remain unavailable. This implementation cannot mint the acyclic authority/join
approval, consume a durable UUID, or act as SC1's positive operation_artifacts.

## Exact collection report

`baseline.py` contains immutable literal tuples for the accepted580 identities
and23 test-module byte pins, plus120 new HB identities and five test-module pins.
The accepted ordinal newline-terminated UTF8 digest of the original union is
rechecked. The full700 IDs/28 modules are exact: no caller-supplied expectation
can redefine them. Source-level enumeration establishes these literals only;
actual loaded-source observations and discovered test identities remain future work.

`collection.verify_collection` accepts at most1MiB of strict JSON, exactly schema,
complete, modules and tests, with schema `cho51_hb1_supplied_collection_v1` and
complete=true. Modules are ordered by name and have exactly module, bytes,
sha256, loader, load_tests and partial. Pins match the literal roster; loader is
`unittest.TestLoader.loadTestsFromModule`, load_tests=false, partial=false.
Tests are the full ordinal ID list; every row has exactly id, module, class_name,
method_name, source_module, source_qualname, skipped, deselected, expected_failure
and xfail. Each source
module/qualified name must match its declared original identity; all four flags
are exact false. Aliases, unknown modules,
equal-count substitutions, duplicates, omissions, order changes, hooks, partial
discovery, skips, deselection and expected-failure/xfail markings refuse.
Actual discovery, runtime attributes/decorators and import custody require a
separate reviewed collector and cannot be proven by this supplied report.

Only after complete report checking does the result expose the unchanged
32/100/384/10/19/35 partitions and all120 HB additions. The verifier selection is
64 existing plus120 new=184. The old384 collector is unchanged; no prefix filter
or relaxed count is installed. No outcomes are accepted and no executable runner
exists. The24 HB scenarios,40 SC scenarios,36 diagnostics,26 local qualification
scenarios,117 candidate cases and34 controls remain separate obligations.

## Review, preservation and next gate

Root and one active peer work locally; author ownership is declared before edits.
An independent read-only reviewer checks the frozen source candidate and sends
verbatim review text. Root alone publishes it in a predeclared slot, then binds
the reviewer's exact saved-byte confirmation in Root acceptance. A different
reviewer assesses final metadata/documentation closeout. Static source acceptance
does not qualify runtime behavior or approve admission. Source revisions after
freeze preserve affected drafts and receive new pins/review.

All source candidates bind this contract, the package, accepted design, path
helper and exact roster dependencies. No historical launcher is replayed and
the obsolete6566e348 watcher remains inert. Every original time, RAM, disk, CPU,
thread, hidden-device, startup/freshness, stop, Job/pipe/channel/handle ownership,
full final verification, partition/capture and cleanup rule remains in force.
Full Q still requires the complete32/100/384 cohorts in all eight modes and all
UTC/fault/native/bootstrap/sharing controls under their original bounded clocks.

Next is design/review of the finite component-model qualification runner and
its real source/runtime loading, capture/accounting and admission prerequisites.
The current checks cannot supply provider onboarding, native witnesses, durable
consumption or the asynchronous publication lifecycle. If these prerequisites
cannot be evidenced within unchanged guards, admission stays refused. Do not
infer a runtime window, reset a clock, split Q, shrink a cap or truncate evidence.
Complete-Q timing/output feasibility remains NOT_ESTABLISHED; P stays disabled.
