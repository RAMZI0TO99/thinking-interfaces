# lplan14 fixed supplied-byte probe successor

This implementation candidate preserves the complete 130,326-byte executed
lplan10 compiler as an exact prefix and appends a fixed non-resumable source
observer. LP17/LQ17 integrate exact384/100/32 cohorts (516 distinct methods).
Earlier accepted sources and all failed/unknown receipts remain frozen. Source
review and fresh Q remain required; operational P is disabled.
This successor retains the lplan5 inventory and migration interfaces and adds a
bounded, non-executing lexical/import/effect observation. It consumes supplied
physical records and an injected parser scope. The index always reports
`INCOMPLETE_REFUSED`, `g2_complete: false`, and no launch authority. A literal
import graph fixed point, when reported, is not an effect or host qualification.

The compiler extracts a closed content pin for reader calls and retains full
native descriptors separately. Comprehension assignment expressions and Python
3.12 annotation/type-parameter scopes carry explicit refusals. Multiple phase
joins carry all discovered contexts and refuse graph closure. Publication is
refused before any page or index is written if the complete frontier and queue
do not fit the resolver output envelope. The row limit applies to every published
node, origin, edge, frontier and queue row. Full node inventories preserve parent
and scope joins. A 512 KiB index reserve is conservative;
a sufficiently small output limit may therefore refuse even a small input.

Source review identified RSL-01 through RSL-05 in the preserved draft. These
revisions and the 40 supplied-byte ResolverTests require fresh independent source
review and separately admitted qualification; no test or runtime result is
claimed. Candidate imports, native effects, ABI, capability joins, L, V and
science remain outside this source-only step. Multi-phase graph traversal is not
qualified: the implementation explicitly refuses such joins instead of claiming
their transitive resolution.

## Supplied frontier API

`frontier_start(binding, graph, checkpoint)` returns an initial checkpoint.
`frontier_continue(snapshot, expected_digest, expected_binding, steps,
checkpoints, checkpoint)` returns a closed result with `result`, `reason`, and `snapshot`.
The results are `ADVANCED`, `NO_WORK`, `CHECKPOINT_REFUSED`, and
`CAPACITY_REFUSED`. Refused/no-work results contain an independent copy of the
unchanged predecessor. Invalid input raises `Refusal`. `expected_digest` is the
caller-retained SHA256 of `encode(snapshot)`, not a value read from the
snapshot. The caller must obtain and retain this identity separately; the
kernel does not authenticate callers. `steps` is an integer from 1 to 1,000,
and `checkpoints` contains exactly that many booleans. Any false value refuses
the entire call. A completed transition that exceeds any limit also refuses
the entire call, including earlier transitions in that call. A call can advance
fewer steps when no runnable work remains.

All object schemas below are exact; unknown and missing keys are rejected.
Integers exclude booleans, floats are rejected, hashes are lowercase 64-digit
SHA256, and module names are ASCII dotted identifiers. Tokens have 1–256 ASCII
letters, digits, underscores, dots, slashes, colons or hyphens. Lists retain
their supplied order. Data payloads are opaque bounded JSON trees: null,
booleans, signed 64-bit integers, strings, lists and dictionaries with nonempty
ASCII keys. Their content is preserved but not interpreted as Python source,
AST, source coverage, exports, or effects. A conservative structural byte
budget and nesting bound can refuse inputs below the nominal serialized limit.

`binding` has exactly `algorithm`, `source`, `runtime`, `spec`, `roots`, `seeds`,
and `predecessor`. The algorithm is `cho51_supplied_frontier_v1`; the other
values are hashes. `seeds` must equal `digest(encode(graph['seeds']))`, binding
the ordered seed records. `roots` is the separate asserted ordered-source-root
digest. These external source, runtime, spec, roots and predecessor-evidence
pins are compared exactly on every continuation; their underlying evidence is
not independently verified by the kernel.

`graph` has exactly `modules`, `seeds`, and `obligations`, each an ordered list:

* A module has `name`, `origin`, `source_bytes`, `nodes`, `depth`, `records`,
  and `edges`. `origin` is exactly `{identity, sha256}`; its identity is a
  token and its hash is an asserted source pin. Counts are nonnegative
  integers, and `nodes` must cover the number of records. A record is exactly
  `{id, payload}`, where `id = frontier_id('record', name, zero_based_index,
  payload)`.
