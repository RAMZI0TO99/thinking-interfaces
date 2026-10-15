# Complete synthetic EEGNet selection and actual publication

This candidate executes one complete engineering EEGNet case, outer subject02,
seed11,shot5. Fresh physical synthetic inputs retain52 subjects,64 channels,
Profile A512 samples and the unchanged1/5/10/20 shot protocol. The frozen
fixture helper also writes Profile B files and synthetic raw-marker provenance;
these are physical fixture inputs, not study recordings or pretrained weights.
Its diagnostic creation metadata remains distinct from this complete execution:
all51 non-target subjects, including subject01, participate as permitted source
subjects across the full inner selection and the final winning fit.

Before execution, the parent independently pins `method-config.json` copied
from the exact EEGNet row in the adopted12October design decision. Its candidates
are `lr_1e-3` and `lr_2e-3`, rates0.001/0.002, source one step/subject with batch4
and input_scale1,000,000, support one step with the same scale and querybatch8.
`materialize_cho_candidates` constructs the real typed candidates. The actual
selector contract must derive exactly the independently pinned configuration.

`run_selection(request, *, set_protected_inputs)` invokes the real public
`BCIEEGNetSourceSelector.run_selection` with the unchanged5,253-step maximum.
Both candidates run all51 leave-one-source-out folds, each with50 actual source
updates and one actual support update. The actual rational winner receives a
fresh51-subject source fit:5,151 source plus102 support updates,5,253 total.
Official SGD pre/post hooks observe finite float32 CPU gradients/parameters,
the exact2,642-parameter mask and changed selected parameter bytes on every
update. The observation roles/order must match every actual public history.
`optimizer-observations.json` stores metadata and digests, never parameter bytes.

The real public complete-evidence verifier must pass. A real `AnchorAdapter`
and metadata-only `sweep_cell_identity` then feed `publish_verified_cho_source`.
The unchanged store writes canonical evidence, a full_v1 safetensors state and
an engineering manifest in the fixture's exact `runs/phase2` publication paths.
The public publication gate verifies its physical-file witness. No target case
executor, recorder API, target prediction, study cell or original attempt runs
in this child. `source-result.json` binds the request, actual winner/histories,
method/input pins, publication paths, logical and physical hashes and identities.

`verify_publication(request, source_result, *,
expected_source_result_file_sha256, set_protected_inputs)` runs in a different
fresh native child. The parent supplies the source-result file digest obtained
from the newly accepted source Job. The verifier requires those exact canonical
bytes and independently derives the EEGNet recipe. It invokes the actual public
tensor checker with its genuine6/4GiB host-RAM floors, then the public full source
restore factory and complete-selector verifier. Each public restore verifies
every full-state tensor's schema and finite bytes, strictly loads the complete
state and checks its byte digest against the external source pin. The candidate
also checks the entire restored schema and finite state. No separate decoder
runs outside those public restore gates. It
returns `detached-result.json` and a real released source adapter witness, with
zero gradients and no target inference or new publication. EEGNet requires no
external pretrained baseline. Fixture source provenance is separate from the
independently pinned execution code.

Both functions receive a callback `(four_outer_subject_paths, enabled: bool)`.
All subject02 A/B/manifest/raw-marker reads are denied during selection/public
verification/publication or detached restoration. Initial catalog reconstruction
and full before/after input hashing occur outside that protected compute phase.
The caller owns read-denial implementation and independent actual backward/SGD
counts. Source/output writes are limited to its own output and the exact fixture
publication namespaces; detached execution writes only its own output.

The planned parent is600s/4–6GiB, holding the real case lock across a separate
420s/3–4GiB selection child and90s/2–3GiB detached verifier. Native admission,
10/4GiB shared RAM floors,20GiB disk,Torch1/1, hidden GPUs and genuine pause paths
remain independent requirements. Source review or an old receipt authorizes no
launch. Completion qualifies this one synthetic EEGNet selector/publication and
engineering terminal only; other methods, complete study work, scientific
admission and original-case attempts remain unqualified, with original0.
