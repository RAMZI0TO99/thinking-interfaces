# Prompt generator design contract

## Purpose

Generate a small set of subject/task-conditioning tokens from the support set of
an episode. The generator must work first with a stand-in transformer and later
with LaBraM without changing the adaptation boundary.

## Input

The generator receives support-only encoder features with shape
`[batch, support_examples, embedding_dim]` and their support labels. Features are
pooled into one prototype per observed class, ordered by the episode's canonical
class order. Missing classes use a learned missing-class vector and an explicit
mask. Query signals, query features, and query labels are forbidden inputs.

## Output

The output is a contiguous floating-point tensor with shape
`[batch, prompt_tokens, embedding_dim]`.

- `prompt_tokens` is configured and independent of the number of EEG patches.
- `embedding_dim` must equal the backbone token width exactly.
- The generator returns prompt tokens only; it does not alter backbone tokens.
- A prompt mask with shape `[batch, prompt_tokens]` marks valid prompt positions.

## Injection point

Prompt tokens are prepended after EEG patch, channel, and positional embeddings
have been formed, and immediately before the first transformer block:

`EEG -> patch/channel embedding -> prepend prompt -> transformer blocks -> head`

Prompt positional embeddings are learned separately. EEG token positions and
channel indices remain unchanged. The classification head reads the backbone's
normal pooled representation after prompt-conditioned transformer processing.

## Adaptation and leakage rules

1. Fit or update the prompt generator using support data only.
2. Freeze the generated prompt before evaluating any query example.
3. Never use query loss, query accuracy, or query labels for checkpoint selection,
   early stopping, normalization statistics, or prompt construction.
4. Rebuild prompts independently for each episode; do not carry state between
   subjects unless an experiment explicitly defines a meta-trained initialization.
5. Save prompt count, embedding width, support indices, class order, seed, and
   parameter digest in the run record.

## First implementation test

Use a stand-in transformer with a known embedding width. Confirm that generated
prompts have the contracted shape, change the model output, receive gradients from
support loss, and remain bitwise unchanged during query-only evaluation.
