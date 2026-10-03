# Current-source Cho read-only route audit

28 September 2026. This review records an actual read-only rebuild of the
proposed four-method, five-shot Cho2017 first-tranche routes on source
`147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`.
The [write-once route receipt](../../runs/phase2/freeze_readiness/20260928_147c0d11_readonly_route/receipt.json)
and [audit script](../../runs/phase2/freeze_readiness/20260928_147c0d11_readonly_route/verify_readonly_route.py)
pin the exact check.

The audit compared the source fingerprint before and after the run and
checked the independently pinned base config against the pilot
specification. It rebuilt 52 actual Profile A trial catalogs, loaded and
rehashed the 52 pinned 60 Hz Profile B artifact/manifest pairs, then ran
the [persisted target declaration check](cho_persisted_target_declarations_review_20260928.md)
over the base config, 60 Hz variant and all 52 B manifests. It produced
1,040 distinct proposed routes: 260 each for EEGNet, LaBraM linear,
LaBraM LoRA and LaBraM full tuning. Each EEGNet route has no B asset map;
each LaBraM route has the complete 52-subject B asset map. The receipt
records 52 target raw-source path and digest declarations. The route audit
completed in 11.203 seconds with stable source.

This route check read real prepared input assets and declarations. It did
not read or publish a real scientific cell or score, hash raw source bytes
on this pass, run a selector or target fit, replay inference, or admit a
scientific result. The earlier cohort audit's raw-source finding is an
input pin; the new persisted declaration reader compares declarations
with manifests and does not rehash raw files. Complete selection evidence,
checkpoint and environment provenance,
source-bound controls, the no-future matched records, the 5,253-step
selection versus unchanged 256-step cap, scientific freeze and Gate A
remain open. The production 20 GiB fit floor is unchanged.

The preceding [303-link documentation receipt](../../runs/phase2/analysis_pairing_checks/20260928_persisted_target_documentation/receipt.json)
pins the documents as they existed before this route-audit update. Its
source and focused-check evidence remain historical evidence for that
exact source, while its document hashes do not cover the updated start
page, status page, handoff or this review. A separate documentation
receipt pins these newer document bytes.

## Subsequent exact-source quality

The same source later passed [full exact-source quality](../../runs/phase2/quality_history/20260928_cho_persisted_target_147c0d11.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_persisted_target_147c0d11_guarded/receipt.json):
Ruff, full strict mypy, 830 passed tests, 2 skips and 1,033 passed
subtests. The minimum free disk was 9.572 GiB. This did not add a fit,
scientific cell, score or admission. The subsequent
[current-source control inventory](../../runs/phase2/control_refresh_checks/20260928_persisted_target_147c0d11/inventory_receipt.json)
found 0 valid / 45 missing with no invalid or unexpected records and
started no fit. The [no-future check-only preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_persisted_target_147c0d11/preflight_receipt.json)
deferred before raw recomputation at 10.494 GiB free against a 20 GiB
requirement; current-source 36-record status is unverified. The
route-audit documentation receipt above pins pre-quality status and
earlier document bytes.
