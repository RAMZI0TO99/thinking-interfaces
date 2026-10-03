# Bounded LaBraM source training and selection

8 September 2026, milestone 21. This extends P2 with source fitting for the plain
LaBraM linear, partial and full tuning paths and complete source-only candidate
selection. It is a bounded BCI engineering implementation. Source-trained LoRA,
adapters and prompt generators remain the next separate integration package.

## Contract

`adaptation.labram_source.BCILaBraMSourceSelector` consumes the nine audited BCI
catalogs, source-selection envelope, pinned Profile A/B assets and a plain LaBraM
template with an explicitly supplied full-state hash. It validates the actual
existing manifest runner's cohort, architecture, montage, shape and CPU float32
requirements. Missing subjects, changed template state, malformed records and
unsupported architecture fail before fitting.

`LaBraMSourceSettings` declares a source parameter mask (`linear`, `partial` with
an explicit depth, or `full`), fixed steps per subject, batch size and SGD rate.
`LaBraMSourceCandidate` pairs those settings with the existing plain-method support
settings. Candidate names and configurations must be unique. All candidates must
evaluate one support method: the selector compares declared settings within a
method, not the research methods against each other. Source and support masks can
differ when explicitly declared. LoRA, adapter and prompt settings are rejected
by this contract rather than treated as trained plain models.

The supplied template remains unchanged. An owned copy preserves its backbone and
resets the linear head using the explicit seed. Every inner and final source fit
clones this same initialized state and starts a fresh SGD optimizer. Both the
supplied template and initialized state hashes are recorded. Earlier training of
the supplied backbone remains unverified by this API; the real check separately
verifies the existing safe pretrained checkpoint and model-configuration hashes.

## Source data and fitting

An inner fold excludes both the outer target and the inner-validation subject from
source fitting. A final fit excludes only the outer target. The outer target's
signals and query outcomes are never read by the executor; its catalog remains
part of the trusted cohort identity and eligibility checks.

Each permitted source is loaded through the existing Profile A-to-B episode binder
at the maximum support size. The maximum pool plus fixed queries covers all retained
source trials. The executor verifies that union against the complete source catalog,
then samples trial IDs in catalog order through a seeded permutation. Those are
training subjects, so all their retained trials are permitted source-training data.
The inner subject's support and queries retain their original separate roles during
validation. The outer subject never enters either role.

Training signals come from unchanged Profile B: 22 named BCI channels, 800 samples
at 200 Hz, stored units of 0.1 mV and no extra amplitude scaling. Profile A determines
retention and trial identity only. Batches are assembled by ID from the verified
binding, so physical Profile B row order does not define source-training order.
Only one source episode is retained at a time; there is no whole-cohort signal copy.

The existing LaBraM tuning masks determine trainable tensors. Linear updates only
the head; partial updates the specified final complete blocks plus head; full
updates all backbone/head parameters. All modules remain in evaluation mode.
Normalization affine parameters follow the mask, buffers remain fixed and dropout
is disabled. SGD has no momentum or weight decay and uses fixed steps with no early
stopping. The seeded sampling generator is independent of caller RNG. Subject
permutations wrap without reshuffling if the requested steps exhaust their trials.

Every source step records its subject, exact trial IDs, within-subject step, wrap
count, finite loss and resulting full-state digest. Each fit records the parameter
mask, input bindings, optimizer/settings and initial/final state digests. Frozen
parameters and buffers are compared with their starting values before a fit returns;
selected gradients and updated parameters must remain finite. Gradients are cleared.

## Selection and evidence

`run_fold(candidate_name=..., validation_subject=...)` is an explicitly incomplete
diagnostic and never returns a selected candidate. `run_selection()` completes all
eight inner folds for every candidate. Each fitted source goes through the existing
LaBraM manifest runner for support adaptation and all common-query predictions on
the inner subject. The prediction's source-state hash must match its fit history.

Class recall is computed from the full inner-query confusion matrix, averaged
within each subject, then averaged equally across the eight subjects. The fractions
are exact rationals. Logit ties use the first class index; equal candidate scores
choose the first candidate in the declared roster. There is no external-score
import, partial-result resume or target-query tuning. A failed fold produces no
winner or final fit. After selection, the winner starts from the original seeded
initialization and fits all eight permitted source subjects afresh.

