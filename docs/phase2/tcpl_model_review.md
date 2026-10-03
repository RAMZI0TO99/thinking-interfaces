# TCPL model assembly

Completed 8 September 2026. `encoder/tcpl.py` assembles the existing TCN and
support generator with four Transformer layers and a classifier. This is a
complete **local model reconstruction**, not author-verified implementation
parity or a published-score reproduction. The
[local contract](../../configs/phase2/tcpl_local_contract.toml) now marks its
Transformer/readout components implemented. Their scientific choices are unchanged.

## Model interface and behavior

`TCPLClassifier(input_channels, classes)` accepts support shaped
`[episodes, shots, channels, time]` and queries shaped
`[episodes, queries, channels, time]`, returning logits
`[episodes, queries, classes]`. Support/query episode counts, devices and dtypes
must match. Support and query trial lengths may differ; each input tensor must
have uniform lengths and nonempty axes. No padded or ragged batches are supported.

For each query, the model prepends its episode's ten generated prompts to the
TCN's 64-dimensional temporal features. This happens exactly once. Four
independently initialized post-norm Transformer layers process the sequence with
eight heads, FFN width 256, ReLU and dropout 0.1. No mask, positional encoding,
CLS token or extra final norm is added. The classifier receives the mean of the
final EEG token positions, excluding the ten prompt positions. Attention within
each complete trial is bidirectional; this model is not a causal streaming decoder.

`forward_with_prompts(queries, prompts)` permits reuse of `[episodes,10,64]`
support prompts across query batches. It neither copies nor detaches prompts, so
source query loss can differentiate through the support encoder and generator.
There are no stored episodes, optimization steps or labels inside the model.

For fixed-target inference, the caller uses `eval()`, `requires_grad_(False)` and
`torch.inference_mode()`. Source training uses ordinary train mode and externally
managed gradients/optimizer. The model does not infer support/query permissions;
manifest enforcement and preprocessing belong to the future runner. Mixed
precision and GPU behavior have not been qualified by these CPU checks.

## Verification

Eight new tests and 28 subtests cover:

- Full-width finite outputs for two/four classes, 3/22/64 channels and query
  lengths 1/128/512, including noncontiguous views and differing support lengths.
- Hooks capture raw TCN inputs, all four Transformer inputs/outputs and classifier
  inputs. They verify the correct per-episode prefix, unchanged sequence length
  across layers, and pooling of final EEG positions only. Including prompts in
  the mean produces a distinguishable result in the control case.
- Changed support signals and zeroed prompt controls change query logits. Query
  cross-entropy alone, without a prompt penalty, reaches generated prompts and
  raw support inputs with nonzero gradients.
- Train-mode cross-entropy produces finite gradients for every parameter tensor;
  all component groups, including each Transformer layer, receive nonzero
  gradients and effective synthetic SGD updates.
- Changing another episode's support or other query trials leaves unaffected
  predictions exactly unchanged in the float64 control. Support permutation and
  split query batches agree within `1e-12` float64 tolerance. Fixed-target float32
  query batching passes `rtol=1e-5, atol=1e-6`.
- Fixed-target calls preserve source weights, support, queries and supplied
  prompts; unrelated episode calls do not affect repeated predictions. Strict
  in-memory `weights_only=True` restoration reproduces outputs exactly.
- Constructor dimensions, normalization/initialization, independent layer
  weights, invalid shapes, class counts and nonfinite inputs are checked.

Measured parameter counts:

| Model shape | TCN | Support path | Transformer | Head | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 22 channels, 4 classes | 231,936 | 66,560 | 199,936 | 260 | 498,692 |
| 64 channels, 2 classes | 238,528 | 74,624 | 199,936 | 130 | 513,218 |

Full lint passes; strict types pass for 146 source files. Full regression output:

```text
400 passed, 3 warnings, 582 subtests passed in 21.54s
```

The three warnings are the existing EEGNet deprecation and classification warning.
The focused behavior tests passed initially. A type annotation and explicit zip
length check were corrected before final validation; float32 query batching was
also checked in that final run. No numerical tolerance was relaxed.

Evidence: `runs/phase2/tcpl_model_checks/20260908T133815977892Z/receipt.json`,
with adjacent lint/type/test logs. Source fingerprint before/after validation:
`9d11fe01062e977a28b157ffd42e230e6a858c02d39cf0aafb0d8803de485d13`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
All pre-existing source/config/test files retain their hashes except the local
contract's two implementation-status fields and associated explanatory comment;
that exact change was independently checked. Existing components are unchanged.

## Next bounded step

Implement the TCPL source meta-episode loss and fixed-target inference helper,
with bounded synthetic checks for loss reduction, optimizer ownership and target
state isolation. Then connect them to audited trial manifests before scientific
source fitting. Dataset/protocol ambiguities and author parity remain unresolved.

No heavy training, source-bound control refresh or scientific gate approval
occurred. The storage snapshot is 8.55 GiB free, below the unchanged 20 GiB floor.
