# Adaptation handoff: one episode interface, explicit backbone boundary

This is the Week 5 handoff required by the supplied Phase I plan. The common
support-only loop is implemented and exercised on stand-ins. Replacing the
stand-in's model/feature boundary is Phase II work; this guide does not claim
that all three methods already run on pretrained LaBraM or reproduce TCPL.

## Common caller contract

`adaptation.episodic.adapt_torch_model` accepts:

- `base_model`: a PyTorch module whose single-tensor forward returns class logits
  shaped `[support_examples, classes]`.
- `support_inputs`: a floating-point tensor in that model's required shape and
  scale; the helper does not preprocess, normalize, patch or convert EEG units.
- `support_targets`: integer class indices (`torch.long`) shaped `[support_examples]`.
- Explicit `steps`, `learning_rate`, optional `device`, and a parameter-name
  predicate `trainable(name, parameter)`.

The caller constructs the source-subject model separately, obtains target support
and query identities from the frozen episode splitter, and checks finite inputs,
class mapping and disjointness. The current support rule is the same earliest
five retained trials per class across model seeds; the plan's seeded-support
wording remains a user decision, not permission to sample query data.

The helper deep-copies the supplied model, moves that copy and support tensors to
the selected device, resets every parameter's `requires_grad` using the predicate,
and runs full-support cross-entropy/AdamW steps. Except for learning rate it uses
the installed optimizer defaults. It neither seeds randomness nor implements
validation, early stopping, resource guards or timing; experiment callers own
those policies and must declare them before Phase II comparisons.

The return value contains `model`, per-step `losses`, and the selected parameter
count. The supplied model remains unchanged. The returned model is still in
training mode: call `result.model.eval()` and use `torch.inference_mode()` for
query prediction. Query labels are not an argument to adaptation and may be used
only by the separate evaluator after prediction.

Important: `trainable=None` means **train every parameter**, even if injection
previously froze it. Always pass the intended predicate for LoRA, adapters or
prompts. Parameter freezing alone does not freeze BatchNorm running statistics
or disable dropout. Compare the full state dictionary, including buffers, when
claiming unchanged frozen state; declare any support-only normalization policy.

## Method-specific construction

Injection mutates its argument in place. Clone the source model before injection,
and enumerate/validate qualified target names before adaptation. A classifier
head is not automatically selected by the predicates below.

| Method | Existing construction | Parameters selected by the caller |
|---|---|---|
| LoRA | `inject_lora(model, rank=..., alpha=..., target_names=...)` replaces selected `nn.Linear` children | Names ending in `.lora_a` or `.lora_b` |
| Bottleneck adapter | `inject_adapters(model, embedding_dim=..., bottleneck_dim=..., target_names=...)` wraps named single-tensor blocks | Names containing `.adapter.` |
| Support-generated prompt | `PromptedTransformerStandIn` holds one detached support context and a frozen attention backbone/head | Names starting with `generator.` |

LoRA has an initially zero residual, so initial outputs match the replaced linear
layer exactly. The configured ranks are 4/8/16 with alpha twice the rank; these are
prepared settings, not a completed performance sweep. The generic adapter starts
as an exact identity and expects a tensor output whose last dimension is the
embedding width. Construct generic adapters with a compatible dtype/device;
the existing stand-in path is float32 on CPU before the common loop moves it.

Prompt inputs are token features `[examples, tokens, embedding]`, not raw EEG.
The stored support context has shape `[1, shots, embedding]`, with integer labels
`[1, shots]`; the current smoke obtains these by averaging support token features.
It is copied/detached once and reused for every query. Temporal prefixes propagate
through the stack; per-block prefixes are removed and replaced each block.
Neither mode may grow the sequence cumulatively or derive its context from query
examples. Details are in `docs/prompt_generator_design.md`.

The older generator-only smoke predicts from generated prompts alone. It is not
evidence of EEG-token attention. Use `scripts/smoke_prompt_transformer.py` for
the actual support-conditioned attention and query-state checks.

## LaBraM-specific boundary: inspect calls, not just parameter names

`encoder.labram.LaBraMClassifier` is already a single-tensor logits wrapper with
fixed canonical channel names. The verified real input is `[2, 22, 800]`, giving
four one-second patches per channel at Profile B's 200 Hz. Preserve the explicit
Profile B unit convention, channel mapping, temporal cropping and class mapping;
the generic episode helper does not supply any of them.

The installed Braindecode 1.7.0 attention implementation reads `self.qkv.weight`
and calls `nn.functional.linear` with separately assembled Q/V bias. It does not
call `self.qkv(inputs)`. Replacing this QKV child with the current `LoRALinear`
therefore raises an attribute error. Simply exposing the base weight to silence
the error would bypass the LoRA update. Do not inject all discovered linear
layers indiscriminately or claim QKV adaptation works.

Attention output projection is called as a module (`self.proj(x)`), so that
particular call boundary supports the generic wrapper. Its exact initial output
was checked on a small installed attention module. A potential qualified name
under the classifier is `backbone.blocks.0.attn.proj`; enumerate the actual loaded
model and validate target count and changed outputs before any full-model run.
This is not a chosen Phase II target set or proof of trained-model parity.

The normal installed backbone loop calls each block as `blk(x)`, which is the
generic adapter's single-tensor contract. Optional attention/QKV-return modes
are not forwarded by `AdaptedBlock`. Prompt integration needs a backbone-specific
token boundary preserving class/electrode/time embeddings and the token budget;
the stand-in is not a drop-in implementation of that boundary. Any architecture
change must be a separately identified Phase II experiment, not a modification
of the frozen Phase I benchmark.

## Verified examples and acceptance before integration

Existing executable examples are `scripts/smoke_adaptation_methods.py` (generic
wrappers), `scripts/smoke_prompt_transformer.py` (both attention modes), and
`scripts/run_episodic_lora.py` (separate real EEGNet episode). Their scope differs;
do not combine their results into a claim of pretrained-LaBraM adaptation.

The focused tests in `tests/test_lora.py`, `tests/test_adapters_prompt.py`,
`tests/test_episodic.py` and `tests/test_prompt_standin.py` cover initial no-op,
target validation, support-only clone updates, actual query-token influence,
bounded prompt sequence length and unchanged query-time state.

Before claiming the real integration works, record exact source/input/config
identities, target names and selected parameter count; check initial no-op where
applicable; show the intended parameters and outputs change on support; check
the source model and required frozen state remain unchanged; and run queries in
evaluation mode without updates. Preserve the fixed episode identities, resource
guards and independent metrics. These are future integration checks, not a claim
that Phase II experiments have already been performed.

A separate CPU-only probe of the installed attention module verified the QKV
failure, exact projection/adapter initial outputs, and the loop's default
parameter-selection behavior. It loaded no pretrained weights and trained no EEG.
Receipt: `runs/runtime_probe/adaptation_handoff_20260831T1659.json`, SHA-256
`15ae6ef5a856964fbe12a026c272204307b9bc12cef14c64cf266f2fd20dcc42`.
Upstream module SHA-256:
`4102baa7e509c8674c663fa0d30937e389f452e414b33c0588b5f59721eb4e45`.
The original plan was reviewed structurally without modifying it; visual DOCX
rendering was unavailable because LibreOffice was not installed.
