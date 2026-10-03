# LaBraM bottleneck adapter integration

5 September 2026. Third bounded Phase II implementation step, following the
user's instruction to continue step by step while heavy work is deferred.

## Result

The adapter integration and one-shot state checks pass on actual installed
LaBraM blocks and on the full pinned safe checkpoint. No changes were needed to
the frozen encoder, generic adapter primitive or original adaptation loop.
The new implementation is in `adaptation/labram_adapter.py`; the repeatable
offline CPU check is `scripts/smoke_phase2_labram_adapter.py`, configured by
`configs/phase2/adapter_smoke.toml`.

## Exact method and state policy

An adapter acts on the output `h` of a complete transformer block:
`h + up(GELU(down(h)))`. The down projection has a bias; the up projection and
its bias start at zero, yielding exact initial identity. There is no additional
normalization or adapter dropout. Standard feature forwards are supported;
attention/QKV diagnostic flags are rejected explicitly.

Injection validates every explicit target before changing the model, requires
actual unwrapped installed LaBraM blocks, rejects duplicate/aliased targets and
invalid widths, and matches each block's dtype/device. It freezes only the
original blocks it wraps. The caller remains responsible for the overall
source-training policy. Saved state requires reconstructing identical wrappers
before strict loading.

`adapt_labram_adapter_support` accepts support tensors and labels only. It:

- Requires finite inputs and integer labels covering every classifier class.
- Copies the supplied source template and clears inherited gradients.
- Freezes all parameters except adapter weights and the explicitly selected head.
- Uses fresh full-support SGD state for each call and rejects nonfinite losses,
  missing/nonfinite selected gradients and nonfinite updated parameters.
- Keeps all modules in evaluation mode throughout gradient updates and returns
  an eval-mode model with gradients cleared.

Reset means calling it again with the immutable source template. Passing a prior
episode result would intentionally start from that result, so the future runner
must own and enforce source-template identity. Support/query manifest permissions
cannot be established from tensors alone and are not claimed by this helper.

## Full-checkpoint smoke

The smoke uses the already available safe checkpoint
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`,
with a separately pinned model-configuration hash and strict loading. It uses
CPU, two threads, deterministic operations, 800 samples, C3/Cz/C4, two synthetic
support examples (one per class), two query examples and three SGD steps at
learning rate 0.01. The classifier head is randomly initialized; no trained
source-subject fit is used.

| Policy | Targets | Adapter parameters | Total selected parameters |
| --- | --- | --- | --- |
| Adapter only, head frozen | `backbone.blocks.10`, `backbone.blocks.11` | 13,232 | 13,232 |
| Adapter and head | Same two blocks, plus existing two-class head | 13,232 | 13,634 |

Each adapter has width 16 and embedding dimension 200. Both policies pass:

- Exact initial logits before support updates.
- Effective changes in both down/up projection weights and finite changed query
  logits; adapter-only execution ensures this cannot be attributed to head updates.
- Exact agreement between selected names and the declared parameter mask.
- Unchanged complete source/template state and every unselected episode tensor.
- Unchanged state across ordinary and perturbed query forwards.
- Exact repeated-episode state and loss sequences from a fresh clone/optimizer.
- Separate parameter storage and exact strict state-dictionary round-trip logits.

Maximum query logit changes are 3.3513222 (adapter only) and 7.7379894 (adapter and
head). These show that the update path is active; they are not improvements in
accuracy. The few synthetic support losses are not monotonic. Width, target
blocks, step budget and learning rate are engineering fixture choices; scientific
selection remains source-only validation followed by the planned runtime pilot.

## Tests, provenance and remaining work

Five new tests with 17 subtests cover actual LaBraM block execution, float64
placement, atomic invalid-target rejection, exact initial identity, one-shot
updates, both head policies, episode reset from a nonzero source adapter, strict
state loading, invalid support and missing adapters. A fixture adds BatchNorm
buffers and active dropout to verify that the episode policy freezes their
evaluation behavior without changing the source model's training flags.

Full lint and strict type checks pass. The regression suite passes **364 tests
and 439 subtests**. Three pre-existing warnings remain. The engineering receipt
binds the smoke and quality-log hashes to the unchanged source fingerprint:
`02f4778666f144606792c7732cabe29da9395448f89a322cb0d8be66acafc44b`.
Actual Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.

Validation index:
`runs/phase2/adapter_checks/20260905T184534256324Z/receipt.json`.
Full-checkpoint receipt:
`runs/phase2/adapter_smoke/374ea391ac9cb354666850e97ddb034a27e649b99bc414463f35fa895c3a8d73/02f4778666f144606792c7732cabe29da9395448f89a322cb0d8be66acafc44b/20260905T184420551905Z/receipt.json`.

This step does not implement source fitting, fair source/support runner integration,
prompts, TCPL or accuracy experiments. The earlier strict float32 permutation
limitation is unchanged. Source-bound controls remain unrefreshed; Gate A and
scientific approval remain unsigned. No heavy experiment or download was launched.

Next: verify linear/full/partial trainable masks, head and normalization policies,
and episode state isolation before continuing to support-generated prompts.
