# Linear, partial and full LaBraM tuning review

Completed 6 September 2026; implementation and checkpoint smoke began 5 September.
Fourth bounded Phase II step, following the user's request to continue.

## Result and implementation

All 14 full-checkpoint depth-mask checks and four representative one-shot tuning
cases pass. The original `encoder/labram.py` and its depth helper are unchanged.
The new `adaptation/labram_tuning.py` supplies an explicit validated method
policy and a support-only episode helper. The reproducible offline command is
`python -B -m scripts.smoke_phase2_labram_tuning`, using the project environment
and `configs/phase2/tuning_smoke.toml`.

| Method | Trainable groups | Parameters in the 800-sample, two-class smoke |
| --- | --- | --- |
| Linear | Existing classifier head | 402 |
| Partial, final 2 blocks | Blocks 10/11 and head | 965,362 |
| Partial, all 12 blocks | Blocks 0–11 and head | 5,790,162 |
| Full | Entire backbone and head | 5,818,138 |

Partial tuning always freezes the patcher, spatial/temporal/CLS embeddings and
final normalization. Thus integer depth 12 and full tuning have different
parameter sets. All methods retain the existing head weights before support
updates; configuring a mask never resets the head or changes initial logits.

`configure_labram_tuning` validates method, depth and plain installed LaBraM
blocks before applying the established depth mask. Partial depth must be an
integer in 1..number of blocks; booleans, floats, zero and out-of-range values
are rejected. Depth arguments on linear/full methods are rejected. Existing
adapter wrappers and LoRA parametrizations are rejected to keep these methods'
parameter definitions explicit. A report lists exact selected names and counts.

## Head, normalization and episode policy

The existing head is always trainable in these three methods. The support helper
copies an immutable source template, clears inherited gradients, applies the
method mask and creates fresh full-support SGD state per call. It accepts no
query argument and does not reinitialize the head. Support inputs must be finite,
have the named-channel dimension, and provide integer labels covering all classes.
Nonfinite losses, missing/nonfinite selected gradients and nonfinite updated
parameters fail explicitly.

All modules stay in evaluation mode during support gradients and query inference.
Dropout is disabled. Evaluation mode does not freeze normalization affine weights:
those inside selected partial blocks can update; the final norm updates only in
full tuning. Other normalization state follows evaluation behavior. The returned
model is in eval mode with gradients cleared. The source model's original mode,
weights, buffers, trainable flags and existing gradients remain intact.

Episode reset requires passing the same immutable source template again. The
future experiment runner must enforce that identity and the support/query
manifests. It must also supply the permitted source fit and class mapping; these
permissions cannot be inferred from arbitrary input tensors.

## Checkpoint smoke and evidence

The runner strictly loads the existing safe checkpoint with SHA-256
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`
and separately verifies the model configuration hash. It uses CPU float32, two
threads, deterministic operations, C3/Cz/C4, 800 samples, two synthetic support
examples (one per class) and two query examples. The existing head in this smoke
is random; no trained source-subject fit is used.

All 14 masks (linear, partial depths 1–12, full) preserve exact initial logits
and state values. This enumeration performs no fitting or depth selection.
The four methods in the table then receive two SGD support steps at learning
rate 0.0001, followed by query, fresh-episode reset and state-loading checks.

For every tuning case, the receipt verifies:

- Only selected parameters change; every other state tensor remains identical.
- The head changes, and QKV weights change in every selected transformer block.
- Patcher, spatial/temporal embeddings and final norm change only in full tuning.
- Query inference, including a perturbed query, leaves complete state unchanged.
- Fresh episodes reproduce complete state and loss sequences exactly.
- Source and episode parameter storage are separate.
- Strict state-dictionary loading reproduces query logits exactly.
- Source state, input tensors, checkpoint files and code identity remain unchanged.

Maximum query logit changes are 0.1865249 for linear, 1.1504616 for partial-2,
0.8895739 for partial-12, and 1.2305225 for full. They establish effective update
paths, not decoding improvements. The synthetic step budget, learning rate and
chosen depths are engineering fixtures. Source-only validation and the planned
runtime pilot still own scientific optimizer/depth selection.

Validation index:
`runs/phase2/tuning_checks/20260905T185607131511Z/receipt.json`.
Full-checkpoint receipt:
`runs/phase2/tuning_smoke/81ba0cc73bdbe6d975368210007b1ccaa30366a8e1791ebd7e71318535ae6bc9/14084e21e77a19df81f869859381f7b950e0806760f48fad2a95952bbfa34d67/20260905T185532744394Z/receipt.json`.

Full lint and strict types pass. The regression suite passes **369 tests and
467 subtests**, including five new tests and 28 subtests on actual installed
LaBraM models. These cover masks, normalization affine boundaries, one-shot
updates, source modes/gradients, query invariance, reset, state loading, invalid
policies/support and nonfinite-loss rejection. Three existing warnings remain.
The test log reports 36,310.01 seconds elapsed across the overnight run; this is
retained as recorded and is not used as a CPU-performance or pilot estimate.

The code, smoke and quality logs are bound to source fingerprint
`14084e21e77a19df81f869859381f7b950e0806760f48fad2a95952bbfa34d67`.
Actual Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
The final storage snapshot has 18.35 GiB free, below the 20 GiB training floor.

## Remaining work

No source fitting, source-validation selection, support/query runner integration,
accuracy sweep or large download was performed. The prior float32 channel-order
limitation is unchanged. Source-bound controls remain unrefreshed and scientific
gates remain unsigned. Next: implement support-generated prompts on the actual
LaBraM feature path and verify conditioning/state isolation; faithful TCPL stays
a separate implementation.
