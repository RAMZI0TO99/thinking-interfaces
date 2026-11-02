# P2 revision8 already-resident reference observation

29 October2026. New source proposal, not an operational result or grant. All
predecessor sources and failures remain frozen. Independent review, fresh
Q8/P8 source/runtime pins and admissions, actual evidence and Root acceptance
are required. R4 guards/performance, strict transport, raw984-entry namespace,
R6 descriptor occurrences and the three explicit System32 additions remain.

Q7 operation `6451d9c4-0c30-42fc-8a47-caa520b2043d` reached its first native
schema query and received E_NOTIMPL0x80004001 for datetime-l1-1-0. It produced
no mapping or suite result. File/guard closure was reviewed, but native module
reference closure lacked an actual result on exception and remains unproved.
Its archived failure actual review and Root disposition are required source
pins for both successors. P7 remains unadmitted. No new observation repairs
that failure, P3 uncertainty or historical custody.

## Narrow experimental basis

Microsoft documents that `GetModuleHandleExW` retrieves an already-loaded
module and, with flags0, adds a reference that must later be released. Full
module paths use backslashes. R8 uses no UNCHANGED_REFCOUNT, PIN, FROM_ADDRESS,
LoadLibrary, GetProcAddress, schema-query function or target-loading fallback.
The three baseline paths are exactly System32 kernelbase/kernel32/ntdll DLLs.
They are acquired by full path and validated before the14 contract-name calls.
The baseline references remain held throughout all observations.
See [GetModuleHandleExW](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulehandleexw).

Each exact pinned contract name is passed unchanged. Only a handle equal to
exactly one of those distinct baseline handles, with the corresponding exact
known module path (case-independent OS path comparison), can become a result.
No prefix/version guess is made. Exact API-contract-name lookup support is
**not established** by the documentation or this authorship; any failed lookup
refuses. Success would observe an already-resident reference in this caller,
not resolve an arbitrary import in another process. No tentative third-party
source-usage suggestion is treated as proof.

`GetModuleFileNameW` is bounded to260 WCHARs, and its return count excludes the
NUL. The helper checks a positive count below260, exact first NUL location and
known baseline path. A separate one-WCHAR call records return1/error122 and
termination. An unknown-contract lookup must fail and return no handle.
Local validation controls reject invalid length, termination and foreign handle.
See [GetModuleFileNameW](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulefilenamew).

Every successful flags0 call is a distinct owned acquisition, even if several
calls return the same HMODULE. A bounded ordered list records all calls; it is
never deduplicated by handle. Finally releases every successful acquisition in
reverse order, including an unexpectedly successful negative probe. Baselines
are not released early. The claim is owned reference balance, never global
module unload or reference counts belonging to other code.

## Failure-safe diagnostics and success-only mapping

The native helper returns a bounded `Result` after finally on both ordinary
success and failure. It includes the original exception type/message, ordered
reference calls, acquisition/release result/error per call, raw module paths
and lengths, acquired/released totals, all-owned-reference status, rows and
controls. A native exception is not thrown past the result before that evidence
can be published. Catastrophic process death or failed publication still leaves
evidence unproved; no guard is bypassed to force a diagnostic write.

The caller exclusively creates `Q8/native-diagnostic_<Q-UUID>.json`, obtains its
original native file identity, flushes and reads back/hashes those same bytes,
and retains the original ReadWrite/ShareRead handle. It records the diagnostic
reference and identity in caller-return and external-return **before** refusing
a returned failed observation. Thus a refused exact lookup may still provide
actual reference-balance evidence. No diagnostic alone authorizes P or accepts
a mapping.

Only complete success creates `Q8/api-mapping_<Q-UUID>.json` through the same
original-handle protocol. The mapping embeds the observation and the exact
diagnostic ref/native ID. Both Q receivers authenticate both files, compare the
observations and retain/verify helper bytes. The mapping SHA/native ID travel
in the existing two authenticated supervisor/child command arguments; the
embedded diagnostic ref is then checked by hash and original native ID.

