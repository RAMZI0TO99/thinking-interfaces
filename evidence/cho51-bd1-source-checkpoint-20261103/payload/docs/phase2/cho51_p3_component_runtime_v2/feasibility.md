# Capacity and feasibility disposition

## What source inspection establishes

All 216 selected method bodies and their named local helpers have direct review.
This completes the direct-method index, not the recursive runtime effect proof.
Normal successful subtest callbacks are:

| Group | Methods | Subtest callbacks |
| --- | ---: | ---: |
| CM1 collection / protocol | 16 / 16 | 32 / 11 |
| HB collection / common / frames / joins / refusal | 14 / 13 / 38 / 25 / 30 | 36 / 16 / 0 / 51 / 0 |
| SC hash-RAM / publisher | 19 / 35 | 12 / 52 |
| QD timing | 10 | 0 |
| Total | 216 | 210 |

Under the proposed mapping, 216 starts + 216 primary PASS + 216 ends + 210 SUBPASS
+ header/footer = **860 records**, below 4,096. At 512 bytes each this is at most
**440,320 event bytes**, below 2,097,152. There are 3,236 remaining record slots,
but that arithmetic does not reserve or prove a complete failure path. The old
650-record synthetic transcript omits actual subtest callbacks; it remains a
valid supplied-model fixture, not a normal runtime event-count proof.

The eight shared surfaces/40 normal patch applications reconcile with the frozen
source map, separately from three fake-instance patches and one disposable fake
assignment. Real ctypes allocation/layout/copy, the 16 MiB hash case, RLock and
datetime.now remain real work. Model file paths, native identities and reserved
bytes are not actual files, handles or resource measurements. The 1,048,577-byte
CaptureModel test input is not evidence of actual stdout overflow.

## What prevents a positive feasibility decision

- The source skeleton is now 72 project modules plus 14 parents. Direct import
  statements are indexed, but recursive stdlib/bootstrap/native edges and their
  loaded identities are incomplete. A count of project sources is not closure.
- Every complete failure/cleanup/exception/trace-depth bound remains open. The
  result callback replacement cannot remove pre-result SkipTest formatting,
  assertion/mock formatting or helper str(error) allocation. No bound is inferred
  from a slice applied after formatting. Exact eligible exception domains or
  separately reviewed successors must resolve these obligations.
- Complete raw producer/transport capture remains NOT_ESTABLISHED. The preserved
  1 MiB control-character example can need 6,291,456 escaped bytes before tool
  envelopes, exceeding the existing return slots. This disproves a universal
  fit claim for unrestricted raw bytes in that JSON representation; it does not
  prove the fixed selected normal test run emits those bytes. A small success
  descriptor cannot replace original failure/cancellation/tool output.
- The 30-report / 17,711,104-byte allocation is only a minimum. Native/bootstrap,
  compiler, guard, temporary/cache and exact parent publication effects require
  individually named allocations. No unnamed sidecar, off-ledger file or reused
  closeout slot may close the gap.
- Original native enforcement, retained custody, durable operation consumption,
  complete parent attribution and the finite asynchronous review lifecycle remain
  unavailable. Proposed loader/producer objects do not supply those capabilities.
- No source-to-wall-time or peak-memory proof is established. Keep original
  whole90/work60/cleanup5/hard65/child55, startup5, sample gap200ms/freshness250ms,
  process512MiB/Job768MiB, available RAM4GiB/disk20GiB, one CPU/library thread,
  hidden GPUs and all owned-stop controls. Final-verification and closure reserves
  F/M remain unproved; child deadline is min(T0+55,T0+60-F-M), never a reset clock.

Disposition: **NORMAL_EVENT_ENVELOPE_SOURCE_ESTABLISHED_CONDITIONALLY**;
**COMPLETE_OPERATION_FEASIBILITY_NOT_ESTABLISHED** and operational admission
**REFUSED_UNADMITTED**. This is a completed negative readiness assessment with
named missing proofs, not a claim that all failure obligations have been closed
or that execution is fundamentally impossible under any reviewed successor.

## Bounded implementation route

Next, implement only supplied retained-byte/code-table reconciliation and a
callback/suite state adapter with strict default refusal, plus independently
reviewed adversarial model coverage. Freeze any new test identities through an
explicit roster successor before source acceptance; CM2 adds none. Do not add a
live importer/producer integration or execute discovery as part of that task.
Resolve the identified failure-domain/transport and native/provider/lifecycle
gates in separately reviewed work. A later real component operation needs exact
source/runtime pins, complete finite effects/allocation, all feasibility proofs,
fresh local admission and separate actual review. Full Q and P remain held.

All original obligations remain: Q32/100/384 with every mode/control; 26 local,
24 HB,40 SC and36 diagnostic scenarios; candidate117/V34; 18,793 resolver rows,
13,406 occurrences,724 queues,1,782 frontiers,1,786 loads,3,972 effects. Complete
continuation remains infeasible at >=31,002 rows against24,000 and G2 remains
INCOMPLETE_REFUSED. QD a1f12701 retains its 17/16 refusal, historical UNKNOWN
custody and consumed attempts remain, science stays0/1020 and freeze unsigned.
