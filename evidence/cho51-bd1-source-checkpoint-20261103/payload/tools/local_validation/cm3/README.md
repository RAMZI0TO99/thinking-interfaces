# CM3 supplied event verification and raw evidence join

Eight-file source-only implementation of the accepted CM3 design. No importer,
executor, native provider, live capture or operational acceptance is provided.
Operational dispatch refuses and every returned authority property is false.

- `events.py` independently parses frozen cho51_cm2_event_v1 bytes under the
  exact 764/248 target. It checks canonical records, owner/order/negative state,
  trace groups, fixture phases, footer reservation and prefix/whole hashes. It
  does not call CallbackModel or CM1's event validator. Its private working state
  never consumes caller Facts. `hash_bytes` handles 1..2 MiB exact immutable
  bytes in 64-KiB chunks; frozen HB1's 1-MiB helper is unchanged.
- `tables.py` reparses closed canonical supplied code/fixture tables, validates
  all exact immutable rows, sorted unique pairs/slots and complete owner sets.
  Its tokens/locations are not original object/code/fixture witnesses.
- `join.py` binds exact raw descriptor/collection/event/table digests. Complete
  CM2 collection precedes table/event views and distinct CM1/HB1 projections.
  Opaque source/runtime/producer strings are supplied context, not native proof.
- `registry.py` explicitly declares the enlarged current source universe:
  796 identities / 34 modules, 280 proposed selections and 516 outside execution.
  This does not change the parser's historical 764/248 report target. Full current
  collection and a producer/wire join for the enlarged roster remain unavailable.

The parser returns SUPPLIED_TRANSCRIPT_CONSISTENT or SUPPLIED_NEGATIVE_TRANSCRIPT
only for complete structurally valid transcripts. Malformed/incomplete inputs
raise bounded Refusal without manufacturing completion. Cleanup, duration order,
suite closure, final producer refusal, actual subcase population, trace origin
and native/source/transport custody remain unavailable. Even identical all-PASS
bytes can accompany different final producer states; the API cannot detect that
hidden difference. Caller-created result objects are never acceptance inputs.

The 32 new methods (16 event and 16 join/table) are unexecuted. They contain zero
unittest subtest contexts. New-current-roster normal mapping would conditionally
be 280*3+254+2=1,096 records / 561,152 bytes, but no such producer/wire is
implemented or qualified. The old CM2 1,000-record calculation retains its exact
scope. Synthetic 746/4,096-record test inputs are model data, not outer unittest
callbacks or measured runtime output. The supplied input maximum remains
4,259,840 bytes; full decoded/copy memory and failure/capture feasibility are open.

The event tests use independent textual fixtures. One explicit CM2 producer
cross-check demonstrates unchanged raw bytes after a later refusal; the verifier
itself never replays that producer. Large synthetic table/hash/record boundary
fixtures do not establish time or memory sufficiency. All runtime gates and
original guards remain; P is disabled, science is 0/1020 and freeze unsigned.
