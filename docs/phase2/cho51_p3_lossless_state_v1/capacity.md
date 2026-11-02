# Capacity accounting and completed feasibility decision

Physical sharing is permitted only as reversible storage in the proposed format.
All semantic expansion and history predicates of the accepted kernel remain
unchanged. No compression, row packing, uncounted references, history pruning,
cross-attempt counter reset or change to the denominator is adopted.

## Exact charges

For a graph with module count M, seed count S, obligation count O, source-record
count R and edge-template count E, define `B = 2M + S + O + R + E`.
For n retained frames, let F_i, L_i and W_i be frame i's fact, link and pending
work counts. The unchanged expanded-state charges are:

```
rows(n)  = n*B + sum((n-i)*(F_i + L_i + W_i + 1), i=0..n-1)
edges(n) = n*E + sum((n-i)*L_i, i=0..n-1)
logical_pages(n) = ceil(rows(n) / 256)
```

Check every prefix and intermediate replay transition against 24,000 rows,
10,000 edges and100 logical pages. Aliasing physical bytes has no term in these
equations. At n=2 even `B <= 12,000` is only a weak necessary condition; positive
frame overhead makes the actual permitted base smaller. It is never a sufficient
feasibility test. Batch size does not change the fact that a committed successor
introduces a second retained frame.

Let C_i be the exact canonical bytes of expanded prefix snapshot i, reconstructed
with its real predecessor digest and exact retained-before counters. Require
`len(C_i) <= 8 MiB` for every prefix and
`sum(len(C_i), i=0..n-1) <= 16 MiB` for the chain. Frame i's retained-before is
the sum of earlier C lengths. Calculate the hashes and lengths in order, since
the retained-before integer's encoding and predecessor digest are part of the
later prefix. Hashes, transport byte size and a guessed JSON overhead cannot
stand in for this computation. The existing structural payload budget is an
additional independent refusal predicate, not an alternative byte estimator.

Preserve source/module/node/depth limits: 128 modules,16 MiB unique source bytes,
2 MiB per module,200,000 nodes and depth128; record counts cannot exceed asserted
node counts. Preserve128 snapshots and1,000 transitions per committed call.
All schema/ID, alias/case, seed-prefix, origin, worklist and unresolved-debt checks
remain in force. These limits apply to the entire chain, not newly stored chunks.

Transport wrappers add obligations; they cannot buy headroom. Besides the
unchanged logical and canonical predicates, the proposed consumer must charge
all actual transport bytes, manifest, historical payload copies, chunk files and
metadata to its original16 MiB resolver/state output allocation and the shared
P64 MiB/256-file allocation. Every file remains <=8 MiB. Physical transport
chunks/manifest plus any other resolver output pages must also fit100 actual
state-output pages; use the greater of that actual count and logical_pages for
the page gate. Copying raw historical indices/pages into the transport charges
their full physical bytes even if their semantics already appear in the graph.
All other P artifacts remain in the same shared allocation; there is no free
second budget for an archive or a provisional file.

The 1 MiB chunk size,64-chunk,512-asset and1,024-part limits are extra bounds,
not replacements for any of the preceding checks. Input/staging buffers and
metadata remain within native process/Job/time limits; a fit in output bytes
does not demonstrate memory or time feasibility. Input handles/files remain
fully covered by the fresh source/extras/census contract, not output counts.

## Real-case findings

The [case record](../../../runs/coordination/cho51_p3_lossless_state_design_20261101_v1/capacity-cases.json)
rechecks all136 pins of the prior accepted static occurrence observation.
Its page/tuple findings are reused as explicitly attributed evidence, not a new
source reconstruction or replay. The record contains these decisions:

| Case | Established bound | Conclusion |
|---|---|---|
| C01: full resolver first successor | At least2*15,501 =31,002 rows before further overhead | Infeasible under the unchanged24,000-row guard, regardless of lossless physical encoding |
| C02: both inventories in one initial graph |28,892 distinct historical node tuples alone | Infeasible if combined; separate historical scopes remain separate |
| C03: both raw inventories/indices copied into this uncompressed transport |20,303,658 page bytes +66,812 index bytes =20,370,470 bytes, excluding new metadata | Exceeds one16 MiB state-output allocation for this defined layout; not a canonical-snapshot byte bound |
| C04: append-only old P layout plus74 ledger pages |198+74 =272 files before new index | Exceeds256 for that append-only layout, not every layout |
| C05: illustrative small two-frame count |M=1,S=1,O=R=E=0; F=(1,1),L=(1,1),W=(1,0): rows17,edges3,pages1 | Arithmetic only; no encoded/valid fixture, bytes, replay, timing or admission established |

C01 is already decisive for the requested complete resolver continuation.
C02-C04 are explicitly conditional and cannot be used to condemn every future
representation or retrospectively invalidate separately accepted observations.
Historical page sizes cannot be substituted for canonical expanded snapshot
sizes: their schemas, wrappers and multiplicities differ. Initial resolver-only
snapshot byte/structural fit remains unmeasured and need not be executed to
establish C01. No positive real-case capacity claim follows from C05.

## Decision and next work

Design disposition: **lossless transport with equivalent refusal accounting**.
Real complete-continuation disposition: **INFEASIBLE_UNDER_CURRENT_GUARDS**.
Neither is an implementation, runtime qualification or grant to change limits.
The next authorized engineering direction is a new supplied-data-only codec,
replay/accounting verifier and refusal implementation, independently source
reviewed and qualified under fresh Q. It must remain P-disabled and cannot claim
that its small fixtures unblock the real case.

To make the complete real case feasible, something beyond lossless encoding must
change: which logical state is required, how retained history is charged, or a
capacity limit. Each would be an explicit contract/scope change, not a formatting
optimization. This task preserves all of them. No particular alternative or
raised bound is proposed as sufficient:31,002 and28,892 are only lower bounds,
and new source/transitive/effect/custody/time requirements remain unknown.

All runtime envelopes remain: Q90 whole/60 work/5 cleanup/65 hard seconds,
512/768 MiB process/Job; P300/240/5/245 seconds,4096/5120 MiB;4 GiB startup/active
RAM,20 GiB disk,one thread,hidden GPUs and local PROJECT_STOP.json. Process/Job
ownership, retained readers, complete final verification, cleanup, bounded streams,
unused operations and independent actual review remain mandatory. No runtime
operation or policy change occurs in this design step.
