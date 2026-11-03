# CM6 S140 supplied profile implementation contract

3 November 2026. Source-only successor to the independently accepted
[S140 design](cho51_p3_cm6_supplement_design_20261103.md), implementing the
[separate profile](cho51_p3_supplement_cohort_v1/profile.md) without editing
frozen CM6 or CM6i sources. Root publishes metadata and owns the new registry;
the implementation author owns the remaining new cm6s package files. Independent
source and metadata reviewers have separate roles. No runtime is admitted.

## Profile, context and full collection

The fixed S140 manifest remains byte-for-byte unchanged: 60 CM6 and 80 CM6i
methods, disjoint from Q360. New implementation tests are held outside both
profiles. Q-oriented D continues to schedule Q360 as COHORT and all other
identities as HELD. S membership never changes a debt kind or scheduling field.

Raw Q/S/D/E and independently expected size/hash tuples bind the operation.
E pins the exact Q/S/D bytes and checks equality of the three source/runtime/
producer manifest references with D. K_Q retains the frozen CM6 domain; K_S
uses the new supplemental domain and E pin. E is downstream of D and independent
source manifests; those manifests must exclude D, E and dependent reports or
admission/review records. Actual dependency/cycle/provenance checks remain open.

The new context requires all current registry identities and module pins,
including this implementation's held additions, beyond frozen CM6's 876/38
floor. Existing 1016 identities and 45 module pins must be conserved. Future
supplied additions do not authenticate their own independent adoption.
The source ledger separately reconciles the actual preceding source roster.
There is no authentic CM6 runtime predecessor descriptor or collection to use
as evidence; none is fabricated.

Full C remains the original CM6 collection schema and K_Q context. Every module
and test row, including held additions, must pass full collection verification
and the required Q/H views before the S view. The S projection copies checked
observed rows, in S order, with exact sorted owner modules and an explicit S-to-C
map. It is an in-memory view with a distinct schema/context/pin, not a new output
file or permission to discover only seven selected modules.

## Supplied producer, parser, terminal and join

The new producer takes six raw inputs Q/S/D/E/C/T, four independently expected
pins and the operation. It verifies context, full collection and tables before
usable state or BEGIN. Tables use the new profile and exact S fixture indices;
owner128, code, slot, phase and aggregate limits remain unchanged.

The S event schema retains the thirteen fields and complete CM6 lifecycle
grammar. Header count is140 and outer case indices are0..139. Q indices are a
different domain. Closed subcases, immediate traces, cleanup, duration, fixture
failure, failfast suffix, suite closure, restoration, input verification and
footer checks remain. CM5-S01 common footer-entry accounting and CM5-S02 refusal
helper secondary-failure handling must be preserved. The independent event
verifier parses raw bytes; it does not replay producer transitions.

Terminal inputs retain exact constructor pins for anchor, supplement, descriptor,
expected, collection and tables, plus the complete event-stream pin. Complete
footer, counters, settlement, refusal latch and supplied detachment are required.
Partial, overflow or secondary-refusal failure cannot produce a completed
terminal. The boundary remains SUPPLIED_SEALED_CHANNEL_SNAPSHOT and proves no
native cutoff or hidden cleanup.

The final join reparses nine raw inputs and checks eight raw pins, all six
retained constructor pins and whole events. Only complete S PASS/END with a
nonrefused terminal returns SUPPLIED_SUPPLEMENT_CONSISTENT. Valid negative
events or a refused terminal return SUPPLIED_NEGATIVE_SUPPLEMENT, including
all-PASS event bytes followed by a represented refusal. Malformed or incomplete
evidence refuses. No caller Facts, self pin or cross-profile alias substitutes
for raw verification. Facts remain immutable and unauthenticated, execution is
not accepted, no debt is discharged, and operational dispatch refuses.

## Debt, source examples and bounds

The accompanying roster, source index and debt ledger record every new method
as unexecuted NEW_TEST_UNQUALIFIED. All656 preceding held rows retain their
identities, source pins and kinds:516 BASELINE_HELD and140 NEW_TEST_UNQUALIFIED.
S140 remains part of that held ledger. Prior500 indexed method bodies remain
unchanged; the original516 held bodies outside that index and their effects
remain open. New supplied examples do not qualify any of the24 S140 scenarios
or32 original CM6 scenarios. Source examples and actual original-boundary
acceptance are distinct claims.

Q/S/E each retain64KiB; D/C/T each1MiB; events2MiB; terminal/join each64KiB.
Nine raw ceilings total5,570,560 bytes, not peak memory. Preserve depth24,
nodes100000, container4096, census4096/module256 maxima and1MiB Q/H/S projection
buffers. Retain4096 records,512-byte event lines,129-record/66048-byte prepared
groups, one-record/512-byte footer reserve and counters0..65535. Every actual
encoded group remains bounded. Closed field-width design bounds remain
347 event /622 E /1098 terminal /1001 join bytes, not measured runtime output.

Conditional outer S output remains706 records/361472 bytes/705 attempts with
no outer subtests. Q360 stays2568 records/1314816 bytes/2567 attempts in its
separate conditional normal scope. Minimal supplied Q fixtures stay1806/1805.
Frozen S bodies still construct at least20 complete inner Q streams:36120
records and36100 primary invocations, plus one known nested entry, with at least
3,259,828,000 cumulative old-prefix bytes and no smaller full-prefix hash reads.
This is cumulative work, not peak RAM, elapsed time, disk or a guard violation.
New held test workload adds obligations and is not folded into S membership.

No operational slot is added. Keep the33-file/18890752-byte report proposal;
global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB and per-file8MiB; inner fixture32-file/4MiB and16-auxiliary/
901120-byte limits. All future source staging/copies and partial/failed writes
must be charged under their original role, with no projection sidecars.

Keep whole90/work60/cleanup5/hard65/child55 seconds; suite40/native12/fault2,
startup5; sample gap200ms/freshness250ms; process512MiB/Job768MiB; RAM4GiB/disk20GiB;
one CPU/library thread, hidden GPUs and owned stop/cleanup. Child deadline is
min(T0+55,T0+60-F-M); final-work/margin remains unproved. T0 never resets and
parsing/sealing is not moved outside the clock. Raw stdout/stderr/tool-return
each1MiB and external-return64KiB remain; the6291456-byte escaped control-payload
counterexample remains open.

Complete timing/peak-memory/original-operation feasibility is NOT_ESTABLISHED.
Original source adoption/manifests, dispatcher/observer/native custody, effects,
capture/EOF/tool return, allocations and final closeout remain open. No staged
execution or partition of a required single operation is adopted. P, full Q,
117/V34 and science remain held; no consumed attempt or UNKNOWN custody changes.
All predecessor guards and historical limitations retain their scope.
