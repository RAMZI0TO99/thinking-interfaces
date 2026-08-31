# Profile A/B comparison review — 2026-08-31

The saved A01 comparison is a negative compatibility check, not an isolated
estimate of the effect of the frequency band. Profile A obtained 56.5972%
balanced accuracy and Profile B 25.3472%, a difference of -31.25 percentage
points (`runs/profile_comparison.json`). The causal explanation remains
unresolved; this review does not make the negative result a pass or change any
preprocessing, benchmark record, acceptance threshold, or H2 source record.

## Checks against current artifacts and code

The two configured A01 artifacts have exactly equal labels, session IDs, run
IDs, within-run trial indices, and channel names/order. Both contain 576 trials:
144 per class and 288 in each session. The comparison calls the same training
function with seed 11 and the same session/validation settings. Given the equal
metadata, its deterministic split selects the same trials for training,
validation, and final evaluation. This verifies identity/order, not independent
validation of the raw cue timestamps or every preprocessing operation.

| Difference | Profile A | Profile B |
|---|---|---|
| Frequency band | 8–30 Hz | 0.1–75 Hz plus 50 Hz notch |
| Reference | Common average | Original dataset reference |
| Pre-cue correction | Subtract one-second channel baseline | None |
| Four-second epoch | 512 samples at 128 Hz | 800 samples at 200 Hz |
| Stored amplitude | Volts | Units of 0.1 mV |
| Training input multiplier | 1,000,000 | 1 |
| Input standard deviation from saved result and multiplier | 2.6584425541 | 0.1001149714 |
| Default 64-sample first temporal kernel | 0.500 seconds | 0.320 seconds |
| Selected checkpoint | Epoch 20 | Epoch 11 |

The code passes sampling frequency and epoch sample count to the same pinned
Braindecode EEGNet but does not supply a profile-specific temporal kernel.
Consequently, this is not a matched physical-time model comparison. Numeric
input scales also differ substantially; Profile B's intended encoder units
are not automatically an equivalent EEGNet training scale. These are verified
differences, not evidence that any single one caused the accuracy reduction.
The selected epochs alone do not reveal the complete learning trajectory;
the saved comparison omits the histories and per-class confusion matrices.

## Interpretation and remaining limits

Both pipelines can produce structurally valid epochs while providing different
inputs to a short EEGNet training run. The check therefore does not establish
interchangeability, exact LaBraM preprocessing parity, or Profile B's suitability
for this EEGNet recipe. A controlled diagnostic would need to separate amplitude
units, temporal kernel duration, referencing, baseline correction, and filtering
while retaining the split and declaring its settings before scoring. No such
ablation has been run or added to the frozen benchmark. Gate A remains unsigned.

Evidence inspected: `configs/profile_comparison.toml`, `scripts/compare_profiles.py`,
`encoder/eegnet_baseline.py`, `data/profile_a.py`, `data/profile_b.py`, both A01
artifact metadata arrays, `runs/profile_comparison.json`, and the pinned-EEGNet
implementation review. This is a read-through of current code and existing
results, not a rerun or a reconstruction of missing historical provenance.

## Declared post-hoc unit diagnostic

`configs/profile_units_diagnostic.toml` declares three bounded conditions before
new scores are observed: Profile A in microvolts (the original multiplier of
1,000,000), Profile B in its original 0.1-mV units (multiplier 1), and Profile B
converted to microvolts (multiplier 100). The latter two use exactly the same
stored signals, model, seed 11, sessions, validation split and training recipe.
Only their numerical input multiplier differs. All other settings come from the
unchanged original comparison configuration: A01, maximum 20 epochs, batch 64,
learning rate 0.001, validation fraction 0.2 and patience 5.

`scripts/diagnose_profile_units.py` saves full histories, class counts, confusion
matrices, query probabilities, exact split indices, source identity and artifact
hashes in a separate resumable output folder. The existing comparison result
and frozen benchmark are never overwritten. The declared GPU run checks free
memory first, uses two CPU threads and does not compete with the main CPU-only
classical worker for GPU training. No diagnostic scores exist yet.

This is post-hoc compatibility debugging, not a preregistered performance claim.
Its B-vs-B comparison can isolate the conditional effect of input scaling under
this recipe. It cannot isolate the remaining A/B changes (band, reference,
baseline or physical kernel duration), and no outcome automatically signs a gate.
