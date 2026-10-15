# Adopted-51 real-input, recorder and selection-file composition

This separate successor composes the qualified recorder/target collector and
selection-file verifier without changing either implementation or the historical
1,040-case and 256-step routes. Source preparation is not a passing receipt.

`collection.collect_cho51_input_selection(project_root, route, recorder, pins, *,
case_input_pins, base_config_sha256, method_config_sha256, expected_source,
selection_ceiling_config_sha256) -> Cho51InputCollection` accepts the existing
adopted route/recorder and independent externally retained pins. The recorder
must already exist; this function constructs no recorder and publishes nothing.

The function freezes one exact 1,020-pin tuple and one immutable method mapping
for both checks. The recorder stage freshly verifies the full 52-source real
input pool while retaining subjects 02-52 as targets. The selection stage uses
the same case/source/method pins and the independent committed 5,253-ceiling file
pin. The composition binds every returned score row to the original key/cell
digest, every claim to the original case/evidence digest, and both stage results
to the same adopted owner decision and ceiling pin.

After selection inspection, it checks the selection witnesses, rereads the
complete recorder ledger/cells/success receipts with `verified_score_rows`,
requires identical final rows and checks the selection witnesses again. These
bounded rereads detect changes across inspection; they are not filesystem locks.

The immutable result contains only rows, selection claims, owner decision hash
and selection ceiling configuration hash. Its selected-publication,
selected-tensor, full-selector-evidence, combined selection/publication/tensor
and scientific-admission flags are always false. It does not return paired
analysis or aggregate scores. No models, fitting, numerical selector, tensor
restore, subprocess, new recorder, original attempt, sweep or scientific
execution is performed.

`test_collection.py` prepares **24** synthetic boundary cases. Stage I/O and
physical witness methods are explicitly replaced with fabricated metadata
collaborators. Cases cover order and shared immutable inputs, incomplete flags,
failure short-circuiting, invalid external rosters/ceiling pins, initial/final
row drift, claim ID/evidence drift and owner/policy mixing. They do not qualify
real arrays, persisted recorder construction, complete selector evidence or
scientific authority. Root owns a separate fresh guarded actual-input plus
fabricated-recorder qualification; execution requires its own finite native
admission and independent review. No test was executed during preparation.
