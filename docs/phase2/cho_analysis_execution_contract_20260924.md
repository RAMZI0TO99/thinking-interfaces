# Proposed Cho first-tranche analysis execution contract

24 September 2026. This is a review draft for the owner's four-method,
five-shot Cho2017 60 Hz first tranche. It is not an adopted analysis
configuration or a result report. No scientific Cho cell is admitted.

## Input admission

An eventual analysis command must read only completed, independently verified
evaluation cells for the ratified 60 Hz cohort and executable configuration.
The proposed complete roster is 52 subjects x 4 methods x 5 model seeds
`11/23/37/53/71` = 1,040 cells. The four methods are `labram_linear`,
`labram_lora`, `labram_full`, and `eegnet`; EA remains outside this tranche.
The command must reject missing, duplicate, conflicting, stale-source,
wrong-cohort, wrong-shot, wrong-seed, wrong-selection, or unreceipted cells.
It must verify the published cell digest, method settings, episode/selection
pins, exact query/confusion inputs and current scientific admission record
before computing any inferential statistic. A partial exploratory table may
be labeled as partial, but it cannot be promoted to this complete-tranche
analysis after results are seen.

## Proposed calculation order

For each subject and method, compute the mean balanced accuracy over the five
fixed seeds without rounding stored exact-rational cell metrics. Form one
paired subject difference: LoRA mean minus linear-probe mean. Subjects, not
seeds or cells, are the 52 inferential units. Publish the per-subject paired
inputs and a digest of the admitted 1,040-cell roster with the aggregate.
The declared primary metric is balanced accuracy, with a 95% interval.

`evaluation/phase2_subject_aggregation.py` now implements only the exact
arithmetic in this step. It requires an explicit complete cell roster and one
externally verified digest and rational score per cell, rejects missing,
duplicate or extra identities, and keeps shot counts separate while averaging
seeds. It returns sorted exact-rational subject-method means and the admitted
digest roster. It reads no cell files and performs no inference or report
publication. A future collector must first verify the published cell and case
receipts and every source, cohort, episode, selection and configuration pin;
the arithmetic function alone does not admit scientific inputs.
Its [write-once engineering receipt](../../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/receipt.json)
pins source `f2d4acdd`, the module and tests, and the verified full quality
bundle (771 passed, 1 skipped, 1,002 subtests). It records zero training and
zero scientific cells.
A [synthetic full-roster rehearsal](../../runs/phase2/analysis_aggregation_checks/20260924_f2d4acdd/full_roster_synthetic_receipt.json)
then passed the unchanged 1,040-case planning crosswalk through the core:
208 subject-method-shot groups, each with five dummy seed rows. It read zero
real cell scores and published no result or inference. The roster and dummy
digests are engineering inputs only.

`evaluation/phase2_cell_aggregation_bridge.py` now supplies a read-only
recorder-to-aggregation path for a caller-provided complete roster. It requires
externally retained cell-envelope, success-file and selection-evidence digests
for each case. It checks exact recorder directories,
bounded canonical cell/claim/failure/intent/success bytes, one initial attempt
or one linked retry, the declared case and cell identity, and the exact
confusion-derived score before producing `ScoreRow` values. Synthetic tests
cover separate shot groups, missing and extra cases, orphan publication,
external-pin mismatch, linked retry, oversize refusal and a self-consistent
record with an incorrect score. Further tests reject Boolean attempt fields,
claim provenance that differs from the pinned successful cell, malformed
recorded source fields, and an unexpected directory entry before scanning the
rest of a writable directory. The bridge reads no real Cho cells and starts
no fit. Its caller still must verify the scientific source, cohort, episode,
selection evidence and configuration pins, then provide the frozen full roster;
the bridge cannot itself admit a scientific result or inferential report.

The configured primary test name is `paired_wilcoxon_pratt`, but
`configs/phase2/analysis.toml` does not yet specify the test direction,
superiority threshold or interval construction. The generic Phase I
`evaluation/statistics.py` helper does not consume this Phase II config.
Those choices and an executable Phase II analysis command must be fixed
before any first-tranche outcomes are interpreted. The
[freeze decision packet](freeze_decision_packet_20260923.md) presents the
owner decision boundary. The [28 September technical proposal](cho_four_method_freeze_technical_proposal_20260928.md)
provides a concrete one-sided Pratt rule, exact tie-class handling,
all-zero policy and separate paired-mean interval for owner review. It is
not an adopted rule. A later [pure calculation module](cho_pure_inference_review_20260928.md)
implements those numerical operations over caller-supplied exact subject
differences and passes synthetic/full-source checks. It cannot admit the
1,040 real cells, interpret a scientific claim or publish a report. The
Phase II analysis command and ratified executable config remain absent.

