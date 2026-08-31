# EEGNet implementation review — 2026-08-31

The installed Braindecode 1.7.0 implementation has the EEGNet-8,2 architecture
family, but it is **not a demonstrated numerically identical reproduction** of
the authors' Keras model. This distinction leaves Gate A unsigned.

The primary reference is [Lawhern et al. (2018)](https://arxiv.org/abs/1611.08024).
The comparison below uses the [authors' implementation](https://github.com/vlawhern/arl-eegmodels/blob/master/EEGModels.py),
reviewed on the date above, and the installed `braindecode/models/eegnet.py`.
The installed source SHA-256 is
`6e22097cfc456748b63d4cf4fc717ea26879e42c7a7588dc8ee3d511faaacb66`.

| Component | Frozen local benchmark | Reference comparison |
|---|---|---|
| Temporal/spatial filters | F1=8, D=2, F2=16; spatial depthwise groups | Same high-level decomposition |
| Temporal kernels | 64 then 16 samples | General Keras defaults match; the authors separately note 32 for their SMR setup |
| Pooling/nonlinearity | Mean pooling 4 then 8; ELU | Same high-level operations |
| Dropout | Ordinary dropout, probability 0.25 | Keras function default is 0.5; this is not an identical default configuration |
| Padding | Symmetric explicit padding; an even-kernel convolution adds one intermediate sample | Keras uses same-length padding; boundary behavior is not identical |
| Final classifier | Unconstrained convolutional head producing logits | Reference uses a norm-constrained dense classifier and softmax |

The local wrapper applies softmax only at prediction and uses logits with
cross-entropy for training. The spatial layer has a max-norm constraint, but
that does not add the missing final-head constraint. Convolution-to-linear
conversion used by the separate adaptation smoke test preserves the existing
local logits; it does not establish parity with Keras training.

The main benchmark deliberately remains the pinned Braindecode baseline:
five epochs, five seeds, identical source/support/query protocol across its
neural variants. Gate A's session-held-out attempts use separate configurations
and cannot be equated with that short LOSO sweep. The source review does not
explain away the failed comparator or prove one particular discrepancy caused it.
Changing kernels, padding or classifier constraints now would require a new
protocol and new results; none was silently changed after the benchmark or H2
margin freeze.
