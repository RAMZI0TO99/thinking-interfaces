# PC1 supplied projection source

Source-only B/I/C canonical ASCII JSON parsers and a supplied consistency join.
`parse_binding`, `parse_ingress`, and `parse_capture` return recursively immutable
primitive tuples. `join(raw_b, raw_i, raw_c, expected_o, expected_b)` requires an
independently sourced expected operation and independently sourced canonical B
bytes; the latter supplies every expected B field. Origin independence is an
external obligation, not authenticated by this code. The entire observed B,
including its final LF, is hashed for each cross-binding check. `classify`
converts only the package's dedicated input refusals; other failures propagate.

This code consumes no raw streams, event bodies, ledger contents, actor map or
native handles. Empty-reference digest shape is checked; nonempty referenced
bytes are not verified. FROZEN/TERMINAL snapshots require a nonempty event reference but do not establish full event
grammar or original sealing. No native authority, execution authorization,
debt discharge, provider, writer, integration or runtime admission follows.
Dispatch is always refused. Original gates, populations, resource and capture
obligations remain open. The 63 tests in two modules are held, unexecuted source;
registry extends the frozen 1062/49 census to 1125/51, preserving Q360 and S140
and all 702 prior held rows. These source counts do not qualify any scenario.

Result flags and dispositions are fixed properties; refusal codes use a finite
fixed domain. JSON integer tokens are limited to seven digits before conversion;
unexpected decoder ValueError and other non-parser failures propagate. Graph
accounting includes object keys and values. These are source bounds, not measured
runtime or peak allocation claims.
