# Inference-cache adoption plan, 10 October 2026

The tested inference adapter is now a tracked, byte-exact recipe alongside its
three dependencies. The [candidate manifest](INTEGRATION_REVIEW.json) pins all
four modules and the four actual execution self-reviews. Root's23-check source
preparation review checked the copied bytes, classes/imports and unchanged431-file
canonical Source without importing the prototypes or launching a model. This
packages an executed diagnostic candidate for review; production adoption and
the resulting source's quality validation have not occurred.

Pro2's genuine reply states that it owns no edits to Pro3 frozen implementation,
requests no conflicting resource window and requests no pause. It acknowledges
communication only. Root owns this new recipe/manifest/plan and project docs.
This preparation declares no frozen implementation edit targets or runtime
admission, and grants no scientific or case authority.

## Exact candidate

| Tracked module | Executed SHA-256 |
| --- | --- |
| [SourceSelectionCacheScope](source_selection_cache_scope_inference.py) |`5fed1301b216efcebf0218a928046f9fad3b97d4ef59980a1a6ec8280b152e5b` |
| [FrozenFeatureCache](frozen_feature_cache_inference.py) |`d5eff3a68996a6f6918fee0ace83572767f1ef3df1b85712989331443ce4c8c1` |
| [DiskBackedChoSnapshot](disk_backed_snapshot.py) |`521772373625feaa11c5b0e36cf4353e83dd9ccd88f8ff401d85a44a557a384c` |
| [Owned cleanup](owned_cache_cleanup.py) |`66d44ab072280c48327674ecfa5c2ac709253cc7da4a90ba809c9665bbea29f7` |

The manifest's execution reviews remain local ignored receipts. An independent
checkout can inspect the tracked candidate, but cannot infer execution evidence
or entry permission from source copies alone. See the [completed diagnostics](cache_diagnostics_20261010.md)
for15 adapter checks, all51 no-fit query results, original iterator sampling,
221 real source-batch comparisons and the limitations of their timings.
The recipe's local attributes retain LF bytes for Python copies and the manifest
across Windows checkouts, preserving their exact pinned content.

## Concrete integration interfaces

Preserve the current adapter construction contract:

```python
scope = SourceSelectionCacheScope(
    selector,
    owner_directory=attempt_directory,
    worker_sha256=actual_worker_sha256,
    event_sink=operational_progress_sink,
)
selected = scope.run_selection()
```

This is a proposed call contract, not a launch command. On real data,
`run_selection()` performs fitting and requires a separately admitted operation.
The interface accepts only the pinned CPU Cho B selector with no resident input
episodes or pre-existing initial-model forward wrapper. It is one-use, retains
the original fit/fold/evidence routines and returns the original selected-model
forward after scope cleanup. Progress remains outside scientific evidence.

Choose the import/ownership boundary before migration:

| Boundary | Required implementation decision | Required evidence |
| --- | --- | --- |
| Feature cache | Preserve inference caller mode, ordinary retained tensors and live head execution; only eligible frozen backbones reuse values | Existing transition/loss/gradient/update fixtures plus fresh checks if bytes change |
| Episode file tier | Preserve original loader, catalog/asset/config/source checks and512MiB logical LRU /2GiB private disk bound | Existing exact linear/full/LoRA fixtures; fresh scope/release checks after migration |
| Selector lifetime | Wrap only the owned instance, use32MiB feature bound, restore input limits/methods and remove returned forward wrapper | Exact synthetic selector evidence/state/RNG and exception-path cleanup |
| Guard integration | Bind actual worker/operation/runtime bytes and physical owned Job closure; clear only registered private files | Guarded current-source success, deadline/stop and release receipts |
| Production entry | Explicit opt-in at a newly owned call site; preserve candidates, roster, SGD, step counts, normalization and target boundary | Fresh source pin and guarded quality validation; separate case admission for real fitting |

There is a concrete relocation constraint: `owned_cache_cleanup.py` derives
`PHASE` from its own file directory. Its output paths must be one or two safe
components beneath that directory. Importing the recipe copy therefore changes
the permitted ownership root from the original operational phase to the recipe
directory. The recipe must not be imported as a shortcut to run existing attempt
paths or patched to allow arbitrary paths. Either provision the exact modules
in a newly reviewed owned operational phase, or explicitly redesign/review the
ownership-root interface and validate its confinement and cleanup behavior.
The top-level sibling imports must likewise be resolved explicitly; a filesystem
copy does not establish a production package interface.

## Implementation and validation order

1. Record exact new/frozen file ownership and the chosen import/cleanup-root
   interface. Preserve this tested candidate and old receipts unchanged.
2. Implement a separate reviewed candidate at those paths, with the original
   scientific route and default entry preserved. Do not silently broaden cache
   eligibility, paths or resource authority.
3. Settle Git and fresh canonical/runtime/operation pins. If bytes or import/root
   semantics change, rerun the meaningful synthetic equivalence/lifecycle checks
   through a fresh finite guarded attempt and obtain physical release evidence.
4. Run the existing guarded quality checks for the resulting canonical source.
   An old quality pass cannot certify a new implementation.
5. Review a separate recorder recovery/admission plan before any future real
   case. The original two attempts remain spent; this recipe admits neither an
   automatic third attempt nor a cap increase.

Full-selector runtime, accuracy, checkpoint pretraining-cohort/target-overlap
provenance, Scientific Gate A and the experiment freeze remain unresolved. The
engineering candidate supplies no signature. No model Job or entry watcher is
active in this Source preparation step; Source021 remains peer scheduling only
through20:40UTC10October and must be refreshed on a later resume.

- [Root23-check source preparation review](../../../runs/coordination/cache_performance_20261008_v1/inference_recipe_preparation_root_source_review_20261010_001.json)
- [Recorded recipe ownership scope](../../../runs/coordination/cache_performance_20261008_v1/inference_recipe_source_ownership_20261010_001.json)
