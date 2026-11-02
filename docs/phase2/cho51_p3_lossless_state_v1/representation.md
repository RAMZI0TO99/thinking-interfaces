# Exact transport format

This specifies `cho51_lossless_state_transport_v1`, a proposed supplied-byte
format. It does not change `cho51_supplied_frontier_v1`. The frozen kernel cannot
read this transport directly. A new reviewed consumer must decode it and prove
equivalence before treating it as a supplied kernel state. A future real-source
producer must additionally satisfy the full accepted reconciliation contract.

## Three identities, kept separate

1. **Physical identity:** exact bytes, length and SHA256 of each manifest/chunk.
   Runtime custody, when later implemented, adds fresh retained descriptors;
   hashes and historical NTFS identities do not establish that custody.
2. **Logical identity:** SHA256 of the exact canonical expanded kernel snapshot
   at each sequence, including graph, every retained frame, binding, predecessor
   and authority fields. This identity is unchanged by transport sharing.
3. **Historical identity:** index hash, page ordinal/hash, row ordinal/kind/hash.
   Distinct ordinals stay distinct even if their bytes or current targets match.
   Embedded binding/effect payloads remain in their complete owning rows.

The consumer receives an externally trusted expected manifest pin, expected last
logical snapshot digest, expected kernel binding, and the exact expected historical
family/index/page content pins. None is inferred from the untrusted manifest.
An empty historical expectation is permitted only for supplied synthetic scope;
it cannot represent a completed real-source reconciliation. Content expectations
are separate from fresh admission, source authenticity and scientific authority.

## Canonical data and closed manifest

Canonical encoding is exactly the frozen kernel's sorted-key, compact ASCII JSON
with `ensure_ascii=True`, no NaN/floats, exact bool/int distinction and signed
int64 payload integers. No duplicate keys, trailing material, unknown/missing
keys or type coercion. For graph/frame assets, decoding and re-encoding must be
byte-identical. Historical assets retain their exact original bytes, including
whitespace and line endings; interpreting their JSON never replaces those bytes.
FILETIME/int64 values must not pass through floating-point JSON.

The manifest has exactly these fields:

| Field | Value |
|---|---|
| `schema` | `cho51_lossless_state_transport_v1` |
| `binding` | Exact seven-field kernel binding; algorithm remains `cho51_supplied_frontier_v1` |
| `graph` | One graph asset ID |
| `frames` | Ordered array of 1..128 complete frame asset IDs |
| `history` | One descriptor per frame/prefix, in sequence order |
| `evidence` | Ordered historical family records; empty only for explicitly supplied-fixture scope |
| `assets` | Unique asset descriptors sorted by asset ID |
| `chunks` | Contiguous chunk descriptors in ordinal order |
| `status` | `INCOMPLETE_REFUSED` |
| `g2_complete`, `launch_authorized`, `capabilities_accepted`, `scientific_admission` | All exactly false |

A history descriptor is exactly `{sequence, predecessor, sha256, bytes}`.
Sequence is its zero-based position. The initial predecessor is null; every
later predecessor is the prior expanded snapshot digest. Its `sha256` and
`bytes` identify the complete expanded snapshot, never a delta or manifest.
Every frame has exactly the accepted `steps`, `retained_before`, `facts`,
`links`, `work` fields. Complete frames are retained; no delta journal is used.

A historical family is exactly `{family, index_asset, page_assets}`. Family is
`resolver` or `inventory`, at most one of each, ordered resolver then inventory.
Each page array is in the authenticated index's descriptor order. The expected
family set, exact index hash and exact page descriptors come from the caller's
independent input contract. Missing an expected family, an extra family, or a
changed page order refuses. The real retained case has 74 resolver pages and 53
inventory pages. Ordinals are not collapsed when multiple slots refer to equal
raw bytes. Every row address and embedded debt is derivable from the retained
exact file bytes and validated page structure; counts never replace payloads.
Historical path strings inside indices are data, not instructions to open files.

