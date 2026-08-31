# CSP runtime investigation

The frozen decoder remains six-band, two-component MNE CSP with OAS covariance,
concatenated training epochs, log-power features and balanced logistic regression.
No labels, trial selection, filtering, covariance regularization or classifier
hyperparameters are tuned in this investigation.

## Thread-limit probe

The separate four-BLAS-thread probe exactly reproduced every non-timing metric
for Cho subjects 01 and 02. It did not improve runtime: fits took 423.116 and
447.423 seconds, versus historical 356.949 and 369.696 seconds. Historical machine
loads differ, so this is not a paired speed estimate. The four-thread setting is
not adopted. Evidence: `runs/runtime_probe/20260831T044225073883Z/result.json`.

## Optional full-numerical-rank shortcut

MNE's default `rank=None` estimates numerical rank from data; supplying a rank
dictionary bypasses that computation for the specified channel type. This is not
the same as unconditionally assuming full rank. The local wrapper creates MNE's
single dummy channel type with no projections; other layouts are outside this
shortcut's scope. See [MNE CSP documentation](https://mne.tools/stable/generated/mne.decoding.CSP.html).

For the actual training matrix A, and a deterministic subset B of its columns,
`A Aᵀ − B Bᵀ` is positive semidefinite. Thus the smallest singular value of A is
at least that of B, and the largest singular value of A is at most its Frobenius
norm. A chunked norm scan bounds MNE's full-matrix rank threshold without creating
the several full-size copies otherwise needed by its rank calculation.

The implementation subtracts a conservative small-SVD rounding allowance and
requires the remaining lower bound to exceed 64 times the upper threshold bound.
It considers 2,048 evenly spaced columns and scans 32 trials at a time. An
inconclusive check falls back to MNE's original `rank=None`; it never guesses a
reduced rank or forces full rank. It is enabled only for the reviewed MNE 1.12.1
implementation. A different version also uses the original calculation.

This preserves a **numerical** rank decision, not a physiological statement about
sensor independence. In particular, floating-point storage can lift an otherwise
rank-deficient common-average-referenced array above MNE's numerical tolerance.
No physical-rank correction is silently introduced here.

Tests compare the certificate against MNE over multiple scales, exercise zero,
rank-deficient and unrepresentative subsets, check exact CSP prediction parity,
and verify the unsupported-version fallback. The real two-fold probe requires
exact equality of all original non-timing metrics and records every band's bound.
An unsaved probe is not a successful result. These auxiliary probes record their
actual dirty-source fingerprints and are not retroactively assigned clean commits.

The two-fold rank probe passed with no differences in any original non-timing
metric. At the observed default 24 BLAS threads, fits took 164.272 and 171.887
seconds, versus historical 356.949 and 369.696 seconds. All six bands in both
folds were certified; the smallest bound ratio exceeded 4,481, comfortably above
the required 64. Evidence: `runs/runtime_probe/20260831T050021073247Z/result.json`.
These timings are not guarantees under other machine loads or datasets.

The guarded production switch is now enabled for subsequent workers. Each newly
fitted benchmark record will expose certified-band and
automatic-rank-band counts, plus the minimum certified separation ratio where
applicable. The independent record auditor checks their arithmetic and margin.
Older completed records are left unchanged.
