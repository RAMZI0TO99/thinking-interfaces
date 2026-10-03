# Cho2017 Profile B preparation

17 September 2026, milestone 29. The primary E2 dataset now has encoder-ready
Profile B inputs: the shared Profile B pipeline gained a Cho2017 subject
preprocessing function over the pinned local GIGADB raw files, a bounded
preprocessing script, and a preparation audit for the pilot's two Cho subjects.
Cross-profile episode binding for Cho remains the next milestone; no scientific
configuration or measurement is involved.

## Contract and implementation

`data/profile_b.py` now exposes `collect_profile_b_runs()`, the run-collection
loop refactored out of the BCI subject function unchanged, plus
`preprocess_profile_b_cho_subject()`, which mirrors the BCI wiring with MOABB's
`Cho2017` dataset and the Cho module's local GIGADB cache and download guards.
The run-level pipeline itself is untouched: pick EEG, FIR bandpass and notch,
resample to the configured rate, epoch at the cue without baseline subtraction,
and scale to the declared amplitude unit. The BCI subject function's behavior
is byte-identical after the refactor; its existing tests pass unmodified.

`scripts/preprocess_profile_b_cho2017.py` mirrors the BCI Profile B script:
explicit subject roster from `configs/cho2017.toml` (refusing subjects outside
it), the unchanged Profile B configuration from `configs/base.toml`, and
artifacts plus manifests under `data/processed/cho2017/profile_b/`.

## Bounded generation and preparation audit

Full-cohort generation would consume roughly two gigabytes and push free disk
below the unchanged 20 GiB floor, so this milestone generated only the two
subjects the pilot specification names for Cho2017: the development target
`subject_01` and the representative inner fold `subject_02` — about 76 MB.
The remaining fifty subjects wait for the disk headroom the user deferred.

The preparation audit verified for both generated subjects, against the saved
cho2017 audits and the untouched Profile A artifacts: identical trial counts
and per-trial label, session and run correspondence with Profile A; identical
64-channel montage; finite signals shaped (200, 64, 800) at 200 Hz with
200-sample patches and four patches per epoch; manifest fields matching the
actual bytes; Profile A artifact hashes unchanged from the pinned catalogs; and
byte-stable re-reads. The pilot's Cho cases remain marked unmeasurable until
the cross-profile binding milestone lands.

## Verification

The focused suite passed **5 tests**, including a new offline unit test that
drives `collect_profile_b_runs` with synthetic annotated MNE raws across two
sessions and runs, checking trial joining, label/session/run/index identity,
channel stability and the empty-collection refusal.

Full lint and strict types pass. The exact-source suite passes **542 tests /
907 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/cho_profile_b_checks/20260917_step29/`.
Current source fingerprint:
`3733247558ab82063a0e6af00a2b270dd057ef56828a79de954bd863934975f1`.
`data/profile_b.py` changed by the behavior-preserving refactor plus the new
Cho function, `tests/test_profile_b.py` gained one test, and the preprocessing
script is new.

## Next work and unchanged limits

Next is the Cho2017 cross-profile episode binding (the A/B join, nested
episode reconstruction and LaBraM 64-channel electrode mapping), then the
remaining fifty subjects once disk is freed. The D01-D06 decisions, operator
compute admission, the scientific freeze and the RAM-deferred control refresh
remain user-gated. P2 remains partial; no gate or guard changed and no
scientific experiment ran.
