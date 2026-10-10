# Namespaced cache candidate validation, 10 October 2026

The integration plan's import boundary is now implemented in a separate
operational package and tested. The adapter's three sibling imports are relative;
its remaining AST is identical to the earlier executed adapter. Feature cache,
disk snapshot and cleanup helper bytes remain exactly unchanged. Cleanup stays
confined to the helper's package directory; no arbitrary-root parameter or path
fallback was introduced. Frozen production files and canonical Source remain
unchanged.

The [tracked namespaced candidate](pro3_inference_candidate/__init__.py) contains
exact executed source copies. Its [new manifest](NAMESPACED_INTEGRATION_REVIEW.json)
is separate from the earlier flat-import candidate/manifest, which remain
preserved. Callers use the explicit package import:

```python
from pro3_inference_candidate.source_selection_cache_scope_inference import (
    SourceSelectionCacheScope,
)
```

This records the import interface; it launches no model and supplies no runtime
admission. Importing only the package initializer performs no model work. The
fixture intentionally populated unrelated top-level dependency names with empty
modules before importing the candidate. The relative imports still resolved the
owned package dependencies. The cleanup helper's `PHASE` remains its own module
parent, so output directories must stay within the reviewed package root.

## Actual evidence

Root's preparation review passed54 Source checks: baseline/changed bytes, AST
equality apart from the three import levels,33 runtime pins and unchanged
canonical Source. The native PowerShell parser passed before any model entry.

Fresh `packaged_scope_fixture_002` passed all15 synthetic equivalence/lifetime/
cleanup checks, with zero errors/failures/skips. It preserves exact linear/full/
LoRA selector behavior, losses/history, evidence, state and RNG, plus exception/
borrowed-view and progress-error cleanup. The fixture performs tiny synthetic
training; it performs no real-data fit or real case. The root execution
self-review passed120 checks and accepted this diagnostic and physical release.

| Measurement | Actual value |
| --- | ---: |
| Execution Git |`52924c5443d8bbc1ba3de3255cdb874db02fdc5b` |
| Canonical Source |`b7452847` /431 files |
| Native / guard elapsed |19.199935s /19.024793s |
| Guard / native limits |90s /120s |
| Process / Job limits |2.25GiB /2.5GiB |
| Maximum measured Job commit |1,363,542,016 bytes |
| Startup / active RAM; free disk |7GiB /4GiB;20GiB |
| CPU/Torch threads |1 |

Original guards/case caps stayed byte-for-byte unchanged. Actual guard minimum
RAM/disk samples complied. The owned Job was empty and closed; fresh named-Job
absence, absent/exited recorded processes and query-handle closure were checked.
Selector private caches cleared. Cleanup refusal tests retain only their exact
documented synthetic sentinels. Both entry invocations exited; no watcher/model
Job remains at this checkpoint.

The first attempt ran all15 tests and exited1 with five cleanup fixture
file-creation errors at its long generated paths. It remains unaccepted and
byte-preserved. The fresh worker uses short hash-derived directory labels while
retaining every original test method/case; it also includes the initializer in
the complete prototype-pin receipt. No candidate module bytes, memory limits or
deadlines changed for the retry. A pre-entry RAM refusal created no second
attempt; its later finite entry invocation launched only the fresh002 attempt.

- [54-check Source preparation](../../../runs/coordination/inference_cache_adoption_20261010_v1/preparation_source_review_001.json)
- [Actual15-check fixture result](../../../runs/coordination/inference_cache_adoption_20261010_v1/pro3_inference_candidate/packaged_scope_fixture_002/result.json)
- [120-check execution self-review](../../../runs/coordination/inference_cache_adoption_20261010_v1/pro3_inference_candidate/execution_root_review_002.json)
- [Preserved first failure and fresh retry preparation](../../../runs/coordination/inference_cache_adoption_20261010_v1/first_fixture_failure_review_001.json)

## Adoption boundary

The chosen operational interface resolves sibling imports and preserves a fixed
confined cleanup root. Copies at another filesystem location remain source
recipes: their module-parent root differs and they supply no admission for old
attempt directories. The tested operational package lives under
`runs/coordination/inference_cache_adoption_20261010_v1/pro3_inference_candidate`.

Production call-site integration and fresh canonical-source quality validation
remain the next scope. The old quality suite was not rerun and does not certify
these operational files. Earlier all51 query/221 real-source batch diagnostics
retain their own dated execution source and receipts; they were not replayed for
this packaging change. Full real-data selector runtime, accuracy and480-second
completion remain unproved. Both original real attempts remain spent, and
Scientific Gate A/freeze/checkpoint cohort provenance remain unresolved.

Pro2 requested no pause or conflicting implementation ownership. Its replies
acknowledge communication only. Root owns the new operational package and
recipe/docs; frozen implementation edit targets are still unassigned. Source021
is peer scheduling only through20:40UTC10October. No new30h window, runtime lease,
whole-host release, independent acceptance or scientific signature is inferred.
