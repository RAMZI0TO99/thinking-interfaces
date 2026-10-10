# Inference-query cache integration preparation

The [namespaced successor](NAMESPACED_INTEGRATION_REVIEW.json) now passed15 fresh
synthetic checks and120 execution-review checks with relative imports and
unchanged cleanup confinement. See its [validation report](namespaced_candidate_validation_20261010.md)
for the corrected fixture paths, source lineage and production adoption boundary.

The [tested inference adapter copy](source_selection_cache_scope_inference.py)
and its three dependencies are now pinned by the [integration manifest](INTEGRATION_REVIEW.json).
The [adoption plan](integration_adoption_plan_20261010.md) records23 actual Source
preparation checks and the module-location ownership-root constraint. This adds
reviewable source packaging, with no production integration or new model run.

## Completed adapter and source diagnostics,10 October

The separate inference selector adapter now passed all15 fixture checks and a
123-check execution self-review. All51 no-fit source queries passed a768-check
combined review, and the221 actual source-step batches passed a separate852-check
review with exact original/cold/copied/warm logits and442 cache hits. This follows
the40-check inference fixture and source02 comparison recorded below. See the
[completed diagnostic report](cache_diagnostics_20261010.md) for actual scopes,
resource envelopes, preserved failures and ownership requirements for adoption.
Older sections retain their original preparation snapshots. No real-data fit,
full selector, new case, production integration or scientific signature followed.

## Executed inference checkpoint,10 October

The candidate below now passed40 actual synthetic checks and the pinned real
source02 no-fit comparison. Exact original/cold/warm/copied logits were preserved
under inference mode, with exact ordinary-context reuse and ordinary detached
retained values. The synthetic transition test preserved head losses, gradients,
updates, full state and RNG after an inference-first miss. Real training, target
data, accuracy and case claims remained absent.

| Batch | Original mean | First cold | Warm mean | First copied reuse |
| --- | ---: | ---: | ---: | ---: |
|2|247.305ms|265.349ms|2.336ms|18.239ms|
|8|1077.019ms|1074.903ms|4.524ms|22.094ms|

Actual cache statistics were2 misses,24 hits, no bypass/eviction and8000 retained
feature bytes. Pinned model state remained `90a9d34e`; Source stayed `b7452847`
/431 files at clean execution Git `c8d10e8`. Native times were64.891/36.247s,
maximum Job peak2.821GiB. Features/wrappers/private files and owned Jobs/handles
cleared. Root's105-check self-review accepted diagnostics and release only.
It recorded two retained exited Windows objects with exit0 without falsely
calling their PIDs absent; the earlier failed review/source remain preserved.

The tested [inference cache copy](frozen_feature_cache_inference.py) preserves
the exact executed candidate bytes. The separate selector adapter using it is
prepared with15 lifecycle checks, which remain unexecuted. The original scope
and frozen production are preserved. This recipe is not a standalone release.

Current cold forwards were slower than historical samples. Remaining26 query
subjects are now prepared in13 units of two, with all51 total sources retained,
the original no-grad diagnostic route, batch8 and unchanged180/210 ceilings.
Source-only preflight checked33 runtime files. Subsequent actual entry checks
held for startup RAM and created no remaining model attempt. These samples still
do not prove a complete selector within480 seconds or sign a scientific gate.

- [Actual40-check fixture](../../../runs/coordination/cache_performance_20261008_v1/inference_feature_fixture_001/result.json)
- [Actual pinned real inference comparison](../../../runs/coordination/cache_performance_20261008_v1/inference_feature_forward_001/result.json)
- [105-check execution self-review](../../../runs/coordination/cache_performance_20261008_v1/inference_execution_root_review_20261010_001.json)
- [Smaller remaining query scope](../../../runs/coordination/cache_performance_20261008_v1/source_query_remaining_scope_20261010_001.json)
- [Prospective15-check adapter fixture](../../../runs/coordination/cache_performance_20261008_v1/inference_scope_preparation_20261010_001.json)

## Initial Source-preparation snapshot

10 October2026. This records Source-only preparation and executed arithmetic.
It records no new numerical fixture, real source forward, selector or case.

## Integration finding

The original [manifest predictor](../../../adaptation/labram_manifest.py) enters
`torch.inference_mode()` for every validation-query batch. The current tested
[feature cache](frozen_feature_cache.py), SHA-256 `f55fa5be`, bypasses that mode.
The completed25-subject diagnostic used no-grad original/cold/warm forwards;
its4078 query trials and measured warm reduction remain valid for that route.
They do not establish validation-query reuse in a complete original selector.
The original caller mode remains part of the integration contract.

## Separate prospective candidate

