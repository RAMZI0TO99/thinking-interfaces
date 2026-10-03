# Proposed no-future matched EEGNet diagnostic

**Current-source check, repeated with a write-once receipt at 08:23 UTC on
24 September 2026:** Source
`458be5698b0c0a7a2dd79afc03c907e94fd51ef88fb19b53999cf744d7def727`
has a verified full quality bundle. The [read-only check receipt](../../runs/phase2/gate_a_diagnostics/20260924_no_future_recorder_bridge_hardened_458be569/receipt.json)
and its hash-pinned command log record that `--check-only` recomputed all
nine saved artifacts from the sealed raw inputs and reported context
`172b6bc0cb198efcbc774549e9c699a25d1e3f5b948386dd60d87b34f6705f2c`:
0 valid / 36 missing fit records, no invalid or unexpected record, and no
score. The child exit code 1 denotes incomplete diagnostic evidence; the
wrapper's expected-incomplete verification succeeded. It started no
model fit or Gate A decision. The context auditor reports
`raw_files_verified = false` until all 36 fit records exist; the separate
all-nine writer raw recomputation itself completed. The earlier `713fe95e`
and `0f679414` receipts, contexts and RAM samples below describe previous
sources and times.

Status: **prepared only**. This is a separate engineering diagnostic. Gate A is
unsigned, no scientific cell is admitted, and the historical pre-cue control and
its 45-record source-bound bundle retain their original identities and bytes.
At 21:45-21:53 UTC on 23 September, the exact-source `--check-only` command
recomputed all nine saved NPZ/manifest pairs from raw EEG without error and
then reported context SHA-256
`7425fea3d5261f879b54aa9940cdd412ec6a0598eae54496a247e146c8d98531`,
**0 valid / 36 missing** fit records, no invalid or unexpected record and no
score. Its nonzero exit reflects the incomplete diagnostic. The default
runner deferred before training at 8.544 GiB available RAM against the
unchanged 10 GiB startup guard (disk 28.629 GiB against 20 GiB).

The proposed 36 fits use the nine BCI IV 2a subjects and four seeds
11/23/37/53. The effective gate is derived from the byte-pinned
`configs/pre_cue_control.toml` (SHA-256
`e157a9632d79ad47387f4356e3ecd3dc35637425965adced28c336c269cad28f`).
Only `gate_name`, `attempt`, and `artifact_pattern` change. The new input path is
`data/processed/bci_iv_2a/pre_cue_no_future_v1/subject_{subject:02d}.npz`.
Training, split, checkpoint selection, session/query protocol, four-class
reference, and subject-weighted mean balanced-accuracy ceiling of 0.35 remain
those of the preset.

`evaluation/no_future_matched_control.py` independently checks the nine NPZ
schemas, 576-trial cue rosters, channel and session order, signal bytes,
manifest summaries, and full NPZ/manifest hashes. The manifests must pin the
same posthash all-nine signal audit, its source files, their own writer, and the
18 raw files. The context records the preset, all 18 artifact/manifest hashes,
the posthash audit, exact source fingerprint, wrapper and writer hashes,
environment including NVIDIA identity, the full exact-source quality status
and its verified logs, all 18 sealed raw MAT digests and sizes, and the
raw-recomputation check output hash. A stale or changed quality bundle stops
supervision before launch and stops the worker before importing Torch or a
model. Saved units are additionally tied to the NPZ signal digest and labels;
`evaluation.source_bound_controls.validate_unit` checks each fit's split,
training history, query predictions and metrics, and memory evidence. The
separate auditor requires all 36 records, no invalid or unexpected record,
four scores per subject, and the original 0.35 cohort limit.

The runner first calls the artifact writer with `--subjects 1 2 3 4 5 6 7 8 9
--check-only`; that call rebuilds every window from the pinned local raw EEG and
compares it exactly with the saved NPZ and manifest. A worker cannot start from
the proposed runner until this check and the context checks pass. The run uses
its own `runs/no_future_matched_control/<context-sha256>/` namespace and a
separate exclusive lock. Context and unit JSON files are published without
overwriting previous bytes. The runner rejects preexisting symlink or junction
aliases in its output directory and rechecks the destination and temporary
file immediately before each hard link. This protects ordinary exclusive
directory operation; a separate process with write access could still race
the short path-check-to-link interval. Existing valid units resume; invalid
evidence stops the run for investigation. Each subject’s two raw MAT files are
rehash checked before and after its fits; all 18 are checked again before a
36-record audit can pass.

For a later authorized execution, use
`python -m scripts.run_no_future_matched_control`. Before training it requires
10 GiB available RAM, 20 GiB free disk and CUDA. It checks 4 GiB RAM and the
20 GiB disk floor during execution, applies the project's GPU cooling policy
before each fit, and supervises its own worker with a 120-minute wall limit.
`--check-only` recomputes all nine raw inputs and verifies any saved 36-unit
bundle; it performs no model fit. A resource deferral is not a failed model
result. The runner does not write checkpoints or a Gate A decision record.
