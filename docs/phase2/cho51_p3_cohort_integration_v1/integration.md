# Versioned raw producer and independent verifier boundary

No frozen registry/parser/producer is modified. CM5 remains an H-target fixture
producer, CM4 remains its independent verifier, and historical evidence keeps
its original meaning. New CM6 code must be a separate supplied-data successor.

## Raw interfaces and construction

Proposed ProducerModel(cohort_raw, descriptor_raw, collection_raw, tables_raw,
expected_cohort_pin, expected_descriptor_pin, operation) accepts no callable,
test instance, exception object, handle, prevalidated Facts or caller-supplied
order. Before constructing usable state it independently checks bounded Q/D raw
pins and context, the full C collection plus both required projections, then all
table context/owner/type/aggregate constraints. Constructor refusal emits no event
and returns no usable producer. It retains immutable constructor-input pins and
its own Q order/table state. It does not ask an event parser to drive transitions.

apply(command,fault='NONE'),raw_prefix(),facts(),seal() retain the accepted CM5
primitive command and refusal contracts. Every CM5-S01/S02 correction is mandatory:
common represented-entry footer accounting; first observed refusal ordinal;
one settlement per represented entry; outer busy ownership; intended refusal
separate from helper failure; overflow/secondary failure invalidating completed
accounting; all-PASS bytes coexisting with a refused terminal. Whole encoded group
and lifecycle state are prepared before one serial-model replacement. No model
claim establishes native atomicity, real concurrency or guaranteed allocation.

Case commands use Q indices0..Q.count-1 in Q order. D's full C position is never
accepted as an alternative. Tables are canonical cho51_cm6_supplied_tables_v1,
closed schema,operation,context,codes,fixtures. Keep exact ordered unique code
pairs and slot rows with the CM4 type/range bounds. Fixture affected indices are
exactly the Q indices whose identity class or module matches owner; unrelated C
held identities are not added, nor can a missing selected identity be hidden.
Fixtures carry slot,owner,phase,affected as before; phase is setup/teardown/cleanup.
Code pairs remain supplied trace locations, not original code-object witnesses.

## Event and terminal schemas

New event schema cho51_cm6_event_v1 has exactly the CM4 thirteen fields except
roster is replaced by context: schema,seq,op,context,event,case,sub,fixture,kind,
code,line,count,prefix. op=O,context=K. HEADER count=Q.count. Preserve the entire
CM4 lifecycle grammar, including closed subcase entry/result/immediate traces/
exit, cleanup/duration before END, failfast new-entry refusal, special outcomes,
late fixture negatives, suite/restoration/input ordering and footer hashing.
All complete passing events cover Q exactly; negatives preserve the unstarted
Q suffix. Such a suffix is distinct from HELD C-minus-Q. No synthetic primary
failure, missing cleanup completion, implicit ordinal remap or target fallback.

Terminal schema cho51_cm6_supplied_terminal_v1 has closed fields schema,operation,
context,inputs,events,boundary,attempts,settled,in_flight,post_footer_attempts,
first_refusal,refused,producer_detached. inputs contains closed cohort,descriptor,
collection,tables raw pin objects {bytes,sha256}; events is the exact whole raw
event pin. inputs equal the constructor's retained raw pins, not later caller
arguments or freshly substituted Facts. boundary=SUPPLIED_SEALED_CHANNEL_SNAPSHOT.
Preserve CM4 counter/type/latch algebra and CM5 sealing semantics; complete requires
settled accounting, detached producer and an existing complete footer. Empty or
partial prefix/overflow/secondary failure produces separate bounded failure facts,
never a completed terminal. Model detachment is not original cutoff authority.

## Independent raw verification and join

verify_events(events_raw, tables_raw, collection_raw, cohort_raw, descriptor_raw,
expected_cohort_pin,expected_descriptor_pin,operation) independently checks Q/D
pins, full C and required projections first, then tables, then event grammar and
whole/prefix digests. No producer replay, producer Facts or shared mutable state
is accepted. Pure canonical/hash/name helpers may be shared; producer transitions
cannot be the independent verifier's event acceptance engine. Returned event
facts remain provisional until terminal and full raw join checks.

parse_terminal(terminal_raw,cohort_raw,descriptor_raw,expected_cohort_pin,
expected_descriptor_pin,operation) independently verifies expected context and
closed terminal/counter schema. It reports supplied pins/algebra only. A complete
integration must additionally match all retained input/event pins in the join.

join_supplied(join_raw,cohort_raw,descriptor_raw,collection_raw,tables_raw,
events_raw,terminal_raw,expected_cohort_pin,expected_descriptor_pin,operation)
reparses all originals, including full collection before semantic views. join_raw
is closed cho51_cm6_supplied_join_v1 with schema,operation,context and raw pin
fields cohort,descriptor,collection,tables,events,terminal. All input pins match
the exact bytes; P_Q/P_D independently match the first two. Terminal inputs/events
must match the same raw objects. Reject swapped table/collection/context/terminal
bytes even if counts or semantic-looking values agree. No self pin or future
output hash appears in the join.

Return SUPPLIED_COHORT_CONSISTENT only for every declared Q PASS/END and complete
nonrefused terminal; valid negative events or a refused terminal yield
SUPPLIED_NEGATIVE_COHORT. Malformed/incomplete input raises fixed Refusal. No join
discharges held debt. Every fact is immutable, authenticated=False and
execution_accepted=False; runtime dispatch refuses. Plain model checkpoints do
not replace original guards. An original collector/dispatcher/observer needs
separate semantic and resource qualification, fresh admission and actual review.

## Qualification boundary and implementation order

Q360 pins an existing regression cohort and fixed source identities. It does not
contain future CM6 test methods and cannot qualify their code through absence.
Additions must enter full C as HELD/NEW_TEST_UNQUALIFIED, with current pins and
explicit scope. Author a finite supplemental cohort only once its concrete tests
exist; independently review membership, debt accounting, body/effect map, budget
and profile semantics. That new cohort is not automatically unioned into Q360.
Generic manifest mechanics alone never adopt it or authorize a run.

Implement/review expected context plus collection first; then the new producer,
tables, independent events/terminal/join with their unexecuted test inventories.
Current D updates are data/source-pin successors, not edits to frozen Q identity
or H parsers. Before any actual validation, all original failure/capture/native/
allocation/lifecycle and complete-operation timing/memory gates still apply.
