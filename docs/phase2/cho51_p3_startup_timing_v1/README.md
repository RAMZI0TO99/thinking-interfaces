# Bounded startup-timing diagnostic successor

Engineering design, 1 November 2026. Root authors the design with read-only source
mapping from timing_map. Independent acceptance applies to exact design bytes
only. There is no implementation, test execution or run admission in this step.

Choose one **QD startup-prefix investigation**, ending immediately before the
supervisor's mode loop. It observes the same caller bootstrap, native builds,
source/runtime retention and handoffs that precede the held Q suite, then performs
complete retained-input verification and owned cleanup. It never creates a suite
child, collects tests, runs the five child observer controls or the two child
fault controls. Existing caller-side checks, including eight UTC checks and two
bootstrap fixture controls, remain in the prefix. Those fixtures are not P.

QD is an explicitly incomplete investigation within implementation qualification,
not a new way to pass Q or a transition beyond Q. Its schema is disjoint from Q
acceptance. Every required probe32/100/384 cohort and control remains outstanding
for a later, separately reviewed full-Q successor. The earlier D1 diagnostic
contract, old admissions and accepted historical Q receipts grant QD no authority.

The latest probe run started its suite at 43.2992148 seconds from caller origin,
compared with 32.0767484 and 33.3629039 in earlier accepted codec runs. Its
supervisor-to-suite interval was 25.8938825 seconds. Its shorter 3.210595-second
suite-to-next-generation interval already produced 32 passing methods, three
sharing passes and six exact provisional artifacts. Full Q still failed. These
intervals locate an observation gap; they do not identify a CPU, cache, I/O,
parser or compiler cause, or prove a future timing bound.

- [Scope, custody, admission and feasibility](contract.md)
- [Closed event format](event-format.json)
- [Finite source-stage map](stages.json)
- [Implementation gates and 36 planned acceptance scenarios](qualification.md)

Use at most two fixed parent-owned journals, each at most 128 records, 512 bytes
per record including its newline, and 65,536 bytes total. Both fit within existing
output partitions. No child telemetry, shared writable handoff, new pipe, output
stream mixing, arbitrary logging, per-file events or pure-probe I/O is introduced.
Early events may remain only in bounded memory until safe journal publication;
an interrupted unpublished prefix is UNKNOWN.

All original sensors, live predicates, deadline origins, memory/disk/thread/device
limits, original handle/Job ownership, final verification and cleanup stay intact.
P is disabled. No original-package-path custody, continuation or debt discharge
is established. All 18,793 resolver rows, 13,406 inventory occurrences, 724 queues,
1,782 frontiers, 1,786 binding loads and 3,972 effects remain open. Complete
continuation remains INFEASIBLE_UNDER_CURRENT_GUARDS (at least 31,002 rows against
24,000), with conditional node/raw-byte findings unchanged. G2 is INCOMPLETE_REFUSED.

Six probe attempts remain consumed; 8bf386d1 and6f9c898c retain their distinct
UNKNOWN caller-custody outcomes, and prior131bc595 remains UNKNOWN. Candidate117,
V34 and science remain unexecuted; science is0/1020 and the freeze unsigned.
Next is implementation and independent source review of this diagnostic only,
then a separately reviewed fresh QD admission if its exact source/allocation and
cleanup gates are met. No unchanged-source Q retry is inferred.
