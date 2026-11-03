# CM6 supplied producer, independent verifier and terminal integration

3 November 2026. Source-only successor to the accepted
[CM6 expected-context/full-collection implementation](cho51_p3_cm6_implementation_20261103.md)
and [integration design](cho51_p3_cohort_integration_v1/integration.md).
The new cm6i package preserves every frozen CM4, CM5 and CM6 source. One author
owns the twelve new implementation/test/package files; Root owns the registry,
four accounting/contract documents and phase records. A different peer reviews
source; a third peer reviews metadata closeout. Root alone publishes records.

## Raw interfaces and independent decisions

ProducerModel(raw_q,raw_d,raw_c,raw_t,expected_q_pin,expected_d_pin,operation)
accepts raw immutable inputs and independently supplied expected Q/D pins. It
must parse context, the entire declared collection and required Q/H projections,
then tables before any usable producer state or BEGIN. It accepts no caller
Facts, supplied case order, callable, test instance, exception or native handle.
Exact input pins are retained from construction for terminal publication.

parse_tables(raw_t,raw_q,raw_d,raw_c,expected_q_pin,expected_d_pin,operation)
binds canonical closed CM6 tables to that expected context and full collection.
Ordered code pairs and fixture slots retain all bounds. Fixture affected indices
are exactly Q positions whose declared identity class/module matches the owner.
Neither held C identities nor historical H ordinals expand that affected set.

apply(command,fault='NONE'), raw_prefix(), facts() and seal() port CM5's supplied
serial state machine. The CM6 wire uses Q ordinals0..359 and context, never the
full-census ordinal or old roster field. Retain all lifecycle/subcase/trace/
fixture/cleanup/duration/failfast grammar and suffix obligations. Port CM5-S01
post-footer accounting through the common entry path, including nested entry
after FINISH. Port CM5-S02 separation of intended refusal from secondary failure
of refusal recording, even with an existing/partially updated sticky latch.
Keep first refusal ordinal, one settlement per represented entry and outer busy
ownership; any counter overflow or secondary failure invalidates accounting.

An entire encoded group and lifecycle state precede one serial-model state
replacement. This is not native atomicity or actual concurrent execution.
Complete footer and detached, settled accounting are prerequisites for terminal
bytes. Partial/empty prefixes, overflow or secondary failure yield bounded
failure facts without a completed terminal. All-PASS bytes may coexist with a
refused terminal; such a join must remain negative. Seal is a supplied snapshot,
not original observer cutoff or proof against unrepresented future activity.

verify_events(raw_events,raw_t,raw_c,raw_q,raw_d,expected_q_pin,
expected_d_pin,operation) reparses context/full collection/tables and independently
accepts the raw event grammar, prefix and whole digests. It must not replay the
producer or use its transitions as the acceptance engine. Shared pure hashing,
canonical representation and expected-context helpers are permitted.

parse_terminal(raw_terminal,raw_q,raw_d,expected_q_pin,expected_d_pin,operation)
checks canonical terminal fields, context and counter/latch algebra. It checks
retained Q/D pins against independently expected inputs and reports supplied C/T/
event pins; original byte joins remain the final join's responsibility.

join_supplied(raw_join,raw_q,raw_d,raw_c,raw_t,raw_events,raw_terminal,
expected_q_pin,expected_d_pin,operation) reparses every raw input. All six pins
in the join and four retained constructor pins in terminal must match those exact
raw inputs; terminal events must match the entire stream. A substituted table,
collection, context or terminal cannot pass merely because counts agree. The
join has no self pin. Complete Q PASS/END and a nonrefused terminal produce only
SUPPLIED_COHORT_CONSISTENT; a valid negative stream or refused terminal produces
SUPPLIED_NEGATIVE_COHORT. Malformed/incomplete evidence raises Refusal.

Returned facts remain immutable, authenticated=False, execution_accepted=False
and incapable of discharging held debt. Runtime dispatch refuses. Source/runtime/
producer manifest hashes retain their supplied-reference scope: CM6-08 actual
dependency-set/cycle/expectation-provenance checks remain open. A raw join is not
authentic discovery, native custody, complete type/code/trace population or
independent prior/current source adoption.

## Cohort, current source and held debt

The [new source roster](cho51_p3_cm6_integration_roster_20261103.json) adds80
unexecuted methods in four new modules,20 each. Current source becomes
**1016 identities /45 modules**. Q stays the same canonical360 identities/order/
digest. **656 held =576 prior +80 new**. Preserve every preceding936 identity,
41 module pins and all576 prior debt rows. In particular the60 prior CM6 additions
keep NEW_TEST_UNQUALIFIED, rather than being relabelled BASELINE_HELD. The original
516 retain BASELINE_HELD; new80 extend the unqualified additions to140.

