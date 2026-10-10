# Empty runtime-file fingerprint correction, revision 003

Revision 002 captured the concrete failure: the installed boto3 resources
initializer is a legitimate zero-byte Python module. The shared nonempty
input hasher rejected it during the final runtime fingerprint, after the
synthetic pipeline and comparisons reached completion. That failed probe
is not certified as a passing result and its receipts remain untouched.

This revision permits empty files only when hashing imported runtime files.
Raw data, cache and ordinary operation inputs still require nonempty bounded
regular files. Two added boundaries verify the SHA-256 of empty runtime bytes
and rejection of empty data input. All signal processing, comparison rules,
network/write restrictions, resource floors/caps and original-case limits
remain as specified in README.md. Logging from revision 002 is retained.

One fresh corrected probe is separately admitted; the earlier two probe
admissions remain spent. Real subject001 reconstruction still requires its
own fresh measured-runtime review/admission. No scientific gate is signed.
