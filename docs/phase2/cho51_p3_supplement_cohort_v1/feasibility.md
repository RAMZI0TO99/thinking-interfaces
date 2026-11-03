# S140 feasibility: representation bounded, execution not established

This decision uses source text and arithmetic only. No test, import, parser,
compiler, diagnostic or benchmark was run. No measured rate, peak memory or
original process/Job behavior is inferred from the calculations.

## Separate outer result bytes from nested test work

All140 selected bodies have zero outer unittest subTest contexts. On the
conditional successful outer path with one cleanup/duration per case and no
additional fixture/error events,5*140+6 gives706 records, at most361,472 bytes
at512 per record, and705 primary command attempts. Existing Q360 arithmetic stays
2568 records/1,314,816 bytes/2567 attempts. These are separate streams; adding the
counts does not define a new500-test operation. Extra qualification controls and
failure/capture paths are not included in the706-record figure.

The [workload index](workload.json) enumerates20 concrete complete inner Q360
all-PASS stream construction paths:17 in integration event tests, one in join
tests and two in producer tests. One stream is followed by an expected nested
post-footer refusal, so this is not20 accepted inner executions. Per stream,
BEGIN commits two records,360 cases commit5 each and closeout commits4:1806
records and1805 primary apply invocations. The selected paths alone account for
at least36,120 inner records/36,100 primary invocations plus one nested entry.
Negative fixtures, other context/reconciliation tests and malformed paths add
work; this is not a complete worst-case accounting.

The frozen producer concatenates the preceding byte prefix and hashes the whole
new buffer after every commit. Following BEGIN, the preceding record counts are
2..1805, whose sum is1,629,914. Every canonical generated record contains a36-byte
operation and64-byte context, even before JSON syntax/other fields. Thus the20
streams pass at least **3,259,828,000 cumulative old-prefix bytes** into concatenation,
and full-prefix hashing rereads at least the same byte volume. This is a source
lower bound on cumulative byte work, not measured copy mechanics, peak RAM,
disk writes, retained output or elapsed time. It does not prove a guard violation.

Valid producer construction performs two full C verifications. A valid event
verification also performs two. A valid raw join performs four full C checks/
Q/H projection chains and six expected-context parses; fixture construction adds
further parsing. The full current1016-row collection cannot be replaced by a
seven-module subset or a historical projection to remove this work. No parsing,
fixture building, hashing or sealing is outside the operation clock.

## Proposed outer representation bounds

| Item | Bound | Meaning |
| --- | ---: | --- |
| S manifest |11102 bytes|Exact current canonical design input;64KiB cap |
| Conditional outer normal events |706 /361472 bytes|No failure/control budget claim |
| Closed event line |347 bytes|Previous conservative346 plus one schema character;512 cap |
| Expected E payload |622 bytes|Independent field-width maximum;64KiB cap |
| Closed terminal payload |1098 bytes|Six retained input pins;64KiB cap |
| Closed final join payload |1001 bytes|Eight raw pins;64KiB cap |
| Nine distinct raw ceilings |5570560 bytes|Additional S/E source inputs;not peak memory |

The new terminal/join widths replace the old888/792 *only for the new CM6S
schemas*. The frozen CM6 bounds retain their original scope. Field maxima may
not combine into a semantically valid record; they are conservative byte-width
arithmetic, not generated runtime evidence. Every future implementation must
still check actual encoded widths, full raw/graph bounds and reserved footer.

Q/S/E<=64KiB each; D/C/T<=1MiB each; events<=2MiB; terminal/join<=64KiB each.
The sum increases the former5,439,488 raw ceiling total by131,072 for S/E.
It does not increase any per-input cap or process/Job budget. Keep depth24,
nodes100000, container4096; C/module maxima4096/256 with full input fit required;
Q/H/S projection buffers<=1MiB each. Decoded graphs, repeated copies, fixture
retention, prefix buffers, imports and failures require separate peak accounting.
Keep4096 records,512-byte lines,129-record/66048-byte prepared groups, footer
reserve and all original counter/type/trace bounds. Remaining record space is
not a universal adversarial ingress or trace reserve.

## No new runtime allocation or relaxed clocks

The33-file/18,890,752-byte report proposal stays caller10/10,878,976,
supervisor7/4,718,592 and closeout16/3,293,184. S and E are proposed independently
pinned source inputs, not free operational sidecars. Future staging/copies and
all partial/failed/temporary/unexpected writes must be declared and charged.
No new output slot or projection file is allocated by this design.

Keep global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB, per-file8MiB and fixed role caps; inner fixture32-file/4MiB and
16-auxiliary/901120-byte limits retain scope. Keep whole90/work60/cleanup5/hard65/
child55 seconds, suite40/native12/fault2, startup5; sampling gap200ms/freshness250ms;
process512MiB/Job768MiB; RAM4GiB/disk20GiB; one CPU/library thread, hidden GPUs,
owned stop and cleanup. Child deadline min(T0+55,T0+60-F-M) retains unproved final
work/margin reserves. T0 never resets. No old launcher, watcher or QD retry is used.

Raw stdout/stderr/tool-return1MiB each and external-return64KiB stay. A1MiB
control-byte stream can still expand to6,291,456 escaped payload bytes before
envelopes. Smaller S result records do not solve that original capture problem.

## Decision and finite successor work

**Representation:** conditional normal outer fields/counts fit their proposed
unchanged per-record/per-input caps. **Current implementation:** S140 unsupported;
new CM6S profile/collection/producer/verifier/terminal/join contracts are not
implemented. **Actual timing, peak memory and complete operation:** NOT_ESTABLISHED.
The source workload is substantial, but no mathematical impossibility or measured
failure of the original time/memory guards is claimed here. Original native
custody, callbacks/observer/cutoff, recursive failure effects, full parent census,
capture/EOF/tool return and finite asynchronous closeout remain open.

The next bounded step is source-only implementation/review of the separate
supplied CM6S contracts. Its new tests must enter full C as additional held debt;
they are not silently added to S140. Before any actual S execution, complete a
whole-operation/effect/allocation plan and original runner/provider qualification
under fresh independently reviewed pins, unchanged guards and separate admission.
Any diagnostic itself needs its own bounded scope and admission; this design
does not authorize one. Do not optimize by dropping full collection, failure
evidence, selected methods, historical obligations or final checks.

A staged alternative may be studied separately, but is not adopted here. It
cannot split a required single operation to evade its whole-operation caps or
masquerade as one passing S140 run. Scope, exact membership coverage, repeated
controls/capture/cleanup, cumulative effects and the permitted claim would need
new independent review. No timing or memory waiver follows from partitioning.

P and full Q32/100/384 remain held, as do117/V34 and original science. All32 CM6
scenarios and24 new design scenarios are unqualified. No debt, consumed attempt,
UNKNOWN custody or source/manifest adoption obligation is discharged. QD remains
INCOMPLETE_REFUSED17/16; continuation still infeasible at least31,002 rows versus
24,000, G2 refused, and science0/1020 with final freeze unsigned.
