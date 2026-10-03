# Pre-cue control: synthetic post-cue influence diagnostic

**Date:** 23 September 2026. **Scope:** read-only synthetic diagnostic of the
current Phase I pre-cue control preprocessing. Gate A remains unsigned.

`data/pre_cue.py` calls `Raw.filter(method="fir", phase="zero")` on the
continuous run, then applies the average reference and resamples. Only after
these steps does `extract_pre_cue_trials` cut the one-second interval ending
at each cue. A symmetric zero-phase filter can therefore draw signal from
after a cue into samples before it. The extraction-only tests do not exercise
this ordering.

The [diagnostic script](../../scripts/diagnose_pre_cue_post_cue_leakage.py)
creates two otherwise silent, 12-second, two-channel synthetic runs at 250 Hz.
Both have a cue at 5.0 seconds. One has a single 100 microvolts C3 pulse at 5.04
seconds; the other has none. Their raw pre-cue samples are exactly equal. The
script processes both with the Profile A settings in `configs/base.toml`
(8 to 30 Hz zero-phase FIR, common-average reference, 128 Hz resampling and a
one-second window). It also compares the pre-cue interval immediately after
the filter and reference, before resampling.

| Stage | Maximum absolute difference in pre-cue window |
| --- | ---: |
| Raw, before preprocessing | 0.000000 microvolts |
| After full-run FIR and reference, before resampling | 1.989618 microvolts |
| After the production pre-cue pipeline | 1.997180 microvolts |

The pre-resampling difference identifies the continuous zero-phase filter as
an influence path. Mean centering at extraction does not eliminate it. This
proves a *possible* post-cue influence under the present code and chosen
synthetic input. It does not estimate its prevalence, magnitude or effect on
classification in the real BCI IV 2a recordings, and it does not by itself
invalidate or accept the reported negative-control accuracy.

Reproduction: run
`.venv\Scripts\python.exe -m scripts.diagnose_pre_cue_post_cue_leakage`
from the repository root. The run used MNE 1.12.1, source
`data/pre_cue.py` SHA-256
`b8d60c0ad8bb1247e00e08697529f7e94964279342e759da1a3858a1cb4a91c6`,
and `configs/base.toml` SHA-256
`02c8e3011abfcafe170f791ec688c791b2187d8e547dd3b2655bae2b5eedf2c4`.
The focused diagnostic and extraction tests passed (4 tests); Ruff and strict
mypy passed for the new script and test. The test asserts identical raw
pre-cue inputs and a measurable difference after filtering and after the
production pipeline. It documents the current behavior and should be revised
if the preprocessing order is deliberately changed.

Before any scientific Gate A acceptance based on the pre-cue control, a
predeclared replacement control or a real-recording sensitivity analysis is
needed. This diagnostic does not change preprocessing, existing control
artifacts, thresholds or scientific results.
