# Pure Cho paired inference calculation — engineering review

28 September 2026. This is a numerical preparation for the
[unratified four-method freeze proposal](cho_four_method_freeze_technical_proposal_20260928.md).
It does not adopt the proposed hypothesis, admit a cell, publish a p-value
from real data, or sign Gate A. The exact-source [engineering receipt](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c/receipt.json)
binds the code, tests, full quality, route rehearsal and control inventory.

## Calculation boundary

The new [pure inference module](../../evaluation/phase2_inference.py) accepts
an explicit roster of all 52 canonical Cho subject IDs and 52 exact
`Fraction` paired differences. The eventual caller must first verify all
1,040 cell records, the source/cohort/configuration/selection pins and the
five-seed subject aggregation. This module has no file reader, model, case
admission, report writer, superiority Boolean or equivalence Boolean.

It calculates the exact paired mean and sample variance, counts zero
differences and nonzero absolute-magnitude tie classes, and maps distinct
exact magnitudes to signed integer levels before SciPy's one-sided Pratt
asymptotic Wilcoxon call. The rank encoding preserves rational ties without
floating-point subtraction. All-zero differences produce statistic 0 and
`p = 1` by the proposed explicit convention. Separate two-sided 95% and
90% Student t intervals describe the paired arithmetic mean; exact zero
variance produces point intervals. Nonfinite or underflowed nonzero numeric
conversions fail closed. The function returns calculations only; the
proposed decision condition remains an owner choice.

The [synthetic tests](../../tests/test_phase2_inference.py) check a
common-denominator independent rank reference, Pratt zeros, all-zero and
constant-positive cases, the t formula, sign reversal, input-order
invariance, exact subject coverage, malformed inputs and float underflow.
Focused verification passed 13 tests, Ruff and strict mypy. The full
exact-source quality bundle passed lint, strict types, **796 tests, 1 skip
and 1,009 subtests** in 20:40 of test time. Its [archived receipt](../../runs/phase2/quality_history/20260928_pure_inference_9bf0516c.json)
verifies source
`9bf0516c11aec1e3cda0635e79fc58a7cc3db5d2df4d496a2039ab661ad597b9`.
The prior 24 September `458be569` source receipts are historical after this
new module and tests entered the source fingerprint.

## Current-source read-only follow-up

The [route rehearsal](../../runs/phase2/freeze_readiness/20260928_9bf0516c_candidate_routes/run_receipt.json)
matched the unchanged unratified candidate template to **1,040/1,040**
planned case routes without fitting. The [45-control inventory](../../runs/phase2/control_refresh_checks/20260928_pure_inference_9bf0516c/inventory_receipt.json)
found **0 valid / 45 missing**, no invalid or unexpected records, and no
refresh lock. Its 06:29 UTC read-only snapshot had 34.619 GiB disk free
and 6.369 GiB available RAM. The separate unchanged **10 GiB** control-fit
startup guard was not met; no refresh fit was attempted. The earlier
no-future 36-fit matched diagnostic is source-bound to the previous code
state and has not been rerun for this source.

The four-method analysis config still has `experiment_frozen = false` and
the secondary family pending. The proposed complete selection still needs
5,253 gradients per case against the unchanged 256-step engineering cap.
There is no complete-case resource envelope, scientific analysis command,
real-cell inferential report, current-source control refresh, Gate A
sign-off, commit or push. These boundaries are also recorded in the
[analysis execution contract](cho_analysis_execution_contract_20260924.md)
and [freeze review sheet](cho_four_method_freeze_review_sheet_20260924.md).

A later [full-roster synthetic rehearsal](cho_full_roster_inference_synthetic_review_20260928.md)
linked the 1,040-row aggregation output to this calculation for all 52
subjects under two generated score rules. It retained the same source
fingerprint and read no real cell score.
