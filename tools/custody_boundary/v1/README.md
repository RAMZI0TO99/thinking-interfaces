# Custody boundary diagnostic and byte verifier v1

This is a source implementation of a bounded, negative-checking subset of the
[reviewed design](../../../docs/phase2/cho51_p3_local_custody_design_20261028.md).
It is not an accepted machine boundary, custody disposition
or successor006 controller. Bootstrap004 remains FAILED_UNRELEASED_CONSUMED;
diagnostics005 stays held. Launch and scientific authority are always false.

`collector.py` adds bounded raw Windows Event Log and local clock diagnostics.
It always returns UNRESOLVED and does not authenticate the old host or establish
restart/persistence semantics. The [provider assessment](../../../docs/phase2/cho51_p3_boundary_providers_20261028.md)
records the official documentation and remaining evidence gaps.
`validation_runner.py` and `child_entry.py` implement a separately admitted fixed
test/collection path; see [PROTOCOL.md](PROTOCOL.md). Their input locks and private
Job apply only to these operations, not to operational boundary authentication.

`verifier.py` uses only the Python standard library and performs no filesystem,
provider, subprocess or network operation. Its public byte core is:

```python
assess_boundary(packet_bytes, artifacts, contracts, *, policy_bytes=None,
                disposition_bytes=None, admission_bytes=None)
```

`artifacts` is an exact `dict[str, bytes]` of project-relative artifact names.
`contracts` is an exact `dict[str, bytes]` keyed by `boundary-evidence`,
`disposition`, `local-admission`; the used contract must match the immutable
reviewed SHA256. No caller qualification booleans or callbacks are accepted.
The returned assessment has status REFUSED or UNRESOLVED only, with reason codes,
bounded details, checked-reference count and false authority/historical-release
flags. It is a static assessment record, not the contract's Root disposition.
Absent candidate data returns UNRESOLVED. Missing/tampered historical bytes and
structural/semantic contradictions return REFUSED. Missing candidate artifacts
or policy bytes return UNRESOLVED. A conforming forged packet stays UNRESOLVED.

Implemented negative checks include strict UTF-8 JSON with duplicate, nonfinite,
Unicode surrogate, encoded-byte/depth/node/string and numeric-token limits;
lossless decimal parsing; explicit calendar-valid UTC with all seven fractional
digits retained; a closed interpreter for the existing schemas' limited
keywords; exact historical hashes and false flags; portable normalized relative
paths and Windows reserved-name/case-alias rejection; bounded byte counts/digests;
policy identity; positive bounded QPC frequency, exact QPC integers, same-capture
ordering and duration agreement. Capture is statically capped at300 seconds.
UTC/QPC agreement does not establish clock truth or compare different boots.

Optional disposition/admission inputs add structural and selected negative joins:
historical/policy/evidence/disposition identity, attempt-directory UUID equality,
host/generation digest equality, capture freshness within300 seconds, and issue
ordering. `validate_sequence` checks a supplied exact chronology map and
`validate_window` checks enclosure as pure functions. They are not proof that
those events occurred, and the chronology helper is not automatically joined to
unsupported auxiliary artifact formats. Auxiliary source-review/runtime/admission,
actual-return/review, event-host binding and native provider formats are not
qualified here. Provider guarantees, reviewer identity/adoption, old-host
authentication, restart kind, clock order and persisted-domain exclusion remain
UNRESOLVED regardless of assertion fields in those bytes.

`read_operational_artifact(approved_root, reference)` always raises
`OperationalReadUnavailable` before any path lookup or read. This avoids claiming
that Python `stat`, `resolve`, or an open-after-check sequence establishes retained
Windows identity. A future separately reviewed collector needs retained
root/ancestor/file handles, reparse and hard-link/alias rejection, containment,
mutation exclusion/detection and qualified evidence of actual read provenance.
Byte-map digest checks authenticate no filesystem object or host. These missing
guarantees cannot be supplied by a caller's boolean or a fixture.

`test_verifier.py` is an adversarial stdlib unittest subset for later guarded
validation. It loads the three immutable contracts and three exact old JSON
records as static fixtures using ordinary local reads; those reads are expressly
not operational evidence authentication. It imports `verifier.py` by absolute
sibling path so isolation mode works. Intended invocation, only after separate
source review, source/runtime pins and local run admission:

```text
Use the fixed guarded runner as described in PROTOCOL.md; do not invoke tests directly.
```

Test source covers parser bounds, malformed Unicode/JSON, decimals, dates,
paths/aliases, artifact tampering, exact schema pins/unknown keywords, QPC and
chronology failures, historical preservation, absent evidence and unconditional
positive-path refusal. These subset tests are not the48 original design cases;
they do not cover process/Job/Start/cleanup or execute provider observations.
Writing or reviewing these files executes no test. The48 design scenarios and
117 candidate tests/34 controls retain their separate unexecuted status.
Atomic attempt consumption, dispatch/post-operation generation reobservation,
stop/resources, actual process containment and owned cleanup require a future
separately reviewed controller and actual evidence review.
