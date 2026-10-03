# TCPL causal TCN component

Completed 8 September 2026. `encoder/tcpl_tcn.py` implements the bounded component
defined by the [reference review](tcpl_reference_review.md). It is a local
reconstruction of the TCN component, with author parity still unverified. The
historical reference inventory and all existing source/config/test files remain
byte-identical; the new model and tests are separate files.

## Implemented contract

`TCPLCausalTCN(input_channels)` accepts floating `[batch, channels, time]` inputs
and returns `[batch, time, 64]`. The four residual blocks use widths
`64, 64, 128, 128`, dilations `1, 2, 4, 8`, and two kernel-three convolutions per
block. These dimensions follow the pinned reference inventory.

The explicit local choices are:

- Stride one throughout, with `2 * dilation` zeros padded on the left before
  each temporal convolution. Sequence length is preserved, including length one.
- Each block computes two `convolution -> ReLU -> elementwise dropout(0.1)`
  stages, adds its skip path, then applies ReLU. The skip is identity at equal
  widths and a biased 1x1 convolution otherwise.
- A biased `Linear(128, 64)` projects each time point independently. Convolutions
  retain the installed PyTorch initialization; the output weight uses Xavier
  uniform initialization and the output bias is zero.
- Ordinary train/eval modes control dropout. No normalization, temporal pooling,
  prompt injection, classifier or persistent streaming state is introduced.
  Each call processes an independent complete sequence; chunked streaming would
  require a separate context-handling contract.

These choices do not resolve the paper's unspecified downsampling/ordering
details. The module does not select dataset channels, preprocess signals or fit
support/query data. It inherits normal PyTorch device/dtype behavior.

Measured parameter counts are **231,936** for 22 input channels and **238,528**
for 64. These counts cover the TCN and output projection only.

## Verification

Nine new tests and 50 subtests run on the full-width component, on CPU:

- Shapes and finite float32 outputs cover 1/3/22/64/128 channels, lengths
  1/17/61/512, batches of two and noncontiguous input views.
- Future-input perturbations leave every earlier output exactly unchanged in
  float64 evaluation and training with the same dropout realization. Later
  outputs change. A symmetric-convolution negative control detects the same
  perturbation, distinguishing causality from a nonresponsive model.
- Positive-weight gradient probes isolate every block's dilated dependency and
  measure the full receptive field: output time 80 depends on exactly input
  times 20 through 80, with zero derivatives elsewhere. Thus the maximum field
  is 61 samples under this local contract.
- Zeroing temporal branches isolates both identity and projected skip paths.
  A synthetic gradient/update check reaches every parameter tensor with finite,
  nonzero gradients and effective updates; this is not scientific training.
- Evaluation does not mutate state or retain previous-sequence information.
  In-memory serialization with `weights_only=True` restores identical outputs.
  Invalid dimensions and nonfloating inputs are rejected.

Full lint passes; strict types pass for 144 source files. Full regression output:

```text
384 passed, 3 warnings, 526 subtests passed in 15.54s
```

The three warnings are the existing EEGNet deprecation and classification warning.
The focused test run passed initially; one overlong test line was then wrapped
before final validation. No behavioral fix or tolerance change was needed.

Evidence: `runs/phase2/tcpl_tcn_checks/20260908T131728868896Z/receipt.json`,
with adjacent lint/type/test logs. The unchanged source fingerprint during checks
is `6096e036af3b03996af0901179a854a3912bec283931857dcbd02843e2bd9b09`.
Git HEAD is `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.

## Remaining work

Next bounded step: define the remaining TCPL constructor contract, then implement
the support encoder and prompt generator against that explicit contract. Missing
author settings must remain labeled as local choices, with full-model assembly
and any author-parity claim treated separately. Dataset/split/preprocessing
questions from the reference review remain unresolved.

The validation snapshot has 8.75 GiB free, below the unchanged 20 GiB training
floor. No heavy training, source-bound control refresh or scientific gate approval
occurred. The old controls remain stale for the changed source.
