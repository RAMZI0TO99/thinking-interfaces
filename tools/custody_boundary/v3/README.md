# Retained local artifacts and auxiliary joins v3

Engineering-only successor to the [v1 negative verifier](../v1/README.md).
This package also supersedes the frozen [v2 attempt](../v2/README.md), which
executed44 methods with one error in a constructor-cleanup test's directory
rename postcondition. The reader and auxiliary implementation bytes are unchanged.
The revised test observes successful real native closes for every handle opened
by the failing constructor; a new case fails after the final directory is opened.
All parent containment locks remain. The old failed attempt is retained and
consumed. Auxiliary record schemas remain version2; validation records use v3.
The v1 sources, design contracts and receipts stay unchanged. This package
implements retained local artifact reading and auxiliary metadata consistency.
It never issues a qualified boot boundary, operational admission or scientific
permission. Run only under the [reviewed local protocol](PROTOCOL.md).

## Retained artifact reader

`RetainedArtifactSet(approved_root)` accepts an exact-spelled uppercase-drive
DOS path on a fixed local NTFS volume. It retains the drive root, every ancestor,
every traversed directory and each file. References contain exactly `path`,
`bytes` and `sha256`; relative paths are normalized and bounded. UNC, device,
stream, short-name, case, traversal, reparse and hard-link aliases are refused.
The retained native handle supplies finalized path, volume/file identity, size,
link count and timestamps. Reads and repeat hashes use that same handle.

```python
with RetainedArtifactSet(approved_root) as files:
    data = files.read(reference)
    files.verify()
    witnesses = files.witnesses
```

File sharing permits read access only; ordinary incompatible writer/deleter
opens are excluded until release. The implementation also rechecks metadata
and hashes, poisons a refused set and attempts closure of every adopted handle.
The limits are16MiB per artifact,64MiB aggregate,64 artifacts,2048 retained handles
and64KiB read chunks. Exact repeated references reuse retained handles.

This authenticates **current checked local bytes and their retained namespace**
against supplied pins. It does not identify who wrote them or establish their
original machine. It is not an atomic snapshot against preexisting writable
mappings, privileged/kernel/filter/raw-volume interference or hardware faults.
Witnesses are saved observations, not an unforgeable certificate.

Microsoft documents the sharing and reparse-opening behavior in
[CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
Handle-based identity and normalized final names are documented in
[GetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle)
and [GetFinalPathNameByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew).
The NTFS check uses
[GetVolumeInformationByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew).
These platform contracts do not authenticate a historical process host.

## Auxiliary provenance records

`auxiliary.py` defines five closed versioned record kinds: source review,
runtime inventory, observation admission, actual caller return and actual review.
Their exact fields and bounds are enforced in code. Each uses a distinct
`cho51_p3_aux_<kind>_v2` schema identifier. They are new contracts, not aliases
for older saved records. No historical receipt is relabelled into this format.

The pure `assess_joins` API requires separately supplied packet, source-review,
actual-review and policy references, an artifact byte map and the three sealed
v1 contract bytes. It verifies complete referenced bytes, fixed old failure
hashes/false states, exact source/runtime/policy/operation joins, closed types,
reviewer separation, accepted flags, raw-observation/host-binding reference sets,
actual caller exit/identifier, capture times and bounded chronological windows.
Source inventories have at most16 entries; runtime metadata has at most1024.
All JSON also obeys the frozen parser's1MiB/depth16/8192node/4096string bounds.

`assess_retained` composes the same checks with native retained reads of the
packet, policy, contracts, reviews and referenced packet/source artifacts.
All reads are verified again before handles close. Runtime inventory entries
are checked metadata; this function does not load or newly observe those runtime
files. Neither API authenticates actor strings, independently proves execution,
or replaces Root's adoption of a genuinely separate review.

A coherent fixture returns `auxiliary_joins_verified=true` and UNRESOLVED.
The native composition may also report `retained_reads_verified=true` after
successful closure. `review_identity_authenticated`, `loaded_runtime_attested`,
`boundary_qualified`, `launch_authorized` and `scientific_admission` stay false.
Any malformed or contradictory required join returns REFUSED. Missing provider
semantics cannot be supplied as a caller boolean to unlock the positive path.

## Validation scope

Reader tests exercise ordinary real NTFS files, handle reuse, writer/delete/
rename exclusion, real hard-link refusal, release, bounds and injected failure
paths. Reparse/native-error branches are injected at the API boundary; actual
junction/symlink behavior is not qualified by those injections. No privilege
assumption or test skip supplies missing evidence.

Auxiliary tests build explicitly synthetic records, recompute downstream hashes
after semantic tampering, and check both pure joins and a materialized retained
file composition. Exact old receipts are static byte fixtures, not evidence
that their missing host identity was recovered. Tests retain fixtures only in
new attempt-local directories. A separate fixed smoke operation reads six real,
already pinned project artifacts under retained handles; it does not query
Windows Event Log, process tables, a model or any scientific case.

The immutable48-case design matrix and original117 candidate tests/34controls
remain separate. Source presence and this README do not claim test execution;
actual results are recorded under the new phase's distinct review/qualification.
This successor has45 methods:31 reader cases and14 auxiliary cases.
