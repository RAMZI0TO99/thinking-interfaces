# Versioned Cho evidence storage option

23 September 2026, updated 24 September 2026 Riyadh time. The factored
physical format described below is now available as an **opt-in engineering
store format**. Canonical JSON remains the default. No real Cho selected
source, target prediction or scientific cell was produced, and no scientific
work is admitted. The [write-once sizing probe](../../runs/phase2/freeze_readiness/20260923_evidence_size_probe/receipt.json)
projects 25.990 GiB for repeated JSON values in the current first-tranche
evidence, before step rows and record framing. The existing store writes
canonical, uncompressed JSON. Final weights add 16.928 GiB under the
no-reuse plan.

## Lower-risk first experiment: lossless envelope compression

Keep the **logical** evidence envelope and its SHA-256 exactly as the current
selectors and `verify_cho_selection_evidence` expect. A new, explicitly
versioned store could compress the canonical JSON bytes after the completed
record has already passed verification. Its manifest would name the codec and
version, uncompressed byte length and digest, compressed byte length and
digest, and the unchanged logical envelope digest. Publication would remain
append-only: fsync a same-directory temporary, link without overwrite, then
publish the completion manifest last. Restore would verify both file digests,
enforce a declared decompression size limit, decode canonical JSON, verify the
original envelope, and only then call the existing scientific evidence
verifier. The old uncompressed store remains readable as version 1.

The probe's in-memory target-01 identity-map array compressed to about 5.05%
with gzip level 6. That is a **sample of highly repetitive map values**, not
an admitted compression ratio for complete 1,040-case evidence. A bounded
representative full-record experiment and measured temporary-disk/RAM peaks
would be needed before granting a physical-space budget. The current
`SelectedSourceStore` has no compressed codec, and a compressed file cannot
be silently substituted for its `.json` evidence path.

As a separate read-only cross-check, two **historical bounded BCI** source
selection JSON files ([source](../../runs/phase2/source_selection_checks/20260908_step20/engineering_selection.json),
[LaBraM adapter](../../runs/phase2/adapter_source_checks/20260909_step23/engineering_selection.json))
compressed in memory with deterministic gzip level 6:
304,182 to 16,450 bytes (5.41%) and 2,377,835 to 106,350 bytes (4.47%).
Both decompressed back to the original SHA-256. They are different cohorts
and workloads from complete Cho selection, so these ratios grant no Cho
storage credit.

## Per-case factored logical evidence

A narrower schema option stores one subject-to-input-identity table **inside
each case's packed evidence**. The encoder checks every source fit's
`input_identities` against that table and its recorded `training_subjects`
before omitting the repeated maps. For LaBraM it likewise checks each fold's
five-shot validation binding against a per-case subject table. A decoder
restores every omitted value, reproduces the exact canonical full-envelope
bytes and SHA-256, and then calls the unchanged public evidence verifier.
The [in-memory codec](../../evaluation/phase2_factored_evidence.py)
implements this exact-byte transformation with a bounded decode and an
external logical-envelope pin. `SelectedSourceStore.publish(...,
evidence_format="factored_json_v1")` now persists those bytes under their
physical SHA-256. Its write-once manifest explicitly pins the logical
envelope SHA-256, physical SHA-256 and byte count, codec schema, format and
physical path. One project-wide, crash-releasing process lock covers
pending-byte admission across all selected-source output directories,
physical publication and manifest-last completion. Packed reads enforce
the codec byte limit before allocating and check size and file identity
again after the bounded read. Canonical version 1
manifests remain byte-compatible, and both formats can be read through a
manifest-pinned store method. The Cho restore factory, preclaim gate and
posttarget reread now use the verified physical evidence path; the unchanged
public selection verifier consumes the reconstructed logical record. Focused
synthetic BCI/Cho store tests cover both formats, sparse-weight composition,
physical tampering, alias paths, unknown manifest fields and interrupted
resume. These tests do not establish an actual Cho storage budget.

