# Local boundary diagnostic and fixture protocol v1

This package implements rejection and raw-diagnostic paths, not a positive
machine boundary or successor006. The immutable design remains the target;
unsupported authentication and provider requirements remain explicit gaps.

Root owns this new phase and the runner/collector. A separate author owns the
pure verifier/tests; a different reviewer accepts the entire exact source set
before execution. Review and actual acceptance are separate records under
`runs/coordination/cho51_p3_boundary_impl_20261028_v1`. No old launcher is used.

The validation runner imports the existing pinned process primitive and atomic
Job adapter as library components with an unnamed Job, preventing a named-Job
collision or another process opening it by name. It launches only `child_entry.py` in `tests`
or `collect` mode. Atomic Job assignment at CreateProcess, suspended start,
kill-on-close, queried memory caps, original retained process/thread handles,
owned Job emptiness and reap checks remain required. No process is reacquired
or killed by PID. Failed/unknown custody cannot be accepted by a zero exit.

The new lightweight fixture/diagnostic workload has its own Root-issued envelope:
4GiB startup and active available RAM,20GiB disk,512MiB process/768MiB Job,
45seconds child,75seconds work and90seconds whole caller,1MiB output, one CPU/library
worker thread and hidden GPU; the parent additionally has its deadline watchdog.
This does not amend the proposed006 bootstrap's10GiB
startup requirement or the pending original contracts phase. Both startup
samples are fresh and separated by200ms. The local stop is
`runs/coordination/PROJECT_STOP.json`; present or unknown refuses/stops work.

Before invocation Root pins the exact17 source/fixture files, independent review and
the base Python3.12 runtime: executable/DLLs, standard-library `.py` files and
extension DLLs/PYDs, excluding site-packages. Use `-I -S -B` and
`-X pycache_prefix=<phase>/disabled-bytecode/<operation UUID>` for BOTH parent
and child. That unique cache prefix must be absent before execution and remain
absent through final acceptance. `-B` alone does not prevent cached bytecode
reads. No numerical,
site-package or startup customization imports. OS libraries remain the Windows
trust base; these pins do not authenticate the OS or qualify reboot evidence.
Runtime/source handles deny writes/deletes while inputs are used; ancestor
directory handles prevent renaming. These input locks do not provide the
unimplemented general historical-artifact authentication API.

Root writes a fresh admission with a <=15minute window and exact review hash.
Invocation is the pinned base Python executable, `-I -S -B` plus the fresh
`-X pycache_prefix` argument above, this runner's
absolute path, admission absolute path and its SHA256. Before dispatch Root
retains the external UTC/QPC bound and confirms no local stop. The runner claims
the UUID attempt directory atomically, checks all pins and review, then records
Start attempted before native creation. No identity is deleted, rearmed or
retried. A refusal may require a separately reviewed correction and new attempt.

The child writes one create-once bounded JSON payload. No stdout/stderr pipe
protocol is used or claimed; complete payload plus retained-handle process exit
and Job closure is the child completion protocol. Missing/partial output fails.
An independent watchdog thread exits the parent at90seconds; closing the private
noninherited Job is then the kernel fallback. Forced exit cannot produce an
accepted result. The actual caller must record it and preserve the failed
attempt; cleanup is not inferred from the watchdog action alone.
The collector never issues a boundary packet/disposition/admission, and returns
UNRESOLVED even when its raw collection completes. Enumeration completeness,
restart-kind semantics, host association, clock order and persistence exclusions
are not certified by collected XML.

After actual tool return Root preserves the real call/chunk/session identity,
actual exit and post-return UTC/QPC upper bound, then asks a different reviewer
to inspect receipts, complete payload, source/runtime pins and custody state.
The runner's accepted flag is provisional until that independent result review.
No scientific case, original117 tests/34controls or all48 design cases is implied.
