# Explicit cached selection callback, 10 October 2026

The [one-use callback](pro3_inference_candidate/selection_callback.py) now connects
the tested namespaced cache scope to the optional production LaBraM hook.
Import and construction use only stdlib, validate the existing package-owned
directory, worker digest and progress sink, and write no cache. Invocation
consumes the callback even on failure, then lazily constructs the original scope.
The five existing package modules remain byte-exact; default CLI activation is
unchanged. See the [executed manifest](SELECTION_CALLBACK_REVIEW.json).

Ten fresh synthetic tests and callback lint passed. Linear, full and LoRA
selection produced exactly the original evidence JSON, model state and RNG state;
the poisoned synthetic outer target was never read. Failure/progress paths restored
selector attributes and model forwards. Invalid selectors/digests/sinks, output
escape, registered-owner reuse and callback replay refused. A real production
dispatch with tiny synthetic selection reached the existing mocked evidence
rejection boundary, with no publication, recorder or target execution.

Execution Git was `b09e2f9023c085e03bfb40ad9692e7f4c12d31a8`; canonical Source remained
`3114ec43a97b1afdcda26149587381cb12105e7064af16e2c3dd64b51f554529` /432 files. Existing engineering quality
(1055 tests plus lint/types) was verified against current source without rerunning
it. Root's actual execution self-review passed142 checks; this is local
self-review, not independent acceptance or accuracy evidence.

The guard kept startup7/active4GiB RAM, disk20GiB, NumPy/Torch1,
process2.25/Job2.5GiB and90/120-second guard/native bounds. Native time was
22.506seconds and peak Job commit1,356,558,336bytes (1.263GiB).
Job/handles/awake request and registered private caches released; the named Job
and known owned processes were freshly absent/exited. The guard handles only the
explicit fixture-owner labels after physical Job closure. A deliberately invalid
registration fixture remains exact evidence. The first metadata reviewer assumed
LF for this Windows CRLF fixture; its refusal and original source remain, and a
fresh142-check reviewer corrected only that expectation. No test/model was replayed.

The [recorder audit](../../../runs/coordination/cho_cached_callback_20261010_v1/recorder_read_only_recovery_decision_001.json)
passed48 read-only checks: both original LaBraM claims/failures remain, zero
attempts remain, and neither publication nor engineering-success intent exists.
Recovery replays an existing successful intent; it cannot reopen these failures.
No recorder was constructed, locked, recovered, reset or claimed. The sole
historical cell remains EEGNet; no LaBraM cell was accepted.

For a separately admitted worker, provision the exact six modules together under
its reviewed operational package, preserving the cleanup helper's module-parent
confinement. Bind an existing safe output directory beneath that package:

```python
from pro3_inference_candidate.selection_callback import make_source_selection_callback

callback = make_source_selection_callback(
    owner_directory=attempt_directory,
    worker_sha256=actual_worker_sha256,
    event_sink=operational_progress_sink,
)
# Supply callback as ProductionChoCaseRunner(labram_source_selection_runner=...).
```

This construction example creates no compute admission. Calling it on real
inputs performs fitting and still requires the exact independently admitted
operation/guard. Synthetic7GiB startup and90seconds are diagnostic limits, not
substitutes for original real-case10GiB startup and480/520/600seconds.

The [next inert prerequisites](../../../runs/coordination/cho_cached_callback_20261010_v1/next_operation_prerequisites_001.json)
bind current source/quality/callback and the completed recorder decision.
Real controls, measured environment and a separate operation are still pending.
Checkpoint cohort/target overlap, Scientific Gate A and freeze remain unresolved
or unsigned. No third original attempt, alternate identity to evade the cap,
full real cached-selector completion, scientific signature or host grant follows.
