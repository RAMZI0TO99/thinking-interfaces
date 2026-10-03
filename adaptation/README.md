# Lane 3 — Adaptation

Owns support/query episodes, the fairness baseline, LoRA, bottleneck adapters, and the prompt generator. Query data must never influence adaptation or early stopping.

The executable entry point is `adaptation.episodic.adapt_torch_model`.
See [the integration contract](../docs/adaptation_integration_contract.md) for
input shapes, parameter selection, query boundaries, validated examples and the
remaining LaBraM-specific work. In particular, the default predicate trains all
parameters, and LaBraM's direct QKV-weight access is not compatible with generic
linear-module replacement.

Phase II now has separate verified LaBraM paths:
`labram_lora.inject_labram_qkv_lora` for effective QKV weights, and
`labram_adapter.inject_labram_adapters` for serial post-block bottlenecks.
`labram_adapter.adapt_labram_adapter_support` provides fresh support episodes
with adapter/optional-head selection and all modules in evaluation mode.
See [the adapter review](../docs/phase2/adapter_integration_review.md) for
one-shot/state evidence, engineering settings and remaining runner integration.

`labram_tuning.configure_labram_tuning` and `adapt_labram_tuning_support` provide
explicit linear/partial/full masks and isolated support episodes. All three
update the existing head; support runs in eval mode, with normalization affine
weights following the parameter mask. See [the tuning review](../docs/phase2/tuning_integration_review.md)
for the difference between all-block partial tuning and full tuning, validation
evidence and the remaining source-selection work.

`labram_prompt` now provides class-mean support conditioning, a prompt forward
on actual LaBraM blocks, copied episode context, and generator/optional-head
support updates. It preserves the signal/label association and CLS position.
See [the prompt review](../docs/phase2/prompt_integration_review.md) for exact
placement, batch-one support encoding, state checks and the separate TCPL scope.

`tcpl_prompt.TCPLSupportPromptGenerator` provides the separate TCPL support
encoder and per-episode mean-conditioned prompt generator. Its raw support API
has no label/query arguments; generated tokens retain gradients through both
networks. See [the component review](../docs/phase2/tcpl_prompt_review.md) for the
local constructor contract, input layouts, tests and remaining model assembly.

`tcpl_episodic` adds the source meta-loss, `TCPLSourceTrainer` with an owned model
and persistent Adam optimizer, and `TCPLTargetSession` with frozen source/support
snapshots and query-only prediction. See [the episode review](../docs/phase2/tcpl_episode_review.md)
for loss reduction, ownership, target isolation and pending manifest enforcement.

`tcpl_manifest.TCPLManifestRunner` binds source steps and fixed predictions to
reconstructed audit records and checked NPZ bytes. It enforces outer/inner subject
roles and derives tensor rows from the fixed support/query partition. See the
[manifest review](../docs/phase2/tcpl_manifest_review.md) for the real BCI check,
trusted inputs and remaining scientific-runner limits.


`evaluation.tcpl_publication.publish_tcpl_engineering_prediction` publishes an
outer-target manifest runner's restored safe checkpoint and bound predictions as
immutable engineering records. Repeat calls revalidate and recompute before
accepting existing bytes. See the [publication review](../docs/phase2/tcpl_publication_review.md)
for provenance, interrupted-write behavior and the remaining scientific scope.


`labram_manifest.LaBraMTuningManifestRunner` connects the BCI Profile B episode
binding to isolated linear/partial/full support tuning. Final and inner-validation
runners expose only their fixed held-out role, own their source snapshot, and
check query/source state after inference. See the [runner review](../docs/phase2/labram_manifest_review.md)
for the real-data checks and the explicit absence of verified source-training history.


The same manifest runner now accepts `LaBraMLoRASettings` for seeded effective-QKV
LoRA with explicit head policy. `labram_lora_support.adapt_labram_lora_support`
starts from a plain CPU source, installs fresh seeded LoRA, and runs support-only
SGD while preserving caller RNG and source state. See the
[LoRA runner review](../docs/phase2/lora_manifest_review.md) for real-data checks,
exact trainable masks and remaining source-fit limitations.


`LaBraMAdapterSettings` now connects seeded adapter initialization and the existing
support-only adapter loop to the same manifest runner. Explicit head policy,
fixed subject roles, complete common queries and source/RNG isolation are verified.
See the [adapter runner review](../docs/phase2/adapter_manifest_review.md) for APIs,
real-data checks, parameter counts and remaining source-training limitations.


