# Profile A/B comparison review — 2026-08-31

The saved A01 comparison is a negative compatibility check, not an isolated
estimate of the effect of the frequency band. Profile A obtained 56.5972%
balanced accuracy and Profile B 25.3472%, a difference of -31.25 percentage
points (`runs/profile_comparison.json`). A later controlled unit-conversion
diagnostic below isolates one contributor; the remaining gap is unresolved.
This review does not make the negative result a pass or change any
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
while retaining the split and declaring its settings before scoring. The initial
review had no such ablation; the subsequent unit-only diagnostic is documented
below and remains separate from the frozen benchmark. Gate A remains unsigned.

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
classical worker for GPU training. The completed scores are recorded below.

The first invocation deferred before its first fit because the initial version
reapplied its 6-GiB startup threshold after its own imports/input loading. A
no-training memory probe measured 6.647 GiB free before imports, 6.061 after CUDA
initialisation, 5.905 after baseline imports and 5.832 after both artifacts;
process resident memory was 0.874 GiB. The two signal arrays total only 63.422 MiB.
Before any diagnostic scores were observed, startup and running thresholds were
separated: startup still requires 6 GiB, while a process-local hook checks for at
least 4 GiB before every model call, including validation and prediction. Minimum
observed free memory and maximum sampled process memory are recorded. The hook
does not change the model or optimizer operations; timing includes its overhead.
The main benchmark and MOABB reference resource thresholds remain unchanged.

This is post-hoc compatibility debugging, not a preregistered performance claim.
Its B-vs-B comparison can isolate the conditional effect of input scaling under
this recipe. It cannot isolate the remaining A/B changes (band, reference,
baseline or physical kernel duration), and no outcome automatically signs a gate.

## Controlled result — 2026-08-31T11:47Z

All three conditions completed and their saved query predictions independently
reproduced their metrics. The original Profile A and B scores reproduced exactly;
the original result file remains byte-identical, SHA-256
`8052859abf76ce60ac86097d6f78899b0c1d137ba5911a69f535f44edbef5d2b`.
All three use identical 230-training/58-validation/288-test trial indices and
identical test labels (72 trials in each of four classes).

| Condition | Balanced accuracy | Best/completed epoch | Fit seconds |
|---|---:|---:|---:|
| Profile A, microvolts | 56.5972% | 20/20 | 2.792 |
| Profile B, original 0.1-mV units | 25.3472% | 11/16 | 0.751 |
| Profile B, converted to microvolts | 36.8056% | 20/20 | 0.885 |

Changing only Profile B's multiplier from 1 to 100 raised balanced accuracy by
11.4583 percentage points in this one-subject/one-seed recipe. The unconverted
model predicted right-hand for 287/288 trials and feet for one: its near-chance
score was not caused by imbalanced test classes. Conversion yielded all four
predicted classes (44 feet, 72 left-hand, 158 right-hand and 14 tongue), though
accuracy remained 19.7917 points below Profile A. This is a conditional scale
effect, not proof that the remaining gap belongs to any specific preprocessing
operation or that Profile B is intrinsically inferior. No tuning sweep followed.

Results and complete histories are in
`runs/profile_units_diagnostic/db1103e8d1a58205468e9565f2843790639b2fd10ad4493888d17451c0987b03/`.
Summary SHA-256:
`54a2e1b7599401680ca05d286fc15e9e33a73812cd9392390ba2b3b5ae65925b`.
Record hashes (A/original B/microvolt B):
`d408d6b6d1e3a56e28bbbf65c4ee81772ef99c48db8602f6f165cbe7d44b3229`,
`c5390bf791045ebfc11494cdf794b4f252e7781b2740c045ff1508fd710688d1`,
`eb25fb982479057e6bd89f0635e1b45e0afb8c21ed62ad968ca304b6629e3395`.
Source was clean commit `bee006f9085d607751e79dfb26802bfdb371c364`, fingerprint
`cabd149765f21a6afc5d4bdc9645c33d6cd62d6a2e8f239b533b244e17b26a45`.
Across 310 model-call checks, free memory never fell below 4.868 GiB; maximum
sampled diagnostic process memory was 1.693 GiB. The main benchmark was not
paused or modified. Timings include resource checks and are not general runtime
estimates; the first condition also paid initial GPU setup overhead.
