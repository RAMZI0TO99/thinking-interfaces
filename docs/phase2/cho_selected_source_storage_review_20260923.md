# Cho first-tranche selected-source storage sizing

23 September 2026. **Engineering planning evidence only.** The selected
four-method, five-shot scope remains unratified; no selector fit, target
prediction, scientific cell or compute admission was started by this probe.

The [write-once sizing receipt](../../runs/phase2/freeze_readiness/20260923_storage_probe/receipt.json)
(envelope SHA-256 `3dc218dc6d8e73e4fbe8ef7fcef36afff69b7b4a41aaf6e429172450a01d639e`)
pins the source, proposed [1,040-case route](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_candidate_case_route_receipt.json),
candidate template, verified baseline safetensors and model configuration.
The [probe](../../runs/phase2/freeze_readiness/20260923_storage_probe/probe_storage.py)
constructed the actual plain LaBraM, trained-LoRA and EEGNet architectures on
CPU and serialized cloned state dictionaries through the same `_state` and
`safetensors.save` path as `SelectedSourceStore`. It did not fit models.

| Selected-source architecture | Cases | Bytes per full blob | Planned bytes |
| --- | ---: | ---: | ---: |
| Plain LaBraM, linear plus full | 520 | 23,294,624 | 12,113,204,480 |
| Trained LaBraM LoRA | 260 | 23,307,704 | 6,060,003,040 |
| EEGNet | 260 | 12,664 | 3,292,640 |
| **Final weights, one distinct blob per case** | **1,040** | | **18,176,500,160 (16.928 GiB)** |

At the receipt's post-probe snapshot, the D: workspace had **31.397 GiB**
free. Preserving the unchanged 20 GiB project floor leaves **11.397 GiB**
available, a **5.531 GiB shortfall for final weights alone** under the
no-reuse planning assumption. Selection evidence, completion manifests,
intermediate checkpoints, control records and filesystem overhead are not in
that figure. Whole-blob content addressing could deduplicate identical saved
states; no such reuse is credited or established for distinct target/seed
source fits.

A later [inline evidence sizing review](cho_selection_evidence_storage_review_20260923.md)
projects another **25.551 GiB** for repeated source-input maps alone under
the current uncompressed JSON store. Its later free-space snapshot and
combined arithmetic supersede this weight-only capacity comparison for
current planning. Neither review is a measured complete selection.

The opt-in `SourceFitCheckpoint` journal retains every generation. If applied
to **all** proposed LaBraM inner and final source steps, its 780 selections
would write 4,017,780 step snapshots. The model tensors alone imply at least
**85.057 TiB** for that conditional policy, before RNG tensors and JSON.
This is a storage consequence of enabling that mode for the full tranche,
not a claim that it has been enabled or admitted. A complete execution plan
must set an explicit crash-recovery and retention policy with a measured
storage envelope; the bounded engineering checkpoint test is insufficient
to price the full study.

The current public Cho evidence verifier also refuses the proposed complete
two-candidate 52-subject selection: 5,253 steps per case exceed the unchanged
256-step ceiling. More disk by itself therefore does not admit scientific
execution. The scope, complete compute budget, committed configurations,
Gate A and independent owner freeze decision remain separate prerequisites.
