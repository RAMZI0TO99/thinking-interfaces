# LaBraM adapter manifest integration

8 September 2026. Seventeenth bounded Phase II step.

`LaBraMTuningManifestRunner` now accepts `LaBraMAdapterSettings` and connects the
existing [adapter support loop](adapter_integration_review.md) to audited BCI
Profile B episodes. The existing source-selection reconstruction, pinned A/B
artifacts, fixed outer/inner permissions and complete common queries are retained.

## Interface and behavior

Settings explicitly declare classifier-qualified block targets, bottleneck width,
initialization seed, existing-head policy, support steps, learning rate and query
batch size. The settings digest includes every field. Duplicate or malformed
targets, invalid scalar settings, unknown blocks and excessive widths are rejected
before binding an episode. Width must be smaller than the block dimension.

Each prediction clones the plain CPU float32 source and installs fresh adapters
inside a saved/restored CPU RNG context. The existing support function takes a
separate clone and fresh SGD state. It receives only bound support signals and
labels. It freezes every original parameter except the explicitly enabled head;
all modules stay in evaluation mode. Adapters retain the verified serial residual
placement after each selected complete transformer block. Their zero up projection
preserves initial identity. The existing head is retained without reinitialization.

`AdapterMask` records the injection report (targets, width, placement and adapter
count), head policy and exact trainable names/count. Predictions use the existing
result format with source/adapted state identities and query-time state checks.
Query labels are attached only for subsequent scoring. The original tuning and
LoRA settings and adaptation paths retain their behavior.

## Limits and next step

This bounded runner accepts a plain source template; it does not restore previously
trained source adapters, fit source subjects, select hyperparameters or authenticate
training history. Settings are engineering inputs, not frozen scientific choices.
Results remain `engineering_only=true` and
`source_training_history_verified=false`. CPU integration does not establish
accuracy, GPU parity, runtime-pilot completion or scientific gate approval.

Next is support-generated prompt integration under the same audited runner roles,
followed by matched anchors and the remaining source-fit/selection work. The user
asked to keep the RAM-dependent control refresh deferred; no refresh or heavy
experiment is launched by this coding milestone. Its resource guards are unchanged.

## Validation

Seven new tests / 23 subtests cover all four shot levels, exact support dimensions,
common query identity, both head policies and actual down/up projection updates.
They verify frozen source tensors, caller modes/gradients/RNG, seeded reset and
isolation from later caller mutations. Changing only query labels preserves
support losses, adapted state and logits. Invalid roles, assets, targets and widths
fail closed. Deliberate query state changes and nonfinite logits are rejected.
A failed initialization also restores RNG and preserves the source.

The initial focused run exposed a misplaced assertion in a new test; it was
corrected and its log retained. Final focused checks: 12 passed / 40 subtests,
including the five existing adapter tests. Full quality checks:

```text
All checks passed!
Success: no issues found in 152 source files
459 passed, 4 warnings, 715 subtests passed in 111.23s (0:01:51)
```

Warnings are the existing two EEGNet deprecations, classification warning and
pytest cache write-permission warning. The complete quality bundle passes its
independent exact-source/log-hash validation.

## Real-data check and provenance

The CPU check reconstructed all nine BCI catalogs and verified the saved selection.
The source template used the pinned safe pretrained backbone with a random
four-class head and no source-subject fitting. Engineering settings were block 11,
width 4, seed 11, one SGD step at 0.0001, four support trials and query batches of
eight. Both head policies predicted all 496 subject-01 common queries with finite
`[496,4]` logits. Adapter-only parameters total 1,804; enabling the head adds 804.

The enabled-head repeat reproduced losses, state and logits exactly. A separate
inner runner predicted all 496 subject-02 queries while declaring subjects 03-09
for future source training. Four bounded support steps occurred across fresh
copies; zero source-training steps and no accuracy calculation occurred.
Caller source/RNG, all 36 A/B input/manifest files, nine episode records, selection,
checkpoint and model config were preserved. Execution used CPU float32/two threads.

Source fingerprint:
`6e7d0992848f7c2375dbc3337f5de0aeb703640e9895fe326a66f0b3d7411c21`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
Only `adaptation/labram_manifest.py` changed among pre-existing source/config/test
files; `tests/test_labram_adapter_manifest.py` is new. The existing adapter code
is unchanged. The previous quality status was saved before the new check updated it.

Evidence: `runs/phase2/adapter_manifest_checks/20260908_step17/`, containing before
snapshots, runner diff, focused logs, real check script/log/receipt, immutable
engineering predictions, quality status, receipt and documentation preservation
receipt. Full quality logs: `runs/quality/20260908T163435524562Z/`.