* An edge has `id`, `target`, `site`, `epoch`, `conditional`, and `kind`.
  Target is a module name, site and kind are tokens, epoch is `eager` or
  `deferred`, and conditional is a boolean. Its id is
  `frontier_id('edge', source_name, target, site, epoch, conditional, kind)`.
  Repeated edge identities are rejected; all flags remain on the immutable
  template and each edge link refers to that exact id.
* A seed has `id`, `module`, `phase`, and `prefixes`. Phase is `L2`, `L3`, or
  `L4`; prefixes are the exact ordered package prefixes including the full
  module (for `a.b`, `["a", "a.b"]`). Its id is
  `frontier_id('seed', module, phase, prefixes)`. Duplicate module/phase seeds
  are rejected. Every prefix is attributed to that seed as requester.
* An obligation has `id`, `kind`, `origin`, and `payload`; kind and origin are
  opaque tokens and the id is `frontier_id('obligation', kind, origin,
  payload)`. Its payload must be an object with at least one non-null field
  other than `id`, `digest`, `sha256`, `ref`, `reference`, `path`, `uri`,
  `bytes`, or `size` (case-insensitive). This rules out common reference-only
  forms; opaque input cannot prove that a field is semantically complete. An
  origin token may name unresolved external evidence, so it is not
  treated as a resolved join to a module. Duplicate obligation ids refuse.

`frontier_id(tag, *values)` hashes the compact, ASCII, sorted-key encoding of
`[tag, *values]`; tags are lowercase ASCII identifiers. `digest` hashes bytes,
and `encode` is the existing canonical JSON encoder. Case-fold collisions
across module names, edge targets and seed prefixes are rejected. Missing
module templates remain blocked work items. New templates require a fresh
construction; a checkpoint cannot be extended in place.

Each checkpoint has `schema`, `binding`, `graph`, `frames`, `status`,
`g2_complete`, `launch_authorized`, `capabilities_accepted`, `saturated`,
`sequence`, and `predecessor`. Sequence starts at zero and increments once per
committed successor; its predecessor is null initially and otherwise the SHA256
of the complete canonical previous snapshot. This snapshot predecessor differs
from the immutable predecessor-evidence hash in the binding.
Status is always `INCOMPLETE_REFUSED` and the three authority flags are always
false. Saturated means only that the supplied worklist is empty, including no
blocked items. Each frame has cumulative `steps`, `retained_before`, ordered
`facts`, ordered `links`, and ordered `work`. A fact is
`{id, module, phase, requester}` with id `frontier_id('fact', module, phase,
requester)`. A seed link is `{id, kind: 'seed', source: seed_id, edge: null,
target: fact_id}`; an edge link has `kind: 'edge'`, source fact id, edge id,
and target fact id. Link id is `frontier_id('link', kind, source, edge,
target)`. A work item is `{fact, cursor, blocked}`. Work is FIFO, except that
blocked entries remain in place while later runnable items proceed. A
zero-edge template consumes one transition. Edges propagate phases and root
requesters regardless of epoch or condition; links describe conservative
may-reach relationships, not execution.

Every predecessor frame is retained. Verification reconstructs the initial
frame and replays each frame's cumulative transition difference, checks every
intermediate capacity and compares the entire frame. It recomputes predecessor
byte accounting over canonical prefix snapshots and checks the external digest,
binding, fixed authority flags, work state and saturation. Up to 128 snapshots
and at most 1,000 transitions per committed call imply at most 127,000 replayed
transitions. The complete retained copies count against the existing row,
edge, page, output and history caps; the complete canonical current snapshot is
also restricted to 8 MiB. The accounting is deliberately conservative, and a
capacity refusal is not evidence that a different representation fits.
`retained_before` is the sum of canonical byte lengths of all earlier snapshot
prefixes. Nothing in this API reads files, parses, imports candidates, writes
checkpoints, authorizes a host capability, or discharges an obligation. A
future host must separately implement and review atomic publication and shared
file/storage budgets. This source has not been executed or accepted by review.

## Static scenario inspection and limitations