A later [pure Cho identity binder](cho_analysis_identity_binding_review_20260928.md)
checks the complete proposed route against caller-supplied cell identities
before any score read. Its full-roster actual-route rehearsal uses synthetic
pins and admits no scientific cell. The caller still needs independently
reviewed method settings and source, persisted complete selection evidence,
verified Profile B asset use and checkpoint/environment pins, plus the
ratified analysis configuration and recorder publication. This binder is
not the complete analysis command.

A later [pure paired-input builder](cho_paired_inputs_review_20260928.md)
now accepts externally verified `ScoreRow` values for the exact frozen Cho
1,040-case roster and forms 208 five-seed means plus 52 exact
LoRA-minus-linear subject differences. It closes the previous manual
conversion step between aggregation and the pure inference calculator.
It does not authenticate the rows or admit scientific cells. Its focused
checks passed on source `a7841e14`; full exact-source quality and fresh
source-bound evidence remain pending.

The later test-only resource fixture and post-child channel guard
regression produce source `ef8b3f82`. The
[focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_ef8b3f82_focused/receipt.json)
passes the changed tests, Ruff and mypy; it is not a full quality bundle.
The unchanged 20 GiB disk floor still blocks the control fits.

The [read-only recorder preparation review](cho_analysis_preparation_review_20260928.md)
then composes those static identity checks, the pinned recorder bridge and
the exact paired-input builder. It requires the independently supplied
source before any recorder read. Its source `c535f457` has a focused
[receipt](../../runs/phase2/analysis_pairing_checks/20260928_c535f457_focused/receipt.json)
with 11 passed tests and 9 passed subtests, Ruff and mypy. The Cho loader
now hashes the exact A/B artifact and B manifest buffers it parses. The
actual target B binding still needs to be carried into each published cell
and checked against an external pin; the current read-only path cannot
establish observed target-use provenance. Full quality and current-source
controls remain pending.

The subsequent [target-input attestation review](cho_target_input_attestation_review_20260928.md)
records the prospective publication change: the Cho case executor carries
the observed LaBraM 60 Hz binding, or the EEGNet Profile A anchor identity,
through the selected case into its success cell. It checks the target
subject, episode, trial IDs, asset digests and Profile A retention before
publication. A read-only verifier checks each attestation in externally
pinned cell bytes against the planned route before the recorder preparation
bridge yields paired scores. A missing attestation is rejected; older cells
are not retroactively verified. The Cho Profile A EEGNet loader also hashes
the exact artifact buffer it parses.

The `c535f457` [guarded full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_preparation_c535f457_guarded/receipt.json)
stopped at its quality-only 8 GiB active disk floor after Ruff and mypy
passed; it has no passing quality archive. Source `98f6f523` has a
[write-once focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_target_attestation_focused/receipt.json)
with stable source, Ruff and strict mypy passing and 9 tests / 15
subtests passing. Full current-source quality remains pending. Target
attestation checks recorded claims under a pinned executor source; they
do not replay inference or alone admit a scientific result. The read-only
verifier syntax-checks B profile-config, base-config and B manifest source
digests but does not independently compare them with persisted bytes.
Those comparisons remain necessary before scientific admission. Earlier
read-only inventories found 0/45 source-bound controls and 0/36 no-future
matched records; current-source inventories remain pending.

The [persisted target declaration review](cho_persisted_target_declarations_review_20260928.md)
records source `147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`.
The preparation path now requires `project_root` and an independently
pinned `base_config_sha256`. After the independent-source identity check,
it verifies exact bounded bytes for the base config, route-pinned 60 Hz
variant and all 52 B manifests. It requires the supported A/B base
definitions, named 60 Hz B variant, matching manifest config digests and
per-subject raw source declarations. It compares those declarations with
each externally pinned LaBraM B binding and the independent base pin with
each EEGNet Profile A anchor before score extraction. Thus the preceding
source's unbound config and manifest-source declarations are now checked
against persisted declarations. The [focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_persisted_target_focused/receipt.json)
pins stable source, Ruff, strict mypy, 13 passed, 1 skipped and 15 passed
subtests. The same source later [passed full exact-source quality](../../runs/phase2/quality_history/20260928_cho_persisted_target_147c0d11.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_persisted_target_147c0d11_guarded/receipt.json):
Ruff, full strict mypy, 830 passed tests, 2 skips and 1,033 passed
subtests, with 9.572 GiB minimum free disk and stable source. This
new check still does not hash the A/B artifact or raw source files, replay
inference, prove complete selection, authenticate checkpoints/environment,
or admit a scientific cell. The freeze, Gate A, controls, 5,253-step
selector-cap decision and 20 GiB production fit floor remain open.
The [current-source control inventory](../../runs/phase2/control_refresh_checks/20260928_persisted_target_147c0d11/inventory_receipt.json)
found 0 valid / 45 missing, with no invalid or unexpected records; no fit
started. The [no-future check-only preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_persisted_target_147c0d11/preflight_receipt.json)
deferred before raw recomputation because the writer requires 20 GiB
disk and 10.494 GiB was free. The current-source 36-record inventory is
unverified; earlier 0/36 findings remain historical. The preceding documentation receipts pin their
pre-quality status and earlier document bytes.

