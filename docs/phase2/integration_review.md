# Integrated P2 readiness review

> Historical review from milestone 13 (8 September 2026). The requirement table
> and ordered queue below describe that snapshot. Milestones 14-36 subsequently
> completed bounded BCI profile binding, method-complete and cohort-generic
> selection, the scientific run recorder, the pilot target-case executor, real
> Cho folds for the entire adopted roster, and generation, audit and binding
> end to end for all three datasets. See the [current status](README.md) and
> [MMIDB binding review](mmidb_binding_review.md). The delegated decision
> resolution adopted every agent-defensible choice; the user's recorded
> admission completed the measured pilot, and the scientific freeze is
> drafted as the working contract. Remaining owner acts: freeze
> ratification, the episode-eligibility policy, the Gate A rationale and
> the compute admission for E2; P2 remains partial and P3 is not yet
> complete.

8 September 2026. Thirteenth bounded step under the version 2 execution plan.
**The review is complete; P2 is not complete and P3 compute is not admitted.**
This is an implementation self-review with automated evidence checks, not
independent scientific sign-off. Gate A remains unsigned.

## Requirement-to-evidence assessment

| Requirement | Verified scope | Remaining condition |
| --- | --- | --- |
| P1 partitions and identities | All 170 current Profile A artifacts match the saved audit hashes. Nested 1/5/10/20-shot support and a common query pool are implemented in `evaluation/phase2_protocol.py`. | These identities do not establish model-specific preprocessing readiness. There are 168 eligible targets: BCI 9, Cho 52, MMIDB 107. |
| P2 encoder | [Reference comparison](forward_parity_review.md): 119 stage comparisons over seven CPU float32 cases match exactly. Safe checkpoint hash and all 221 tensor keys verified locally again. | Strict float32 joint-permutation invariance still fails its original tolerance. Preserve channel order. GPU/training parity and TUAB/TUEV downstream reproduction remain unverified under the adopted weaker route. |
| P2 same-backbone methods | Effective QKV LoRA, [linear/partial/full masks](tuning_integration_review.md), [adapters](adapter_integration_review.md) and [support-generated prompts](prompt_integration_review.md) have component/state tests and bounded checkpoint smokes. | They still need the common audited data/selection runner, trained source identity, matched anchors and integrated checks at every adopted shot level. Smoke optimizer values are not scientific search defaults. |
| P2 separate TCPL | Local TCN, support encoder, generator, Transformer, source-step and frozen-target helpers are implemented. [Manifest binding](tcpl_manifest_review.md) and [publication](tcpl_publication_review.md) have real BCI integration evidence. | The [reference discrepancies](tcpl_reference_review.md) remain unresolved. A local constructor contract does not satisfy the research plan's faithful-reproduction claim. Source episode scheduling, full selection and preprocessing are unfinished. |
| P2 preprocessing | `data/profile_b.py` implements the BCI Profile B path; nine BCI Profile B artifacts exist. Profile A audit inputs are 128 Hz / 512 samples per four-second trial. | No Cho or MMIDB Profile B subject artifacts exist in the configured processed-data directories. Bind original trial IDs across profiles, units, channel order, rejection policy and fit scope before encoder-ready claims. A cast or resampling of already band-limited Profile A cannot establish the broader Profile B filtering contract. |
| P2 source-only selection | `source_selection` declares outer exclusion and inner source-subject LOSO. The TCPL runner rejects forbidden subjects before execution. | No complete inner-fold search, stopping rule, source-fit provenance chain or common method dispatcher exists. MMIDB 079/100 remain in source cohorts but cannot use the target-style maximum-support episode; their source policy must be explicit. |
| P2 E1 feasibility | Original and safe checkpoint hashes verified. The safe downstream checkpoint has no mask token or output-vocabulary head. The configured omitted original keys are `student.mask_token`, `student.lm_head.weight`, `student.lm_head.bias`. | E1 is locally blocked by an unverified compatible discrete tokenizer and unverified complete masked-prediction forward/loss path. The cached reference contains fine-tuning code and utilities only. No one-recording loss, entropy or codebook-state check has run. Do not substitute a tokenizer or reconstruction loss. |
| P3 pilot/freeze | [Pilot specification](pilot_specification.md) and [machine-readable draft](pilot_specification.json) now enumerate the work and admission conditions. | The pilot has not run. Search budgets, training duration and total cost are not measured or frozen. |
| P4 execution integrity | TCPL engineering checkpoints and prediction JSON publish without clobbering; repeated inference verifies existing bytes. | Planned `evaluation/phase2_runner.py`, `scripts/phase2_pilot.py`, `scripts/run_phase2.py` and `scripts/audit_phase2.py` are absent. Shared claims, scientific cell audits, failure lineage, optimizer resume and complete-grid accounting remain future work. |
| Resources and checks | Current preflight: 7.7 GiB free, GPU capacity check passes. Control audit: 0/45 current-source fits valid, all 45 missing. | The unchanged 20 GiB disk floor fails. Control refresh remains required before a checked source commit. No scientific gate advances from this review. |

