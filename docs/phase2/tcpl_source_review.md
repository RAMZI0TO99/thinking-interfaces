# TCPL bounded source-fit selection

16 September 2026, milestone 26. The bounded selection roster now covers the
local TCPL reconstruction: `adaptation.tcpl_source` fits a fresh trainer from a
pinned caller template on class-stratified bounded episodes over the permitted
source subjects and runs the complete source-only eight-fold LOSO. With this
step every method family in the bounded roster — six LaBraM methods, EEGNet,
EA-tangent and TCPL — has a selection path.

## Contract and implementation

`BCITCPLSourceSelector` accepts a fixed tuple of `TCPLSourceCandidate` entries:
source settings (steps per subject, class-balanced support/query shots per
class, explicit Adam settings) and support settings (query batch size). The
caller supplies a pinned template digest and a Profile A manifest inventory;
the selector never reinitializes the template and validates cohort, protocol
and model dimensions through the existing manifest runner before any fit.

Every fit builds a fresh `TCPLSourceTrainer` with the candidate's explicit
optimizer settings and takes one Adam step per subject episode. Episodes are
class-stratified: each step draws distinct support and query trials per class
from one permitted subject's retained Profile A trials, sized within the
eight-trial batch ceiling, with the exact trial IDs, loss decomposition and the
model state hash recorded after every step. Train-mode dropout draws from a
per-fold isolated seeded RNG, so fits repeat exactly and the caller's RNG is
untouched. Validation binds the audited episode and predicts the fixed common
queries through the frozen support-conditioned session; selection averages the
eight folds with equal weight and breaks exact rational ties by declared order.
The winner gets a fresh eight-source fit, and the returned runner owns the
fitted trainer under its declared roles.

The audited manifest runner changed additively: optional `TCPLTrainerSettings`
for its owned trainer, optional admission of a caller-owned trainer (mutually
exclusive), and a `source_state_sha256` property exposing the owned model's
evolving state. Defaults and prior behavior are unchanged; its existing tests
pass unmodified.

## The measured full-episode memory finding

The first design trained through the manifest runner's full-episode
`source_step` at the maximum audited shots, which forwards a subject's entire
fixed common-query pool (about 430 trials) with retained activations in one
step. On real BCI data that footprint requested roughly 4.3 GB in a single
attention allocation and the bounded CPU check died before completing fold one;
no evidence was written and no data or source file was affected. The episodic
TCPL trainer had previously been exercised only at toy scale. The lesson is
recorded in the contract: full-query-pool training is not a bounded CPU
workload, and the selector's episode policy field carries that finding. The
failed log is preserved beside the evidence.

## Verification

The focused suite passed **8 tests / 14 subtests**: class-balanced episodes with
per-step class coverage, both held-out subjects excluded, exact repeat and seed
isolation, complete two-candidate selection with recomputed means and
declared-order tie-breaks, optimizer settings reaching the owned trainer,
immutable write-once evidence, roster/settings/ceiling/role rejections before
execution, and corruption fail-closed behavior.

The real-data check declared two candidates before selection: one-plus-one-shot
class-balanced episodes (eight trials per step), one step per subject per fit,
Adam rates 0.001 and 0.0005 with weight decay and prompt penalty 1e-4, query
batches of eight, template/sampling seed 23 and a 200-step ceiling. Selection
completed **16 inner folds** with 7,924 common-query predictions, a fresh final
eight-source fit and an exact repeated first fold. Including the repeat, work
totaled **127 Adam steps over eight-trial episodes**, with **zero outer-target
predictions**. Caller template, RNG, source identity and all original input and
audit hashes were preserved.

Full lint and strict types pass. The exact-source suite passes **527 tests / 873
subtests**, with the same four existing warnings; raw results are retained in
the receipt. Evidence directory:
`runs/phase2/tcpl_source_checks/20260916_step26/`.
Current source fingerprint:
`59eda9438085b6533a8d6aa1431736ff5c1e3716b5660633911768b1ccc4ce8c`.
The TCPL selector and its tests are new; `adaptation/tcpl_manifest.py` changed
additively as described above.

## Next work and unchanged limits

The bounded BCI selection roster is now method-complete at the engineering
level. Next are broader dataset coverage (Cho2017 is the primary E2 dataset and
has no Profile B binding yet), the scientific run/history recorder, and the
measured P3 pilot that freezes the scientific contract. P2 remains partial; the
RAM-dependent control refresh stays deferred. No guard, method configuration,
scientific comparison or gate changed, and no full scientific experiment ran.