The new operational candidate has SHA-256
`d5eff3a68996a6f6918fee0ace83572767f1ef3df1b85712989331443ce4c8c1`.
The tested candidate, production, raw inputs and weights are preserved.
The new code admits inference-mode queries only with supported ordinary frozen
backbone state. It evaluates the actual backbone and live head in the caller's
mode, then retains an ordinary detached feature clone outside inference mode.
That private stored value is intended to support later gradient-enabled head
updates. Inference-created backbone parameters/buffers still bypass. Existing
hook, trainable-backbone, input-layout, state/forward invalidation and byte-budget
rules remain. Numerical equivalence and transition safety are **not yet proven**.

The pinned fixture plans40 checks:15 existing input/selector checks,8 disk-cache
checks and17 feature checks. Four added checks exercise exact inference cold/hit
outputs and ordinary retained values, subsequent exact head losses/gradients/
updates, copied-model reuse and output mutation isolation, and rejection of
inference-created backbone state. Existing complete tiny linear/full/LoRA
selectors remain in the suite; their model training is synthetic fixture work.

The separate real no-fit worker plans original/cold/hit/copied-model inference
comparisons at batch2 and8, then exact reuse in an ordinary no-grad context.
Model state/RNG, operation bytes, source pins and private-file cleanup must
remain unchanged. It constructs no optimizer and performs no real-data training,
target access, accuracy calculation or case claim. Copied model state is created
before entering inference mode, matching the original prediction route.

## Conservative capacity arithmetic

The unchanged original two-candidate linear recipe has51 source subjects,
50 training subjects per validation fold, one source step per subject at batch2,
and a final51-step source fit. Its complete declared source budget is5151 steps.
Each fold performs one support step at two-class five-shot and predicts its
common query in batches of8.

The executed all-source loader receipt records10,309 retained source pool trials.
Using every retained pool trial as a query upper bound and counting every
declared encoding as a new feature value gives:

| Contribution | Trial encodings | Float32 feature-value bytes |
| --- | ---: | ---: |
| All source SGD batches, including final fit |10,302|8,241,600|
| Validation queries for both candidates, using full pools as upper bounds |20,618|16,494,400|
| Validation support steps at five-shot |1,020|816,000|
| Total upper bound |31,940|25,552,000|

Each feature has200 float32 values (800 bytes). The24.37MiB payload bound leaves
8,002,432 bytes below the32MiB logical feature-value limit. This calculation
covers one complete declared selector with no replay, resume or additional
prediction calls. Dictionary keys, metadata, live model copies, input arrays and
runtime memory lie outside it. It proves neither observed absence of evictions
in a full selector nor a6/7.5GiB process/Job memory result or480-second completion.

## Executed and pending evidence

The actual PowerShell source-only resume preflight passed with33 runtime-file
pins checked and no model launch. Root's27-check Source self-review verified
candidate/worker hashes, AST parsing,40-check accounting, preserved tested cache,
capacity arithmetic and fresh attempt directories. These are self-reviews of
Source preparation; the new prototype remains numerically unvalidated.

The prepared combined51-source reviewer distinguishes historical Git for the
five accepted groups from the fresh resume Git and requires actual receipts for
all six remaining groups. It excludes interrupted `source_query_g06_a001` and
retains its separate absence/recovery evidence. The combined review has not run.

Latest sampled RAM was about8.49GiB, below the retained10GiB startup floor.
No new model operation ran. Genuine pro2/phase pause files were absent; Source021
is peer scheduling only. Numerical checks use fresh attempts,90/120-second
guard/native ceilings, CPU/Torch1 and unchanged10/4GiB RAM,20GiB disk and6/7.5GiB
process/Job limits. Run the real check only after the40-check fixture passes and
physically releases. Remaining26 subjects retain180/210 ceilings.

Both original real LaBraM attempts remain spent. No automatic replay, production
integration, deadline guarantee or scientific sign-off follows from this work.
Scientific Gate A/freeze and checkpoint pretraining-cohort provenance remain open.

- [Executed Source preflight](../../../runs/coordination/cache_performance_20261008_v1/source_query_resume_preflight_execution_20261010_001.json)
- [Prospective worker preparation](../../../runs/coordination/cache_performance_20261008_v1/inference_workers_preparation_20261010_001.json)
- [Executed capacity arithmetic](../../../runs/coordination/cache_performance_20261008_v1/selector_feature_capacity_bound_20261010_001.json)
- [27-check Source self-review](../../../runs/coordination/cache_performance_20261008_v1/inference_preparation_root_source_review_20261010_001.json)
- [Prospective combined reviewer](../../../runs/coordination/cache_performance_20261008_v1/Review-SourceQueryCombined20261010.ps1)
