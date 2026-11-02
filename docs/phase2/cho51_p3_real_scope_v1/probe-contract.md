# Fixed source-observation contract

Design interface only; implementation must use a new version and source review.
There is no operational file reader or writer in the pure probe API.

## Inputs and closed schemas

`observe_selected_source(request, raw_source, raw_index, raw_page, checkpoint)`
accepts only supplied immutable bytes and a trusted live guard. The caller
independently supplies the reviewed request; input bytes cannot choose their
own expected pins. No filesystem/network discovery, candidate import, eval,
exec, source-code execution, native loading or follow-up import is permitted.
AST parsing by the pinned trusted interpreter is allowed only in a future
admitted Q child; filename is an inert diagnostic label.

All object keys below are exact; missing/extra keys refuse. All integers are
nonnegative exact integers (no bool/float); hashes are lowercase 64-digit SHA256.
Identifiers are fixed literals or bounded ASCII, paths are inert data. A Pin
is exactly `{bytes, sha256}`. JSON is strict UTF-8 with duplicate keys, floats,
nonfinite numbers, trailing bytes, excessive depth or oversized values refused.
The fixed case requires exact source/index/page pins from the reviewed static
case; no caller-specified larger limits are accepted.

JSON metadata integers remain signed-int64 bounded (with nonnegative values
where specified); every container has at most4096 entries, nesting depth32 and
strings at most65536 characters before tighter field checks. Observed field paths
are ASCII of at most1024 characters, kinds at most64 ASCII identifier characters,
and node/parent identifiers are SHA256 strings (root parent null). Coordinates
are null or exactly four nonnegative integers with positive line numbers and
validated byte offsets. Each report list has at most128 entries. All selected
ordinals and fixed-case comparison counts remain exact, not merely below caps.

| Object | Exact keys and meaning |
| --- | --- |
| Request | `schema, case_id, module, source_pin, index_pin, page_pin, page_ordinal, selected_ordinals, global_resolver_rows, global_inventory_rows, desired_product` |
| Request constants | schema `cho51_source_probe_request_v1`; case_id `packaging_source_v1`; module `packaging`; page54; ordinals176..213 in order; counts18793/13406; desired_product `syntax_observation_only` |
| Syntax observation | `id, parent, path, kind, span_utf8, raw_span_sha256` |
| Comparison | `page_ordinal, row_ordinal, historical_id, observed_id, outcome, compared_fields` |
| Comparison constants | node comparisons only; outcome `SYNTAX_FIELDS_EQUAL` or `SYNTAX_FIELDS_DIFFER`; compared_fields exactly the six syntax keys above |
| Report | `schema, case_id, source_pin, index_pin, page_pin, selected_ordinals, observations, comparisons, origin_pin_equal, selected_syntax_equal, global_scope, authority` |
| Global scope | `resolver_rows, inventory_rows, selected_rows, unselected_resolver_rows, obligations_discharged, global_ledger_mutated` with18793,13406,38,18755,0,false |
| Authority | `resumable, exhaustive_reconciliation, complete_dependency_closure, g2_complete, launch_authorized, capabilities_accepted, scientific_admission, historical_custody_closed, current_p_custody_refreshed`, all false |
| Pure return | `schema, outcome, reason, checks_completed, report`; schema `cho51_source_probe_result_v1`; outcome `OBSERVED_SELECTED_SOURCE`, `REFUSED_INPUT`, `REFUSED_CAPACITY` or `REFUSED_SCOPE` |

Successful reason is null. Refusals have null report and a closed reason code;
allowed reasons are `schema`, `pin`, `selection`, `historical_membership`,
`source_encoding`, `parser`, `span`, `duplicate_identity`, `bound`,
`unsupported_product`. Guard failure raises a distinct
`SourceProbeCheckpointRefusal` and returns nothing; no refusal summary
fabricates success or completed checks. Checks complete in the fixed order
`request_and_pins`, `historical_membership`, `syntax_observation`,
`selected_comparison`, `final_guard`. Only actually completed checks appear.
A syntax mismatch is an observed bounded discrepancy, not source eligibility.
Exact source-pin mismatch refuses the fixed case rather than silently accepting
drift or selecting another source; the original and supplied bytes stay in the
failed attempt's bounded owned evidence if safely retainable.

## Deterministic comparison

Verify complete source/index/page byte lengths and SHA256 before parsing. Inspect
the exact historical page schema and full index as bounded data. Check the
page54 descriptor's content pin, the selected exact ordinals and original
origin/node fields. Retain unknown/uncompared semantic fields in the full raw
page; do not rewrite them into an apparently approved schema. This checks
selected membership only, not the full resolver index/queue/component closure.
Do not pass a partial family to the existing lossless codec: that verifier
requires every historical page and must continue to refuse missing pages.

Parse the complete supplied source once into an AST in `exec` mode without
executing it. Traverse in preorder using `ast.iter_fields` field order and list
indices, including context/operator AST occurrences. Root path is `$`; append
`/field` or `/field:index`. Node ID is SHA256 of compact ASCII sorted-key JSON
`[module, source_sha256, field_path]`, as in the retained resolver.
Parent is the immediately enclosing AST occurrence ID; root parent is null.
Kind is the exact AST class name. Compute UTF-8 byte spans and hashes with the
retained resolver's BOM/CRLF-aware rule; a node lacking any coordinate has both
span and span hash null. Invalid positions refuse. Depth, node and output caps
apply before retaining additional records. Observe every current node, including
current-only nodes; do not truncate to the historical count.

The 37 selected historical node tuples must be unique and joined by exact
(module, source SHA256, field path), never name/kind/line alone. Return every
bounded observation, and exactly one comparison per selected historical node.
A missing observation has null observed_id and `SYNTAX_FIELDS_DIFFER`; an
extra current node keeps selected_syntax_equal false. Duplicate current
identities refuse. The historical origin is retained in the raw page and checked
only for its source content pin; the descriptor's native identity is historical
data and cannot prove new custody. No origin-row comparison is a syntax node.
selected_syntax_equal is true only for exact37-node membership and all six
compared fields equal. It says nothing about unexamined resolution, scope,
epoch, conditional, binding, effect, exports, import targets or package contents.

## Bounds and publication boundary

Use the fixed-case bounds in [feasibility.md](feasibility.md). The live guard
is sampled before/after parsing, before each AST occurrence/comparison, during
bounded byte/hash/encoding traversal at most64 KiB apart and before return.
The parser itself is an indivisible trusted call on at most4 KiB; no continuous
parser sampling or memory/time guarantee is claimed. The native outer guard
and original process/Job limits remain mandatory.

The pure function returns data only. A future Q-owned fixture writer may retain
exact raw source, index, page, selector, report and receipt with CreateNew inside
the unused operation directory. Whole allocation is reserved before writes,
including temporary/failed copies and all other operation artifacts. Receipt
schema, native handoff and final verification must be specialized and source
reviewed before execution; no generic path in this design is a publication grant.
Report is provisional until complete caller return, final input verification,
owned closure and independent actual acceptance. Do not publish a commit index,
kernel checkpoint or P-consumable artifact. A failed operation stays consumed;
no partial report is accepted. If a return or cleanup proof is absent, its
custody remains UNKNOWN, independent of later successful operations.

