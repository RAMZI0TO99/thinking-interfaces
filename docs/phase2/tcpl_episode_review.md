# TCPL meta-episode and fixed-target helpers

Completed 8 September 2026. `adaptation/tcpl_episodic.py` supplies the source
meta-loss, an owned source trainer and a fixed-target session for the
[local TCPL model](tcpl_model_review.md). These are tensor-level primitives;
audited-manifest integration and scientific source training remain outstanding.
All pre-existing source/config/test files retain their before-step hashes.

## Loss and source training

`tcpl_meta_episode_loss(model, support, queries, query_targets)` returns graph-
connected total loss, query cross-entropy, weighted prompt penalty, logits and
prompts. For E dense episodes with Q queries each, it computes:

```text
mean_e [ mean_q CE(logits[e,q], labels[e,q])
         + lambda * sum_{token,coordinate} prompts[e]^2 ]
```

The prompt penalty is counted once per episode, independently of query count.
Prompt coordinates are summed, not averaged. Default lambda is `1e-4`, from the
reference inventory. The helper preserves model modes and weights and neither
clears nor accumulates parameter gradients itself; backward is caller-controlled.
The supplied queries must belong to source training. Tensor values alone cannot
establish subject permissions or disjoint trial identities.

`TCPLSourceTrainer(source_template)` owns a deep copy with all parameters trainable
and all modules in train mode. It creates one Adam optimizer for that copy and
retains its moments across calls to `step`. A newly constructed trainer resets
both model and optimizer from its supplied template. No optimizer is borrowed
from the caller or shared with target sessions.

Defaults are learning rate `1e-3`, coupled weight decay `1e-4`, and lambda `1e-4`.
The explicit local Adam choices are betas `(0.9,0.999)`, epsilon `1e-8` and no
AMSGrad. A step detaches caller inputs, computes the meta-loss, backpropagates,
checks finite gradients, and updates all owned parameter groups. It returns
detached scalar loss components. Gradients are cleared after success or failure.
Nonfinite losses/gradients are rejected before the optimizer update. Failed
calls may consume dropout RNG; arbitrary optimizer failures are not transactional.

No scheduler, stopping criterion, epoch budget or scientific search selection is
implemented. Each call is a single dense meta-batch, with uniform support/query
counts and no padding mask. Loss reduction here means aggregation of loss terms,
not an assertion of convergence or falling validation loss.

## Fixed-target inference

`TCPLTargetSession(source_model, support)` copies source weights, freezes all
parameters, switches the copy to evaluation mode and clears copied gradients.
It generates support prompts under inference mode before receiving any query.
Raw support is copied for conditioning and then discarded. No labels or optimizer
are accepted, and the caller's model modes, gradient flags and gradients are
preserved.

`session.predict(queries, query_batch_size=...)` reuses those prompts for each
query chunk and returns logits without a computation graph. Changing the original
source model, support tensor, returned logits or diagnostic `session.prompts`
copy cannot change the session's retained state. New subjects require new sessions.
Python private attributes are an API convention, not a security boundary.

The helper rejects invalid batch sizes and nonfinite generated prompts/logits.
Partition enforcement, class-balanced support sampling, preprocessing fit scope
and scientific scoring are future runner responsibilities. The local contract's
`runner_not_implemented` status remains accurate.

## Verification and evidence

Ten new tests and 22 subtests check the scalar loss formula independently using
log-sum-exp, repeated-query invariance and controls for incorrectly scaled prompt
penalties. Query cross-entropy alone still reaches support inputs and generated
prompts. The tests also establish:

- Adam parameters belong exactly to the owned model; all component groups change,
  moments advance to step two, and fresh trainers reset and reproduce a first step
  with the same dropout RNG.
- Caller source weights, modes, gradient flags and existing gradients are preserved.
  Source training does not accumulate gradients on caller support/query tensors.
- Nonfinite loss and injected nonfinite gradients cause no optimizer update and
  leave owned gradients cleared. Nonfinite target outputs are rejected.
- Target weights, prompts and queries remain unchanged across predictions;
  caller mutations and unrelated sessions do not affect repeated predictions.
  Query batching/order checks pass at float32 `rtol=1e-5, atol=1e-6` and float64
  `rtol=atol=1e-12`. Unaffected queries/episodes remain exactly equal in the controls.

Full lint passes; strict types pass for 147 source files. Regression output:

```text
410 passed, 3 warnings, 604 subtests passed in 22.15s
```

The three warnings are the existing EEGNet deprecation and classification warning.
The initial nine focused tests passed. Type annotations, two line wraps, an
additional penalty-scaling assertion and a nonfinite-target test preceded the
final run; no behavioral correction or tolerance relaxation was needed.

Evidence: `runs/phase2/tcpl_episode_checks/20260908T140448227020Z/receipt.json`,
with adjacent lint/type/test logs. Validation source fingerprint:
`d4997e37dad0d84731f54112af7e22d6b323fd19f194504047d5085565443d77`.
Git HEAD remains `e378dfd5f65e53b7ae7da62c778e829b60c61b98`, dirty and uncommitted.

Next bounded step: bind these helpers to audited trial catalogs and episode
manifests, enforcing outer-subject exclusion and support/query identities before
tensor execution. Use bounded checks before any scientific source fitting.

The final storage snapshot is 7.75 GiB free, below the unchanged 20 GiB training
floor. No heavy training, source-bound control refresh or scientific gate approval
occurred. Author parity and the reference protocol questions remain unresolved.
