# Cho2017 60 Hz Profile B bounded rebuild and cohort audit

23 September 2026. **Engineering preprocessing evidence only.** The owner's
first exploratory Cho2017 five-shot scope remains the four neural methods
linear probe, LoRA, full tuning and EEGNet; EA-tangent is deferred. This
rebuild does not ratify the scientific freeze or admit any evaluation cell.

## Subject 01 admission and signal check

The [write-once preflight](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/before.json)
independently pinned the raw source, frozen Profile A, historical 50 Hz
artifact and manifest, and the Cho-only 60 Hz config. The raw hash matched
`configs/cho2017.toml`; exact-source quality was current. The start reading
was 28.702 GiB free disk against the writer's 22 GiB pre-subject minimum.
The source configuration and historical files were left intact.

The writer created only `subject_01.npz` and its manifest under
`data/processed/cho2017/profile_b_60hz_v1/`. Its output was independently
rehash-pinned in [pins.json](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/pins.json).
The [predeclared, read-only diagnostic](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/diagnostic.json)
verified all 200 Profile A/50 Hz/60 Hz trial identities and labels, finite
64-channel, 800-sample Profile B epochs, the 200 Hz rate, config and raw
hashes. The 60 Hz line-to-sideband ratio fell from **6.8815** in the
historical artifact to **0.00590** in the versioned artifact, a **30.67 dB**
attenuation against the fixed 6 dB engineering diagnostic. The 50 Hz ratio
rose from 0.00869 to 0.94547, consistent with replacing the old 50 Hz
notch. This subject-level comparison supports the applied notch; it does
not measure model accuracy or prove an effect for all subjects.

The real [five-shot binding receipt](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/binding_receipt.json)
records a versioned `cho-a-to-b-episode-60hz-v1` binding with 10 support,
160 query and 200 original trials. No prediction or fitting occurred.

## Complete engineering cohort

All 52 raw Cho files were present before expansion. The 51 remaining
historical artifacts totaled 1.813 GiB and supplied a planning proxy,
not an upper bound. At 27.058 GiB free, the [cohort admission](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_admission.json)
required the 20 GiB floor plus this proxy and a separate 4 GiB margin.
Each subject ran in a separate process with a 22 GiB writer startup check,
active disk/RAM monitoring, a 10-minute timeout, and independent artifact,
manifest and raw hash checks. Per-subject logs and write-once receipts are
under `runs/phase2/cho_60hz_subject01_checks/20260923_bounded/`. Subjects
02-52 all completed. No historical destination was overwritten.

The final [independent cohort audit](../../runs/phase2/cho_60hz_subject01_checks/20260923_bounded/cohort_audit.json)
passed:

| Check | Result |
| --- | ---: |
| Versioned NPZ/manifest pairs, with no extra files | 52/52 |
| Historical 50 Hz NPZ hashes versus saved milestone-32 receipt | 52/52 match |
| Raw-source hashes and 60 Hz config/manifest binding | 52/52 |
| Profile A to versioned Profile B original trial/label joins | 52/52 |
| Real five-shot versioned episode bindings | 52/52 |
| Original trials across subjects | 10,520 |
| Profile A rejected trials | 11 |
| Five-shot query trials per subject | 154-200 |
| New artifact bytes | 1.848 GiB |

The audit measured 24.799 GiB free disk; a later 17:10 UTC snapshot had
24.533 GiB. The disk floor stayed intact. The later RAM reading was
7.98 GiB available, below the separate 10 GiB startup guard for the
45-fit current-source control refresh. No project Python worker remained
running at that inspection.

The exact-source quality receipt still verifies the unchanged source hash
`70d7340750626909a8250c0ba5a8f060f4c0e2feef4eabed94e4fcce379627a6`:
589 tests, 935 subtests, lint and types. The historical 45/45 controls
belong to the previous source snapshot and are **stale** after the 60 Hz
config/code/test changes; they have not been rerun. No commit or push was
performed, and the executable Phase II configs remain untracked.

## Next boundary

The 60 Hz **input cohort is ready for engineering review**. Subject 01 is
the only predeclared spectral diagnostic; the complete-cohort audit verifies
contracts and identities, not a separately thresholded spectrum for every
subject. No scientific cells are admitted. A current-source control refresh
must pass its unchanged RAM and active guards. The full scientific freeze,
committed executable configurations, complete selector and resource
envelope, Gate A, and MMIDB cohort policy remain separate prerequisites.
The two-candidate Cho LaBraM/EEGNet selection still needs 5,253 gradient
steps, above the unchanged 256-step engineering ceiling.

The next control preflight is
`.\.venv\Scripts\python.exe -B -m scripts.refresh_source_bound_controls --check-only`.
It checks the current source/environment context without running fits.
When the 10 GiB startup RAM guard and separate 20 GiB project disk floor
both pass, use the fresh bounded wrapper for the current 589-test quality
bundle; the historical milestone-51 wrapper is specific to its earlier
source and receipt format. Existing control records remain immutable.

A [new guarded wrapper](../../runs/phase2/control_refresh_checks/20260923_cho60hz_source/README.md)
is now prepared for this exact source. Its read-only `--preflight` at
17:24:25 UTC found 21.214 GiB free disk and 4.984 GiB available RAM,
so it deferred before creating receipts or starting fits. The guard must
pass on a fresh check before the wrapper can run the established controls.
