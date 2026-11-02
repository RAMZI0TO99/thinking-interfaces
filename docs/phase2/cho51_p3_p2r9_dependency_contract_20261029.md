# P2 revision9 cooperative original-handle handoff

29 October2026. Source-only successor, requiring independent review and fresh
Q9/P9 pins/admissions/results. All prior sources, artifacts and consumed failures
stay frozen. Q8 operation `7c2de01e-6143-4421-a750-b686b69dc2d4` observed14
exact names,17 released acquisitions and five native controls, then failed
WinError32 while the supervisor read the mapping. Its independent actual review
and Root disposition are required pins. It is
`FAILED_P2Q_CONSUMED_OWNED_CLOSED`; neither mapping nor tests were qualified.
No Q8 artifact is adopted as an accepted Q9 input. The earlier Q8 startup failure
and every older cleanup limitation also remain unchanged.

## Sharing diagnosis and narrow custody contract

The original caller owns mapping/diagnostic/helper output handles opened
ReadWrite with ShareRead. A new read handle that shares only READ refuses the
existing writer access, even though the writer permits a reader. The same
problem affects all three artifacts, not only the first mapping read.

The Q9 control reader therefore provides only an operation-scoped cooperative
authorization, not a general sharing option. The caller-supplied canonical
root/UUID/role computes exactly one of `api-mapping_UUID.json`,
`native-diagnostic_UUID.json`, `native-helper_UUID.dll`. Role, byte count,
SHA256 and original volume:file ID are mandatory before opening. At most three
such authorizations exist. Only their read-only handles share READ|WRITE.
They still do not request WRITE or DELETE access and do not share DELETE.
Every ordinary input, directory and output open keeps its existing sharing.
The production P reader is unchanged and uses strict ShareRead after Q closes.

The consumer's share-WRITE bit admits the **existing original caller writer**;
it cannot independently protect against another writer if that owner vanishes.
Protection comes from the caller's continuously retained RW/ShareRead original
handles, which deny all other writers/deleters while consumers are alive. The
reviewed caller does not mutate their bytes after publication. No close/reopen
transition, reissued writer handle or pathname-only custody inference is used.

Native type/identity/final-path/single-link/reparse/ancestry/hash bounds remain
unchanged. Capability identity is checked on the actual new read handle before
registration. Retention hashes against the mandatory expected pin. Verification
uses those same original consumer handles; it does not strict-reopen an artifact
while the parent's writer is still live. Mismatched path/role/hash/ID refuses.

## Producer and both consumers

The caller now sends mapping byte count as one extra fixed command argument,
alongside the existing authenticated SHA/native ID. The supervisor and child
authorize the mapping before its first read. The authenticated mapping then
provides diagnostic and helper refs/native IDs; both are separately authorized
before their first read. Both receivers verify all three actual identities and
bytes and report their exact capabilities. Mapping/diagnostic schemas advance
to `cho51_q9_api_mapping_v1`/`cho51_q9_native_diagnostic_v1`, adding
`native_helper_native_identity`. P joins that value to the accepted emitted
helper's builder identity. The plan schema is
`cho51_p9_resident_reference_plan_v1`; observation mechanics remain R8's.

The caller compares returned capabilities against its three originals, reaps
the supervisor and its owned Job/consumers, then rehashes/reidentifies every
original writer handle before closing any of them. Successful acceptance
requires all three originals, complete consumer reaping and that final recheck.
Writer lifetime is continuous through consumer closure. Files are preserved
on failure; uncertainty refuses. No artifact from a failed operation becomes
qualified because it happens to contain a successful native observation.

`caller_artifact_capabilities` in the Q report/payload/supervisor return contains
three `{role,path,bytes,sha256,native_identity,read_share:3}` entries. Both consumer
lists must agree and the caller compares every entry to its original reference.
The caller/external returns carry `artifact_handoff`:

- `consumers_reaped`, `final_original_recheck`,
  `original_writers_held_through_consumers` are exact true for accepted handoff;
- `artifacts` has three `{role,reference,native_identity,writer_share:1}` entries
  for mapping, diagnostic and helper. References retain path/bytes/SHA256.

No-consumer failure is not described as reaping. A failed supervisor can report
`handle_closure.output_state=not_created`, separately from `open` or `closed`,
so an output owner that never existed is not silently described as an unclosed
original output handle.

## Qualification and Root record changes

Three new native fixture methods test: a cooperative read while the original
writer blocks unrelated write/delete/rename; ordinary Q and P readers refusing
that live writer; and path/role/hash/native-ID capability refusal. Fixtures use
only three additional JSON files in bounded short directories. These are real
sharing checks under a newly admitted Q, not author-executed evidence.

The exact roster becomes195 (192 predecessor methods plus those three), and
only the roster bound increases to195. All time/process/memory/IO/file/output
caps stay unchanged. A separate `sharing_controls` report has exact true keys
`cooperative_read_protected`, `ordinary_reader_strict`,
`capability_authentication`, tied to the three collected/executed method IDs.
The existing five resident-reference controls, eight timestamps and two fault
controls remain distinct and are not inflated by these tests.

New mandatory Q actual-review/Root-qualification fields are `artifact_handoff`
and `sharing_controls`, copied from genuine accepted external return and test
report and joined exactly by P. Existing `api_mapping`,
`api_mapping_native_identity`, `native_diagnostic`,
`native_diagnostic_native_identity`, helper/builder IDs and false authority
fields remain. Root qualification now requires195 exact tests,8/2 controls and
the three sharing outcomes. Its source/actual reviews remain independent.

P admission/adoption keep the R8 fields: both artifact refs in admission,
`api_mapping_sha256` and `native_diagnostic_sha256` in adoption; no new operational
field is needed there. Their qualification/actual joins additionally require
the exact original-writer handoff and sharing controls. Source pins, Q9 paths,
new schemas and195-method requirement prevent reuse of failed Q8 records.

The native helper remains emitted in fresh Q; P is file-only. Seven explicit OS
pins, resident-reference semantics, raw984 namespace, explicit host trust,
occurrence evidence, provisional preparation and the mandatory final full
original-byte/identity/census verification remain unchanged. L owns actual
per-importer loader/export/ABI qualification.

Q retains90/60/5 seconds,512/768MiB; P300/240/5 and4096/5120MiB,4GiB
available RAM/20GiB disk, original clocks, independent guards, stop/sample
freshness, Jobs/pipes,64KiB chunks and all physical/JSON/page/output caps. No
source/API/runtime/compiler/import/AST/test/Git execution occurred in this
authorship. Historical custody stays UNRESOLVED; P3 and old Q7 limitations
remain unproved,004 consumed,005 held,006 unadmitted,117 tests/34 controls
unexecuted, scientific cells0/1020 and freeze unsigned.
