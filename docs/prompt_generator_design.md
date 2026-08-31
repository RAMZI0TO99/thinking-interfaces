# Prompt generator: implemented local contract

This is a support-conditioned prototype, not a TCPL reproduction. The source
review and reproduction decisions are in `tcpl_reproduction_plan.md`.

## Input and output

`SupportPromptGenerator` receives support features [batch, shots, embedding]
and integer support labels [batch, shots]. It embeds each label, concatenates
features and label embeddings, averages over shots, and applies a two-layer
MLP with GELU. Output is [batch, prompt_tokens, embedding].

The current code does not build per-class prototypes, learn a missing-class
vector, return a prompt mask, or add separate prompt positional embeddings.
Those were unimplemented proposals in the earlier note, not existing features.
The Phase I episode splitter supplies balanced nonempty support classes.

## Injection and query boundary

`PromptedTransformerStandIn` uses a detached copy of one support context and a
frozen attention backbone/head. The generator is the only adapted component.
The same context conditions all query examples; query labels are not accepted.

In temporal_prefix mode, prompts are inserted once before block zero and
propagate through later blocks. In per_block_prefix mode, each block receives
fresh support prompts; its prompt outputs are removed before the next insertion.
Thus the sequence does not grow by the prompt count at every block. Both modes
classify the mean of the original signal-token representations after attention,
not the prompt tokens alone. These are sequence prefixes, not direct key/value
activation prefixes.

The stand-in consumes token features, not raw EEG. A LaBraM integration still
needs to preserve EEG positional/electrode embeddings and respect its sequence
budget; Phase I does not claim that integration has already happened.

## Evidence and limitations

`scripts/smoke_prompt_transformer.py` exercises both modes using the common
support-only adapt_torch_model interface. It checks changed prompts and held-out
query logits, unchanged base/backbone state, and no query-time updates. Tests
also check bounded sequence length and sensitivity to the actual query tokens.
The small CPU smoke uses synthetic data: it establishes integration, not EEG
accuracy, meta-training success, or paper-level reproducibility. The previous
generator-only smoke remains separate historical evidence.
