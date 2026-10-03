# Cho first-tranche sweep runner considerations

Late 30 September 2026. **Owner-decision framing only; nothing here
authorizes execution.** Every engineering prerequisite from the
[isolated-case execution plan](cho_isolated_case_execution_plan_20260930.md)
is implemented and validated at source `4542cc11`: per-case isolated
verification under a verified Job commit cap, measured per-method peak
commit, and a fully passing exact-source validation chain. This note
consolidates what a future sweep runner must decide or receive before any
real case runs, so the owner conversation has one place to start.

## Decisions only the owner can make

1. **Selector scope.** The complete selector requires 5,253 gradient steps
   per case against the unchanged 256-step engineering cap. Running the
   sweep with the cap keeps engineering-bound selection; raising or
   removing it changes the scientific meaning of "selected source" and must
   be an explicit, recorded decision in the sweep configuration.
2. **Production memory cap.** The measured per-child peaks are 2.545 to
   2.667 GiB; the recommended cap is 5.5 GiB (2.06x factor). The runner's
   pinned configuration must record the ratified value and its factor.
3. **Method template and scientific freeze ratification.** Both remain
   proposed and unratified; the sweep cannot claim a frozen protocol until
   they are signed.
4. **Control-fit scheduling.** The 45 leakage-control fits (10 GiB RAM
   startup floor) and the 36 no-future fits are honest-empty inventories;
   someone must schedule them, and their results feed Gate A, not the
   tranche.
5. **Gate A.** Unsigned; nothing in the tranche resolves it.

## Engineering shape of a sweep runner (design pointer, not a plan)

- One case at a time through the existing supervised child path, with the
  ratified cap, per-case deadline leases, and the recorder/publication
  machinery already verified by the composer tests. The runner's receipt
  records per-case measured peaks, attempt counts and every refusal.
- Write-once attempt directories per session and per case, following the
  established wrapper pattern; a stopped attempt is preserved, never
  rewritten.
- The analysis side is already built: after all 1,040 cases pass
  verification, the composer constructs paired inputs all-or-nothing and
  the aggregation core averages exact cell scores by subject, method and
  shot count.

## Boundary

No real Cho fit, cell, score, report, scientific admission, commit or push
has occurred. This note changes documentation only and ratifies nothing.