A [read-only bounded BCI factoring probe](../../runs/phase2/freeze_readiness/20260923_factored_codec_probe/receipt.json)
checked this structure against the complete historical LaBraM adapter source
selection record. It verified the pinned input file and logical envelope,
matched every one of 16 folds' source identities to its seven recorded
training subjects and a shared eight-subject table, and matched each fold's
validation binding to its subject table. The packed canonical representation
was **334,969 bytes**, versus **2,377,835 bytes** for the original; the
decoder reconstructed the exact original bytes and both corrupted-table tests
failed closed. Deterministic gzip level 6 measured **106,350 bytes** for the
original and **24,068 bytes** for the packed representation. The packed data
was never published as a selection artifact. This is a BCI structural analogy,
not a measured Cho case or storage credit. The later store implementation has
only synthetic physical publications so far.

The current sizing receipt projects **27,906,236,120 bytes (25.990 GiB)**
for the repeated source-map and validation-binding values. From the receipt's
52 per-subject entry lengths, one table of each kind for the 51 eligible
sources per case would project **507,019,560 value bytes (0.472 GiB)**:
`15 x 51 x sum(LaBraM entry lengths) + 15 x 51 x sum(validation binding
lengths) + 5 x 51 x sum(EEGNet entry lengths)`. That is a conditional
structural reduction of about **25.517 GiB** before table keys and framing. The
encoder must prove that each repeated value matches before this saving can
be credited. Skeleton fields, step histories, file framing and temporary
space remain unmeasured. With the existing full final weights, even the
table-plus-weights subtotal would be **17.401 GiB**, at least **8.766 GiB**
above the probe's 8.635 GiB headroom over the disk floor.
Combining those tables with the separately proposed **5.648 GiB** of sparse
final weights would yield a conditional **6.120 GiB** subtotal, leaving only
about **2.515 GiB** for all other evidence, intermediate state, temporary
files and filesystem overhead at that disk snapshot. Both options are
implemented as opt-in storage capabilities but are not yet integrated with a
real Cho selected-source run or measured end-to-end. This subtotal is not a
compute admission.

The restore factory resolves the physical evidence path from a verified
selected-source manifest. The preclaim gate and posttarget check read that
path through the store decoder, verifying the packed bytes again. The store
does not create a full JSON shadow alongside factored evidence. It enforces
content hashes, packed byte count, bounded decode, append-only publication
and manifest-last completion. Version 1 reading remains available.

## Shared binding references and sparse weights

Content-addressing each subject's episode binding once could remove most
inline repetition, but it changes the selector evidence schema and verifier:
every fold would need to resolve and verify exactly the same binding bytes,
source cohort, target exclusion and trial identities before a metric or cell
is accepted. This is more invasive than lossless outer compression. It also
needs an atomic multi-object completion rule to avoid dangling references.

The [sparse-weight option](cho_selected_source_sparse_storage_option_20260923.md)
is separate. It reconstructs frozen initial tensors from a pinned baseline
and saves only trained tensors for linear/LoRA cases. Both opt-in formats can
be combined. Even if a future factored-evidence plus
sparse-weight combination fits one disk snapshot, selection steps,
intermediate checkpoint policy, filesystem overhead and the permanent 20 GiB
floor still need a measured full-work envelope. The unchanged 256-step cap,
unratified freeze and uncommitted configuration continue to block the
proposed 5,253-step complete selection independently of storage.

## Before scientific adoption

The opt-in physical format now has synthetic store and bounded historical BCI
round trips, tamper checks, concurrent publication tests and bounded decode.
A real completed Cho selection must still demonstrate byte-identical logical
evidence, the same selected candidate and model digest, and unchanged target
predictions against canonical version 1. Measure actual packed bytes,
temporary disk and RAM peaks, and checkpoint retention before placing this
format in a revised scientific freeze or compute admission. Preserve
historical evidence; no in-place migration is assumed.
