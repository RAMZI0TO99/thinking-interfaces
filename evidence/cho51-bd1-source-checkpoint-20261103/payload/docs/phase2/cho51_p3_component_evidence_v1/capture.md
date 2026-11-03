# Original capture and capacity decision

## Required original records

Capture outside the tested interpreter before decoding or newline normalization.
The actual source of each record must remain attributed: child stdout, child
stderr, owner-observed pipe chunk, caller return, tool chunk/envelope, cancellation
or refusal. Preserve per-stream order and the external observer's merge order;
concurrent pipe observations do not prove an unknowable cross-stream write order.
No reordering, deduplication, text replacement, omitted empty/control bytes or
summary descriptor may replace the original evidence.

Original chunk metadata must include its bounded ordinal, stream, exact offset,
byte count and hash plus independent EOF/error/closure state. Schema, producer,
finite chunk ceiling, encoded metadata bound and exact slot allocation require
implementation-specific review before effects. A quiet stream is not EOF; process
exit and valid event footer do not establish pipe/tool closure. A supplied
CaptureModel snapshot has no such original authority.

Keep stdout and stderr ceilings of 1,048,576 bytes each, raw_tool_return
1,048,576 bytes and external_return 65,536 bytes. The model's 4,096 supplied chunks
is not a qualified operational chunk bound. Actual pipes may fragment the same
byte total differently, and tool envelopes may expand it. Do not silently join
or split captured chunks to satisfy a count while claiming original chunk identity.

## Finite producer and transport proof

Before real admission, for every allowed normal/failure/startup/cancellation route:

1. Pin the exact producer and transport/escaping grammar, including every envelope.
2. Bound raw bytes, chunk count, metadata, nested quoting and total encoded bytes.
3. Include malformed/uncaught output, late stderr, partial writes and tool errors.
4. Assign each retained byte/record to a named partition, fixed slot and publisher.
5. Prove complete publication, final rechecks and independent closeout fit original
   time/memory/disk/ownership and asynchronous-review bounds.

For arbitrary bytes represented as JSON control escapes, one 1 MiB stream alone
can require 6 * 1,048,576 = 6,291,456 encoded payload bytes before quotes/envelopes.
That exceeds both existing return slots. Two such streams total 12,582,912
payload bytes before framing. This is a counterexample to universal raw-to-JSON
fit, not evidence that the fixed selected normal run emits those bytes. Small
success descriptors cannot prove failure transport fit; external original output
cannot be replaced by pins to local files. A narrower producer domain must be
proven against every eligible effect, not assumed from one successful run.

Capture overflow, metadata exhaustion, missing EOF, uncertain return custody or
cancellation consumes/refuses. Preserve the exact available prefix with explicit
loss status and original owned cleanup. Prefix retention is not complete capture,
and failure reporting itself must fit the unchanged reserved failure path.

## Allocation and unchanged guards

The frozen report-only minimum remains 30 files / 17,711,104 reserved bytes:
caller 8 / 9,764,864; supervisor 6 / 4,653,056; closeout 16 / 3,293,184. It is not
the complete native/bootstrap/compiler/capture-metadata allocation. This design
adds no operational report or reservation and borrows no closeout slot. A future
join descriptor, code/fixture/lifecycle tables and chunk metadata must either fit
an explicitly reviewed exact existing report layout or receive named allocations
under unchanged partitions before effects. Duplicate evidence/copies still count.

Retain global 256 files / 64 MiB; fixtures 160 / 32 MiB; supervisor 40 / 8 MiB;
caller 40 / 20 MiB; closeout 16 / 4 MiB; per-file 8 MiB and every fixed role cap.
Charge failed, unused, partial, temporary and unexpected writes. Complete actual
parent conservation precedes projections. No untracked auxiliary artifact or
reused metadata reservation fixes the earlier QD 17/16 refusal.

Retain whole90/work60/cleanup5/hard65/child55 seconds, subordinate suite40/native12/
fault2 maxima, startup5, sample gap200ms/freshness250ms, process512MiB/Job768MiB,
available RAM4GiB/free disk20GiB, one CPU/library thread, hidden GPUs and original
owned-stop/cleanup controls. T0 remains the original origin; child deadline is
min(T0+55,T0+60-F-M), with final-work F and margin M still unproved. No retained
compilation, outside-clock collection, extra worker or resumed review renews time.

Disposition: COMPLETE_CAPTURE_FEASIBILITY_NOT_ESTABLISHED and
COMPLETE_OPERATION_FEASIBILITY_NOT_ESTABLISHED. Actual import/discovery, native
publisher/provider, dispatcher and runtime integration remain REFUSED_UNADMITTED.
This finite contract records concrete missing proofs; it does not claim universal
impossibility or discharge any original obligation.
