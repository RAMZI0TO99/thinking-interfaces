# Declared ordered preprocessing bridge

Declared on 2026-08-31 before any intermediate-condition model fits. This is
post-hoc debugging of the existing A01/seed-11 comparison, not preregistration,
model selection, a new benchmark, or a Gate A acceptance threshold.

All seven conditions will be reported, in this fixed order. The original
230/58/288 optimization/validation/query partition, 20 maximum epochs, batch 64,
learning rate 0.001, patience 5 and model are unchanged. Query labels cannot
select conditions, stopping rules, preprocessing settings or a preferred model.

| Condition | Change from preceding condition |
|---|---|
| Original B | Saved B in original 0.1-mV units |
| B in microvolts | Multiply the same saved input by 100 |
| A filter specification | Replace 0.1–75 Hz plus 50-Hz notch with 8–30 Hz and no notch; retain 200 Hz, original reference, no baseline |
| Common-average reference | Add CAR; other settings retained |
| A sampling rate | Change 200 to 128 Hz; four-second epochs retained |
| A pre-cue baseline | Subtract the one-second pre-cue mean |
| Exact A representation | Remove B's intermediate 0.1-mV float32 conversion; use the canonical saved-A voltage-to-microvolt path |

The final representation step separates float32 rounding from physiological
preprocessing. Raw intermediate conditions use the independently checked MAT
cue origin and manual epoch extraction. The first two stored inputs and final
canonical A endpoint are checked against their unchanged saved artifacts. All
three endpoint scores must reproduce the preceding diagnostic; an inconsistency
is reported as a failed compatibility check rather than silently accepted.

Adjacent score differences are conditional on this chosen order. They telescope
to the endpoint gap but are not independent additive causal contributions: the
operations interact, filtering and notch removal are grouped, and changing
sampling rate also changes the 64-sample temporal kernel's physical duration.
One subject and one seed cannot establish general profile superiority. No
subsequent outcome-driven setting search is authorized by this diagnostic.

Receipts retain full histories, predictions, input bytes/identity hashes, exact
configuration, source/environment identity and resource observations. They live
under `runs/profile_bridge_diagnostic`, separate from frozen artifacts/results.
Execution requires clean committed source, at least 6 GiB free startup RAM and
1 GiB free GPU memory; before preprocessing stages and every model call the
4-GiB running guard applies. GPU cooling policy is retained. Source-wide leakage
controls must be refreshed after adding this implementation; existing guards,
benchmark settings, outputs and user processes are unchanged.

The first committed invocation stopped before its first model fit: the cooling
loader was passed the project directory instead of its TOML file. Its context
and error log are retained; no condition score was observed. The lookup was
corrected to `configs/runtime_limits.toml`, with a real-path regression test and
another complete source-bound control refresh. No declared condition, training
rule or cooling threshold changed in response to this startup error.

The first seven-fit execution then completed at clean commit
`6163e0dd2e1c2e45668deca52ada58d0031ed07b`, source
`0aec5f63da937ebea3fc0806e9fa976a8ceabc019708818faefd1d8481463341`.
Its endpoint booleans initially failed solely because `ClassificationReport`
retains tuple labels/confusion rows in memory while JSON reload returns lists.
All three saved endpoint results, complete histories, probabilities and splits
are exactly equal to the pinned earlier unit diagnostic. No numerical tolerance
was introduced: the corrected comparison uses exact canonical serialized values,
and tests reject even one-representable-step changes to losses/probabilities.

The original false summary remains preserved at
`runs/profile_bridge_diagnostic/18d425057c93393dc5aeab7ee4c5f9ae6b34b893dd1368e6de42023626d6e89f/summary.json`,
SHA-256 `ad9be35064e6ce369852af34adf772a541e78bc6b3f15f36ef0808d96cf8fc7a`.
Independent serialized-record review checked all seven prediction reports:
`runs/runtime_probe/profile_bridge_serialization_review_20260831T1643.json`,
SHA-256 `8545550df8c5cd59d98409f8a9b02310511010468dbaef3b2826953c734f68ff`.
The reporting correction requires refreshed controls and a separately identified
complete rerun; none of the initial numerical records is overwritten or relabeled.
