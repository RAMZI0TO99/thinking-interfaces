# Cho first-tranche analysis identity binding

28 September 2026. The [pure verifier](../../evaluation/phase2_cho_analysis_identity.py)
checks static identities for the proposed Cho2017 four-method, five-shot
first tranche. It reads no score, recorder file, EEG signal, selector record,
checkpoint or runtime environment, and makes no scientific claim. Its
[focused tests](../../tests/test_phase2_cho_analysis_identity.py) passed
6 tests and 7 subtests.

The verifier requires the exact Cartesian **52 subjects x four selected
methods x seeds 11/23/37/53/71 = 1,040 cases**, with one matching
`PinnedCaseCell` per `CasePlan`. From the typed `ChoFirstTrancheRoute`, it
reconstructs the protocol, source-selection and nested episode hashes and
checks the target catalog preprocessing hash. It requires an externally
reviewed digest map for all four method configurations, fixed-earliest null
draw and montage seeds, and uniform source provenance across the roster.
An independently supplied `SourceProvenance` can bind that common source;
without it, uniformity alone does not establish authenticity. Missing,
duplicate, extra, swapped and altered identities are rejected.

The [exact-source quality archive](../../runs/phase2/quality_history/20260928_cho_analysis_identity_5dce82b1.json)
pins source `5dce82b17ee36d791d78659900ba87cd1f3d4c425e1fc237bf0fd6cbb8198d20`.
Ruff, strict mypy and the full suite passed: **802 tests, 1 skip, 1,016
subtests**. The [fresh candidate-route receipt](../../runs/phase2/freeze_readiness/20260928_5dce82b1_candidate_routes/run_receipt.json)
matches all 1,040 proposed routes without fitting. The
[current-source control inventory](../../runs/phase2/control_refresh_checks/20260928_identity_binding_5dce82b1/inventory_receipt.json)
finds 0 valid / 45 missing, no invalid or unexpected record.

An [actual-route synthetic rehearsal](../../runs/phase2/analysis_identity_checks/20260928_5dce82b1_full_roster_synthetic/receipt.json)
rebuilt the current-source typed route from reviewed Cho input pins, required
exact equality with the planning crosswalk, and passed 1,040 synthetic
cell identities through the verifier. Swapped episode, swapped selection and
mixed-source pins were rejected. Its cell, success, selection-evidence,
checkpoint and environment digests were fabricated for engineering only.
It read no real cell score and performed no fit, recorder publication,
inference or report.

A separate [read-only no-future check](no_future_identity_source_check_20260928.md)
completed on the same source and quality. Its [receipt](../../runs/phase2/gate_a_diagnostics/20260928_no_future_identity_binding_5dce82b1/receipt.json)
records 0 valid / 36 missing matched-control records, no invalid or
unexpected record, and no training. The writer checked the nine subject
inputs; final record-bound raw verification remains false while records
are missing. It made no Gate A decision.

This verifier does not rehash method configuration bytes, prove which
per-subject Profile B artifact was used by a cell, authenticate persisted
complete selection evidence or checkpoint/environment provenance, or verify
recorder publication. The [recorder bridge](../../evaluation/phase2_cell_aggregation_bridge.py)
handles a separate part of publication verification. The proposed method
map remains unratified, complete selection needs 5,253 steps above the
unchanged 256-step engineering cap, and the 45 current-source controls are
missing. The full scientific freeze and Gate A remain unsigned; no real Cho
scientific cell or analysis report is admitted.
