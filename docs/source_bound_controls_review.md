# Current-source Phase I leakage controls

The 2026-08-31 refresh preserves the existing complete protocols: nine BCI
subjects with seed 11 for development-label shuffling, and nine subjects with
seeds 11/23/37/53 for one-second pre-cue classification. Training, validation,
best-checkpoint selection and early-stopping settings are unchanged. Cohort mean
balanced-accuracy ceilings remain 0.60 and 0.35 respectively; these are not new
post-result thresholds or Gate A acceptance bands.

The runner captures the actual original held-out prediction call without
re-executing or changing its model output. Its verifier independently reconstructs
train/validation/test identities and shuffled targets, checks histories and
resource observations, and recomputes confusion counts, balanced accuracy and
kappa. All 45 fits must be valid. Missing units, stale source/input/environment,
changed context, unexpected records and forged saved pass flags cannot pass.

The source-wide cache deliberately invalidates on any tracked implementation,
test or configuration change. Documentation changes alone do not invalidate it.
Fits made before the checked commit honestly record the previous commit plus
`git_dirty=true` and the exact staged-source fingerprint. Committing that same
source does not retrospectively relabel the fit as a clean-commit execution.

Local commit/merge hooks and the Phase I status checker use the current verified
bundle. Historical records and summaries are retained separately and are never
assigned new provenance. These BCI controls do not establish chance performance
for every benchmark method/dataset, remove existing plausibility flags, establish
MOABB reproduction, or resolve the fixed-earliest support protocol question.

## Initial verified refresh (preserved, superseded by the correction below)

The focused suite covers the full 45-unit grid, reconstructed split/shuffle,
prediction/metric tampering, first early-stopping boundary, metadata, memory
guards, source/input/environment invalidation, complete-bundle reuse and
fail-closed merge checks. Full project quality passed with 269 tests and 328
subtests at source `26f2db269fba969fd04f1060eec764f9b455a1944f7823cd5a43d8bf1b1b94e2`.
Quality receipt: `runs/quality/20260831T152408758477Z/`.

The first real-data refresh used context
`efe99c1d0baa21d4a1a69ef914114673ed7b215a1b8f3293915e2724906ae300`.
All 45 real-data records passed, with no missing, invalid or unexpected records.
Snapshot SHA-256:
`67e67194c8e17f51324aa01f31122b41430de4e67edf452c20c5a76187c77666`.

| Configured control | Fits | Subject-weighted mean balanced accuracy | Existing limit |
|---|---:|---:|---:|
| Development-label shuffle | 9 | 0.4876543209876543 | 0.60 |
| One-second pre-cue | 36 | 0.24855324074074076 | 0.35 |

The full original epoch/patience rules completed 1,166 epochs. Recorded training
and prediction time summed to 72.323 seconds; this excludes preprocessing,
cooling, input hashing and audit time. Minimum observed free RAM was 8.502 GiB;
maximum observed control-process resident memory was 1.680 GiB. The context plus
45 records occupy 1,951,439 bytes, excluding the separate input-audit receipt.

Independent reconstruction reloaded all nine raw two-class subject inputs and
all nine pre-cue artifacts and matched the exact signal bytes, shapes, labels,
sessions and query targets of every one of the 45 records. No model was trained
in that audit. Receipt:
`runs/source_bound_controls/input_audits/20260831T152949722097Z.json`, SHA-256
`bd08d6977ffe05cd359a56ffee5dd4a84b7a79510f06413f9faa2688ff5c2fcb`.
All 2,184 snapshotted benchmark/historical-control files remained byte-identical.
Module-mode leakage CI passed all checks. The subsequent checked commit
correctly failed because direct-script discovery listed the editable local
package once whereas module-mode discovery listed the identical name/version
twice. Source, inputs and installed numerical packages had not changed. The
hook was not bypassed and that attempted commit did not succeed.

## Corrected environment identity and full rerun

The verifier now removes duplicate identical package-name/version discoveries;
different versions remain distinct. A regression test covers both cases, and
actual module/direct-script contexts were compared and matched. This is a
metadata canonicalization correction, not removal of package/version binding.

The changed source is
`287a576e1739a20c130a633b93fc94c46bf12438c5dc45722f3318e220d1e89c`,
with control context
`7f39353ab987d42b8cac5aa41c118ad40d0a05da9fecf2fc0f6ef75eee3094a3`.
All 45 fits were rerun and passed under that source, with the same cohort means
shown above. Snapshot:
`ee3e2bc56746ffa03776a102605cefd467a6e5827c15d75b3845656fdb922a62`.
All histories, numerical result reports and query predictions exactly matched
the first refresh. Recorded fit/prediction time summed to 70.183 seconds across
1,166 epochs; minimum observed free RAM was 9.059 GiB and maximum process resident
memory was 1.680 GiB. Timing excludes preprocessing/cooling/auditing.

A new hash-linked audit checked every rerun's actual input identity, labels,
sessions and query targets against the pinned independent reconstruction above.
It rehashed the previous records and confirmed all underlying input/configuration
hashes were unchanged; it did not claim a second raw preprocessing execution.
Receipt: `runs/source_bound_controls/input_audits/20260831T153803007522Z.json`,
SHA-256 `6b67f9dd31b9fcc414f3fd8c47f2d9a6532c7180ad3f28fe5f418bbc5acffa9e`.
The direct-script CI invocation used by the hook now passes all checks. The
initial bundle and its source metadata remain untouched, not retroactively
assigned to the corrected verifier.

## Benchmark interruption preserved separately

The preceding benchmark process exited at 15:20:03 UTC after saving Cho EA tangent
subject 39. Its stderr reports `Bad file descriptor` from libzmq `epoll.cpp:100`,
followed by exit 1073741845. The underlying cause is unresolved; this is not
evidence that a numerical accuracy result failed. All project processes had
ended before the control refresh, so no unrelated process was terminated.

Independent audit found 2,132 valid benchmark records, none invalid; all 2,118
files from the previous paused snapshot were also independently rehashed and
unchanged. Subject 39 SHA-256:
`82cc8140016ac10ffacd55255b698242e395f10f0f6f1c2db580e701a49bfd39`.
The main benchmark remains incomplete and is to resume from these preserved
records after the control refresh. No reference grid, frozen thresholds, epochs
or benchmark scientific settings were changed to recover execution.
