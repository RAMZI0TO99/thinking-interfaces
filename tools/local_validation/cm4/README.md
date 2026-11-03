# CM4 supplied-data contracts

Source-only implementation of the [accepted CM4 design](../../../docs/phase2/cho51_p3_cm4_lifecycle_design_20261102.md),
with an explicit [current roster successor](../../../docs/phase2/cho51_p3_cm4_roster_successor_20261103.json).
No module was imported or executed in this phase. Tests remain unexecuted.

- collection.py checks the complete operation-bound **836/36** supplied census
  before deriving and checking separate frozen **764/732/700** projections.
- tables.py checks current operation/roster/selection, exact code pairs and
  complete fixture-owner/affected sets before immutable tuple conversion/use.
- events.py independently checks canonical CM4 lifecycle records, closed subcase
  triplets, cleanup/duration, negatives/trace groups, suite/restoration/input claims
  and separate whole/prefix hashes. It never replays a callback producer.
- terminal.py checks a complete supplied snapshot, counter algebra and refusal
  latch claims. A snapshot cannot attest its own actual cutoff or future absence.
- join.py reparses five exact raw inputs in collection-first order, joins every
  whole hash and preserves both event and terminal negatives. Dispatch refuses.
- registry.py declares 40 new methods and their two module pins, extending the
  selection to **320** with the same 516 outside execution. No own-source hash is
  embedded in a test or registry, so the pins are acyclic.

All facts are immutable with unconditional authenticated=False and
execution_accepted=False. Event facts are provisional supplied claims until the
terminal join; neither returned disposition means runtime acceptance. No original
collector, dispatcher, callback producer, terminal observer or native capability
is implemented here. The terminal counter algebra does not verify original
sticky-latch implementation, reentry serialization or complete attempted calls.

The 20 event tests and 20 contract tests add no unittest subTest contexts. With
the earlier254, conditional normal output is5*320+3*254+6 = **2368 events /
1,212,416 bytes at512 each**, plus a separately reserved terminal snapshot. Minimal
synthetic all-pass fixtures omit subcases and use1606 records; record-limit tests
contain supplied4096/4097 streams. Those synthetic records do not add outer test
callbacks or establish normal/failure timing, memory or capture feasibility.

Record4096/line512/stream2MiB/trace128 and all prior guards remain. Five input
ceilings total4,325,376 bytes, not a peak-memory proof. The unchanged CM4 report
proposal remains33 files/18,890,752 bytes, with no runtime reservation created.
See the [implementation contract](../../../docs/phase2/cho51_p3_cm4_implementation_contract_20261103.md)
and [source/scenario index](../../../docs/phase2/cho51_p3_cm4_source_coverage_20261103.json).
P stays disabled; no original obligation or failed disposition is discharged.
