# Closed continuation state and conservation

## Authority and identities

The first implementation is a pure supplied-data kernel. It neither reads files
nor imports, parses or executes candidate/dependency sources. Its input is an
asserted finite static graph, not a proof that any actual source has that graph.
Its return always has `g2_complete:false`, `launch_authorized:false`,
`capabilities_accepted:false` and `status:INCOMPLETE_REFUSED`.

All values are closed JSON-shaped data: exact object keys, list/string/integer/
boolean/null types, bounded ASCII identifiers, lowercase SHA256, no floats,
duplicate identities, case-fold module collisions, unknown fields or implicit
defaults. Canonical encoding is sorted-key ASCII JSON with compact separators.
IDs are SHA256 of canonical tagged tuples, not Python object identity or a
runtime callable. A supplied digest must match the content it identifies.

An immutable binding names the algorithm version and the exact source, runtime,
specification, ordered-root and predecessor-evidence digests. Changing any one
requires a new reconstruction; it cannot resume or rebase an old checkpoint.
The kernel compares expected binding supplied by the admitted consumer; it
cannot authenticate that consumer or establish native custody itself.

The complete seed set is explicit. Each seed `(module, phase)` has a stable
requester ID, propagated unchanged downstream. Phases are L2, L3 or L4. Every
seed's package prefixes are explicit root facts, attributed to that seed.
Same-phase distinct requesters remain distinct. Root facts have explicit seed
links; requester identity is never replaced by an immediate import site.

## Immutable supplied graph and unresolved obligations

Each module template identifies its exact origin/source pin and retains its
complete ordered source records, including parent/scope/source-occurrence IDs,
lexical candidates, effects and unresolved constructs. Source records are
opaque preserved data to this kernel; interpretation and coverage belong to
the later producer/reconciler. There is no claim that this kernel verifies AST
completeness, source spans, export inference or Python semantics.

Outgoing edge templates retain source module, target module, source site, eager
or deferred epoch, conditional flag and import kind. They describe conservative
literal may-import relationships. Package-parent edges must be explicit;
attribute/submodule alternatives cannot silently become a resolved import.
Targets without a template remain pending-origin obligations, never emptiness
or proof of absence. Origin ambiguity, native images, unknown builtins/frozen
modules, dynamic calls, unproved exports, unsupported syntax and binding/effect
obligations remain unresolved. Deferred/conditional edges still propagate the
requester's phase as a may-reach fact and retain their guards on each link;
propagation never asserts actual execution, order, or reachability exclusion.

Every input obligation carries a stable kind, origin identity, complete payload
and digest. No operation in this kernel resolves or deletes one. Member/export
obligations and multi-phase legacy refusals remain present even after propagation
work is drained. Explicit future disposition requires a separately reviewed
proof-producing successor, not a changed status string in this kernel.

## Finite phase/requester worklist

A fact is `(module, phase, root_requester)`. A provenance link is either the
explicit seed link or `(source_fact, edge_id, target_fact)`. Facts deduplicate
only on that exact triple; links deduplicate only on that exact tuple. Do not
retain full paths: cycles would generate infinitely many paths. A diamond has
one shared fact per requester and both immediate predecessor links. A cycle
terminates after the finite fact/link sets stop growing.

Each new fact schedules one ordered work item. Its cursor starts at zero in the
module's immutable ordered edge list. One atomic transition advances one edge:
it adds the target fact and provenance link, schedules a previously unknown
target fact, and advances the source cursor. A zero-edge module finishes in one
transition. A missing target template becomes an explicit blocked work item;
it cannot be removed as completed. Late contexts always process cached edges,
even when another phase or requester already processed that module. No AST
reparse is needed for phase propagation. New module templates cannot be appended
to an admitted checkpoint in place; later integration must bind their complete
finite catalog at reconstruction or use a separately reviewed graph-extension
transaction. That extension is outside the first kernel.

The FIFO worklist, edge order and seed order are canonical. A step limit is a
yield boundary, not a refusal or proof of closure. Step-limited runs and a
single sufficiently large run on the same small finite graph must yield the
same facts/links/debts, irrespective of snapshot boundaries. Worklist emptiness
means only supplied-literal-context saturation; blocked missing origins prevent
that claim. SCCs are observations and never an initialization grant.

## Atomic bounded continuation

Every snapshot contains the entire immutable graph, every obligation, all facts
and links, every unfinished cursor and blocked item, cumulative counters, binding,
sequence and predecessor snapshot digest. No counts, Merkle roots, page hashes
or external references substitute for unavailable obligation payloads. Input
snapshot verification re-derives IDs, joins, counts, cursor ranges, worklist
completeness and reachable facts/links; it rejects injected facts, skipped edges,
fabricated completion and mismatched predecessor/binding. A caller must supply
the expected predecessor identity, not merely trust the snapshot's own hash.

Build a transition in temporary state, recheck every limit and publish all or
nothing. On capacity or stop/checkpoint refusal, the supplied predecessor is
unchanged. A capacity result may report that unchanged state and precise reason;
it cannot consume a cursor or omit its newly discovered obligations. Partial
serialization/writer failure has no committed successor. Publication uses
CreateNew and an index written last by the future host; an incomplete output is
failed-operation evidence only. A repeated or forked checkpoint never carries
an execution grant, and each runtime attempt still needs fresh admission.

Existing logical limits apply to the complete state across continuation, not
just the newly emitted delta: 128 modules, 16 MiB source, 2 MiB/module, 200,000
nodes, depth128, 24,000 rows, 10,000 edges, 100 pages, 16 MiB resolver output,
256 rows/page and 8 MiB/file. Rows include all source records, origins, seeds,
edge templates, obligations, facts, provenance links, pending/blocked items and
history entries. Source bytes/nodes count each module once; copying a record
does not make it new scientific evidence. Template edges plus provenance links
also share the 10,000-edge cap, a stricter finite allocation.

Additional finite kernel limits are 128 snapshots, 1,000 transitions per call,
and 16 MiB total canonical retained snapshot bytes over the whole chain. These
are restrictive bounds, not extensions. Every predecessor remains immutable;
its bytes count in history. No resetting counters, pruning obligations,
unbounded retry/chain, compressed debt summaries or delta-only cap accounting.
An oversized atomic transition is `CAPACITY_REFUSED`; continuation cannot fix a
logical ceiling. It may require a separately designed representation or a new
owner-approved contract. This design promises conservation, not G2 convergence
within current caps. The real P2 prefix may already leave insufficient capacity
for reconstructed contexts; a complete refusal is an acceptable engineering
outcome, not an accepted complete plan.

The host also retains P's shared 256-file/64-MiB output budget. Index, descriptors,
history and serialized payloads count before commitment. Budget refusal takes
precedence over publishing a supposedly resumable but incomplete snapshot.
