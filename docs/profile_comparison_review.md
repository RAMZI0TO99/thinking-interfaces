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

## Source-session signal-energy cross-check

`scripts/audit_profile_signals.py` inspected only the unchanged 288-trial training
session, not the held-out test outcomes. Both profiles were expressed in volts
before comparison. It used a one-sided DFT of each four-second epoch, no
window taper or detrending, separate DC, 0.25-Hz bins, and verified Parseval's
identity. These are finite-window energy allocations, including spectral
leakage, not perfectly isolated physiological frequency-band powers.

| Source-session quantity | Profile A | Profile B |
|---|---:|---:|
| RMS amplitude | 2.6792 microvolts | 10.0279 microvolts |
| DC energy fraction | 0.0456% | 0.8134% |
| Above DC but below 8 Hz | 4.7490% | 66.3801% |
| 8–30 Hz, inclusive | 92.8968% | 26.7328% |
| Above 30 Hz | 2.3086% | 6.0738% |
| Spatial common-mean energy fraction | approximately zero | 83.4320% |

This verifies that the profiles differ in more than storage units: the broad-
band/original-reference B input retains substantial low-frequency and shared-
channel components that A suppresses. The shared component is not identified
as artifact or physiology by this analysis. These signal facts do not assign
the remaining 19.7917-point accuracy gap to any one operation or justify changing
the frozen pipelines; model physical-time kernels and learning dynamics also
differ. No model was trained, no test data selected and no artifact rewritten.

Report: `runs/profile_signal_review/20260831T115831022928Z.json`, SHA-256
`9c1e48965378cc2d5457575eb81acf04877b4bf0694af9a3ae65e32d7f1f1a05`.
It records source provenance, both artifact hashes, complete preprocessing
configuration and the exact source-session indices.

## Independent raw-event and epoch alignment — 2026-08-31

`scripts/audit_profile_alignment.py` independently reconstructed all 576 A01
trials directly from the two original MAT files. It used neither the production
profile helper nor the MOABB dataset/annotation parser. Native MAT trial markers
are one-based trial starts; the cue is two seconds later. The installed MOABB
annotation conversion already applies that offset. Adding another two seconds
to the existing production epochs would be incorrect.

The independent path checked labels, sessions, six run identities per session,
within-run trial order, channels, sample counts, filtering, reference, resampling,
baseline and stored-unit quantization. All 24 run/profile comparisons passed:
576 epochs per profile, 1,152 comparisons in total. Every reconstructed float32
value was exactly equal to the corresponding saved value (maximum difference
0.0 volts), stronger than the declared numerical tolerance. Raw inputs and both
saved artifacts remained byte-identical. No model was trained or profile changed.

Receipt: `runs/profile_alignment_review/20260831T160810847353Z.json`, SHA-256
`79e7492050c1fc40cd53b56e1a0e3b907bed1800c9fc3ef8e64e6586508c7e06`.
Audit-code SHA-256:
`de491723f4ee704ec02e6262e884483b77f854f4df35a1c5fffbc5370019abc9`.
Its actual staged source was
`3a004d326f567c021b2a3a475d2bc5dfc50683007527ebc20aec9912c3d6c1fc`;
the receipt correctly records the preceding commit with dirty source. Forty
resource checkpoints observed at least 10.848 GiB free RAM.

This closes the independent A01 epoch/timing check, not the remaining 19.7917-pp
accuracy attribution. It neither validates all nine subjects independently nor
establishes online causal filtering or Gate A acceptance. The main benchmark was
deliberately paused at 16:07:58 UTC, about 69 seconds after saving Cho EA subject
48; some unsaved subject-49 work was discarded. All 2,141 completed records
remained valid and unchanged. No unrelated process was stopped.

## Complete ordered explanation — 2026-08-31T16:47Z

The seven-condition protocol in `docs/profile_bridge_protocol.md` was fixed
before intermediate fits. Every condition used the original A01/seed-11 model,
230/58/288 split and training/stopping recipe. Both B endpoints and the final A
endpoint exactly reproduce the earlier complete results, histories, probabilities
and splits. Independent checking verified every saved prediction report. The
final raw-reconstructed A input also exactly matches the unchanged saved A input.

| Ordered condition | Balanced accuracy | Change from preceding condition |
|---|---:|---:|
| Original B, 0.1-mV units | 25.3472% | — |
| B converted to microvolts | 36.8056% | +11.4583 pp |
| Replace B filter/notch with A 8–30 Hz, no notch | 35.4167% | -1.3889 pp |
| Add common-average reference | 59.0278% | +23.6111 pp |
| Change 200 to 128 Hz, keeping four seconds | 54.8611% | -4.1667 pp |
| Add one-second pre-cue baseline | 56.9444% | +2.0833 pp |
| Use exact canonical A float32 representation | 56.5972% | -0.3472 pp |

These adjacent conditional changes reconstruct the full 31.25-pp endpoint gap.
After the unit correction, the other five changes sum to the remaining 19.7917
points. The largest positive conditional change is CAR after narrowing the band;
this is consistent with the separately observed large shared-channel component
in B, but does not identify it as physiology or artifact. Narrowing the filter
alone did not improve this particular recipe. The final rounding-only step
changes one correctly classified query trial and is reported rather than hidden.

This is an ordered one-subject/one-seed compatibility explanation, not a unique
causal decomposition: preprocessing operations interact, band/notch changes are
grouped, and resampling also changes the physical duration of the fixed 64-sample
kernel. The original 20-epoch stopping limit is retained; the band-only condition
stopped at epoch 19 under the original patience rule. No winner was selected,
no further outcome-driven tuning followed, and no frozen artifact, original
comparison, benchmark, gate threshold or support partition was changed.

Corrected run directory:
`runs/profile_bridge_diagnostic/ff5fe8556b0a342ade4450dfcfa8ccc9e1a406516fc5331f28a43f1fdbc33536/`.
Summary SHA-256:
`440a41843d93015e2eeea45c7025c2a3884a3fd59048ed5456636ef13f25fc3f`.
Source fingerprint:
`c8af5d97c0965f0933621a53389a3a558e593e78a0ca42d7ae48ee4832a48679`.
All seven fits were rerun after a tuple/list reporting correction; their complete
numerical results and signal identities exactly match the retained initial seven
fits. The initial false summary and independent serialization explanation remain
preserved, not overwritten. The corrected summary's endpoint checks all pass.

Independent verification: `runs/runtime_probe/profile_bridge_verified_20260831T1646.json`,
SHA-256 `3e2c395a5a15422e877bcaa4a3e517859d4d0746c8ea2a967dd2c4c0b0b696ba`.
The 135 total training epochs took 8.991 seconds of recorded fit/prediction work,
excluding raw preprocessing/cooling/auditing. Across 822 preprocessing/model
resource checks, free RAM stayed at least 8.673 GiB and process memory at most
1.754 GiB. All 2,353 benchmark files and raw inputs remained unchanged.

The local one-subject profile cross-check and its bounded explanation are now
complete. The earlier negative profile-score comparison remains negative under
its original rule: an explanation is not a claim of score equivalence, general
profile superiority, online filtering validity or Gate A scientific sign-off.
