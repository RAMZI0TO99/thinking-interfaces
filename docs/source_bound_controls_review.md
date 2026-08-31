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

## Full refresh after adding independent profile alignment

The new alignment audit and tests changed the source fingerprint to
`3a004d326f567c021b2a3a475d2bc5dfc50683007527ebc20aec9912c3d6c1fc`.
All 45 controls were consequently rerun, not relabeled from earlier records.
Context: `02639784f82afe61505186aa45c3a079fcfc7051c40a355615bf865612825d21`.
Snapshot: `0eb6d0ff8523fb0a13abb497ae83961f7a53c1dd0eeba9dc842c4badd994e935`.
Every record passed, with no missing, invalid or unexpected units. All numerical
results, histories and predictions exactly matched the initial refresh. The
unchanged means remain 48.7654% shuffled-label and 24.8553% pre-cue.

The 1,166 completed epochs took 58.067 seconds of recorded fit/prediction time,
excluding preprocessing, cooling and auditing. Minimum free memory was 9.502 GiB;
maximum process resident memory was 1.680 GiB. The independently reconstructed
unchanged inputs were hash-linked again for all 45 new records:
`runs/source_bound_controls/input_audits/20260831T161659383311Z.json`, SHA-256
`88c4a656335d81523a811856bf064e841bed65505621363611a34df7bc1d4efa`.
This was a fresh verification against the pinned raw reconstruction, not another
claimed raw preprocessing execution. Earlier bundles remain preserved.

## Full refresh for the predeclared ordered bridge

Before observing intermediate bridge scores, source
`84d859ea25235c6a17dcc193efef6a7e0e52f2b97dd6fae17925c9775fa34550`
completed all 45 controls under context
`f8672cbace3cc7bc1a652070c06c69d8fbeb8837a9500f3fbba1f15431e4e9cc`.
Snapshot: `cb784deae33ae50bec4a84c7408be34aa0913aaf80b3a6414185a7d183483123`.
All checks passed and all results, histories and predictions exactly matched the
initial refresh. The 1,166 epochs took 64.352 seconds of fit/prediction time;
minimum free RAM was 8.323 GiB and maximum process memory 1.681 GiB.
Hash-linked independent input verification covered all 45 records again:
`runs/source_bound_controls/input_audits/20260831T163313704362Z.json`, SHA-256
`aeb518b754bdf9f1a6f0c18ff57cf3e1f692dc365aa55471f7cc4ec3279a1d06`.
The preserved raw reconstruction was reused by hash, not rerun or relabeled.

The bridge's pre-fit cooling-path correction required a further complete refresh
at source `0aec5f63da937ebea3fc0806e9fa976a8ceabc019708818faefd1d8481463341`.
All 45 fits passed under context
`4b32ad6730b52bb6e1cd9fd58042a88b0949b75d404421af27d0efd56247bd8d`,
snapshot `99f01a8e31040969dbb3918c86d8437c70c5aaa41d25c8fbd34d4b98e2a9bf51`.
Every result/history/prediction again matched the initial refresh. Across 1,166
epochs, recorded fit/prediction time was 71.231 seconds, minimum free RAM 8.651 GiB
and maximum process memory 1.682 GiB. Hash-linked input receipt:
`runs/source_bound_controls/input_audits/20260831T163848306240Z.json`, SHA-256
`b7a609bd97d52a863ea05429d3bd20cfdad50473492e689f96cbd66ca621d3b6`.

The subsequent exact-JSON endpoint reporting fix was verified with another full
45-fit refresh, source
`c8af5d97c0965f0933621a53389a3a558e593e78a0ca42d7ae48ee4832a48679`,
context `4bdc1385ab9445529e3d8dd72764f58bcbb22162aee4610ae72e5a716eac279c`,
snapshot `8260e403754ba4d5d55be805ee0d9c8198323d8934dbd7debc31b97c12e7e4a6`.
All results, histories and predictions again matched the initial refresh exactly.
Recorded fit/prediction time was 68.917 seconds over 1,166 epochs, minimum free
RAM 8.595 GiB, maximum process memory 1.681 GiB. All 45 inputs were hash-linked
to the pinned independent reconstruction:
`runs/source_bound_controls/input_audits/20260831T164551199457Z.json`, SHA-256
`c20671d22375d47fed25659c1c9797a46139779b0b30f754cf60df1b9cc2543b`.

## Full refresh for bounded shared compute scheduling

The bounded benchmark/reference supervisor and its regression tests changed the
source fingerprint to
`b35ac4a10503748ec44243f1c3cfaced415a761c5e8c5ea6a1a8ef7a53a44446`.
All 45 controls were rerun under context
`c961ef68b30c9d18f0ec5ba2c41d0248c33accfb00f62dc2ba6dd9e8943284dc`,
snapshot `4de9db1b1580b1256e38099fb5f1c6f73195d8a4382f2fef8bc42d50adebc339`.
No units were missing or invalid. Every result, history, prediction, input/split
identity and training/query target exactly matched the initial refresh. Means
remain 48.7654% shuffled-label and 24.8553% pre-cue under unchanged limits.

The 1,166 epochs took 56.275 seconds of recorded fit/prediction time; minimum free
RAM was 8.938 GiB and maximum process memory 1.681 GiB. All 45 new records were
hash-linked to the pinned independently reconstructed inputs, without claiming
another preprocessing execution:
`runs/source_bound_controls/input_audits/20260831T173206998783Z.json`, SHA-256
`69f6e692ac4323cfcda9466b183891ea214f2905e1dfe2b8205e65152cf0ee9a`.
The separate 20-record bounded MMIDB recovery also preserved all 2,390 earlier
records; its 2,410-record snapshot was
`3c026dd9cb15bb8de3de2620932a19e04a92f66282008ccbcd68b6083f1dc861`.