The subsequent [query, route and raw review](cho_query_route_raw_review_20260928.md)
records source `48e668e3bc8ed9b8b277454de460d359e686c3519ea5173d2107d771cdb58dcf`.
The read-only preparation path requires independent typed
`ChoCaseInputPins`, exactly rederives the 1,040-case route, and compares
each pinned cell's query count and two true-class confusion-row totals
with the planned target query labels before reading score rows. A
synthetic 32-query adversarial repin is rejected even when recorder
metric arithmetic and publication hashes are self-consistent. Its
[raw-source audit](../../runs/phase2/freeze_readiness/20260928_cho_raw_source_readonly/receipt.json)
directly hashed 52 declared Cho files totaling 10,704,036,837 bytes
while rebuilding 1,040 routes, 52 A catalogs and 52 B assets. The
[method-template revalidation](../../runs/phase2/freeze_readiness/20260928_48e668e3_method_template_readonly/receipt.json)
remains proposed and unratified. This source later passed
[full quality](../../runs/phase2/quality_history/20260928_cho_query_route_48e668e3.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_query_route_48e668e3_guarded/receipt.json):
Ruff, full strict mypy, 832 tests and 1,033 subtests passed, with 2
skips; minimum disk/RAM were 10.809/15.077 GiB. The
[source `48e668e3` control inventory](../../runs/phase2/control_refresh_checks/20260928_query_route_48e668e3/inventory_receipt.json)
found 0 valid / 45 missing. The [no-future preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_query_route_48e668e3/preflight_receipt.json)
deferred before raw recomputation at 11.525 GiB free against 20 GiB
required, so the source's 36-record inventory is unverified.
The source `147c0d11` receipts above remain historical for that source.
No fit, cell, score, report or scientific admission occurred.

The subsequent [selection-file binding review](cho_selection_file_binding_review_20260928.md)
records source `a80b571d64460dbe18285bb367520195810bccf66fc0b7d1034bad85d2fd7344`.
Before score extraction, the read-only composer now binds each externally
pinned cell to bounded persisted selection bytes and checks case claims,
candidate settings, selected winner, method digest and final-fit digest
claims against the independently rederived route. It retains a physical
file witness and checks it again after paired-input construction. The
cell's completion flag and final-fit digest are recorded claims; this
does not prove complete selector folds, actual fit work, checkpoint bytes
or scientific admission. Its [current method-template receipt](../../runs/phase2/freeze_readiness/20260928_a80b571d_method_template_readonly/receipt.json)
checked 40 candidates and four matching digests but remains unratified.
The [raw audit](../../runs/phase2/freeze_readiness/20260928_a80b571d_raw_source_readonly/receipt.json)
verified 1,040 routes and 52 declared raw files totaling 10,704,036,837
bytes. [Full exact-source quality](../../runs/phase2/quality_history/20260928_cho_selection_binding_a80b571d.json)
passed Ruff, strict mypy, 847 tests and 1,033 subtests, with 2 skips.
The [45-control inventory](../../runs/phase2/control_refresh_checks/20260928_selection_binding_a80b571d/inventory_receipt.json)
found 0 valid / 45 missing. The [no-future preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_selection_binding_a80b571d/preflight_receipt.json)
deferred before raw recomputation at 11.37 GiB free versus the unchanged
20 GiB requirement; the current-source 36-record inventory is unverified.

For owner review, the proposed secondary superiority family is empty.
Full tuning remains a regularization reference and EEGNet an architecture
anchor; report their matched descriptive summaries and uncertainty without
superiority p-values, winner or mechanism claims. A later superiority family
would need prospective definition and the declared within-family Holm rule.
The configured LoRA-linear TOST margin is
`0.05202907926797159`, alpha `0.05` with a 90% interval. Its formal-versus-
exploratory reporting status remains an owner decision; the decision packet
proposes exploratory reporting without an equivalence claim for this tranche.

## Publication boundary

The report must pin its input roster, frozen analysis configuration,
implementation source and environment, exact per-subject values, test
parameters, and output bytes in a write-once receipt. A later code or
configuration change produces a new report identity, never an overwrite.
Gate A is unsigned, the scientific freeze and complete-work resource
admission are pending, the 5,253-step selector exceeds the unchanged
256-step engineering cap, and no Phase II analysis runner is wired yet.
Therefore this contract authorizes no fit, cell, p-value or scientific claim.
