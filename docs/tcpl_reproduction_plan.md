# TCPL reproduction plan and source review

Reviewed 2026-08-31. The original Full Project Plan section 5.2 is absent, so
its exact three objections cannot be reconstructed. The earlier uncited list
of alleged contradictions is withdrawn; it is not evidence about the paper.

## Published implementation and three consistency checks

The current paper specifies a two-convolution support encoder, mean support
pooling, a ReLU MLP, ten 64-dimensional prompts, four TCN blocks and four
Transformer layers. Support-label embeddings are not specified in that generator.
Meta-training jointly updates backbone, support encoder and generator; inference
uses the support-conditioned fixed backbone. [Wang et al., sections 2.2-2.6](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1689286/full).

1. Section 2.2 retains a raw-channel equation but explicitly resolves the
   implementation to temporal prefixes after TCN processing. Treat this as a
   clarified description, not evidence for replacing signal tokens.
2. Section 3.5 specifies LOSO for nine-subject BCI2a, whereas section 4.1 describes
   ten-fold evaluation across all datasets. The reported BCI protocol needs
   reconciliation before numeric reproduction.
3. The introduction/results refer to two datasets while the materials and main
   table contain three. This editorial inconsistency does not determine which
   subject-level results were actually computed. [Primary article](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1689286/full).

## Local decisions, not claims copied from the paper

The current prototype uses label embeddings, GELU, four prompts, and a generic
stand-in. Its two injection modes are local variants, not two established TCPL
implementations. No main benchmark result comes from this prototype.

A future numeric reproduction must be a separate experiment: implement the
published support encoder and TCN/Transformer, document the resolved subject
splits and class inventory, keep target query data out of adaptation and
normalization fitting, and specify validation, optimizer, stopping and seed
rules before launching. Do not tune this frozen Phase I table toward the paper's
scores. A matched TCPL run and its ablations belong to Phase II.

The source review is complete for these implementation sections. Matching the
missing Full Project Plan's exact critique and obtaining independently executable
author code remain unverified; neither is silently claimed complete.
