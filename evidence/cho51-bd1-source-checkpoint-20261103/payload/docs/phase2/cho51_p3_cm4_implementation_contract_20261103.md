# CM4 supplied-data implementation and roster/budget successor

3 November 2026. Source-only implementation of the independently accepted
[CM4 design](cho51_p3_cm4_lifecycle_design_20261102.md). Root owns collection,
tables, terminal, raw join, registry, contract tests, all documents and records.
cm4_events_author owns the initial event parser/test implementation and releases
it for Root integration. A different peer reviews source; another peer reviews
metadata closeout. Preserve9,369 predecessor inputs and12 archived current pages.

## Implemented boundary

The ten-file tools/local_validation/cm4 package implements independent supplied
collection, current reference tables, lifecycle-event and terminal-snapshot
parsers plus a five-raw-input join. Frozen predecessors remain byte-identical.
No Python/import/project parser/AST/compiler/native execution, tests or Git is
permitted in this phase. Checks use files, text, JSON metadata, hashes, links and
arithmetic. Source review does not certify executable syntax or runtime behavior.

verify_collection(raw,operation,*,check) validates the full new census, exact
module/code owners, complete false eligibility flags and operation/roster/selection
before projecting to CM2 and its separate CM1/HB1 views. Any old module-pin mismatch
refuses. The new raw digest and three projection digests remain distinct.
parse_tables(raw,operation,*,check) checks all canonical rows/context and complete
current affected sets. validate_tables(codes,fixtures,*,check) accepts exact tuples
only. Code/fixture4096, raw1MiB, depth24/node100000/container4096 and integer/owner
bounds all remain; aggregate maxima need not fit simultaneously.

verify_events(raw,operation,*,codes=(),fixtures=(),check) independently parses
cho51_cm4_event_v1 using the new literal current registry. It implements the
accepted D01 closed SUB_ENTER/outcome/immediate trace/SUB_EXIT interval, including
refusal of interposed parent callbacks. Every ended case requires cleanup and
duration. SKIP can precede repeated mixed cleanup failures; XFAIL/XPASS require
cleanup/duration; no negative becomes PASS. Complete declared suite close,
restoration and final-input claims precede footer. Supplied duration is an integer
0..2**63-1, never original native time. Whole and prefix hashes stay separate.
All4096 records,512-byte lines,2MiB stream,4095 nonfooter/2MiB-minus512 prefix,
128-frame trace bounds and64KiB hash chunks/checkpoints remain unchanged.

parse_terminal(raw,operation,*,check) checks exact64KiB schema/context, whole-event
pin, bounded attempt/settled/in-flight/post-footer counters, first-refusal ordinal,
exact bool latch and detached=true with no active attempts. Refused snapshots are
valid negative data; incomplete or malformed snapshots produce no completed facts.
This is an independent algebra verifier, not a mutable producer/latch implementation
or an original observer. It cannot prove which real calls occurred, counter/latch
serialization, a real cutoff, or the absence of later activity.

join_supplied(descriptor_raw,collection_raw,events_raw,tables_raw,terminal_raw,
*,check) checks exact input bounds/pins, full current collection before views,
all tables, independent events, terminal state and its exact whole-event pin, then
a final checkpoint. It never trusts caller-created Facts, cached parses or an
event producer. Results and nested facts are immutable with unconditional false
authority properties. Disposition is SUPPLIED_LIFECYCLE_CONSISTENT only for all
selected declared PASS/END and a complete nonrefused terminal; any valid negative
event or refused terminal yields SUPPLIED_NEGATIVE_LIFECYCLE. Invalid/incomplete
input raises Refusal. Runtime dispatch always refuses.

## Exact new-test accounting

The [roster successor](cho51_p3_cm4_roster_successor_20261103.json) adds exactly20
CM4EventTests and20 CM4ContractTests with literal module byte/hash pins. Current
source and the new supplied target become **836 identities /36 modules /320
selections**, retaining516 outside execution. The design's796/34/280 target is
historical; earlier CM3's frozen parser still targets764/248. This is an explicit
implementation-specific adoption of the design's required new-test extension;
old schema meaning and registry files are not rewritten or relabelled current.

All40 new methods have zero normal unittest subTest contexts. With254 earlier
contexts, conditional ordinary success mapping is5*320+3*254+6 = **2368 records /
1,212,416 bytes** at512 each. The historical CM4 design2168 bound and earlier
1096/1000/860 bounds retain their respective wire/roster scopes. The new minimal
no-subcase synthetic fixture has1606 events;4096/4097 synthetic boundary streams
and raw2MiB hash inputs are supplied test data, not outer callback counts.

Input caps remain64KiB+1MiB+2MiB+1MiB+64KiB =4,325,376 bytes. The accepted named
report-only allocation proposal remains33 files/18,890,752 bytes: caller10/
10,878,976, supervisor7/4,718,592 and closeout16/3,293,184. No native allocation,
runtime parent map, filesystem writer or extra report slot is implemented. Every
future test/native/bootstrap/capture/failure effect still needs original accounting.
The [source index](cho51_p3_cm4_source_coverage_20261103.json) pins all320 selected
methods and textual new declarations/imports, with direct-body limits. It is not
complete recursive effects, allocation, memory, failure or capture qualification.

## Review and remaining obligations

Root alone publishes predeclared phase records under
runs/coordination/cho51_p3_cm4_implementation_20261103_v1. Frozen candidates needing
correction must have exact affected files and manifest archived first. Reviewers
send message-only verdicts and verify Root's saved bytes; final closeout confirmation
is conversation-only. Current pages are archived before updates. No commit/push.

The28 CM4 scenarios remain unqualified. Eighteen supplied scenarios have source
examples; CM4-17 has only counter/late-snapshot examples, with original producer
sticky/reentry/post-checkpoint behavior still unimplemented. Two accounting
scenarios have source artifacts. Seven original-runtime scenarios remain
unimplemented. Source examples do not complete a scenario, especially malicious
or post-footer producer behavior. CM3's original nine failure/capture obligations,
all26 local/24 HB/40 SC/36 diagnostic/48 original scenarios remain open.

Next is source-only design/review of the bounded producer/dispatcher lifecycle and
terminal observation boundary, including finite recursive failure/effect mapping.
Real imports/discovery, semantic equivalence, original code/type/trace/subcase
witnesses, trusted native observer/capture/custody, complete parent allocation and
finite asynchronous closeout with timing/memory/final reserves remain gates.
No supplied result admits runtime; original guards and holds stay unchanged.

P stays disabled, full Q32/100/384 and candidate117/V34 held. QD a1f12701 stays
INCOMPLETE_REFUSED17/16; six Q failures remain consumed; UNKNOWN custody stays
unknown. All18,793 resolver rows,13,406 inventory occurrences,724 queues,1782
frontiers,1786 loads and3972 effects remain open. Complete continuation remains
infeasible at least31,002 rows against24,000; G2 remains refused. Science0/1020,
final freeze unsigned. No full-restart, runtime or scientific acceptance follows.
