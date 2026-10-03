# Bounded LaBraM reference-forward review

5 September 2026. Exploratory engineering evidence; Gate A remains unsigned.

## Outcome

The installed Braindecode LaBraM encoder and the pinned official forward code
produce exactly equal float32 tensors at every measured stage on identical
inputs and weights: **119/119 comparisons across seven cases**. No change to
`encoder/labram.py` or the frozen Phase I contracts was required.

This establishes the tested encoder path, including CLS features, temporal
cropping and named electrode embeddings. It does not establish decoding accuracy,
training/gradient parity, GPU parity, faithful TUAB/TUEV reproduction, TCPL
reproduction, tokenizer feasibility or scientific gate acceptance.

## Reference and loading

- Official repository: [935963004/LaBraM at c431221](https://github.com/935963004/LaBraM/tree/c431221e6cfd23dbfa9950e0180682fb322b0548).
- The three small files `modeling_finetune.py`, `utils.py` and `LICENSE` are cached
  under `.cache/phase2/labram-reference/c431221e6cfd23dbfa9950e0180682fb322b0548/`.
  Exact SHA-256 hashes are pinned in `configs/phase2/forward_parity.toml` and
  checked before use and after execution. The runner does not download anything.
- Safe checkpoint SHA-256: `53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`.
  All **221 tensors / 5,819,936 elements** map bijectively by name, without
  reshaping or changing values, and load strictly into both encoders. Existing
  byte correspondence with the original student checkpoint remains the basis
  for that provenance; this runner never unpickles the original checkpoint.
- Both encoders use the checkpoint's CLS path (`use_mean_pooling=false`), no
  classifier, no QKV bias, zero dropout, frozen evaluation state and CPU float32.
  This is not the official downstream training recipe or mean-pooling default.
- Installed environment: Python 3.12.13, Torch 2.13.0+cu130 (CPU execution),
  Braindecode 1.7.0, einops 0.8.2 and safetensors 0.8.0; two CPU threads.

The original model imports `timm`, which is absent locally. The bounded loader
removes exactly the two expected timm imports and the three model-registration
decorators. It binds the initialization helper to `torch.nn.init.trunc_normal_`;
strict loading then replaces every initialized tensor. The unused `drop_path`
and `to_2tuple` helpers raise if reached. Every model class and forward definition
is retained without modification. The full upstream dependency/training
environment is therefore **not** reproduced. No dependencies were installed.
`utils.py` is parsed only for its literal channel table, never imported.

The upstream utility contains 136 names, but the checkpoint has only 128
electrode positions plus CLS. Its first 128 names match the installed table
exactly, ignoring letter case. The eight trailing bipolar names lack checkpoint
positions and remain unsupported. None is used in this comparison.

## Cases and acceptance criteria

| Case | Batch / channels / samples | Input |
| --- | --- | --- |
| Synthetic 1, 2, 4 and 15 seconds | 2 / 3 / 200, 400, 800, 3000 | Seeded nonzero noise; C3, Cz, C4 |
| Existing real examples | 2 / 22 / 800 | BCI IV 2a subject 01 Profile B, rows 0 and 1 |
| Joint permutation | 2 / 22 / 800 | Reverse signals and matching channel names |
| Incorrect-name control | 2 / 22 / 800 | Reverse names only, retaining original signals |

No labels were read or used. Input artifact and manifest hashes, exact input
tensor hashes, channel indices, source fingerprint and installed source hashes
are recorded. Inputs, checkpoint files and model state remain unchanged.

Each case observes the actual public forwards via temporary hooks: patch
embedding, positional/temporal token assembly, each of 12 transformer blocks,
final norm, CLS and patch features. Hooks are removed even when a forward fails.
Tolerance was set before executing the comparisons to `atol=1e-5`, `rtol=1e-4`
for float32 accumulation; all same-input comparisons have zero error anyway.
Wrong names alter CLS features beyond this tolerance, and deliberate output
corruption is detected using the same criterion.

## Recorded precision limitation

Jointly permuting signals and electrode names is an additional algebraic
invariance check, distinct from comparing two implementations on identical
inputs. In float32, undoing the permutation gives maximum absolute differences
of **8.8214874e-5 for CLS** and **5.0258636e-4 for patch features**. Both fail the
original all-element tolerance. The official implementation gives exactly the
same outputs for each order, so this is not a local/reference discrepancy.

A post hoc float64 diagnostic uses the same weights and examples, with
`atol=1e-10`, `rtol=1e-8` specified before that diagnostic ran. It passes across
all 17 stages; the largest permutation difference is **7.4051876e-13**. Local
and reference float64 outputs also match exactly. This supports an explanation
based on floating-point reduction/accumulation, not a mapping discrepancy.

The float32 threshold was **not relaxed** and its failures were **not removed**.
The command deliberately exits 1, with `all_checks_passed=false`, alongside the
separate true `reference_forward_parity_verified` flag. Preserve a fixed channel
order in experiments; do not promise bitwise invariance under arbitrary
reordering or infer downstream score stability from this check.

## Validation and evidence

Full lint and strict type checks pass. The complete regression suite passes
**359 tests / 422 subtests**, including five new tests and 18 subtests covering
corruption, nonfinite tensors, shape/dtype mismatch, missing stages, ambiguous
weight mapping, reference hash/table validation and hook cleanup.

Final validation index:
`runs/phase2/forward_parity_checks/20260905T182908002340Z/final_receipt.json`.
It points to the immutable numerical receipt and hashes the quality logs.
Earlier receipts are preserved, including the initial aggregate failure and
the launch that could not discover Git. The final rerun sets Git's PATH in the
actual Python process, records the real HEAD and dirty state, and checks the
same source fingerprint against the already completed regression run:
`7952a61e83faf5651bff9ca8a164719b11f26ac8d1793dfeb2c6efe5af78f7b1`.

Changes remain uncommitted. The source-bound control bundle is still stale and
its refresh remains resource-deferred. No old receipt or scientific gate is
relabelled by this check. Large downloads and training were not launched.
Only 51,510 bytes of reference source/license files were downloaded. The latest
validation snapshot reports 14.4 GiB free, below the 20 GiB training floor.

Next step: implement the bottleneck adapter and its episode/state-isolation
checks, then continue the remaining methods one bounded step at a time.
