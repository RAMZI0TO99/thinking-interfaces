# CM1 supplied-data implementation

This package implements the independently accepted CM1 design's source-only
contract layer. It has no importer, runtime collector, TestResult producer,
launcher, native provider or operational publisher. `refusal.dispatch` always
refuses. P stays disabled.

`registry.py` combines HB1's frozen 700 identities and 28 module pins with the
exact 32 CM1 identities and two test-module pins. Its source is pinned externally;
tests do not embed the registry hash, avoiding a self-hash cycle. All 732 source
identities and the selected 216 have literal ordered digests.

`collection.py` checks canonical supplied JSON, the entire 732/30 universe,
then the deterministic unchanged 700/28 projection through frozen HB1. It returns
both byte digests and the selection digest. Namespace, bootstrap and restoration
checks are supplied-token models, not observations of live objects. They cannot
establish actual loading, mock restoration or continuous guard enforcement.

`protocol.py` verifies a bounded canonical supplied transcript with exact ordinal,
operation, roster, trace-group, case and subcase joins. It preserves partial and
negative transcript facts without making them successful. A complete 216-case
transcript is explicitly an unauthenticated supplied success, never an accepted
run. Supplied reference tables are model inputs, not frozen runtime/code evidence.
Unknown in-case fixture boundaries and nested failfast unwinding refuse. Trace
code tables are conservatively limited to 4,096 supplied location pairs while
individual code ordinals retain the 0..65,535 design range.

`refusal.py` models byte-preserving ordered chunks, sticky consumed overflow,
minimum report reservation totals, disjoint supplied guard surfaces and original
deadline arithmetic. It performs no I/O or actual reservation, custody or cleanup.

The exact 16 collection and 16 protocol test methods are unexecuted. The source
inventory records bounded local operations and unresolved recursive/runtime
obligations; it is not an admission or complete producer/output sufficiency proof.