The native observation has18 call records on success: three baselines,14
contract calls and one failed negative. Exactly17 acquisitions must have17
successful releases. Contract rows identify their reference index and baseline
handle. Equal handles across multiple rows remain separate owned references.
The five control keys are `negative_lookup_refused`, `small_buffer_refused`,
`invalid_length_refused`, `invalid_termination_refused`, `foreign_handle_refused`.
They are distinct from the192 suite methods, eight timestamp controls and two
native fault controls.

## Exact records and P joins

The source file keeps its legacy name `api_query_plan.json`, but schema is
`cho51_p8_resident_reference_plan_v1`: exact14 names, negative name, three exact
`baseline_modules`, OS version and seven file pins. Added byte/version pins are
kernel32 and ntdll. Existing pins cover kernelbase, apisetschema, cabinet,
fontsub and mswsock. Original read-only caller streams are retained throughout
Q/P use. They are explicit Windows platform-trust inputs, not hardlink waivers
in the strict physical-map reader. No loaded-image attestation follows.

New/changed fields for Root records:

- Diagnostic schema `cho51_q8_native_diagnostic_v1`: operation/plan/helper/file
  pins and original artifact native ID, `observation`, false
  `target_modules_loaded`, `loader_qualified`, `scientific_admission`.
- Mapping schema `cho51_q8_api_mapping_v1`: the same successful observation plus
  `native_diagnostic` `{path,bytes,sha256}` and
  `native_diagnostic_native_identity`16hex:32hex. It has no R7 `query` field or
  HRESULT/availability semantics.
- Q reports/payload/returns, actual review and Root qualification retain
  `api_mapping`/`api_mapping_native_identity` and add `native_diagnostic`/
  `native_diagnostic_native_identity`. Caller/external returns carry diagnostic
  fields even when mapping is null on failure.
- Q adoption retains `query_plan_sha256` as the legacy-named source-plan hash.
  It never contains a future diagnostic/mapping hash.
- P admission adds `native_diagnostic` alongside `api_mapping`. P adoption adds
  `native_diagnostic_sha256` alongside `api_mapping_sha256`. Both refs/native IDs
  must match the accepted Q actual review/qualification and the same Q UUID.
  P strictly retains/hashes both artifacts, verifies native IDs and requires
  identical successful observations.

Reference filenames are exactly
`runs/coordination/cho51_p3_dependency_prepare_20261029_q8/native-diagnostic_<Q-UUID>.json`
and the corresponding `api-mapping_<Q-UUID>.json`. The new native diagnostic
and mapping are each at most1MiB within unchanged total output caps. Raw native
call records are bounded to18, result rows14, flags exactly0 and buffer260.

P remains file-only. It makes no reference lookup or dependency load, freshly
checks the seven protected OS byte pins and the ordinary accepted JSON native
identities, preserves raw namespace derivation, and labels additional edges
`accepted_q_resident_reference_observation`. Hosts remain only the three known
baselines and must already be explicitly trusted and actually present. L must
qualify real per-importer loader/resource/export/ABI behavior; the Q caller's
resident reference observation is not that proof.

Existing test methods gain valid repeated-handle reference fixtures, lost-call/
missing-release/foreign-handle/wrong-flag refusals and a failed diagnostic that
cannot become an accepted mapping. The roster stays192. No native API call,
compiler, Python import, AST or test was executed in this authorship; only
source/file/hash/version metadata inspection and official documentation reading.

All Q90/60/5-second512/768MiB and P300/240/5-second4096/5120MiB guards,4GiB
available RAM/20GiB disk, original deadlines/process/Job/pipe ownership, stop,
sampling, physical/JSON/page/output limits remain. No fallback, limit increase,
package/Git/numerical execution or scientific grant is introduced. Historical
custody remains UNRESOLVED, Q1/P3/Q7 native cleanup limitations stay explicit,
004 consumed,005 held,006 unadmitted,117 tests/34 controls unexecuted, cells
0/1020 and freeze unsigned.
