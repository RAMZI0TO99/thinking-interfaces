# Pilot target-case executor: admission, adapters and capped cases

17 September 2026, milestone 28. `evaluation.phase2_pilot.py` completes the last
code-only layer before the measured P3 pilot: fail-closed compute admission,
method adapters for the full nine-method roster, and a target-case executor
that claims a case, verifies its cell identity against the live source and
environment, predicts the outer target's fixed common queries through the
existing audited runners, derives exact-rational metrics and publishes the
evaluation cell with staged timings. The measured pilot itself remains
unexecuted and unadmitted.

## Contract and implementation

`machine_snapshot()` reads the unchanged `configs/base.toml` disk floor and GPU
minimum plus the pilot specification's 4 GiB host-RAM floor; reads are
injectable so the fail-closed logic is testable without mutating the host.
`compute_admission()` requires an explicit operator decision AND passing
machine guards; either alone refuses. Caps are carried from the specification:
ten minutes of active work per probe and two hours for the first pilot session.

Adapters wrap the audited runners without re-implementing them:
`LaBraMTunedAdapter` (linear/partial/full selected fits), `TrainedLaBraMAdapter`
(effective-QKV LoRA, post-block adapters, support-prompt containers),
`TCPLAdapter` (a final outer-role TCPL runner only) and `AnchorAdapter` (EEGNet
with its fitted model, EA-tangent with its classical settings). Each returns a
`CaseOutcome` with logits, targets, bound trial ids, the episode digest, the
fitted-state digest and its own stage timing.

`TargetCaseExecutor.run_case` refuses, in order and before any claim: missing
compute admission, an exhausted session cap, adapter/identity/plan mismatches
(method, target subject, shot level, model seed), a method-configuration
digest that differs from the cell identity, a declared episode that differs
from the audited episode record, and a cell identity that does not match the
live source fingerprint, Git identity or environment digest. It then claims the
case, predicts, re-checks that the bound episode still matches, and publishes
the cell through the run recorder with claim/persist and adapter stage timings.
Any case failure is recorded as an immutable failure record and re-raised; a
case that exceeds the probe cap records a cap failure and publishes nothing.
The recorder's own metric verification (exact-rational recall, cited selection
evidence, positive query counts) applies unchanged to every published cell.

## Verification

The focused suite passed **6 tests / 8 subtests**: fail-closed admission with
injectable disk and GPU reads; a complete plain-LaBraM case publishing a
verified cell with recomputable rational metrics and three stage timings; all
pre-claim refusals leaving the claims directory empty; failure recording plus
probe- and session-cap refusals on distinct case repetitions; EA-tangent and
EEGNet adapters predicting the outer target over the fixed common queries; and
the TCPL adapter rejecting an inner-validation runner while a final runner
predicts. The trained LoRA/adapter/prompt adapter paths reuse the same runner
construction verified by their own milestone suites.

The real-machine check took a live admission snapshot under the unchanged
guards, confirmed that admission refuses without the operator decision whether
or not the machine guards pass, digested nine explicit method configurations
(all four declared fields present; incomplete configurations refused), mapped
every roster method to its adapter, enumerated the 54 measurable BCI pilot
cases, assembled a sample cell identity from live digests, and verified that
the unadmitted executor refuses before any claim, prediction or cell. **Zero
claims, zero cells and zero outer-target predictions** occurred; no source or
data file changed.

Full lint and strict types pass. The exact-source suite passes **541 tests /
907 subtests**, with the same four existing warnings; raw results are retained
in the receipt. Evidence directory:
`runs/phase2/pilot_executor_checks/20260917_step28/`.
Current source fingerprint:
`4b202213194c710e2b1ce8cd17dded7665b015566e279c110e6776a4c538dbba`.
The executor module and its tests are new; no pre-existing source/config/test
file changed this milestone.

## Next work and unchanged limits

The bounded engineering track is now complete end to end: partitions, encoders,
nine selection paths, the run recorder and the target-case executor. What
remains before any measured run is user-owned: the D01-D06 register decisions,
operator compute admission with passing machine guards, the scientific freeze
of candidate counts and settings, Cho2017/MMIDB Profile B preparation (disk
headroom), and the RAM-deferred control refresh before any checked commit.
P2 remains partial; no gate or guard changed and no scientific experiment ran.
