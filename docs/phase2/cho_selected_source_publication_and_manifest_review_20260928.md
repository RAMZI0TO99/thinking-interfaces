# Cho selected-source publication and manifest binding

This page records the 28 September file-binding step. The later
[tensor-state engineering review](cho_selected_tensor_state_review_20260930.md)
covers reconstructed selected weights before analysis score extraction.

28 September 2026. This is an engineering review of the proposed four-method,
five-shot, 60 Hz Cho2017 tranche. Current source
`69d671acdadf8e1dd4db129621ac01471d246cc77f2f8d344bff6277bf1101ce`
has focused checks and read-only evidence, while full quality and
source-bound control verification are pending.
No real Cho source fit, target cell, score, report or scientific admission is
claimed.

## Prospective case publication

The [Cho publication hook](../../evaluation/phase2_cho_publication_gate.py)
is called by the [case executor](../../evaluation/phase2_pilot.py) after the
full persisted selection preclaim check and a renewed compute admission,
before the recorder claim or target prediction. It accepts only the live,
built-in model for the planned Cho method, compares its state digest with the
cell checkpoint identity, derives a restore recipe from the independently
pinned case configuration, and rereads the selected evidence. It checks the
live model class and key architecture claims against that recipe: LaBraM
channel names and linear classifier output, or EEGNet channels, outputs,
time length, sampling rate and constrained final linear head. It then uses
the write-once [selected-source store](../../evaluation/phase2_selected_source_store.py)
to publish the source state and selection evidence under the existing 20 GiB
production disk guard. This hook requests full weights; the store also has
other formats for separately controlled uses.

Before returning to the executor, the hook runs the
[physical manifest verifier](../../evaluation/phase2_cho_selected_manifest_bridge.py)
on the newly persisted manifest, selection-evidence copy and weights file.
Its source, contract, candidate, protocol, recipe and model-state pins come
from the independently checked live case and preclaim, rather than from the
published manifest. It also compares the publication paths and weights
digest with the verifier's witness. The executor records the resulting
manifest digest and project-relative path in the cell metrics. It checks
the live source, environment and model again, renews admission, and enforces
the session cap before the recorder claim. After target prediction, it
rechecks the environment digest and the physical manifest witness before
`record_cell`; changed published files or environment prevent a success
cell. These steps narrow the prospective publication gap; they do not supply
a completed selector or prove that historical records used a published model.
The public complete Cho selection still requires 5,253 gradient steps against
the unchanged 256-step engineering cap, so this path is not a real Cho run.

## Read-only analysis boundary

The [paired-input composer](../../evaluation/phase2_cho_analysis_preparation.py)
requires independent case-input, source, method, cell and selected-source
pins for the full 1,040-case roster. It rederives the route and checks case
identity, persisted target declarations and observed target-input
attestations. Before it reads any score row, the
[selection-file bridge](../../evaluation/phase2_cho_selection_file_bridge.py)
checks each bounded canonical or factored selection file against its external
digest, route, candidate settings, static source policy, runtime and input
declarations, and final-fit winner and candidate digest. A recorded
`complete` flag is a claim in that file, not independent proof of every
source-only fold or gradient.

The composer also requires a `ChoSelectedSourcePin` for every case, including
the manifest, recipe and environment digests. It checks the recorded manifest
digest and path against the external pin and invokes the
[selected-manifest bridge](../../evaluation/phase2_cho_selected_manifest_bridge.py)
before score extraction. That bridge checks bounded canonical manifest and
selection-copy bytes, the selected candidate, contract, source, protocol,
recipe and fitted-state claims, format-dependent manifest fields, and the
streamed weights-file digest. It rejects path aliases and file changes while
reading. After exact score verification and paired-input construction, the
composer rechecks physical selection, manifest, evidence-copy and weights
files for replacement or mutation.

The manifest check binds **published bytes and declared claims**. The live
model class checks do not independently reconstruct the full tensor schema
from saved weights. The verifier does not decode safetensors, restore the
checkpoint state, replay inference, authenticate historical model use, or
verify the full selector ledger. The caller remains responsible for
supplying pins independently of the files
being checked. Synthetic tests exercise this boundary; they are not real
Cho publication or analysis evidence.

## Admission state

Focused Ruff, strict mypy, 65 tests and 19 subtests passed for `69d671ac`.
Its [guarded full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_final_manifest_69d671ac_guarded/receipt.json)
passed Ruff and strict mypy, but pytest reached 96% and timed out at the
unchanged 1,800-second command limit. Source stayed stable and the resource
guard held. This is **not a full-quality pass**; a retry is planned when CPU
headroom improves. The [exact-source raw audit](../../runs/phase2/freeze_readiness/20260928_69d671ac_raw_source_readonly/receipt.json)
verified 52 raw files totaling 10,704,036,837 bytes across 1,040 proposed
routes. The [method-template revalidation](../../runs/phase2/freeze_readiness/20260928_69d671ac_method_template_readonly/receipt.json)
checked 40 candidates and four digests, but remains unratified. The
[preceding `2264317d` quality archive](../../runs/phase2/quality_history/20260928_cho_publication_witness_2264317d.json)
passed 890 tests, 3 skips and 1,037 subtests for its own source only.
Current-source 45-control and 36-record no-future inventories remain
unverified while full quality is pending. The scientific freeze and Gate A
are unsigned; no real Cho fit, cell, score, report or scientific claim
follows from these engineering changes.