This is the author's inspection, not independent review or executed evidence.
FC01–FC05 are addressed by closed graph/binding/checkpoint fields, exact scalar
checks, content ids, collision checks, replay and the externally supplied
digest. FC06–FC14 are represented by explicit seed prefixes, root-requester
facts, retained immediate links, template guards, blocked work, immutable
obligations and permanently false authority flags. FC15–FC17 are addressed by
deterministic FIFO replay and transactional refusal. FC18–FC21 count graph,
work and repeated retained frames conservatively, with source and per-file
ceilings and finite call/chain limits. FC22–FC24 are checked by exact canonical
frame replay and comparison of the supplied binding and predecessor digest.
FC25–FC28 use a live checkpoint plus preflight booleans, canonical
serialization, supplied-only inputs and returned deep copies. FC29–FC32 retain obligation
payloads, refuse common reference-only forms, bound oversized inputs, retain
blocked items, and fix the authority fields.

These observations do not establish that tests pass. In particular, a generic
opaque payload cannot prove the factual completeness or authenticity of the
supplied graph or an obligation; the reference-only check is structural, not a
semantic proof. Limits are intentionally stricter than their stated upper
bounds because all retained copies and a conservative structural byte budget
are counted. JSON serialization/deserialization is used solely for canonical
data and deep copies; there is no candidate-source parser or import surface.
The boolean checkpoint list is an assertion supplied before a call. The separate
trusted, zero-argument live `checkpoint` callable is sampled during validation,
replay, payload traversal, capacity checks and before transitions; it must
return the singleton `True`. False, other values, a missing/non-callable guard,
or an exception raises `FrontierCheckpointRefusal` (a `Refusal`), without
committing a successor or mutating the caller's snapshot. The trusted guard
must not mutate its inputs. An explicit false in the boolean list instead
returns `CHECKPOINT_REFUSED`; capacity exhaustion returns `CAPACITY_REFUSED`.
Real stop controls, process ownership, storage publication, P integration, and
acceptance remain separate host work; a callback fixture does not qualify them.

## Supplied lossless transport (unreviewed source)

`pack_supplied_chain(snapshot, raw_evidence, allocation, checkpoint)` returns
`{manifest: bytes, chunks: list[bytes]}` or raises `Refusal`.
`verify_supplied_bundle(bundle, expected_manifest_pin, expected_digest,
expected_binding, expected_evidence, allocation, checkpoint)` returns the
closed `cho51_lossless_verification_result_v1` outcome. The caller supplies all
expected identities independently. A live guard failure raises
`LosslessCheckpointRefusal` and produces no result.

`raw_evidence` is a list, in resolver then inventory order, of exactly
`{family, index: bytes, pages: list[bytes]}`. `expected_evidence` is the same
ordered family list with `{family, index: {bytes, sha256}, pages:
list[{bytes, sha256}]}`. Empty lists designate synthetic supplied scope only.
Each index must name all supplied pages in order with frozen native descriptor
and matching content pins. Raw file contents retain their original line endings
and whitespace. Index path strings are checked as data; no path is opened.
Manifest, asset, chunk, family and history fields follow the accepted v1 design.

`allocation` is required and exactly `{resolver_bytes, resolver_pages, p_bytes,
p_files}` of nonnegative exact integers. Each represents all other claimed
outputs, including provisional records; for a synthetic isolated fixture the
caller explicitly supplies zeros. The transport's manifest and chunks are
added to each applicable ledger and checked against the existing 16 MiB/100
page and 64 MiB/256 file caps. This is a caller assertion only: it does not
measure other outputs, native handles, custody, or actual P allocation.
The P ledger includes all other resolver outputs: `p_bytes >= resolver_bytes`
and `p_files >= resolver_pages`. To bound supplied input work, the sum of
every raw index/page use, including repeated references to identical bytes,
plus the respective other-output byte ledger must fit the 16 MiB/64 MiB
limits. This is a conservative additional input refusal: it can reject a
bundle whose deduplicated physical transport would fit. Repeated permitted
uses retain their order and multiplicity; the condition does not replace the
separate physical transport, expanded snapshot or history charges.

### Frozen transport schemas

Every object below has exactly the listed keys. Ordered lists preserve every
ordinal use; assets alone are deduplicated by equal same-kind bytes. A collision
between unequal bytes refuses. SHA256 values are lowercase 64-digit strings;
integers are exact signed int64, excluding booleans. Pins are `{bytes,sha256}`,
with positive byte lengths up to 8 MiB. Canonical JSON uses the inherited
`encode` format. Raw historical JSON can retain whitespace and CRLF.

