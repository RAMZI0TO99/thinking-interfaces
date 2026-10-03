# Proposed Cho2017 four-method candidate template

**Status:** review draft, unratified, no scientific cells or fits. The owner
selected the four-method first tranche and the 60 Hz Cho Profile B rebuild;
those choices did not ratify candidate values or admit the full workload.

**Engineering update, 1 October 2026:** the configured selection ceiling
is now 5,253 and the user authorized the documented 30-hour engineering
session. The template remains unratified scientifically. Its full source
selection has not yet completed as a real admitted case; measured runtime,
memory and convergence remain open. The historical review below records the
earlier budget assumptions. See the [handoff](../../HANDOFF.md).

The [candidate template](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json)
names `labram_linear`, `labram_lora`, `labram_full`, and `eegnet` in that order,
for Cho2017 five shots and model seeds 11/23/37/53/71. Each method has two
ordered candidates, `lr_1e-3` then `lr_2e-3`, with the same rate at source
and support and one source update per subject plus one support update. It
pins the selector's current source policy, equal-subject exact-rational mean
balanced accuracy, first-candidate tie break and no early stopping.

The three LaBraM methods require `cho_profile_b_60hz_v1` and pin its actual
variant-config SHA-256
`6a3d5b9afca7bc0b82532276df1ef8f0a14db85da0eb609b5176ac967d04afb3`.
EEGNet uses the audited `cho_profile_a` identity and a null 60 Hz variant pin.
The candidate records use the selector's literal `candidates` field and
`name`/`source`/`support` structure. The static template keeps LoRA source
`seed` as `"$case_model_seed"`; `source_seed_policy="case_model_seed"`
materializes it to each case's model seed. Other methods have no
candidate-level source seed; their selector model/sampling seed remains a
separate dynamic case field.

| Setting | Draft value | Basis and decision still needed |
| --- | --- | --- |
| Source/support learning rates | 1e-3, 2e-3 in ordered slots | Proposed by the [freeze draft](scientific_freeze_draft.md), not measured as a two-candidate comparison. Pilot LaBraM used 0.01; pilot EEGNet used 0.001. Owner must ratify the roster and cost/convergence plan. |
| Source and support updates | One per source subject; one support step | Freeze draft's bounded proposal. These are not converged settings; full selection exceeds the unchanged engineering ceiling. Owner must approve the scientific budget and resource envelope. |
| Plain LaBraM | Source batch 2; query batch 8; linear or full mask | Values used by the [measured pilot](../../runs/phase2/pilot_matrix_checks/20260919_step40/phase2_pilot.py). Review for the 60 Hz rebuild. |
| LoRA | Last-block QKV, rank 4, alpha 1.0, head trainable, source batch 2, query batch 8 | Pilot structure. The smoke config used alpha 8.0, so alpha 1.0 is specifically a pilot continuation choice, not a universal default. Owner must ratify structure, alpha, head and per-case seed policy. |
| EEGNet | Profile A, source batch 4, query batch 8, input scale 1e6 | Pilot code's volts-to-microvolts path. Owner must ratify these settings and the unmeasured second rate. |

The [read-only validator](../../runs/phase2/freeze_readiness/20260923_cho60hz_scope/verify_proposed_four_method_candidates.py)
checks exact fields and method order, current protocol seeds/shots, actual
60 Hz config bytes, selection policy, fixed settings, and the source/support
rate pair. It materializes every candidate for every model seed into the
existing production dataclasses and checks that the serialized settings match
the template after substitution: **40 typed candidate instances checked**.
The template raw SHA-256 is
`f3dba0643cba2807fbc6e0421c271f260c8cf357a8bc67a19f7456931ca892ef`;
its semantic SHA-256 is
`c3b446ecc82b2a50ffd9cfcccc6270ecbadee437cacaa9ba0be6df29e9530fb1`.
The validator, Ruff and strict mypy passed. No model was loaded or fitted.

This artifact is a concrete decision draft, not a committed executable
scientific configuration. Full freeze ratification, measured complete
selection/resource admission, current-source controls, Gate A and the
separate MMIDB policy remain open.
