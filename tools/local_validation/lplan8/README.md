# lplan8 supplied-state frontier successor

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
