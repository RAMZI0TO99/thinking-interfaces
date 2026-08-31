# Tangent-space process scheduling: diagnostic only

The production benchmark still uses its original calculation. This investigation
does not change the frozen benchmark configuration, BLAS thread counts, inputs,
classifier settings, completed records, or scientific gates.

## Candidate and limits

`evaluation/process_eigh_probe.py` schedules independent float64 64-by-64 NumPy
eigendecompositions in two spawned processes, with 64 matrices per block and at
most two pending blocks. Each worker verifies the exact NumPy/backend identity
and the original 24-thread setting before calling unmodified `numpy.linalg.eigh`.
The parent patches only the separate Array API facade and restores it on exit.
Unsupported shapes, types, layouts, and keyword arguments use the original path.
Startup requires 10 GiB available memory; the existing 4 GiB stop is retained.

An earlier same-process threaded experiment exited with a native access violation
(-1073741819) after its serial stage. That approach is rejected. No benchmark
record came from it. Small isolated-process synthetic and single-subject feature
checks subsequently produced bit-identical eigenpairs/reference/features, but
those exploratory console observations are not standalone persisted evidence or
full-fold qualification.

## Persisted normal-tangent qualification

The real two-fold qualification used clean commit
`573f62a61f00f4eef2c94598e62cc5a1bac09ed0`, source fingerprint
`30bcb739374a6b3bbc690e6bed3897130e2eddeb6e93e26c517c2fc838f74a95`,
and `configs/tangent_process_probe.toml`. It fitted the full original LOSO
training set and predicted the original query set for each held-out subject.

Receipt: `runs/runtime_probe/20260831T134537682348Z/result.json`.
SHA-256: `d17d00a079f5594aa6b5b255c47cf1df0c00623c893f9e712157fc68e4b647a6`.

| Cho subject, seed 11 | Every non-timing metric exactly equal | Candidate fit seconds | Historical fit seconds | Minimum observed free GiB |
|---|---|---:|---:|---:|
| 01 | Yes | 205.433141 | 296.254049 | 6.240284 |
| 02 | Yes | 213.029099 | 281.558283 | 6.060707 |

Each fold used 12 parallel calls, 32 fallback calls, 1,785 blocks and at most two
pending blocks. The receipt contains reference record hashes, backend identities,
worker PIDs, full original/candidate metrics and an empty differences mapping.
The source fingerprint did not change during qualification. Historical timings
come from different machine loads and are not a controlled speed estimate.

## Preserved benchmark and deferred adoption

The main queue was paused at a saved boundary after Cho EA+tangent subject 21,
at 2026-08-31 13:44:35 UTC. The preceding 2,113 records were unchanged and the
paused snapshot contained 2,114 records:
`runs/runtime_probe/paused_process_probe_integrity_20260831T1344.json`.
All 2,114 files were independently rehashed unchanged after qualification.

After both normal-tangent folds passed, available memory was 9.37899 GiB, below
the unchanged 10 GiB qualification startup threshold. No alignment-enabled
qualification was started. The original main queue resumed at 13:57:43 UTC,
with logs `runs/compute_logs/20260831T1357434822202Z.stdout.log` and the matching
stderr log. Its resumed worker uses the source fingerprint above, not an
experimental production switch.

Exact agreement on two normal-tangent folds does not establish agreement on
alignment-enabled folds, every subject, another dataset, or another numerical
backend. The candidate remains disabled in production. Alignment-specific
qualification, if pursued when resource limits permit, must be separate and must
not overwrite benchmark records. No high-score flag or scientific gate is cleared
by this runtime investigation.
