# Lane 3 — Adaptation

Owns support/query episodes, the fairness baseline, LoRA, bottleneck adapters, and the prompt generator. Query data must never influence adaptation or early stopping.

The executable entry point is `adaptation.episodic.adapt_torch_model`.
See [the integration contract](../docs/adaptation_integration_contract.md) for
input shapes, parameter selection, query boundaries, validated examples and the
remaining LaBraM-specific work. In particular, the default predicate trains all
parameters, and LaBraM's direct QKV-weight access is not compatible with generic
linear-module replacement.
