# P2 revision3 strict long-path transport successor

29 October 2026. Source implementation only; independent source review and new
Q3/P3 admissions/results remain required. Frozen Q/P/R sources and receipts are
unchanged. This supplement retains the [local validation contract](cho51_p3_local_validation_contract_20261029.md),
[P2 contract](cho51_p3_p2_dependency_contract_20261029.md) and
[revision2 isolated-runtime supplement](cho51_p3_p2r2_dependency_contract_20261029.md).

The revision2 P operation `2cc07db6-c210-4e9e-bed9-788d5abb8a0c` is consumed.
Its independently reviewed Root disposition is
`FAILED_P2_P_CONSUMED_OWNED_CLOSED`, with exit1, owned lifecycle closed, no
accepted physical map and retry false. The saved failure names an unselected
historical census leaf of261 characters below
`evidence/cho51-worker-lifecycle-20261015/artifacts/`. Static file/metadata
diagnosis found that file through .NET (452 bytes), with
`windows_LongPathsEnabled=0`. This supports a legacy path-transport explanation;
it does not establish a complete causal trace. The exact diagnosis, actual
review and Root disposition are required source pins for both new versions.
No Windows setting changes, skipped path, excluded historical subtree, relaxed
single-link check or replay of the consumed attempt is authorized.

`p2r3/native_reader.py` is a new fork of the strict Q4 reader, with one internal
transport function. It validates the existing ordinary canonical local-drive
path using the unchanged lexical contract **before** constructing its
`\\?\` Win32 API spelling. `CreateFileW`, `os.scandir` and no-follow `os.stat`
receive that spelling locally. The manifest's metadata/census operations use
the same transport. Returned names are joined to the original canonical root;
descriptors, pins, census rows and absence paths retain ordinary forward-slash
drive paths. User-supplied prefixed/device/UNC/dot/8.3/reserved-name aliases stay
refused. The native final-path comparison still requires the exact final
`\\?\` spelling generated from that canonical descriptor path.

All original-handle identity, fixed local NTFS, single-link, reparse/device,
ancestry, incompatible-writer/delete, hash and initial/final membership guards
are retained. Directory handles still do not freeze membership. The limits
remain25,000 physical files/4GiB aggregate/2GiB per file/depth32, with64KiB
hash/range chunks, bounded pages,8MiB/200,000-node records and64MiB/256 outputs.
This is API transport, not a broader accepted path grammar or loader grant.
No source, selected scientific scope or scientific eligibility is removed.

The Q3 bootstrap/control reader remains the short-control implementation copied
from Q2. The30 reader qualification methods are explicitly retargeted to the
new P3 reader; P3 manifest/output type-exact checks and its supervisor loader
also name that new reader. Eight additional methods cover >260-character
leaf/directory paths, retained input and output identities, writer denial,
full census drift, actual optional absence resampling and lexical/prefixed
alias refusals. The proposed roster is184 methods, not an execution receipt.
Q3's child-only final fixture census uses bounded local extended-path scanning
and JSON size/type accounting. Existing negative hardlink fixtures remain
controlled qualification fixtures; this does not waive the production reader's
single-link refusal. No global os/Path monkeypatch or registry change occurs.

Q3 audit confinement reverses only the exact generated extended fixture
transport, revalidates the underlying canonical path and applies the unchanged
owned-fixture boundary. It adds no external read/write allowance. The Q parent
retains its short source/runtime/control/output handles; it does not claim a
strict physical-map observation of all negative fixture bytes. The child retains
the existing exact roster and bounded report/handoff controls.

Q3 retains90/60/5 seconds and512/768MiB; P3 retains300/240/5 seconds and
4096/5120MiB, original caller clocks/deadlines, independent guards, stop controls,
one thread, hidden GPUs,4GiB available RAM and20GiB disk. Fresh native PE
emission/identity qualification, reviewed source coverage, unused UUID/admission,
actual tool return, independent result review and Root adoption are still
separate requirements. P3's protocol/caller bind184 Q methods/eight UTC/two
native fault controls only after those exact new results are accepted.

R provisioning remains provisioning only. L/V/C, Git execution, native search,
ABI and loaded-resource/origin qualification remain separate and unproved.
The117 candidate tests and34 successor controls remain unexecuted. Historical
custody stays UNRESOLVED, Q1 cleanup/cause unproved,004 consumed,005 held,
006 unadmitted, scientific cells0/1020 and final freeze unsigned. Closing the
new owned failure does not repair any historical process or authorize retry.
