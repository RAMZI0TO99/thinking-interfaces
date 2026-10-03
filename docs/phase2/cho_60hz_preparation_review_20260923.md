# Cho2017 Profile B 60 Hz preparation review

23 September 2026. The owner selected a four-method first exploratory Cho
five-shot tranche and asked for a 60 Hz Profile B rebuild. This review records
the engineering preparation and the next admission boundary. It does not
ratify the scientific freeze or admit preprocessing or scientific cells.

**Later real-cohort update, 23 September 2026:** After disk headroom was
restored, all 52 versioned 60 Hz subject pairs were generated and independently
audited. The predeclared subject-01 diagnostic passed with 30.67 dB 60 Hz
line-to-sideband attenuation; full-cohort Profile A-to-B joins and real
five-shot bindings passed 52/52. All 52 historical 50 Hz NPZ hashes still
match the saved cohort receipt. The evidence and resource stop below describe
this review's earlier preparation snapshot. See the
[real-cohort review](cho_60hz_real_cohort_review_20260923.md) for the later
result and current gates. No scientific cell or source-bound control refresh
was run, and the scientific freeze remains unratified.

## Prepared path

- `configs/phase2/cho_profile_b_60hz.toml` copies the shared Profile B settings
  with only the notch changed to 60 Hz. The shared `configs/base.toml` remains
  at 50 Hz for historical Cho, BCI and MMIDB inputs.
- `scripts/preprocess_cho_profile_b_60hz.py` accepts a declared Cho subject
  roster and writes only to `data/processed/cho2017/profile_b_60hz_v1/`.
  It checks the metadata line frequency, pinned config identity, raw source
  bytes, finite 64 by 800 signals, and the 20 GiB disk floor with a 2 GiB
  pre-subject reserve. Publication refuses an aliased output path, a partial
  pair, or different bytes at an existing destination. A same-byte pair may
  be reused. The historical 50 Hz writer and directory are unchanged.
- `evaluation/phase2_profile_binding.py` has an explicit 60 Hz Cho binding
  schema and asset type. It checks the variant config and its hash, the
  versioned artifact and manifest hashes, raw source bytes, full Profile A/B
  trial joins, montage, labels, and episode identities. The older 50 Hz
  binding keeps its original schema and hash inputs.
- `adaptation/labram_manifest.py` chooses the matching full-cohort directory
  and refuses a mix of 50 Hz and 60 Hz Cho assets before any fitting.
- `scripts/audit_cho_profile_b_60hz_bounded.py` is a read-only diagnostic for
  predeclared `subject_01`. It requires seven independently supplied input
  hashes, checks the Profile A/50 Hz/60 Hz trial joins and raw provenance,
  then reports 50 Hz and 60 Hz line-to-sideband power ratios. A provisional
  engineering diagnostic requires at least 6 dB attenuation at 60 Hz against
  the historical artifact. It uses no model accuracy and cannot admit a
  scientific cell by itself.

An independent review found an output-directory alias risk and a missing raw
hash check in the first binding draft. Both were fixed, with Windows junction
and changed-raw regression cases. Synthetic bounded-diagnostic cases pass;
they do not establish that the real Cho signal has passed the diagnostic.

## Evidence and current stop

The dry run for subject 01 resolves only the new directory and does not read
raw EEG or write an artifact. The prepared config's byte hash at that dry run
was `6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3`;
the Profile B settings digest was
`d395915d657ed4b9c69e203fe2e83fcb9255b8bba0a2f18d63977f040e63b01a`.
Focused preparation, binding, runner and diagnostic tests passed: 26 tests
and 7 subtests; targeted Ruff and mypy passed. The full exact-source quality
gate then passed **589 tests, 935 subtests, lint and types**. Its source hash
was `70d7340750626909a8250c0ba5a8f060f4c0e2feef4eabed94e4fcce379627a6`
before and after, and its saved log hashes verified. The receipt is
`runs/quality_status.json`.

At 15:54:32 UTC, the project volume had **6.071 GiB** free, below the
unchanged **20 GiB** floor and the prepared script's **22 GiB** pre-subject
minimum. Available RAM was **9.611 GiB**, below the separate **10 GiB**
control-refresh startup guard. These readings are snapshots, not an estimate
of the new cohort's peak storage or RAM. The legacy Cho directory still has
52 NPZ files and 52 manifests; the new versioned directory does not exist.
No real Cho 60 Hz artifact, bounded diagnostic, full-cohort rebuild, control
refresh, source selection, or scientific cell was run in this step.

A final read-only comparison rehashed all 52 historical NPZ files against
the milestone-32 saved cohort hashes: **52/52 match**. All 52 historical
manifests still declare the 50 Hz settings digest. The write-once
`runs/phase2/cho_60hz_preparation_checks/20260923_prepared/receipt.json`
records this comparison, exact-source quality and the 16:07 UTC resource
snapshot: 5.485 GiB free disk and 9.924 GiB available RAM. The disk
admission check still fails. Previous 45/45 controls remain bound to the
earlier source and require a fresh guarded refresh for this working tree.

## Next admission sequence

1. Restore enough disk headroom for the 22 GiB pre-subject check and the
   measured raw, staging, log and artifact peaks, while preserving the 20 GiB
   floor throughout. Recheck RAM for any later control refresh. Do not infer
   an admission merely from crossing a startup threshold.
2. Capture independent seven-input hashes and a fresh resource receipt for
   predeclared subject 01. Run the 60 Hz dry run, then one guarded subject
   preparation only. Preserve the write-once output hashes and legacy inputs.
3. Run the read-only bounded diagnostic with those hashes. Review its
   spectral result and all input identities before planning 52 subjects.
   A diagnostic pass would support only the preprocessing choice.
4. Before scientific execution, finish the full freeze, committed executable
   configurations, complete selector/workload envelope, source-bound quality
   and controls, Gate A and separate MMIDB policy. The existing 256-step
   engineering cap cannot implement the 5,253-step Cho selection.

The versioned configuration and code are currently untracked/modified in the
working tree. No commit or push was performed.
