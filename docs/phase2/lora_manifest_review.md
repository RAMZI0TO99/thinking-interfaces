# LaBraM LoRA manifest integration

8 September 2026. Sixteenth bounded Phase II step.

`adaptation/labram_lora_support.py` adds seeded support-only SGD using the existing
effective-QKV injector. `adaptation/labram_manifest.py` accepts the new
`LaBraMLoRASettings` through the same runner used for linear/partial/full tuning.
The [existing runner contract](labram_manifest_review.md) still governs the BCI
cohort, pinned Profile A/B files, reconstructed episodes and outer/inner roles.

## Settings and state policy

LoRA settings explicitly identify QKV targets, rank, alpha, initialization seed,
whether to train the existing head, fixed support steps, learning rate and query
batch size. Their digest includes every field. Targets use classifier-qualified
names such as `backbone.blocks.11.attn.qkv`; unknown targets and excessive ranks
fail before episode binding. These are engineering inputs, not scientifically
selected optimizer settings or a frozen search budget.

Each call deep-copies the runner's plain CPU float32 source, freezes its parameters,
and installs fresh LoRA A/B tensors before constructing fresh SGD state. The seed
is applied inside a saved/restored CPU RNG context. All modules stay in evaluation
mode, preserving dropout behavior, normalization buffers and source affine weights.
Only LoRA tensors and, when explicitly enabled, the existing head are trainable.
The head is never reset. Zero-initialized B preserves the initial effective weight;
A may legitimately have zero gradient on the first step.

Only bound support signals and labels enter adaptation. Query prediction uses the
existing complete common-query partition and state-digest checks. The result
records settings, exact trainable names/counts, adapter count, support losses and
source/adapted state digests alongside the bound predictions. Query labels are
returned for later scoring and never passed to adaptation.

## Scope

This runner still requires a plain source template. It does not accept or restore
an already LoRA-trained source, train on source subjects, select hyperparameters,
authenticate prior training subjects, or publish scientific evaluation cells.
Results remain `engineering_only=true` and
`source_training_history_verified=false`. CPU tests do not establish GPU parity,
accuracy, runtime-pilot completion or scientific gate approval.

The next bounded coding step is adapter integration under the same audited roles
and episode binding, followed by support prompts and matched anchors. The deferred
45-fit source-bound control refresh remains RAM-blocked and must use the source
identity current when it is eventually admitted. Its 10 GiB startup and 4 GiB
runtime guards are unchanged.

## Validation and evidence

Seven new tests / 32 subtests cover all four shot levels, exact support sizes and
common query IDs, both head policies, effective attention-weight updates, frozen
source tensors, caller modes/gradients/RNG, repeat/reset behavior and seed identity.
Changing only query labels leaves adaptation losses, adapted state and logits
identical. Invalid roles, changed assets, invalid support and settings are rejected;
deliberate query-time state mutation and nonfinite logits also fail closed.
The original linear/partial/full and QKV tests remain intact.

The real-data CPU check reconstructed all nine BCI catalogs and used the pinned
safe pretrained backbone with a random four-class head, without source fitting.
It targeted `backbone.blocks.11.attn.qkv`, rank 4, alpha 8, seed 11, one SGD step
at 0.0001, four support trials and query batches of eight. Both head policies
predicted all 496 subject-01 common queries with finite `[496,4]` logits.
LoRA has 3,200 trainable adapter parameters; enabling the head adds 804.
A repeated enabled-head episode reproduced state, losses and logits exactly.
The inner runner predicted all 496 subject-02 queries and declared subjects 03-09
for future source training. Caller source/RNG and all 36 input/manifest files,
nine episode records, selection record, checkpoint and model config were preserved.
There were four bounded support steps across fresh copies, zero source-training
steps and no accuracy calculation. Execution used CPU float32 and two threads.

The established quality command completed successfully:

```text
All checks passed!
Success: no issues found in 152 source files
452 passed, 4 warnings, 692 subtests passed in 98.19s (0:01:38)
```

Warnings comprise two existing EEGNet deprecations, one classification warning
and a pytest cache write-permission warning. Tests completed successfully.

Source fingerprint:
`f4a8501f868511fbaec29c2ede6d228e657b4fdc7f91b5ebdf20222d60a3eefc`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
Only `adaptation/labram_manifest.py` changed among pre-existing source/config/test
files. The new support module and test file account for the other source changes.
The quality status now identifies this source; its prior bytes were saved first.

Evidence: `runs/phase2/lora_manifest_checks/20260908_step16/`, including the before
snapshot, runner diff, real check script/log/receipt, immutable engineering
predictions, quality-command log, receipt and documentation preservation receipt.
Full quality logs are under `runs/quality/20260908T162412573577Z/`.
