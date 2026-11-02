# LQ19 SC1 source-only successor

Implements the selected [SC1 design](../../../docs/phase2/cho51_p3_startup_cost_v1/README.md)
changes in a successor to LQ18. The retained reader uses invocation-local hash
scratch while preserving all reads/checkpoints and fresh hash passes. Guard uses
a declared64-byte memory-status layout and a new zeroed instance for every RAM
sample; all native queries, thresholds, stop checks and watchdog behavior remain.

The caller, supervisor main and child main refuse before dispatch. The retained
QD body, old protocol and source roster are inert reference/library code in this
version. They are not a complete-Q runner or a second QD admission. P is disabled.
Full-Q timing/output feasibility remains NOT_ESTABLISHED.

test_sc1.py adds19 supplied-call methods (11 hash,8 memory). They and the10
TimingFormatTests remain unexecuted. Real native I/O/ABI/fault/sharing/custody
coverage remains separate. H10's native limits/sharing obligations are retained
in the inherited sources, not discharged by these injected-call methods. Nested
sample tests establish no real thread/watchdog qualification.

The held516 legacy identities,10 QD methods,36 diagnostic scenarios and40 planned
SC scenarios remain distinct obligations. A complete reviewed discovery partition,
bounded qualification runner, capture/output budget and fresh admission are still
required. No changed-source qualification, speedup, native custody, continuation,
candidate117/V34 or scientific result is claimed by this source implementation.
