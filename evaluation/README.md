# Shared Evaluation

Contains baseline wrappers, metrics, leakage tests, paired comparisons, aggregate tables, and deterministic figure regeneration from run records.

The proposed Cho2017 four-method path now has a
[pre-target selected-source publication hook](phase2_cho_publication_gate.py)
and a [read-only paired-input composer](phase2_cho_analysis_preparation.py).
The executor runs the full persisted-selection preclaim verifier, renews compute
admission, publishes the live model and selection evidence, and records the
selected-source manifest identity before target prediction. The composer
requires external pins for the full 1,040-case roster and checks bounded
selection-file, manifest, evidence-copy and weights bytes, then reconstructs
each published `full_v1` selected-source tensor state before score rows. It
rechecks file stability after paired-input construction. The
[tensor-state review](../docs/phase2/cho_selected_tensor_state_review_20260930.md)
states the remaining historical-use, complete-selection, memory and admission
limits. For source `08751a39`, focused restore checks passed 39 tests / 29
subtests, all five composer tests passed, and focused Ruff/strict mypy passed.
The [guarded full-quality runner](../runs/phase2/quality_attempts/20260930_tensor_state_08751a39_guarded/run_guarded_quality.py)
is prepared but cannot start below its 9 GiB disk floor. The
[prior `90d822aa` archive](../runs/phase2/quality_history/20260928_quality_timeout_90d822aa.json)
is historical.



`evaluation.phase2_runner` records Phase II runs: deterministic pilot case
manifests, atomic claims with one linked retry, immutable failures and
evaluation_cell publication with exact-rational metric verification against a
cited selection evidence digest. See the
[recorder review](../docs/phase2/runner_review.md) for the lifecycle, invariants
and the 177-case manifest check.

`evaluation.phase2_subject_aggregation` computes exact-rational means over an
explicit, complete roster of externally verified Phase II cell scores. It
keeps shot counts separate and returns the ordered cell digest roster. It
does not read or verify cell files, run inference, or publish a report; see
the [proposed analysis contract](../docs/phase2/cho_analysis_execution_contract_20260924.md).

`evaluation.phase2_cell_aggregation_bridge` checks an explicit recorder roster
against externally retained cell, success-receipt and selection-evidence
digests. It verifies bounded canonical case records, linked retries and exact
confusion-derived scores before calling the aggregation core. The caller must
still verify scientific source, cohort, episode, selection and configuration
evidence; this bridge makes no inferential claim.


`evaluation.phase2_pilot` executes admitted pilot target cases: fail-closed
compute admission with machine guards and caps, nine method adapters over the
audited runners, identity verification against the live source and environment,
immutable failure records and staged-timing evaluation cells. See the
[executor review](../docs/phase2/pilot_executor_review.md) for the lifecycle
and the zero-prediction readiness check.


`load_cho_profile_b_episode` binds audited Cho2017 Profile A episodes to the
generated Profile B encoder inputs: catalog-hash identity (Cho has no A
sidecars), session/run/index bijections with equal labels, fixed query pools
and unchanged hash/byte-stability enforcement. See the
[Cho binding review](../docs/phase2/cho_binding_review.md) for the contract
and the 160-query real check.


`evaluation.phase2_cho_profile_a` loads audited Cho2017 Profile A subjects
with catalog-hash identity (no sidecar manifests), enforcing the 64-channel
finite contract before returning owned retained rows. See the
[anchor generalization review](../docs/phase2/anchor_cho_review.md).


`load_mmidb_profile_b_episode` binds audited MMIDB episodes to Profile B
encoder inputs with the T9/T10 montage, catalog-hash identity, the recorded
resample policy and hard refusal of the audited-ineligible subjects. See the
[MMIDB binding review](../docs/phase2/mmidb_binding_review.md).