| Object | Exact keys and constraints |
| --- | --- |
| Manifest | `schema,binding,graph,frames,history,evidence,assets,chunks,status,g2_complete,launch_authorized,capabilities_accepted,scientific_admission`; schema `cho51_lossless_state_transport_v1`, status `INCOMPLETE_REFUSED`, all four flags false; graph is a graph asset ID; frames contains 1–128 ordered frame asset IDs; history has the same count; evidence has 0–2 ordered families |
| Asset | `id,kind,bytes,sha256,parts`; kind graph/frame/raw; positive bytes <=8 MiB; id is SHA256 of canonical `["asset",kind,bytes,sha256]`; at most512 assets, sorted strictly by id |
| Part | `chunk,offset,bytes`; exact nonnegative chunk/offset and positive bytes; at most1,024 parts in total; canonical concatenation fills each chunk before advancing, with no gaps, overlap, alternate split or unused bytes |
| Chunk | `ordinal,bytes,sha256`; ordinal is its zero-based list position; chunks are 1 MiB except the nonempty last chunk; at most64 chunks |
| History | `sequence,predecessor,sha256,bytes`; sequence is the zero-based prefix position; predecessor is null initially and otherwise the exact previous canonical prefix digest; bytes/hash identify the entire expanded prefix |
| Evidence family | `family,index_asset,page_assets`; family resolver/inventory, in that order without duplicates; index_asset and each ordered page asset must have kind raw; at most100 page uses per family |
| Result | `schema,outcome,reason,checks_completed,logical_digest,snapshot,g2_complete,launch_authorized,capabilities_accepted,scientific_admission`; schema `cho51_lossless_verification_result_v1`; outcome `VERIFIED_SUPPLIED_STATE`, `INVALID_INPUT`, or `CAPACITY_REFUSED`; successful reason null; refusals have null snapshot/logical_digest and name only completed checks |

Completed checks are appended in order: `external_and_allocation`,
`transport_partition`, `historical_content`, `expanded_replay`. Guard failures
raise `LosslessCheckpointRefusal` and return no outcome. Ordinary malformed
inputs produce `INVALID_INPUT`; capacity predicates produce `CAPACITY_REFUSED`.
Packing raises `Refusal` for either and returns a bundle only after verification.

### Historical row validation

Both indices/pages use their exact closed emitter schemas in `compiler.py`.
Every native page descriptor has `schema,path,native_identity,file_type,
reparse_point,link_count,bytes,sha256`; the identity has
`schema,volume_serial,file_id,volume_kind,filesystem`. Only regular, single-link,
non-reparse local NTFS/ReFS descriptors are accepted. Nonzero fixed-width native
identities, safe absolute page paths, distinct path/identity slots and exact
externally supplied content pins are required. These are historical data checks,
not retained handles or physical custody.

All inventory nodes have exactly `id,parent,path,scope,kind,span_utf8,
raw_span_sha256,epoch,module,source,scope_parent,shape_sha256,context,analysis,phase`.
Resolver nodes replace the last five inventory-only fields with
`scope_kind,conditional,resolution,capability`. IDs are recomputed from
`[module,source.sha256,path]`; parent paths, source pins, module roots, scope
owners/ancestry and binding targets must join complete retained rows. Inventory
epochs include `unknown`; resolver epochs are eager/deferred. Inventory analysis
is unresolved; resolver capability is pending. Equal inventory rows can occur at
multiple ordinals and remain separately counted; differing rows under the same
identity and duplicate resolver node identities refuse.

Resolver node additions are closed by kind: Global/Nonlocal add
`binding_kind,names`; FunctionDef/AsyncFunctionDef/ClassDef/arg/Name add
`binding_kind,name`; alias adds `binding_kind,name,alias`; Name Load adds
`binding_candidates` and may have `import_candidate`; Call adds
`lexical_targets,import_candidate,runtime_binding_proven` (always false), and may
have `possible_dynamic_effect`. The observer's exact per-kind effect value is
required where applicable. Only its enumerated refusal reasons are accepted.
These fields preserve supplied lexical candidates and effects, without proving
their real source meaning.

The exact retained generator effect is `generator_protocol`; unresolved lexical
debt includes `multiple_bindings`, and resolver node epochs retain
`future_annotation_unknown`. These values do not grant execution or change the
kernel's separate edge-epoch contract. Native extension-origin pins describe
image sizes with exact nonnegative int64 metadata bounds and exact descriptor
joins; source/package byte limits and transported asset/output ceilings remain
unchanged. LS10 includes supplied-row/descriptor regressions for these four
source-review corrections and malformed near misses. The preserved first
candidate and independent findings remain in the predecessor phase's `draft-v1`
and `source-findings-v1.json`; this fixture successor is still unexecuted.