## Assets and finite byte chunks

An asset descriptor is exactly `{id, kind, bytes, sha256, parts}`. Kind is
`graph`, `frame` or `raw`. Length is a positive integer at most 8 MiB. Asset ID
is SHA256 of canonical `["asset", kind, bytes, sha256]`. Different kinds never
share identity. Identical same-kind bytes may be stored once, but every graph,
frame or historical use remains in the ordered manifest. Encoding must compare
actual bytes before sharing; a hash match alone cannot justify collapsing
different supplied bytes. Decoding verifies all bytes against the trusted pins
under the same SHA256 integrity assumption as existing evidence.

The graph asset contains exactly the complete accepted graph object. Each frame
asset contains one complete accepted frame. A raw asset contains one exact
historical index/page file. These assets cannot reference each other internally
as a substitute for payload. Graph payloads are real nested JSON, not asset IDs
standing in for records, exports, source spans or obligations.

Assets are concatenated in lexicographic asset-ID order into a byte stream, then
cut at 1 MiB boundaries. Every non-final chunk is exactly 1 MiB; the last has
1..1 MiB. No compression, dictionary expansion, recursive references, filesystem
links or external fetches. At most 64 chunks, 512 assets and 1,024 parts provide
additional finite bounds; all existing tighter limits still apply.

Each chunk descriptor is exactly `{ordinal, bytes, sha256}`. Each asset part is
exactly `{chunk, offset, bytes}` and denotes a positive-length range in a chunk.
Its ordered parts must be the **unique** ranges obtained by slicing that asset's
position in the sorted concatenation. Verify the full partition: no gaps, overlap,
extra bytes, alternate slices, omitted chunks or unreferenced assets/chunks.
References go manifest -> asset -> chunk only, so reference cycles are impossible.
Graph/frame/raw kinds must match every use. Identical asset IDs cannot occur twice
in the descriptor table, while a frame or historical *use* may repeat only where
the semantic replay or exact historical index permits that repetition.

The manifest itself is canonical JSON, at most 8 MiB. All descriptors and indices
are bounded before allocation; arithmetic is checked and overflows refuse.
Physical file names, when a later host exists, are generated solely from the
validated ordinal (`data-000.bin`, etc.) and a fixed manifest name in the owned
unused output directory. No payload-provided path may choose a read/write target.
The transport uses at most 65 data/manifest files, but shares the original P
256-file budget with every other artifact. Its full bytes and wrapper overhead
share the state 16 MiB and P 64 MiB budgets as defined in [capacity.md](capacity.md).
Those limits may refuse far below the descriptor-count maxima.

## Losslessness and semantic multiplicity

Concatenating each asset's exact parts recovers its exact bytes. Decoding a
canonical graph/frame and constructing prefix `i` with the frozen snapshot
constructor recovers the same graph, all frames 0..i, immutable binding,
sequence, predecessor, fixed false authority flags and saturation expression.
Canonical encoding then recovers the exact prefix bytes and digest. Independently
returning each raw asset recovers the original index/page bytes. Both round trips
are required; semantic JSON equality alone is insufficient for raw evidence.

No separate caller-supplied multiplicity table is authoritative. It is derived
from all ordered uses and prefix inclusions. Every graph/base row is charged once
per retained snapshot, and frame `i` is charged in every prefix containing it.
Equal bytes at two historical ordinals or frame positions remain two logical
uses. A repeated physical asset cannot reduce that charge. The verifier also
retains all originally supplied evidence uses even if a new producer relates
several of them to the same current source fact.

The format preserves supplied bytes; it cannot prove an asserted graph covers
real sources. An asset's presence is not a reconciliation result. For real use,
the producer must supply the exhaustive ledgers, current-only occurrences and
complete payload witnesses required by the accepted reconstruction design,
under matching reviewed schemas and the same whole-state limits. No such producer
schema, implementation or complete real-data mapping is accepted by this format.
