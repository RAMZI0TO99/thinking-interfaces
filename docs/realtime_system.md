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
wall time was 60.246 seconds for a nominal 59.992-second timestamp span, including
the deliberate 0.25-second startup lead. The held-out-subject EEGNet replay path
completed with explicit neutral frames and per-window latency logging.