The [source-phase ledger](cho51_p3_cm6_integration_debt_20261103.json) compares
actual predecessor/current source inventories and pins. The supplied parser's
fixed876/38 floor cannot by itself prove conservation of later additions. Actual
successor adoption must still choose and independently reconcile authentic prior
descriptor/census/source evidence. No original CM6 runtime predecessor descriptor
or collection is available or fabricated. Synthetic fixtures remain explicitly
synthetic; no held row is removed, renamed, promoted, reclassified or discharged.

The [source index](cho51_p3_cm6_integration_coverage_20261103.json) preserves420
preceding body rows and adds80 held bodies:500 accounted bodies, comprising360
anchor and140 held, not500 selected tests. The original516 held bodies/effects
remain outside this body index and open. New tests add no outer subTest contexts.
The fixed Q360 regression cohort cannot qualify code absent from its membership.
A concrete finite supplemental cohort needs separate membership, profile, debt,
effect and budget review before later admission; no automatic Q union is adopted.

## Caps, authority and remaining evidence

Q<=64KiB; D/C/tables<=1MiB each; events<=2MiB; terminal/join<=64KiB each.
The seven raw ceilings sum5,439,488 bytes. All JSON depth24/nodes100000/container4096
and full-census876..4096/module38..256 bounds remain, jointly subject to raw caps.
Historical/Q projection buffers retain1MiB each. Repeated parsing, input copies,
decoded graphs, tuples, buffers, hash scratch, imports and failure allocations
are additional chargeable memory; these caps do not prove peak memory.

Retain4096 event records,512 bytes per encoded line, one prepared group at most
129*512=66048 bytes, and one-record/512-byte footer reserve. Codes0..65535,
lines1..2147483647, fixture slots0..4095, trace1..128, subcase1..4096 and bounded
duration/counters retain their prior limits. The closed CM6 schema design maxima
346 event-line/888 terminal/792 join bytes remain representation bounds, not
arbitrary capture or outer report bounds. Every encoded group is still measured.

Conditional normal Q output remains5*360+3*254+6=2568 events /1,314,816 bytes /
2567 attempts. Minimal no-subcase supplied Q fixtures use1806 events/1805 attempts.
Frozen CM5 H remains2368 events /1,212,416 bytes /2367 attempts, with its separate
1606-event minimal fixture. Held census additions do not increase Q output.
Neither figure is a complete failure/capture/observer feasibility proof.

Keep the33-file/18,890,752-byte report proposal: caller10/10,878,976,
supervisor7/4,718,592, closeout16/3,293,184. This phase creates only source and
metadata; no operational files/sidecars, source admission or publisher is added.
Future Q/D staging/copies and any failed/unused/unexpected writes require original
parent accounting. Retain global256 files/64MiB, fixtures160/32MiB, supervisor40/
8MiB, caller40/20MiB, closeout16/4MiB, per-file8MiB and fixed role limits.

Keep whole90/work60/cleanup5/hard65/child55 seconds; suite40/native12/fault2,
startup5; sampling gap200ms/freshness250ms; process512MiB/Job768MiB; RAM4GiB/disk20GiB;
one CPU/library thread, hidden GPUs, owned stop/cleanup. Child deadline remains
min(T0+55,T0+60-F-M), with final-work/margin reserves unproved. No clock reset or
outside-clock parsing/sealing. Raw stdout/stderr/tool-return1MiB each and external
return64KiB remain; the6,291,456-byte escaped capture counterexample remains open.

All32 design scenarios remain unqualified even where supplied examples now exist.
Complete original dispatcher/observer lifecycle, recursive failure effects,
capture/native custody, allocation, finite asynchronous closeout and whole-operation
timing/memory gates remain. P, full Q32/100/384 and117/V34 stay held. QD a1f12701
remains INCOMPLETE_REFUSED17/16; consumed failures and UNKNOWN custody remain.
All18,793 resolver rows,13,406 inventory occurrences,724 queues,1782 frontiers,
1786 loads and3972 effects remain open. Full continuation is still infeasible at
least31,002 rows against24,000; G2 refused. Science0/1020, final freeze unsigned.

Only source edits and file/text/JSON/hash/link/arithmetic checks are permitted.
No Python/import/project parser/AST/compiler/native/tests/Git/runtime. Before
correcting frozen candidates, archive affected exact bytes and confirmed review.
Static source acceptance is not executable syntax, test success or admission.
Next is source-only review of a concrete supplemental qualification scope and
remaining original execution prerequisites, without automatically enabling P.
