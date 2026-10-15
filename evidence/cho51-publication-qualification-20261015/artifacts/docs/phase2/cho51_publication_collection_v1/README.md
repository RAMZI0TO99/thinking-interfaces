# Adopted-51 publication file collection candidate

This separately versioned read-only stage composes the qualified 51-target
input/selection collector with the existing selected-manifest **file-byte**
verifier. It preserves all 52 available source subjects, subjects 02–52 as
evaluation targets, the four canonical methods, seeds 11/23/37/53/71, five
shots per class, and all 1,020 unchanged case identities.

`collect_cho51_publication_files` requires an existing recorder, independently
supplied `PinnedCaseCell` and `ChoSelectedSourcePin` sequences, independent
source/configuration pins, and the pinned 5,253-step selection ceiling. It
snapshots mutable containers once and rejects incomplete, duplicate, untyped,
out-of-roster or digest-invalid metadata before input/data or manifest reads.
Each publication environment is bound to its cell; each manifest receives the
same pinned selection contract, candidate, protocol, source, recipe and
checkpoint state digest.

The input collector freshly verifies actual source inputs. The publication
stage then obtains another physical selection witness and requires exact
equality with the preceding stage's immutable claims. Ledger rereads bracket
the publication loop. Selection witnesses and all manifest/evidence/weight
identities are checked again around the final ledger reread. These bounded
checks detect interval drift without providing a filesystem lock.

The immutable result includes per-case manifest, evidence, contract, candidate,
protocol, method, environment, recipe, checkpoint-state and weights-file
digests. Only `selected_publication_file_bytes_verified` is true. The broader
publication, tensor, complete-selector, combined publication/tensor and
scientific-admission properties remain false.

The unchanged byte helper currently accepts `full_v1` and
`sparse_frozen_init_v2` weight declarations, with canonical or factored
selection evidence. File-byte acceptance of either format does not establish
decoded tensor identity, model reconstruction, fitted-state history, complete
fold evidence or numerical selector correctness. The existing tensor-state
restore path's `full_v1` restriction remains a separate future boundary.

The candidate never constructs a recorder or model, creates a case attempt,
executes a tensor child, fits a selector, predicts targets, performs paired
aggregation, changes canonical code or grants scientific execution authority.
The original subject01 case remains exhausted with zero attempts remaining.

`test_collection.py` contains **65 prepared checks**, comprising 63
dependency-mocked boundary cases and two hybrid cases with
fabricated metadata. Its exact typed route, case pins, publication pins,
selection witnesses and manifest witnesses preserve type validation while
stage I/O is replaced in the candidate's namespace. Witness class methods are
temporarily patched for boundary tests and restored by pytest. The two hybrid
cases delegate one publication to the actual canonical byte verifier and its
actual stability method, using a tiny fabricated blob; the other 1,019
publication calls and all input/selection/ledger I/O remain mocked. One hybrid
case accepts that byte binding and the other refuses post-verification weights
drift. No synthetic blob is decoded as a tensor. The checks cover complete
binding, immutable snapshots, roster/digest/claim mismatches, ledger drift,
wrong publication witnesses and ordered refusal after collaborator failures.
These tests have **not been executed** as part of authoring this candidate;
they establish no current runtime or real publication-file qualification.
