# Provenance-aware selected-source restoration v1

This separate engineering API restores the accepted linear `full_v1` selected
source while preserving historical producer and current executor identities.
It does not qualify LoRA/EEGNet/full-tuning restoration, the unchanged canonical
single-root factories, scientific cells, cohort lineage or the final freeze.

`HistoricalProducer` binds an independently admitted accepted publication, exact
manifest/evidence bytes and logical digests, complete selection contract, recipe,
weight bytes and final tensor state. `ExecutorContext` binds actual current Git,
the canonical source fingerprint, candidate/operations sources, interpreter and
dependency versions, and effective Python binary bytes. Immutable canonical JSON
strings avoid mutable nested contract fields. Historical Python metadata remains
historical; current binary/version pins independently bind the current executor.

`RestoreRequest` binds both roles, adopted case, direct historical store, separate
workspace, current durable request, fresh claim and independent pins. Admitted
pins must contain exact `factory_producer` and `factory_executor` snapshots. A
caller cannot substitute an ancestor or executor by rewriting its request alone.
The native guard independently authenticates the pins before importing sources;
the factory is not an alternate native admission mechanism.

Construct `ProvenanceRestoreFactory(request, request_path,
request_file_sha256, locked_case._require_active)`. The final argument must be
the actual canonical bound method; no-op callbacks and foreign recorder cases
are rejected. Admitted `factory_claim` pins bind recorder root/output, its fresh
current source, worker and attempt 1 separately from the executor root. The
physical canonical claim is checked against that live recorder and environment.
The durable request is exactly compact
canonical UTF-8 `request.payload()` without a newline, so `request.sha256` is its
physical digest. `authenticate()` only authenticates bounded bytes and current
bindings; it does not assert complete selector validity or decode weights.
`restore(method_config=..., protocol_config=..., catalogs=...,
selection_record=..., assets=...)` revalidates complete historical metadata,
derives the canonical recipe/settings, reconstructs authentic baseline lineage,
decodes selected safetensors safely, checks all tensor names/shapes/dtypes/finite
values and raw state digest, and performs a genuine strict state load before
delivering the concrete canonical `LaBraMTunedAdapter`.

`selection.py` is an explicitly versioned adaptation of the canonical complete
metadata verifier. It receives the authenticated producer source as a named
argument rather than recapturing it from the current root. Canonical leaf checks
remain shared, including input identities, all folds, exact rational scores,
candidate order, winner, final fit and required total gradient-step calculation.
The current project root supplies the local hard ceiling only. No Git identity
is spoofed, no canonical provenance capture is patched and no evidence is edited.

Every reader uses stable direct single-link regular files and compares descriptor
and path identity, size, mtime, ctime and digest before returning. Windows path
and descriptor ctimes are stable independently; their common four identity
fields must match across the two APIs. Runtime hashing alone retains the exact
admitted two-link Git-binary exception; all store files remain single-link.
Weights always
have the explicit 64 MiB limit, ordinary metadata 8 MiB, and complete evidence
32 MiB. Runtime binary hashing is streamed within an explicit 2 GiB bound. Full
source/runtime/request/claim/pins checks occur before model allocation, before
selected loading and before adapter delivery. Restore writes and fsyncs a
write-once `restore-attempt.json` before numerical work. A new factory instance
cannot replay the same consumed request, and failed or terminal recorder cases
are rejected. Native recovery must preserve failed/incomplete counters and
never replay the backend.

Focused tests use fabricated byte metadata and never decode tensors. The one
freshly admitted integration must independently observe one constructor and
baseline/selected safe decode plus strict loads, genuine adapter construction,
zero source/support updates, zero query calls and zero measured cells. Factory
witness counters describe the required successful path; native observations
remain the authority for executed calls and post-Job cleanup.

The owner's 25 October instruction to work with the available 4 GiB is recorded
as a startup-only allowance for this bounded phase. The separately versioned
guard requires two fresh 4 GiB startup samples and retains the 4 GiB active
floor, 20 GiB disk floor and all other Job and peer-release limits. The factory
checks 4 GiB before allocating the model. This does not requalify historical
10 GiB receipts or authorize wider work; an active-floor failure still stops
the run. See the [phase plan](../cho51_provenance_restore_plan_20261025.md).

Implementation is prepared for independent source review. Executed validation
and actual restoration acceptance are recorded separately in the dated project
qualification and new operations evidence; this README alone is not a receipt.
