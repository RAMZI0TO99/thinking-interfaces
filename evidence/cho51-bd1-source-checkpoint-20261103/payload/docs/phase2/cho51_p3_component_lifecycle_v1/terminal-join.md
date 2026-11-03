# Terminal snapshot and five-input raw join

An append-only footer cannot prove the producer never refused later. CM2._guard
can fail its post-finish checkpoint, or a later call can set the refusal latch
without changing footer bytes. CM4 uses a separate final supplied snapshot;
it never strengthens the old footer or treats a self-reported boolean as custody.

## Closed terminal snapshot

terminal_raw is canonical sorted-key ASCII/LF JSON, exact bytes1..65536, with
frozen depth/node/container limits. Its exact keys are schema,operation,roster,
selection,events,boundary,attempts,settled,in_flight,post_footer_attempts,
first_refusal,refused,producer_detached. Schema is cho51_cm4_supplied_terminal_v1;
operation/full/selected values match the joined evidence. events is exactly
bytes,sha256 and pins the complete original event stream, not its prefix hash.
boundary is exactly SUPPLIED_SEALED_CHANNEL_SNAPSHOT. Counters are exact integers
0..65535, with attempts at least1; attempts=settled+in_flight,
post_footer_attempts<=attempts. first_refusal
is null or an exact attempted-call ordinal1..attempts. refused is exact bool and
equals (first_refusal is not null). Every post_footer_attempts>0 requires refused.
producer_detached is exact bool. No user text, exception message or native-looking
object is accepted. The bound is a refusal ceiling, not a proof all calls fit.

Complete snapshot consistency requires in_flight=0, settled=attempts and
producer_detached=true. A valid complete snapshot with refused=true is retained
as a negative terminal result, never supplied success; a false snapshot cannot
erase a negative event. Invalid or unsettled snapshots raise Refusal with no
completed join facts. Counters describe supplied attempted guarded operations,
not event rows: one operation can emit several rows and internal checks are not
separate attempts. Their completeness is not derivable from the event count.

The source-only producer model must make first refusal sticky, serialize entry
and reentry accounting, and refuse counter overflow without wrapping. It must
include failure at the post-footer checkpoint. Reads of raw bytes/facts are not
new guarded operations. Once detached, a model snapshot is immutable; an attempted
later callback is outside that snapshot's observation boundary and cannot make
the old snapshot evidence of its own future absence. No future mutable model is
granted an execution path. Independent parsing checks algebra only, not observer
honesty or actual serialization.

For original evidence a trusted external observer must establish the finite
cutoff: revoke producer entry, settle every in-flight/reentrant operation, observe
the final sticky latch after all producer checkpoints, retain the exact completed
bytes, and establish executor/channel/process closure with no producer capability
remaining. Late activity before that cutoff must be observed as refusal. Timeout,
cancellation, capture loss or inability to establish cutoff refuses the operation.
A detached boolean, footer, quiet pipe, PID absence or reported exit alone is not
that proof. The observer and its native boundary are unimplemented/unqualified;
these requirements do not create another open-ended observation period or reset T0.

## Raw join and authority separation

Proposed join_supplied(descriptor_raw,collection_raw,events_raw,tables_raw,
terminal_raw,*,check) takes five exact immutable byte inputs. Descriptor is
1..65536 canonical bytes with exactly schema,operation,roster,selection,source_set,
runtime_set,producer_set,collection,events,tables,terminal. Schema is
cho51_cm4_supplied_evidence_join_v1. Each artifact pin has exactly bytes,sha256,
positive exact bounded length and lowercase64-hex digest. source_set/runtime_set/
producer_set are opaque canonical64-hex digests, never authority. All input limits
are simultaneous:64KiB descriptor,1MiB collection,2MiB events,1MiB tables,64KiB
terminal, sum4,325,376 bytes. This is input arithmetic, not peak memory.

Order: primitive/size preflight; closed descriptor and all exact raw pins; complete
current collection and separately checked historical projections; all current
table rows; independent new event parser; terminal parser and exact context/event
join; final checkpoint; immutable result. Parse original raw inputs every time,
never accept supplied Facts or cached successful parses. Unknown/old schema
refuses; historical projections are only collection projections, never converted
event streams. No filesystem/environment/dynamic import/native operation is an API
input capability. No invocation of the future producer is needed for verification.

Return every whole-input digest, distinct collection projection digests, operation/
roster/selection/context digests, event facts and terminal facts. Disposition is
SUPPLIED_LIFECYCLE_CONSISTENT only if all280 cases passed/ended, no negative event,
complete required declared lifecycle and a complete nonrefused terminal snapshot.
Otherwise valid negative event or refused terminal yields
SUPPLIED_NEGATIVE_LIFECYCLE. Missing/incomplete/malformed input yields Refusal, no
completed result. A terminal-only refusal after an all-PASS footer is therefore
distinguishable from the same raw events joined to a nonrefused supplied snapshot.

authenticated and execution_accepted are unconditional false properties, not
constructor fields or selectable modes. Unavailable labels always include actual
lifecycle/subcase/trace population, original exception/code identity, observer
cutoff/custody, future-activity exclusion, final native source/restoration checks,
capture/EOF/tool return, complete parent census and owned process/Job closure.
Runtime dispatch always raises REFUSED_UNADMITTED. No supplied consistency label
can authorize Q/P/L/V, native capture, publication or science.
