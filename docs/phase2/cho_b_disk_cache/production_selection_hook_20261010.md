# Explicit LaBraM production selection hook, 10 October 2026

`ProductionChoCaseRunner` now accepts an optional
`labram_source_selection_runner` callable. Its default is `None`, so existing
callers retain the original selector execution. EEGNet always uses its original
selector. A supplied LaBraM callable receives the already constructed selector;
the returned evidence/model then flow through the existing selection verifier,
publication gate, target executor and recorder. Supplying the callable changes
selection dispatch only and admits no compute or scientific experiment.

This is the production integration point for the separately tested namespaced
cache wrapper. A reviewed operational worker can explicitly provide a callback
that invokes `SourceSelectionCacheScope(...).run_selection()` using its guarded
owned directory, actual worker hash and operational progress sink. The package's
fixed module-parent cleanup confinement and original source/target lifetimes
still apply. The default CLI does not activate the candidate automatically.

Root owns the change to `evaluation/phase2_cho_sweep.py` and the new test file.
Genuine pro2 coordination confirmed no competing file ownership or pause;
its reply accepts communication only. The original runner is preserved in Git
and its prior byte pin is recorded in the phase ownership receipt. Both spent
case artifacts, raw inputs, weights and original guard/case limits are preserved.

Six regression checks are prepared: default LaBraM dispatch, supplied callback
and continued evidence verification, EEGNet isolation, a callable whose boolean
value is false, exception propagation before publication/target work, and refusal
of noncallable values. These tests construct tiny synthetic model objects and
mock selection/publication boundaries; they fit no real data and claim no case.
At this preparation checkpoint these checks and fresh full quality have **not
executed**. Syntax/source review does not substitute for executed validation.

Canonical Source changed from the earlier `b7452847` /431 files to the new
432-file implementation/test source. The fresh operational validation plan must
bind its exact live source, clean Git,33 selected runtime files and new attempt
identity. The historical quality pointer remains unchanged and certifies only
its earlier source. Earlier15/51/221 diagnostic receipts keep their own dated
source and are not upgraded to validate this change.

Next: guarded focused regressions and lint/type checks on settled source, then
the existing guarded full-quality runner with current pins and physical release
evidence. Work with actual available resources, retain original10GiB full-quality
startup and active4GiB RAM/disk20GiB floors, CPU1 and at most one owned Job.
No obsolete watcher, old peer grant or spent case attempt may be reused.
Scientific Gate A/freeze and checkpoint cohort provenance remain unresolved.

- [Explicit file ownership](../../../runs/coordination/cho_selection_hook_20261010_v1/ownership_001.json)
- [Tested namespaced candidate](NAMESPACED_INTEGRATION_REVIEW.json)
- [Namespaced diagnostic validation](namespaced_candidate_validation_20261010.md)
