# LaBraM original-to-safe checkpoint correspondence

10October2026 addendum: a separate
[inert metadata and pretraining provenance review](checkpoint_pretraining_provenance_20261010.md)
records original training declarations and a complete local-paper Appendix D
review. They do not establish the checkpoint's recording-level training cohort
or resolve target overlap. The historical tensor-byte evidence below retains
its original scope; no new numerical correspondence or scientific acceptance
is inferred from the addendum.

The safe working conversion retains **221 tensors / 5,819,936 elements** from
the original checkpoint. Every retained tensor has exactly the same shape and
serialized bytes under the explicit name-only mapping. No tensor was reshaped,
retrained, rounded, or added to force the plan's count.

## Evidence and safety

Machine-written report:
`runs/checkpoint_audit/20260831T124411577972Z.json`, SHA-256
`4f7dce8d442c97e15482802c948cddd7b7f4ff85b0331817929f80fcb7ae6638`.
Audit source commit `51e92abc081a6334b2cfa41b52dacb58f81df7d5`, source fingerprint
`0b4b7e52c07b2a76715755c1cd1a2b1f0ed5d2f0c705f8cb52599c88f75e6d6a`.
The full quality suite passed: 244 tests and 227 subtests, lint/types, and the
three historical leakage checks. The checkpoint audit adds malformed-input,
inert dangerous-global, and altered-byte/shape regression tests.

Inputs are pinned in `configs/labram_checkpoint_audit.toml`:

- Original `checkpoints/labram-base.pth`: SHA-256
  `7c50583826afac76c4ab18f43d958df40496c8229accc09ed6a227c9bb57c37c`.
- Safe conversion, cached snapshot `0563b6c626e7b40d9a36653b763715db94d945d7`:
  SHA-256 `53b752edb366fd6395dd3cb7d63ae3e1e16aabed040aa0901d64ef32e8f444f8`.

The original ZIP's protocol-2 metadata was inspected with an inert, restricted
stack parser using `pickletools.genops`. GLOBAL, REDUCE, NEWOBJ, BUILD, and
persistent-storage references are descriptors only: no named callable is
imported or invoked. There is no `pickle.load`, `torch.load`, allowlisting, or
model instantiation. Unknown instructions, malformed ranges, noncontiguous
storage, ambiguous keys, and unexpected omissions fail closed. Input hashes
were verified before and after the audit. The checkpoint's absent byte-order
marker is recorded; the original float values were not decoded.

## Tensor accounting

The original bundle has model, optimizer, epoch, arguments, and scaler entries.
Its model dictionary contains 229 tensors / 9,153,521 elements. The `student`
subset has 7,466,728 elements; these are state-dictionary element counts, not an
independent reconstruction of the original architecture's trainable parameters.

| Original model entries omitted from the safe backbone | Elements |
|---|---:|
| `student.mask_token` | 200 |
| `student.lm_head.weight` and `.bias` | 1,646,592 |
| Separate `lm_head.weight` and `.bias` | 1,646,592 |
| `projection_head.0.weight` and `.bias` | 40,200 |
| `logit_scale` | 1 |

Thus 7,466,728 minus the student mask/output-layer entries equals 5,819,936.
The safe name mapping removes `student.`, renames position/time embeddings,
adds `temporal_conv` within the patch embedder, and names MLP fc1/fc2 as 0/2.
All original/safe key pairs, shapes, and individual byte hashes are in the report.

The current 800-sample configuration separately crops 16 temporal embeddings to
5, removing 2,200 elements: 5,817,736 backbone parameters. The four-class local
classifier is an additional 804 parameters, not included in those backbone counts.

## What remains unresolved

The plan requests 5,822,770 parameters. Neither the retained backbone nor these
documented additions/cropping explains that exact count. The literal count check
remains false. Byte correspondence establishes retained-weight identity, **not**
equivalent forward implementations, exact paper reproduction, or scientific
sign-off. The existing real-input forward smoke is separate functional evidence.
