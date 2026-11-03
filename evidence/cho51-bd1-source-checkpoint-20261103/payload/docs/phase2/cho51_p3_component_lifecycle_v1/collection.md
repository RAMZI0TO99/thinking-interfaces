# Full current collection before historical views

Proposed verify_collection(raw, operation, *, check) accepts exact immutable bytes,
1..1,048,576 bytes. Canonical compact sorted-key ASCII JSON with one final LF is
required, no duplicate keys, unknown keys, floats, coercion or bool-as-int. Frozen
HB1 depth24/node100000/container4096 limits remain. Checkpoints surround bounded
hash/parse work; they are supplied calls, not independent native enforcement.

The closed top-level keys are schema,operation,roster,selection,complete,modules,
tests. Schema is cho51_cm4_supplied_collection_v1; operation is the canonical
nonzero UUID supplied to the API. complete is exactly true. Roster and selection
are exactly the digests in pinned CM3 registry.py:

- full: 11b76c3173fdaf6de6ef3e9b4ce71814b423930d7ac75d5c9f0768fa5a6edd56
- selected: 33f075f498b160748883fc3f53f3bed18258db0d706f66d41dd0c4b25024c092

Digest input is the complete ordinal-sorted ASCII identities joined with LF and
one terminal LF. Full/test order is the literal CM3 expected_ids order; selected
order is its selected_ids order. Event case indexes are full-roster ordinals
0..795, only those in the exact 280 selection. Counts alone are insufficient.

Every module row has exactly module,bytes,sha256,loader,load_tests,partial. The
34 rows match every CM3 expected_modules literal name/size/hash in order. loader
equals the pinned CM1 collection.LOADER literal, load_tests and partial are false.
Every one of the 796 test rows has exactly the frozen CM2 ten keys: id,module,
class_name,method_name,source_module,source_qualname,skipped,deselected,
expected_failure,xfail. Names/code owners match the exact expected identity;
the four eligibility flags are false. Selection exclusion is not discovery
deselection: all 516 outside execution must still be present and eligible in
the full supplied census. There is no import, discovery or code-object inspection.

Only after checking every current row and all module pins may the verifier build
a canonical cho51_cm2_supplied_collection_v1 projection: preserve all exact CM2
764 identities and 32 module rows, drop only current-only rows and new header
fields, retain complete=true. Feed those derived bytes to the pinned CM2 raw
verifier, which separately checks CM1 732/30 and HB1 700/28 projections. Each raw
and derived digest is separately named. This is a derived identity/source-pin
projection, not original historical execution or original same-operation custody.

Historical module bytes must still match their exact frozen pins. If a future
successor changes an old module, refuse this projection route; never replace the
old hash with a current hash, weaken the old verifier, or report a successful
historical projection based on identity overlap alone. A separately reviewed
compatibility contract is needed for that change. No projection precedes full
current conservation or hides an omitted new method.

The returned immutable facts retain whole current digest, all three separately
named CM2/CM1/HB1 projection digests, operation/full/selected digests, exact IDs
and selection. Operation in the raw collection closes the earlier schema's
missing-field ambiguity only within supplied data. Matching strings cannot prove
fresh collection, producer identity or runtime custody. Authority properties are
always false; invalid/incomplete inputs raise Refusal with no success facts.

The new tables_raw schema is cho51_cm4_supplied_tables_v1 with exactly schema,
operation,roster,selection,codes,fixtures. Operation/full/selected values must
match the collection/join. The CM3 code-pair and fixture-row rules remain, except
affected uses complete selected full ordinals 0..795 and at most 280 entries.
All owners match exact selected module/class owners, all rows are checked before
use, slots remain unique 0..4095, pairs sorted/unique, code0..65535 and
line1..2147483647. Same owner/phase in distinct slots remains legal. Raw1MiB,
4096 rows per table and all aggregate graph limits apply simultaneously.
Tables are supplied references, never original type/code/lifecycle witnesses.
