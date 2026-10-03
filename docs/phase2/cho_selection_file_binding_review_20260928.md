# Cho selection-file binding review

28 September 2026. This engineering review covers the four-method,
five-shot, 60 Hz Cho2017 first-tranche preparation path at source
`a80b571d64460dbe18285bb367520195810bccf66fc0b7d1034bad85d2fd7344`.
It does not report a real Cho selection or scientific result.
The [later working-tree review](cho_selected_source_publication_and_manifest_review_20260928.md)
adds static policy and final-fit winner checks, selected-source manifest
binding and a prospective publication hook. The quality archive below
applies only to this historical `a80b571d` source.

## Selection files before scores

The [paired-input composer](../../evaluation/phase2_cho_analysis_preparation.py)
now calls the [selection-file bridge](../../evaluation/phase2_cho_selection_file_bridge.py)
after independent route, identity, persisted-target and target-input checks,
but before it extracts recorder score rows. For each externally pinned cell,
the bridge rereads the canonical cell envelope and checks its selection
digest and recorded file path. The path must be a direct, canonical relative
path under `runs/phase2`; the persisted selection must match the external
selection digest and a valid engineering envelope. Canonical logical files
have a 128 MiB bound. Factored files use the bounded 64 MiB packed reader
and reconstruct the pinned logical envelope. Physical reads reject file
aliases, multiple hard links and changes during a read.

The bridge checks recorded case claims against the rederived route: purpose,
completion flag, absence of outer-target predictions, method, dataset,
source selection, protocol, shots, model seed, executor source and the final
source-fit digest named by the cell checkpoint. It requires the selected
candidate to appear exactly once in the contract roster. It derives the
static method template from that roster and compares its digest with both
the independently supplied four-method digest map and the cell identity.
The [current-source read-only method-template receipt](../../runs/phase2/freeze_readiness/20260928_a80b571d_method_template_readonly/receipt.json)
revalidated 40 typed candidate settings and four digests from the proposed
template; that template is still unratified. The bridge checks a caller's
independent digest pins; it does not read or ratify that receipt itself.

The [focused bridge tests](../../tests/test_phase2_cho_selection_file_bridge.py)
exercise canonical and factored evidence, missing or noncanonical paths,
hard links, size bounds, repinned wrong digests and case claims, altered
candidate settings, an undeclared winner, and file replacement. The
[1,040-cell synthetic composer test](../../tests/test_phase2_cho_analysis_preparation.py)
also rejects a missing selection file before score extraction. Its fixture
is an engineering example with claimed completion, not a completed selector.

## Post-aggregation file witness

The bridge retains the physical file digest and filesystem identity for each
cell and selection file. The composer rereads that witness after score
verification and paired-input construction, before returning the paired
values. A [synthetic mutation test](../../tests/test_phase2_cho_analysis_preparation.py)
deletes a selection file during paired-input construction and verifies that
the composer fails. This narrows the interval in which a checked file can
be replaced unnoticed; it does not replay inference or independently
authenticate a fitted model.

## Admission boundary

These checks bind persisted **files and claims** to the proposed route,
external pins and reviewed method digests. They do not verify every selector
fold, score or gradient, the actual final source fit, checkpoint bytes,
environment, or scientific freeze. The separate
[preclaim verifier](../../evaluation/phase2_cho_execution_gate.py) calls the
full selection-evidence verifier before target work, but the current public
engineering path hard-refuses ceilings above 256 steps. The
[workload review](cho_four_method_freeze_technical_proposal_20260928.md)
calculates 5,253 steps per complete two-candidate selection. That cap and
the scientific admission contract remain open.

Source `a80b571d` [passed full exact-source quality](../../runs/phase2/quality_history/20260928_cho_selection_binding_a80b571d.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_selection_binding_a80b571d_guarded/receipt.json):
Ruff and full strict mypy passed; pytest had **847 passed, 2 skipped and
1,033 passed subtests**. Source remained stable, with minimum free disk
11.182 GiB and available RAM 13.945 GiB. The [read-only raw audit](../../runs/phase2/freeze_readiness/20260928_a80b571d_raw_source_readonly/receipt.json)
verified 1,040 routes, 52 Profile A catalogs, 52 Profile B assets and
52 declared raw files totaling 10,704,036,837 bytes. The
[control inventory](../../runs/phase2/control_refresh_checks/20260928_selection_binding_a80b571d/inventory_receipt.json)
found 0 valid / 45 missing source-bound controls with no invalid or
unexpected record. The [no-future preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_selection_binding_a80b571d/preflight_receipt.json)
deferred before raw recomputation at 11.37 GiB free against its
unchanged 20 GiB disk requirement. Thus the current-source 36-record
inventory is unverified. No real Cho fit, scientific cell, score, report
or admission follows from this review. The scientific freeze and Gate A
are unsigned.
