# Verifier, refusal and future publication

The proposed initial implementation is pure supplied-data encoding/verification
only: byte buffers, asserted kernel objects, externally supplied expected pins
and a trusted live checkpoint callback. It has no filesystem/network/source-AST
reader, dynamic loader, candidate import, native writer or P entry point.
Parsing bounded JSON as data is distinct from parsing/executing source code.
No codec or verifier has been implemented or run in this design step.

## Ordered verification

1. Check the live guard, external expected identities, total supplied bytes and
   finite manifest/chunk limits before allocating parsed structures. Strictly
   decode the canonical manifest; check its closed schema, exact types, authority
   flags and externally expected binding/family membership. Unknown fields refuse.
2. Verify the exact provided chunk set, order, length and content hashes. Reject
   missing or unused objects, reordered/gapped ranges and changed bytes. Recompute
   the deterministic sorted asset partition and every asset pin/ID from actual
   slices. No untrusted path, URI, decompressor or recursive resolver is called.
3. Strictly decode graph and all complete frames; require canonical re-encoding
   equality. Check the frozen graph/schema, IDs, seeds, root/requester relations,
   names/case collisions, unresolved payload structures and all limits. Preserve
   raw assets byte-exact and check the expected historical index/page structures,
   identities, counts and embedded obligations in the admitted real-case contract.
   Q synthetic fixtures can only prove supplied-data behavior, not real coverage.
4. Reconstruct every expanded prefix, deriving every logical use and historical
   weight from the actual graph and frame lists. Count complete rows/edges/pages,
   exact canonical byte lengths/hashes and the structural payload cost. Do not
   use the manifest's `bytes` or a declared count as a measurement. Exceeding a
   limit refuses; a scalar lower-bound refusal may stop before full expansion.
5. Replay the frozen deterministic initial worklist and each cumulative step
   difference. Check all **intermediate transitions**, not only saved endpoints.
   Differences must be 1..1,000 after the initial frame; reject fabricated progress,
   skipped cursors, removed blocked work and invented facts/links. Require exact
   canonical frame equality, complete debt conservation, retained-before sums,
   every prefix history descriptor and the independent expected last digest.
6. Return the exact verified supplied state only when all structural, replay,
   losslessness, accounting and external identity checks pass. The result remains
   INCOMPLETE_REFUSED for G2 and has no execution or capability authority. A
   verified encoding is not real-source completeness, native custody or admission.

The guard must be callable and return singleton true. Missing/false/other values
or exceptions refuse. Sample at entry, between bounded chunks of at most 64 KiB,
during token/container traversal, at each replay transition, between every prefix
and before returning a result. Native time/memory/stop containment remains the
outer safety boundary for any future execution. Pre-supplied booleans cannot
replace live sampling. No unbounded loop, recursive reference, giant speculative
allocation or unchecked arithmetic may precede the next guard/size boundary.

The exact `_frontier_payload` walk is also preserved: per-value/container debit,
ASCII key rules, string-length/list-size/depth limits, int64 checks and its 8 MiB
structural budget. Apply it at every graph, record/debt, ID preimage and expanded
snapshot boundary where the frozen kernel applies it, not only to unique stored
assets. A streaming implementation may avoid duplicate allocation, but must
produce the same debits, canonical bytes, refusal predicates and replay results.
Any unproved equivalence refuses rather than treating it as an optimization.

## Outcome contract

The new verifier's proposed closed result has `schema`, `outcome`, `reason`,
`checks_completed`, `logical_digest`, `snapshot`, `g2_complete`,
`launch_authorized`, `capabilities_accepted`, and `scientific_admission`.
Schema is `cho51_lossless_verification_result_v1`; all authority flags are false.
Outcome is `VERIFIED_SUPPLIED_STATE`, `CAPACITY_REFUSED` or `INVALID_INPUT`.
On verified supplied state, reason is null and logical digest/snapshot equal the
fully verified last expanded prefix. Otherwise those two fields are null;
reason identifies a failed predicate and `checks_completed` names only completed
checks. These names are a fixed implementation-reviewed enum, never arbitrary
claims supplied by the input. Missing/failed live guard raises the dedicated
checkpoint refusal and commits nothing, preserving the inherited failure model.

The verifier never advances a cursor or mutates caller data. Encoding may not
return a supposedly valid bundle if it would fail decoding/accounting. Packing
an already verified chain preserves every prefix and never manufactures a fresh
logical sequence to evade cumulative history. Missing historical payloads or an
unreconciled real-source graph cannot be repaired by returning a small positive
encoding result. A capacity witness is a refusal explanation, not a checkpoint
or an exhaustive reconciliation report. All original input bytes remain intact.

An operational envelope is deliberately absent. Closed native handoff descriptors,
producer ledgers, Q/P aggregate consumer, file custody and runtime dispatch require
separate source design/review; this result schema grants none of them.

## Future host requirements, not implemented here

Any later host must retain fresh handles for every input and verify original
descriptors/content through final verification. Stage new chunks and provisional
metadata using CreateNew in a fresh owned operation. Include all provisional,
final, timing, failure and native/control output bytes/files in shared budgets.
Recheck live guards and full content/descriptor joins, then write the committing
index last under the reviewed final-verification condition. Crash/stop/partial
write does not produce an accepted state; unreferenced partial artifacts remain
failed-operation evidence and are not silently deleted to reclaim accounting.
Exact caller return, owned process/Job cleanup and independent actual review
remain necessary after publication. Frozen failures are never replayed.

Cross-operation storage sharing must not use old released handles, reset a
history charge, omit a required payload, or erase the shared output allocation.
Fresh physical coverage and separate admission remain mandatory. LP11's P refusal
stays in place; its inherited aggregate parser is not a consumer for this format.
