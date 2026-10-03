# LaBraM support-prompt manifest integration

8 September 2026. Eighteenth bounded Phase II step.

`LaBraMTuningManifestRunner` now accepts `LaBraMPromptSettings`, connecting the
existing [support-prompt implementation](prompt_integration_review.md) to audited
BCI Profile B episodes. All six same-backbone LaBraM support methods now have a
path through this bounded BCI runner. This does not complete their source-training
or scientific experiment workflows. TCPL remains its separate implementation.

## Settings, conditioning and state

Settings explicitly declare prompt-token count, generator hidden width, seed,
existing-head policy, support steps, learning rate and query batch size. Their
digest includes all fields. Invalid dimensions/scalars and an unsupported encoder
configuration fail before episode binding. Prompts require the verified
neural-tokenizer encoder with its CLS head. Existing subject roles, complete
common queries, selection reconstruction and pinned A/B identities are retained.

Each prediction initializes a fresh generator within a saved/restored CPU RNG
context. The existing support loop clones the plain CPU float32 source and the
generator, extracts frozen unprompted support features one trial at a time, and
caches copied features and labels. It pools by class in fixed label-index order,
then generates tokens using Linear-GELU-Linear. Only bound support signals and
labels enter conditioning and optimization. Fresh SGD updates the generator and
the explicitly enabled existing head; all other source parameters are frozen.
All modules stay in evaluation mode.

Tokens are inserted once after position/time assembly in the order
`[CLS, prompts, EEG patches]` and persist through every original block. Added
tokens do not have an initial-identity guarantee. `PromptMask` records token count,
hidden width, generator count, conditioning, placement, head policy and exact
trainable names/count. The shared result includes source/adapted state identities,
support losses, binding and predictions. The adapted state digest includes cached
support features and labels; query-time changes to them are rejected. Query labels
are attached for later scoring and never enter adaptation.

## Remaining scope

The generator is freshly initialized for each engineering episode. The runner does
not accept a source-trained generator, fit source subjects, select hyperparameters
or authenticate prior training subjects. Settings remain engineering inputs and
results remain `engineering_only=true`, `source_training_history_verified=false`.
This check does not establish accuracy, GPU parity, author reproduction or pilot
completion. Cho/MMIDB runner coverage and their missing Profile B artifacts remain
outstanding alongside source-fit provenance and source-only selection.

Next bounded step: matched anchor integration using the same audited support/query
and subject permissions. The RAM-dependent control refresh remains deferred at the
user's request, with its guards unchanged. No full experiment or gate signing is
authorized by passing these engineering checks.

## Validation

Seven new tests / 25 subtests cover all four shot levels, exact support sizes,
common query identity, both head policies and effective updates in both generator
projections. Cached support features are independently recomputed from the frozen
source one trial at a time and match exactly. Caller model state, modes, gradients,
RNG and generator template are preserved. Repeats reproduce exactly; changing the
seed changes settings and adapted-state identities and predictions.

Changing only query labels leaves adaptation losses, state and logits identical.
Invalid roles, altered artifacts, invalid settings and unsupported encoder heads
fail closed. Deliberate query-time head or cached-feature mutation and nonfinite
logits are rejected. Failed generator initialization restores RNG and source state.
The original prompt component tests remain unchanged.

Focused checks: 13 passed / 34 subtests. Full quality checks:

```text
All checks passed!
Success: no issues found in 152 source files
466 passed, 4 warnings, 740 subtests passed in 167.08s (0:02:47)
```

Warnings are the existing two EEGNet deprecations, classification warning and
pytest cache write-permission warning. The quality bundle is verified against
the final source fingerprint and log hashes.

## Real-data check and provenance

The bounded CPU check reconstructed all nine BCI catalogs and verified the saved
selection. It used the pinned safe pretrained backbone with a random four-class
head and fresh random generator, without source-subject training. Engineering
settings: two prompt tokens, hidden width eight, seed 11, one SGD step at 0.0001,
four support trials and query batches of eight. Both head policies predicted all
496 subject-01 common queries with finite `[496,4]` logits. The generator has
10,008 parameters; enabling the head adds 804, for 10,812 trainable parameters.

The enabled-head repeat reproduced losses, state and logits exactly. A separate
inner runner predicted all 496 subject-02 queries while declaring subjects 03-09
for future source training. Four support steps occurred across fresh episodes;
zero source-training steps and no accuracy calculation occurred. Caller source/RNG,
all 36 A/B artifact/manifest files, nine episodes, selection, checkpoint and model
config retained their identities. Execution used CPU float32 and two threads.

Source fingerprint:
`527c0c8b0d4cdb575e0f3c359740e199d68a906374aaf8283f587c10713d148b`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
Only `adaptation/labram_manifest.py` changed among pre-existing source/config/test
files; `tests/test_labram_prompt_manifest.py` is new. The prior quality status was
preserved before the new exact-source checks updated it.

Evidence: `runs/phase2/prompt_manifest_checks/20260908_step18/`, with before
snapshots, runner diff, focused log, real check script/log/receipt, immutable
engineering predictions, quality status, receipt and documentation preservation
receipt. Full quality logs: `runs/quality/20260908T164418467063Z/`.
