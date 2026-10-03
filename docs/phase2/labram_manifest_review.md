# LaBraM manifest-bound support tuning

8 September 2026. Fifteenth bounded Phase II step.
`adaptation/labram_manifest.py` connects the verified BCI Profile B binding to
linear, partial and full LaBraM support tuning. This is bounded engineering
integration; source-model training and scientific evaluation remain unfinished.

## Interface and permissions

`LaBraMTuningManifestRunner` takes the project root, protocol, all nine trusted
BCI catalogs, saved source-selection envelope, source classifier and a complete
mapping of `BCIProfileAssets`. Each asset entry pins the A manifest, B artifact
and B manifest hashes; the catalog pins A artifact identity.

The constructor reconstructs source selection from the catalog cohort and compares
the complete envelope, checks both profile directories against all nine subjects,
and validates the fixed four-class/22-channel source classifier. The supported
backbone accepts 800 samples in 200-sample patches, with finite CPU float32 state.
It owns a deep copy of the source; later caller mutations cannot change this copy.

- A final runner's `predict_target` can consume only its fixed outer target's
  episode. `predict_validation` is unavailable on that runner.
- A runner constructed with an inner-validation subject exposes only
  `predict_validation`; it rejects outer-target prediction before binding data.
- Wrong-subject or altered episode records fail the existing independent binding
  check before adaptation. Query subsets and arbitrary signal/label overrides
  are absent from the public prediction API.
- `training_subjects` excludes the outer target and, where present, the inner
  validation subject. This declares permission for future source fitting; this
  class has no source-training operation and cannot authenticate the template's
  previous training subjects from weights.

`LaBraMTuningSettings` requires an explicit method, positive fixed step count and
learning rate. Partial tuning additionally requires a valid depth; depth is rejected
for linear/full tuning. Query batch size is explicit, defaulting to eight.
Settings have a deterministic digest and are engineering inputs, not selected or
frozen scientific hyperparameters.

## Adaptation and prediction

The existing [profile binding](profile_binding_review.md) reconstructs the selected
subject's A catalog and entire episode, verifies pinned A/B bytes and manifests,
and returns B arrays in the unchanged support/query order. Stored values receive
no additional scaling, rejection or learned target transformation.

Only support signals and support labels enter `adapt_labram_tuning_support`.
It starts from the same owned source snapshot on every call, using fresh model
and SGD state. Existing [tuning masks](tuning_integration_review.md) are retained:
linear updates the head; partial updates final blocks plus head; full updates
the whole model. Modules remain in evaluation mode during support gradients.

The runner then predicts every common query in fixed batches under inference
mode. It rejects nonfinite or incorrectly shaped logits and checks full state
digests before/after query execution. The owned source must also remain unchanged.
Query labels are attached only to the returned result for later scoring.

`LaBraMTuningPrediction` records the profile binding, role, reconstructed selection
digest, source/adapted state digests, settings, exact parameter mask, support losses,
logits and targets. It always reports `engineering_only=true` and
`source_training_history_verified=false`. A state digest identifies tensor contents;
it is not a checkpoint-origin or training-history certificate. No scientific record
publisher, source-fit resume, candidate selector or accuracy calculation is added.

## Real-data check

All nine BCI catalogs were reconstructed, and the saved outer-source selection
was verified. The source template used the pinned safe pretrained backbone and
a newly initialized four-class head, without any source-subject fitting.
The bounded CPU check used one support example per class, one SGD step at 0.0001,
and query batches of eight:

| Method on subject 01 | Trainable parameters | Common-query logits |
| --- | --- | --- |
| Linear | 804 | `[496,4]`, finite |
| Partial, final two blocks | 965,764 | `[496,4]`, finite |
| Full | 5,818,540 | `[496,4]`, finite |

Every method changed its adapted state while preserving the source. Repeating
the linear episode reproduced the losses, adapted state digest and logits exactly.
A separate inner runner predicted all 496 subject-02 common queries; its permitted
source cohort is subjects 03–09, excluding both subject 01 and subject 02.

There were **five bounded support steps** including the repeat and validation
check, each on a fresh copy with four support trials. There were **zero source
training steps**. No accuracy metric was calculated. All 36 input/manifest files,
nine saved episodes and the saved selection record retained their hashes.
The caller model, safe checkpoint and model configuration were preserved.

Execution used Python 3.12.14, Torch 2.13.0+cu130, CPU float32 and two threads.
Checkpoint SHA-256:
`53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`.
The engineering prediction record SHA-256 is
`74f1bfd892383a1ca59d45a22c55638b4927009b2595ccecad2770a8927bb9a2`.

## Tests and evidence

Eight new tests and twenty subtests exercise all three methods at all four shot
levels using the installed two-block LaBraM fixture. They verify exact support
dimensions, fixed query IDs, effective updates, source/caller state and RNG
preservation, repeated reset and isolation from later caller mutations. Role,
selection, inventory, settings and pinned-file violations fail before execution.

A discriminator changes only bound query labels: adaptation losses, state and
predictions remain identical while returned scoring targets change. Separate
negative controls deliberately mutate query-time head state or produce NaN logits;
both are rejected and the source remains intact. The focused tests passed;
type annotations and test closure binding were corrected before final checks.

Full lint passes; strict types pass for 151 source files. Full regression:

```text
445 passed, 3 warnings, 660 subtests passed in 63.53s (0:01:03)
```

The warnings are the existing EEGNet deprecation and classification warnings.

Source fingerprint:
`7c32a0c43a13ac6300994180db1b9b7e1bbc761873d056872a16502af60a72bf`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
All pre-existing source/config/test files retain their before-step hashes.

Evidence directory: `runs/phase2/labram_manifest_checks/20260908_step15/`.
It contains `receipt.json`, full lint/type/test logs, `real_manifest_check.py`,
`real_manifest_receipt.json`, immutable `engineering_predictions.json` and the
documentation preservation receipt. Results remain local engineering evidence.

## Remaining scope

Next is effective-QKV LoRA integration with the same audited support/query and
role boundaries. Adapters, prompts and matched anchors follow within the common
runner package. Complete source-only selection, source-fit provenance, scientific
publication and the measured pilot remain outstanding. This step does not establish
raw-preprocessing reproduction, author parity, causal deployment or a scientific
gate pass. Heavy training and source-bound control refresh remain deferred.
Final free disk is 22.04 GiB, above the unchanged 20 GiB minimum at this snapshot.
Storage headroom alone does not complete the remaining experiment-admission checks.
