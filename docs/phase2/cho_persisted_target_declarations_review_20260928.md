# Cho persisted target declarations and recorded target checks

28 September 2026. This engineering review follows the
[target-input attestation review](cho_target_input_attestation_review_20260928.md).
It describes source
`147c0d1111fbdbff3d508c7c962af522a6e81301077fb6af13f47d25fb7b931c`.
It does not ratify the scientific freeze, admit a real cell, or establish an
inferential result.

## Read-only preparation order

The [Cho preparation function](../../evaluation/phase2_cho_analysis_preparation.py)
now requires a project root and an independently supplied SHA-256 pin for
`configs/base.toml`. It checks the independently supplied source and all
1,040 planned case identities first. It then verifies the exact bounded
bytes of the base config, the route-pinned 60 Hz variant config, and all 52
route-pinned Profile B manifests through the
[persisted declaration reader](../../evaluation/phase2_cho_persisted_target.py).
Only after these checks does it inspect each externally pinned cell's
target-input attestation, verify recorder publication and scores, and form
208 five-seed means and 52 exact paired subject inputs. The recorder must
belong to the reviewed project's Phase II output root.

The persisted reader requires the supported Profile A and B base
preprocessing definitions, the named 60 Hz variant and output directory,
and each manifest's subject, variant digest and B preprocessing digest. It
keeps each manifest's raw source path and SHA-256 declaration, requiring a
path inside the Cho raw namespace and a valid digest. Configs and manifests
are size bounded, hashed from the buffers parsed, and checked again after
the 52-manifest scan. Path alias checks reject a symlink, junction or
hardlink for the files it reads. Its output is a fixed set of declarations
for subsequent cell checks.

The [recorded target verifier](../../evaluation/phase2_cho_target_input_bridge.py)
now compares each LaBraM cell's full observed B binding with those
persisted declarations: B preprocessing config, independently pinned base
config, and the target subject's raw source path and digest. It continues
to require the planned episode, support/query IDs, Profile A retention,
Profile B artifact and manifest identity, and 60 Hz variant. For EEGNet,
it requires a target Profile A-only anchor and compares its base-config
digest with the independent persisted pin. A mismatch rejects the proposed
paired-input preparation before scores are consumed.

## Evidence and limits

The preceding source `98f6f523` has a
[focused receipt](../../runs/phase2/analysis_pairing_checks/20260928_target_attestation_focused/receipt.json)
for the prospective cell attestation. Its statement that config and raw
source declarations were not independently bound to persisted bytes is
historical for that source. The new comparison uses persisted config and
manifest declarations. It does **not** hash the Profile A or B artifact
files, hash the raw source files, replay inference, or prove that a
potentially fabricated runner consumed the claimed buffers. The observed
target binding still depends on the pinned execution source and runner
contract.

Focused checks for this source are recorded in the
[write-once receipt](../../runs/phase2/analysis_pairing_checks/20260928_persisted_target_focused/receipt.json).
The receipt pins stable source, Ruff, strict mypy, 13 passed tests,
1 skipped test and 15 passed subtests across three targeted files. Full
exact-source quality was pending when that focused receipt was written.
It later [passed in full](../../runs/phase2/quality_history/20260928_cho_persisted_target_147c0d11.json)
under a [guarded attempt](../../runs/phase2/quality_attempts/20260928_cho_persisted_target_147c0d11_guarded/receipt.json):
Ruff, full strict mypy and 830 tests / 1,033 subtests passed, with 2
skipped. The source stayed stable and minimum free disk was 9.572 GiB.
No fit, cell, score or scientific admission occurred. The earlier `c535f457`
[guarded full-quality attempt](../../runs/phase2/quality_attempts/20260928_cho_preparation_c535f457_guarded/receipt.json)
stopped at its quality-only disk floor after Ruff and strict mypy passed;
it is not a passing quality bundle for any later source.

The [current-source 45-control inventory](../../runs/phase2/control_refresh_checks/20260928_persisted_target_147c0d11/inventory_receipt.json)
found 0 valid / 45 missing with no invalid or unexpected records. It
started no fit. The [no-future check-only preflight](../../runs/phase2/gate_a_diagnostics/20260928_no_future_persisted_target_147c0d11/preflight_receipt.json)
deferred before raw recomputation with 10.494 GiB free against its
20 GiB disk requirement. Thus the current-source 36-record inventory is
unverified; the older 0/36 inventory applies only to its earlier source. Complete
selection evidence, checkpoint and environment provenance, scientific
freeze and analysis configuration, Gate A, and the 5,253-step selection
versus 256-step cap remain open. The production 20 GiB fit floor remains
unchanged. No real Cho fit, cell, score, report or scientific claim was
produced by this check.
