# Proposed no-future pre-cue control v1

**Status:** proposed, unratified preprocessing contract. Gate A remains
unsigned. All nine proposed control artifacts have now been saved and
raw-recomputed on readback. There is no matched classifier result and this
version does not replace the historical `pre_cue_control` identity. The
[write-once cohort receipt](../../runs/phase2/gate_a_diagnostics/20260923_no_future_artifact_pairs/receipt.json)
(envelope SHA-256 `1ef7e05bf4cc0b4cc598ab19569ca716814a2d29ee8feffe37c4f51e62357c5d`)
pins the nine artifact/manifest pairs, 5,184 windows, source and signal-audit
identity. Its file SHA-256 is
`52d6862fbfc5e862e748cd9a0da076b1f71b102f2e5840f30065a0f962084bcf`.

The [versioned config](../../configs/pre_cue_no_future_v1.toml) and
[implementation](../../data/pre_cue_no_future.py) define the following order
for each annotated BCI IV 2a cue:

1. Read the cue sample from the original raw annotations and select the
   canonical 22 EEG channels and four-class event mapping.
2. Copy raw EEG samples from the start of that run **up to but excluding**
   the cue sample. Samples at and after the cue are never supplied to a
   signal-processing operation for that window.
3. Apply the same 8–30 Hz, zero-phase FIR bandpass as Profile A to this
   prefix, then common-average reference and resample to 128 Hz.
4. Take the last 128 resampled samples and subtract each channel's mean.

The filter is zero-phase *within the available prefix*. This is a no-future
input contract relative to the cue, not a claim of real-time causal filter
phase or equivalence to continuous-run filtering. Endpoint padding and a
separate resampling boundary can change the distribution; the [real-run
sensitivity](real_pre_cue_future_sensitivity_20260923.md) measured that
distinction on eight subject 01 cues.

The current MNE 1.12.1 FIR kernel is 413 samples at 250 Hz. The contract
requires a prefix of at least the larger of that full kernel and the raw
one-second window, so the current minimum is **413 raw samples**. A cue at
the boundary is accepted; a shorter prefix is rejected before filtering.
The config records that policy, and a future manifest records the observed
minimum along with the MNE version and config hashes.

The proposal reserves
`data/processed/bci_iv_2a/pre_cue_no_future_v1` and assigns
`artifact_kind=pre_cue_no_future_control_v1` and
`manifest_kind=pre_cue_no_future_manifest_v1`. The separate summary builder
validates shape, channel order, finite float32 values and subject identity,
then returns metadata in memory. The historical `data/pre_cue.py`, its
manifests and saved control data were not changed.

The [proposed writer](../../scripts/preprocess_pre_cue_no_future_v1.py) can
build one subject at a time from the 18 already cached BCI raw files. It
pins the [revised all-nine-subject signal audit](../../runs/phase2/gate_a_diagnostics/20260923_no_future_all9_posthash/real_pre_cue_no_future_all9_posthash.json)
by file SHA-256
`14accc31cb041b17cda1a670bbaae635a1fee53500d3ebbce95608a12ae69be5`
and envelope SHA-256
`3327faa236306f6a83ce28a53be541bebd934fcad53023ca6f468e80436c6770`.
It checks each selected raw file's size and SHA-256 before and after processing
against that receipt, verifies all eleven source/config paths sealed by the
audit, and rejects library-version or cue-roster drift. For each subject it requires
exactly two sessions, twelve runs, 48 cues per run, 576 windows of shape
`(22, 128)`, and 144 windows per class. MOABB's file resolver is replaced
within the local load call by a resolver that accepts only that subject's two
verified local files; a download request fails closed. Available disk must
remain at least 20 GiB and RAM at least 4 GiB before each run and write. The
NPZ publisher reserves twice the uncompressed array size plus 1 MiB above
the 20 GiB floor, then checks the floor again after writing the temporary;
the manifest publisher reserves its encoded bytes plus metadata headroom.

Each artifact is a compressed NPZ containing signals, labels, sessions, runs,
trial indices and ordered channel names. The writer fsyncs a same-directory
temporary and publishes through an atomic, no-clobber hard link. It writes
the source/raw/config-bound manifest **after** the artifact. A completed pair
is accepted for reuse only after all 576 windows have been rebuilt from the
pinned local raw files and every saved array is exactly equal; an artifact
left without a manifest can resume
only if its bytes exactly match a newly rebuilt artifact. A manifest without
an artifact, or any conflicting existing bytes, stops without replacement.
All outputs stay in the new `pre_cue_no_future_v1` namespace. A dry run with
`python -m scripts.preprocess_pre_cue_no_future_v1 --subjects 1 --dry-run`
checks the pins and resources without producing an artifact.
`python -m scripts.preprocess_pre_cue_no_future_v1 --subjects 1 2 3 4 5 6 7 8 9 --check-only`
rebuilds all selected subjects from raw and checks their completed pairs,
including every stored array and exact manifest bytes, without writing. It
requires each selected pair to exist.

The writer rechecks resolved output paths immediately before each hard link.
On Windows, a hostile concurrent directory swap in the interval between that
check and the link could still redirect publication; fully closing that race
would need a handle-based publisher. The raw/source pre- and post-hash checks
also do not prove immutability against a file changed and restored between
checks. Keep the raw and output directories exclusive during a rebuild.

The initial subject 01 dry run passed against the revised signal receipt and
left the proposed output directory absent at that time. The subsequent
all-nine build created 18 files totaling **54,308,340 bytes**. The writer's
read-only `--check-only` passed all nine, and the cohort receipt independently
recomputed all 576 windows per subject before publication. The writer's
synthetic tests cover
no-clobber publication, identical orphan resume, conflicting bytes,
manifest-last verification, resource and raw/source hash guards, local-only
MOABB loading, and audited subject shape/order. Together with the processor
tests, 13 tests and 4 subtests passed, including rejection of a self-consistent
forged NPZ/manifest with signals different from recomputed raw. Ruff and strict mypy passed for the
writer. No saved proposed EEG or model evaluation resulted from these checks.

The [focused tests](../../tests/test_pre_cue_no_future.py) perturb the raw
cue sample, later samples and both together. All three altered runs produce
windows **exactly equal** to the unaltered window. Tests also cover the
full-FIR boundary, short-prefix and out-of-range refusals, canonical event
mapping, and distinct summary identity. The 3 new tests passed; with the
earlier pre-cue and diagnostic tests, 7 passed. Ruff and strict mypy passed
for the new module and tests.

A read-only integration check on locally cached subject 01 session `0train`,
run `0`, produced **48 windows of shape (22, 128)** and an in-memory summary
with the new identities. It wrote no processed EEG or scientific result.
The config file SHA-256 is
`4f6208feafb4fc76c27f79f28bff3702183eeb42ca7511d7ff227d7a55f5fa91`;
the implementation SHA-256 is
`31dd1b0ff44858d4bf05680667aecdb2858dcc9fd7ed89c09ed979f23d6b05c5`.

The versioned input rebuild and raw-source/artifact provenance are now
available for review. A [separate matched-control plan](no_future_matched_control_plan_20260923.md)
retains the historical EEGNet preset and 0.35 comparison limit, with distinct
proposed output identity. It still needs current-source quality, its unchanged
resource admission, actual fits and an independent Gate A decision. None is
inferred from the saved signals.
