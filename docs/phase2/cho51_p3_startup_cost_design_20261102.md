# Startup-cost design, complete-Q feasibility and fixed-slot ownership

2 November 2026. Engineering design only; P disabled. The exact
[six-file SC1 package](cho51_p3_startup_cost_v1/README.md) has
[independent design acceptance](../../runs/coordination/cho51_p3_startup_cost_design_20261102_v1/design-review-v3.json).
It selects two bounded allocation improvements and fixes metadata publication
ownership. **Complete-Q timing and output feasibility remain NOT_ESTABLISHED.**
No implementation, runtime operation, tests, qualification or admission occurred.

## Selected improvements and their limits

- Reuse a single invocation-local read buffer and counter within each retained
  hash pass. Keep every actual read, rewind, fresh hash, before/after guard,
  EOF/growth/short-read check and independently owned returned byte chunk.
- Declare the64-byte RAM-status layout once while creating fresh storage for
  every sample. Keep all live sensor calls, thresholds, watchdog behavior,
  stop/time/custody checks and separate foreground/watchdog observations.

The [source map](cho51_p3_startup_cost_v1/source-map.json) binds28 exact source
and evidence inputs. It identifies allocation repetition without inferring a
measured speedup. Repeated original-file hashes, read_small's two passes,
S14 whole-reader verification, S17 final verification and both runtime censuses
remain. In particular, S14's5.0341002-second QD span includes whole-reader
verification; it is not an isolated PE-parser benchmark. Sensor caching,
checkpoint removal, old census/artifact reuse and preclock work are rejected.

The earlier QD run remains INCOMPLETE_REFUSED for17/16 closeout accounting
units. Its reviewed prefix37.7609334 and external45.4523028 seconds imply a
nonoverlapping7.6913694-second tail. Using those observations alone would leave
14.5476972 seconds before work60 for missing Q work, or12.5476972 with an
illustrative2-second planning margin. These subtractions do not bound the
unmeasured children, controls, full-Q final output/verification or variance.
The [feasibility record](cho51_p3_startup_cost_v1/feasibility.json) keeps those
unknowns explicit. The sum of mode caps is not a runtime lower bound either;
full Q is not proven impossible, and it is not ready for admission.

The preserved disjoint32/100/384 rosters contain516 methods. The10 QD methods
added afterward need explicit additional coverage: copying the old collector
would break its exact384 inherited gate. Every cohort retains its eight UTC,
two fault, five native observer, two bootstrap and three sharing controls, full
final verification and owned closure. The36 diagnostic scenarios remain distinct
unexecuted obligations. SC1 adds40 planned scenarios, not40 implemented methods.
New namespace IDs, exact full discovery partition and a bounded qualification
runner still require implementation-specific review.

## Fixed metadata ownership and resolved findings

Root is the sole operation-metadata publisher. Reviewers return bounded messages
and confirm the exact published bytes; they create no operation files. The
[ownership design](cho51_p3_startup_cost_v1/metadata-ownership.json) retains16 fixed
roles and3,293,184 reserved bytes within16 files/4MiB, with no release, reassignment,
overflow sidecar, temporary file, overwrite or fallback writer. Complete escaped
tool capture and failure envelopes must fit their own slots before admission;
a runtime stream cap alone does not establish that serialized capture will fit.

Three independent findings were resolved and the earlier drafts remain preserved:

| Finding | Final design rule |
| --- | --- |
| SC-D1: circular ledger bootstrap | A reviewed complete in-memory reservation authorizes allocation-only CreateNew; verified original readback/closure yields the immutable ledger pin required by later roles. Bootstrap failure consumes all charges and prohibits later creates/runtime. |
| SC-D2: confirmation had no fixed destination | Source confirmation goes in contract_adoption; actual-review confirmation goes in root_disposition. Each has an8,192-byte envelope inside its existing cap; absent/mismatched/oversized/consumed destinations refuse adoption. |
| SC-D3: one-link check preceded file creation | Check ancestry/path/absence/authority/size/reservation before create; check the returned original file's type/link count/final path/native identity immediately after exclusive create and before payload writing. Final original readback/ancestry/closure checks remain. |

The reviewer `qd_source_review` authored the independent conclusions. Root
published their exact messages with attribution and text digests, and the peer
confirmed the saved bytes. The [Root design acceptance](../../runs/coordination/cho51_p3_startup_cost_design_20261102_v1/root-design-acceptance.json)
adopts only that design scope. Old QD files, its extra review note and all16 old
reservations are unchanged; nothing here repairs that consumed operation.

## Validation and next bounded step

Validation for this step is file/text/JSON/hash/link inspection only. Six design
files and28 reference pins were checked, the516 held methods and10 additions
were accounted for, and40 SC scenarios and the16-slot byte sum were checked.
The [pre-step archive](../history/startup_cost_design_20261102/manifest.json)
preserves12 prior active pages. The preservation baseline covers8,607 files;
the two six-file rejected drafts also remain exact. A separate reviewer checks
the metadata/documentation closeout. None of these checks is an executed test.

Next is source-only implementation and independent review of the selected
scratch/layout changes and the fixed-slot publisher in a new versioned successor.
Frozen LP18/LQ18/lplan15 stay unchanged. Qualification-runner design, complete
roster/output bounds and evidence-based timing assessment remain separate gates.
Do not issue full Q or a second QD merely because the design is accepted.
Keep original child55/work60/cleanup5/hard65/whole90 and all tighter limits,
memory/disk/freshness/stop/thread/device and native custody controls.

P stays disabled. All18,793 resolver rows,13,406 inventory occurrences,724 queues,
1,782 frontiers,1,786 binding loads and3,972 effects remain open. Complete
continuation remains INFEASIBLE_UNDER_CURRENT_GUARDS (at least31,002 rows
against24,000); conditional node/raw-byte findings retain scope. G2 is
INCOMPLETE_REFUSED. No original-package-path custody, continued state or debt
discharge is established. Historical UNKNOWN custody and all failed attempts
remain. Candidate117/V34 and science are unexecuted, scientific cells0/1020,
freeze unsigned. No commit or push occurred.
