# Cho target-input attestation and recorder checks

28 September 2026. This is an engineering review of the prospective
four-method, five-shot Cho2017 first tranche. It follows the earlier
[recorder preparation review](cho_analysis_preparation_review_20260928.md).
It does not ratify the scientific freeze or admit a real cell.
The exact source fingerprint is
`98f6f5233e4656bd6d2b61aed1151dfa4f75efcd6ae93d854f1bab3af931dcb7`.

## Publication path

The [case executor](../../evaluation/phase2_pilot.py) now carries the
observed target-loader result through `CaseOutcome` into the proposed Cho
cell. For the three LaBraM methods, it requires a
`ChoProfileBinding60Hz`, checks its target subject, episode, support and
query trial IDs, Profile A retention, and Profile B artifact, manifest and
60 Hz variant against the selected case and target asset. It publishes the
binding fields and their digest in `metrics.target_input_attestation` before
the success cell is recorded. EEGNet instead carries its target anchor
prediction and publishes only the target Profile A input identity. A Cho
EEGNet cell cannot claim Profile B. These checks are inside the case failure
boundary, so a mismatch prevents a success cell.

The [Profile B episode loader](../../evaluation/phase2_profile_binding.py)
hashes the exact A and B artifact and B manifest buffers it parses. The
[Profile A EEGNet loader](../../evaluation/phase2_cho_profile_a.py) now also
hashes the in-memory artifact buffer it parses. The latter change has a
focused transient substitution regression in
[the Cho anchor tests](../../tests/test_anchor_cho.py). The two loader
checks tie their observed buffer bytes to the published identities.

## Read-only verification path

The new [target-input verifier](../../evaluation/phase2_cho_target_input_bridge.py)
reads externally pinned canonical cell bytes and checks the attestation
schema, case identity and route-matched target identities. It checks the
full LaBraM binding digest and its B asset fields, row counts and static
60 Hz properties. For EEGNet, it requires a Profile A-only anchor and the
target catalog and artifact identity. The proposed
[recorder preparation bridge](../../evaluation/phase2_cho_analysis_preparation.py)
must run the independent-source case identity binder first, then these
attestation checks, before yielding any score row or 52 paired inputs.
An absent or old-format attestation is rejected; historical records do not
gain target-use evidence from this code change.

The cell verifier checks what a pinned cell declares. The case executor's
source and the observed runner output are part of the trust boundary: a
fabricated runner could fabricate an observed binding. The verifier does
not replay inference, inspect an already produced model state, or by itself
establish scientific admission. In particular, the read-only bridge checks
the syntax of the B profile-config, base-config and B manifest source
digests, but does not independently compare those declarations with
persisted config, base-config or raw-source bytes. The EEGNet base-config
digest also is not independently bound by this read-only check. Those
persisted-byte comparisons must be independently verified before any
scientific admission. The complete selection, restored model, environment,
controls and scientific analysis freeze remain separate.

## Quality and admission state

The earlier `c535f457` [guarded full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_preparation_c535f457_guarded/receipt.json)
passed Ruff and strict mypy, then stopped its owned test process when free
disk fell below the quality-only 8 GiB active floor. It has no passing
quality archive; the production 20 GiB fit floor was unchanged. The
[write-once focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_target_attestation_focused/receipt.json)
pins stable source, Ruff, strict mypy, 9 passed tests and 15 passed
subtests across five targeted files. No training or scientific admission
occurred. Full quality for this source remains pending. Earlier
read-only inventories found 0/45 source-bound controls and 0/36 no-future
records; current-source inventories are pending. The 5,253-step
complete selector exceeds the unchanged 256-step cap, the full scientific
freeze and Gate A are unsigned, and there is no real Cho cell, score,
report or scientific claim.
