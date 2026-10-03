# TCPL reference review

Reviewed 6 September 2026. This bounded review is complete; faithful architecture
and numerical reproduction remain **unverified**. The machine-readable inventory
is [tcpl_reference.toml](../../configs/phase2/tcpl_reference.toml). It is reference
metadata, not a runnable experiment configuration. Existing benchmark choices
and dataset artifacts remain in force.

## Evidence and findings

The [publisher article, sections 2.2-2.6 and Algorithm 1](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1689286/full)
specifies support-mean conditioning and prefixes after the TCN. Algorithm 1 was
visually inspected: source episodes jointly train the three parameter groups;
meta-test constructs prompts from support without backbone fine-tuning. It does
not specify a support-label embedding. Our class-conditioned LaBraM prompt path
therefore remains a separate method.

The article's Cho class inventory includes feet/rest, while the
[original Cho dataset](https://academic.oup.com/gigascience/article/6/7/gix034/3796323?login=false)
describes left/right-hand imagery. [MOABB's Cho2017 documentation](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Cho2017.html)
also exposes those two classes. This project retains two-class Cho; it must not
relabel rest recordings or invent feet trials to imitate the TCPL description.

[TCPL sections 3.4-4.1](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2025.1689286/full)
also leave BCI LOSO versus ten-fold evaluation inconsistent and the fit scope of
subject-wise normalization unclear. The latter is an ambiguity, not proof of
query leakage. Neither issue is resolved by matching reported mean accuracy.

No author implementation or checkpoint was verified in the reviewed sources.
The article promises later releases; the [author lab publication list](https://cityucompuneurolab.github.io/pub.html)
links the article without an adjacent code link. Publisher links and targeted
GitHub/title/DOI searches yielded no verified reference asset. This is a scoped
search result, not a claim that code cannot exist. The PMC mirror's direct page
returned a challenge; the publisher HTML and algorithm image supplied the review.

## Implementation decisions still needed

The inventory records published dimensions separately from unresolved settings.
A uniquely specified full model still needs support-convolution widths, temporal
downsampling, positional encoding and classifier readout, including which tokens
are pooled. Exact activation placement, normalization options and initialization
also need a declared contract. Supplying framework defaults would create a local
reconstruction, not independently verify the author's implementation.

Numerical reproduction additionally needs reconciled classes/folds, validation
and support/query identities, preprocessing fit scope, and an executable training
budget, stopping rule and seed list. Author code or a documented clarification
could resolve these; no author contact has been sent. Keep target queries out of
fitting and selection. Source-episode queries used in meta-training are distinct
from held-out target queries.

## Next bounded step

Implement the causal TCN component with an explicit **local stride-one,
length-preserving contract**, retaining configurable input channels and a
128-to-64 output projection. Document convolution/activation/residual ordering
alongside the code. This permits useful engineering work while the full-model
questions remain open; it does not settle the paper's downsampling description.

Verify future-input perturbations cannot change earlier outputs, all four
dilations and residual paths work, variable lengths preserve the declared shape,
gradients are finite, and state round-trips. Under the proposed stride-one
contract, the derived convolutional receptive field is
`1 + 2 * (3 - 1) * (1 + 2 + 4 + 8) = 61` samples. This is a local derivation,
not a measured result or a paper assertion about its actual sampling stride.

After that component, resolve the remaining constructor contract before assembling
a full model; label any unresolved local choices explicitly. Reference parity and
published-score reproduction require independent assets/protocol evidence. Large
training remains deferred under the existing storage rule.

## Validation and retained evidence

The publisher HTML and algorithm image are cached under
`.cache/phase2/tcpl-reference/20260906/`; SHA-256 identities are in the inventory.
The validation receipt is
`runs/phase2/tcpl_reference_review/20260906T074714397443Z/receipt.json`.
It checks TOML structure, cached-source hashes, dimension consistency, unresolved
readiness flags, the conditional receptive-field calculation, and unchanged
benchmark protocol. It does not validate a TCPL implementation.

Only documentation and reference metadata changed. No training or regression
suite was rerun: the previous prompt checkpoint's 375 tests / 476 subtests remain
historical evidence. This new config changes the source fingerprint; existing
source-bound controls remain stale. No scientific gate or reproduction claim
has advanced.
