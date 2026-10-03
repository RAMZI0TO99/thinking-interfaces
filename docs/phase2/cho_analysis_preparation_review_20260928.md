# Cho recorder preparation and target input provenance

28 September 2026. Source
`c535f4576a53ae0aa6b5f107ccc7115bd06d808f3527a1b5d9ea4dc0f1cb7a71`
adds a [read-only preparation bridge](../../evaluation/phase2_cho_analysis_preparation.py)
for the proposed four-method, five-shot Cho2017 first tranche. Its
[synthetic tests](../../tests/test_phase2_cho_analysis_preparation.py)
exercise all 1,040 planned cases and a complete temporary recorder. The
[focused write-once receipt](../../runs/phase2/analysis_pairing_checks/20260928_c535f457_focused/receipt.json)
pins the source before and after Ruff, mypy, and **11 passed tests with
9 passed subtests** across the preparation and Cho binding test files.
Mypy checked the new preparation module, the binding module and the new
typed test file; the older Cho binding test file is untyped and was not
included in that type command. This is focused evidence, not full quality.

The bridge requires an independently supplied `SourceProvenance` and an exact
four-method configuration digest map. It runs the [identity binder](../../evaluation/phase2_cho_analysis_identity.py)
against the complete route and 1,040 external pins **before** any recorder
read. It then derives the exact roster from the verified plans, asks the
[recorder bridge](../../evaluation/phase2_cell_aggregation_bridge.py) to
verify complete published cells and scores, and passes those rows to the
[paired-input builder](../../evaluation/phase2_cho_paired_inputs.py).
The synthetic test rejects missing source, wrong source, changed route,
changed episode and incomplete method digests before the reader is called.
It produces 208 exact subject-method means and 52 exact subject pairs from
the temporary publication, then rejects a missing success receipt and a
corrupt cell. It runs no fit, inference, report or scientific admission.

The [Cho Profile B loader](../../evaluation/phase2_profile_binding.py) now
hashes the in-memory Profile A and Profile B artifact buffers and the
Profile B manifest buffer that it parses. It still checks the pinned file
hashes before loading and checks the paths again afterward. The new
[regression](../../tests/test_phase2_cho_binding.py) substitutes different
read bytes while the files on disk retain their expected hashes; both a B
artifact substitution and a B manifest substitution are refused. This
closes the narrow gap in which a separate path-based hash could match even
though a transient buffer differed at parse time. This change is limited to
the Cho episode loader; it does not itself publish a target-use attestation.

## Remaining target-use boundary

The route's selection evidence declares the complete 52-subject 60 Hz
Profile B asset map for LaBraM, and the target loader produces a
`ChoProfileBinding60Hz` with the target artifact, manifest, variant, source
and episode identities. The LaBraM adapters currently reduce predictions
to `CaseOutcome` without retaining that binding. `TargetCaseExecutor`
therefore publishes scores and selection evidence but no observed target B
binding in the cell. Existing `CellIdentity` and `PinnedCaseCell` cannot
recover which B bytes a particular prediction consumed. EEGNet takes the
Profile A route and must not receive a Profile B claim.

A future publication path needs to carry the observed target binding from
the supervised prediction through `CaseOutcome`, compare its subject,
episode, trial IDs and B digests with independently pinned expected assets,
and include its digest in the exact cell publication. The recorder verifier
then needs an external binding pin before it yields a score row. A sidecar
of expected inputs alone proves planned bytes, not observed use. This is a
prospective engineering requirement: no existing cell gains that proof.

## Current gate

The latest D: reading was about 9.05 GiB free, below the project's unchanged
20 GiB control-fit disk floor. Full exact-source quality for `c535f457`
and refreshed source-bound controls are pending; earlier quality and control
receipts remain historical for their own fingerprints. The 5,253-step
complete selection exceeds the unchanged 256-step engineering cap. The
scientific analysis freeze and Gate A remain unsigned. There is no real
Cho score, admitted scientific cell or inferential report.