The TCPL local contract still says `episode_policy.status = "runner_not_implemented"`.
That field does not describe the newer bounded manifest runner clearly. Reconcile
it in the next relevant integration change without implying the scientific runner
or training budget is complete. This review does not silently change a configuration
hash that existing publication records bind.

## E1 feasibility outcome and scope

The local asset check covers `checkpoints/` top-level files, the configured safe
checkpoint, model directories in `.cache/huggingface/hub`, and the cached LaBraM
reference directory. The only cached hub model is the downstream LaBraM model.
This is a scoped local inventory, not a new search for external releases.
The original pickle checkpoint was hashed but not deserialized.

E1's outcome is **blocked, missing compatible tokenizer and verified masked
inference path**. Under the research plan this blocks E1, not unrelated E2
engineering. Clearing it requires pinned tokenizer/codebook and original head
identities, exact masks/targets/normalization, same-input reference loss agreement,
and proof that inference preserves tokenizer buffers. Merely locating a file or
recovering three tensor names is insufficient.

## Ordered work remaining

| Order | Bounded package | Acceptance evidence | Storage dependency |
| --- | --- | --- | --- |
| 1 — next | BCI cross-profile trial identity and encoder-input contract using existing A/B artifacts. | Independent joins on subject/session/run/original trial index; fixed support/query membership and class/channel order; explicit sampling/units/profile hashes; missing/duplicate/relabeled rows rejected; no unused maximum-support examples leak into query. | Can proceed with existing files and small tests. |
| 2 | Common Phase II manifest binding for six LaBraM methods and the two anchors; keep Phase I split APIs intact. | Identical permitted trial IDs for every method and every shot level, support-only fitted target transforms, source/query state checks, fresh episode state and method-specific parameter masks. | Bounded BCI checks can proceed; full-data preparation remains deferred. |
| 3 | Source-training and selection contract plus bounded executor. | Fixed candidate list and tie-breaks, source-only inner folds, explicit excluded/ineligible source handling, immutable fit history and seed provenance, no target-query tuning. Separate local TCPL evidence from faithful reproduction. | Toy/small integration first; full fits need admission. |
| 4 | Pilot recorder and scientific run-integrity foundation. | Measured stage timers/resources, content-bound records, exclusive cell claims, interruption/retry tests and an audit rejecting unexplained missing or duplicate cells. | Instrumentation can proceed without heavy training. |
| 5 | Prepare the missing admitted profiles, resolve affected method gaps, refresh controls, then run and audit the pilot. | Actual measured work fits the resource/schedule envelope; method/search/analysis settings and reusable source dependencies can then be frozen. | Requires resource admission; no launch from this review. |

E1 asset recovery can proceed independently when compatible assets are available.
The unresolved reference questions must remain visible in TCPL's admission status;
local TCPL timing can be measured as such without relabeling it faithful.
P5 causal E3 and hardware-faithful E4 preprocessing are separate unfinished work.
The offline zero-phase profile and causal TCPL convolution do not themselves
establish a causal end-to-end deployment path.

This is five engineering packages, not a five-day promise. A defensible calendar
estimate depends on the profile-preparation and source-fit pilot measurements.
The pilot specification supplies exact cell-count arithmetic and the cost formula
instead of treating historical synthetic smoke duration as a workload forecast.

## Evidence and preservation

Evidence is retained in `runs/phase2/readiness_review/20260908T145034Z/`:
`inspection.json`, `inspect_readiness.py`, `preflight.log`, `source_controls.log`,
`runtime_snapshot.json` and the final `receipt.json`. The inspection hashes all
170 audited Profile A artifacts, both LaBraM checkpoints, referenced numerical
receipts and the most recent quality logs. Profile B existence counts are an
inventory only; this review does not re-audit their signal contents.

The first inventory-script attempt read an enveloped parity flag at the top
level and stopped with `KeyError`; correcting the read to `payload` allowed the
inventory to complete. No model, test tolerance or scientific criterion changed.
The resource and control checks deliberately retain their nonzero results:

```text
preflight: exit 1; storage_ok=false
source_controls --check-only: exit 1; valid_records=0; expected_records=45
BCI artifact hashes verified: 9
Cho artifact hashes verified: 52
MMIDB artifact hashes verified: 109
```

Latest saved regression evidence remains:
`428 passed, 3 warnings, 614 subtests passed in 23.64s`, with lint/types passing.
Those logs match the unchanged source fingerprint
`8f06f3f62df988711715169302feb3cac132755bdf254341e45d0160186fe34f`.
They are historical checks, not reruns in this review. Current Python reports
3.12.14; previous numerical reports recorded 3.12.13. Future execution must bind
its actual runtime and revalidate affected evidence rather than assume equivalence.

Only documentation and review evidence changed. Original paired v2 plans, all
source/config/tests and historical records are preserved. The scoped runtime
snapshot is not a future worker/lock admission guarantee; no lock was removed.
No new prediction scores were read, training run, control refreshed or gate signed.