Resolver non-node rows are exactly: origin
`kind,module,phase,origin,via,capability`; edge
`kind,from,to,site,phase,epoch,conditional`; queued
`kind,module,phase,via`; frontier `kind,reason` plus the emitter's reason-specific
module/site/detail/candidate/base/member/other/contexts/limit fields. Origins
have exact per-kind schemas: builtin/frozen `kind,module`; file origins add
`path,pin,physical_descriptor`; missing/namespace origins retain `paths` when
emitted; parent_unresolved adds its complete recursive `parent`. No unknown
keys, packed records, digest-only replacement or arbitrary reason is accepted.
Origin/source, site, phase, epoch, conditional, queue-via and component joins are
checked. Index counts, embedded binding/effect counts, ordered frontier/queue
digests, source-origin digest, graph_fixed_point and capacity-frontier joins are
recomputed. Inventory diagnostics and migration references also have closed
schemas; no referenced path is opened.

### Guard sampling and allocation

The byte parser samples its live callback at most64 KiB of explicit byte
traversal apart, and at value/string boundaries. It rejects floats, duplicate
keys, trailing material, excessive depth, per-container counts over24,000 and
strings over65,536 characters. This is not a total JSON-node-count claim.
The codec's canonical encoder traverses values with callbacks, escaping at most
4,096 characters per library call and encoding/hashing bounded blocks. UTF-8
segments are at most64 KiB. No newly added canonical serialization first builds
an unbounded complete string token.

Some finite library primitives remain indivisible: sorted bounded key lists,
string joins (at most65,536 characters), final buffer/asset joins (at most8 MiB),
chunk copies (at most1 MiB), and comparisons of bounded buffers. They have guard
samples before/after, not continuous observation. The inherited kernel's
canonical encoder/deep-copy primitives remain byte-for-byte unchanged; their
structural/capacity preflight and before/after guards remain effective.

Before parsing graph/frame copies, the decoder checks necessary raw canonical
asset lower bounds for the entire current snapshot and weighted retained
history. Repeated asset references count repeatedly in those bounds. Each frame
also gets structural validation; full prefix/intermediate canonical accounting
and replay remain authoritative. The packer checks structure/expanded capacity
before canonical buffers and checks cumulative unique content and projected
file ledgers before chunk construction. Historical resolver row accumulation is
bounded before extending the retained list. None of these preflights replaces
the final whole-allocation or expanded-history guards.

### Static coverage and remaining qualification

All28 named `LosslessTests` methods remain unexecuted. LS03 retains fully shaped
raw inventory bytes with CRLF and int64; LS09 preserves two equal256-row page
uses. LS10 exercises complete resolver bindings/effects plus schema/count/join
tampering. LS04 injects an asset-ID collision and rejects cross-kind aliasing.
LS07 crosses1 MiB and probes one actual8 MiB JSON input boundary/one-over case.
It does not build a valid8 MiB graph/frame or manifest, or valid maximal
512-asset/1,024-part/64-chunk bundles; tighter whole-output bounds make some
maxima unreachable. LS11 compares canonical prefix bytes/hashes with the
unchanged inherited encoding, including9,999/10,000 retained-before widths.

LS13 tests nominal24,000/24,001 row and10,000/10,001 edge counter boundaries
through the unchanged lower-level capacity function, not valid reconstructed
graphs. Logical100 pages is unreachable under24,000 rows and256 rows/page;
physical100/101 page allocation is exercised in LS24. LS14 exercises repeated
frame pre-expansion refusal under a reduced history cap. Other full-size
snapshot/history, structural and source/count boundaries use inherited or
reduced-limit fixtures. LS17 has an endpoint-valid35-row two-step fixture whose
first replay transition needs36 rows and refuses under a35-row cap. LS21 covers
byte/hash/encoding/parser/replay and final-return guard refusal/exception, not
every possible callback position.

LS23 uses lower-level multiplicity counters for15,501-base first-successor and
28,892 combined-record refusal; its placeholder lists are expressly not valid
source graphs, AST reconstruction or real-case evidence. LS26 tests malformed
historical page paths as inert data. LS27 tests the exact new100 roster;
`lq17.test_protocol.ProtocolTests.test_complete_window` and
`test_report_omissions_failures_and_false_authority` plus child roster checks
separately cover admission/report integration. LS28 invokes the preloaded LP17
main refusal and confirms its inherited384+40 library consumer rejects the
lossless aggregate schema; it cannot accept this phase's results.

