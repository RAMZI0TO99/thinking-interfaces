# Cho query metrics, route origin and raw-source review

28 September 2026. This engineering review is specific to source
`48e668e3bc8ed9b8b277454de460d359e686c3519ea5173d2107d771cdb58dcf`.
It covers the proposed four-method, five-shot, 60 Hz Cho2017 first tranche.
It is a read-only preparation check, not a scientific freeze or a result.

## Recorded query metrics

The [recorded target-input verifier](../../evaluation/phase2_cho_target_input_bridge.py)
now checks each externally pinned cell's `query_count` against the number
of query indices in its freshly derived target episode. It also requires a
two-by-two confusion matrix of nonnegative integers whose two true-class
row totals equal the class counts in the target [trial catalog](../../evaluation/phase2_protocol.py)
at those query indices. It runs this check before the recorder's score rows
are extracted by the [paired-input preparation path](../../evaluation/phase2_cho_analysis_preparation.py).
This binds the recorded score inputs to the planned query count and label
distribution. It does not independently replay predictions or verify a
prediction for each individual query trial.

The [synthetic adversarial test](../../tests/test_phase2_cho_analysis_preparation.py)
uses a complete 1,040-cell recorder fixture with 32 queries in the changed
case. It republishes one cell with a self-consistent 31-query confusion
matrix, then with a 32-query matrix whose true-class totals differ from
the planned labels. In both cases it recalculates the score, cell
envelope, publication intent and success record and supplies a matching
external cell pin. The recorder's metric arithmetic accepts those
self-consistent values; the new route-bound check rejects each before
score extraction. The number 32 describes this synthetic case, not a
fixed query count for all real Cho subjects.

## Independent route origin

The paired-input preparation call now requires independently supplied,
typed [ChoCaseInputPins](../../evaluation/phase2_cho_case_inputs.py) for
the protocol, threshold, cohort audit and 60 Hz variant. It rebuilds
the proposed 1,040-case route from those pinned files and assets and
requires exact equality with the supplied route before it checks case
identities or reads cell and score records. A synthetic regression rejects
an absent pin object and a changed supplied route, even when the changed
protocol text would parse to the same values. Source, method settings,
base config, persisted target declarations and recorder publication have
their separate checks in the same preparation path. This route equality
does not establish complete source-selection evidence, checkpoint or
environment provenance.

## Current-source raw bytes

The [write-once read-only receipt](../../runs/phase2/freeze_readiness/20260928_cho_raw_source_readonly/receipt.json)
and [audit script](../../runs/phase2/freeze_readiness/20260928_cho_raw_source_readonly/verify_raw_sources.py)
record a stable source fingerprint across an actual route rebuild and raw
file scan. The audit rebuilt 1,040 routes, 260 per method, with 52 Profile A
catalogs and 52 pinned 60 Hz Profile B asset pairs. It checked the
independent base-config pin and persisted B manifest source declarations,
then streamed and hashed all 52 distinct declared raw Cho `.mat` files:
**10,704,036,837 bytes** in total. Each direct digest matched its manifest
declaration. The file reader bounded size, rejected path aliases and
multiple hard links, and checked file identity and metadata around each
read. The audit took 18.594 seconds; minimum free disk was 10.780 GiB.

This verifies those raw file bytes against the current declarations. It
does not decode the raw EEG again, rerun preprocessing or inference, or
prove that an eventual fit will use those files. The audit started no
training and admitted no scientific cell or score.

## Status and admission boundary

The source later passed [full exact-source quality](../../runs/phase2/quality_history/20260928_cho_query_route_48e668e3.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_query_route_48e668e3_guarded/receipt.json):
Ruff and full strict mypy passed; pytest had 832 passed, 2 skipped and
1,033 passed subtests. The source stayed stable; minimum free disk was
10.809 GiB and minimum available RAM was 15.077 GiB. The separate
[method-template revalidation](../../runs/phase2/freeze_readiness/20260928_48e668e3_method_template_readonly/receipt.json)
checked 40 typed candidates and four method config digests. It remains
proposed and unratified; its earlier `quality_pass_claimed: false` field
records the scope at the time of that read-only check.

The [source `48e668e3` control inventory](../../runs/phase2/control_refresh_checks/20260928_query_route_48e668e3/inventory_receipt.json)
found 0 valid / 45 missing source-bound records with no invalid or
unexpected record and started no fit. The
[no-future check-only preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_query_route_48e668e3/preflight_receipt.json)
deferred before raw recomputation at 11.525 GiB free against its 20 GiB
disk requirement. Thus the 36-record inventory is unverified for this
source. The source `147c0d11`
[quality and inventory snapshot](../../runs/phase2/freeze_readiness/20260928_147c0d11_full_quality_handoff/documentation_receipt.json)
is historical for its own source. Complete selection evidence, chosen
checkpoint and environment provenance, the 5,253-step selector versus
256-step cap, scientific analysis configuration and full freeze remain
open. Gate A is unsigned and the production 20 GiB fit floor is
unchanged. No real Cho fit, cell, inferential score, report or scientific
claim follows from this review.
