# Cho2017 Profile B 60 Hz rebuild plan

23 September 2026. **Preparation only.** The owner chose a four-method first Cho tranche and asked to prepare a 60 Hz Profile B rebuild. No config, code, artifact, scientific cell, or resource guard has been changed by this plan. The full scientific freeze remains unratified.

**Later implementation update:** The proposed Cho-only config, versioned
writer and binder now exist, along with a bounded read-only diagnostic. This
paragraph preserves the plan's original pre-implementation snapshot; consult
the [preparation review](cho_60hz_preparation_review_20260923.md) for the
file paths, tests and resource stop at that checkpoint. No real 60 Hz output
existed at that checkpoint.

**Later real-cohort update, 23 September 2026:** Restored disk headroom
allowed the guarded subject-01 preparation, predeclared spectral diagnostic,
and subsequent 52/52 versioned cohort build. Subject 01 showed 30.67 dB
60 Hz line-to-sideband attenuation against the 6 dB engineering threshold.
The full audit passed all Profile A-to-B joins and real five-shot bindings;
all 52 historical 50 Hz NPZ hashes still match the saved cohort receipt.
The preceding paragraphs and starting-point table record their earlier
snapshots. See the [real-cohort review](cho_60hz_real_cohort_review_20260923.md)
for current evidence and remaining gates. No scientific cell, source-bound
control refresh, or freeze ratification followed from this rebuild.

## Verified starting point

| Item | Current state |
| --- | --- |
| Dataset line frequency | `configs/cho2017.toml` declares 60 Hz. |
| Profile B notch | Shared `configs/base.toml` declares 50 Hz; `scripts/preprocess_profile_b_cho2017.py` reads it unchanged. |
| Existing Cho output | `data/processed/cho2017/profile_b/` contains 52 NPZ artifacts and 52 manifests, totaling 1.848 GiB. These are the 50 Hz historical inputs. |
| Writer | `save_epoch_artifact()` and `write_manifest()` atomically replace an existing destination; the current Cho script has a fixed output directory. It must not be aimed at historical paths for the rebuild. |
| Binding | `load_cho_profile_b_episode()` pins the 50 Hz `_PROFILE_B` contract and fixed historical directory. Cho LaBraM callers use that loader. |
| Local resource snapshot | 8.289 GiB free disk after the documentation update, below the unchanged 20 GiB floor. The new cohort size and peak temporary space have not been measured. |

The existing cohort's 1.848 GiB is a rough size reference, not an upper bound for the new version. Even if the new artifacts were the same size, restoring the 20 GiB floor *after* writing them would require at least 13.56 GiB more free space than the snapshot, before temporary files, logs, controls, and safety margin. A fresh admission measurement must replace this arithmetic before any preprocessing.

## Version boundary

1. Preserve `configs/base.toml`, the 50 Hz Cho artifacts/manifests, frozen Profile A artifacts, and historical receipts. The shared base profile is also used by BCI and MMIDB.
2. Prepare a Cho-specific versioned config, proposed path `configs/phase2/cho_profile_b_60hz.toml`, declaring the complete Profile B settings, `notch_hz = 60.0`, dataset identity, and a versioned output namespace such as `data/processed/cho2017/profile_b_60hz_v1/`. These paths are proposals, not files or committed configurations yet.
3. Change the Cho preprocessing entry point to accept only the declared variant and to refuse any destination under the historical `profile_b/` directory. Each new subject pair must be published without clobber; a resume may reuse it only after both artifact and manifest verify against the variant config and input identities. Preserve incomplete attempts for diagnosis.
4. Add an explicit 60 Hz Cho binding version. It must read only the new namespace, verify the variant config digest and artifact/manifest hashes, and retain the existing Profile A episode, trial identity, class, montage, and support/query checks. Keep the 50 Hz binding available for historical engineering evidence; new-tranche asset manifests must reject a mix of 50 and 60 Hz subjects.

## Implementation and audit gates

| Gate | Files likely involved | Acceptance evidence |
| --- | --- | --- |
| Versioned preparation | `configs/phase2/cho_profile_b_60hz.toml`, `scripts/preprocess_profile_b_cho2017.py`, `data/profile_b.py` or a new Cho-only entry point | A dry-run shows only the versioned destination; old-path and existing-file writes refuse; source/raw hashes, config, subject and output identities are logged. |
| Binding and asset inventory | `evaluation/phase2_profile_binding.py`, `adaptation/labram_manifest.py`, `adaptation/labram_source.py`, Cho LaBraM caller adapters, relevant tests | 60 Hz version binds only correctly pinned artifacts; wrong variant, config digest, manifest, label, trial ID or subject fails closed. Existing 50 Hz and BCI/MMIDB tests still pass. |
| Bounded signal check | Newly versioned outputs for a predeclared small Cho subset, with write-once audit records | Confirm the actual applied notch is 60 Hz using a predeclared spectral diagnostic; compare line-noise behavior without using model accuracy to choose preprocessing. Check finite `(trials, 64, 800)` signals, 200 Hz sample rate, units, sessions/runs/indices and exact A/B trial joins. Preserve every input/output hash. |
| Complete cohort | 52 newly versioned subject pairs and a cohort audit | Verify 52/52 artifact and manifest hashes, all trial joins and input contracts; no missing, unexpected or mixed-version subjects; historical 50 Hz hashes unchanged. |
| Source and scientific admission | Exact-source quality and controls, executable committed configs, complete selector/resource envelope | Full lint/types/tests and source-bound controls must match changed source/environment when guards pass. Scientific execution still needs full freeze ratification and complete-work admission; the 256-step engineering cap cannot be bypassed. |

The current disk reading fails the 20 GiB floor, and the separate control-refresh startup RAM guard was also below its 10 GiB requirement at the 23 September snapshot. No bounded generation, full-cohort rebuild, control refresh, or scientific selection is admitted by this document. The selected first Cho tranche remains 1,040 planned cells with a 1,893.4-hour CPU no-reuse planning proxy; neither number is an approved compute budget.