Distinct source review and fresh admitted validation remain required. Native
publication, retained handles, crash/cleanup, actual result review and real-source
reconciliation remain separate host/real-case work. No method establishes real
coverage, real-case fit, custody, G2, host capability, candidate/V execution or
scientific admission. Operational P remains disabled.

## Fixed supplied-source observation (implementation candidate)

`observe_selected_source(request, raw_source, raw_index, raw_page, checkpoint)`
accepts only the independently fixed packaging case. It returns a pure result;
its report schema is `cho51_source_probe_report_v1`. The supplied fixture is
`source_probe_fixture()` in `test_compiler.py`; it embeds the exact full source,
index and page and performs no ambient read. It must be called by a separately
admitted, guarded child. A `SourceProbeCheckpointRefusal` returns no result.
No production selector can adopt altered pins. No output is a checkpoint or
P grant. This source has not been executed or independently reviewed.

The 32 RS methods are candidate tests, not completed qualification. RS05 and
RS12–14 use mutated bounded structures with private helpers; they do not give a
production selector a variable pin. RS20 constructs complete syntax records at
the local source, depth and node limits. RS21 uses complete encoded data at the
report byte limit and one byte beyond. RS18 tests state and lossless refusal;
other consumers require integration controls. RS22/23 exercise partition
counters and account for repeated fixture bytes, but cannot prove the physical
writer's treatment of every temporary, failed or receipt file. RS24 samples
selected callback positions and operations, not every possible callback
position. RS27/28 test result validation and false custody fields; actual
caller/cleanup and historical custody proof require outer integration controls.
RS30 tests exact probe/lossless method rosters and cohort classification using
384 synthetic inherited identities; the actual inherited roster needs separate
integration verification. RS31 is a numeric guard check, not a valid reconstructed
full-state witness. RS32 checks authority fields and P supervisor refusal;
aggregate behavior requires integration controls. No test claims source review,
actual execution, cleanup, acceptance or debt discharge.
SP-01 source review found a missing final live sample on ordinary refusal.
The candidate now samples before every refusal return; RS24 arms faults after
scope/pin/capacity detection and after successful final encoding. RS11 also checks
a multibyte UTF-8 literal span. Both corrections preserve the inherited compiler
prefix. The original reviewed draft and finding remain in the phase records.

The Q parent retains the exact raw fixture bytes, fixed selector, full report and
provisional receipt using its original native writer. Output reservations include
failed/provisional writes and duplicate frame payloads; no side allocation or
P/state consumer is enabled. See the pinned phase contract for the complete
three-cohort and whole-operation allocation boundaries.

SP-02 extends live guard propagation to raw-asset transport. Hex encoding and
decoding/hash traversal sample bounded parts, and the final bounded copy is
sampled on both sides. RS23 exercises every checkpoint in the fixed transport,
missing/nonboolean/faulting guards and altered raw bytes. Production callers
must supply the actual Q guard; no implicit success callback is installed.

The LP15/LQ15/lplan12 probe attempt exhausted the existing child deadline before
a complete result frame. It remains failed and consumed; no test result or
specific in-child location is inferred. This successor removes a redundant
post-parse JSON walk and unnecessary one-piece string joins. JSON parsing checks
the actual live guard every16KiB consumed bytes or128 values, before/after the
parse, around large UTF-8 decodes and multi-piece joins. The accepted64KiB byte
bound, every-AST-occurrence/comparison checks and final/refusal guards remain.
RS07 retains all strict JSON rules and covers both byte and value budgets.
This is a source-level performance hypothesis until fresh Q and actual review.

LP16's later d26ee8c7 attempt returned32 passing probe tests and all six raw/report
artifacts, but failed a later native control at the unchanged session deadline;
the whole operation and its provisional observation remain unaccepted. This
successor gives only the pure probe encoder an ordinary cumulative16KiB output /
128-value budget, with separately guarded escape-output blocks up to49152bytes,
instead of calling the live sensor for every punctuation token. Larger escape
calls, key sorts and final immutable copy retain before/after samples. Canonical
ASCII JSON, original depth/container/string/int64/output limits, final/refusal
guards and the complete inherited codec remain unchanged. RS21 compares exact
bytes against the inherited encoder and stdlib canonical JSON, including Unicode,
strict refusals and every checkpoint of a bounded dense-value fixture.
