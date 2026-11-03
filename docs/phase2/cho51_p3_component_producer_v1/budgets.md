# Bounded scope and unchanged feasibility gates

Design target is the frozen CM4 supplied836/36/320 roster, with254 conditional
normal flat subcases and zero new methods in this phase. A next implementation
must account for every added test and dependency before source acceptance; old
CM4 raw evidence remains its own historical target if the checkout grows.

The producer model uses exact immutable command tuples; no retained command
history is required. Bounded state keeps at most4096 event records/2MiB bytes,
one command's encoded scratch at most129*512=66,048 bytes, one trace tuple at
most128 pairs, fixed bounded tables, finite scalar counters and one immutable
sealed snapshot. Independent parser/copies/JSON graphs/hash scratch remain
additional chargeable allocations. This is a representation bound, not a proof
of Python object overhead, total peak memory or actual complete-operation fit.

Ordinary normal mapping is unchanged:320*5+254*3+6 =2368 events, at most1,212,416
bytes using the existing512-byte line ceiling. BEGIN emits two events but is one
attempt; every other ordinary success event has its own command, including FINISH.
Therefore the conditional normal model uses2367 guarded attempts. seal and pure
reads are controller/read operations, not producer attempts. Failures can emit
multiple trace records per attempt; reentry/refused attempts may emit none. There
is no general equality between attempt and event counts. The65535 attempt bound
is independent of4096 record capacity; overflow always invalidates accounting.

The model's pre/post fault script is one fixed enum per command; reentry simulates
one rejected nested entry, at most2 in_flight, with no recursively executed script.
This finite test mechanism does not bound actual adversarial entry or prove
concurrency. Unknown real call counts/types/effects block admission. A constant
error enum does not bound upstream formatting or the original outer transport.

The report-only proposal stays33 files/18,890,752 bytes: caller10/10,878,976,
supervisor7/4,718,592, closeout16/3,293,184. No operational allocation is added by
CM5. The five CM4 input ceilings still total4,325,376 bytes. Exact native/bootstrap/
compiler/test/capture/failure writes and terminal witness packing remain open.
The primitive model needs no native fixture publication; the original fixture
32-file/4MiB combined and16 auxiliary/901120-byte caps remain if later applicable.

Retain global256 files/64MiB, fixtures160/32MiB, supervisor40/8MiB, caller40/20MiB,
closeout16/4MiB, per-file8MiB and every original fixed role cap. Failed/unused/
partial/temp/copy/unexpected writes retain charges. No borrowed closeout role,
extra output channel or untracked implementation cache may bypass accounting.

Retain whole90/work60/cleanup5/hard65/child55 seconds; suite40/native12/fault2,
startup5; sampling gap200ms/freshness250ms; process512MiB/Job768MiB; RAM4GiB/disk20GiB;
one CPU/library thread, hidden GPUs and original owned stop/cleanup. T0 never
resets. Child deadline min(T0+55,T0+60-F-M) still requires unproved final-work F
and margin M. Retained compilation, discovery, sealing or review is not moved
outside the clock. No complete-Q timing claim or new QD attempt is inferred.

Keep raw stdout/stderr1MiB each, raw_tool_return1MiB and external_return64KiB.
One1MiB control-byte stream can require6,291,456 escaped payload bytes before
envelopes; two require12,582,912. This disproves universal raw-to-envelope fit,
not every specific normal run. Exact per-stream order and external-observed merge
order are distinct from unknowable concurrent write order. EOF/error/pipe/tool
closure, cancellation and failure-report preservation need original witnesses.

Complete recursive failure effects, capture, allocation, original dispatch/cutoff,
finite asynchronous closeout and timing/memory feasibility remain NOT_ESTABLISHED.
The concrete feasible next source-only target is the primitive producer/refusal/
seal model, with independent raw verification and explicit roster accounting.
Actual dispatcher/provider integration remains REFUSED_UNADMITTED, P disabled.
