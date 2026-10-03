# Support-generated LaBraM prompt integration

6 September 2026. Fifth bounded Phase II step, following the user's instruction
to move to the next step. This is the same-backbone prompt comparator; it is not
the separately planned faithful TCPL architecture.

## Result and conditioning definition

The full safe-checkpoint smoke and state tests pass. The new implementation is
`adaptation/labram_prompt.py`, with offline command
`python -B -m scripts.smoke_phase2_labram_prompt` and configuration
`configs/phase2/prompt_smoke.toml`.

The old `SupportPromptGenerator` concatenates feature and label embeddings and
then averages them. That removes the association between signals and labels:
changing label assignments while preserving class counts leaves that pooled
representation mathematically unchanged. The original prototype and its
historical tests are preserved; it is not used by the new Phase II prompt path.

The new `ClassPrototypePromptGenerator` uses one frozen, unprompted source CLS
feature per support trial. It averages features within each class, concatenates
those class means in fixed label-index order, and uses Linear–GELU–Linear to
generate prompt tokens. It requires every classifier class in support, weights
class means equally, and preserves label associations. These are explicit local
method choices, not claims about TCPL's published support encoder.

## Token placement and source policy

`prompted_labram_logits` reuses the installed LaBraM patcher, positional and
temporal embedding helpers, original transformer blocks, final norm and existing
CLS head. It inserts prompts once after position/time assembly, in the sequence
`[CLS, prompts, EEG patches]`. Prompts receive no EEG electrode/time index, and
remain present through every block. Classification reads CLS at index 0.

The supported configuration is the verified neural-tokenizer, CLS-head path in
evaluation mode. The empty-prefix path matches the original classifier exactly.
A nonempty zero-valued prompt would still affect attention; initial identity is
not asserted for added tokens. Per-block replacement is not implemented in this
step; the optional injection ablation remains future work.

`SupportPromptedLaBraM` copies the source classifier and generator, freezes the
source encoder/head initially, and caches copied, detached support features and
labels as episode buffers. Queries cannot change or regenerate this context.
`adapt_labram_prompt_support` creates that context and fresh SGD state per call;
it selects only the generator and an explicitly optional existing head. Support
gradients flow through frozen attention to the generator. Source normalization
and dropout remain in evaluation mode. The returned episode is in eval mode
with gradients cleared; forwards reject a classifier switched into training mode.

Reset means using the same immutable source and generator templates again.
The future runner must enforce their identities, source-training permissions,
label mappings and support/query manifests. These are not inferred from tensors.

## Numerical issue encountered and resolution

The first full-checkpoint smoke failed the joint support-order check: encoding
the two support examples as a reordered batch produced small float32 feature
differences. The prompt comparison differed in 87/800 elements, with maximum
absolute error 6.7055225e-6 against `atol=1e-6`, `rtol=1e-5`.

The final implementation extracts each support trial with a fixed batch size of
one before class pooling. The same order check then passes at the **unchanged**
tolerance. A record of the initial tool-reported failure is retained next to the
validation index as `initial_order_failure.json`; that failed attempt did not
publish a source-bound numerical receipt. The batch-one policy adds support
encoding work that the future runtime pilot must measure.

Pooling multiple examples within a class still has ordinary floating-point
reduction sensitivity. The tests use tolerances for joint support reordering;
they do not promise bitwise invariance for arbitrary support batches or EEG
channel permutations. The previous encoder float32 channel-order limitation
remains unchanged.

## Full-checkpoint evidence

The runner strictly loads the existing safe checkpoint
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`
and checks its model-configuration hash. It uses CPU float32, two threads,
deterministic operations, 800 samples, C3/Cz/C4, two synthetic support examples
(one per class), and two synthetic query examples. There is no trained
source-subject fit or source-trained generator in this smoke.

The generator has two class means of width 200, hidden width 32, and four prompts
of width 200: **39,232 parameters**. Generator-only adaptation selects 39,232
parameters; including the existing two-class head selects **39,634**. Both use
two support SGD steps at learning rate 0.0001. These are engineering fixture
settings, not a frozen scientific optimizer or architecture search.

The checks verify:

- Exact empty-prefix logits relative to the normal encoder.
- Exactly 17 tokens at every block: CLS + four prompts + 12 EEG patches.
- Changing support labels while retaining class counts changes prompts and
  query logits; perturbing support signals also changes prompts.
- Jointly reordering support examples and labels preserves the prompt within
  the stated tolerance.
- Both generator projections receive effective support updates, with the head
  changing only when selected. All other state remains identical.
- Ordinary and perturbed queries preserve model, support-context and prompt state.
- Repeated episodes reproduce state and losses exactly, with separate parameter
  storage; strict state loading reproduces logits exactly.
- Source classifier/generator, raw input tensors, checkpoint files and code
  identity remain unchanged.

Label swapping changes prompts by at most 1.2633905 and logits by 0.6104251;
support-signal perturbation changes prompts by 1.1231364. Support optimization
changes query logits by 3.4697225 with a frozen head and 3.6182349 with a selected
head. These quantities demonstrate active conditioning/update paths, not
accuracy gains or decoding quality.

## Validation and remaining work

Full lint and strict types pass. The regression suite passes **375 tests and
476 subtests**, including six new tests and nine subtests on actual installed
LaBraM blocks. They cover CLS position, empty-prefix identity, sequence lengths,
class/label associations, context copying, query batching, nonempty classes,
gradient masks, state round-trip and reset. Three existing warnings remain.

Validation index:
`runs/phase2/prompt_checks/20260906T073454212875Z/receipt.json`.
Checkpoint smoke:
`runs/phase2/prompt_smoke/36046bf19b0db58be53af53692eab949257db320002a868da8e5d079ef3805f1/47ebbd5e9fde9799125df9629ae9e7e3907ef05c50f073348e03a55f5206f658/20260906T073403463415Z/receipt.json`.
The receipts and quality logs bind source fingerprint
`47ebbd5e9fde9799125df9629ae9e7e3907ef05c50f073348e03a55f5206f658`
to actual Git HEAD `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.

No source fitting, scientific hyperparameter selection, accuracy sweep, large
download, source-bound control refresh or scientific gate signing occurred.
Next: verify the separate TCPL reference architecture and unresolved protocol
details before implementing its reproduction path. Fair source/support runner
integration and E1 feasibility limits remain outstanding.
