# TCPL support encoder and prompt generator

Completed 8 September 2026. `adaptation/tcpl_prompt.py` adds `TCPLSupportEncoder`
and `TCPLSupportPromptGenerator`. The
[local constructor contract](../../configs/phase2/tcpl_local_contract.toml)
records implementation choices separately from the unchanged
[reference inventory](../../configs/phase2/tcpl_reference.toml). Author parity
and numerical reproduction remain unverified.

## Implemented behavior

The support encoder maps `[trials, channels, time]` to `[trials, 64]` using two
kernel-three convolution/ReLU stages, a temporal mean and a linear projection.
Widths `64, 64`, ReLU placement, symmetric zero padding, bias and initialization
details are explicit local choices. It has no normalization or dropout. Complete
support trials are available, so this encoder is intentionally noncausal; the
separate TCN's causal contract is unchanged.

The combined generator accepts `[episodes, shots, channels, time]`, encodes each
trial independently, means the embeddings within each episode, and applies
`Linear(64,64) -> ReLU -> Linear(64,640)`. Its output is `[episodes,10,64]`.
All linear weights use Xavier uniform initialization with zero biases;
convolutions retain installed PyTorch defaults.

The shot axis counts total supplied trials. Each batch has uniform shot counts
and trial lengths; padded shots and ragged trials are unsupported. Zero-valued
trials are ordinary data, not a padding marker. Use separate calls for different
sizes. Empty, nonfloating, nonfinite and dimensionally invalid inputs are rejected.

There are no label/query arguments, free prompt parameters, detached features or
episode caches. Gradients connect generated prompts to both networks. The caller
must provide correctly partitioned support, enforce class balancing, and freeze
parameters for target inference. The module cannot infer trial permissions from
tensor contents. Labels remain useful to the sampler and later supervised loss,
but do not condition this generator. Existing LaBraM prompts are unchanged.

## Remaining constructor choices

The local contract specifies the next Transformer/readout implementation: four
post-norm layers, eight heads, dimension 64, FFN 256, ReLU, dropout 0.1 and LayerNorm
epsilon `1e-5`; no additional positional encoding, attention mask or final norm;
one prompt prefix after the TCN; and mean pooling of final EEG positions only
before a dataset-sized linear logits head. It also specifies initialization.
Unreported choices are marked local. These modules are **specified, not yet
implemented** by this step. The attention candidate is for complete offline
epochs and would not preserve the TCN's causal output property.

No training budget, split reconciliation or preprocessing ambiguity has been
resolved by choosing constructors. Those scientific questions remain as recorded
in the reference review; the contract is not a runnable training configuration.

## Validation

Eight new tests and 28 subtests cover the full-width support component on CPU:

- Finite outputs and unchanged inputs for 1/3/22/64 channels, single-shot and
  multi-shot support, short/512-sample trials and noncontiguous views.
- Independent per-trial calculation matches encode-then-mean output. A control
  with opposing-sign trials distinguishes it from averaging raw signals first.
- Permutation and uniform replication of support preserve prompts at declared
  tolerances (`1e-6` float32, `1e-12` float64).
- Changed signals change their episode's prompts; another episode's output is
  exactly unchanged. An autograd probe confirms zero cross-episode derivative.
- A synthetic squared-prompt loss yields finite, nonzero gradients through every
  parameter tensor and every support trial. One SGD step changes every parameter
  tensor and the prompts. This is gradient-path evidence, not model training.
- Fixed-parameter inference leaves state unchanged; unrelated support calls do
  not affect repeated output. `weights_only=True` in-memory restoration is exact.
  Contract dimensions, parameter inventory and invalid inputs are checked.

Parameter counts:

| Input channels | Support encoder | Generator | Combined |
| --- | ---: | ---: | ---: |
| 22 | 20,800 | 45,760 | 66,560 |
| 64 | 28,864 | 45,760 | 74,624 |

Full lint passes; strict types pass for 145 source files. Full regression output:

```text
392 passed, 3 warnings, 554 subtests passed in 20.89s
```

The three warnings are the existing EEGNet deprecation and classification warning.
The initial focused test run passed; three long test lines were wrapped before
final validation. No behavioral correction or tolerance change was needed.

Evidence: `runs/phase2/tcpl_prompt_checks/20260908T132443136231Z/receipt.json`,
with adjacent lint/type/test logs. The unchanged source fingerprint during checks
is `9badf0fb7da4ac82329d496756699a834f37721d39df8414ea54ac27dfb3bdde`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.
All pre-existing source/config/test files retain their before-step hashes.

Next bounded step: assemble the TCN, generated prefix, Transformer and classifier
under this local contract; test actual token placement, effective conditioning,
joint gradients and fixed-target query/state isolation. This will be a local
TCPL reconstruction until independent author evidence establishes parity.

The validation snapshot reports 8.70 GiB free, below the unchanged 20 GiB training
floor. Heavy training, source-bound control refresh and scientific gate approval
remain deferred.
