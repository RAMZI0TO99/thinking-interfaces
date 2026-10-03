# Source-trained LoRA integration

8 September 2026, milestone 22. The bounded BCI LaBraM selector now trains effective
QKV LoRA on permitted source subjects and carries the learned low-rank weights into
inner validation. A new manifest runner also supports the fixed outer-target role.
This is engineering integration; adapters and prompt generators remain separate
source-training work.

## Changes and interfaces

`adaptation.labram_lora_trained` introduces `LoRASourceSettings`,
`LoRAContinuationSettings`, `LoRASourceCandidate`, initialization/continuation helpers
and `TrainedLoRAManifestRunner`. The existing `BCILaBraMSourceSelector` accepts the
new candidate type alongside plain tuning candidates. A search still requires one
method throughout its roster. Plain-method settings and the old fresh-LoRA support
runner retain their behavior.

Source settings explicitly name QKV targets, rank, alpha, initialization seed,
source head policy, steps per source subject, batch size and SGD rate. Continuation
settings declare support head policy, steps, rate and query batch size. They contain
no initialization seed or replacement rank: continuation must preserve the learned
components. Source and support head policies are independent and explicit.

Each source fit starts from the selector's pinned backbone and common seeded head,
then initializes effective-weight LoRA with its separate declared seed. The original
QKV weights, backbone and normalization parameters stay frozen; LoRA A/B tensors
and the optionally enabled head receive fresh SGD. Subject sampling, source/inner
exclusions, Profile B binding, units, step ceilings and fixed normalization follow
the existing source selector. Every step records actual trial IDs, loss and full
state digest. Source records now distinguish the plain seeded initialization from
the fit's initialized LoRA state. Candidate-specific rank/targets/alpha/seed remain
part of the hashed candidate contract.

## Learned-weight continuation

The new runner receives a trained model, its expected state digest and explicit
source LoRA metadata. It validates the installed target inventory, exactly one
effective-weight parametrization per declared QKV, A/B dimensions, original model
architecture, finite CPU float32 state and the scalar `alpha/rank` scaling. The
model is copied into owned state; a supplied model's earlier training remains
unverified by this general runner.

Existing BCI cohort, class/montage, profile, selection-envelope and role checks are
reused through a plain architecture-admission copy. That copy is never used for
prediction. Installed Torch's parametrization removal deletes a property from the
dynamic class shared by deep copies. To preserve the trained caller, admission
replaces QKV modules only inside its owned copy instead of removing their shared
parametrization properties. Tests execute the original trained model afterward.

Support continuation deep-copies the complete learned model, retains its A/B
tensors and head, applies the declared head policy, and starts fresh SGD. It never
calls LoRA injection or resets learned parameters. Only audited selected support
signals/labels enter this update. Frozen parameters and buffers must stay exact;
losses, gradients and updated state must remain finite. Full common-query inference
uses the resulting model and must change neither its tensor state nor LoRA scaling.
Scaling is checked explicitly because it is a Python scalar outside `state_dict`.

Both `predict_validation` and `predict_target` enforce fixed constructor roles and
reconstruct/bind the requested episode. An inner runner cannot predict the outer
target. The returned prediction identifies the source state, source-settings hash,
support mask/losses, adapted state, complete binding and the policy
`continue_source_trained_lora_without_reinitialization`. Its general source-history
flag remains false; a tensor hash cannot authenticate arbitrary historical subjects.

## Selection and persistence

Complete selection evaluates every candidate on all eight source-only inner folds.
Each source fit excludes outer and inner subjects; validation must start from its
recorded fitted state. The record links that state to the continuation prediction
and preserves the source-settings identity. Exact subject-averaged balanced accuracy
and declared-order tie breaks are unchanged. No externally supplied scores or
partial-result resume are accepted. A diagnostic fold cannot produce a winner.
After complete selection the winning candidate is fitted afresh on eight sources,
including fresh initialization rather than reuse of an inner-fit model.

Engineering evidence remains canonical immutable JSON with atomic no-clobber
writes. Safetensors holds the selected source's original and low-rank tensors.
Reload must reconstruct the same LoRA structure and scaling from its recorded
metadata before strict state loading; the tensor file alone cannot specify alpha.
No scientific checkpoint/history publication, optimizer resume or gate signing
was added. Heavy resource admission and the user's deferred control refresh remain
separate; no guard was changed.

## Verification

The focused suite passed **7 tests / 16 subtests**. It independently replays seven
source updates from Profile B rows using the effective-QKV implementation and
reproduces every full-state hash. Learned A and B tensors change while original
weights remain frozen. Caller template/RNG and cleared-gradient behavior are checked.

For all four source/support head-policy combinations, a pre-forward observation
shows that continuation starts from the exact trained state. A patched injection
function raises if reinitialization occurs. Only selected support inputs are seen,
the expected tensors change and the original trained model still forwards after
architecture admission. Other tests cover complete selection with unreadable outer
A/B artifacts, both roles and all four shot levels, altered query labels/signals
leaving the fit unchanged, scalar scaling tampering invisible to state hashing,
query tensor mutation, malformed settings/roles/pins, nonfinite loss, safe structural
checkpoint reconstruction, exact repeat and immutable incomplete evidence.

The bounded real check uses the existing pinned safe pretrained backbone, head and
sampling seed 23, LoRA seed 11, last-block QKV, rank four and alpha eight. Two
candidates declare source rates 0.001 and 0.002, one two-trial source step per
subject, one-shot support SGD at 0.0001 and query batches of eight. Both train the
head. The full selection ceiling is 136 total gradient steps. Separate diagnostics
freeze the head during support only and during both source/support fitting. These
are explicit engineering choices, not frozen scientific search settings.

The real check passed both candidates across all eight inner subjects: 16 complete
folds and 7,924 common-query predictions. Each inner source fit used seven steps
on 14 sampled source trials, followed by four support trials. Subject 09 has 490
queries and the other inner subjects have 496. The winner received a fresh
eight-source fit on 16 sampled trials, and the first fold repeated exactly.
The two frozen-head diagnostics also passed with 496 queries each.

The declared last-block LoRA has 3,200 trainable low-rank parameters and an optional
804-parameter head (4,004 total when enabled). Including repeat and diagnostic work,
the check performed **141 source steps and 19 support steps**, with **zero outer-target
predictions**. Learned LoRA state was retained throughout validation. The selected
checkpoint was loaded into a newly reconstructed LoRA architecture with identical
state; source/template/RNG and all original input/audit hashes were preserved.

Full lint and strict types pass. The exact-source suite passes **497 tests / 810
subtests**, with four existing warnings. The raw summary and immutable quality
log identities are retained in the milestone receipt.
Evidence is in `runs/phase2/lora_source_checks/20260908_step22/`. Current source:
`1354b457030270632fe6bcff3a98142bd7c6ee1692dd128ffd5b713c3cc84649`.
The source selector is the only pre-existing source file changed. Its saved diff
contains the candidate/fit/validation additions; other prior source/config/test
hashes are preserved. Historical quality status and documentation prefixes are saved.

## Next work

Next is source-trained adapter integration, then the support-generated prompt
generator, preserving each learned component through validation. TCPL/EA selection,
broader datasets, scientific run recording and history validation, the measured P3
pilot and scientific freeze remain open. P2 is still partial. No full experiment,
independent scientific approval or resource-dependent control refresh was performed.
