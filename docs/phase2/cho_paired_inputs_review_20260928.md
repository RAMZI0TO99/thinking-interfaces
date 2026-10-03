# Cho first-tranche paired-input preparation

28 September 2026. The [pure paired-input builder](../../evaluation/phase2_cho_paired_inputs.py)
connects externally verified rational `ScoreRow` values to the proposed Cho
subject-level comparison. Its [focused tests](../../tests/test_phase2_cho_paired_inputs.py)
passed **12 tests**; Ruff and strict mypy passed for the new module and tests.
This is an engineering check, not an analysis result.

The builder fixes the complete Cho2017 five-shot roster: **52 named subjects x
four methods x five seeds = 1,040 cells**. It checks the selected constants
against the frozen values, then requires exactly one row for every expected
case. Missing, extra, duplicate, wrong-identity and reused-digest rows are
rejected. The underlying [aggregation core](../../evaluation/phase2_subject_aggregation.py)
uses exact `Fraction` arithmetic to produce **208 five-seed subject-method
means** and retain the 1,040 input cell digests. The builder then forms **52
sorted, exact LoRA-minus-linear subject differences**. It checks complete
group coverage and five contributing cells per mean. The synthetic tests also
exercise shuffled input order, malformed digests and drift in the frozen
subject, method, seed or shot constants. A synthetic complete roster flows
through the [pure inference calculator](../../evaluation/phase2_inference.py).

`ScoreRow` is a **caller-supplied trust boundary**. Its constructor validates
the case key, a rational score in `[0, 1]` and digest syntax; the builder
checks roster and digest uniqueness. Neither function proves that a score or
digest came from a real recorder publication. The caller must independently
verify every cell's bytes, balanced-accuracy numerator and denominator,
identity, source, cohort, episode, selection, method configuration and
scientific admission before constructing rows. The
[analysis identity review](cho_analysis_identity_binding_review_20260928.md)
and [execution contract](cho_analysis_execution_contract_20260924.md) describe
related checks and remaining admission requirements. This builder reads no
records and does not write a report or decide the proposed
[statistical rule](cho_four_method_freeze_technical_proposal_20260928.md).

The source fingerprint after the initial pair builder was
`a7841e14fde97a8badc62ad5ce1e0c204183ab79e023e2b7138c42d6c3c5f311`.
The [previous full quality archive](../../runs/phase2/quality_history/20260928_cho_analysis_identity_5dce82b1.json)
pins source `5dce82b1`, so it is stale for this code. New exact-source full
quality and source-bound evidence were pending while D: free disk was below
the 20 GiB floor. The 12 focused tests did not replace that gate.

The [first full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_paired_inputs_a7841e14_disk_floor/receipt.json)
on `a7841e14` passed Ruff and mypy, with 810 tests passed, 1 skipped and
4 failed. All four failures were synthetic case-engineering tests stopped
by the real 20 GiB result-frame disk prelaunch guard. The attempt was
preserved as failed evidence; it is not a quality pass. A test-only
function-scoped fixture now supplies an ample deterministic resource
reading to those lifecycle tests, while running the real Windows child,
Job, frame and post-child guard. Production floors remain unchanged. A
new channel-specific regression confirms that a post-child disk drop
still blocks proposal and attestation publication.

The current source is
`ef8b3f8289de6d23418d5e4d287be2ddc1a745f6b6ad164ae21cfc034f12be9c`.
Its [focused write-once receipt](../../runs/phase2/analysis_pairing_checks/20260928_ef8b3f82_focused/receipt.json)
records Ruff and strict mypy passes plus **37 tests passed, 1 skipped**
across the changed files. This remains focused verification. A second full
quality attempt was deferred before launch as D: fell to about 9.3 GiB
free; there is no current-source full quality archive or refreshed control
evidence. The 20 GiB fit guard remains in force.

No scientific cell, fit, inferential report or claim was produced. The
analysis configuration is unratified, and Gate A remains unsigned.
