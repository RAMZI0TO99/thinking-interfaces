# Adaptation references: implementation review

Review date: 2026-08-31. Relevant method sections were read; adapter Figure 2
and the prompt/prefix method pages were visually inspected from local PDFs.
These notes distinguish verified mechanisms from exact paper reproduction.

## LoRA

Hu et al. section 4.1 freezes the base matrix, adds a low-rank product scaled by
alpha/r, and initializes one factor randomly and the other to zero. Merging the
product into the base weight removes the extra inference operations.
[Original paper, version 2](https://arxiv.org/html/2106.09685v2).

Our wrapper has the same residual and zero initial update, but uses Kaiming-uniform
rather than the stated Gaussian initialization. It does not merge weights at
inference, so zero extra inference latency is not claimed. Ranks 4/8/16 are
configured local choices, not an EEG performance guarantee.

## Bottleneck adapters

Houlsby et al. section 2.1 and Figure 2 use down-projection, nonlinearity,
up-projection and a residual path. Their Transformer placement includes two
adapters per layer and trains layer normalization and the final classifier.
[Primary paper](https://proceedings.mlr.press/v97/houlsby19a.html).

Our generic wrapper attaches one adapter after a named block, starts as an exact
identity using a zero up-projection, and trains only the selected adapter in the
smoke. This is not the complete BERT recipe. The publisher download was
unreachable; the authors' arXiv copy was inspected.

## Input prompt tuning

Lester et al. section 2 learns a continuous input prefix while freezing the
language model. The prompt is task-specific rather than generated anew by a
support encoder. Its scale findings concern language models, not EEG decoders.
[Primary paper](https://aclanthology.org/2021.emnlp-main.243/).

Our input-prefix mode shares the sequence-injection idea, but generates prompts
from support examples and uses a separate classifier. It is not their T5 recipe.

## Intermediate prefix tuning

Li and Liang sections 4.2-4.3 optimize prefix activations across layers while
freezing the model, using a learned reparameterization during training.
[Primary paper](https://aclanthology.org/2021.acl-long.353/).

Our per-block mode reinserts support-generated sequence tokens. It does not
directly parameterize each layer's key/value activations, so it must not be
labelled an exact Li-Liang prefix-tuning implementation.

## Local reference copies

| Source | File under runs/references | SHA-256 |
|---|---|---|
| Houlsby, arXiv | houlsby_adapters_2019.pdf | 7889e34caf5b786c378951be4b2f391234f5ff05ed61cba237b8281e3c94974b |
| Lester, ACL | lester_prompt_tuning_2021.pdf | d201f70a733b065d802b1adfa98ecac35c4633aa839dd7ef54d56c73d0fecf80 |
| Li-Liang, ACL | li_liang_prefix_tuning_2021.pdf | 89b23665c4e377361bae6b3924b8670d69739669b8af0bafe9d64b6a2e2d9d87 |
