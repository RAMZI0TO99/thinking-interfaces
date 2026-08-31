# TCPL reproduction plan

This is a build specification, not a claim that TCPL has been reproduced.

## Fixed interpretation

The support set is encoded without query access. Support embeddings are paired
with learned label embeddings, pooled over shots, and transformed into a fixed
number of prompt tokens shaped `(batch, prompt_tokens, embedding_dim)`. Prompt
tokens are injected after patch, electrode-position, and temporal embeddings and
before transformer attention.

Two variants are predeclared: a temporal prefix inserted once before block 0,
and a per-block prefix reintroduced at every transformer block. Both use the same
support draw and token count.

## Three contradictions to isolate

1. The prose alternates between a single shared prompt and prompts generated at
   multiple layers. Both variants are therefore explicit configurations.
2. The support aggregation description does not uniquely specify whether labels
   are concatenated before or after pooling. This build embeds labels per shot,
   concatenates them with support features, then pools.
3. Reported dimensional descriptions do not uniquely determine whether prompt
   tokens replace or prefix signal tokens. This build prefixes and never removes
   signal tokens.

The reproduction comparison must vary one contradiction at a time and retain the
same folds, seeds, preprocessing, support trials, and optimizer settings.
