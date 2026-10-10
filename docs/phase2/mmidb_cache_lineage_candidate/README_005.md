# Reconstruction receipt scalar correction, revision 005

The first real subject001 reconstruction reported exact signal and identity
equality in its partial output, then failed while JSON encoded raw.n_times,
a NumPy int64. The failed native/guard receipts and partial output remain
untouched and are not accepted as a successful validation.

The sole implementation correction is int(raw.n_times) in receipt metadata.
The frozen pipeline, input hashes, comparison, tolerances, twelve qualified
probe checks, write/network restrictions and all limits stay unchanged. A
fresh finite admission binds the existing measured scientific runtime and
unchanged canonical Source, plus this separately compiled worker revision.
The initial reconstruction admission remains spent; one fresh revision
attempt is defined. No original model case is reset or retried.
