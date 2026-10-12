# Gate A: evidence review and proposed retrospective criterion

12 October 2026 UTC. The completed reference study supports a bounded
reproduction of the linked reference procedure. It does not establish numerical
equivalence to the published result or identity with the original 2024 runtime.
Formal Gate A is still unsigned. This proposal requires the owner's direct
scientific acceptance decision; root's engineering delegation does not sign it.

## Evidence and limits

| Item | Retained evidence | Limit |
| --- | --- | --- |
| Reference procedure | BCI IV-2a left/right-hand, within-session five-fold evaluation; upstream Keras EEGNet-8,2 and explicitly pinned preprocessing, training, splits and environment. | The retained review pins implementation commit507a4ccc from2025, later than the2024 study. |
| Complete historical grid | 450 declared fits:90 seed42 anchors and360 repeat-seed fits;9 subjects,2 sessions and5 folds. Original record snapshot `196b419bf2f15c02fd55b9046fd78260605e2be869e3695bb09196616921427e`. | These are9 participant units, not450 independent observations. |
| Historical record/input checks | Final record integrity and independent MAT/event/epoch-orchestration audit report complete coverage and zero mismatches. Both dated1 September. | The input audit shares pinned MNE/sklearn primitives; it is not an independent numerical-library implementation or confound clearance. |
| Published comparator |77.15% mean ROC-AUC, SD19.33 percentage points, after averaging folds within subject/session. | Published SD is descriptive; it is not an acceptance tolerance or confidence interval. |
| Retained seed42 result |75.66061980347695% mean ROC-AUC; gap -1.4893801965230491 percentage points. | It is lower than the published mean; no numerical equivalence or exact reproduction follows. |
| Repeat-seed result |75.0191798941799% subject mean; retained95% subject interval59.03977788629133–90.99858190206846%. | The interval is descriptive and is not a test or acceptance band against the published point estimate. |
| Current negative controls | Retained current-source shuffled-label9-fit mean0.4876543209876543 below0.60, and36+36 pre-cue controls below0.35. | These are EEGNet/control results, not LaBraM selector or pretraining-cohort acceptance. |

The [official MOABB table](https://moabb.neurotechx.com/docs/paper_results.html)
was checked again in this step: the comparator, metric and aggregation remain
as above. It describes expected variation with evaluation randomness; it does
not provide a numerical acceptance threshold. The
[reference investigation](../moabb_reference_reproduction.md) and
[current Gate A status](../gate_a_status.md) preserve the detailed earlier audit.
No causal explanation for the score gap is established here.

The one-time [LaBraM #75](https://github.com/935963004/LaBraM/issues/75) refresh
completed on12 October at13:08 UTC with zero comments. Actual checkpoint
recording coverage and evaluation overlap remain unknown. That question is
independent of this EEGNet baseline acceptance decision.

## Exact proposed amendment for owner review

> Accept Gate A as a retrospectively adopted, process-based baseline criterion:
> accept the completed and historically audited linked-procedure EEGNet
> reproduction and its negative controls as a usable reference baseline, while
> reporting the published0.7715 ROC-AUC, retained seed42 result0.7566061980347695
> and their -0.014893801965230491 gap. Do not claim exact numerical reproduction,
> statistical equivalence, an original2024 runtime match or a pre-existing
> acceptance tolerance. This decision does not accept checkpoint-cohort
> independence, sign the experiment freeze, admit training or reset the original
> exhausted case.

This would be an **explicit amendment of the Gate A acceptance condition**,
adopted after the historical results were known. It cannot be described as
passing a numerical criterion that was specified before those results. The
scientific owner can instead keep Gate A unsigned or require a separately
defined new reproduction protocol. No option changes existing scores or turns
published SD into a threshold. The amendment is a defensible narrow operational
baseline decision; it is not proof of the stronger original numerical claim.

## This step's execution state

The read-only issue collection passed in Job20261012T130847Z_1fc7a4ded7.
A separately prepared re-audit would recheck all450 saved record hashes,
configuration/identity/split fields and ROC-AUC arithmetic from retained
probabilities without EEG reads or fitting. Its admission
20261012T131425Z_1975510152 refused before a child or Job was created:
7.708 GiB available RAM versus the unchanged10 GiB startup floor. **That
re-audit did not execute and has no passing result.** The prepared recipe and
refusal are preserved, with no overwrite or relaxed floor.

The proposed acceptance relies on the dated retained evidence, not a new
current-source fit, raw-input replay or executed re-audit. The worker-specific
runtime/environment preparation is likewise unexecuted in this step; it needs
fresh admitted resources and its own finite scope. No watcher is armed.
The [portable evidence packet](../../evidence/gate-a-review-20261012/README.md)
distinguishes the successful read, historical evidence, proposed amendment and
unexecuted audit.

Canonical Source3114ec43/432, the original owner packet, four adopted design
choices and all13 live configuration pins remain unchanged. Gate A and the
experiment freeze remain unsigned; no scientific execution budget is admitted.
The original LaBraM case still has two spent attempts and zero remaining.
Any direct owner adoption needs a separate successor decision receipt naming
this exact amendment; no acceptance is inferred from preparing or publishing it.