The caller declares a total source-plus-support gradient ceiling. Complete selection
is checked against its worst-case total, including the winning final fit, before
the first update. Hard engineering ceilings are 256 steps per invocation and eight
trials per source/query batch. These small CPU bounds do not admit heavy training
or replace the existing disk/RAM/thermal guards. The deferred control refresh is
not invoked. Failed-attempt recording, optimizer resume and scheduling remain open.

Immutable `SelectionEvidence` reuses the existing canonical engineering-envelope
and atomic no-clobber writer. The contract pins source/Git identity, templates,
input inventory, candidates/order, seed, protocol, units and the recorded CPU runtime.
Source/config identity, owned initialization and runtime are checked before public
execution and before evidence returns. The complete installed environment is not
certified. Returned weights are mutable and must be checked against their final-fit
digest on reuse. Existing arbitrary-template runners retain their unverified
source-history flag; no scientific history certification or cell publication occurs.

## Verification

The focused source suite passed seven tests and twenty subtests; an additional
iterator-wrap test passed separately. Tests independently reconstruct each source
batch from raw Profile B NPZ rows and replay all seven updates for each of the
three masks, reproducing every full-state hash. They check frozen tensors, caller
weights/modes/flags/gradients/RNG, seed effects, cleared fit gradients and exact repeats.
Actual eight-fold selection also succeeds with both outer-target artifacts replaced
by unreadable bytes. Other checks cover ranking and ties, a fresh final fit,
incomplete/failed folds, no-clobber evidence, bad contracts and budgets, corrupt
source data, nonfinite loss, injected frozen-state mutation, context changes and wraps.

Evidence is recorded in `runs/phase2/labram_source_checks/20260908_step21/`.
Full lint and strict types pass. The exact-source suite passes **490 tests / 794
subtests**, with four existing warnings. The raw summary and immutable quality
log identities are retained in the milestone receipt.
The real check uses the pinned safe pretrained
backbone, seed 23, CPU float32 and two Torch threads. It declares two linear-source
learning rates (0.001 and 0.002) before selection, one two-trial source step per
subject, one-shot support SGD at 0.0001 and query batches of eight. The main
selection ceiling is 136 gradient steps. Separate partial-depth-one and full
diagnostics use the same seven-source inner fold, source/support rate 0.0001 and
one step per source/support episode. These settings exercise the code and are not
scientific search defaults or evidence of convergence.

The real check passed both linear candidates across all eight inner subjects
(02 through 09), using outer subject 01. It covered 7,924 complete inner-query
predictions: subject 09 has 490 queries and the other seven inner subjects have
496, per candidate. Each inner source fit sampled 14 trials in seven steps. The
winner was fitted afresh on eight source subjects, sampling 16 trials in eight
steps. Repeating the first linear fold was exact. Partial and full tuning each
completed a separate seven-source inner fit, one support step and all 496 queries.

Actual source trainable counts were **804** for linear, **483,284** for partial
depth one and **5,818,540** for full tuning. Including the repeated linear fold
and the partial/full diagnostics, work totaled **141 source steps and 19 support
steps**, with **zero outer-target predictions**. Partial/full diagnostic evidence
remains incomplete selection evidence; a complete real-data candidate search was
performed only for the declared linear candidates.

The selected final source was saved as safetensors and strictly reloaded with an
identical state digest. All 36 original Profile A/B artifacts/manifests, nine episode
records and the original selection record retained their hashes. The caller's
template/RNG, source identity and pinned safe backbone/configuration files were
preserved. The output checkpoint is a bounded engineering source fit, not a
converged research model or proof of the supplied backbone's training history.

Current source fingerprint:
`c3b08d8556e5dd639f6ba1860faa5faad785020ef6977f7a6b609aa13f9c0004`.
Only the new LaBraM source module and its test file were added to source/config/tests.
All pre-existing implementation files, configurations, prior evidence and the
historical documentation prefixes are preserved; prior quality status is saved.

## Remaining work

Next is source-trained LoRA, adapters and support-generated prompts, including
carrying their learned components into validation without reinitializing them.
The existing support runner currently creates fresh components per episode, so it
cannot stand in for that future contract. TCPL and EA selection integration, broader
dataset coverage, scientific run histories/checkpoint publication, resource admission,
the measured P3 pilot and the scientific freeze remain open. P2 is still partial.
No control guard, gate, method configuration or frozen scientific comparison changed.
