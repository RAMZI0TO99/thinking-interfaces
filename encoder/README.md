# Lane 2 — Encoder

Owns LaBraM checkpoint verification, electrode-name-to-spatial-index mapping, real-epoch forward passes, and partial fine-tuning depth controls. Silent underperformance is treated as an integration failure until external verification passes.

`tcpl_tcn.py` adds the separate TCPL causal TCN component under an explicit local
stride-one contract. It maps `[batch, channels, time]` to `[batch, time, 64]`.
This is not a complete or author-verified TCPL reproduction. See the
[component review](../docs/phase2/tcpl_tcn_review.md) for ordering, initialization,
causality tests and remaining integration work.

`tcpl.TCPLClassifier` assembles the local TCN, support prompts, Transformer and
classifier into per-episode query logits. It also accepts precomputed support
prompts for query batching. See the [model review](../docs/phase2/tcpl_model_review.md)
for input shapes, fixed-target mode, tests and remaining episode-runner work.
Author parity and scientific reproduction remain unverified.
