# Phase I real-time system draft

A saved channel-first recording can be replayed through Lab Streaming Layer at
its nominal rate or directly through the deterministic array stream. The causal
ring buffer exposes only received samples. Fixed windows are emitted at configured
stride boundaries and sent to a decoder's `predict_proba` interface.

The confidence gate emits a class only for a unique maximum at or above threshold;
otherwise it emits the explicit neutral state. Accumulated evidence requires three
consistent non-neutral windows and emits one command before latching. Neutral or a
state change resets the evidence. The interface receives only gate and evidence
objects, never raw probability arrays.

The 60-second LSL loopback sent and received all 7,680 samples at 128 Hz. Measured
wall time was 60.243 seconds for a nominal 59.992-second timestamp span, including
the deliberate 0.25-second startup lead. The held-out-subject EEGNet replay path
completed with explicit neutral frames and per-window latency logging.

## Integrated native demonstration

`scripts/run_live_demo.py` connects an actual LSL outlet/inlet to the causal
buffer, CPU EEGNet, confidence gate, accumulated evidence, and a native Windows
Forms command grid. It uses the configured modern PowerShell runtime without
changing execution policies. The grid receives gate decisions, not probability
vectors, and acknowledges each displayed window. The script closes the display
automatically after the rehearsal and saves its own initial/final renders.

This protocol trains on subjects other than A09 only: zero A09 support trials,
zero A09 training or validation trials. The first three available trials per
class from A09 are replayed without repeats at 128 Hz (12 windows, 48 seconds).
The saved Profile A epochs were preprocessed offline; this is not causal online
raw-EEG filtering or live brain control. Boundaries between saved trials are
explicit, and the four-second windows do not cross those boundaries.

The hidden-render rehearsal received all 6,144 samples unchanged and rendered
all 12 windows. Wall time was 48.260 s versus a 47.992 s timestamp span; CPU
processing p95 was 6.327 ms. All decisions abstained at the fixed 0.40 threshold,
so no command was emitted. These are functional transport/gating checks, not
evidence of useful decoding accuracy. No threshold was lowered to force a demo.

Local completion additionally requires an actual visible rehearsal, a matching
configuration, verified result/receipt/preview hashes, and one display receipt
per decoded window (`evaluation/live_demo_audit.py`). A hidden render alone
cannot satisfy that check. The latest receipt is `runs/live_demo/latest.json`.

To rehearse on this laptop, from the project folder:

```powershell
.\.venv\Scripts\python.exe scripts/run_live_demo.py
```

Processing latency includes the ready-window copy, prediction and decision logic.
It excludes acquisition of the four-second window, file handoff and native screen
paint. Display acknowledgments are separately timestamped. CPU fallback on the
same laptop is not a substitute for testing a second physical machine.
