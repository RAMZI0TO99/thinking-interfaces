# Delegated decision resolution: analysis and adopted choices

19 September 2026, milestone 37. Following the user's instruction
"i want you to analyze the best decisions and make them for me" together with
the standing instruction "do not push anything to github or gitlab until i
tell you to", this document analyzes every open execution decision, adopts
the choices an agent can defensibly make, and records what only the owner can
still change. The delegation itself is recorded in the deviation log; it is
not converted into scientific sign-off or compute admission.

## Measured facts the decisions rest on

- Live machine guard: **17.59 GiB free disk against the unchanged 20 GiB
  floor (storage fails)**; GPU 12,282 MiB (passes); free host RAM 4.08 GiB
  (passes the executor's 4 GiB floor, far below the control refresh's 10 GiB
  startup guard). The measured pilot fails compute admission on disk alone
  today, independent of any operator choice.
- Git: the working tree sits at `e378dfd` (Phase I) with the entire Phase II
  surface uncommitted by design; nothing has been pushed and nothing will be
  until the owner says so.
- Reference reproduction: seed-42 mean 75.6606% ROC-AUC versus the published
  77.15%, with 450/450 protocol-matched fits passing their audits and no
  acceptance rule ever adopted.
- No prediction score has been read for any Phase II method; all engineering
  fold scores recorded so far are one-step chance-level verifications.

## D01 — Gate A status: REMAINS EXPLORATORY/UNSIGNED (adopted)

Options considered: (a) adopt a tolerance band and accept — rejected because
any band chosen now would be constructed after observing the 75.66 vs 77.15
result, the exact post-hoc thresholding the evidence discipline forbids;
(b) declare failure — rejected because the protocol-matched grid completed
and audits found no implementation error, and a failure declaration would
equally require a pre-registered criterion that never existed; (c) remain
exploratory — adopted. This is the only choice that adds no result-aware
judgment, costs nothing (Phase II proceeds exactly as it has), and stays
reversible: the owner can still supply an independent, pre-registered
rationale either way. An agent approving its own work's scientific acceptance
is precisely the conversion this project forbids.

## D02 — Support pool: FIXED-EARLIEST KEPT (adopted)

The v2 default (nested fixed-earliest 1/5/10/20 per class, maximum pool
excluded from every query set, training seeds never resample support) is
implemented, audited at every shot level on all three datasets, and was
adopted before any score existed, so no result-awareness contaminates it.
Switching to a seeded pool now would invalidate every partition, episode and
binding audit from milestones 14-36 and purchase nothing. The recorded Cho
loader-order caution (order is not proven acquisition chronology) stands.

## D03 — Roster: STRUCTURAL DRAFT FREEZE CONFIRMED; BUDGETS STAY POST-PILOT (adopted)

Structural content confirmed as the planned freeze: nine systems (six
same-backbone LaBraM methods, TCPL as a separate architecture, EEGNet and
EA-tangent anchors); primary comparison LoRA minus linear probe on Cho2017 at
five shots with model seeds 11/23/37/53/71; subject as the inferential unit;
exact-rational balanced accuracy. Optimizer/search budgets, stopping rules,
candidate counts and multiplicity families remain **unfrozen**: their declared
status is pending verified implementation and runtime pilot cost, and
inventing numbers now would fabricate a scientific configuration. The actual
freeze happens after the measured pilot, per the plan's own sequencing.

## D04 — TUAB/TUEV: UNCHANGED (adopted)

External dataset access is not an agent-creatable resource. Parity remains on
the documented weaker route (pinned reference bytes, 119 exact stage
comparisons; strict float32 joint-permutation invariance fails with the
supplemental float64 diagnosis passing, all visible). No external downstream
reproduction is claimed.

## D05 — E1: UNCHANGED, STILL BLOCKED (adopted)

No verified compatible tokenizer or masked-prediction path exists. Missing
assets do not authorize a substitute loss or a completion claim.

## D06 — Operations and compute admission: PILOT BLOCKED BY THE MACHINE GUARD (adopted)

One agent, bounded work, unchanged. Operator compute admission for the
measured pilot is **not self-granted**, for two independent reasons: the
machine guard genuinely fails today (17.59 GiB < 20 GiB floor), and a
delegation to "analyze and decide" does not override an unchanged resource
guard. The path to unblocking: the owner frees disk above the floor (project
junk — tmp, caches — has already been cleaned; the remaining large consumers
are pinned raw datasets and audited artifacts the discipline preserves), or
supplies a documented below-floor deviation. GPU capacity already passes.

## Standing instructions recorded

- **No push to GitHub or GitLab until the owner says so** (user instruction,
  19 September 2026). No commit exists to push in any case: the RAM-deferred
  control refresh (0/45 current-source fits, 10 GiB startup guard vs 4.08 GiB
  free) gates every checked commit, and that guard is unchanged.
- The decision delegation is recorded as a deviation, not as Gate A approval
  or compute admission.

## What only the owner can still change

D01's formal resolution (a pre-registered acceptance rationale either way),
below-floor operation for the pilot, disk freeing, TUAB/TUEV access, and the
eventual push instruction. Everything else needed for the measured pilot is
built, tested and waiting.
