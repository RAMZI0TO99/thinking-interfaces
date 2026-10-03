# GPU source fitting and crash-resumable checkpoints

19 September 2026, milestone 50. The owner authorized appropriate GPU use,
requested crash checkpoints, then delegated 12 hours of autonomous work.
This is bounded engineering. Scientific ratification and every existing guard
remain in force; no commit or push is authorized.

## Implemented contract

`BCILaBraMSourceSelector` now accepts optional `source_device="cuda:0"`,
`checkpoint_directory=<dedicated directory beneath runs/phase2>`, and explicit
`operator_compute_admitted=True`. Plain linear/partial/full tuning and LoRA
are supported. Defaults preserve the CPU path. Adapter/prompt GPU or checkpoint
requests are refused. Support/query adaptation and evaluation remain on CPU;
the fitted source is moved back before the existing audited runners use it.

Every public call still admits its complete logical source/support step count
before any fit. Resume does not subtract completed steps from that admission,
increase the 256-step cap, split a large selection, or admit E2. Extended fits
check the existing machine guards, GPU cooling/headroom when applicable, and
source/runtime identity before each new source step. Checkpoint writes reserve
their full pending bytes above the same project disk floor.

Each completed source step publishes a unique, fsynced safetensors blob, then
an atomic immutable JSON manifest. The manifest binds the source/config/runtime
contract, candidate/fold, exact iterator history, model hash, input identities,
stateless SGD configuration, CPU/CUDA RNG and sampling state, and previous
manifest hash. No pickle is loaded. A single-writer OS lock releases on process
death. Committed corrupt records refuse; blobs without a committed manifest
are preserved and ignored. All generations are retained, with no auto-pruning.

Resume reconstructs and validates the complete sampling sequence and reloads
audited source inputs even for completed steps. It restores only source SGD.
An interrupted validation support/query calculation restarts from that fitted
source; it does not have a mid-evaluation checkpoint. Completed-case publication
continues to use the existing recorder. Full-fit evidence is stable across
resume; the optimizer's `fresh` label describes the independently initialized
logical fit with momentum-free SGD, whose restored optimizer state is empty.

## Discriminating checks

Focused checks: **28 tests / 50 subtests passed**. New tests compare exact
uninterrupted and resumed linear/full/LoRA source histories, final state and
validation outputs; count only remaining source gradients; verify caller/RNG
preservation; reject changed context, corrupt committed weights and concurrent
writers; preserve interrupted publication blobs; re-audit changed source data;
and retain step admission and the pending-write disk reservation.

The real-data check rebuilt all 52 Cho catalogs/episode identities with safe
pretrained LaBraM weights. For each of full tuning and LoRA it ran one public
validation fold with outer subject 01 and inner validation subject 02: 50
source steps and one CPU support step. A second process exited deliberately
with `os._exit(86)` after checkpoint 3, without Python cleanup. A fresh process
acquired the OS lock. The full-tuning resume then stopped at the unchanged GPU
temperature-sensor guard while publishing step 47: step 46 remained committed.
A further restart computed steps 47-50 and one support step. LoRA resumed all
47 remaining source steps plus one support step without that interruption. **Every source step, loss, state hash and complete validation
fold matched the uninterrupted GPU run exactly.** No saved generation changed.

Across both methods (including one recomputed uncommitted step): **201 GPU source + 4 CPU support steps**, two deliberate
hard exits, 100 retained checkpoint generations. Each public call admits only
51 logical steps; each process has a 600-second limit and an additional 8 GiB
GPU allocator cap. Existing machine/cooling guards were not mocked or weakened.
The complete Cho selection refused before fitting. All data/template/RNG checks
passed. There were zero outer-target predictions, full selections or scientific
cells. These engineering validation scores are not research evidence.

| Method | Uninterrupted fold seconds | Final recovery invocation seconds | Retained checkpoint MiB |
| --- | ---: | ---: | ---: |
| Full tuning | 75.00 | 41.16 | 1119.57 |
| LoRA | 70.33 | 87.85 | 1120.15 |

The final recovery column includes reading previous checkpoints, re-auditing
sources, the remaining fit and new checkpoint writes: four source steps for
full tuning, 47 for LoRA. It excludes both interrupted processes and initial
process setup. The preserved sensor-failure traceback and committed cursor
identify the one uncommitted source step recomputed on recovery. It is not a checkpoint overhead estimate or a
CPU/GPU speedup comparison. The full scientific storage/runtime envelope stays
unknown. Keeping every generation is a bounded engineering policy, not an
admitted retention budget for the proposed full campaign. Exact replay was
verified on this machine with deterministic FP32 CUDA settings and TF32 off;
cross-device/driver migration and power-loss recovery were not tested.

Fresh full quality: **571 tests / 935 subtests**, lint and strict types
passed. Raw summary: `571 passed, 4 warnings, 935 subtests passed in 845.69s (0:14:05)`.
Source fingerprint: `6d01ec59d7323af0fd91f141d1484a419717062b43d7d52dc221d27ea9be19a2`.
Evidence: `runs/phase2/gpu_checkpoint_checks/20260919_step50/receipt.json`.
The initial lint/type diagnostics and both deliberate crash logs are retained.
All 1660 baseline Phase II evidence files and
the scientific freeze draft retain their hashes/bytes.

Freeze ratification/EA inclusion, MMIDB eligibility, Gate A and commit/push remain
owner decisions. Scientific committed configurations and workload admission
remain prerequisites. The existing RAM-deferred control refresh may be retried
under its unchanged guards; no control refresh is claimed by this milestone.
