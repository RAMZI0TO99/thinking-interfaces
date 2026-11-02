# Real-source scope decision and bounded observation approach

Engineering design, 1 November 2026. Root authors; an independent peer accepts
exact pinned design bytes. This package follows the accepted
[supplied-data codec qualification](../cho51_p3_lossless_codec_implementation_20261101.md).
It implements no runner and admits no Q, P, loader, candidate or scientific run.

The decision is to keep complete real-source continuation refused under its
existing contract and develop **one fixed, non-resumable source-observation
probe**. The probe answers a narrower useful question: can a qualified observer
recover the syntax occurrences of a particular pinned source and compare the
explicitly selected historical fields without executing that source? It cannot
answer whether the project dependencies, effects, custody or G2 are complete.

- [Decision, alternatives and conservation](decision.md)
- [Exact probe contract and refusal behavior](probe-contract.md)
- [Concrete case and feasibility limits](feasibility.md)
- [Implementation gates and 32 qualification scenarios](qualification.md)

The [static case](../../../runs/coordination/cho51_p3_real_scope_design_20261101_v1/static-case.json)
selects the 494-byte `packaging/__init__.py`, one complete 256-row historical page,
its complete index and exactly 38 page ordinals (one origin and 37 syntax nodes).
The retained bytes currently match the historical source pin. File/JSON/hash
inspection gives a six-file output bound of 498,123 bytes, well inside the
unchanged applicable output ceilings. This is **STATIC_DATA_ENVELOPE_FITS_RUNTIME_UNQUALIFIED**.
No new AST observation, checkpoint, replay, codec invocation or timing test ran.

A successful probe is neither a smaller resumable project state nor a fragment
that can be stitched into one. Its selected and unselected obligations remain
open. No continuation/aggregation/P consumer may accept it. Full continuation
still needs at least 31,002 rows against 24,000 and remains
`INFEASIBLE_UNDER_CURRENT_GUARDS`. The new scope does not change that result.

P remains disabled. All 18,793 resolver rows, 13,406 separate inventory
occurrences, 724 queued contexts, 1,782 frontier records, 1,786 unresolved
binding loads and 3,972 effects retain their complete original payloads and
identities. Historical failures remain consumed; attempt `131bc595` retains
UNKNOWN outer/bootstrap custody. G2 is `INCOMPLETE_REFUSED`, candidate117/V34
are unexecuted, science is 0/1020 and the final freeze is unsigned.

