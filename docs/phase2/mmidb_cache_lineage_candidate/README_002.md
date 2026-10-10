# Diagnostic revision 002

The initial guarded synthetic runtime probe exited 1, with a clean released
Job and approximately 1.04 GiB peak aggregate commit. Its worker traceback
was not captured; no real reconstruction was admitted or executed. The exact
failed worker, plan, guard and receipts remain untouched.

This fresh revision adds worker-owned stdout/stderr and exception receipts,
with import progress. It retains all processing, comparison tolerances,
network/write restrictions, original case boundaries and resource limits
specified in README.md. The first probe attempt remains spent; this is one
separately reviewed diagnostic-revision probe, not a reset of that admission.
The real reconstruction still requires a successful measured probe and a
fresh exact admission. No model/case, scientific acceptance, or broader
subject scope is provided.
