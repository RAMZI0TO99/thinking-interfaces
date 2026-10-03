# Cho full-roster synthetic inference rehearsal

28 September 2026. The [write-once engineering receipt](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c_full_roster_synthetic/receipt.json)
pins a low-resource rehearsal from the [exact aggregation core](../../evaluation/phase2_subject_aggregation.py)
to the [pure paired calculation](../../evaluation/phase2_inference.py).
It read the planning crosswalk and current-source route evidence, then
generated every score locally. It read **zero real cell scores**, trained no
model, admitted no scientific cell and published no scientific report.

The [script](../../runs/phase2/analysis_inference_checks/20260928_9bf0516c_full_roster_synthetic/run_synthetic.py)
independently built the Cartesian roster of 52 canonical Cho subjects ×
four selected methods × five fixed seeds at five shots and required exact
set equality with the 1,040 saved planning cells. It checked the current
`9bf0516c` source, verified full quality, the current 1,040/1,040 no-fit
route receipt and the unchanged planning-crosswalk bytes before use.

Two synthetic score rules each produced **1,040 exact-rational rows → 208
five-seed subject-method means → 52 LoRA-minus-linear subject differences**.
Every mean and paired difference was checked against an independent formula;
missing and duplicate rows were refused. The all-`1/2` rule exercised the
declared all-zero policy (`p = 1`, statistic `0`, point intervals). The
second rule included positive, negative, zero and tied differences plus
seed-varying scores. Its Pratt statistic and p-value matched a separate
SciPy call on common-denominator scaled integers; its 95% mean interval
contained its 90% interval. The receipt's numbers are explicitly
**synthetic engineering outputs**, not Cho decoding results or a claim.

The unchanged read-only guards passed: available RAM was 4.884 GiB before
and 4.772 GiB after, with 34.389 GiB disk free. This does not satisfy the
separate 10 GiB control-fit startup guard. Source fingerprint
`9bf0516c11aec1e3cda0635e79fc58a7cc3db5d2df4d496a2039ab661ad597b9`
still matches the [796-test exact-source quality archive](../../runs/phase2/quality_history/20260928_pure_inference_9bf0516c.json).

The rehearsal proves the synthetic calculation handoff and complete roster
arithmetic. Its fabricated `ScoreRow` digests do not establish real-cell
receipt authenticity. A real analysis still needs an independently
verified collector, ratified executable configuration, report publication
contract, complete-work budget and source-bound controls. The proposed
5,253-step selection exceeds the unchanged 256-step engineering cap;
Gate A remains unsigned. The owner choices are in the
[freeze review sheet](cho_four_method_freeze_review_sheet_20260924.md).
