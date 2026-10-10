# Evaluation identity inventory candidate

This separately owned, standard-library candidate reads only `sessions.npy`,
`runs.npy` and `trial_indices.npy` from the fixed Profile A catalogs. It hashes
compressed containers without decoding signals, labels or channels. It accepts
a bounded subset of the [official NPY format](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html):
one-dimensional Unicode identifiers and signed integer trial indices. Object
arrays, executable header expressions and unexpected archive members reject.

The candidate compares local sidecar declarations and the previously executed
Cho raw-hash audit. Raw EEG files are not opened or freshly rehashed. BCI paths
are declarations; MMIDB sidecars provide no raw-file mapping. Stored project
identifiers are not authenticated publisher recording identifiers. All 109
MMIDB artifacts are inventoried without deciding scientific eligibility.

Synthetic tests and an actual bounded metadata inventory require a fresh,
pinned guarded attempt. Preparation alone is not executed validation. The new
documentation namespace is outside the existing canonical Source fingerprint
and is not certified by older full-quality receipts. No checkpoint cohort,
overlap decision, scientific signature, query freeze, model work or original
case attempt is supplied by this candidate.
