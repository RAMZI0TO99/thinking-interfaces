# P2 revision5 exact API host metadata grammar

29 October2026. Source-only successor requiring independent review and fresh
Q5/P5 admissions, pins and results. Frozen sources/attempts remain unchanged.
The [local validation contract](cho51_p3_local_validation_contract_20261029.md),
[P2 contract](cho51_p3_p2_dependency_contract_20261029.md), strict transport
[revision3](cho51_p3_p2r3_dependency_contract_20261029.md) and guard-preserving
performance [revision4](cho51_p3_p2r4_dependency_contract_20261029.md) remain the
substantive basis. No resource, clock, stop or native ownership rule changes.

P4 operation `ad3cee21-4d81-42f9-9f7e-52410462bdda` is consumed with Root status
`FAILED_P2_P_CONSUMED_OWNED_CLOSED`, exit1 and independently reviewed owned
closure. Its73.13-second failed operation retained39 provisional physical-map
outputs; no physical map or final full input verification was accepted. The
failure was `Refusal: API host basename` while deriving API metadata, before
the selected PE image import-table pass. The P4 actual review, Root disposition
and static API-host diagnosis are required source pins for both new versions.
Nothing here replays or accepts that failed attempt. P3's separate deadline
failure and unproved closure remain unchanged.

The already pinned namespace contains984 API entries, including48 entries with
non-DLL hosts and15 distinct `.sys`/`.drv` names. The source-reviewed diagnosis
found a mismatch between that existing namespace and the parser/supervisor's
DLL-only host grammar. No namespace entry or platform-trust image is added.

The sole functional correction is a shared concrete `pe.host_basename` predicate
used by both namespace derivation and supervisor validation. It accepts only
lowercase ASCII basename metadata ending `.dll`, `.sys` or `.drv`, under the
existing strict Windows lexical path validator. Device/reserved names, paths,
UNC/device syntax, separators, drive/stream syntax, traversal/double-dot names,
trailing spaces/dots and other suffixes refuse. Empty metadata hosts retain the
existing representation as no named host; they are not passed to the predicate.
API keys remain `.dll` and retain their existing API-name grammar.

Derivation from fresh bounded retained `apisetschema.dll` bytes must still equal
the exact pinned policy namespace. A syntactically valid host is not trusted by
its suffix: every host of a used API edge must already appear in the explicit
platform policy, and every used platform path still needs fresh exact System32
presence/type checks. Unknown/untrusted driver hosts do not resolve merely
because they end `.sys` or `.drv`. No automatic driver allowance, platform trust
expansion, image loading, ABI or native-search qualification is introduced.

One additional Q method uses the shared concrete helper and synthetic namespace
bytes for `.dll`/`.sys`/`.drv` roundtrips. Its subtests reject malformed/device/
path/traversal/unsupported hosts in both the helper and parser and confirm that
valid but untrusted hosts leave the API edge unresolved. The proposed suite is
192 methods, within the unchanged192-method roster cap. Source counts are not
execution results. P5's caller/protocol bind192 methods/eight UTC/two native
fault controls only after separately reviewed Q5 results and qualification.

All R4 mechanics remain: fresh ancestor/leaf stop checks with lexical-only cache,
one complete retained parent traversal, provisional preparation and a mandatory
full original-handle byte/identity and initial/final census verification after
PE/result publication before any accepted observer return. No verification or
resource decision is cached, and pending saved artifacts are not rewritten into
acceptance. Original process/Job/pipe/output handoff, limits and deadlines remain.

Q remains90/60/5 seconds and512/768MiB; P remains300/240/5 seconds and
4096/5120MiB, with4GiB available RAM/20GiB disk, one thread, hidden GPUs, strict
stop and sampling freshness,25,000 physical files/4GiB aggregate/2GiB per file,
depth32,64KiB chunks and unchanged JSON/page/output caps. No Git, package,
candidate, scientific or new runtime execution was performed in this authorship.

The117 candidate tests/34 controls remain unexecuted. L/V/C, Git execution,
native search, ABI and loaded-resource/origin qualification remain separate.
Historical custody remains UNRESOLVED, Q1 unproved,004 consumed,005 held,
006 unadmitted, scientific cells0/1020 and final freeze unsigned.