`LaBraMPromptSettings` connects the existing class-conditioned support-prompt loop
to the audited BCI runner, with seeded generator initialization and an explicit
head policy. Source features are cached from support only, and query-time state
checks include those features and labels. See the
[prompt runner review](../docs/phase2/prompt_manifest_review.md) for validation,
parameter counts and the remaining source-trained-generator limitations.


`anchor_manifest.BCIAnchorManifestRunner` binds EEGNet support tuning and the
EA-tangent source-plus-support recipe to verified Profile A data with the same
trial IDs as LaBraM. It enforces fixed outer/inner roles, fits target alignment on
support only, and checks complete fitted state across query inference. See the
[anchor review](../docs/phase2/anchor_manifest_review.md) for settings, real checks
and the distinction between permitted EEGNet source history and actual classical fits.


`source_selection.BCIEEGNetSourceSelector` adds explicit bounded source settings and
candidate selection for BCI EEGNet. It trains seven permitted sources per inner
fold, validates with the existing anchor runner, ranks all complete candidate/fold
results, then fits the winner afresh on eight sources. Exact training-trial/state
histories and incomplete single-fold diagnostics stay in engineering envelopes.
See the [source-selection review](../docs/phase2/source_selection_review.md) for the
API, bounded real checks and remaining scientific/source-history limitations.


`labram_source.BCILaBraMSourceSelector` adds bounded linear/partial/full LaBraM source
fitting from verified Profile B trials and complete source-only inner selection.
It pins the template, initializes an owned head with the declared seed, records
actual source batches/state hashes and fits the selected settings afresh on eight
sources. See the [LaBraM source review](../docs/phase2/labram_source_review.md) for
the contract, real checks and remaining source-trained-component limitations.


`labram_lora_trained.LoRASourceCandidate` connects source-trained effective-QKV LoRA
to `BCILaBraMSourceSelector`. `TrainedLoRAManifestRunner` continues learned A/B
tensors with fresh support SGD under fixed roles and separate head policies. It
checks non-tensor scaling as well as tensor state during inference. See the
[trained-LoRA review](../docs/phase2/lora_source_review.md) for APIs, real checks,
checkpoint reconstruction and remaining scientific-history limits.


`labram_adapter_trained.AdapterSourceCandidate` connects source-trained post-block
adapters to `BCILaBraMSourceSelector`. `TrainedAdapterManifestRunner` continues the
learned weights with the existing support loop, fixed roles and independent head
policies. It validates dimensions, activation/dropout and frozen state. See the
[trained-adapter review](../docs/phase2/adapter_source_review.md) for APIs, real
checks, checkpoint reconstruction and remaining scientific-history limits.


`labram_prompt_trained.PromptSourceCandidate` connects a source-trained
class-conditioned support-prompt generator to `BCILaBraMSourceSelector`. Source
fits are class-balanced episodic steps over each permitted subject's retained
trials; `TrainedPromptManifestRunner` continues the learned generator with fresh
support SGD under fixed roles and separate head policies, rebuilding conditioning
from each held-out subject's permitted support. It validates generator structure,
activation semantics and frozen classifier state. See the
[trained-prompt review](../docs/phase2/prompt_source_review.md) for APIs, real
checks, checkpoint reconstruction and remaining scientific-history limits.


`ea_selection.BCIEATangentSelector` fixes a roster of classical EA-tangent
recipe settings and runs the complete eight-fold source-only LOSO through the
audited anchor runner. Each fold refits permitted sources plus the held-out
subject's support; selection ranks exact rational balanced accuracy and declares
winning settings, not weights. See the
[EA-tangent selection review](../docs/phase2/ea_selection_review.md) for the
contract, real checks and the preserved invalidation incident.


`ea_selection.BCIEATangentSelector` fixes a roster of classical EA-tangent
recipe settings and runs the complete eight-fold source-only LOSO through the
audited anchor runner. Each fold refits permitted sources plus the held-out
subject's support; selection ranks exact rational balanced accuracy and declares
winning settings, not weights. See the
[EA-tangent selection review](../docs/phase2/ea_selection_review.md) for the
contract, real checks and the preserved invalidation incident.


`tcpl_source.BCITCPLSourceSelector` fits the local TCPL model on permitted BCI
source subjects through class-stratified bounded episodes and runs the complete
eight-fold source-only LOSO, validating via the audited manifest runner with the
fitted trainer admitted directly. See the
[TCPL source review](../docs/phase2/tcpl_source_review.md) for the contract, the
measured full-episode memory finding and the real checks.
