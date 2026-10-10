# Inference-query cache integration preparation

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
