# Stable arithmetic and unchanged operation guards

This is a source-only representation/design bound, not an operation allocation,
measured run, peak-memory proof or complete runtime feasibility result.

## Input and identity limits

Q manifest<=65536 bytes/count1..360 mechanically; only the exact360-member profile
is adopted here. D expected descriptor<=1048576 bytes; C collection<=1048576;
tables<=1048576; events<=2097152; terminal<=65536; final join<=65536. The seven
distinct raw ceilings sum **5,439,488 bytes**, not simultaneous peak memory.
Compared with CM4's five inputs, Q and D add1,114,112 raw input bytes. Copies,
decoded graphs, inherited registry tables, projection buffers, hashing scratch,
proof metadata and failure allocations are additional chargeable memory.

Keep exact JSON graph depth24/nodes100000/container4096, immutable primitive
types and integer bounds. Q and D/canonical reports must pass both aggregate
bytes and graph caps before conversion/use. D C-count876..4096 and modules38..256
are maxima, not a promise that every combination fits1MiB. Q/C/H projected raw
collection buffers each retain1MiB caps. Never truncate, batch away, omit held
rows or widen caps when full context/projection construction refuses.

Code/fixture tables retain4096 rows each, code0..65535, line1..2147483647,
fixture slot0..4095, exact affected Q tuples and trace1..128 on exception routes.
Q ordinal max359; subcase index1..4096; ordinary record count0..4096; supplied
duration0..2**63-1. Identity strings are bounded as specified in identity.md.
Count maxima need not be simultaneously attainable under stream/graph limits.

## Event and fixed-record bounds

With360 ordinary successful cases,254 flat normal subcase outcomes, one cleanup
and duration per case, and no failure traces or extra fixture events:
5*360+3*254+6 = **2568 events /1,314,816 bytes at512 each**.
BEGIN emits two events, so the same conditional command path has2567 attempts.
No-subcase synthetic all-pass Q fixtures use1806 events/1805 attempts. The1528
remaining positions within4096 are not a universal failure/capture reserve.
Future held census additions do not change these Q counts; a different adopted
cohort needs its own reviewed arithmetic. Frozen CM5 H accounting stays2368 /
1,212,416 /2367, with its separate1606-event synthetic fixture scope.

The new thirteen-field CM6 schema replaces roster with one context64 digest;
it does not append the entire census or any identity string to event lines.
Canonical ASCII/LF field-width arithmetic gives these conservative maxima, using
seq4096 even where grammar would require a smaller sequence, the largest allowed
owner/count values, longest fixed kind KEYBOARD_INTERRUPT, operation36/context64
and complete null fields. TRACE_CASE_SUB and TRACE_FIXTURE are the two ownership
shapes of the single TRACE event, not new wire names.

| Event or ownership shape | Maximum bytes including LF |
| --- | ---: |
| HEADER |283|
| SUITE_OPEN |288|
| SUITE_CLOSE |289|
| RESTORED |286|
| INPUTS_VERIFIED |293|
| CASE_START |287|
| CLEANUP_DONE |289|
| PASS |281|
| SUB_ENTER |286|
| SUBPASS |284|
| SUB_EXIT |285|
| CASE_END |285|
| DURATION |300|
| FAIL |294|
| ERROR |295|
| XFAIL |295|
| SUBFAIL |297|
| SKIP |278|
| XPASS |279|
| FIXTURE_ERROR |304|
| TRACE_CASE_SUB |302|
| TRACE_FIXTURE |303|
| FOOTER |346|

These closed-schema maxima fit the unchanged512-byte line cap. Implementation
must still measure every encoded line/group and reject overflow before commit;
schema changes require fresh bounds. Footer hash/count refer to exact prior raw
bytes. Reserve one record and512 bytes before each nonfooter commit. Keep at
most4096 records/2MiB, one prepared group<=129*512=66048 bytes, and counters
0..65535 with at most2 in flight in the fixed reentry model. Overflow invalidates
accounting; 4096 records does not authorize65535 calls or bound adversarial ingress.

For the exact new terminal and final-join schemas, maximum-width canonical
supplied payload arithmetic is888 and792 bytes respectively, including LF.
This uses maximum pin sizes,64-digit hashes,36-character operation and five-digit
counters. Both retain64KiB caps. It proves only those closed supplied payloads,
not an original native cutoff witness, report envelope, error text, arbitrary
capture data, tool return or complete outer failure report.

## Existing report roles and actual operation

The unchanged report-only proposal remains33 files/18,890,752 bytes: caller10/
10,878,976; supervisor7/4,718,592; closeout16/3,293,184. Its existing roles can
carry new-schema payloads only under a future separately reviewed operational
mapping: caller/collection.json1MiB, caller/tables.json1MiB,
caller/events.ndjson2MiB, supervisor/producer-terminal.json64KiB and
caller/evidence-join.json64KiB. Do not replay or alter old reports or launchers.

Q and D are predeclared pinned source inputs, not two free runtime sidecars.
If a future operation creates/stages/copies them, those writes need explicit
parent path/owner/transaction/cap and complete accounting within existing limits.
No projection file, extra per-attempt journal or seventeenth closeout role is
allocated. Full raw-input/parent census precedes all views. Matching hashes and
reserved report space do not prove native allocation or witness packing.

Retain global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB, per-file8MiB and every fixed role cap. Retain inner fixture32-file/
4MiB combined and16 auxiliary/901120-byte caps if later applicable. Failed,
unused, partial, temporary, copied and unexpected writes remain charged.

Retain whole90/work60/cleanup5/hard65/child55 seconds; suite40/native12/fault2,
startup5; sampling gap200ms/freshness250ms; process512MiB/Job768MiB; RAM4GiB/free
disk20GiB; one CPU/library thread, hidden GPUs, original stop and owned cleanup.
T0 never resets; child deadline min(T0+55,T0+60-F-M) still has unproved final-work
F and margin M. Descriptor parsing, collection/projections, sealing and complete
closeout are not outside the clock. No QD retry or new worker/window is inferred.

Raw stdout/stderr each1MiB, raw_tool_return1MiB and external_return64KiB remain.
One1MiB control-byte stream can expand to6,291,456 escaped payload bytes before
envelopes. Closed event bounds do not solve that capture counterexample. Original
EOF/error/pipe/tool/cancel/parent closure, recursive formatter effects, native
custody, complete allocation, finite asynchronous closeout and timing/memory
feasibility remain NOT_ESTABLISHED. P and all original execution holds remain.
