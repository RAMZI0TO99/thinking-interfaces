# Matched BCI anchor integration

8 September 2026. Nineteenth bounded Phase II step.

`adaptation/anchor_manifest.py` connects EEGNet and EA-tangent logistic regression
to the same audited trial partitions as the six LaBraM methods. Anchors consume
the existing Profile A contract (22 channels, 128 Hz, 512 samples, volts), while
LaBraM consumes Profile B. Matching refers to subject roles, retained trial IDs,
selected support and common queries; the profiles remain explicitly different.

## Binding and permissions

The new `load_bci_profile_a_subject` in `evaluation/phase2_profile_binding.py`
verifies pinned artifact/manifest bytes, fixed Profile A configuration and metadata,
reconstructs the thresholded catalog, and returns owned retained rows in catalog
order. It shares existing profile validators without modifying the A-to-B loader.
It does not require Profile B artifacts or independently reproduce raw filtering.

`BCIAnchorManifestRunner` requires all nine trusted catalogs and A-manifest hashes,
the protocol and reconstructed source-selection envelope, a fixed outer target and
optional fixed inner-validation subject. Directory/cohort, classes and hashes are
checked. Predictions reconstruct the complete saved episode before loading signals.
Wrong-role/subject calls cannot bind data. There is no public tensor, trial-index,
query-subset or source-cohort override. Unused target support-pool rows never enter
either fit or prediction.

## EEGNet

The caller supplies an installed EEGNet source template with 22 input channels,
four classes, 512 samples and 128 Hz metadata. The runner owns a finite CPU float32
copy; prior source-training subjects and history remain trusted, unverified input.
`EEGNetAnchorSettings` explicitly declares steps, learning rate, input scale and
query batch size. A fresh model and SGD optimizer are created per episode.
Every parameter, including normalization affine weights, is selected; normalization
buffers and dropout remain in evaluation mode. Queries run under inference mode.
Source and complete adapted-state hashes must remain unchanged across queries.
The installed max-norm parametrizations remain active and do not mutate stored
weights during inference. No Phase I adaptation routine or split API was changed.

## EA-tangent logistic regression

`EATangentAnchorSettings` declares alignment regularization, logistic C, iteration
limit and query batch size. The existing source-plus-support recipe is retained:
each permitted source subject gets an EA fit using all of its retained trials;
target EA is fitted on selected support only. Source covariances are assembled one
subject at a time, avoiding a combined multi-subject EEG signal array. OAS
covariances, a Riemannian tangent reference and balanced logistic regression use
all permitted source trials plus the selected support. Outer and inner held-out
subjects are excluded from the source loop. Query data never enter these fits.

Every call creates fresh aligners and a fresh decoder. Logistic convergence
warnings abort the call. Class order and finite normalized output probabilities
are checked. Complete locally created alignment/decoder state is serialized only
in memory for SHA-256 comparison before/after queries; no pickle is saved or loaded.
Results record the exact source trial IDs, pinned input identities, target
whitener, fit policy and fitted-state identity.

## Scope and next step

`AnchorPrediction` records settings and their digest, selection/episode identities,
support/query IDs, profile units, source permissions, fit details, probabilities and
targets. It remains engineering evidence with source-training history unverified.
For EEGNet, `source_subjects` declares permission, not verified prior fitting.
For EA, actual source-plus-support fitting is performed and its inputs are recorded.
No accuracy metric or scientific cell is published.

This completes the bounded BCI anchor connections. Source-model training provenance,
source-only candidate selection, broader dataset coverage and the measured pilot
remain open. Next is the source-training and selection contract with a bounded
executor. The RAM-dependent control refresh remains deferred, with guards unchanged.

## Tests and real-data evidence

Nine new tests / 19 subtests verify both anchors against Profile B trial IDs at
1/5/10/20 shots, exact EEGNet repeats, support-only gradients and unchanged caller
state/modes/gradients/RNG and normalization buffers. EA-tangent matches an independent
raw-signal reconstruction of the existing source-plus-support recipe. Altering
target-query labels and signals leaves both fitted states and fit metadata identical.
Wrong roles, rehashed selection changes, changed source/target bytes, invalid
settings and changed Profile A configuration fail closed. Anchors also run with
Profile B unavailable. Deliberate query-time state mutation and NaN outputs fail.

Focused checks passed (16 tests / 45 subtests, then two additional tests).
Full quality checks:

```text
All checks passed!
Success: no issues found in 153 source files
475 passed, 4 warnings, 759 subtests passed in 181.38s (0:03:01)
```

The warnings are the existing two EEGNet deprecations, classification warning and
pytest cache write-permission warning. The exact-source quality bundle and its log
hashes pass independent validation.

The real check reconstructed all nine BCI catalogs and used a seeded random EEGNet
source (22 channels, four classes, constrained linear classifier, 2,484 parameters).
EEGNet engineering settings were one full-support SGD step at 0.0001, input scale
1,000,000 (volts to microvolts), and query batches of eight. EA used regularization
0.000001, C=1, maximum 1,000 iterations and query batches of eight.

Both anchors passed on subject 01 as outer target and subject 02 as inner validation.
All four results match the independently bound Profile B episode: four support
trials and 496 common query trials, with matching labels and finite `[496,4]`
probabilities. The EEGNet outer repeat reproduced state, losses and probabilities
exactly. Caller source/RNG and all 36 A/B artifact/manifest files, nine saved episodes
and selection record were preserved.

There were three EEGNet support steps including the repeat, zero neural source
training steps, and two classical source-plus-support fits. EA used 4,602 source
trials from subjects 02-09 for the outer target, and 4,026 from subjects 03-09 for
inner validation; each fit also included four target-support trials. No accuracy
was calculated. Execution used CPU float32 EEGNet and two Torch threads; the
classical covariance/tangent calculations retain their existing precision policies.

Source fingerprint:
`99bebe21cb6553892fe9a41b6acd4ab069e67541394e59b20509e5e340d1304a`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
`evaluation/phase2_profile_binding.py` has additions only; its prior functions
remain unchanged. The anchor module and tests are new. All other pre-existing
source/config/test files retain their hashes. The prior quality status was saved.

Evidence: `runs/phase2/anchor_manifest_checks/20260908_step19/`, including before
snapshots, binding diff, focused logs, real check script/log/receipt, immutable
engineering predictions, quality status, receipt and documentation preservation
receipt. Full quality logs: `runs/quality/20260908T170436739895Z/`.
