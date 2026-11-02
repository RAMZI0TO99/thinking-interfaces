# P3 boundary diagnostics and verifier implementation

28 October 2026. Engineering-only implementation and bounded validation.

The [new source package](../../tools/custody_boundary/v1/README.md) implements a
strict byte verifier, a bounded Windows raw-diagnostic collector and a new fixed
validation runner. It does **not** implement a qualified positive custody
boundary or successor006. Bootstrap004 remains FAILED_UNRELEASED_CONSUMED and
diagnostics005 remains launch-held.

## Implemented and exercised

- Strict JSON, immutable schema pins, duplicate/nonfinite/type/date/size limits,
  historical hashes and false flags, normalized artifact names, byte/digest
  checks, QPC arithmetic and selected temporal/disposition/admission joins.
- A refusal-only operational artifact interface. The pure core accepts supplied
  bytes for inspection; it does not authenticate a Windows file, host or reviewer.
  Forged positive metadata cannot enable eligibility or launch authority.
- Bounded Event Log XML and local-clock collection, retaining errors, truncation
  and its explicit UNRESOLVED outcome. No restart, process enumeration, service
  change or scientific workload is performed.
- A separately reviewed fixed runner with anonymous atomic Job assignment,
  suspended start, verified memory caps, retained process handles, stop/resource
  checks, a deadline watchdog, immutable attempt claims and bounded output.

Sol6.1 authored the verifier/tests; Root authored the collector/runner. A separate
Sol6.1 reviewer accepted the exact17 source/fixture inputs. Five review findings
were resolved: cached-bytecode provenance, anonymous Job isolation, output
directory-handle lifetime, final stop/window checks and accurate thread wording.
The source and actual-result reviews are separate records.

| Operation | Actual result | Scope |
| --- | --- | --- |
| `c1fdd56a-7fb2-4fc1-96aa-99164bf489e5` | 25 tests passed; zero failures, errors or skips; runner4.531s | Adversarial byte-verifier subset only |
| `e9ad5105-478e-4d96-9aac-56915a3b8d0f` | 32 raw events retained; truncation=true; selected query not exhausted; no collection errors; runner4.031s | Successful bounded diagnostic capture, UNRESOLVED boundary |

Both actual caller exits were0. Receipts report verified atomic Job membership,
an empty Job before close, original-process exit after close, closed process and
thread handles, and no cleanup or peak-sampling errors. These facts apply only
to the two new operations. They do not repair historical004 custody.

The fresh scope used4GiB available RAM at startup/active,20GiB free disk,
512MiB process/768MiB Job caps,45seconds child/90seconds whole caller,1MiB output,
one CPU/library worker and hidden GPUs. The parent also has a deadline watchdog.
732 base-runtime files were pinned. A fresh absent bytecode-cache prefix was
used for both parent and child because `-B` alone does not prevent cache reads.
This envelope does not amend the proposed006 bootstrap's10GiB startup floor.

## Evidence and acceptance

Phase records reside in
[`runs/coordination/cho51_p3_boundary_impl_20261028_v1`](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1):

- [Independent source review](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/source-review.json)
- [Tests admission](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/tests-admission_001.json),
  [actual caller audit](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/tests-external-audit_001.json)
  and [complete test payload](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/attempts/c1fdd56a-7fb2-4fc1-96aa-99164bf489e5/payload.json)
- [Collection admission](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/collect-admission_001.json),
  [actual caller audit](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/collect-external-audit_001.json)
  and [collection receipt](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/attempts/e9ad5105-478e-4d96-9aac-56915a3b8d0f/receipt.json)
- [Independent actual-result review](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/actual-review.json)
- [Root acceptance of that exact review](../../runs/coordination/cho51_p3_boundary_impl_20261028_v1/root-qualification.json)

The independent outcome is ACCEPTED_FIXTURE_AND_TRUNCATED_DIAGNOSTIC_RESULTS;
Root adopted it after rechecking all22 saved artifact pins. External before-to-
post-return QPC upper bounds were25.9876769s for tests and23.4793618s for capture,
both within90seconds. Raw capture retained26,420 UTF-8 XML bytes, all32 hashes
verified. These are engineering-operation results, not a boundary qualification.

The runner's saved pending-review flags are historical and remain unchanged;
the later independent review records their resolution. The88 predecessor files,
including the sealed design/contracts, remain exact. Original48 design scenarios
are not claimed fully executed by the25 subset tests. The original117 metadata/
telemetry tests and34 controls remain unexecuted. Scientific cells remain0/1020
and the final freeze is unsigned.

## Remaining work and next step

The [provider assessment](cho51_p3_boundary_providers_20261028.md) records the
Microsoft documentation and limits. The raw query reached its32-row cap, so it
does not even claim completeness of the selected event history. No old-event
host association, independently qualified restart kind, cross-boot ordering or
persisted-domain exclusion has been established. No restart is requested.

Next implement and qualify the **authenticated artifact reader and auxiliary
provenance/review joins**, then a focused bounded provider qualification capable
of resolving the stated evidence gaps. Keep the positive path disabled until
actual evidence supports it. Successor006, native preparation and the original
contract tests follow only after the relevant boundary is independently accepted.
The remaining work is substantial; these tests certify the implemented negative
checks and this collector's bounded diagnostic behavior, not the full design.
