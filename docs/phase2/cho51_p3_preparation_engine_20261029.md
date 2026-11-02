# P1 retained preparation engine qualification

29 October 2026. Engineering-only implementation and Q qualification accepted.

The P1 engine now joins an explicit physical recipe to retained native file
observations. Its fresh Q qualification passed **108 methods**, including
**35 new preparation methods**, plus **eight timestamp controls and two native
fault controls**. No failures, errors or skips occurred. The actual tool returned
exit0 in13.4948485 seconds with the new operation's owned lifecycle closed.

The [independent source review](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/source-review.json)
and separate [actual-result review](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/actual-review.json)
are accepted with no findings. [Root qualification](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/root-qualification.json)
adopts only the tested engine scope. This is Q qualification of a P component;
it is not actual P dependency preparation or proof of complete package coverage.

## What changed

The new [preparation engine](../../tools/local_validation/p1/README.md) provides
strict recipe parsing and a retained observation session. Recipes declare fixed
scope roots, all four source/runtime/package/metadata roles, exact-file or tree
groups, literal suffixes, exclusions, seeds and the complete expected selected
path/bytes/SHA256 map. Aliases, overlap, missing or extra selected paths, pin
drift and count/size/JSON limits refuse rather than producing a partial pass.

The session uses unchanged Q4 native handles and v1 bounded record primitives.
It retains file and ancestor identities, compares initial/final tree membership,
rehashes inputs and returns defensive records. A failure poisons the session;
it cannot be reused. Caller-owned publication must occur while the session
remains open, with verification immediately before and after publication, and
explicit final cleanup. Directory handles do not freeze membership. Exact-file
groups do not claim completeness of unrelated parent-directory members.

The 35 new methods comprise21 recipe tests and14 preparation tests, including
real retained four-role JSON trees, missing/extra/changed inputs, added directory
membership, hardlinks, writer/delete denial and failed-session reuse. Reparse
attribute injection is explicitly narrower than a real reparse-point fixture.
The synthetic role labels do not represent observed third-party packages.

The new [P1Q runner](../../tools/local_validation/p1q/README.md) adapts the frozen
Q4 runner's phase/module/source bindings and loads the new engine/tests. Native
Job helper, adapter and reader behavior remain unchanged. The
[implementation-specific supplement](cho51_p3_p1_preparation_contract_20261029.md)
keeps this caller Q-only, including its explicitly admitted in-memory compiler.
It must not be relabeled as a file-only P caller.

## Admitted and reviewed evidence

Operation: `1888ddc4-cce7-49f4-9b61-255683a8d0ab`.
The fresh [admission](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/admission_1888ddc4-cce7-49f4-9b61-255683a8d0ab.json)
followed source acceptance and Root adoption, with37 source inputs and732
freshly checked base-runtime files. The independent actual review also verified
all874 preservation pins and the fresh exact runtime census. The runtime was
the admitted local Python3.12.14 and PowerShell7.6.5; changed sources or another
runtime are not certified by this result.

| Result or resource | Actual evidence |
| --- | --- |
| Exact method roster |108:31 foundation,30 retained reader,12 protocol,35 P1 |
| Test outcomes |108 passed; zero failure/error/skip/expected failure/unexpected success |
| Separate caller controls |Eight timestamp controls passed |
| Separate native controls |Badframe refused trailing bytes; stall hit its frame deadline; both owned Jobs closed |
| Synthetic fixtures |93 JSON files totaling1,355 bytes |
| Whole/work/cleanup limits |90s /60s /5s, unchanged |
| Actual complete tool boundary |13.4948485s, exit0 |
| Process/caller and Job caps |512MiB /768MiB, unchanged |
| Peak caller private / outer Job |136,536,064 /80,723,968 bytes |
| Minimum observed outer available RAM |9,821,814,784 bytes; required4GiB |
| Minimum observed outer free disk |79,014,387,712 bytes; required20GiB |
| Thread/device limits |One library thread; GPUs hidden |

The retained [test report](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/attempts/1888ddc4-cce7-49f4-9b61-255683a8d0ab/test-report.json),
[payload](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/attempts/1888ddc4-cce7-49f4-9b61-255683a8d0ab/payload.json)
and [external tool audit](../../runs/coordination/cho51_p3_preparation_engine_20261029_p1q/external-audit.json)
bind the actual return and owned closure. The outer Job and three sequential
inner Jobs closed; original process/thread/pipe/file handles and the guard
closed with bounded EOF. Original pending flags stay immutable; the subsequent
actual review and Root adoption resolve them through separate joined records.

## Remaining gate

Next, build and independently review the **complete physical dependency recipe
and file-only P caller**. The recipe must cover transitive Python/native
dependencies, exact import resources and distribution metadata, current project
source census and initializers, configuration assets, Git/runtime inputs and
explicit platform-trust boundaries. It must exclude scientific data and weights.
The source-time seed list is insufficient to establish this coverage.

Only then can actual P run under its separately reviewed300s/240s/5s envelope,
fresh admission, retained observation and independent pin/coverage/result review.
L loader/collection, V117/34 and C closeout remain separate later stages. The
engine's proposed maps intentionally leave coverage, loader, runtime, launch
and scientific authority false.

The full26 qualification scenarios and original48 custody cases remain
incomplete; a real reparse fixture and complete loaded-image/dependency coverage
are not established. Q1's cause and cleanup remain unproved. Q2/Q3 failures,
Q4 acceptance and all earlier sources/receipts remain unchanged. Bootstrap004
is consumed,005 held,006 unadmitted and historical custody UNRESOLVED.
The117 candidate tests and34 successor controls remain unexecuted; scientific
cells remain0/1020 and the final freeze unsigned.

The12 prior active documents are preserved in the
[documentation archive](../history/preparation_engine_20261029/ARCHIVE_INDEX.md).
No raw data,weights,frozen evidence or prior attempt was modified. The source
changes remain uncommitted; no push was made in this step.
